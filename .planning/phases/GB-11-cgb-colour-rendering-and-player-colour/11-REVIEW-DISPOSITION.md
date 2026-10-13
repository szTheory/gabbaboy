---
phase: 11
review: 11-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: no_change_needed
    title: "Compat ppu_disabled_state test said to be unable to tell pass from fail"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "acid2 runner: manifest errors exit like a frame mismatch; pin hash and use read the file twice"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "reproduce-cgb-colour.sh: missing pin keys compare equal; tool failures reported as result=differs"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "create_machine overwrites the battery status with the CGB-only note"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "capture_format silently falls back to the DMG store when gbb_get_info fails"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "RGB555 accept helpers do not check alignment or NULL path/out"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "Mutant failure regexes are single common words; fuzz contract failures print the same text"
  - id: IN-05
    severity: info
    disposition: fixed
    title: "cgb_measure_core_unknown_profile passes a known profile name"
---

# Phase 11 — Code Review Disposition

| ID | Severity | Disposition | Commit | Evidence |
|----|----------|-------------|--------|----------|
| WR-01 | warning | no_change_needed | 452ec35 | The ROM paints colour index 1, not 0: the pass path writes BGP 0x00 (shade 0) and the fail path 0x0C (shade 3), so the compat frame differs by verdict. The misleading test comment and ELIGIBILITY.md wording were corrected, and a new mutant `magentests_lcd_off_no_mode0_compat` (core skips STAT mode 0) fails with `pixel 0,0 expected 0x639F got 0x0421`; its control passes. |
| WR-02 | warning | fixed | 2de610e | Manifest/usage errors exit 3 (`acid2 error: manifest unusable`), distinct from a frame mismatch; ROM and reference are read once and the hashed bytes are used. `cgb_acid2_local_bad_manifest`; self-test `checks=5`. |
| WR-03 | warning | fixed | 825b3a2 | Missing pin keys, bad recipes and tool failures print `result=error reason=...` with tool stderr and exit 2; only real differences print `result=differs`. `cgb_colour_repro_tool_failure`, `cgb_colour_repro_missing_pin` (stub tools, non-Windows). |
| IN-01 | info | fixed | 268b611 | CGB-only note now follows the `replace_session_rom` precedence. Player package verification passes; the SDL-bound path has no unit seam. |
| IN-02 | info | fixed | bf9396f | Unreadable profile ends as `frame-invalid`; static assert on the RGB555 scratch size. `acceptance_*` and the DMG baseline pass. |
| IN-03 | info | fixed | cae35e7 | Misaligned base, NULL `path` and NULL `out` refused; `acceptance_digest_rgb555_vectors` fails when the guards are removed. |
| IN-04 | info | fixed | 3206b48 | Regexes tightened to the specific failure reason and matched against real mutant output; fuzz `require_contract` reports expression and line. |
| IN-05 | info | fixed | 2acb742 | `--profile bogus` still exits 2 with `usage: measure_core`. |

After the fixes: `ctest --preset phase1` 689/689, DMG baseline pass, player package verification pass.
