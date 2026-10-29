/* D-07: the save stem is validated, never rewritten. Each refusal class has its own case so a failure
 * names the class, and each input maps to exactly one status under the first-match rule in
 * src/host/host_basename.c. Links gabbaboy_host only (public header + libc); no core is involved. */
#include "gbb_host.h"

#include <stdio.h>
#include <string.h>

#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

#define SENTINEL 0xA5

/* Accepts `path` and requires the stem to equal `expected` exactly. */
static int accepts_as(const char *path, const char *expected) {
    char out[GBB_HOST_STEM_MAX_BYTES + 1u];
    memset(out, SENTINEL, sizeof(out));
    const host_stem_status status = host_stem(path, out, sizeof(out));
    if (status != HOST_STEM_OK || strcmp(out, expected) != 0) {
        fprintf(stderr, "accept mismatch: status=%s stem=\"%s\" expected=\"%s\"\n",
                host_stem_reason(status), status == HOST_STEM_OK ? out : "", expected);
        return 1;
    }
    return 0;
}

/* Refuses `path` with exactly `status` and `token`, and leaves a sentinel-filled `out` untouched
 * (a refused stem must never be partly written or rewritten). */
static int refuses_as(const char *path, host_stem_status status, const char *token) {
    char out[GBB_HOST_STEM_MAX_BYTES + 1u];
    memset(out, SENTINEL, sizeof(out));
    const host_stem_status got = host_stem(path, out, sizeof(out));
    if (got != status || strcmp(host_stem_reason(got), token) != 0) {
        fprintf(stderr, "refusal mismatch: got=%s(%d) expected=%s(%d)\n",
                host_stem_reason(got), (int)got, token, (int)status);
        return 1;
    }
    for (size_t i = 0u; i < sizeof(out); ++i) {
        if ((unsigned char)out[i] != SENTINEL) {
            fprintf(stderr, "out byte %zu was written on a %s refusal\n", i, token);
            return 1;
        }
    }
    return 0;
}

static int accepts(void) {
    /* Playstead-agreeing extensions: .gb .gbc .GB .GBC .bin. */
    static const char *const agreeing[] = {"x.gb", "x.gbc", "x.GB", "x.GBC", "x.bin"};
    for (size_t i = 0u; i < sizeof(agreeing) / sizeof(agreeing[0]); ++i)
        REQUIRE(accepts_as(agreeing[i], "x") == 0);
    REQUIRE(accepts_as("roms/Tetris.gb", "Tetris") == 0);
    REQUIRE(accepts_as("a/b/Game.GBC", "Game") == 0);
    REQUIRE(accepts_as("x.bin", "x") == 0);
    REQUIRE(accepts_as("Pok\xC3\xA9mon Red.gb", "Pok\xC3\xA9mon Red") == 0);
    /* Documented Playstead divergence: deletingPathExtension would give "game". `.v2-final` has a
     * non-alphanumeric byte, so it is not an extension here and the whole name is the stem. */
    REQUIRE(accepts_as("game.v2-final", "game.v2-final") == 0);
    REQUIRE(accepts_as("noext", "noext") == 0);
    REQUIRE(accepts_as("dir.d/noext", "noext") == 0);
    /* The 200-byte limit is inclusive, with and without an extension. */
    char name[GBB_HOST_STEM_MAX_BYTES + 8u];
    char stem[GBB_HOST_STEM_MAX_BYTES + 1u];
    memset(stem, 'a', GBB_HOST_STEM_MAX_BYTES);
    stem[GBB_HOST_STEM_MAX_BYTES] = '\0';
    REQUIRE(accepts_as(stem, stem) == 0);
    (void)snprintf(name, sizeof(name), "%s.gb", stem);
    REQUIRE(accepts_as(name, stem) == 0);
    return 0;
}

static int refuse_empty(void) {
    /* A trailing slash names a directory: the last component is empty. */
    REQUIRE(refuses_as("dir/", HOST_STEM_EMPTY, "stem-empty") == 0);
    return 0;
}

static int refuse_leading_dot(void) {
    /* A dot at byte 0 never separates an extension, so `.gb` is the stem and it starts with a dot. */
    REQUIRE(refuses_as(".gb", HOST_STEM_LEADING_DOT, "stem-leading-dot") == 0);
    /* `..gb` strips `.gb` and leaves the stem `.`. */
    REQUIRE(refuses_as("..gb", HOST_STEM_LEADING_DOT, "stem-leading-dot") == 0);
    REQUIRE(refuses_as("roms/.hidden.gb", HOST_STEM_LEADING_DOT, "stem-leading-dot") == 0);
    return 0;
}

static int refuse_control(void) {
    REQUIRE(refuses_as("a\x01" "b.gb", HOST_STEM_CONTROL, "stem-control") == 0);
    REQUIRE(refuses_as("a\x1f" "b.gb", HOST_STEM_CONTROL, "stem-control") == 0);
    REQUIRE(refuses_as("a\tb.gb", HOST_STEM_CONTROL, "stem-control") == 0);
    return 0;
}

static int refuse_del(void) {
    REQUIRE(refuses_as("a\x7f" "b.gb", HOST_STEM_DEL, "stem-del") == 0);
    return 0;
}

static int refuse_backslash(void) {
    REQUIRE(refuses_as("a\\b.gb", HOST_STEM_BACKSLASH, "stem-backslash") == 0);
    REQUIRE(refuses_as("dir/x\\y.gb", HOST_STEM_BACKSLASH, "stem-backslash") == 0);
    return 0;
}

static int refuse_bad_utf8(void) {
    REQUIRE(refuses_as("a\xC0\x80" "b.gb", HOST_STEM_BAD_UTF8, "stem-bad-utf8") == 0);          /* overlong NUL */
    REQUIRE(refuses_as("a\xED\xA0\x80" "b.gb", HOST_STEM_BAD_UTF8, "stem-bad-utf8") == 0);      /* surrogate */
    REQUIRE(refuses_as("a\xF4\x90\x80\x80" "b.gb", HOST_STEM_BAD_UTF8, "stem-bad-utf8") == 0);  /* > U+10FFFF */
    REQUIRE(refuses_as("a\xE2\x82.gb", HOST_STEM_BAD_UTF8, "stem-bad-utf8") == 0);              /* truncated */
    REQUIRE(refuses_as("a\xFF" "b.gb", HOST_STEM_BAD_UTF8, "stem-bad-utf8") == 0);
    return 0;
}

static int refuse_too_long(void) {
    char name[GBB_HOST_STEM_MAX_BYTES + 16u];
    char stem[GBB_HOST_STEM_MAX_BYTES + 2u];
    memset(stem, 'a', GBB_HOST_STEM_MAX_BYTES + 1u);
    stem[GBB_HOST_STEM_MAX_BYTES + 1u] = '\0'; /* 201 bytes */
    REQUIRE(refuses_as(stem, HOST_STEM_TOO_LONG, "stem-too-long") == 0);
    (void)snprintf(name, sizeof(name), "%s.gb", stem);
    REQUIRE(refuses_as(name, HOST_STEM_TOO_LONG, "stem-too-long") == 0);
    return 0;
}

int main(int argc, char **argv) {
    static const struct {
        const char *name;
        int (*run)(void);
    } cases[] = {
        {"accepts", accepts},
        {"refuse_empty", refuse_empty},
        {"refuse_leading_dot", refuse_leading_dot},
        {"refuse_control", refuse_control},
        {"refuse_del", refuse_del},
        {"refuse_backslash", refuse_backslash},
        {"refuse_bad_utf8", refuse_bad_utf8},
        {"refuse_too_long", refuse_too_long},
    };
    if (argc != 2) {
        fprintf(stderr, "usage: %s <case>\n", argv[0]);
        return 2;
    }
    for (size_t i = 0u; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        if (strcmp(argv[1], cases[i].name) != 0) continue;
        if (cases[i].run() != 0) {
            printf("FAIL %s\n", cases[i].name);
            return 1;
        }
        printf("PASS %s\n", cases[i].name);
        return 0;
    }
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
