/* Signal flag and paced wait for host mode (Phase 18, HOST-02, D-03, D-13).
 *
 * Only host mode installs handlers. The handler does nothing but store the signal number into a
 * file-static volatile sig_atomic_t, which is all C17 allows a handler to touch (CERT SIG30-C/SIG31-C);
 * the runner polls the flag at frame boundaries and does every flush, print and free in ordinary code. */
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gbb_host.h"

#include <signal.h>

#ifndef _WIN32
#include <errno.h>
#include <string.h>
#include <time.h>
#endif

/* The adapter's one global. The no-hidden-globals rule governs the core; a signal flag has to be
 * process-wide because a handler has no argument that could carry a context. */
static volatile sig_atomic_t g_host_stop;

const char *host_signal_name(int sig) {
    if (sig == SIGTERM) return "SIGTERM";
    if (sig == SIGINT) return "SIGINT";
#ifdef SIGHUP
    if (sig == SIGHUP) return "SIGHUP";
#endif
    return "SIGNAL";
}

#ifndef _WIN32

static void host_on_signal(int sig) { g_host_stop = sig; }

/* SA_RESETHAND makes a second signal take the default action, so a supervisor that repeats SIGTERM can
 * always kill a wedged process; SA_RESTART keeps unrelated blocking calls from failing with EINTR. */
static int install_handler(int sig) {
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = host_on_signal;
    (void)sigemptyset(&action.sa_mask);
    action.sa_flags = SA_RESTART | SA_RESETHAND;
    return sigaction(sig, &action, NULL);
}

int host_signal_install(void) {
    g_host_stop = 0;
    const int handled[] = {SIGTERM, SIGINT, SIGHUP};
    sigset_t unblock;
    (void)sigemptyset(&unblock);
    for (size_t i = 0u; i < sizeof(handled) / sizeof(handled[0]); ++i) {
        const int sig = handled[i];
        struct sigaction old;
        if (sigaction(sig, NULL, &old) != 0) return -1;
        /* nohup and shells that start background jobs leave SIGINT and SIGHUP ignored on purpose;
         * D-13 honours that. SIGTERM is always handled: it is the supervisor's stop request. */
        if (sig == SIGTERM || old.sa_handler != SIG_IGN) {
            if (install_handler(sig) != 0) return -1;
        }
        (void)sigaddset(&unblock, sig);
    }
    /* A closed stderr pipe must not kill the process in the middle of a flush. */
    struct sigaction ignore;
    memset(&ignore, 0, sizeof(ignore));
    ignore.sa_handler = SIG_IGN;
    (void)sigemptyset(&ignore.sa_mask);
    if (sigaction(SIGPIPE, &ignore, NULL) != 0) return -1;
    /* Handlers first, then unblock, so a signal that was already pending is delivered to a handler. */
    if (sigprocmask(SIG_UNBLOCK, &unblock, NULL) != 0) return -1;
    return 0;
}

int host_signal_stop_requested(void) { return (int)g_host_stop; }

/* One relative nanosleep toward a CLOCK_MONOTONIC deadline. A signal wakes it (EINTR even with
 * SA_RESTART), and it is deliberately NOT retried: the caller polls the stop flag next. macOS has no
 * clock_nanosleep, so the remaining time is computed here and slept relatively (D-03). */
int host_pace_wait(struct timespec *deadline) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return -1;
    const long long second_ns = 1000000000LL;
    const long long remaining =
        ((long long)deadline->tv_sec - (long long)now.tv_sec) * second_ns +
        ((long long)deadline->tv_nsec - (long long)now.tv_nsec);
    if (remaining <= 0) return 0;
    struct timespec pause;
    pause.tv_sec = (time_t)(remaining / second_ns);
    pause.tv_nsec = (long)(remaining % second_ns);
    if (nanosleep(&pause, NULL) == 0) return 0;
    return errno == EINTR ? 1 : -1;
}

#else

/* Windows has no host mode in v0.3 (D-05) and never generates SIGTERM. ISO C stubs keep every target
 * compiling. */
int host_signal_install(void) { return 0; }
int host_signal_stop_requested(void) { return (int)g_host_stop; }
int host_pace_wait(struct timespec *deadline) {
    (void)deadline;
    return 0;
}

#endif
