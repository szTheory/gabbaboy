#include "gbb_accept.h"

#include <string.h>

/* Compiled progress predicates (D-08, D-09), keyed by the pinned ROM digest.
 * No RGBDS or .sym dependency: each address carries its source derivation and
 * ROM anchor bytes, and anchors are verified only after the digest matches.
 * On any Libbet upgrade, re-derive from a rebuilt .sym and replace the row. */

#define LIBBET_SHA256 "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9"
#define CGB_CONTROL_SHA256 "17822873ec8641280d9504229d96850414e872bc90de5431469a498e5271db7e"
#define CGB_CONTROL_COMPAT_SHA256 "6a1d4a1ed58e8a51f3a5be1283a2226775867fc1373b628ecbc798d12d3ca5fc"

static const gbb_accept_predicate libbet_tutorial_cleared = {
    "libbet-tutorial-cleared",
    LIBBET_SHA256,
    {
        [GBB_ACCEPT_ROLE_HW_CAPABILITY] = {
            "hw_capability", 0xC5A3u,
            "src/pads.z80 section ram_pads (WRAM0), hw_capability.",
            0x14FBu, 5, {0xFA, 0xA3, 0xC5, 0x1F, 0x30}},
        [GBB_ACCEPT_ROLE_ATTRACT_MODE] = {
            "attract_mode", 0xC580u,
            "src/main.z80 section mainvars (WRAM0), second variable after cur_floor.",
            0x153Au, 5, {0xE6, 0x04, 0xEA, 0x80, 0xC5}},
        [GBB_ACCEPT_ROLE_CUR_FLOOR] = {
            "cur_floor", 0xC57Fu,
            "src/main.z80 section mainvars (WRAM0), first variable; written by ld [cur_floor],a.",
            0x155Cu, 8, {0xAF, 0xEA, 0x7F, 0xC5, 0xE0, 0x43, 0xE0, 0x42}},
        [GBB_ACCEPT_ROLE_FLOOR_WIDTH] = {
            "floor_width", 0xC4E8u,
            "src/floormodel.z80 section floor_map ALIGN[3]: floor_map ds 64 at 0xC4A8, then "
            "floor_width; anchored by cur_score and cursor_y.",
            0, 0, {0}},
        [GBB_ACCEPT_ROLE_FLOOR_HEIGHT] = {
            "floor_height", 0xC4E9u,
            "src/floormodel.z80 variable order: floor_width, floor_height; anchored by "
            "cur_score and cursor_y.",
            0, 0, {0}},
        [GBB_ACCEPT_ROLE_MAX_SCORE] = {
            "max_score", 0xC4ECu,
            "src/floormodel.z80 variable order: floor_width, floor_height, cursor_x, cursor_y, "
            "max_score, cur_score; anchored by cur_score and cursor_y.",
            0, 0, {0}},
        [GBB_ACCEPT_ROLE_CUR_SCORE] = {
            "cur_score", 0xC4EDu,
            "src/floormodel.z80 section floor_map variable order (cur_score follows max_score); "
            "the anchored sequence zero-stores last_tried_move 0xC592, cur_score 0xC4ED, "
            "move_flags 0xC58D, tracks_since_pause 0xC58E and airrot_amt 0xC590.",
            0x15A6u, 17,
            {0xAF, 0xEA, 0x92, 0xC5, 0xEA, 0xED, 0xC4, 0xEA, 0x8D, 0xC5, 0xEA, 0x8E, 0xC5,
             0xEA, 0x90, 0xC5, 0x3D}},
        [GBB_ACCEPT_ROLE_CURSOR_Y] = {
            "cursor_y", 0xC4EBu,
            "src/floormodel.z80 section floor_map variable order, after cursor_x.",
            0x1680u, 5, {0xFA, 0xEB, 0xC4, 0x3C, 0x20}},
    },
    /* detect_sgb runs from the first boot frames (MLT_REQ over FF00, then a JOYP read); 90 frames
     * is generous for it and still well before the title screen accepts START. */
    90u
};

/* This original harness sets C000 to A5 when ready, then changes C001 once after RIGHT. The two
 * predicates intentionally use the same source-derived state and ROM anchors; the impossible
 * control asks for a value the authored program cannot store. */
static bool cgb_control_progress_eval(gbb_accept_peek_fn peek, void *context, uint8_t expect_hw) {
    (void)expect_hw;
    return peek != NULL && peek(context, 0xC000u) == 0xA5u && peek(context, 0xC001u) == 0x01u;
}

static bool cgb_control_impossible_eval(gbb_accept_peek_fn peek, void *context, uint8_t expect_hw) {
    (void)expect_hw;
    return peek != NULL && peek(context, 0xC000u) == 0xA5u && peek(context, 0xC001u) == 0xFFu;
}

static const gbb_accept_predicate cgb_control_progress = {
    .name = "cgb-control-progress",
    .rom_sha256 = CGB_CONTROL_SHA256,
    .evaluate = cgb_control_progress_eval,
    .observation_policy = GBB_ACCEPT_OBSERVE_PROGRESS_ONLY,
    .source_rows = {
        {"ready", 0xC000u, "Authored SM83 writes A5 to C000 before enabling the LCD.",
         0x15Fu, 8, {0x3E, 0xA5, 0xEA, 0x00, 0xC0, 0xAF, 0xEA, 0x01}},
        {"progress", 0xC001u, "A debounced RIGHT press stores one at C001 exactly once.",
         0x17Cu, 5, {0x3E, 0x01, 0xEA, 0x01, 0xC0}},
        {"right_input", 0x0000u, "Selects direction input and tests active-low RIGHT at JOYP.",
         0x16Cu, 8, {0x3E, 0x20, 0xE0, 0x00, 0xF0, 0x00, 0xCB, 0x47}},
    },
};

static const gbb_accept_predicate cgb_control_impossible = {
    .name = "cgb-control-impossible",
    .rom_sha256 = CGB_CONTROL_SHA256,
    .evaluate = cgb_control_impossible_eval,
    .observation_policy = GBB_ACCEPT_OBSERVE_PROGRESS_ONLY,
    .source_rows = {
        {"ready", 0xC000u, "Authored SM83 writes A5 to C000 before enabling the LCD.",
         0x15Fu, 8, {0x3E, 0xA5, 0xEA, 0x00, 0xC0, 0xAF, 0xEA, 0x01}},
        {"progress", 0xC001u, "A debounced RIGHT press stores one at C001 exactly once.",
         0x17Cu, 5, {0x3E, 0x01, 0xEA, 0x01, 0xC0}},
        {"right_input", 0x0000u, "Selects direction input and tests active-low RIGHT at JOYP.",
         0x16Cu, 8, {0x3E, 0x20, 0xE0, 0x00, 0xF0, 0x00, 0xCB, 0x47}},
    },
};

/* A temporary header variant of the authored control exercises the actual API-reported
 * compatibility-mode refusal. It shares the same executable bytes and source anchors. */
static const gbb_accept_predicate cgb_control_compatibility = {
    .name = "cgb-control-compatibility",
    .rom_sha256 = CGB_CONTROL_COMPAT_SHA256,
    .evaluate = cgb_control_progress_eval,
    .observation_policy = GBB_ACCEPT_OBSERVE_PROGRESS_ONLY,
    .source_rows = {
        {"ready", 0xC000u, "Authored SM83 writes A5 to C000 before enabling the LCD.",
         0x15Fu, 8, {0x3E, 0xA5, 0xEA, 0x00, 0xC0, 0xAF, 0xEA, 0x01}},
        {"progress", 0xC001u, "A debounced RIGHT press stores one at C001 exactly once.",
         0x17Cu, 5, {0x3E, 0x01, 0xEA, 0x01, 0xC0}},
        {"right_input", 0x0000u, "Selects direction input and tests active-low RIGHT at JOYP.",
         0x16Cu, 8, {0x3E, 0x20, 0xE0, 0x00, 0xF0, 0x00, 0xCB, 0x47}},
    },
};

static bool predicate_row_anchor_match(const gbb_accept_predicate_row *row,
                                       const uint8_t *rom, size_t length) {
    if (row->anchor_length == 0) return true;
    if (row->anchor_length > GBB_ACCEPT_ANCHOR_MAX) return false;
    if (row->anchor_offset > length || length - row->anchor_offset < row->anchor_length) return false;
    return memcmp(rom + row->anchor_offset, row->anchor, row->anchor_length) == 0;
}

const gbb_accept_predicate *gbb_accept_predicate_find(const char *name, const char *rom_sha256) {
    if (name == NULL || rom_sha256 == NULL) return NULL;
    if (strcmp(name, libbet_tutorial_cleared.name) == 0 &&
        strcmp(rom_sha256, libbet_tutorial_cleared.rom_sha256) == 0) {
        return &libbet_tutorial_cleared;
    }
    if (strcmp(name, cgb_control_progress.name) == 0 &&
        strcmp(rom_sha256, cgb_control_progress.rom_sha256) == 0) {
        return &cgb_control_progress;
    }
    if (strcmp(name, cgb_control_impossible.name) == 0 &&
        strcmp(rom_sha256, cgb_control_impossible.rom_sha256) == 0) {
        return &cgb_control_impossible;
    }
    if (strcmp(name, cgb_control_compatibility.name) == 0 &&
        strcmp(rom_sha256, cgb_control_compatibility.rom_sha256) == 0) {
        return &cgb_control_compatibility;
    }
    return NULL;
}

bool gbb_accept_predicate_anchors_match(const gbb_accept_predicate *predicate,
                                        const uint8_t *rom, size_t length) {
    if (predicate == NULL || (rom == NULL && length != 0)) return false;
    for (size_t i = 0; i < GBB_ACCEPT_ROLE_COUNT; i++) {
        if (!predicate_row_anchor_match(&predicate->rows[i], rom, length)) return false;
    }
    for (size_t i = 0; i < GBB_ACCEPT_SOURCE_ROW_COUNT; i++) {
        if (!predicate_row_anchor_match(&predicate->source_rows[i], rom, length)) return false;
    }
    return true;
}

bool gbb_accept_predicate_anchors_ok(const gbb_accept_predicate *predicate,
                                     const uint8_t *rom, size_t length) {
    if (predicate == NULL || (rom == NULL && length != 0)) return false;
    char digest[65];
    gbb_accept_sha256_hex(rom, length, digest);
    if (strcmp(digest, predicate->rom_sha256) != 0) return false; /* digest first (D-09) */
    return gbb_accept_predicate_anchors_match(predicate, rom, length);
}

bool gbb_accept_predicate_eval(const gbb_accept_predicate *predicate, gbb_accept_peek_fn peek,
                               void *context, uint8_t expect_hw) {
    if (predicate == NULL || peek == NULL) return false;
    if (predicate->evaluate != NULL) return predicate->evaluate(peek, context, expect_hw);
#define ADDR(role) predicate->rows[role].address
    uint8_t max_score = peek(context, ADDR(GBB_ACCEPT_ROLE_MAX_SCORE));
    return peek(context, ADDR(GBB_ACCEPT_ROLE_HW_CAPABILITY)) == expect_hw &&
           peek(context, ADDR(GBB_ACCEPT_ROLE_ATTRACT_MODE)) == 0 &&
           peek(context, ADDR(GBB_ACCEPT_ROLE_CUR_FLOOR)) == 0 &&
           peek(context, ADDR(GBB_ACCEPT_ROLE_FLOOR_WIDTH)) == 2 &&
           peek(context, ADDR(GBB_ACCEPT_ROLE_FLOOR_HEIGHT)) == 2 &&
           max_score >= 2 &&
           peek(context, ADDR(GBB_ACCEPT_ROLE_CUR_SCORE)) == max_score;
#undef ADDR
}

void gbb_accept_track_init(gbb_accept_track *track) {
    memset(track, 0, sizeof(*track));
}

bool gbb_accept_predicate_track(gbb_accept_track *track, uint64_t boundary_half_dots, bool value) {
    if (track->hit) return true;
    if (value && track->previous_true) {
        track->hit = true;
        track->t_hit = track->previous_time;
        return true;
    }
    track->previous_true = value;
    track->previous_time = boundary_half_dots;
    return false;
}
