#ifndef GBB_RUNNER_ACCEPTANCE_H
#define GBB_RUNNER_ACCEPTANCE_H

/* Case-file parser and acceptance run entry points for gabbaboy-runner
 * (--acceptance <cases.txt> --case <id> [--receipt]).
 *
 * The parser is pure: it reads a caller-supplied byte buffer and touches no
 * file, clock or global. The run entry points own every heap buffer they
 * allocate and free it on every exit path. Paths in a case file are relative
 * to the process working directory; the repository CTests set that directory
 * to the repository root. */

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- Case-file limits (D-21, D-28) ---- */
#define GBB_CASES_MAX_BYTES 65536u
#define GBB_CASES_MAX_LINE 1024u
#define GBB_CASES_MAX_CASES 128u
#define GBB_CASES_MAX_PATH 255u
#define GBB_CASES_MAX_MODELS 8u
#define GBB_CASES_MODEL_LEN 32u
#define GBB_CASES_MAX_ROM_BYTES 8388608u /* one 8 MiB cap for every ROM buffer (D-27) */

typedef enum {
    GBB_ORACLE_PROGRESS_PREDICATE = 0,
    GBB_ORACLE_FRAME_DIGEST_LDBB,  /* frame-digest@ldbb */
    GBB_ORACLE_FRAME_DIGEST_AT     /* frame-digest@t=<half-dots>, see oracle_half_dots */
} gbb_case_oracle;

typedef struct {
    char id[49];
    char rom[GBB_CASES_MAX_PATH + 1u];
    char rom_sha256[65];
    uint32_t rom_size;
    gbb_case_oracle oracle;
    uint64_t oracle_half_dots;   /* FRAME_DIGEST_AT only */
    char reference_digest[65];   /* empty when the key is absent */
    char input_script[GBB_CASES_MAX_PATH + 1u];  /* empty when absent */
    char input_sha256[65];
    uint64_t budget_half_dots;
    char model_pass[GBB_CASES_MAX_MODELS][GBB_CASES_MODEL_LEN + 1u];
    size_t model_pass_count;
    char model_fail[GBB_CASES_MAX_MODELS][GBB_CASES_MODEL_LEN + 1u];
    size_t model_fail_count;
    char expect_fail_reason[65]; /* empty when absent */
    char target_revision[65];    /* empty when absent */
    char predicate[49];          /* empty when absent */
    uint8_t expect_hw_capability; /* only 0 is accepted in this phase */
} gbb_case;

typedef struct {
    gbb_case *cases;
    size_t count;
} gbb_case_list;

/* Parses the whole file before returning. Returns 0 on success, 1 for an
 * invalid file (err receives "invalid-cases: <reason> line=<n>", line 0 for a
 * whole-file limit), 2 when allocation fails. On failure *out is left empty
 * and nothing was retained. err may be NULL when err_capacity is 0. */
int gbb_cases_parse(const uint8_t *bytes, size_t length, gbb_case_list *out,
                    char *err, size_t err_capacity);
void gbb_cases_free(gbb_case_list *list);
/* Returns the case with this id, or NULL. */
const gbb_case *gbb_cases_find(const gbb_case_list *list, const char *id);

/* Relative-path rule (T-07-05): non-empty, at most GBB_CASES_MAX_PATH bytes,
 * printable ASCII without spaces, no leading '/', no backslash, no colon, no
 * empty, "." or ".." segment (so no trailing slash either). Returns 1 when
 * the path is acceptable, 0 otherwise. */
int gbb_cases_path_valid(const char *path);

/* Reads a whole file into a fresh heap buffer. Returns 0 on success (caller
 * frees *out; a zero-length file yields a non-NULL buffer), 1 when the file
 * cannot be opened, 2 when it is larger than capacity or a read fails, 3 when
 * allocation fails. Capacity+1 bytes are read so oversize files are detected
 * without truncation. */
int gbb_runner_read_file(const char *path, size_t capacity, uint8_t **out, size_t *length);

typedef struct {
    int receipt;                  /* print a provenance line after the status line */
    const char *core_revision;    /* optional, for the receipt */
    int build_qualified;
} gbb_acceptance_options;

/* Runs one parsed case on DMG-CPU-B. Exit codes: 0 pass, 1 fail, 2 invalid
 * input (every input check completes before an instance is created), 3
 * unsupported or stopped. Status goes to stdout, input errors to stderr. */
int gbb_acceptance_run_case(const gbb_case *c, const gbb_acceptance_options *options);
/* Reads and fully validates cases_path, then runs the selected case. */
int gbb_acceptance_run_file(const char *cases_path, const char *case_id,
                            const gbb_acceptance_options *options);

#ifdef __cplusplus
}
#endif
#endif
