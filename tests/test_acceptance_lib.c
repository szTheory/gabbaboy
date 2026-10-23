#include "gbb_accept.h"
#include "../src/core/gbb_accept_input.h"

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("PASS %s\n", name); return 0; } while (0)

/* Bounded whole-file read; the caller frees the buffer. */
static uint8_t *read_file(const char *path, size_t capacity, size_t *length) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    uint8_t *buffer = malloc(capacity + 1u);
    if (buffer == NULL) { fclose(f); return NULL; }
    size_t n = fread(buffer, 1, capacity + 1u, f);
    int failed = ferror(f);
    fclose(f);
    if (failed || n > capacity) { free(buffer); return NULL; }
    *length = n;
    return buffer;
}

static int case_libbet_replay(const char *rom_path, const char *script_path) {
    size_t rom_length = 0, script_length = 0;
    uint8_t *rom = read_file(rom_path, 32768u, &rom_length);
    uint8_t *script_bytes = read_file(script_path, GBB_ACCEPT_SCRIPT_MAX_BYTES, &script_length);
    gbb_instance *instance = NULL;
    gbb_accept_script script;
    memset(&script, 0, sizeof(script));
    int rc = 1;
    char digest[65], err[160];
    const gbb_accept_predicate *predicate = NULL;
    gbb_accept_stepper *stepper = NULL;

    if (rom == NULL || script_bytes == NULL) { fprintf(stderr, "cannot read inputs\n"); goto done; }
    gbb_accept_sha256_hex(rom, rom_length, digest);
    predicate = gbb_accept_predicate_find("libbet-tutorial-cleared", digest);
    if (predicate == NULL) { fprintf(stderr, "predicate not bound to ROM %s\n", digest); goto done; }
    if (gbb_accept_script_parse(script_bytes, script_length, &script, err, sizeof(err)) != 0) {
        fprintf(stderr, "%s\n", err);
        goto done;
    }
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) != GBB_OK) goto done;
    if (gbb_load_rom(instance, rom, rom_length) != GBB_OK) goto done;
    stepper = malloc(sizeof(*stepper));
    if (stepper == NULL) goto done;
    gbb_accept_stepper_init(stepper, instance, NULL, NULL);

    gbb_accept_drive_config config;
    memset(&config, 0, sizeof(config));
    config.stepper = stepper;
    config.script = &script;
    config.predicate = predicate;
    config.expect_hw = 0;
    config.budget_half_dots = 3600u * GBB_ACCEPT_HALF_DOTS_PER_FRAME; /* D-13: 3600f */
    config.tail_half_dots = GBB_ACCEPT_TAIL_HALF_DOTS;
    config.max_batch = 32;
    gbb_accept_drive_result result;
    gbb_accept_drive(&config, &result);
    if (result.status != GBB_ACCEPT_DRIVE_HIT) {
        fprintf(stderr, "drive status=%d stop=%d end=%llu\n", (int)result.status,
                (int)result.stop_reason, (unsigned long long)result.end_half_dots);
        goto done;
    }
    printf("lib_replay status=hit t_hit_half_dots=%llu\n", (unsigned long long)result.t_hit_half_dots);
    rc = 0;
done:
    free(stepper);
    gbb_accept_script_free(&script);
    gbb_destroy(instance);
    free(script_bytes);
    free(rom);
    if (rc == 0) printf("PASS acceptance_lib_libbet_replay\n");
    return rc;
}

/* ---- gbinput 1 parser cases (no file I/O, no core instance) ---- */

static int parse_text(const char *text, size_t length, gbb_accept_script *out, char *err, size_t cap) {
    return gbb_accept_script_parse((const uint8_t *)text, length, out, err, cap);
}

static int script_is_empty(const gbb_accept_script *s) {
    return s->events == NULL && s->event_count == 0 && s->marks == NULL && s->mark_count == 0 &&
           s->end_half_dots == 0;
}

/* Rejection must name the right line, carry the reason and leave *out empty. */
static int expect_reject(const char *what, const uint8_t *bytes, size_t length, size_t line,
                         const char *reason) {
    gbb_accept_script s;
    char err[200], want[64];
    memset(&s, 0x5a, sizeof(s)); /* stale contents must be cleared by the parser */
    int rc = gbb_accept_script_parse(bytes, length, &s, err, sizeof(err));
    snprintf(want, sizeof(want), "invalid-script: line %zu: ", line);
    if (rc != 1 || strncmp(err, want, strlen(want)) != 0 || strstr(err, reason) == NULL ||
        !script_is_empty(&s)) {
        fprintf(stderr, "%s: rc=%d err='%s' wanted line %zu reason '%s'\n", what, rc, err, line, reason);
        gbb_accept_script_free(&s);
        return 1;
    }
    return 0;
}

static int expect_accept(const char *what, const uint8_t *bytes, size_t length, size_t events) {
    gbb_accept_script s;
    char err[200];
    int rc = gbb_accept_script_parse(bytes, length, &s, err, sizeof(err));
    if (rc != 0 || s.event_count != events) {
        fprintf(stderr, "%s: rc=%d err='%s' events=%zu wanted %zu\n", what, rc, err, s.event_count, events);
        gbb_accept_script_free(&s);
        return 1;
    }
    gbb_accept_script_free(&s);
    return 0;
}

#define EXPECT_REJECT_TEXT(text, line, reason) \
    REQUIRE(expect_reject(#text, (const uint8_t *)(text), sizeof(text) - 1u, (line), (reason)) == 0)
#define EXPECT_ACCEPT_TEXT(text, events) \
    REQUIRE(expect_accept(#text, (const uint8_t *)(text), sizeof(text) - 1u, (events)) == 0)

/* Builds `lines` lines: "gbinput 1" padded with spaces to `width` bytes
 * (at least 10) including its LF, then `lines - 1` comment lines of `width`
 * bytes each (width 2 is "#\n"). */
static uint8_t *build_lines(size_t lines, size_t width, size_t *length) {
    size_t first = width < 10u ? 10u : width;
    size_t total = first + (lines - 1u) * width;
    uint8_t *b = malloc(total + 1u);
    if (b == NULL) return NULL;
    memset(b, ' ', first - 1u);
    memcpy(b, "gbinput 1", 9);
    b[first - 1u] = '\n';
    for (size_t i = 1; i < lines; i++) {
        uint8_t *line = b + first + (i - 1u) * width;
        memset(line, '#', width - 1u);
        line[width - 1u] = '\n';
    }
    *length = total;
    return b;
}

static int case_parse_bounds(void) {
    size_t n;
    uint8_t *b;

    /* 64 KiB: 512 lines of 128 bytes is exactly 65536; one byte more is rejected. */
    b = build_lines(512, 128, &n);
    REQUIRE(b != NULL && n == 65536u);
    REQUIRE(expect_accept("65536 bytes", b, n, 0) == 0);
    free(b);
    b = build_lines(512, 128, &n);
    REQUIRE(b != NULL);
    uint8_t *big = malloc(n + 1u);
    REQUIRE(big != NULL);
    memcpy(big, b, n);
    big[n] = '\n'; /* 65537 bytes; the extra line is not what is being measured */
    REQUIRE(expect_reject("65537 bytes", big, n + 1u, 0, "exceeds 65536") == 0);
    free(big);
    free(b);

    /* 4096 lines accepted, 4097 rejected on the 4097th. */
    b = build_lines(4096, 2, &n);
    REQUIRE(b != NULL);
    REQUIRE(expect_accept("4096 lines", b, n, 0) == 0);
    free(b);
    b = build_lines(4097, 2, &n);
    REQUIRE(b != NULL);
    REQUIRE(expect_reject("4097 lines", b, n, 4097, "too many lines") == 0);
    free(b);

    /* 128 bytes per line (content, LF/CR excluded) accepted, 129 rejected. */
    uint8_t line128[10 + 128 + 1], line129[10 + 129 + 1];
    memcpy(line128, "gbinput 1\n", 10);
    memset(line128 + 10, '#', 128);
    line128[138] = '\n';
    REQUIRE(expect_accept("128-byte line", line128, 139, 0) == 0);
    memcpy(line129, "gbinput 1\n", 10);
    memset(line129 + 10, '#', 129);
    line129[139] = '\n';
    REQUIRE(expect_reject("129-byte line", line129, 140, 2, "exceeds 128") == 0);
    uint8_t crlf128[10 + 128 + 2];
    memcpy(crlf128, "gbinput 1\n", 10);
    memset(crlf128 + 10, '#', 128);
    crlf128[138] = '\r';
    crlf128[139] = '\n';
    REQUIRE(expect_accept("128-byte CRLF line", crlf128, 140, 0) == 0);

    /* Event cap: every line yields at most two events (tap), so with the
     * 4096-line cap the 16384-event limit is a defensive bound that no valid
     * line count can reach. The densest script is pinned instead. */
    {
        size_t lines = 4096, w = sizeof("tap A 1hd\n") - 1u;
        uint8_t *s = malloc(10 + (lines - 1u) * w);
        REQUIRE(s != NULL);
        memcpy(s, "gbinput 1\n", 10);
        for (size_t i = 1; i < lines; i++) memcpy(s + 10 + (i - 1u) * w, "tap A 1hd\n", w);
        REQUIRE(expect_accept("4095 taps", s, 10 + (lines - 1u) * w, 2u * (lines - 1u)) == 0);
        free(s);
    }

    /* 600 s ceiling with checked arithmetic. */
    EXPECT_ACCEPT_TEXT("gbinput 1\nwait 600s\n", 0);
    EXPECT_ACCEPT_TEXT("gbinput 1\nwait 5033164800hd\n", 0);
    EXPECT_REJECT_TEXT("gbinput 1\nwait 5033164801hd\n", 2, "600 s");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 600s\nwait 1hd\n", 3, "600 s");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 600s\ntap A 1hd\n", 3, "600 s");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 601s\n", 2, "600 s");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 18446744073709551616hd\n", 2, "overflow");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 18446744073709551615hd\n", 2, "600 s");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 2199023255552s\n", 2, "overflow"); /* 2^41 s * 2^23 = 2^64 */
    EXPECT_REJECT_TEXT("gbinput 1\nwait 131072000000f\n", 2, "600 s");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 99999999999999999999999f\n", 2, "overflow");
    PASS("acceptance_parse_script_bounds");
}

static int case_parse_errors(void) {
    EXPECT_REJECT_TEXT("gbinput 1\nwa\0it 1f\n", 2, "NUL");
    EXPECT_REJECT_TEXT("gbinput 1\n# caf\x80\nwait 1f\n", 2, "non-ASCII");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 1f\x7f\n", 2, "non-ASCII");
    EXPECT_REJECT_TEXT("wait 1f\n", 1, "version");
    EXPECT_REJECT_TEXT("", 1, "version");
    EXPECT_REJECT_TEXT("# only a comment\n\n", 2, "version");
    EXPECT_REJECT_TEXT("# c\n\nwait 1f\n", 3, "version");
    EXPECT_REJECT_TEXT("gbinput 2\n", 1, "version");
    EXPECT_REJECT_TEXT("gbinput 1\nfoo 1f\n", 2, "unknown verb");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 1f\ntap a 1f\n", 3, "unknown button");
    EXPECT_REJECT_TEXT("gbinput 1\npress Start\n", 2, "unknown button");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 1x\n", 2, "suffix");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 1\n", 2, "suffix");
    EXPECT_REJECT_TEXT("gbinput 1\nwait f\n", 2, "malformed");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 1.5f\n", 2, "suffix");
    EXPECT_REJECT_TEXT("gbinput 1\nwait -1f\n", 2, "malformed");
    EXPECT_REJECT_TEXT("gbinput 1\nwait\n", 2, "wait takes");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 1f 2f\n", 2, "wait takes");
    EXPECT_REJECT_TEXT("gbinput 1\ntap A 1f 2f\n", 2, "too many");
    EXPECT_REJECT_TEXT("gbinput 1\nmark one\nmark one\n", 3, "duplicate");
    EXPECT_REJECT_TEXT("gbinput 1\nmark Upper\n", 2, "label");
    EXPECT_REJECT_TEXT("gbinput 1\nmark\n", 2, "mark takes");
    EXPECT_REJECT_TEXT("gbinput 1\nmark aaaaaaaaaabbbbbbbbbbccccccccccddd\n", 2, "label");
    EXPECT_REJECT_TEXT("gbinput 1\npress A\npress A\nrelease A\n", 3, "already pressed");
    EXPECT_REJECT_TEXT("gbinput 1\npress A\ntap A 1f\nrelease A\n", 3, "already pressed");
    EXPECT_REJECT_TEXT("gbinput 1\nrelease A\n", 2, "release without press");
    EXPECT_REJECT_TEXT("gbinput 1\npress A\nrelease A\nrelease A\n", 4, "release without press");
    EXPECT_REJECT_TEXT("gbinput 1\nwait 1f\npress B\nwait 2f\n", 3, "still held");
    EXPECT_REJECT_TEXT("gbinput 1\npress UP\npress DOWN\nrelease UP\n", 3, "still held");

    /* Valid forms: comments, blank lines, tabs, trailing comments, no final LF. */
    EXPECT_ACCEPT_TEXT("# header\n\ngbinput 1  # version\n\n  wait\t1f # idle\ntap A 3f\n", 2);
    EXPECT_ACCEPT_TEXT("gbinput 1\npress A\nrelease A", 2);

    /* CRLF yields exactly the LF events and marks. */
    {
        const char lf[] = "gbinput 1\nwait 2f\nmark a\ntap START 3f\nwait 1hd\npress A\nrelease A\nmark b\n";
        const char crlf[] = "gbinput 1\r\nwait 2f\r\nmark a\r\ntap START 3f\r\nwait 1hd\r\npress A\r\nrelease A\r\nmark b\r\n";
        gbb_accept_script a, b;
        char err[160];
        REQUIRE(parse_text(lf, sizeof(lf) - 1u, &a, err, sizeof(err)) == 0);
        REQUIRE(parse_text(crlf, sizeof(crlf) - 1u, &b, err, sizeof(err)) == 0);
        REQUIRE(a.event_count == 4 && b.event_count == 4);
        /* Field-wise: gbb_input_event has padding after kind/value whose bytes are unspecified. */
        for (size_t i = 0; i < 4u; ++i) {
            REQUIRE(a.events[i].at_half_dots == b.events[i].at_half_dots);
            REQUIRE(a.events[i].kind == b.events[i].kind);
            REQUIRE(a.events[i].value == b.events[i].value);
        }
        REQUIRE(a.end_half_dots == b.end_half_dots && a.mark_count == 2 && b.mark_count == 2);
        REQUIRE(a.marks[1].at_half_dots == 5u * GBB_ACCEPT_HALF_DOTS_PER_FRAME + 1u);
        REQUIRE(a.events[0].at_half_dots == 2u * GBB_ACCEPT_HALF_DOTS_PER_FRAME);
        REQUIRE(a.events[0].kind == GBB_INPUT_BUTTON_PRESS && a.events[0].value == GBB_BUTTON_START);
        REQUIRE(a.events[1].kind == GBB_INPUT_BUTTON_RELEASE &&
                a.events[1].at_half_dots == 5u * GBB_ACCEPT_HALF_DOTS_PER_FRAME);
        gbb_accept_script_free(&a);
        gbb_accept_script_free(&b);
    }
    /* A NULL error buffer is allowed with zero capacity. */
    {
        gbb_accept_script s;
        REQUIRE(gbb_accept_script_parse((const uint8_t *)"x\n", 2, &s, NULL, 0) == 1);
        REQUIRE(script_is_empty(&s));
    }
    PASS("acceptance_parse_script_errors");
}

/* ---- Predicate cases ---- */

static uint8_t synthetic_peek(void *context, uint16_t address) {
    return ((const uint8_t *)context)[address];
}

/* Addresses are written literally (D-08), not read from the table under test. */
static void set_play_hit(uint8_t *ram) {
    memset(ram, 0, 0x10000u);
    ram[0xC5A3] = 0x00; /* hw_capability: DMG */
    ram[0xC580] = 0x00; /* attract_mode */
    ram[0xC57F] = 0x00; /* cur_floor */
    ram[0xC4E8] = 2;    /* floor_width */
    ram[0xC4E9] = 2;    /* floor_height */
    ram[0xC4EC] = 4;    /* max_score */
    ram[0xC4ED] = 4;    /* cur_score */
}

static const gbb_accept_predicate *libbet_predicate(void) {
    return gbb_accept_predicate_find("libbet-tutorial-cleared",
                                     "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9");
}

static int case_predicate_truth_table(void) {
    const gbb_accept_predicate *p = libbet_predicate();
    REQUIRE(p != NULL);
    uint8_t *ram = malloc(0x10000u);
    REQUIRE(ram != NULL);

    set_play_hit(ram);
    REQUIRE(gbb_accept_predicate_eval(p, synthetic_peek, ram, 0)); /* play hit */

    /* Title garbage: pseudo-random WRAM must not satisfy the predicate. Rounds 0..6 of every
     * eight start from random WRAM with the seven predicate bytes forced to their play-hit
     * values and then break exactly one clause, so deleting any clause fails some round. Round 7
     * is fully random (the fixed seed makes it deterministic). */
    uint32_t x = 12345u;
    for (unsigned round = 0; round < 64; round++) {
        for (unsigned a = 0xC000u; a < 0xE000u; a++) {
            x = x * 1664525u + 1013904223u;
            ram[a] = (uint8_t)(x >> 24);
        }
        const unsigned clause = round % 8u;
        if (clause != 7u) {
            ram[0xC5A3] = 0x00; ram[0xC580] = 0x00; ram[0xC57F] = 0x00;
            ram[0xC4E8] = 2; ram[0xC4E9] = 2; ram[0xC4EC] = 4; ram[0xC4ED] = 4;
            switch (clause) {
            case 0: ram[0xC5A3] = 0x80; break;               /* hw_capability */
            case 1: ram[0xC580] = 0x04; break;               /* attract_mode */
            case 2: ram[0xC57F] = 0x01; break;               /* cur_floor */
            case 3: ram[0xC4E8] = 3; break;                  /* floor_width */
            case 4: ram[0xC4E9] = 1; break;                  /* floor_height */
            case 5: ram[0xC4EC] = 1; ram[0xC4ED] = 1; break; /* max_score below 2 */
            default: ram[0xC4ED] = 3; break;                 /* cur_score != max_score */
            }
        }
        REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));
    }

    set_play_hit(ram);
    ram[0xC580] = 0x04; ram[0xC4EC] = 4; ram[0xC4ED] = 4; /* attract mode, demo scored 4/4 */
    REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));

    set_play_hit(ram);
    ram[0xC4ED] = 1; /* play not yet scored: 1/4 */
    REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));

    set_play_hit(ram);
    ram[0xC5A3] = 0x80; /* hardware says CGB-capable but the case expects DMG */
    REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));
    REQUIRE(gbb_accept_predicate_eval(p, synthetic_peek, ram, 0x80)); /* per-profile expectation */

    set_play_hit(ram);
    ram[0xC4EC] = 1; ram[0xC4ED] = 1; /* max_score below 2 */
    REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));

    set_play_hit(ram);
    ram[0xC57F] = 1; /* cur_floor != 0 */
    REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));
    set_play_hit(ram);
    ram[0xC4E8] = 3;
    REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));
    set_play_hit(ram);
    ram[0xC4E9] = 1;
    REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));
    set_play_hit(ram);
    ram[0xC4ED] = 5; /* cur_score above max_score */
    REQUIRE(!gbb_accept_predicate_eval(p, synthetic_peek, ram, 0));
    free(ram);

    /* Consecutive rule through the same tracker the driver uses. */
    gbb_accept_track tr;
    gbb_accept_track_init(&tr);
    REQUIRE(!gbb_accept_predicate_track(&tr, 100, true));
    REQUIRE(!gbb_accept_predicate_track(&tr, 200, false)); /* single true then false */
    REQUIRE(!tr.hit);
    REQUIRE(!gbb_accept_predicate_track(&tr, 300, true));
    REQUIRE(gbb_accept_predicate_track(&tr, 400, true));   /* two consecutive */
    REQUIRE(tr.hit && tr.t_hit == 300);                    /* first of the two */
    REQUIRE(gbb_accept_predicate_track(&tr, 500, false));  /* sticky */
    REQUIRE(tr.t_hit == 300);

    /* find() is bound to the name and the pinned digest. */
    REQUIRE(gbb_accept_predicate_find("no-such-predicate",
                "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9") == NULL);
    REQUIRE(gbb_accept_predicate_find("libbet-tutorial-cleared",
                "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a8") == NULL);
    REQUIRE(gbb_accept_predicate_find("libbet-tutorial-cleared", "") == NULL);
    REQUIRE(gbb_accept_predicate_find(NULL, NULL) == NULL);
    PASS("acceptance_predicate_truth_table");
}

static int case_predicate_anchors(const char *rom_path) {
    size_t length = 0;
    uint8_t *rom = read_file(rom_path, 32768u, &length);
    REQUIRE(rom != NULL && length == 32768u);
    char digest[65];
    gbb_accept_sha256_hex(rom, length, digest);
    REQUIRE(strcmp(digest, "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9") == 0);
    const gbb_accept_predicate *p = gbb_accept_predicate_find("libbet-tutorial-cleared", digest);
    REQUIRE(p != NULL);
    REQUIRE(gbb_accept_predicate_anchors_ok(p, rom, length)); /* digest, then all five anchors */

    unsigned anchored = 0;
    for (size_t i = 0; i < GBB_ACCEPT_ROLE_COUNT; i++) anchored += p->rows[i].anchor_length != 0;
    REQUIRE(anchored == 5);

    /* Flipping any anchor byte: rejected by the anchor check itself, and by
     * the digest-first entry point. */
    for (size_t i = 0; i < GBB_ACCEPT_ROLE_COUNT; i++) {
        const gbb_accept_predicate_row *row = &p->rows[i];
        if (row->anchor_length == 0) continue;
        size_t at = row->anchor_offset + row->anchor_length / 2u;
        rom[at] ^= 1u;
        REQUIRE(!gbb_accept_predicate_anchors_match(p, rom, length));
        REQUIRE(!gbb_accept_predicate_anchors_ok(p, rom, length));
        rom[at] ^= 1u;
        REQUIRE(gbb_accept_predicate_anchors_match(p, rom, length));
    }

    /* A changed digest is rejected before any anchor is read: with every
     * anchor intact, a change elsewhere still fails the digest-first check. */
    rom[0x7000] ^= 1u;
    REQUIRE(gbb_accept_predicate_anchors_match(p, rom, length));
    REQUIRE(!gbb_accept_predicate_anchors_ok(p, rom, length));
    rom[0x7000] ^= 1u;
    REQUIRE(gbb_accept_predicate_anchors_ok(p, rom, length));

    /* A truncated image cannot reach an anchor out of bounds. */
    REQUIRE(!gbb_accept_predicate_anchors_match(p, rom, 0x15A6u + 16u));
    REQUIRE(!gbb_accept_predicate_anchors_match(p, NULL, 0));
    free(rom);
    PASS("acceptance_predicate_anchors");
}

static int case_drive_dense_queue(void) {
    size_t rom_length = 0;
    uint8_t *rom = read_file("fixtures/libbet/libbet.gb", 32768u, &rom_length);
    REQUIRE(rom != NULL && rom_length == 32768u);
    char digest[65];
    gbb_accept_sha256_hex(rom, rom_length, digest);
    const gbb_accept_predicate *predicate =
        gbb_accept_predicate_find("libbet-tutorial-cleared", digest);
    REQUIRE(predicate != NULL);

    int failed = 0;
    for (unsigned scenario = 0; scenario < 2u; ++scenario) {
        gbb_input_event events[65];
        for (size_t i = 0; i < sizeof(events) / sizeof(events[0]); ++i) {
            events[i].at_half_dots = scenario == 0u ? 0u : 1u;
            events[i].kind = (i & 1u) == 0u ? GBB_INPUT_BUTTON_PRESS : GBB_INPUT_BUTTON_RELEASE;
            events[i].value = GBB_BUTTON_A;
        }
        gbb_accept_script script;
        memset(&script, 0, sizeof(script));
        script.events = events;
        script.event_count = sizeof(events) / sizeof(events[0]);
        script.end_half_dots = 64u;

        gbb_instance *instance = NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
        REQUIRE(gbb_load_rom(instance, rom, rom_length) == GBB_OK);
        gbb_accept_stepper stepper;
        gbb_accept_stepper_init(&stepper, instance, NULL, NULL);
        gbb_accept_drive_config config;
        memset(&config, 0, sizeof(config));
        config.stepper = &stepper;
        config.script = &script;
        config.predicate = predicate;
        config.budget_half_dots = script.end_half_dots;
        config.max_batch = 64u;
        gbb_accept_drive_result result;
        gbb_accept_drive(&config, &result);
        if (result.status != GBB_ACCEPT_DRIVE_NOT_REACHED ||
            result.end_half_dots != script.end_half_dots ||
            stepper.actual_half_dots > script.end_half_dots ||
            script.end_half_dots - stepper.actual_half_dots > 48u) {
            fprintf(stderr,
                    "dense input scenario=%s status=%d end=%llu actual=%llu; expected logical completion at 64 half-dots with at most 48 half-dots carried\n",
                    scenario == 0u ? "equal-time" : "inside-instruction",
                    (int)result.status, (unsigned long long)result.end_half_dots,
                    (unsigned long long)stepper.actual_half_dots);
            failed = 1;
        }
        gbb_destroy(instance);
    }
    free(rom);
    if (failed) return 1;
    PASS("acceptance_drive_dense_queue");
}

static void make_accept_test_rom(uint8_t rom[32768], const uint8_t *program, size_t program_size) {
    memset(rom, 0, 32768u);
    memcpy(rom + 0x100u, program, program_size);
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14cu; ++i) checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14du] = checksum;
}

typedef struct {
    size_t calls;
    size_t delivered;
    gbb_instance *instance;
} delivery_stats;

static bool deliver_and_count(void *context, const gbb_input_event *events, size_t count) {
    delivery_stats *stats = (delivery_stats *)context;
    stats->calls++;
    stats->delivered += count;
    return gbb_queue_events(stats->instance, events, count) == GBB_OK;
}

static bool reject_delivery(void *context, const gbb_input_event *events, size_t count) {
    (void)events;
    (void)count;
    ((delivery_stats *)context)->calls++;
    return false;
}

static int case_accept_drive_batch_order(void) {
    static const uint8_t program[] = {
        0x3e,0x00,0xe0,0x01, 0x3e,0x80,0xe0,0x02,
        0xf0,0x01,0xea,0x00,0xc0, 0xf0,0x02,0xea,0x01,0xc0,
        0xf0,0x0f,0xea,0x02,0xc0
    };
    uint8_t rom[32768];
    make_accept_test_rom(rom, program, sizeof(program));
    gbb_input_event edges[8];
    static const uint8_t bits[8] = {1u,0u,1u,0u,0u,1u,0u,1u};
    for (size_t i = 0; i < 8u; ++i)
        edges[i] = (gbb_input_event){80u, GBB_INPUT_SERIAL_EDGE, bits[i]};

    for (size_t pass = 0; pass < 2u; ++pass) {
        gbb_instance *instance = NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
        REQUIRE(gbb_load_rom(instance, rom, sizeof(rom)) == GBB_OK);
        gbb_run_result started = gbb_run(instance, 80u, NULL, 0u);
        REQUIRE(started.reason == GBB_STOP_BUDGET && started.consumed_half_dots == 80u);

        gbb_accept_script script;
        memset(&script, 0, sizeof(script));
        script.events = edges;
        script.event_count = sizeof(edges) / sizeof(edges[0]);
        script.end_half_dots = 248u;
        gbb_accept_stepper stepper;
        gbb_accept_stepper_init(&stepper, instance, NULL, NULL);
        stepper.actual_half_dots = 80u;
        gbb_accept_predicate predicate;
        memset(&predicate, 0, sizeof(predicate));
        delivery_stats stats = {0u, 0u, instance};
        gbb_accept_drive_config config;
        memset(&config, 0, sizeof(config));
        config.stepper = &stepper;
        config.script = &script;
        config.predicate = &predicate;
        config.budget_half_dots = script.end_half_dots;
        config.max_batch = pass == 0u ? 1u : 64u;
        config.deliver = deliver_and_count;
        config.context = &stats;
        gbb_accept_drive_result result;
        gbb_accept_drive(&config, &result);
        if (result.status != GBB_ACCEPT_DRIVE_NOT_REACHED || result.end_half_dots != 248u ||
            stats.delivered != 8u || stats.calls != (pass == 0u ? 8u : 1u) ||
            gbb_peek_ram(instance, 0xc000u) != 0xa5u ||
            (gbb_peek_ram(instance, 0xc001u) & 0x80u) != 0u ||
            (gbb_peek_ram(instance, 0xc002u) & 0x08u) == 0u) {
            fprintf(stderr, "batch replay batch=%zu status=%d calls=%zu delivered=%zu ram=%02x/%02x/%02x\n",
                    config.max_batch, (int)result.status, stats.calls, stats.delivered,
                    gbb_peek_ram(instance, 0xc000u), gbb_peek_ram(instance, 0xc001u),
                    gbb_peek_ram(instance, 0xc002u));
            gbb_destroy(instance);
            return 1;
        }
        gbb_destroy(instance);
    }
    PASS("acceptance_drive_batch_order");
}

static int case_accept_drive_stop_guard_failure(void) {
    static const uint8_t stop_program[] = {0x10,0x00,0x00,0x18,0xfe};
    uint8_t rom[32768];
    make_accept_test_rom(rom, stop_program, sizeof(stop_program));
    gbb_instance *instance = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, sizeof(rom)) == GBB_OK);
    gbb_accept_predicate predicate;
    memset(&predicate, 0, sizeof(predicate));
    gbb_accept_stepper stepper;
    gbb_accept_stepper_init(&stepper, instance, NULL, NULL);

    gbb_input_event wake = {20u, GBB_INPUT_STOP_WAKE, 1u};
    gbb_accept_script script;
    memset(&script, 0, sizeof(script));
    script.events = &wake;
    script.event_count = 1u;
    script.end_half_dots = 64u;
    gbb_accept_drive_config config;
    memset(&config, 0, sizeof(config));
    config.stepper = &stepper;
    config.script = &script;
    config.predicate = &predicate;
    config.max_batch = 64u;
    config.budget_half_dots = script.end_half_dots;
    gbb_accept_drive_result result;
    gbb_accept_drive(&config, &result);
    REQUIRE(result.status == GBB_ACCEPT_DRIVE_NOT_REACHED && result.end_half_dots == 64u);
    REQUIRE(stepper.actual_half_dots >= wake.at_half_dots && stepper.last_stop == GBB_STOP_BUDGET);

    /* A stopped guest with 1,992 non-waking deadlines inside a short replay
     * deadline forces the stepper's iteration guard without a mock core. */
    REQUIRE(gbb_reset(instance) == GBB_OK);
    gbb_input_event deadlines[2000];
    for (size_t i = 0; i < sizeof(deadlines) / sizeof(deadlines[0]); ++i) {
        deadlines[i].at_half_dots = 8u + i;
        deadlines[i].kind = (i & 1u) == 0u ? GBB_INPUT_BUTTON_PRESS : GBB_INPUT_BUTTON_RELEASE;
        deadlines[i].value = GBB_BUTTON_A;
    }
    script.events = deadlines;
    script.event_count = sizeof(deadlines) / sizeof(deadlines[0]);
    script.end_half_dots = 2000u;
    gbb_accept_stepper_init(&stepper, instance, NULL, NULL);
    config.budget_half_dots = script.end_half_dots;
    gbb_accept_drive(&config, &result);
    if (result.status != GBB_ACCEPT_DRIVE_GUARD || result.stop_reason != GBB_STOP_STOPPED ||
        stepper.actual_half_dots <= 8u || stepper.actual_half_dots >= script.end_half_dots) {
        fprintf(stderr, "guard replay status=%d stop=%d actual=%llu end=%llu\n", (int)result.status,
                (int)result.stop_reason, (unsigned long long)stepper.actual_half_dots,
                (unsigned long long)result.end_half_dots);
        gbb_destroy(instance);
        return 1;
    }
    gbb_destroy(instance);

    /* Delivery failure must stop before stepping and remain distinguishable
     * from successful or stopped replay results. */
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, sizeof(rom)) == GBB_OK);
    gbb_input_event event = {0u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A};
    script.events = &event;
    script.event_count = 1u;
    script.end_half_dots = 64u;
    gbb_accept_stepper_init(&stepper, instance, NULL, NULL);
    memset(&config, 0, sizeof(config));
    config.stepper = &stepper;
    config.script = &script;
    config.predicate = &predicate;
    config.max_batch = 1u;
    config.budget_half_dots = script.end_half_dots;
    delivery_stats stats = {0u, 0u, instance};
    config.deliver = reject_delivery;
    config.context = &stats;
    gbb_accept_drive(&config, &result);
    REQUIRE(result.status == GBB_ACCEPT_DRIVE_DELIVER_FAILED && result.end_half_dots == 0u);
    REQUIRE(stats.calls == 1u && stepper.actual_half_dots == 0u);
    gbb_destroy(instance);
    PASS("acceptance_drive_stop_guard_failure");
}

static int case_accept_input_span_edges(void) {
    size_t rom_length = 0;
    uint8_t *rom = read_file("fixtures/libbet/libbet.gb", 32768u, &rom_length);
    REQUIRE(rom != NULL && rom_length == 32768u);
    gbb_audio_frame frames[GBB_ACCEPT_PCM_FRAMES];

    static const size_t event_counts[] = {0u, 1u, 63u, 64u, 65u};
    for (size_t c = 0; c < sizeof(event_counts) / sizeof(event_counts[0]); ++c) {
        gbb_input_event events[65];
        const size_t count = event_counts[c];
        for (size_t i = 0; i < count; ++i) {
            events[i].at_half_dots = 0u;
            events[i].kind = (i & 1u) == 0u ? GBB_INPUT_BUTTON_PRESS : GBB_INPUT_BUTTON_RELEASE;
            events[i].value = GBB_BUTTON_A;
        }

        gbb_instance *instance = NULL;
        REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
        REQUIRE(gbb_load_rom(instance, rom, rom_length) == GBB_OK);
        size_t cursor = 0u, frame_count = 99u;
        gbb_accept_input_span span = {events, count, &cursor};
        gbb_run_result result = gbb_accept_run_audio(instance, 0u, &span, NULL, 0u, &frame_count);
        REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 0u);
        REQUIRE(cursor == 0u && frame_count == 0u);

        result = gbb_accept_run_audio(instance, 64u, &span, frames, GBB_ACCEPT_PCM_FRAMES, &frame_count);
        if (result.reason != GBB_STOP_BUDGET || result.consumed_half_dots == 0u ||
            result.consumed_half_dots > 64u || cursor != count) {
            fprintf(stderr, "span edge count=%zu reason=%d consumed=%llu cursor=%zu\n", count,
                    (int)result.reason, (unsigned long long)result.consumed_half_dots, cursor);
            gbb_destroy(instance);
            free(rom);
            return 1;
        }

        /* A later public run and a new private borrow prove the prior cursor was
         * not retained in the opaque instance after return. */
        result = gbb_run(instance, 0u, NULL, 0u);
        REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 0u);
        size_t empty_cursor = 0u;
        const gbb_accept_input_span empty = {NULL, 0u, &empty_cursor};
        result = gbb_accept_run_audio(instance, 0u, &empty, NULL, 0u, &frame_count);
        REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots == 0u);
        REQUIRE(empty_cursor == 0u);
        gbb_destroy(instance);
    }

    /* A malformed span and a span mixed with the public queue are rejected
     * before either the guest or caller cursor changes. */
    gbb_instance *instance = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, rom_length) == GBB_OK);
    gbb_input_event unordered[] = {
        {8u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A},
        {7u, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A}
    };
    size_t cursor = 0u, frame_count = 0u;
    gbb_accept_input_span invalid_span = {unordered, 2u, &cursor};
    gbb_run_result result = gbb_accept_run_audio(instance, 32u, &invalid_span, frames,
                                                 GBB_ACCEPT_PCM_FRAMES, &frame_count);
    REQUIRE(result.reason == GBB_STOP_INVALID_STATE && result.consumed_half_dots == 0u && cursor == 0u);

    const gbb_input_event queued = {0u, GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A};
    REQUIRE(gbb_queue_events(instance, &queued, 1u) == GBB_OK);
    gbb_input_event span_event = {0u, GBB_INPUT_BUTTON_RELEASE, GBB_BUTTON_A};
    gbb_accept_input_span mixed_span = {&span_event, 1u, &cursor};
    result = gbb_accept_run_audio(instance, 32u, &mixed_span, frames, GBB_ACCEPT_PCM_FRAMES, &frame_count);
    REQUIRE(result.reason == GBB_STOP_INVALID_STATE && result.consumed_half_dots == 0u && cursor == 0u);
    result = gbb_run(instance, 32u, NULL, 0u);
    REQUIRE(result.reason == GBB_STOP_BUDGET && result.consumed_half_dots > 0u &&
            result.consumed_half_dots <= 32u);
    gbb_destroy(instance);
    free(rom);
    PASS("acceptance_input_span_edges");
}

static int case_accept_drive_stop_wake_deadline(void) {
    static const uint8_t stop_program[] = {0x10,0x00,0x00,0x18,0xfe};
    uint8_t rom[32768];
    make_accept_test_rom(rom, stop_program, sizeof(stop_program));
    gbb_instance *instance = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, sizeof(rom)) == GBB_OK);

    gbb_input_event wake = {100u, GBB_INPUT_STOP_WAKE, 1u};
    gbb_accept_script script;
    memset(&script, 0, sizeof(script));
    script.events = &wake;
    script.event_count = 1u;
    script.end_half_dots = 100u;
    gbb_accept_stepper stepper;
    gbb_accept_stepper_init(&stepper, instance, NULL, NULL);
    gbb_accept_predicate predicate;
    memset(&predicate, 0, sizeof(predicate));
    gbb_accept_drive_config config;
    memset(&config, 0, sizeof(config));
    config.stepper = &stepper;
    config.script = &script;
    config.predicate = &predicate;
    config.budget_half_dots = script.end_half_dots;
    config.max_batch = 64u;
    gbb_accept_drive_result driven;
    gbb_accept_drive(&config, &driven);
    if (driven.status != GBB_ACCEPT_DRIVE_NOT_REACHED || driven.end_half_dots != 100u ||
        driven.stop_reason != GBB_STOP_BUDGET || stepper.actual_half_dots != 100u) {
        fprintf(stderr, "wake-at-deadline status=%d stop=%d end=%llu actual=%llu\n",
                (int)driven.status, (int)driven.stop_reason,
                (unsigned long long)driven.end_half_dots,
                (unsigned long long)stepper.actual_half_dots);
        gbb_destroy(instance);
        return 1;
    }
    gbb_run_result next_tick = gbb_run(instance, 48u, NULL, 0u);
    REQUIRE(next_tick.reason != GBB_STOP_STOPPED && next_tick.consumed_half_dots != 0u);
    gbb_destroy(instance);

    /* A wake at the final half-dot of the first private run must complete that
     * budget, and explicit continuation must execute the next CPU tick. */
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, sizeof(rom)) == GBB_OK);
    size_t cursor = 0u, frame_count = 0u;
    const gbb_accept_input_span span = {&wake, 1u, &cursor};
    gbb_audio_frame frames[GBB_ACCEPT_PCM_FRAMES];
    gbb_run_result first = gbb_run(instance, 99u, NULL, 0u);
    if (first.reason != GBB_STOP_STOPPED || first.consumed_half_dots >= 99u || cursor != 0u) {
        fprintf(stderr, "stop setup reason=%d consumed=%llu cursor=%zu\n", (int)first.reason,
                (unsigned long long)first.consumed_half_dots, cursor);
        gbb_destroy(instance);
        return 1;
    }
    gbb_run_result boundary = gbb_accept_run_audio(instance, 100u - first.consumed_half_dots,
                                                    &span, frames,
                                                    GBB_ACCEPT_PCM_FRAMES, &frame_count);
    REQUIRE(boundary.reason == GBB_STOP_BUDGET &&
            boundary.consumed_half_dots == 100u - first.consumed_half_dots && cursor == 1u);
    next_tick = gbb_run(instance, 48u, NULL, 0u);
    REQUIRE(next_tick.reason != GBB_STOP_STOPPED && next_tick.consumed_half_dots != 0u);
    gbb_destroy(instance);

    /* Without a due wake the guest remains stopped, including after a zero
     * budget poll; a later positive budget reports STOPPED, not a wake. */
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, sizeof(rom)) == GBB_OK);
    memset(&script, 0, sizeof(script));
    script.end_half_dots = 100u;
    gbb_accept_stepper_init(&stepper, instance, NULL, NULL);
    config.script = &script;
    config.stepper = &stepper;
    config.budget_half_dots = 100u;
    gbb_accept_drive(&config, &driven);
    if (driven.status != GBB_ACCEPT_DRIVE_STOPPED || driven.stop_reason != GBB_STOP_STOPPED) {
        fprintf(stderr, "no-wake status=%d stop=%d end=%llu actual=%llu\n", (int)driven.status,
                (int)driven.stop_reason, (unsigned long long)driven.end_half_dots,
                (unsigned long long)stepper.actual_half_dots);
        gbb_destroy(instance);
        return 1;
    }
    gbb_run_result zero = gbb_run(instance, 0u, NULL, 0u);
    REQUIRE(zero.reason == GBB_STOP_BUDGET && zero.consumed_half_dots == 0u);
    gbb_run_result still_stopped = gbb_run(instance, 16u, NULL, 0u);
    REQUIRE(still_stopped.reason == GBB_STOP_STOPPED && still_stopped.consumed_half_dots == 16u);
    gbb_destroy(instance);
    PASS("acceptance_drive_stop_wake_deadline");
}

static uintptr_t align_test_address(uintptr_t address, size_t alignment) {
    const size_t remainder = (size_t)(address % alignment);
    return remainder == 0u ? address : address + alignment - remainder;
}

static int span_alias_was_rejected(const char *name, gbb_run_result result,
                                   const gbb_accept_input_span *span, size_t count_before,
                                   size_t cursor_before, const gbb_input_event *events,
                                   const gbb_input_event *saved_events, size_t event_count) {
    if (result.reason != GBB_STOP_INVALID_STATE || result.consumed_half_dots != 0u ||
        span->count != count_before || *span->cursor != cursor_before ||
        memcmp(events, saved_events, event_count * sizeof(*events)) != 0) {
        fprintf(stderr, "span-output alias=%s reason=%d consumed=%llu count=%zu cursor=%zu\n",
                name, (int)result.reason, (unsigned long long)result.consumed_half_dots,
                span->count, *span->cursor);
        return 0;
    }
    return 1;
}

/* Number of span_alias_was_rejected sub-cases in case_accept_input_span_output_alias. The printed
 * rejected=N/M line derives M from this constant, and the output_alias mutant regex in
 * tests/acceptance/CMakeLists.txt matches it, so the denominator cannot drift from the sub-case count. */
enum { SPAN_OUTPUT_ALIAS_CASES = 12 };

static int case_accept_input_span_output_alias(void) {
    const size_t storage_size = 4096u;
    uint8_t *storage = malloc(storage_size);
    REQUIRE(storage != NULL);
    gbb_accept_input_span *span = (gbb_accept_input_span *)(void *)(storage + 128u);
    size_t *cursor = (size_t *)(void *)(storage + 256u);
    gbb_input_event *events = (gbb_input_event *)(void *)(storage + 1024u);
    gbb_input_event saved_events[4];
    for (size_t i = 0; i < 4u; ++i) {
        events[i] = (gbb_input_event){8u, (i & 1u) == 0u ? GBB_INPUT_BUTTON_PRESS : GBB_INPUT_BUTTON_RELEASE,
                                     GBB_BUTTON_A};
    }
    memcpy(saved_events, events, sizeof(saved_events));
    *cursor = 0u;
    *span = (gbb_accept_input_span){events, 4u, cursor};

    uint8_t rom[32768];
    static const uint8_t loop_program[] = {0x18,0xfe};
    make_accept_test_rom(rom, loop_program, sizeof(loop_program));
    gbb_instance *instance = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, sizeof(rom)) == GBB_OK);
    gbb_audio_frame *partial_frame = (gbb_audio_frame *)(void *)align_test_address(
        (uintptr_t)(void *)(events + 1u) + offsetof(gbb_input_event, kind), _Alignof(gbb_audio_frame));
    gbb_trace_record *partial_trace = (gbb_trace_record *)(void *)align_test_address(
        (uintptr_t)(void *)(events + 1u) + offsetof(gbb_input_event, kind), _Alignof(gbb_trace_record));
    gbb_diagnostic_record *partial_diagnostic = (gbb_diagnostic_record *)(void *)align_test_address(
        (uintptr_t)(void *)(events + 1u) + offsetof(gbb_input_event, kind), _Alignof(gbb_diagnostic_record));
    REQUIRE((uintptr_t)(void *)partial_frame < (uintptr_t)(void *)(events + 2u));
    REQUIRE((uintptr_t)(void *)partial_trace < (uintptr_t)(void *)(events + 2u));
    REQUIRE((uintptr_t)(void *)partial_diagnostic < (uintptr_t)(void *)(events + 2u));

    int failures = 0;        /* the valid zero-budget span check */
    int alias_failures = 0;  /* span_alias_was_rejected sub-cases */
    const uint64_t alias_budget = 32u;
    size_t frame_count = 7u;
    gbb_run_result result = gbb_accept_run_audio(instance, alias_budget, span, partial_frame, 1u, &frame_count);
    if (!span_alias_was_rejected("partial-frame/events", result, span, 4u, 0u,
                                 events, saved_events, 4u) || frame_count != 0u) ++alias_failures;

    frame_count = 7u;
    result = gbb_accept_run_audio(instance, alias_budget, span, (gbb_audio_frame *)(void *)span, 1u, &frame_count);
    if (!span_alias_was_rejected("frame/span-descriptor", result, span, 4u, 0u,
                                 events, saved_events, 4u) || frame_count != 0u) ++alias_failures;

    *cursor = 1u;
    result = gbb_accept_run_audio(instance, alias_budget, span, NULL, 0u, cursor);
    if (!span_alias_was_rejected("frame-count/cursor", result, span, 4u, 1u,
                                 events, saved_events, 4u)) ++alias_failures;
    *cursor = 0u;

    result = gbb_accept_run_audio(instance, alias_budget, span, NULL, 0u, &span->count);
    if (!span_alias_was_rejected("frame-count/span-descriptor", result, span, 4u, 0u,
                                 events, saved_events, 4u)) ++alias_failures;
    span->count = 4u;

    size_t *count_in_events = (size_t *)(void *)align_test_address((uintptr_t)(void *)(events + 1u),
                                                                   _Alignof(size_t));
    REQUIRE((uintptr_t)(void *)count_in_events + sizeof(*count_in_events) <= (uintptr_t)(void *)(events + 4u));
    result = gbb_accept_run_audio(instance, alias_budget, span, NULL, 0u, count_in_events);
    if (!span_alias_was_rejected("frame-count/events", result, span, 4u, 0u,
                                 events, saved_events, 4u)) ++alias_failures;

    /* The span itself is invalid (cursor above count), so validate_accept_input_span rejects it; the count
     * aliases the cursor and must still not be written. */
    *cursor = 5u;
    result = gbb_accept_run_audio(instance, alias_budget, span, NULL, 0u, cursor);
    if (!span_alias_was_rejected("frame-count/unvalidated-cursor", result, span, 4u, 5u,
                                 events, saved_events, 4u)) ++alias_failures;
    *cursor = 0u;

    result = gbb_accept_run_diagnostic(instance, alias_budget, span, partial_trace, 1u, NULL, 0u);
    if (!span_alias_was_rejected("partial-trace/events", result, span, 4u, 0u,
                                 events, saved_events, 4u)) ++alias_failures;
    result = gbb_accept_run_diagnostic(instance, alias_budget, span,
                                       (gbb_trace_record *)(void *)cursor, 1u, NULL, 0u);
    if (!span_alias_was_rejected("trace/cursor", result, span, 4u, 0u,
                                 events, saved_events, 4u)) ++alias_failures;
    result = gbb_accept_run_diagnostic(instance, alias_budget, span,
                                       (gbb_trace_record *)(void *)span, 1u, NULL, 0u);
    if (!span_alias_was_rejected("trace/span-descriptor", result, span, 4u, 0u,
                                 events, saved_events, 4u)) ++alias_failures;

    result = gbb_accept_run_diagnostic(instance, alias_budget, span, NULL, 0u, partial_diagnostic, 1u);
    if (!span_alias_was_rejected("partial-diagnostic/events", result, span, 4u, 0u,
                                 events, saved_events, 4u)) ++alias_failures;
    result = gbb_accept_run_diagnostic(instance, alias_budget, span, NULL, 0u,
                                       (gbb_diagnostic_record *)(void *)cursor, 1u);
    if (!span_alias_was_rejected("diagnostic/cursor", result, span, 4u, 0u,
                                 events, saved_events, 4u)) ++alias_failures;
    result = gbb_accept_run_diagnostic(instance, alias_budget, span, NULL, 0u,
                                       (gbb_diagnostic_record *)(void *)span, 1u);
    if (!span_alias_was_rejected("diagnostic/span-descriptor", result, span, 4u, 0u,
                                 events, saved_events, 4u)) ++alias_failures;

    gbb_audio_frame frames[GBB_ACCEPT_PCM_FRAMES];
    frame_count = 7u;
    result = gbb_accept_run_audio(instance, 0u, span, frames, GBB_ACCEPT_PCM_FRAMES, &frame_count);
    if (result.reason != GBB_STOP_BUDGET || result.consumed_half_dots != 0u ||
        frame_count != 0u || *cursor != 0u || span->count != 4u) {
        fprintf(stderr, "valid zero-budget span reason=%d consumed=%llu cursor=%zu count=%zu frames=%zu\n",
                (int)result.reason, (unsigned long long)result.consumed_half_dots,
                *cursor, span->count, frame_count);
        ++failures;
    }

    gbb_destroy(instance);
    free(storage);
    if (alias_failures != 0) {
        fprintf(stderr, "span-output alias rejected=%d/%d\n", SPAN_OUTPUT_ALIAS_CASES - alias_failures,
                SPAN_OUTPUT_ALIAS_CASES);
    }
    if (failures != 0 || alias_failures != 0) return 1;
    PASS("acceptance_input_span_output_alias");
}

/* ---- WR-03: the diagnostic replay and the main stepper share one STOP-resume rule ---- */

typedef struct {
    const char *name;
    gbb_input_event events[3];
    size_t count;
    int null_span;                          /* run without a borrowed span */
    enum gbb_accept_step_status status;     /* expected in both paths */
    size_t cursor;                          /* expected diagnostic-path cursor */
    int woke;                               /* guest left STOP by the end of the window */
} stop_parity_case;

typedef struct {
    enum gbb_accept_step_status status;
    uint64_t actual;
    int woke;
} stop_parity_run;

static int guest_left_stop(gbb_instance *instance) {
    gbb_run_result next = gbb_run(instance, 48u, NULL, 0u);
    return next.reason != GBB_STOP_STOPPED && next.consumed_half_dots != 0u;
}

/* The main path. The drive keeps its event cursor private, so the delivered events are observed
 * through the guest: the wake only reaches it when the cursor passed the wake event. */
static int stop_parity_main(const uint8_t *rom, const stop_parity_case *pc, uint64_t end,
                            stop_parity_run *out) {
    gbb_instance *instance = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, 32768u) == GBB_OK);
    gbb_accept_stepper stepper;
    gbb_accept_stepper_init(&stepper, instance, NULL, NULL);
    if (pc->null_span) {
        out->status = gbb_accept_advance_to(&stepper, end);
    } else {
        gbb_input_event events[3];
        memcpy(events, pc->events, sizeof(events));
        gbb_accept_script script;
        memset(&script, 0, sizeof(script));
        script.events = pc->count != 0u ? events : NULL;
        script.event_count = pc->count;
        script.end_half_dots = end;
        gbb_accept_predicate predicate;
        memset(&predicate, 0, sizeof(predicate));
        gbb_accept_drive_config config;
        memset(&config, 0, sizeof(config));
        config.stepper = &stepper;
        config.script = &script;
        config.predicate = &predicate;
        config.budget_half_dots = end;
        config.max_batch = 64u;
        gbb_accept_drive_result driven;
        gbb_accept_drive(&config, &driven);
        out->status = driven.status == GBB_ACCEPT_DRIVE_NOT_REACHED ? GBB_ACCEPT_STEP_OK
                    : driven.status == GBB_ACCEPT_DRIVE_STOPPED ? GBB_ACCEPT_STEP_STOPPED
                                                                : GBB_ACCEPT_STEP_GUARD;
    }
    out->actual = stepper.actual_half_dots;
    out->woke = guest_left_stop(instance);
    gbb_destroy(instance);
    return 0;
}

static int stop_parity_diag_origin(const uint8_t *rom, const stop_parity_case *pc, uint64_t end,
                                   uint64_t origin, stop_parity_run *out, size_t *cursor_out) {
    gbb_instance *instance = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, 32768u) == GBB_OK);
    size_t cursor = 0u;
    const gbb_accept_input_span span = {pc->count != 0u ? pc->events : NULL, pc->count, &cursor};
    uint64_t actual = 0u;
    out->status = gbb_accept_diag_advance(instance, &actual, end, pc->null_span ? NULL : &span,
                                          NULL, 0u, NULL, 0u, NULL, NULL, origin);
    out->actual = actual;
    *cursor_out = cursor;
    out->woke = guest_left_stop(instance);
    gbb_destroy(instance);
    return 0;
}

static int stop_parity_diag(const uint8_t *rom, const stop_parity_case *pc, uint64_t end,
                            stop_parity_run *out, size_t *cursor_out) {
    return stop_parity_diag_origin(rom, pc, end, 0u, out, cursor_out);
}

#define STOP_BTN(at) {(at), GBB_INPUT_BUTTON_PRESS, GBB_BUTTON_A}
#define STOP_WAKE(at) {(at), GBB_INPUT_STOP_WAKE, 1u}

static int case_replay_stop_resume_parity(void) {
    static const uint8_t stop_program[] = {0x10,0x00,0x00,0x18,0xfe};
    uint8_t rom[32768];
    make_accept_test_rom(rom, stop_program, sizeof(stop_program));
    const uint64_t end = 100u;
    /* A button press with the joypad interrupt masked does not end STOP: the first row proves that,
     * so the wake rows below really exercise "resume past a non-waking event". */
    static const stop_parity_case cases[] = {
        {"non-wake-only", {STOP_BTN(40)}, 1u, 0, GBB_ACCEPT_STEP_STOPPED, 1u, 0},
        {"press-then-wake", {STOP_BTN(40), STOP_WAKE(80)}, 2u, 0, GBB_ACCEPT_STEP_OK, 2u, 1},
        {"wake-at-deadline", {STOP_BTN(40), STOP_WAKE(100)}, 2u, 0, GBB_ACCEPT_STEP_OK, 2u, 1},
        {"wake-after-deadline", {STOP_BTN(40), STOP_WAKE(101)}, 2u, 0, GBB_ACCEPT_STEP_STOPPED, 1u, 0},
        {"null-span", {STOP_WAKE(40)}, 0u, 1, GBB_ACCEPT_STEP_STOPPED, 0u, 0},
        {"empty-span", {STOP_WAKE(40)}, 0u, 0, GBB_ACCEPT_STEP_STOPPED, 0u, 0},
        {"equal-timestamps", {STOP_BTN(40), STOP_WAKE(40)}, 2u, 0, GBB_ACCEPT_STEP_OK, 2u, 1},
    };
    int failed = 0;
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        const stop_parity_case *pc = &cases[i];
        stop_parity_run main_run, diag_run;
        size_t cursor = 0u;
        if (stop_parity_main(rom, pc, end, &main_run) != 0) return 1;
        if (stop_parity_diag(rom, pc, end, &diag_run, &cursor) != 0) return 1;
        if (main_run.status != diag_run.status || main_run.actual != diag_run.actual ||
            main_run.woke != diag_run.woke || diag_run.status != pc->status ||
            diag_run.woke != pc->woke || cursor != pc->cursor) {
            fprintf(stderr,
                    "replay-stop-parity sub=%s main(status=%d actual=%llu woke=%d) "
                    "diag(status=%d actual=%llu woke=%d cursor=%zu) expected(status=%d woke=%d cursor=%zu)\n",
                    pc->name, (int)main_run.status, (unsigned long long)main_run.actual, main_run.woke,
                    (int)diag_run.status, (unsigned long long)diag_run.actual, diag_run.woke, cursor,
                    (int)pc->status, pc->woke, pc->cursor);
            failed = 1;
        }
    }

    /* Guard-origin precondition (GR-WR-02): an origin past the deadline must be refused as GUARD with
     * no core run; an origin equal to the deadline is still accepted. */
    static const struct {
        const char *name;
        uint64_t origin;
        enum gbb_accept_step_status status;
    } origin_rows[] = {
        {"origin-past-deadline", 101u, GBB_ACCEPT_STEP_GUARD},
        {"origin-equals-deadline", 100u, GBB_ACCEPT_STEP_STOPPED},
    };
    static const stop_parity_case origin_case = {"origin", {STOP_WAKE(40)}, 0u, 1, GBB_ACCEPT_STEP_STOPPED, 0u, 0};
    for (size_t i = 0; i < sizeof(origin_rows) / sizeof(origin_rows[0]); ++i) {
        stop_parity_run run;
        size_t ocursor = 0u;
        if (stop_parity_diag_origin(rom, &origin_case, end, origin_rows[i].origin, &run, &ocursor) != 0) return 1;
        const int guarded = origin_rows[i].status == GBB_ACCEPT_STEP_GUARD;
        if (run.status != origin_rows[i].status || ocursor != 0u || (guarded && run.actual != 0u)) {
            fprintf(stderr, "replay-stop-parity guard-origin sub=%s status=%d actual=%llu cursor=%zu want_status=%d\n",
                    origin_rows[i].name, (int)run.status, (unsigned long long)run.actual, ocursor,
                    (int)origin_rows[i].status);
            failed = 1;
        }
    }

    /* Truth table of the shared rule itself. */
    size_t cursor = 0u;
    const gbb_input_event at_deadline = STOP_WAKE(100);
    const gbb_input_event past_deadline = STOP_WAKE(101);
    const gbb_accept_input_span due = {&at_deadline, 1u, &cursor};
    const gbb_accept_input_span late = {&past_deadline, 1u, &cursor};
    const gbb_accept_input_span empty = {NULL, 0u, &cursor};
    const gbb_accept_input_span null_cursor = {&at_deadline, 1u, NULL};
    const gbb_accept_input_span null_events = {NULL, 1u, &cursor};
    size_t spent = 1u;
    const gbb_accept_input_span exhausted = {&at_deadline, 1u, &spent};
    const struct {
        const char *name;
        int got;
        int want;
    } table[] = {
        {"null-span", gbb_accept_stop_resumable(NULL, 100u, 0u, 10u), 0},
        {"empty-span", gbb_accept_stop_resumable(&empty, 100u, 0u, 10u), 0},
        {"null-cursor", gbb_accept_stop_resumable(&null_cursor, 100u, 0u, 10u), 0},
        {"null-events", gbb_accept_stop_resumable(&null_events, 100u, 0u, 10u), 0},
        {"cursor-at-count", gbb_accept_stop_resumable(&exhausted, 100u, 0u, 10u), 0},
        {"event-at-deadline", gbb_accept_stop_resumable(&due, 100u, 0u, 10u), 1},
        {"event-past-deadline", gbb_accept_stop_resumable(&late, 100u, 0u, 10u), 0},
        {"consumed-equals-budget", gbb_accept_stop_resumable(&due, 100u, 10u, 10u), 0},
        {"consumed-below-budget", gbb_accept_stop_resumable(&due, 100u, 9u, 10u), 1},
    };
    for (size_t i = 0; i < sizeof(table) / sizeof(table[0]); ++i) {
        if (table[i].got != table[i].want) {
            fprintf(stderr, "replay-stop-parity truth-table sub=%s got=%d want=%d\n", table[i].name,
                    table[i].got, table[i].want);
            failed = 1;
        }
    }
    if (failed) return 1;
    PASS("acceptance_replay_stop_resume_parity");
}

/* Main-drive-only sibling control: the same ROM and script as the first wake row, driven only through
 * gbb_accept_drive, so a replay-side mutant leaves it untouched. */
static int case_drive_stop_resume_main(void) {
    static const uint8_t stop_program[] = {0x10,0x00,0x00,0x18,0xfe};
    uint8_t rom[32768];
    make_accept_test_rom(rom, stop_program, sizeof(stop_program));
    static const stop_parity_case pc = {"press-then-wake", {STOP_BTN(40), STOP_WAKE(80)}, 2u, 0,
                                        GBB_ACCEPT_STEP_OK, 2u, 1};
    stop_parity_run run;
    if (stop_parity_main(rom, &pc, 100u, &run) != 0) return 1;
    if (run.status != GBB_ACCEPT_STEP_OK || run.actual < 80u || run.actual > 100u || !run.woke) {
        fprintf(stderr, "main-stop-resume status=%d actual=%llu woke=%d\n", (int)run.status,
                (unsigned long long)run.actual, run.woke);
        return 1;
    }
    PASS("acceptance_drive_stop_resume_main");
}

/* IN-06: a rejected call with a count that is provably outside the span leaves the count 0, whichever check
 * rejected it. Every sub-case uses a count disjoint from the span, so none of them depends on the
 * span-aliasing carve-out (that is covered by acceptance_input_span_output_alias). */
static int stale_count_check(const char *sub, gbb_run_result result, size_t count,
                             const gbb_accept_input_span *span, size_t count_before,
                             size_t cursor_before, const gbb_input_event *events,
                             const gbb_input_event *saved_events) {
    int ok = 1;
    if (result.reason != GBB_STOP_INVALID_STATE || result.consumed_half_dots != 0u) {
        fprintf(stderr, "frame-count-stale sub=%s result reason=%d consumed=%llu\n", sub,
                (int)result.reason, (unsigned long long)result.consumed_half_dots);
        ok = 0;
    }
    if (count != 0u) {
        fprintf(stderr, "frame-count-stale sub=%s count=%zu\n", sub, count);
        ok = 0;
    }
    if (span->count != count_before || *span->cursor != cursor_before ||
        memcmp(events, saved_events, 4u * sizeof(*events)) != 0) {
        fprintf(stderr, "span-mutated-on-reject sub=%s count=%zu cursor=%zu\n", sub, span->count,
                *span->cursor);
        ok = 0;
    }
    return ok;
}

static int case_accept_input_span_invalid_zeroes_count(void) {
    const size_t storage_size = 4096u;
    uint8_t *storage = malloc(storage_size);
    REQUIRE(storage != NULL);
    gbb_accept_input_span *span = (gbb_accept_input_span *)(void *)(storage + 128u);
    size_t *cursor = (size_t *)(void *)(storage + 256u);
    gbb_input_event *events = (gbb_input_event *)(void *)(storage + 1024u);
    gbb_input_event saved_events[4];
    for (size_t i = 0; i < 4u; ++i) {
        events[i] = (gbb_input_event){8u, (i & 1u) == 0u ? GBB_INPUT_BUTTON_PRESS : GBB_INPUT_BUTTON_RELEASE,
                                     GBB_BUTTON_A};
    }
    memcpy(saved_events, events, sizeof(saved_events));
    *cursor = 0u;
    *span = (gbb_accept_input_span){events, 4u, cursor};

    uint8_t rom[32768];
    static const uint8_t loop_program[] = {0x18,0xfe};
    make_accept_test_rom(rom, loop_program, sizeof(loop_program));
    gbb_instance *instance = NULL;
    REQUIRE(gbb_create(GBB_PROFILE_DMG_CPU_B, &instance) == GBB_OK);
    REQUIRE(gbb_load_rom(instance, rom, sizeof(rom)) == GBB_OK);
    gbb_audio_frame *partial_frame = (gbb_audio_frame *)(void *)align_test_address(
        (uintptr_t)(void *)(events + 1u) + offsetof(gbb_input_event, kind), _Alignof(gbb_audio_frame));
    gbb_audio_frame frames[4];

    int ok = 1;
    size_t count = 7u;
    gbb_run_result result = gbb_accept_run_audio(instance, 32u, span, partial_frame, 1u, &count);
    ok &= stale_count_check("frames/events", result, count, span, 4u, 0u, events, saved_events);

    count = 7u;
    result = gbb_accept_run_audio(instance, 32u, span, (gbb_audio_frame *)(void *)span, 1u, &count);
    ok &= stale_count_check("frames/span-descriptor", result, count, span, 4u, 0u, events, saved_events);

    count = 7u;
    result = gbb_accept_run_audio(instance, 32u, span, frames, SIZE_MAX, &count);
    ok &= stale_count_check("frame-capacity-SIZE_MAX", result, count, span, 4u, 0u, events, saved_events);

    count = 7u;
    *cursor = 5u;
    result = gbb_accept_run_audio(instance, 32u, span, frames, 4u, &count);
    ok &= stale_count_check("span-invalid", result, count, span, 4u, 5u, events, saved_events);
    *cursor = 0u;

    gbb_destroy(instance);
    free(storage);
    if (!ok) return 1;
    PASS("acceptance_input_span_invalid_zeroes_count");
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: test_acceptance_lib <case> [args]\n"); return 2; }
    if (strcmp(argv[1], "acceptance_lib_libbet_replay") == 0) {
        REQUIRE(argc == 4);
        return case_libbet_replay(argv[2], argv[3]);
    }
    if (strcmp(argv[1], "acceptance_parse_script_bounds") == 0) return case_parse_bounds();
    if (strcmp(argv[1], "acceptance_parse_script_errors") == 0) return case_parse_errors();
    if (strcmp(argv[1], "acceptance_predicate_truth_table") == 0) return case_predicate_truth_table();
    if (strcmp(argv[1], "acceptance_predicate_anchors") == 0) {
        REQUIRE(argc == 3);
        return case_predicate_anchors(argv[2]);
    }
    if (strcmp(argv[1], "acceptance_drive_dense_queue") == 0) return case_drive_dense_queue();
    if (strcmp(argv[1], "acceptance_drive_batch_order") == 0) return case_accept_drive_batch_order();
    if (strcmp(argv[1], "acceptance_drive_stop_guard_failure") == 0) return case_accept_drive_stop_guard_failure();
    if (strcmp(argv[1], "acceptance_input_span_edges") == 0) return case_accept_input_span_edges();
    if (strcmp(argv[1], "acceptance_drive_stop_wake_deadline") == 0) return case_accept_drive_stop_wake_deadline();
    if (strcmp(argv[1], "acceptance_input_span_output_alias") == 0) return case_accept_input_span_output_alias();
    if (strcmp(argv[1], "acceptance_replay_stop_resume_parity") == 0) return case_replay_stop_resume_parity();
    if (strcmp(argv[1], "acceptance_drive_stop_resume_main") == 0) return case_drive_stop_resume_main();
    if (strcmp(argv[1], "acceptance_input_span_invalid_zeroes_count") == 0) return case_accept_input_span_invalid_zeroes_count();
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
