#ifndef GBB_HOST_H
#define GBB_HOST_H

/* Host-process contract for the headless runner (Phase 18, D-01).
 *
 * This is a conformance adapter, not a play surface: it loads a ROM, imports an
 * exact-size raw `{saveDir}/{stem}.sav`, runs fixed frames and publishes the
 * battery image with an atomic directory-relative writer.
 *
 * The module names no core. It includes only the public API header and libc, so
 * the executable that links it supplies GabbaBoy::core exactly once (D-04).
 * Diagnostics print reason tokens and the stem, never a caller path. */

#include "gabbaboy/gabbaboy.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* One host frame is one fixed gbb_run step (D-03): 70,224 dots at two half-dots each. */
#define GBB_HOST_FRAME_HALF_DOTS UINT64_C(140448)
/* The core's own ROM limit is private (MBC5 types reach 8 MiB), so the host owns this cap. */
#define GBB_HOST_MAX_ROM_BYTES (8u * 1024u * 1024u)
/* 128 KiB of cartridge RAM plus the 21-byte RTC block: the largest raw image the core exports. */
#define GBB_HOST_MAX_SAVE_BYTES (131072u + 21u)
/* The longest stem keeps `.<stem>.sav.tmp-<pid>-<seq>` inside NAME_MAX (255). */
#define GBB_HOST_STEM_MAX_BYTES 200u
#define GBB_HOST_TEMP_RETRIES 16u

/* D-11 cadence, in host frames. A generation change flushes after 16 quiet frames, or once the first
 * unflushed change is 300 frames old; the image is exported and compared every 3,600 frames. */
#define GBB_HOST_QUIET_FRAMES UINT64_C(16)
#define GBB_HOST_MAX_DIRTY_FRAMES UINT64_C(300)
#define GBB_HOST_RTC_COMPARE_FRAMES UINT64_C(3600)

/* D-07: every input has exactly one status; the first matching check decides. */
typedef enum {
    HOST_STEM_OK = 0,
    HOST_STEM_EMPTY,
    HOST_STEM_LEADING_DOT,
    HOST_STEM_CONTROL,
    HOST_STEM_DEL,
    HOST_STEM_BACKSLASH,
    HOST_STEM_BAD_UTF8,
    HOST_STEM_TOO_LONG
} host_stem_status;

/* Derives the save stem from the last component of rom_path. Pure: no filesystem, no allocation.
 * On HOST_STEM_OK the stem is written NUL-terminated into out (cap must be at least
 * GBB_HOST_STEM_MAX_BYTES + 1). On any refusal nothing is written: a stem is validated, never rewritten. */
host_stem_status host_stem(const char *rom_path, char *out, size_t cap);
/* The `stem-*` reason token of a refusal status; "stem-ok" for HOST_STEM_OK. */
const char *host_stem_reason(host_stem_status status);

/* Host I/O codes. Zero is success; every failure is negative so the sign never collides with a count. */
enum {
    HOST_IO_OK = 0,
    HOST_IO_EMISSING = -1,   /* import: the file is absent (a fresh image); open_dir: no such directory */
    HOST_IO_ESYMLINK = -2,
    HOST_IO_ENOTREG = -3,
    HOST_IO_ESIZE = -4,
    HOST_IO_EUNSTABLE = -5,
    HOST_IO_EREAD = -6,
    HOST_IO_ETEMP = -7,      /* replace stages, in order */
    HOST_IO_EWRITE = -8,
    HOST_IO_ESYNC = -9,
    HOST_IO_ECLOSE = -10,
    HOST_IO_ETARGET = -11,
    HOST_IO_ERENAME = -12,
    HOST_IO_EDIRSYNC = -13,  /* the rename happened; only the directory sync failed */
    HOST_IO_ENOTDIR = -14    /* open_dir: the path exists but is not a directory */
};

/* Opens the save directory once with O_RDONLY|O_DIRECTORY|O_CLOEXEC (D-06). Symlinks in the path are
 * resolved into the descriptor. Returns HOST_IO_OK, HOST_IO_EMISSING or HOST_IO_ENOTDIR. */
int host_save_io_open_dir(const char *path, int *out_dirfd);
/* Reads exactly `want` bytes of dirfd/name into buf, which must hold want + 1 bytes (D-08).
 * HOST_IO_EMISSING means the file is absent, which callers treat as a fresh image; every other
 * non-zero code is a refusal. The file is opened without following symlinks and without blocking,
 * must be a regular file of exactly `want` bytes, and must be unchanged after the read. */
int host_save_io_read_exact(int dirfd, const char *name, uint8_t *buf, size_t want);
/* Atomically publishes bytes as dirfd/name (D-09). Old-or-new against process death; prints nothing
 * and preserves errno. The temp name is `.<name>.tmp-<pid>-<seq>`. Frozen signature. */
int host_save_io_replace(int dirfd, const char *name, const uint8_t *bytes, size_t len);
/* Reason token or stage name for a HOST_IO_* code. */
const char *host_io_stage_name(int code);

/* Removes stale temp files left by a crashed writer: every entry of dirfd whose name starts with exactly
 * `.<stem>.sav.tmp-` is unlinked without following links (D-10). Returns the number removed or a negative
 * HOST_IO_* code. Run once, after every refusal check and before the first frame; the contract is one
 * writer per (save dir, stem), so there is no liveness check. */
int host_save_io_sweep(int dirfd, const char *stem);

/* ---- Flush cadence (D-11): a pure state machine, no clock, no I/O ------------------------------- */

typedef enum {
    HOST_CADENCE_NONE = 0,
    HOST_CADENCE_FLUSH,          /* a generation change is due: export, compare, write if different */
    HOST_CADENCE_EXPORT_COMPARE  /* periodic: export and compare, which catches RTC-only drift */
} host_cadence_action;

typedef struct {
    bool dirty;                     /* an unflushed generation change is pending */
    uint64_t observed_generation;   /* the last generation seen, compared with != */
    uint64_t flushed_generation;    /* the generation covered by the last successful flush */
    uint64_t first_dirty_frame;     /* frame of the first unflushed change */
    uint64_t last_change_frame;     /* frame of the latest change */
    uint64_t last_compare_frame;    /* frame of the last successful flush or compare */
    uint64_t retry_after_frame;     /* no action before this frame after a failed flush */
} host_cadence;

void host_cadence_reset(host_cadence *cadence, uint64_t generation, uint64_t frame);
/* Call at every frame boundary with the frame count so far and gbb_battery_generation. */
host_cadence_action host_cadence_step(host_cadence *cadence, uint64_t frame, uint64_t generation);
/* Call only after the writer succeeded (or the compare found the image unchanged). */
void host_cadence_flushed(host_cadence *cadence, uint64_t generation, uint64_t frame);
/* Keeps the image dirty and retries 16 frames later (a recorded D-11 discretion choice). */
void host_cadence_flush_failed(host_cadence *cadence, uint64_t frame);

#ifdef GBB_HOST_TESTING
/* Test builds only (gabbaboy_host_testing): the next call at `stage_code` fails once with errno `err`.
 * `stage_code` is a HOST_IO_* writer stage (ETEMP, EWRITE, ESYNC, ECLOSE, ETARGET, ERENAME, EDIRSYNC). */
void host_save_io_test_fail_next(int stage_code, int err);
/* Number of sync calls made by host_save_io_replace since the process started. */
unsigned host_save_io_test_sync_calls(void);
#endif

/* True when any argument selects host mode: `--rom`, `--save-dir`, or either with `=`.
 * `--help` alone stays in acceptance mode. */
bool gbb_host_is_host_invocation(int argc, char **argv);
/* Runs host mode. Returns 0 on a clean exit, 1 on a core stop or writer failure, 2 on any refusal. */
int gbb_host_main(int argc, char **argv);

#endif
