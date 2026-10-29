/* HOST-02 below the real-signal harness: signal dispositions, the exit table and the stop before the first
 * frame, driven in-process.
 *
 *   test_host_run disposition|exit_table|stop_before_first_frame
 *
 * Linked against gabbaboy_host_testing (the only host library built with GBB_HOST_TESTING, which carries
 * the after-ready hook) and the core. Each case prints `PASS <case>` or fails with a located REQUIRE
 * line. POSIX only: sigaction, sigprocmask, dup2 and mkdtemp. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gbb_host.h"
#include "host_exit.h"

#include <dirent.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static const int handled_signals[] = {SIGTERM, SIGINT, SIGHUP};
#define HANDLED_COUNT (sizeof(handled_signals) / sizeof(handled_signals[0]))

typedef struct {
    struct sigaction action[HANDLED_COUNT];
    struct sigaction pipe_action;
    sigset_t mask;
} saved_signals;

static void save_signals(saved_signals *saved) {
    for (size_t i = 0u; i < HANDLED_COUNT; ++i) (void)sigaction(handled_signals[i], NULL, &saved->action[i]);
    (void)sigaction(SIGPIPE, NULL, &saved->pipe_action);
    (void)sigprocmask(SIG_SETMASK, NULL, &saved->mask);
}

static void restore_signals(const saved_signals *saved) {
    for (size_t i = 0u; i < HANDLED_COUNT; ++i) (void)sigaction(handled_signals[i], &saved->action[i], NULL);
    (void)sigaction(SIGPIPE, &saved->pipe_action, NULL);
    (void)sigprocmask(SIG_SETMASK, &saved->mask, NULL);
}

static void default_action(int sig) {
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = SIG_DFL;
    (void)sigemptyset(&action.sa_mask);
    (void)sigaction(sig, &action, NULL);
}

static int is_handled(const struct sigaction *action) {
    return action->sa_handler != SIG_DFL && action->sa_handler != SIG_IGN;
}

static int mask_is_empty(const sigset_t *set) {
    for (int sig = 1; sig < 32; ++sig)
        if (sigismember(set, sig) == 1) return 0;
    return 1;
}

/* D-13: handler install. A non-default handler with SA_RESETHAND and SA_RESTART and an empty mask on
 * TERM, INT and HUP; SIGPIPE ignored; an inherited SIG_IGN on INT stays ignored; TERM, INT and HUP are
 * unblocked even when the process started with them blocked. */
static int disposition(void) {
    saved_signals saved;
    save_signals(&saved);

    for (size_t i = 0u; i < HANDLED_COUNT; ++i) default_action(handled_signals[i]);
    sigset_t blocked;
    (void)sigemptyset(&blocked);
    for (size_t i = 0u; i < HANDLED_COUNT; ++i) (void)sigaddset(&blocked, handled_signals[i]);
    REQUIRE(sigprocmask(SIG_BLOCK, &blocked, NULL) == 0);

    REQUIRE(host_signal_install() == 0);

    for (size_t i = 0u; i < HANDLED_COUNT; ++i) {
        struct sigaction query;
        REQUIRE(sigaction(handled_signals[i], NULL, &query) == 0);
        REQUIRE(is_handled(&query));
        REQUIRE((query.sa_flags & SA_RESTART) != 0);
        REQUIRE(mask_is_empty(&query.sa_mask));
    }
    /* SA_RESETHAND is proven by behaviour: Darwin does not report that flag back from a sigaction query,
     * but on every platform the first delivery stores the signal number and puts the default action back,
     * so a second SIGTERM from a supervisor still kills a wedged runner. */
    for (size_t i = 0u; i < HANDLED_COUNT; ++i) {
        REQUIRE(host_signal_install() == 0);
        REQUIRE(host_signal_stop_requested() == 0);
        REQUIRE(raise(handled_signals[i]) == 0);
        REQUIRE(host_signal_stop_requested() == handled_signals[i]);
        struct sigaction after;
        REQUIRE(sigaction(handled_signals[i], NULL, &after) == 0);
        REQUIRE(after.sa_handler == SIG_DFL);
    }
    REQUIRE(host_signal_install() == 0);
    struct sigaction pipe_query;
    REQUIRE(sigaction(SIGPIPE, NULL, &pipe_query) == 0);
    REQUIRE(pipe_query.sa_handler == SIG_IGN);

    sigset_t current;
    REQUIRE(sigprocmask(SIG_SETMASK, NULL, &current) == 0);
    for (size_t i = 0u; i < HANDLED_COUNT; ++i) REQUIRE(sigismember(&current, handled_signals[i]) == 0);

    /* nohup and background shells: SIGINT and SIGHUP inherited as SIG_IGN stay ignored; TERM does not. */
    struct sigaction ignore;
    memset(&ignore, 0, sizeof(ignore));
    ignore.sa_handler = SIG_IGN;
    (void)sigemptyset(&ignore.sa_mask);
    REQUIRE(sigaction(SIGINT, &ignore, NULL) == 0);
    REQUIRE(sigaction(SIGHUP, &ignore, NULL) == 0);
    default_action(SIGTERM);
    REQUIRE(host_signal_install() == 0);
    struct sigaction query;
    REQUIRE(sigaction(SIGINT, NULL, &query) == 0);
    REQUIRE(query.sa_handler == SIG_IGN);
    REQUIRE(sigaction(SIGHUP, NULL, &query) == 0);
    REQUIRE(query.sa_handler == SIG_IGN);
    REQUIRE(sigaction(SIGTERM, NULL, &query) == 0);
    REQUIRE(is_handled(&query));

    /* The flag is the only effect of a signal: raise one and read it back. */
    REQUIRE(host_signal_stop_requested() == 0);
    REQUIRE(raise(SIGTERM) == 0);
    REQUIRE(host_signal_stop_requested() == SIGTERM);
    REQUIRE(strcmp(host_signal_name(SIGTERM), "SIGTERM") == 0);
    REQUIRE(strcmp(host_signal_name(SIGINT), "SIGINT") == 0);
    REQUIRE(strcmp(host_signal_name(SIGHUP), "SIGHUP") == 0);
    /* SA_RESETHAND: the disposition is back to the default action after the first signal. */
    REQUIRE(sigaction(SIGTERM, NULL, &query) == 0);
    REQUIRE(query.sa_handler == SIG_DFL);
    /* A fresh install clears the earlier stop. */
    REQUIRE(host_signal_install() == 0);
    REQUIRE(host_signal_stop_requested() == 0);

    restore_signals(&saved);
    return 0;
}

/* D-15: the table has exactly the rows 0 clean, 1 failure, 2 refusal; every other number is unnamed. */
static int exit_table(void) {
    static const struct { int code; const char *name; } rows[] = {
#define GBB_TEST_EXIT_ROW(code, ident, name, meaning) {(code), (name)},
        GBB_HOST_EXIT_TABLE(GBB_TEST_EXIT_ROW)
#undef GBB_TEST_EXIT_ROW
    };
    REQUIRE(sizeof(rows) / sizeof(rows[0]) == 3u);
    REQUIRE(rows[0].code == 0 && strcmp(rows[0].name, "clean") == 0);
    REQUIRE(rows[1].code == 1 && strcmp(rows[1].name, "failure") == 0);
    REQUIRE(rows[2].code == 2 && strcmp(rows[2].name, "refusal") == 0);
    REQUIRE(GBB_HOST_EXIT_CLEAN == 0 && GBB_HOST_EXIT_FAILURE == 1 && GBB_HOST_EXIT_REFUSAL == 2);
    for (size_t i = 0u; i < sizeof(rows) / sizeof(rows[0]); ++i) {
        const char *name = host_exit_name(rows[i].code);
        REQUIRE(name != NULL && strcmp(name, rows[i].name) == 0);
    }
    /* 3 and 4 belong to the acceptance mode of the same executable, 77 to skip semantics: host mode never
     * emits them, so they have no row. */
    REQUIRE(host_exit_name(3) == NULL);
    REQUIRE(host_exit_name(4) == NULL);
    REQUIRE(host_exit_name(77) == NULL);
    REQUIRE(host_exit_name(-1) == NULL);
    REQUIRE(host_exit_name(256) == NULL);
    return 0;
}

/* ---- stop before the first frame ---------------------------------------------------------------- */

static void raise_term(void) { (void)raise(SIGTERM); }

static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}

static int write_file(const char *path, const uint8_t *bytes, size_t length) {
    FILE *file = fopen(path, "wb");
    if (file == NULL) return 0;
    const size_t count = fwrite(bytes, 1u, length, file);
    return fclose(file) == 0 && count == length;
}

static int count_entries(const char *directory) {
    DIR *handle = opendir(directory);
    if (handle == NULL) return -1;
    int count = 0;
    struct dirent *entry;
    while ((entry = readdir(handle)) != NULL)
        if (strcmp(entry->d_name, ".") != 0 && strcmp(entry->d_name, "..") != 0) ++count;
    (void)closedir(handle);
    return count;
}

static void remove_entry(const char *directory, const char *name) {
    char path[1024];
    (void)snprintf(path, sizeof(path), "%s/%s", directory, name);
    (void)unlink(path);
}

/* D-14: a signal that is already pending when the first boundary is polled stops the run with
 * stopped_at_frame=0 flush=none, exit 0, and a battery cartridge gets no .sav. */
static int stop_before_first_frame(void) {
    saved_signals saved;
    save_signals(&saved);

    const char *tmp = getenv("TMPDIR");
    if (tmp == NULL || tmp[0] == '\0') tmp = "/tmp";
    char templ[512];
    (void)snprintf(templ, sizeof(templ), "%s/gabbaboy-host-run-XXXXXX", tmp);
    REQUIRE(mkdtemp(templ) != NULL);

    static uint8_t rom[32768];
    memset(rom, 0, sizeof(rom));
    rom[0x147] = 0x03; /* MBC1 + RAM + battery */
    rom[0x148] = 0x00;
    rom[0x149] = 0x02; /* 8 KiB */
    fix_checksum(rom);
    char rom_path[600];
    (void)snprintf(rom_path, sizeof(rom_path), "%s/guard.gb", templ);
    REQUIRE(write_file(rom_path, rom, sizeof(rom)));
    char save_dir[600];
    (void)snprintf(save_dir, sizeof(save_dir), "%s/saves", templ);
    REQUIRE(mkdir(save_dir, 0700) == 0);

    char log_path[600];
    (void)snprintf(log_path, sizeof(log_path), "%s/stderr.log", templ);
    const int log_fd = open(log_path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
    REQUIRE(log_fd >= 0);
    (void)fflush(stderr);
    const int saved_stderr = dup(2);
    REQUIRE(saved_stderr >= 0);
    REQUIRE(dup2(log_fd, 2) >= 0);
    (void)close(log_fd);

    host_run_test_set_after_ready_hook(raise_term);
    char *argv[] = {"gabbaboy-runner", "--rom", rom_path, "--save-dir", save_dir, NULL};
    const int code = gbb_host_main(5, argv);
    host_run_test_set_after_ready_hook(NULL);

    (void)fflush(stderr);
    REQUIRE(dup2(saved_stderr, 2) >= 0);
    (void)close(saved_stderr);

    char text[4096];
    memset(text, 0, sizeof(text));
    FILE *log = fopen(log_path, "rb");
    REQUIRE(log != NULL);
    const size_t length = fread(text, 1u, sizeof(text) - 1u, log);
    (void)fclose(log);
    text[length] = '\0';

    const int entries = count_entries(save_dir);
    restore_signals(&saved);

    REQUIRE(code == 0);
    REQUIRE(strstr(text, "gbb-host: ready") != NULL);
    REQUIRE(strstr(text, "reason=SIGTERM stopped_at_frame=0 flush=none") != NULL);
    REQUIRE(strstr(text, "flush reason=final") == NULL);
    REQUIRE(entries == 0);

    remove_entry(save_dir, "guard.sav");
    remove_entry(templ, "stderr.log");
    remove_entry(templ, "guard.gb");
    (void)rmdir(save_dir);
    (void)rmdir(templ);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: test_host_run <case>\n");
        return 2;
    }
    static const struct { const char *name; int (*run)(void); } cases[] = {
        {"disposition", disposition}, {"exit_table", exit_table},
        {"stop_before_first_frame", stop_before_first_frame}
    };
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (strcmp(argv[1], cases[i].name) != 0) continue;
        if (cases[i].run() != 0) {
            fprintf(stderr, "FAIL %s\n", cases[i].name);
            return 1;
        }
        printf("PASS %s\n", cases[i].name);
        return 0;
    }
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
