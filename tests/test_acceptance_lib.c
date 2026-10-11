#include "gbb_accept.h"

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

    /* Title garbage: pseudo-random WRAM must not satisfy the predicate. */
    uint32_t x = 12345u;
    for (unsigned round = 0; round < 64; round++) {
        for (unsigned a = 0xC000u; a < 0xE000u; a++) {
            x = x * 1664525u + 1013904223u;
            ram[a] = (uint8_t)(x >> 24);
        }
        ram[0xC4E8] = 3; /* keep garbage from landing on the 2x2 floor by chance */
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
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
