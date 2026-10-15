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
 * The register visibility matrix is checked the same way (Plan 10-10): io_visibility[] against the
 * rows between the cgb-io-visibility markers. Every address FF00-FF7F must be classified in every
 * column (a zero-initialised hole is a failure); EXISTING rows are not published and must have no
 * doc row; every other cell has exactly one doc row that equals its rendering.
 *
 * The compat palette default (D-18) is checked the same way against the cgb-compat-palette block
 * and against the ramp rule recomputed here.
 *
 * Usage: test_cgb_tables postboot|postboot_selftest|io|compat_palette <doc.md>
 *        test_cgb_tables emit|emit_io    (prints the table rows for the doc maintainer) */
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
    "key1", "vram_bank", "svbk", "wram_bank", "bcps", "ocps", "ff56",
    "ff72", "ff73", "ff74", "ff75",
    "bg_cram_fill", "obj_cram_fill", "opri",
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
    /* FF56 now has instance-owned state. Keep its reset row in this table so creation, reset, and
     * successful-load initialization cannot be mistaken for an undocumented hardware power-up
     * value. The implementation/doc mirror below checks all three mode columns independently. */
    for (int col = 0; col < 3; ++col) {
        int found = 0;
        for (int i = 0; i < n; ++i)
            if (strcmp(g_doc[i].field, "ff56") == 0 &&
                strcmp(g_doc[i].column, column_names[col]) == 0) found = 1;
        if (!found) {
            printf("cgb-tables missing postboot field: ff56 %s\n", column_names[col]);
            return 1;
        }
    }
    if (check_all(post_boot, g_doc, n) != CHECK_OK) return 1;
    printf("cgb-tables postboot pass rows=%d\n", n);
    return 0;
}

static int io_selftest(const char *path);

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

    const int io_rejected = io_selftest(path);
    if (io_rejected != 11) {
        printf("cgb-tables self-test: io mutation accepted (rejected %d of 11)\n", io_rejected);
        return 1;
    }

    printf("cgb-tables self-test pass mutants=14\n");
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


/* ---- Register visibility (io_visibility[]) ------------------------------------------------- */

#define IO_MARK_BEGIN "<!-- cgb-io-visibility-begin -->"
#define IO_MARK_END "<!-- cgb-io-visibility-end -->"
#define MAX_IO_DOC_ROWS 512

typedef struct {
    char addr[12];
    char column[16];
    char read[64];
    char write[80];
    char status[24];
    char src[24];
} io_doc_row;

static const char *const io_src_names[] = { "?", "PANDOCS", "HW_TEST", "SAMEBOY", "POLICY", "EXISTING" };

static const io_cell *io_cell_of(const io_row *row, int col) {
    return col == 0 ? &row->dmg : col == 1 ? &row->cgb : &row->compat;
}

/* Canonical text of one cell. Returns 0 for a cell the doc does not publish (EXISTING), 1 for a
 * published cell and -1 for a hole (IO_UNSET or an unknown kind). */
static int render_io(const io_cell *c, int col, char *rd, size_t rd_n, char *wr, size_t wr_n,
                     char *st, size_t st_n) {
    snprintf(st, st_n, "IMPL");
    switch (c->kind) {
    case IO_EXISTING: return 0;
    case IO_DMG_STOP: snprintf(rd, rd_n, "stop"); snprintf(wr, wr_n, "ignored"); return 1;
    case IO_CONST_FF: snprintf(rd, rd_n, "$FF"); snprintf(wr, wr_n, "ignored"); return 1;
    case IO_KEY1: snprintf(rd, rd_n, "$7E, bit 7 speed, bit 0 armed"); snprintf(wr, wr_n, "bit 0 arms the switch"); return 1;
    case IO_VBK:
        snprintf(rd, rd_n, "$FE or bank");
        snprintf(wr, wr_n, col == 1 ? "bit 0 selects the bank" : "ignored, bank stays 0");
        return 1;
    case IO_SVBK:
        snprintf(rd, rd_n, "$F8 or raw bank bits");
        snprintf(wr, wr_n, "raw 3 bits stored, 0 selects bank 1");
        return 1;
    case IO_STORE:
        snprintf(rd, rd_n, "stored or $%02X", (unsigned)c->read_or);
        snprintf(wr, wr_n, "stored and $%02X", (unsigned)c->write_mask);
        return 1;
    case IO_BCPD:
        snprintf(rd, rd_n, "palette byte at index, $FF while mode 3");
        snprintf(wr, wr_n, "stores at index, auto-increments even when blocked");
        return 1;
    case IO_OCPD:
        snprintf(rd, rd_n, "palette byte at index, $FF while mode 3");
        snprintf(wr, wr_n, "stores at index, auto-increments even when blocked");
        return 1;
    case IO_OPRI:
        snprintf(rd, rd_n, "$FE or bit 0");
        snprintf(wr, wr_n, "bit 0 stored, no priority effect after boot");
        return 1;
    case IO_PCM12:
        snprintf(rd, rd_n, "channel 2:channel 1 digital DAC values");
        snprintf(wr, wr_n, "ignored");
        return 1;
    case IO_PCM34:
        snprintf(rd, rd_n, "channel 4:channel 3 digital DAC values");
        snprintf(wr, wr_n, "ignored");
        return 1;
    case IO_DEFERRED_RW:
        snprintf(rd, rd_n, "stop");
        snprintf(wr, wr_n, "dropped, stop after retire");
        snprintf(st, st_n, "DEFERRED(%u)", (unsigned)c->phase);
        return 1;
    case IO_DEFERRED_W:
        snprintf(rd, rd_n, "$FF");
        snprintf(wr, wr_n, "dropped, stop after retire");
        snprintf(st, st_n, "DEFERRED(%u)", (unsigned)c->phase);
        return 1;
    default: return -1;
    }
}

static int parse_io_doc(const char *path, io_doc_row *rows, int max_rows) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) {
        fprintf(stderr, "cgb-tables cannot open %s\n", path);
        return -1;
    }
    char line[1024];
    int inside = 0, begun = 0, ended = 0, n = 0;
    while (fgets(line, sizeof(line), f) != NULL) {
        if (strstr(line, IO_MARK_BEGIN) != NULL) { inside = 1; ++begun; continue; }
        if (strstr(line, IO_MARK_END) != NULL) { inside = 0; ++ended; continue; }
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
        if (strcmp(cells[0], "address") == 0 || cells[0][0] == '-') continue;
        if (n >= max_rows || cells[0][0] != '$' || strlen(cells[0]) >= sizeof(rows->addr) ||
            strlen(cells[1]) >= sizeof(rows->column) || strlen(cells[2]) >= sizeof(rows->read) ||
            strlen(cells[3]) >= sizeof(rows->write) || strlen(cells[4]) >= sizeof(rows->status) ||
            strlen(cells[5]) >= sizeof(rows->src)) {
            fprintf(stderr, "cgb-tables malformed row: %s\n", cells[0]);
            fclose(f);
            return -1;
        }
        io_doc_row *r = &rows[n++];
        snprintf(r->addr, sizeof(r->addr), "%s", cells[0]);
        snprintf(r->column, sizeof(r->column), "%s", cells[1]);
        snprintf(r->read, sizeof(r->read), "%s", cells[2]);
        snprintf(r->write, sizeof(r->write), "%s", cells[3]);
        snprintf(r->status, sizeof(r->status), "%s", cells[4]);
        snprintf(r->src, sizeof(r->src), "%s", cells[5]);
    }
    fclose(f);
    if (begun != 1 || ended != 1) {
        fprintf(stderr, "cgb-tables markers: io begin=%d end=%d (each must appear once)\n", begun, ended);
        return -1;
    }
    return n;
}

static void io_addr_text(unsigned index, char *out, size_t n) { snprintf(out, n, "$FF%02X", index); }

/* Independent PCM policy oracle: D-10 settles the native CGB, compatibility, and DMG cells.
 * CGB mode exposes read-only PCM values, compatibility mode reads $FF, and the DMG profile keeps
 * its fail-closed stop. The docs mirror remains a separate code/table comparison. */
static int pcm_io_contract(const io_row *code) {
    static const unsigned addresses[] = { 0x76u, 0x77u };
    static const uint8_t cgb_kinds[] = { IO_PCM12, IO_PCM34 };
    for (size_t i = 0; i < sizeof(addresses) / sizeof(addresses[0]); ++i) {
        const io_row *row = &code[addresses[i]];
        if (row->dmg.kind != IO_DMG_STOP || row->cgb.kind != cgb_kinds[i] ||
            row->compat.kind != IO_CONST_FF || row->src != IOS_PANDOCS)
            return 0;
    }
    return 1;
}

/* Independent undocumented-port oracle for D-04/D-10. Compatibility FF72/73 remain stored,
 * FF74 is absent, and FF75 stores only bits 4-6. These expectations do not come from the rows
 * being checked. */
static int undocumented_io_contract(const io_row *code) {
    for (unsigned address = 0x72u; address <= 0x73u; ++address) {
        const io_row *row = &code[address];
        if (row->src != IOS_SAMEBOY || row->dmg.kind != IO_DMG_STOP ||
            row->cgb.kind != IO_STORE || row->cgb.read_or != 0u || row->cgb.write_mask != 0xFFu ||
            row->compat.kind != IO_STORE || row->compat.read_or != 0u ||
            row->compat.write_mask != 0xFFu) return 0;
    }
    const io_row *ff74 = &code[0x74];
    if (ff74->src != IOS_SAMEBOY || ff74->dmg.kind != IO_DMG_STOP ||
        ff74->cgb.kind != IO_STORE || ff74->cgb.read_or != 0u || ff74->cgb.write_mask != 0xFFu ||
        ff74->compat.kind != IO_CONST_FF) return 0;
    const io_row *ff75 = &code[0x75];
    if (ff75->src != IOS_PANDOCS || ff75->dmg.kind != IO_DMG_STOP) return 0;
    for (int col = 1; col < 3; ++col) {
        const io_cell *cell = io_cell_of(ff75, col);
        if (cell->kind != IO_STORE || cell->read_or != 0x8Fu || cell->write_mask != 0x70u)
            return 0;
    }
    return 1;
}

static int io_mismatch(const char *addr, const char *column) {
    printf("cgb-tables mismatch: %s %s\n", addr, column);
    return 1;
}

/* Two-way diff of a row array against the parsed doc. Returns 0 on equality. */
static int compare_io(const io_row *code, const io_doc_row *doc, int ndoc) {
    for (unsigned i = 0; i < IO_VISIBILITY_ROWS; ++i) {
        char addr[12];
        io_addr_text(i, addr, sizeof(addr));
        for (int col = 0; col < 3; ++col) {
            char rd[64], wr[80], st[24];
            const int published = render_io(io_cell_of(&code[i], col), col, rd, sizeof(rd), wr, sizeof(wr), st, sizeof(st));
            if (published < 0) return io_mismatch(addr, column_names[col]);
            int found = 0;
            for (int j = 0; j < ndoc; ++j) {
                if (strcmp(doc[j].addr, addr) != 0 || strcmp(doc[j].column, column_names[col]) != 0) continue;
                ++found;
                if (published == 0 || strcmp(doc[j].read, rd) != 0 || strcmp(doc[j].write, wr) != 0 ||
                    strcmp(doc[j].status, st) != 0 || strcmp(doc[j].src, io_src_names[code[i].src]) != 0)
                    return io_mismatch(addr, column_names[col]);
            }
            if (found != (published ? 1 : 0)) return io_mismatch(addr, column_names[col]);
        }
    }
    for (int j = 0; j < ndoc; ++j) {
        int known = 0;
        for (unsigned i = 0; i < IO_VISIBILITY_ROWS && !known; ++i) {
            char addr[12];
            io_addr_text(i, addr, sizeof(addr));
            for (int col = 0; col < 3; ++col)
                if (strcmp(doc[j].addr, addr) == 0 && strcmp(doc[j].column, column_names[col]) == 0) { known = 1; break; }
        }
        if (!known) return io_mismatch(doc[j].addr, doc[j].column);
    }
    return 0;
}

static io_doc_row g_io_doc[MAX_IO_DOC_ROWS];
static io_row g_io_copy[IO_VISIBILITY_ROWS];

static int case_io(const char *path) {
    const int n = parse_io_doc(path, g_io_doc, MAX_IO_DOC_ROWS);
    if (n < 0) return 1;
    if (!pcm_io_contract(io_visibility)) {
        printf("cgb-tables PCM policy mismatch: native/compat/DMG FF76-FF77\n");
        return 1;
    }
    if (!undocumented_io_contract(io_visibility)) {
        printf("cgb-tables undocumented-port policy mismatch: FF72-FF75\n");
        return 1;
    }
    if (compare_io(io_visibility, g_io_doc, n) != 0) return 1;
    printf("cgb-tables io pass rows=%d\n", n);
    return 0;
}

/* Mutants of the io check, run from the postboot self-test. Returns the number of mutants rejected,
 * or -1 when the unmutated tables are not accepted (the mutants would prove nothing). */
static int io_selftest(const char *path) {
    const int n = parse_io_doc(path, g_io_doc, MAX_IO_DOC_ROWS);
    if (n < 0) return -1;
    memcpy(g_io_copy, io_visibility, sizeof(g_io_copy));
    if (!pcm_io_contract(g_io_copy) || !undocumented_io_contract(g_io_copy) ||
        compare_io(g_io_copy, g_io_doc, n) != 0) return -1;
    int rejected = 0;

    /* (d) an io row removed from the code copy (reclassified as handled elsewhere). */
    g_io_copy[0x4C].cgb.kind = IO_EXISTING;
    if (compare_io(g_io_copy, g_io_doc, n) != 0) ++rejected;

    /* (e) a hole: a zero-initialised row. */
    memcpy(g_io_copy, io_visibility, sizeof(g_io_copy));
    memset(&g_io_copy[0x55], 0, sizeof(g_io_copy[0x55]));
    if (compare_io(g_io_copy, g_io_doc, n) != 0) ++rejected;

    /* (f) a doc row removed. */
    memcpy(g_io_copy, io_visibility, sizeof(g_io_copy));
    {
        static io_doc_row shortened[MAX_IO_DOC_ROWS];
        memcpy(shortened, g_io_doc, sizeof(io_doc_row) * (size_t)n);
        memmove(&shortened[10], &shortened[11], sizeof(io_doc_row) * (size_t)(n - 11));
        if (compare_io(io_visibility, shortened, n - 1) != 0) ++rejected;
    }

    /* (g-i) Catch the superseded dispositions independently of the documentation mirror for
     * both PCM registers: deferred CGB, readable compat, or non-stopping DMG cells are invalid. */
    for (unsigned i = 0; i < 2; ++i) {
        const unsigned address = i == 0 ? 0x76u : 0x77u;
        memcpy(g_io_copy, io_visibility, sizeof(g_io_copy));
        g_io_copy[address].cgb.kind = IO_DEFERRED_RW;
        if (!pcm_io_contract(g_io_copy)) ++rejected;

        memcpy(g_io_copy, io_visibility, sizeof(g_io_copy));
        g_io_copy[address].compat.kind = i == 0 ? IO_PCM12 : IO_PCM34;
        if (!pcm_io_contract(g_io_copy)) ++rejected;

        memcpy(g_io_copy, io_visibility, sizeof(g_io_copy));
        g_io_copy[address].dmg.kind = IO_CONST_FF;
        if (!pcm_io_contract(g_io_copy)) ++rejected;
    }
    memcpy(g_io_copy, io_visibility, sizeof(g_io_copy));
    g_io_copy[0x75].cgb.write_mask = 0xF0u;
    if (!undocumented_io_contract(g_io_copy)) ++rejected;

    memcpy(g_io_copy, io_visibility, sizeof(g_io_copy));
    g_io_copy[0x74].compat = (io_cell){ IO_STORE, 0u, 0u, 0xFFu };
    if (!undocumented_io_contract(g_io_copy)) ++rejected;
    return rejected;
}

static int case_emit_io(void) {
    for (unsigned i = 0; i < IO_VISIBILITY_ROWS; ++i)
        for (int col = 0; col < 3; ++col) {
            char addr[12], rd[64], wr[80], st[24];
            if (render_io(io_cell_of(&io_visibility[i], col), col, rd, sizeof(rd), wr, sizeof(wr), st, sizeof(st)) != 1)
                continue;
            io_addr_text(i, addr, sizeof(addr));
            printf("| %s | %s | %s | %s | %s | %s |\n", addr, column_names[col], rd, wr, st,
                   io_src_names[io_visibility[i].src]);
        }
    return 0;
}

/* D-18: the doc block, compat_default_rgb555 and the rule agree. The rule is recomputed here so a
 * change to the code table and the doc together still fails if it leaves the rule. */
static int case_compat_palette(const char *path) {
    static const char *const sets[3] = { "BG", "OBJ0", "OBJ1" };
    static const unsigned ramp[4] = { 31u, 21u, 11u, 1u };
    FILE *f = fopen(path, "rb");
    if (f == NULL) {
        fprintf(stderr, "cgb-tables cannot open %s\n", path);
        return 1;
    }
    char line[512];
    int inside = 0, begun = 0, ended = 0, rows = 0;
    while (fgets(line, sizeof(line), f) != NULL) {
        if (strstr(line, "<!-- cgb-compat-palette-begin -->") != NULL) { inside = 1; ++begun; continue; }
        if (strstr(line, "<!-- cgb-compat-palette-end -->") != NULL) { inside = 0; ++ended; continue; }
        if (!inside || line[0] != '|') continue;
        char *cells[5];
        char *p = line + 1;
        int k = 0;
        for (; k < 5; ++k) {
            char *bar = strchr(p, '|');
            if (bar == NULL) break;
            *bar = '\0';
            cells[k] = trim(p);
            p = bar + 1;
        }
        if (k != 5) { fprintf(stderr, "cgb-tables malformed row: %s", line); fclose(f); return 1; }
        if (strcmp(cells[0], "set") == 0 || cells[0][0] == '-') continue;
        int set = -1;
        for (int i = 0; i < 3; ++i) if (strcmp(cells[0], sets[i]) == 0) set = i;
        if (set < 0 || set != rows) { printf("cgb-tables mismatch: compat %s\n", cells[0]); fclose(f); return 1; }
        for (int shade = 0; shade < 4; ++shade) {
            const char *cell = cells[1 + shade];
            char *end = NULL;
            unsigned long doc = cell[0] == '$' ? strtoul(cell + 1, &end, 16) : 0xFFFFFFFFul;
            const unsigned y = ramp[shade];
            const unsigned rule = y | ((y - (y >> 3)) << 5) | ((y - (y >> 2)) << 10);
            if (cell[0] != '$' || end == NULL || *end != '\0' || doc != compat_default_rgb555[set][shade] ||
                doc != rule || doc > 0x7FFFul) {
                printf("cgb-tables mismatch: compat %s shade %d\n", sets[set], shade);
                fclose(f);
                return 1;
            }
        }
        ++rows;
    }
    fclose(f);
    if (begun != 1 || ended != 1 || rows != 3) {
        printf("cgb-tables mismatch: compat markers or row count (%d rows)\n", rows);
        return 1;
    }
    puts("cgb-tables compat_palette pass rows=3");
    return 0;
}

int main(int argc, char **argv) {
    _Static_assert(sizeof(field_names) / sizeof(field_names[0]) == PB_FIELD_COUNT,
                   "field_names must cover every post_boot_field");
    if (argc >= 2 && strcmp(argv[1], "emit") == 0) return case_emit();
    if (argc >= 2 && strcmp(argv[1], "emit_io") == 0) return case_emit_io();
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
    if (strcmp(argv[1], "io") == 0) return case_io(argv[2]);
    if (strcmp(argv[1], "compat_palette") == 0) return case_compat_palette(argv[2]);
    fprintf(stderr, "unknown case %s\n", argv[1]);
    return 2;
}
