/* Writer and sweep behaviour checked without the fault seams.
 *
 *   test_host_save_mode preserve_mode|sweep_batches
 *
 * A separate program from test_host_save_io so a mutant host library (built without GBB_HOST_TESTING) can be
 * linked against the same cases. Prints `PASS <case>` or `FAIL <case>: file:line expr`. POSIX only.
 *
 *   preserve_mode  WR-05: host_save_io_replace keeps the permission bits of the save it replaces. The temp is
 *                  created 0600, and a rename would publish that, dropping the access of a save that was shared
 *                  (0644, 0664) or read by a supervisor under another uid. A first write stays 0600.
 *   sweep_batches  IN-01: the sweep collects names before it unlinks them, at most one fixed batch per pass, and
 *                  still removes every stale temp when there are more than a batch; a pass that removes nothing
 *                  (temp-named directories, which unlinkat cannot remove) ends the sweep. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gbb_host.h"

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

static const char *current_case = "unknown";

#define REQUIRE(x) do { if (!(x)) { \
    printf("FAIL %s: %s:%d %s\n", current_case, __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define IMAGE_BYTES 64u

static bool make_root(char *root, size_t capacity, const char *tag) {
    const char *base = getenv("TMPDIR");
    if (base == NULL || base[0] == '\0') base = "/tmp";
    const int count = snprintf(root, capacity, "%s/gbb-host-%s-XXXXXX", base, tag);
    return count > 0 && (size_t)count < capacity && mkdtemp(root) != NULL;
}

static bool put(int dirfd, const char *name, mode_t mode) {
    const int fd = openat(dirfd, name, O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) return false;
    const bool ok = write(fd, "old", 3u) == 3 && fchmod(fd, mode) == 0;
    return close(fd) == 0 && ok;
}

static bool exists(int dirfd, const char *name) {
    struct stat info;
    return fstatat(dirfd, name, &info, AT_SYMLINK_NOFOLLOW) == 0;
}

static void remove_entries(int dirfd, const char *const *names, size_t count) {
    for (size_t i = 0u; i < count; ++i) (void)unlinkat(dirfd, names[i], 0);
}

static int preserve_mode(void) {
    char root[512];
    REQUIRE(make_root(root, sizeof(root), "save-mode"));
    int dirfd = -1;
    REQUIRE(host_save_io_open_dir(root, &dirfd) == HOST_IO_OK);

    uint8_t image[IMAGE_BYTES];
    for (size_t i = 0u; i < sizeof(image); ++i) image[i] = (uint8_t)(0x66u + i);
    struct stat info;
    int result = 0;

    /* No target yet: owner-only. */
    if (host_save_io_replace(dirfd, "fresh.sav", image, sizeof(image)) != HOST_IO_OK ||
        fstatat(dirfd, "fresh.sav", &info, AT_SYMLINK_NOFOLLOW) != 0 || (info.st_mode & 0777) != 0600)
        result = 1;

    /* An existing target keeps its bits, whether wider or narrower than 0600. */
    static const mode_t modes[] = {0640, 0664, 0644, 0400};
    for (size_t i = 0u; result == 0 && i < sizeof(modes) / sizeof(modes[0]); ++i) {
        if (!put(dirfd, "game.sav", modes[i]) ||
            host_save_io_replace(dirfd, "game.sav", image, sizeof(image)) != HOST_IO_OK ||
            fstatat(dirfd, "game.sav", &info, AT_SYMLINK_NOFOLLOW) != 0 || !S_ISREG(info.st_mode) ||
            (info.st_mode & 0777) != modes[i] || info.st_size != (off_t)sizeof(image))
            result = 1;
        (void)fchmodat(dirfd, "game.sav", 0600, 0); /* so the cleanup below can unlink under any umask */
    }

    static const char *const names[] = {"fresh.sav", "game.sav"};
    remove_entries(dirfd, names, sizeof(names) / sizeof(names[0]));
    (void)close(dirfd);
    (void)rmdir(root);
    REQUIRE(result == 0);
    return 0;
}

/* More than two full batches (the sweep holds 64 names per pass), so a single pass cannot pass. */
#define SWEEP_TEMPS 150
/* More temp-named directories than one batch: the first pass fills up and removes nothing. */
#define SWEEP_STUCK 65

static int sweep_batches_in(int dirfd) {
    char name[64];
    for (int i = 0; i < SWEEP_TEMPS; ++i) {
        (void)snprintf(name, sizeof(name), ".game.sav.tmp-%d-0", 1000 + i);
        REQUIRE(put(dirfd, name, 0600));
    }
    static const char *const kept[] = {"game.sav", ".game.sav", ".other.sav.tmp-1-0", "game.sav.tmp-1-0"};
    for (size_t i = 0u; i < sizeof(kept) / sizeof(kept[0]); ++i) REQUIRE(put(dirfd, kept[i], 0600));

    REQUIRE(host_save_io_sweep(dirfd, "game") == SWEEP_TEMPS);
    for (int i = 0; i < SWEEP_TEMPS; ++i) {
        (void)snprintf(name, sizeof(name), ".game.sav.tmp-%d-0", 1000 + i);
        REQUIRE(!exists(dirfd, name));
    }
    for (size_t i = 0u; i < sizeof(kept) / sizeof(kept[0]); ++i) REQUIRE(exists(dirfd, kept[i]));
    REQUIRE(host_save_io_sweep(dirfd, "game") == 0); /* idempotent */

    /* Nothing removable: the sweep must end, report nothing removed and leave the directories alone. */
    for (int i = 0; i < SWEEP_STUCK; ++i) {
        (void)snprintf(name, sizeof(name), ".stuck.sav.tmp-%d-0", i);
        REQUIRE(mkdirat(dirfd, name, 0700) == 0);
    }
    REQUIRE(host_save_io_sweep(dirfd, "stuck") == 0);
    for (int i = 0; i < SWEEP_STUCK; ++i) {
        (void)snprintf(name, sizeof(name), ".stuck.sav.tmp-%d-0", i);
        REQUIRE(exists(dirfd, name));
    }
    return 0;
}

static int sweep_batches(void) {
    char root[512];
    REQUIRE(make_root(root, sizeof(root), "sweep"));
    int dirfd = -1;
    REQUIRE(host_save_io_open_dir(root, &dirfd) == HOST_IO_OK);
    const int result = sweep_batches_in(dirfd);
    /* Cleanup is best effort and runs whatever the outcome. */
    char name[64];
    for (int i = 0; i < SWEEP_TEMPS; ++i) {
        (void)snprintf(name, sizeof(name), ".game.sav.tmp-%d-0", 1000 + i);
        (void)unlinkat(dirfd, name, 0);
    }
    for (int i = 0; i < SWEEP_STUCK; ++i) {
        (void)snprintf(name, sizeof(name), ".stuck.sav.tmp-%d-0", i);
        (void)unlinkat(dirfd, name, AT_REMOVEDIR);
    }
    static const char *const kept[] = {"game.sav", ".game.sav", ".other.sav.tmp-1-0", "game.sav.tmp-1-0"};
    remove_entries(dirfd, kept, sizeof(kept) / sizeof(kept[0]));
    (void)close(dirfd);
    (void)rmdir(root);
    return result;
}

int main(int argc, char **argv) {
    static const struct { const char *name; int (*run)(void); } cases[] = {
        {"preserve_mode", preserve_mode}, {"sweep_batches", sweep_batches}
    };
    if (argc == 2) {
        for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
            if (strcmp(argv[1], cases[i].name) != 0) continue;
            current_case = cases[i].name;
            if (cases[i].run() != 0) return 1;
            printf("PASS %s\n", cases[i].name);
            return 0;
        }
    }
    fprintf(stderr, "usage: test_host_save_mode preserve_mode|sweep_batches\n");
    return 2;
}
