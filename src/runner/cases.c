#include "acceptance.h"
#include "gbb_accept.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Bounded case-file parser (D-20, D-21, D-22, D-28). One case per line,
 * space-separated key=value tokens, '#' comment lines, CRLF tolerated. The
 * whole file is validated before the caller runs anything. */

enum {
    K_ID, K_ROM, K_ROM_SHA256, K_ROM_SIZE, K_ORACLE, K_REFERENCE_DIGEST, K_INPUT_SCRIPT,
    K_INPUT_SHA256, K_BUDGET, K_MODEL_PASS, K_MODEL_FAIL, K_EXPECT_FAIL_REASON,
    K_TARGET_REVISION, K_PREDICATE, K_EXPECT_HW, K_COUNT
};

static const char *const key_names[K_COUNT] = {
    "id", "rom", "rom_sha256", "rom_size", "oracle", "reference_digest", "input_script",
    "input_sha256", "budget_half_dots", "model_pass", "model_fail", "expect_fail_reason",
    "target_revision", "predicate", "expect_hw_capability"
};

static int reject(char *err, size_t capacity, const char *reason, size_t line) {
    if (err != NULL && capacity > 0) {
        snprintf(err, capacity, "invalid-cases: %s line=%zu", reason, line);
    }
    return 1;
}

static int is_lower_hex(const char *s, size_t length) {
    if (strlen(s) != length) return 0;
    for (size_t i = 0; i < length; i++) {
        if (!((s[i] >= '0' && s[i] <= '9') || (s[i] >= 'a' && s[i] <= 'f'))) return 0;
    }
    return 1;
}

/* [a-z0-9-]{min,max} */
static int is_token(const char *s, size_t length, size_t min, size_t max) {
    if (length < min || length > max) return 0;
    for (size_t i = 0; i < length; i++) {
        char c = s[i];
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-')) return 0;
    }
    return 1;
}

/* Decimal without sign or leading zeros, in 1..max. */
static int parse_u64(const char *s, uint64_t max, uint64_t *out) {
    size_t n = strlen(s);
    if (n == 0 || n > 20 || (s[0] == '0' && n > 1)) return 0;
    uint64_t value = 0;
    for (size_t i = 0; i < n; i++) {
        if (s[i] < '0' || s[i] > '9') return 0;
        uint64_t digit = (uint64_t)(s[i] - '0');
        if (value > (UINT64_MAX - digit) / 10u) return 0;
        value = value * 10u + digit;
    }
    if (value < 1u || value > max) return 0;
    *out = value;
    return 1;
}

int gbb_cases_path_valid(const char *path) {
    if (path == NULL) return 0;
    size_t n = strlen(path);
    if (n == 0 || n > GBB_CASES_MAX_PATH || path[0] == '/') return 0;
    size_t segment = 0;
    for (size_t i = 0; i <= n; i++) {
        char c = path[i];
        if (c == '/' || c == '\0') {
            const char *start = path + i - segment;
            if (segment == 0) return 0;
            if (segment == 1 && start[0] == '.') return 0;
            if (segment == 2 && start[0] == '.' && start[1] == '.') return 0;
            segment = 0;
        } else {
            if (c == '\\' || c == ':' || c <= ' ' || c > '~') return 0;
            segment++;
        }
    }
    return 1;
}

/* Comma-separated [a-z0-9-]{1,32} tokens, no empty or repeated entry. */
static int parse_models(const char *value, char out[][GBB_CASES_MODEL_LEN + 1u], size_t *count) {
    size_t n = 0;
    const char *p = value;
    for (;;) {
        const char *comma = strchr(p, ',');
        size_t length = comma != NULL ? (size_t)(comma - p) : strlen(p);
        if (!is_token(p, length, 1, GBB_CASES_MODEL_LEN) || n == GBB_CASES_MAX_MODELS) return 0;
        memcpy(out[n], p, length);
        out[n][length] = '\0';
        for (size_t i = 0; i < n; i++) {
            if (strcmp(out[i], out[n]) == 0) return 0;
        }
        n++;
        if (comma == NULL) break;
        p = comma + 1;
    }
    *count = n;
    return 1;
}

static int list_contains(char list[][GBB_CASES_MODEL_LEN + 1u], size_t count, const char *model) {
    for (size_t i = 0; i < count; i++) {
        if (strcmp(list[i], model) == 0) return 1;
    }
    return 0;
}

/* Copies a value that must fit; the destination is sized by the caller. */
static int copy_token(char *dst, size_t dst_size, const char *value, size_t min) {
    size_t n = strlen(value);
    if (!is_token(value, n, min, dst_size - 1u)) return 0;
    memcpy(dst, value, n + 1u);
    return 1;
}

/* Applies one key=value pair; returns NULL or the rejection reason. */
static const char *apply(gbb_case *c, int key, const char *value) {
    uint64_t number = 0;
    switch (key) {
    case K_ID:
        return copy_token(c->id, sizeof(c->id), value, 1) ? NULL : "bad-id";
    case K_ROM:
        if (!gbb_cases_path_valid(value)) return "bad-path";
        strcpy(c->rom, value);
        return NULL;
    case K_ROM_SHA256:
        if (!is_lower_hex(value, 64)) return "bad-digest";
        strcpy(c->rom_sha256, value);
        return NULL;
    case K_ROM_SIZE:
        if (!parse_u64(value, GBB_CASES_MAX_ROM_BYTES, &number)) return "bad-number";
        c->rom_size = (uint32_t)number;
        return NULL;
    case K_ORACLE:
        if (strcmp(value, "progress-predicate") == 0) {
            c->oracle = GBB_ORACLE_PROGRESS_PREDICATE;
        } else if (strcmp(value, "frame-digest@ldbb") == 0) {
            c->oracle = GBB_ORACLE_FRAME_DIGEST_LDBB;
        } else if (strncmp(value, "frame-digest@t=", 15) == 0) {
            if (!parse_u64(value + 15, GBB_ACCEPT_MAX_SCRIPT_HALF_DOTS, &number)) return "bad-number";
            c->oracle = GBB_ORACLE_FRAME_DIGEST_AT;
            c->oracle_half_dots = number;
        } else if (strcmp(value, "fibonacci-ldbb") == 0 || strcmp(value, "screen-text") == 0) {
            return "rejected-oracle";
        } else {
            return "unknown-oracle";
        }
        return NULL;
    case K_REFERENCE_DIGEST:
        if (!is_lower_hex(value, 64)) return "bad-digest";
        strcpy(c->reference_digest, value);
        return NULL;
    case K_INPUT_SCRIPT:
        if (!gbb_cases_path_valid(value)) return "bad-path";
        strcpy(c->input_script, value);
        return NULL;
    case K_INPUT_SHA256:
        if (!is_lower_hex(value, 64)) return "bad-digest";
        strcpy(c->input_sha256, value);
        return NULL;
    case K_BUDGET:
        if (!parse_u64(value, GBB_ACCEPT_MAX_SCRIPT_HALF_DOTS, &number)) return "bad-number";
        c->budget_half_dots = number;
        return NULL;
    case K_MODEL_PASS:
        return parse_models(value, c->model_pass, &c->model_pass_count) ? NULL : "bad-model-list";
    case K_MODEL_FAIL:
        return parse_models(value, c->model_fail, &c->model_fail_count) ? NULL : "bad-model-list";
    case K_EXPECT_FAIL_REASON:
        return copy_token(c->expect_fail_reason, sizeof(c->expect_fail_reason), value, 1)
                   ? NULL : "bad-reason";
    case K_TARGET_REVISION: {
        size_t n = strlen(value);
        if ((n != 40 && n != 64) || !is_lower_hex(value, n)) return "bad-revision";
        strcpy(c->target_revision, value);
        return NULL;
    }
    case K_PREDICATE:
        return copy_token(c->predicate, sizeof(c->predicate), value, 1) ? NULL : "bad-predicate";
    case K_EXPECT_HW:
        /* Open Question 4: the key is kept; only 0 is accepted this phase. */
        if (strcmp(value, "0") != 0) return "expect-hw-capability-unsupported";
        c->expect_hw_capability = 0;
        return NULL;
    default:
        return "unknown-key";
    }
}

/* Parses one non-blank, non-comment line (NUL-terminated, mutable). */
static int parse_line(char *line, gbb_case *c, size_t line_no, char *err, size_t err_capacity) {
    unsigned seen = 0;
    char *p = line;
    memset(c, 0, sizeof(*c));
    while (*p != '\0') {
        while (*p == ' ') p++;
        if (*p == '\0') break;
        char *token = p;
        while (*p != '\0' && *p != ' ') p++;
        if (*p == ' ') *p++ = '\0';
        char *equals = strchr(token, '=');
        if (equals == NULL || equals == token) return reject(err, err_capacity, "malformed-token", line_no);
        *equals = '\0';
        const char *value = equals + 1;
        if (*value == '\0') return reject(err, err_capacity, "empty-value", line_no);
        int key = -1;
        for (int k = 0; k < K_COUNT; k++) {
            if (strcmp(token, key_names[k]) == 0) { key = k; break; }
        }
        if (key < 0) {
            return reject(err, err_capacity,
                          strcmp(token, "rtc_policy") == 0 ? "rejected-key" : "unknown-key", line_no);
        }
        if (seen & (1u << key)) return reject(err, err_capacity, "duplicate-key", line_no);
        seen |= 1u << key;
        const char *reason = apply(c, key, value);
        if (reason != NULL) return reject(err, err_capacity, reason, line_no);
    }
    static const int required[] = {K_ID, K_ROM, K_ROM_SHA256, K_ROM_SIZE, K_ORACLE, K_BUDGET};
    for (size_t i = 0; i < sizeof(required) / sizeof(required[0]); i++) {
        if (!(seen & (1u << required[i]))) return reject(err, err_capacity, "missing-key", line_no);
    }
    if (((seen >> K_INPUT_SCRIPT) & 1u) != ((seen >> K_INPUT_SHA256) & 1u)) {
        return reject(err, err_capacity, "input-script-needs-digest", line_no);
    }
    if (c->oracle == GBB_ORACLE_PROGRESS_PREDICATE) {
        if (!(seen & (1u << K_PREDICATE)) || !(seen & (1u << K_INPUT_SCRIPT))) {
            return reject(err, err_capacity, "missing-key", line_no);
        }
    } else if (!(seen & (1u << K_REFERENCE_DIGEST))) {
        return reject(err, err_capacity, "missing-key", line_no);
    }
    for (size_t i = 0; i < c->model_pass_count; i++) {
        if (list_contains(c->model_fail, c->model_fail_count, c->model_pass[i])) {
            return reject(err, err_capacity, "model-in-pass-and-fail", line_no);
        }
    }
    return 0;
}

int gbb_cases_parse(const uint8_t *bytes, size_t length, gbb_case_list *out,
                    char *err, size_t err_capacity) {
    if (out != NULL) memset(out, 0, sizeof(*out));
    if (out == NULL || (bytes == NULL && length != 0)) return reject(err, err_capacity, "bad-argument", 0);
    if (length > GBB_CASES_MAX_BYTES) return reject(err, err_capacity, "file-too-large", 0);

    gbb_case_list list = {NULL, 0};
    list.cases = calloc(GBB_CASES_MAX_CASES, sizeof(*list.cases));
    if (list.cases == NULL) return 2;

    size_t pos = 0, line_no = 0;
    while (pos < length) {
        size_t end = pos;
        while (end < length && bytes[end] != '\n') end++;
        size_t line_length = end - pos;
        const uint8_t *text = bytes + pos;
        line_no++;
        pos = end < length ? end + 1u : end;

        if (line_length > 0 && text[line_length - 1u] == '\r') line_length--; /* CRLF */
        if (line_length > GBB_CASES_MAX_LINE) {
            gbb_cases_free(&list);
            return reject(err, err_capacity, "line-too-long", line_no);
        }
        char line[GBB_CASES_MAX_LINE + 1u];
        for (size_t i = 0; i < line_length; i++) {
            if (text[i] < 0x20 || text[i] > 0x7e) { /* controls, tabs, stray CR, NUL, non-ASCII */
                gbb_cases_free(&list);
                return reject(err, err_capacity, "bad-character", line_no);
            }
            line[i] = (char)text[i];
        }
        line[line_length] = '\0';

        const char *first = line;
        while (*first == ' ') first++;
        if (*first == '\0' || *first == '#') continue;

        if (list.count == GBB_CASES_MAX_CASES) {
            gbb_cases_free(&list);
            return reject(err, err_capacity, "too-many-cases", line_no);
        }
        gbb_case *c = &list.cases[list.count];
        if (parse_line(line, c, line_no, err, err_capacity) != 0) {
            gbb_cases_free(&list);
            return 1;
        }
        for (size_t i = 0; i < list.count; i++) {
            if (strcmp(list.cases[i].id, c->id) == 0) {
                gbb_cases_free(&list);
                return reject(err, err_capacity, "duplicate-id", line_no);
            }
        }
        list.count++;
    }
    if (list.count == 0) {
        gbb_cases_free(&list);
        return reject(err, err_capacity, "no-cases", 0);
    }
    *out = list;
    return 0;
}

void gbb_cases_free(gbb_case_list *list) {
    if (list == NULL) return;
    free(list->cases);
    list->cases = NULL;
    list->count = 0;
}

const gbb_case *gbb_cases_find(const gbb_case_list *list, const char *id) {
    if (list == NULL || id == NULL) return NULL;
    for (size_t i = 0; i < list->count; i++) {
        if (strcmp(list->cases[i].id, id) == 0) return &list->cases[i];
    }
    return NULL;
}

int gbb_case_model_known(const char *model) {
    return model != NULL && (strcmp(model, "dmg-cpu-b") == 0 || strcmp(model, "cgb-cpu-e") == 0);
}

static int has_model(const char list[][GBB_CASES_MODEL_LEN + 1u], size_t count, const char *model) {
    for (size_t i = 0; i < count; i++) {
        if (strcmp(list[i], model) == 0) return 1;
    }
    return 0;
}

gbb_case_applicability_kind gbb_case_applicability(const gbb_case *c, const char *model,
                                                   const char *revision) {
    if (revision == NULL) revision = model;
    gbb_case_applicability_kind kind;
    if (has_model(c->model_fail, c->model_fail_count, model)) {
        kind = GBB_CASE_EXPECT_FAIL;
    } else if (has_model(c->model_pass, c->model_pass_count, model)) {
        kind = GBB_CASE_EXPECT_PASS;
    } else {
        return GBB_CASE_EXCLUDED_MODEL;
    }
    if (c->target_revision[0] != '\0' && strcmp(c->target_revision, revision) != 0) {
        return GBB_CASE_EXCLUDED_REVISION;
    }
    return kind;
}
