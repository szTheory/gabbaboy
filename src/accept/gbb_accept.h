#ifndef GBB_ACCEPT_H
#define GBB_ACCEPT_H

/* Shared acceptance library: SHA-256, the gbinput 1 script parser, the
 * deadline stepper, the replay driver and the compiled progress predicates.
 * Used by the runner and the player smoke so both share one stepping, batching
 * and predicate implementation. No host clock, filesystem or global mutable
 * state is used here; callers own every buffer. */

#include "gabbaboy/gabbaboy.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Time units (D-11) ---- */
#define GBB_ACCEPT_HALF_DOTS_PER_FRAME UINT64_C(140448)   /* 70224 dots */
#define GBB_ACCEPT_HALF_DOTS_PER_SECOND UINT64_C(8388608)
#define GBB_ACCEPT_MAX_SCRIPT_HALF_DOTS UINT64_C(5033164800) /* 600 s */

/* ---- SHA-256 ---- */
typedef struct {
    uint32_t h[8];
    uint64_t bits;
    uint8_t block[64];
    size_t used;
} gbb_accept_sha256_ctx;

void gbb_accept_sha256_init(gbb_accept_sha256_ctx *ctx);
void gbb_accept_sha256_update(gbb_accept_sha256_ctx *ctx, const uint8_t *bytes, size_t length);
/* Writes 64 lowercase hex digits and a NUL. */
void gbb_accept_sha256_final(gbb_accept_sha256_ctx *ctx, char out[65]);
void gbb_accept_sha256_hex(const uint8_t *bytes, size_t length, char out[65]);

/* ---- gbinput 1 script (D-10..D-12) ---- */
#define GBB_ACCEPT_SCRIPT_MAX_BYTES 65536u
#define GBB_ACCEPT_SCRIPT_MAX_LINES 4096u
#define GBB_ACCEPT_SCRIPT_MAX_LINE_BYTES 128u
#define GBB_ACCEPT_SCRIPT_MAX_EVENTS 16384u
#define GBB_ACCEPT_SCRIPT_MAX_LABEL 32u

typedef struct {
    char label[GBB_ACCEPT_SCRIPT_MAX_LABEL + 1u];
    uint64_t at_half_dots;
} gbb_accept_mark;

typedef struct {
    gbb_input_event *events;   /* nondecreasing absolute half-dot times */
    size_t event_count;
    gbb_accept_mark *marks;    /* ascending times */
    size_t mark_count;
    uint64_t end_half_dots;    /* final script cursor */
} gbb_accept_script;

/* Parses completely before returning; on failure *out is left empty (all
 * zero) and nothing was retained. Returns 0 on success, 1 for an invalid
 * script (err receives "invalid-script: line N: <reason>"), 2 when allocation
 * fails. err may be NULL when err_capacity is 0. */
int gbb_accept_script_parse(const uint8_t *bytes, size_t length, gbb_accept_script *out,
                            char *err, size_t err_capacity);
void gbb_accept_script_free(gbb_accept_script *script);

/* ---- Deadline stepper (D-15) ---- */
#define GBB_ACCEPT_PCM_FRAMES 4096u

typedef void (*gbb_accept_pcm_sink)(void *context, const gbb_audio_frame *frames, size_t count);

enum gbb_accept_step_status {
    GBB_ACCEPT_STEP_OK = 0,
    GBB_ACCEPT_STEP_STOPPED,   /* stepper->last_stop carries the reason */
    GBB_ACCEPT_STEP_GUARD      /* iteration guard tripped */
};

typedef struct {
    gbb_instance *instance;
    uint64_t actual_half_dots;   /* sum of consumed half-dots since creation/reset */
    gbb_audio_frame frames[GBB_ACCEPT_PCM_FRAMES];
    gbb_stop_reason last_stop;
    gbb_accept_pcm_sink sink;    /* optional; receives frames from every call */
    void *sink_context;
} gbb_accept_stepper;

/* The instance must be at emulated time zero (fresh or reset). */
void gbb_accept_stepper_init(gbb_accept_stepper *stepper, gbb_instance *instance,
                             gbb_accept_pcm_sink sink, void *sink_context);
/* Advances until the deadline is reached logically. Instructions never start
 * unless they fit, so up to 48 half-dots may be carried and are consumed by
 * the next call, whose budget is computed from the actual instance time. */
enum gbb_accept_step_status gbb_accept_advance_to(gbb_accept_stepper *stepper,
                                                  uint64_t deadline_half_dots);

/* ---- Compiled predicates (D-08, D-09) ---- */
typedef uint8_t (*gbb_accept_peek_fn)(void *context, uint16_t address);

typedef enum {
    GBB_ACCEPT_ROLE_HW_CAPABILITY = 0,
    GBB_ACCEPT_ROLE_ATTRACT_MODE,
    GBB_ACCEPT_ROLE_CUR_FLOOR,
    GBB_ACCEPT_ROLE_FLOOR_WIDTH,
    GBB_ACCEPT_ROLE_FLOOR_HEIGHT,
    GBB_ACCEPT_ROLE_MAX_SCORE,
    GBB_ACCEPT_ROLE_CUR_SCORE,
    GBB_ACCEPT_ROLE_CURSOR_Y,   /* anchor-only provenance row, not evaluated */
    GBB_ACCEPT_ROLE_COUNT
} gbb_accept_role;

#define GBB_ACCEPT_ANCHOR_MAX 20u

typedef struct {
    const char *role_name;
    uint16_t address;
    const char *derivation;
    uint32_t anchor_offset;
    uint8_t anchor_length;       /* 0 when the row has no ROM anchor */
    uint8_t anchor[GBB_ACCEPT_ANCHOR_MAX];
} gbb_accept_predicate_row;

typedef struct {
    const char *name;
    const char *rom_sha256;
    gbb_accept_predicate_row rows[GBB_ACCEPT_ROLE_COUNT];
} gbb_accept_predicate;

/* NULL for an unknown name or a ROM digest other than the pinned one. */
const gbb_accept_predicate *gbb_accept_predicate_find(const char *name, const char *rom_sha256);
/* Checks the ROM digest first and reads no anchor when it differs. */
bool gbb_accept_predicate_anchors_ok(const gbb_accept_predicate *predicate,
                                     const uint8_t *rom, size_t length);
/* Anchor bytes only (bounds-checked), for callers that verified the digest. */
bool gbb_accept_predicate_anchors_match(const gbb_accept_predicate *predicate,
                                        const uint8_t *rom, size_t length);
bool gbb_accept_predicate_eval(const gbb_accept_predicate *predicate, gbb_accept_peek_fn peek,
                               void *context, uint8_t expect_hw);

/* Two-consecutive-boundary rule; t_hit is the first of the two boundaries. */
typedef struct {
    bool previous_true;
    uint64_t previous_time;
    bool hit;
    uint64_t t_hit;
} gbb_accept_track;

void gbb_accept_track_init(gbb_accept_track *track);
/* Feeds one boundary result; returns whether T_hit is now set (sticky). */
bool gbb_accept_predicate_track(gbb_accept_track *track, uint64_t boundary_half_dots, bool value);

/* ---- Replay driver (D-15) ---- */
typedef bool (*gbb_accept_deliver_fn)(void *context, const gbb_input_event *events, size_t count);
typedef void (*gbb_accept_after_step_fn)(void *context, gbb_instance *instance,
                                         uint64_t actual_half_dots);
typedef void (*gbb_accept_boundary_fn)(void *context, gbb_instance *instance,
                                       uint64_t boundary_half_dots, bool predicate_value);

typedef struct {
    gbb_accept_stepper *stepper;
    const gbb_accept_script *script;
    const gbb_accept_predicate *predicate;
    uint8_t expect_hw;
    uint64_t budget_half_dots;
    uint64_t tail_half_dots;     /* emulated time kept running after T_hit */
    size_t max_batch;            /* 1..64 events per delivery */
    gbb_accept_deliver_fn deliver;          /* NULL: gbb_queue_events on the instance */
    gbb_accept_after_step_fn after_step;    /* optional */
    gbb_accept_boundary_fn at_boundary;     /* optional */
    void *context;                          /* passed to every callback */
} gbb_accept_drive_config;

typedef enum {
    GBB_ACCEPT_DRIVE_HIT = 0,
    GBB_ACCEPT_DRIVE_NOT_REACHED,
    GBB_ACCEPT_DRIVE_STOPPED,
    GBB_ACCEPT_DRIVE_GUARD,
    GBB_ACCEPT_DRIVE_DELIVER_FAILED,
    GBB_ACCEPT_DRIVE_INVALID_CONFIG
} gbb_accept_drive_status;

typedef struct {
    gbb_accept_drive_status status;
    uint64_t t_hit_half_dots;    /* valid when status is HIT */
    uint64_t end_half_dots;      /* last logical deadline reached */
    gbb_stop_reason stop_reason; /* valid when status is STOPPED */
} gbb_accept_drive_result;

#define GBB_ACCEPT_TAIL_HALF_DOTS UINT64_C(8388608) /* 1 s after T_hit */

void gbb_accept_drive(const gbb_accept_drive_config *config, gbb_accept_drive_result *result);

/* ---- Canonical frame and PCM digests (D-16, D-24, D-33) ----
 * The frame digest is SHA-256 over the ASCII header below followed by
 * 160x144x3 row-major R,G,B bytes. Shade map: 0->255, 1->170, 2->85, 3->0 on
 * all three channels. The version tag in the header is the migration path for
 * any later container change. Only explicitly serialized byte buffers are
 * hashed, never struct or int16 array memory. */
#define GBB_ACCEPT_RGB_HEADER "GBB-RGB888-v1 160x144\n"
#define GBB_ACCEPT_FRAME_WIDTH 160u
#define GBB_ACCEPT_FRAME_HEIGHT 144u
#define GBB_ACCEPT_FRAME_SHADE_BYTES (GBB_ACCEPT_FRAME_WIDTH * GBB_ACCEPT_FRAME_HEIGHT)

/* shades holds 144 rows of 160 shade bytes spaced pitch bytes apart
 * (pitch >= 160; the caller guarantees (144-1)*pitch+160 readable bytes).
 * Return 0 on success, nonzero when a shade is above 3 (out is then not
 * written). */
int gbb_accept_rgb_digest(const uint8_t *shades, size_t pitch, char out_hex[65]);
int gbb_accept_rgb_digest_bin(const uint8_t *shades, size_t pitch, uint8_t out[32]);
/* Writes a binary P6 PPM of the same pixels with fopen "wb". Returns 0 on
 * success, nonzero when a shade is above 3 (nothing is created) or any open,
 * write or close fails. */
int gbb_accept_write_ppm(const char *path, const uint8_t *shades, size_t pitch);
/* Number of distinct shades (0..4) present in the frame, or 0 for an invalid shade. */
unsigned gbb_accept_frame_distinct_shades(const uint8_t *shades, size_t pitch);

/* Whole-stream PCM digest over little-endian int16 L,R bytes. */
typedef struct {
    gbb_accept_sha256_ctx sha;
} gbb_accept_pcm_digest_ctx;

void gbb_accept_pcm_digest_init(gbb_accept_pcm_digest_ctx *ctx);
void gbb_accept_pcm_digest_feed(gbb_accept_pcm_digest_ctx *ctx, const gbb_audio_frame *frames,
                                size_t count);
void gbb_accept_pcm_digest_final(gbb_accept_pcm_digest_ctx *ctx, char out_hex[65]);

/* Per-channel window statistics (D-16). A change is a sample that differs from
 * the previous sample of the same channel within the window. */
#define GBB_ACCEPT_PCM_MIN_PEAK_TO_PEAK 2048
#define GBB_ACCEPT_PCM_MIN_CHANGES 4800u

typedef struct {
    int16_t min;
    int16_t max;
    int16_t last;
    uint64_t changes;
} gbb_accept_pcm_channel_stats;

typedef struct {
    uint64_t samples;
    gbb_accept_pcm_channel_stats left;
    gbb_accept_pcm_channel_stats right;
} gbb_accept_pcm_stats;

void gbb_accept_pcm_stats_init(gbb_accept_pcm_stats *stats);
void gbb_accept_pcm_stats_feed(gbb_accept_pcm_stats *stats, const gbb_audio_frame *frames,
                               size_t count);
/* max - min for a channel, 0 when no samples were fed. */
int32_t gbb_accept_pcm_peak_to_peak(const gbb_accept_pcm_channel_stats *channel, uint64_t samples);
/* Both channels meet the D-16 thresholds. */
bool gbb_accept_pcm_audible(const gbb_accept_pcm_stats *stats);

#ifdef __cplusplus
}
#endif
#endif
