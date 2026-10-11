#include "acceptance.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Case-file parser and path validator boundary matrix (D-21, D-28). Inputs are built in memory
 * and handed to the same functions gabbaboy-runner uses; nothing touches the filesystem. */

#define REQUIRE(x) do { if (!(x)) { fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
#define PASS(name) do { printf("PASS %s\n", name); return 0; } while (0)

#define D64 "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9"
#define D63 "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a"
#define U64 "3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1A9"
#define VALID_BASE                                                                          \
    "id=%s rom=fixtures/libbet/libbet.gb rom_sha256=" D64 " rom_size=32768"                 \
    " oracle=progress-predicate predicate=libbet-tutorial-cleared expect_hw_capability=0"   \
    " input_script=tests/acceptance/inputs/libbet-tutorial.input input_sha256=" D64         \
    " budget_half_dots=505612800 model_pass=dmg-cpu-b"

/* Parses `text`; on rejection checks the message has the reason and line. */
static int parse(const char *text, size_t length, gbb_case_list *list, char *err, size_t cap) {
    return gbb_cases_parse((const uint8_t *)text, length, list, err, cap);
}

static int expect_accept(const char *text, size_t length, size_t cases) {
    gbb_case_list list;
    char err[160] = "";
    int rc = parse(text, length, &list, err, sizeof(err));
    if (rc != 0 || list.count != cases) {
        fprintf(stderr, "accept failed rc=%d count=%zu wanted %zu err='%s'\n", rc, list.count, cases, err);
        gbb_cases_free(&list);
        return 1;
    }
    gbb_cases_free(&list);
    return 0;
}

/* Rejection must be exit class 1, carry the exact "invalid-cases: <reason> line=<n>" and leave
 * no parsed cases (all-or-nothing). */
static int expect_reject(const char *what, const char *text, size_t length, const char *reason, size_t line) {
    gbb_case_list list;
    char err[160] = "", want[160];
    int rc = parse(text, length, &list, err, sizeof(err));
    snprintf(want, sizeof(want), "invalid-cases: %s line=%zu", reason, line);
    int bad = rc != 1 || strcmp(err, want) != 0 || list.cases != NULL || list.count != 0;
    if (bad) fprintf(stderr, "%s: rc=%d err='%s' wanted '%s' cases=%p count=%zu\n", what, rc, err, want,
                     (void *)list.cases, list.count);
    gbb_cases_free(&list);
    return bad;
}

static void valid_line(char *out, size_t cap, const char *id) {
    snprintf(out, cap, VALID_BASE, id);
}

/* A rejection test for one malformed single-line file built from the valid line. `from` is replaced
 * by `to` (both must be present exactly once in the valid line, or `to` is appended when from is NULL). */
static int mutate_reject(const char *what, const char *from, const char *to, const char *reason) {
    char line[GBB_CASES_MAX_LINE + 64], out[GBB_CASES_MAX_LINE + 128];
    valid_line(line, sizeof(line), "libbet");
    if (from == NULL) {
        snprintf(out, sizeof(out), "%s %s\n", line, to);
    } else {
        char *at = strstr(line, from);
        REQUIRE(at != NULL);
        snprintf(out, sizeof(out), "%.*s%s%s\n", (int)(at - line), line, to, at + strlen(from));
    }
    return expect_reject(what, out, strlen(out), reason, 1);
}

static int acceptance_parse_cases_bounds(void) {
    char line[GBB_CASES_MAX_LINE + 64], id[16];
    valid_line(line, sizeof(line), "libbet");
    size_t base = strlen(line);
    REQUIRE(base < GBB_CASES_MAX_LINE);

    /* 1024 characters on one line is accepted (padding is trailing spaces), 1025 is rejected,
     * and CRLF does not count toward the limit. */
    char *buf = malloc(GBB_CASES_MAX_BYTES + 16u);
    REQUIRE(buf != NULL);
    memcpy(buf, line, base);
    memset(buf + base, ' ', GBB_CASES_MAX_LINE - base);
    buf[GBB_CASES_MAX_LINE] = '\n';
    REQUIRE(expect_accept(buf, GBB_CASES_MAX_LINE + 1u, 1) == 0);
    buf[GBB_CASES_MAX_LINE] = '\r';
    buf[GBB_CASES_MAX_LINE + 1u] = '\n';
    REQUIRE(expect_accept(buf, GBB_CASES_MAX_LINE + 2u, 1) == 0);
    memset(buf + base, ' ', GBB_CASES_MAX_LINE + 1u - base);
    buf[GBB_CASES_MAX_LINE + 1u] = '\n';
    REQUIRE(expect_reject("1025-char line", buf, GBB_CASES_MAX_LINE + 2u, "line-too-long", 1) == 0);

    /* 128 distinct cases are accepted, the 129th is rejected on its own line. */
    size_t used = 0;
    for (unsigned i = 0; i < GBB_CASES_MAX_CASES; i++) {
        snprintf(id, sizeof(id), "c%u", i);
        valid_line(line, sizeof(line), id);
        used += (size_t)snprintf(buf + used, 400, "%s\n", line);
    }
    REQUIRE(used < GBB_CASES_MAX_BYTES);
    REQUIRE(expect_accept(buf, used, GBB_CASES_MAX_CASES) == 0);
    valid_line(line, sizeof(line), "c128");
    size_t more = used + (size_t)snprintf(buf + used, 400, "%s\n", line);
    REQUIRE(expect_reject("129 cases", buf, more, "too-many-cases", 129) == 0);

    /* 64 KiB exactly is accepted; one byte over is rejected as a whole-file limit (line 0). */
    valid_line(line, sizeof(line), "libbet");
    size_t n = 0;
    n += (size_t)snprintf(buf, 400, "%s\n", line);
    while (n + 128u <= GBB_CASES_MAX_BYTES) { memset(buf + n, '#', 127u); buf[n + 127u] = '\n'; n += 128u; }
    if (n < GBB_CASES_MAX_BYTES) { memset(buf + n, '#', GBB_CASES_MAX_BYTES - n - 1u); buf[GBB_CASES_MAX_BYTES - 1u] = '\n'; n = GBB_CASES_MAX_BYTES; }
    REQUIRE(n == GBB_CASES_MAX_BYTES);
    REQUIRE(expect_accept(buf, n, 1) == 0);
    buf[n] = '#';
    REQUIRE(expect_reject("65537 bytes", buf, n + 1u, "file-too-large", 0) == 0);
    free(buf);

    /* Empty and comment-only files have no cases. */
    REQUIRE(expect_reject("empty", "", 0, "no-cases", 0) == 0);
    REQUIRE(expect_reject("comments", "# only\n\n", 8, "no-cases", 0) == 0);
    PASS("acceptance_parse_cases_bounds");
}

static int acceptance_parse_cases_errors(void) {
    /* Single-line files: every defect is reported on line 1. */
    REQUIRE(mutate_reject("unknown key", NULL, "bogus=1", "unknown-key") == 0);
    REQUIRE(mutate_reject("rtc_policy", NULL, "rtc_policy=zero", "rejected-key") == 0);
    REQUIRE(mutate_reject("duplicate key", NULL, "rom_size=32768", "duplicate-key") == 0);
    REQUIRE(mutate_reject("oracle fibonacci-ldbb", "oracle=progress-predicate", "oracle=fibonacci-ldbb", "rejected-oracle") == 0);
    REQUIRE(mutate_reject("oracle screen-text", "oracle=progress-predicate", "oracle=screen-text", "rejected-oracle") == 0);
    REQUIRE(mutate_reject("uppercase digest", "rom_sha256=" D64, "rom_sha256=" U64, "bad-digest") == 0);
    REQUIRE(mutate_reject("63-char digest", "rom_sha256=" D64, "rom_sha256=" D63, "bad-digest") == 0);
    REQUIRE(mutate_reject("rom_size 0", "rom_size=32768", "rom_size=0", "bad-number") == 0);
    REQUIRE(mutate_reject("rom_size over 8 MiB", "rom_size=32768", "rom_size=8388609", "bad-number") == 0);
    REQUIRE(mutate_reject("hw capability", "expect_hw_capability=0", "expect_hw_capability=1",
                          "expect-hw-capability-unsupported") == 0);
    REQUIRE(mutate_reject("model both lists", "model_pass=dmg-cpu-b", "model_pass=dmg-cpu-b model_fail=dmg-cpu-b",
                          "model-in-pass-and-fail") == 0);
    REQUIRE(mutate_reject("bad path", "rom=fixtures/libbet/libbet.gb", "rom=../x.gb", "bad-path") == 0);

    /* rom_size is accepted at exactly 8 MiB. */
    {
        char line[GBB_CASES_MAX_LINE + 64], out[GBB_CASES_MAX_LINE + 64];
        valid_line(line, sizeof(line), "libbet");
        char *at = strstr(line, "rom_size=32768");
        REQUIRE(at != NULL);
        snprintf(out, sizeof(out), "%.*srom_size=8388608%s\n", (int)(at - line), line, at + 14);
        REQUIRE(expect_accept(out, strlen(out), 1) == 0);
    }

    /* A defect on line 3 after two good lines (and a comment) is reported with that line and
     * discards the already parsed cases; a repeated id is reported on the repeating line. */
    {
        char a[GBB_CASES_MAX_LINE + 64], b[GBB_CASES_MAX_LINE + 64], out[4 * GBB_CASES_MAX_LINE];
        valid_line(a, sizeof(a), "one");
        valid_line(b, sizeof(b), "two");
        snprintf(out, sizeof(out), "%s\n# note\n%s bogus=1\n", a, b);
        REQUIRE(expect_reject("line 3 defect", out, strlen(out), "unknown-key", 3) == 0);
        snprintf(out, sizeof(out), "%s\n%s\n%s\n", a, b, a);
        REQUIRE(expect_reject("duplicate id", out, strlen(out), "duplicate-id", 3) == 0);
        snprintf(out, sizeof(out), "%s\n%s\n", a, b);
        REQUIRE(expect_accept(out, strlen(out), 2) == 0);
        /* Non-ASCII, tab and NUL bytes are rejected. */
        snprintf(out, sizeof(out), "%s\tx\n", a);
        REQUIRE(expect_reject("tab", out, strlen(out), "bad-character", 1) == 0);
        snprintf(out, sizeof(out), "%s\n", a);
        out[strlen(a) - 1u] = '\0';
        REQUIRE(expect_reject("nul", out, strlen(a) + 1u, "bad-character", 1) == 0);
    }
    PASS("acceptance_parse_cases_errors");
}

static int acceptance_parse_paths(void) {
    REQUIRE(gbb_cases_path_valid("a/b.gb"));
    REQUIRE(gbb_cases_path_valid("a"));
    REQUIRE(gbb_cases_path_valid("a/.hidden"));
    REQUIRE(gbb_cases_path_valid("a/..b/c.."));
    REQUIRE(!gbb_cases_path_valid(NULL));
    REQUIRE(!gbb_cases_path_valid(""));
    REQUIRE(!gbb_cases_path_valid("../x"));
    REQUIRE(!gbb_cases_path_valid("a/../x"));
    REQUIRE(!gbb_cases_path_valid("/x"));
    REQUIRE(!gbb_cases_path_valid("\\x"));
    REQUIRE(!gbb_cases_path_valid("a\\b"));
    REQUIRE(!gbb_cases_path_valid("C:x"));
    REQUIRE(!gbb_cases_path_valid("a//b"));
    REQUIRE(!gbb_cases_path_valid("a/./b"));
    REQUIRE(!gbb_cases_path_valid("./a"));
    REQUIRE(!gbb_cases_path_valid("a/"));
    REQUIRE(!gbb_cases_path_valid("a b"));
    REQUIRE(!gbb_cases_path_valid("a\tb"));
    REQUIRE(!gbb_cases_path_valid("a\x7f" "b"));
    REQUIRE(!gbb_cases_path_valid("a\xc3\xa9"));

    /* 255 bytes is accepted, 256 is rejected. */
    char path[300];
    memset(path, 'a', 255u);
    path[255] = '\0';
    REQUIRE(gbb_cases_path_valid(path));
    path[255] = 'a';
    path[256] = '\0';
    REQUIRE(!gbb_cases_path_valid(path));
    PASS("acceptance_parse_paths");
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: test_acceptance_cases <name>\n"); return 2; }
    if (strcmp(argv[1], "acceptance_parse_cases_bounds") == 0) return acceptance_parse_cases_bounds();
    if (strcmp(argv[1], "acceptance_parse_cases_errors") == 0) return acceptance_parse_cases_errors();
    if (strcmp(argv[1], "acceptance_parse_paths") == 0) return acceptance_parse_paths();
    fprintf(stderr, "unknown test %s\n", argv[1]);
    return 2;
}
