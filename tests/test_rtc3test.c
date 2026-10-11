/* rtc3test v004 headless oracle (D-11).
 *
 * rtc3test is hardware-derived (author-attested) evidence: the ROM author states the RTC
 * behaviour a real MBC3 timer cartridge shows, and the ROM reports pass/fail and measured
 * timings on screen only. This test therefore decodes the BG map ($9C00), not any memory
 * result byte. A pass requires ALL of: the "* Return" end marker, no red (fail) tile, the
 * suite's exact green-cell count, every millisecond value the ROM displays equal to the
 * ROM author's own stated expectation, and a byte-identical decoded transcript. A blank or
 * early frame can never satisfy that, and rtc3test_negative_control must never see the
 * marker when the suite is not started.
 *
 * White-box single translation unit: it includes the core and the acceptance sources it needs
 * (script parser, stepper, SHA-256), so it must not link GabbaBoy::core or gabbaboy_accept.
 * argv: <case> <rom> <script> <expected-transcript> [--emit]
 *       rtc3test_negative_control <rom> <basic-script>
 * The expected values below are transcribed from fixtures/rtc3test/tests.md, never from this
 * emulator's output. */

#include "../src/core/gabbaboy.c"
#include "../src/accept/sha256.c"
#include "../src/accept/input_script.c"
#include "../src/accept/predicate.c"
#include "../src/accept/stepper.c"

#include <limits.h>
#include <stdio.h>

#define ROM_SHA256 "a271013fb37ea1d927b854798401320b220d57abb3ca77f3d318ceb8a9def30d"

/* Digest of each committed script, checked before replay. */
static const struct { const char *suite; const char *sha256; unsigned green; } SUITES[] = {
    { "basic", "ea0075e59880b594799057397498c73a3f9c4f0a019e026917376eaf82b49729", 36u },
    { "range", "d22dbdb4396122f0431b19d3370adb216e49e2e5f9ac536e1bd2df76ea481707", 28u },
    { "subsecond", "c00462fc120ea2afc7ecfafd134bdd879362ca18a11128b0d1aa36689a754e61", 57u },
};

/* Stated expectations, transcribed from fixtures/rtc3test/tests.md (the verbatim upstream file at
 * commit 80ae792bf1b3c3387929b912e6df001af3511e24, SHA-256
 * 1937b614b49cff4e2e9b3e36aaa888e754ece6eb141ce46406a28f8f005d4172, digest-pinned in
 * fixtures/rtc3test/manifest.json). Range states no millisecond values. */
static const struct { const char *suite; const char *label; unsigned ms; } stated_expectations[] = {
    { "basic", "Tick", 1000 },
    { "subsecond", "RTCS/500", 1000 },
    { "subsecond", "RTCS/900", 1000 },
    { "subsecond", "RTCM/50", 50 },
    { "subsecond", "RTCM/600", 600 },
    { "subsecond", "RTCH/200", 200 },
    { "subsecond", "RTCDL/800", 800 },
    { "subsecond", "RTCDH/300", 300 },
    { "subsecond", "RTC off/400", 400 },
};
#define STATED_COUNT (sizeof(stated_expectations) / sizeof(stated_expectations[0]))

#define FRAME UINT64_C(140448)
#define BUDGET_FRAMES 3600u /* 60 emulated seconds */
#define MAP_ROWS 18u
#define MAP_COLS 20u
#define MAP_BASE 0x1C00u /* $9C00 within the 8 KiB VRAM */
#define MARKER_ROW 17u
#define MARKER_COL 6u
static const uint8_t MARKER[8] = { 0xC1u, 0x3Fu, 0x1Bu, 0x28u, 0x37u, 0x38u, 0x35u, 0x31u };

/* rtc3test charmap (src/charmap.asm at the pinned commit): $00-$09 digits, $0A-$23 A-Z,
 * $24-$3D a-z, $3E '.', $3F ' '; $C0 '>', $C1 '*' (A button), $C2 ':', $C3 '/', $C4 '-', $FF blank.
 * Tile values add $40 (green, pass) or $80 (red, fail) to the $00-$3F glyph. */
static char glyph(uint8_t tile) {
    const uint8_t g = tile & 0x3Fu;
    if (tile >= 0xC0u) {
        switch (tile) {
        case 0xC0u: return '>';
        case 0xC1u: return '*';
        case 0xC2u: return ':';
        case 0xC3u: return '/';
        case 0xC4u: return '-';
        case 0xFFu: return ' '; /* ClearScreen fill: a blank tile */
        default: return '?';
        }
    }
    if (g <= 9u) return (char)('0' + g);
    if (g <= 0x23u) return (char)('A' + (g - 0x0Au));
    if (g <= 0x3Du) return (char)('a' + (g - 0x24u));
    return g == 0x3Eu ? '.' : ' ';
}

static uint8_t *read_file(const char *path, size_t *size) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    const long n = ftell(f);
    if (n < 0 || n > (1L << 20) || fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }
    uint8_t *buf = malloc((size_t)n + 1u);
    if (buf != NULL && fread(buf, 1u, (size_t)n, f) != (size_t)n) { free(buf); buf = NULL; }
    fclose(f);
    if (buf != NULL) { buf[n] = 0u; *size = (size_t)n; }
    return buf;
}

static int digest_is(const uint8_t *bytes, size_t size, const char *expect, const char *what) {
    char hex[65];
    gbb_accept_sha256_hex(bytes, size, hex);
    if (strcmp(hex, expect) != 0) {
        fprintf(stderr, "%s digest %s != pinned %s\n", what, hex, expect);
        return 1;
    }
    return 0;
}

static const uint8_t *map_cell(const gbb_instance *m, unsigned row, unsigned col) {
    return &m->vram[MAP_BASE + row * 32u + col];
}

static int marker_present(const gbb_instance *m) {
    for (unsigned i = 0u; i < 8u; ++i)
        if (*map_cell(m, MARKER_ROW, MARKER_COL + i) != MARKER[i]) return 0;
    return 1;
}

/* Decodes the visible 20x18 map. Text is written as the glyphs; a run of green (pass) cells is
 * wrapped as [+...] and a run of red (fail) cells as [!...], so a coloured numeric stays one
 * contiguous token. Trailing spaces of each line are trimmed. Also counts coloured cells. */
static size_t map_decode(const gbb_instance *m, char *out, size_t cap, unsigned *green, unsigned *red) {
    size_t n = 0u;
    *green = 0u;
    *red = 0u;
    for (unsigned row = 0u; row < MAP_ROWS; ++row) {
        char line[128];
        size_t len = 0u;
        char run = 0;
        for (unsigned col = 0u; col < MAP_COLS; ++col) {
            const uint8_t tile = *map_cell(m, row, col);
            char colour = 0;
            if (tile >= 0x40u && tile < 0x80u) { colour = '+'; ++*green; }
            else if (tile >= 0x80u && tile < 0xC0u) { colour = '!'; ++*red; }
            if (colour != run) {
                if (run != 0) line[len++] = ']';
                if (colour != 0) { line[len++] = '['; line[len++] = colour; }
                run = colour;
            }
            line[len++] = glyph(tile);
        }
        if (run != 0) line[len++] = ']';
        while (len > 0u && line[len - 1u] == ' ') --len;
        if (n + len + 1u >= cap) return 0u;
        memcpy(out + n, line, len);
        n += len;
        out[n++] = '\n';
    }
    out[n] = 0;
    return n;
}

/* Every N.Nms field the ROM displays must equal the stated expectation of the suite, as a
 * multiset, and, where the row text starts with a stated label, that label's entry. */
static int check_numerics(const char *suite, const char *transcript) {
    unsigned want[16], want_n = 0u;
    for (size_t i = 0u; i < STATED_COUNT; ++i)
        if (strcmp(stated_expectations[i].suite, suite) == 0) want[want_n++] = stated_expectations[i].ms;
    unsigned seen[32], seen_n = 0u;
    int bad = 0;
    /* Walk line by line; strip the colour brackets so "[+1000.0ms]" reads as one field. */
    const char *p = transcript;
    while (*p != 0) {
        char row[160];
        size_t len = 0u;
        while (*p != 0 && *p != '\n' && len < sizeof(row) - 1u) {
            if (*p == '[') { p += 2; continue; }
            if (*p == ']') { ++p; continue; }
            row[len++] = *p++;
        }
        row[len] = 0;
        while (*p != 0 && *p != '\n') ++p;
        if (*p == '\n') ++p;
        for (size_t i = 0u; i + 4u < len; ++i) {
            if (row[i] < '0' || row[i] > '9') continue;
            size_t j = i;
            unsigned whole = 0u;
            while (j < len && row[j] >= '0' && row[j] <= '9') whole = whole * 10u + (unsigned)(row[j++] - '0');
            if (j + 3u < len + 1u && row[j] == '.' && row[j + 1u] >= '0' && row[j + 1u] <= '9' &&
                row[j + 2u] == 'm' && row[j + 3u] == 's') {
                if (row[j + 1u] != '0' || seen_n == 32u) {
                    fprintf(stderr, "numeric field %u.%cms in row '%s' is not an exact stated value\n",
                            whole, row[j + 1u], row);
                    bad = 1;
                } else {
                    seen[seen_n++] = whole;
                    for (size_t k = 0u; k < STATED_COUNT; ++k) {
                        const size_t ll = strlen(stated_expectations[k].label);
                        if (strcmp(stated_expectations[k].suite, suite) == 0 &&
                            strncmp(row, stated_expectations[k].label, ll) == 0 &&
                            (row[ll] == ' ' || row[ll] == 0) && whole != stated_expectations[k].ms) {
                            fprintf(stderr, "row '%s' shows %u.0ms but tests.md states %ums\n", row,
                                    whole, stated_expectations[k].ms);
                            bad = 1;
                        }
                    }
                }
                i = j + 3u;
            } else {
                i = j;
            }
        }
    }
    if (seen_n != want_n) {
        fprintf(stderr, "%s: %u millisecond fields displayed, tests.md states %u\n", suite, seen_n, want_n);
        return 1;
    }
    for (unsigned i = 0u; i < want_n; ++i) {
        unsigned found = 0u;
        for (unsigned a = 0u; a < seen_n; ++a) if (seen[a] == want[i]) { seen[a] = UINT_MAX; found = 1u; break; }
        if (!found) {
            fprintf(stderr, "%s: stated %ums never displayed\n", suite, want[i]);
            bad = 1;
        }
    }
    return bad;
}

/* Replays `script` and stops at the end marker or the 60 s budget. Returns 0 and sets
 * *marker_frame (1-based frame count) when the marker appeared, 1 when it did not, 2 on error. */
static int replay(const uint8_t *rom, size_t rom_size, const gbb_accept_script *script,
                  gbb_instance **out, unsigned *marker_frame) {
    gbb_instance *m = NULL;
    if (gbb_create(GBB_PROFILE_DMG_CPU_B, &m) != GBB_OK) return 2;
    if (gbb_load_rom(m, rom, rom_size) != GBB_OK) { gbb_destroy(m); return 2; }
    if (script->event_count > 64u ||
        (script->event_count != 0u && gbb_queue_events(m, script->events, script->event_count) != GBB_OK)) {
        gbb_destroy(m);
        return 2;
    }
    gbb_accept_stepper stepper;
    gbb_accept_stepper_init(&stepper, m, NULL, NULL);
    for (unsigned frame = 1u; frame <= BUDGET_FRAMES; ++frame) {
        if (gbb_accept_advance_to(&stepper, (uint64_t)frame * FRAME) != GBB_ACCEPT_STEP_OK) {
            fprintf(stderr, "stepper stopped (reason %d) at frame %u\n", (int)stepper.last_stop, frame);
            gbb_destroy(m);
            return 2;
        }
        if (marker_present(m)) {
            *marker_frame = frame;
            *out = m;
            return 0;
        }
    }
    *out = m;
    return 1;
}

static int load_script(const uint8_t *bytes, size_t size, gbb_accept_script *script) {
    char err[160];
    memset(script, 0, sizeof(*script));
    if (gbb_accept_script_parse(bytes, size, script, err, sizeof(err)) != 0) {
        fprintf(stderr, "%s\n", err);
        return 1;
    }
    return 0;
}

static int run_suite(const char *suite, const char *rom_path, const char *script_path,
                     const char *expected_path, int emit) {
    size_t k = 0u;
    while (k < sizeof(SUITES) / sizeof(SUITES[0]) && strcmp(SUITES[k].suite, suite) != 0) ++k;
    if (k == sizeof(SUITES) / sizeof(SUITES[0])) { fprintf(stderr, "unknown suite %s\n", suite); return 2; }
    size_t rom_size = 0u, script_size = 0u;
    uint8_t *rom = read_file(rom_path, &rom_size);
    uint8_t *script_bytes = read_file(script_path, &script_size);
    if (rom == NULL || script_bytes == NULL) { fprintf(stderr, "cannot read inputs\n"); return 2; }
    int rc = digest_is(rom, rom_size, ROM_SHA256, "ROM") | digest_is(script_bytes, script_size, SUITES[k].sha256, "script");
    gbb_accept_script script;
    gbb_instance *m = NULL;
    unsigned marker_frame = 0u;
    if (rc == 0 && load_script(script_bytes, script_size, &script) != 0) rc = 1;
    if (rc == 0) {
        const int r = replay(rom, rom_size, &script, &m, &marker_frame);
        gbb_accept_script_free(&script);
        if (r == 2) rc = 1;
        else if (r == 1) { fprintf(stderr, "%s: end marker never appeared in 60 s\n", suite); rc = 1; }
    }
    if (rc == 0) {
        static char transcript[4096];
        unsigned green = 0u, red = 0u;
        if (map_decode(m, transcript, sizeof(transcript), &green, &red) == 0u) rc = 1;
        else if (emit) {
            printf("# marker frame %u green %u red %u\n%s", marker_frame, green, red, transcript);
        } else {
            if (red != 0u) { fprintf(stderr, "%s: %u red (fail) cells\n%s", suite, red, transcript); rc = 1; }
            if (green != SUITES[k].green) {
                fprintf(stderr, "%s: %u green cells, expected %u\n%s", suite, green, SUITES[k].green, transcript);
                rc = 1;
            }
            if (check_numerics(suite, transcript) != 0) rc = 1;
            size_t exp_size = 0u;
            uint8_t *exp = read_file(expected_path, &exp_size);
            if (exp == NULL) { fprintf(stderr, "cannot read %s\n", expected_path); rc = 1; }
            else if (exp_size != strlen(transcript) || memcmp(exp, transcript, exp_size) != 0) {
                fprintf(stderr, "%s: transcript differs from %s; decoded:\n%s", suite, expected_path, transcript);
                rc = 1;
            }
            free(exp);
        }
    }
    if (m != NULL) gbb_destroy(m);
    free(rom);
    free(script_bytes);
    return rc;
}

/* The Basic script without its tap never leaves the menu, so the marker must never appear. */
static int negative_control(const char *rom_path, const char *script_path) {
    size_t rom_size = 0u, script_size = 0u;
    uint8_t *rom = read_file(rom_path, &rom_size);
    uint8_t *src = read_file(script_path, &script_size);
    if (rom == NULL || src == NULL) { fprintf(stderr, "cannot read inputs\n"); return 2; }
    int rc = digest_is(rom, rom_size, ROM_SHA256, "ROM") | digest_is(src, script_size, SUITES[0].sha256, "script");
    uint8_t *cut = malloc(script_size + 1u);
    size_t cut_size = 0u;
    if (cut == NULL) return 2;
    for (size_t i = 0u; i < script_size && rc == 0;) {
        size_t e = i;
        while (e < script_size && src[e] != '\n') ++e;
        const size_t next = e < script_size ? e + 1u : e;
        if (!(e - i >= 4u && memcmp(src + i, "tap ", 4u) == 0)) {
            memcpy(cut + cut_size, src + i, next - i);
            cut_size += next - i;
        }
        i = next;
    }
    if (rc == 0 && cut_size + 8u >= script_size) { fprintf(stderr, "no tap line was removed\n"); rc = 1; }
    gbb_accept_script script;
    if (rc == 0 && load_script(cut, cut_size, &script) != 0) rc = 1;
    if (rc == 0) {
        gbb_instance *m = NULL;
        unsigned frame = 0u;
        const int r = replay(rom, rom_size, &script, &m, &frame);
        gbb_accept_script_free(&script);
        if (r == 0) { fprintf(stderr, "negative control: marker appeared at frame %u without the tap\n", frame); rc = 1; }
        else if (r == 2) rc = 1;
        if (m != NULL) {
            /* Control sanity: the menu itself must be on screen, not a blank map. */
            unsigned drawn = 0u;
            for (unsigned row = 0u; row < MAP_ROWS; ++row)
                for (unsigned col = 0u; col < MAP_COLS; ++col) {
                    const uint8_t tile = *map_cell(m, row, col);
                    if (tile != 0x3Fu && tile != 0xFFu) ++drawn;
                }
            if (rc == 0 && drawn < 20u) {
                fprintf(stderr, "negative control: only %u drawn cells, the ROM did not reach its menu\n", drawn);
                rc = 1;
            }
            gbb_destroy(m);
        }
    }
    free(cut);
    free(rom);
    free(src);
    return rc;
}

int main(int argc, char **argv) {
    if (argc == 4 && strcmp(argv[1], "rtc3test_negative_control") == 0)
        return negative_control(argv[2], argv[3]);
    if (argc >= 5) {
        const char *name = argv[1];
        if (strncmp(name, "rtc3test_", 9u) == 0)
            return run_suite(name + 9, argv[2], argv[3], argv[4], argc == 6 && strcmp(argv[5], "--emit") == 0);
    }
    fprintf(stderr, "usage: test_rtc3test <case> <rom> <script> <expected> [--emit]\n");
    return 2;
}
