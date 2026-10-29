#ifndef GBB_HOST_EXIT_H
#define GBB_HOST_EXIT_H

/* The host-mode exit table (Phase 18, D-15), declared once.
 *
 * Host mode emits exactly these codes. Death by signal (SIGKILL, a crash) is the documented crash row of
 * the host contract and has no number here; 3, 4 and 77 belong to other modes of the same executable and
 * are never emitted by host mode. Each row is X(code, IDENT, "name", "meaning"): the enum constant is
 * GBB_HOST_EXIT_<IDENT>, and the lower-case name is what `host_exit_name` and the docs print.
 * Adding a row is additive; renumbering one is a breaking change of the published contract. */

#include <stddef.h>

#define GBB_HOST_EXIT_TABLE(X) \
    X(0, CLEAN, "clean", "Signal or --frames end; the flush succeeded or there was nothing to write") \
    X(1, FAILURE, "failure", "I/O or flush failure, allocation failure, a failed pacing clock, or a core stop mid-run") \
    X(2, REFUSAL, "refusal", "Refused before any save mutation")

enum {
#define GBB_HOST_EXIT_ENUM(code, ident, name, meaning) GBB_HOST_EXIT_##ident = (code),
    GBB_HOST_EXIT_TABLE(GBB_HOST_EXIT_ENUM)
#undef GBB_HOST_EXIT_ENUM
    GBB_HOST_EXIT_END_ = 3
};

/* The row name for a code the host emits, or NULL for any other number. */
static inline const char *host_exit_name(int code) {
    switch (code) {
#define GBB_HOST_EXIT_NAME(code_, ident, name, meaning) case (code_): return (name);
        GBB_HOST_EXIT_TABLE(GBB_HOST_EXIT_NAME)
#undef GBB_HOST_EXIT_NAME
    default: return NULL;
    }
}

#endif
