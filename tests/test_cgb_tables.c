/* Code-versus-doc check for the post-boot table (D-06, D-07).
 *
 * docs/cgb-profile.md mirrors post_boot[] between two marker comments, one row per field and
 * column. This single-TU white-box test includes the core to reach the static table, parses the
 * doc, and fails on any difference in either direction. It also enforces the provenance rules on
 * the code table itself:
 *   - a POLICY cell must carry a non-empty reason;
 *   - HW_TEST is only legitimate in the COMPAT column, because no hardware test covers CGB mode
 *     and the DMG column records the implemented value, not a hardware measurement.
 * It must not link GabbaBoy::core (the core is included here).
 *
 * Usage: test_cgb_tables postboot|postboot_selftest <doc.md>
 *        test_cgb_tables emit            (prints the table rows for the doc maintainer) */
#include "../src/core/gabbaboy.c"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *const field_names[PB_FIELD_COUNT] = {
    "a", "f", "b", "c", "d", "e", "h", "l", "sp", "pc",
    "div", "divider_counter", "divider_phase",
    "tima", "tma", "tac",
    "serial_data", "serial_control",
    "ie", "if", "ime",
    "nr11", "nr12", "ch1_enabled",
    "nr50", "nr51", "apu_power",
    "dma_register",
    "lcdc", "stat", "ly", "lyc", "scx", "scy", "wx", "wy",
    "bgp", "obp0", "obp1", "ppu_mode",
    "joypad_select", "joypad_buttons",
    "ram_fill",
};

static const char *const column_names[3] = { "DMG", "CGB", "COMPAT" };

static const char *const prov_names[] = {
    "?", "HW_TEST", "PANDOCS", "ORACLE_SAMEBOY", "POLICY", "HEADER_DERIVED"
};

#define MARK_BEGIN "<!-- cgb-post-boot-begin -->"
#define MARK_END "<!-- cgb-post-boot-end -->"
#define MAX_DOC_ROWS 256
#define REASON_MAX 384

typedef struct {
    char field[32];
    char column[16];
    unsigned value;
    char prov[24];
    unsigned src;
    char reason[REASON_MAX];
} doc_row;

typedef enum {
    CHECK_OK = 0,
    CHECK_MISMATCH,
    CHECK_POLICY_WITHOUT_REASON,
    CHECK_HW_OUTSIDE_COMPAT
} check_result;

static const post_boot_cell *cell_of(const post_boot_row *row, int col) {
    return col == 0 ? &row->dmg : col == 1 ? &row->cgb : &row->compat;
}

static char *trim(char *s) {
    while (*s == ' ') ++s;
    char *end = s + strlen(s);
    while (end > s && (end[-1] == ' ' || end[-1] == '\r' || end[-1] == '\n')) *--end = '\0';
    return s;
}

/* Parse the marker-delimited table. Returns the row count, or -1 on a malformed doc. */
static int parse_doc(const char *path, doc_row *rows, int max_rows) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) {
        fprintf(stderr, "cgb-tables cannot open %s\n", path);
        return -1;
    }
    char line[1024];
    int inside = 0, begun = 0, ended = 0, n = 0;
    while (fgets(line, sizeof(line), f) != NULL) {
        if (strstr(line, MARK_BEGIN) != NULL) { inside = 1; ++begun; continue; }
        if (strstr(line, MARK_END) != NULL) { inside = 0; ++ended; continue; }
        if (!inside || line[0] != '|') continue;
        char *cells[6];
        char *p = line + 1;
        int k = 0;
        for (; k < 6; ++k) {
            char *bar = strchr(p, '|');
            if (bar == NULL) break;
            *bar = '\0';
            cells[k] = trim(p);
            p = bar + 1;
        }
        if (k != 6) { fprintf(stderr, "cgb-tables malformed row: %s", line); fclose(f); return -1; }
        if (strcmp(cells[0], "field") == 0 || cells[0][0] == '-') continue; /* header, separator */
        if (n >= max_rows || cells[2][0] != '$' || strlen(cells[0]) >= sizeof(rows->field) ||
            strlen(cells[1]) >= sizeof(rows->column) || strlen(cells[3]) >= sizeof(rows->prov) ||
            strlen(cells[5]) >= sizeof(rows->reason)) {
            fprintf(stderr, "cgb-tables malformed row: %s", cells[0]);
            fclose(f);
            return -1;
        }
        doc_row *r = &rows[n++];
        snprintf(r->field, sizeof(r->field), "%s", cells[0]);
        snprintf(r->column, sizeof(r->column), "%s", cells[1]);
        r->value = (unsigned)strtoul(cells[2] + 1, NULL, 16);
        snprintf(r->prov, sizeof(r->prov), "%s", cells[3]);
        r->src = (unsigned)strtoul(cells[4], NULL, 10);
        snprintf(r->reason, sizeof(r->reason), "%s", cells[5]);
    }
    fclose(f);
    if (begun != 1 || ended != 1) {
        fprintf(stderr, "cgb-tables markers: begin=%d end=%d (each must appear once)\n", begun, ended);
        return -1;
    }
    return n;
}

static check_result report(check_result r, const char *field, const char *column) {
    switch (r) {
    case CHECK_MISMATCH: printf("cgb-tables mismatch: %s %s\n", field, column); break;
    case CHECK_POLICY_WITHOUT_REASON: printf("cgb-tables policy-without-reason: %s %s\n", field, column); break;
    case CHECK_HW_OUTSIDE_COMPAT: printf("cgb-tables hw-test-outside-compat: %s %s\n", field, column); break;
    case CHECK_OK: break;
    }
    return r;
}

/* Two-way row diff: every code cell has exactly one equal doc row, and every doc row names a real
 * field and column. Works on any row array so the self-test can feed it mutated copies. */
static check_result compare_tables(const post_boot_row *code, const doc_row *doc, int ndoc) {
    for (int i = 0; i < PB_FIELD_COUNT; ++i) {
        for (int col = 0; col < 3; ++col) {
            const post_boot_cell *c = cell_of(&code[i], col);
            int found = 0;
            for (int j = 0; j < ndoc; ++j) {
                if (strcmp(doc[j].field, field_names[code[i].field]) != 0 ||
                    strcmp(doc[j].column, column_names[col]) != 0) continue;
                ++found;
                if (doc[j].value != c->value || strcmp(doc[j].prov, prov_names[c->prov]) != 0 ||
                    doc[j].src != c->src_id || strcmp(doc[j].reason, c->reason == NULL ? "" : c->reason) != 0)
                    return report(CHECK_MISMATCH, field_names[code[i].field], column_names[col]);
            }
            if (found != 1) return report(CHECK_MISMATCH, field_names[code[i].field], column_names[col]);
        }
    }
    for (int j = 0; j < ndoc; ++j) {
        int known = 0;
        for (int i = 0; i < PB_FIELD_COUNT && !known; ++i)
            for (int col = 0; col < 3; ++col)
                if (strcmp(doc[j].field, field_names[code[i].field]) == 0 &&
                    strcmp(doc[j].column, column_names[col]) == 0) { known = 1; break; }
        if (!known) return report(CHECK_MISMATCH, doc[j].field, doc[j].column);
    }
    return CHECK_OK;
}

/* Provenance rules on the code table. */
static check_result check_provenance(const post_boot_row *code) {
    for (int i = 0; i < PB_FIELD_COUNT; ++i) {
        for (int col = 0; col < 3; ++col) {
            const post_boot_cell *c = cell_of(&code[i], col);
            if (c->prov == PROV_POLICY && (c->reason == NULL || c->reason[0] == '\0'))
                return report(CHECK_POLICY_WITHOUT_REASON, field_names[code[i].field], column_names[col]);
            if (c->prov == PROV_HW_TEST && col != 2)
                return report(CHECK_HW_OUTSIDE_COMPAT, field_names[code[i].field], column_names[col]);
        }
    }
    return CHECK_OK;
}

static check_result check_all(const post_boot_row *code, const doc_row *doc, int ndoc) {
    check_result r = check_provenance(code);
    return r != CHECK_OK ? r : compare_tables(code, doc, ndoc);
}

static doc_row g_doc[MAX_DOC_ROWS];

static int case_postboot(const char *path) {
    const int n = parse_doc(path, g_doc, MAX_DOC_ROWS);
    if (n < 0) return 1;
    if (check_all(post_boot, g_doc, n) != CHECK_OK) return 1;
    printf("cgb-tables postboot pass rows=%d\n", n);
    return 0;
}

static post_boot_row g_copy[PB_FIELD_COUNT];

static int case_selftest(const char *path) {
    const int n = parse_doc(path, g_doc, MAX_DOC_ROWS);
    if (n < 0) return 1;

    /* The unmutated copy must pass, or the mutants below prove nothing. */
    memcpy(g_copy, post_boot, sizeof(g_copy));
    if (check_all(g_copy, g_doc, n) != CHECK_OK) {
        printf("cgb-tables self-test: unmutated copy rejected\n");
        return 1;
    }

    /* (a) one DMG cell value changed -> the diff against the real doc must reject it. */
    memcpy(g_copy, post_boot, sizeof(g_copy));
    g_copy[PB_A].dmg.value ^= 1u;
    if (check_all(g_copy, g_doc, n) != CHECK_MISMATCH) goto accepted;

    /* (b) a POLICY cell with its reason cleared. */
    memcpy(g_copy, post_boot, sizeof(g_copy));
    if (g_copy[PB_DIVIDER_COUNTER].dmg.prov != PROV_POLICY) goto accepted;
    g_copy[PB_DIVIDER_COUNTER].dmg.reason = "";
    if (check_all(g_copy, g_doc, n) != CHECK_POLICY_WITHOUT_REASON) goto accepted;

    /* (c) a CGB-column cell relabelled HW_TEST. */
    memcpy(g_copy, post_boot, sizeof(g_copy));
    g_copy[PB_A].cgb.prov = PROV_HW_TEST;
    if (check_all(g_copy, g_doc, n) != CHECK_HW_OUTSIDE_COMPAT) goto accepted;

    printf("cgb-tables self-test pass mutants=3\n");
    return 0;
accepted:
    printf("cgb-tables self-test: mutation accepted\n");
    return 1;
}

/* Print the table rows in the doc's format so a maintainer can refresh the mirror. */
static int case_emit(void) {
    for (int i = 0; i < PB_FIELD_COUNT; ++i)
        for (int col = 0; col < 3; ++col) {
            const post_boot_cell *c = cell_of(&post_boot[i], col);
            printf("| %s | %s | $%0*X | %s | %u | %s |\n", field_names[post_boot[i].field],
                   column_names[col], post_boot[i].field == PB_SP || post_boot[i].field == PB_PC ||
                   post_boot[i].field == PB_DIVIDER_COUNTER ? 4 : 2, (unsigned)c->value,
                   prov_names[c->prov], (unsigned)c->src_id, c->reason);
        }
    return 0;
}

int main(int argc, char **argv) {
    _Static_assert(sizeof(field_names) / sizeof(field_names[0]) == PB_FIELD_COUNT,
                   "field_names must cover every post_boot_field");
    if (argc >= 2 && strcmp(argv[1], "emit") == 0) return case_emit();
    if (argc < 3) {
        fprintf(stderr, "usage: test_cgb_tables postboot|postboot_selftest <doc.md>\n");
        return 2;
    }
    for (int i = 0; i < PB_FIELD_COUNT; ++i)
        if (post_boot[i].field != (uint8_t)i) {
            fprintf(stderr, "cgb-tables post_boot[] is not indexed by field at %d\n", i);
            return 1;
        }
    if (strcmp(argv[1], "postboot") == 0) return case_postboot(argv[2]);
    if (strcmp(argv[1], "postboot_selftest") == 0) return case_selftest(argv[2]);
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
