---
phase: 10
review: 10-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "run_profile() falls back to DMG for an unknown model"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Suite categories count expected-unsupported rows as passes"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "reproduce-mooneye-cgb.sh --compare skips original_sha256 without a manifest; temp dirs leak on abort"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Runner hand-declares gbb_test_last_unsupported_address"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "Stale comments in acceptance.h, GATE-23/GATE-38 and reproduce-mooneye-cgb.sh"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Redundant test -s in the CGB banking CI step"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "A/B mode raw KeyError on missing elapsed_ns; test hooks read in production"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "CGB suite headline says status=pass with two expected-unsupported rows"
  - id: IN-05
    severity: info
    disposition: no_change_needed
    title: "Upstream maintainer e-mail in fixtures/mooneye-cgb/LICENSE.txt"
open: 0
total: 9
---
# Phase 10: Code Review Disposition

Source: `10-REVIEW.md` (standard depth, 49 files; 0 critical, 4 warning, 5 info). Fixes applied by gsd-code-fixer, one commit per finding; full suite 541/541, `baseline status=pass`, `verify-model-gates.py` pass after the last fix.

| ID | Severity | Disposition | Commit | Evidence |
|----|----------|-------------|--------|----------|
| WR-01 | warning | fixed | 927ff60 | `acceptance_unknown_model_refused` (exit 3, `reason=unknown-model`); fails against the old `acceptance.c` |
| WR-02 | warning | fixed | 0917e59 | `cgb_mooneye_required_suite` regex now requires `post-boot-hwio=0/1 post-boot-hwio.expected-unsupported=1`; fails on old output |
| WR-03 | warning | fixed | 47af1ee | `cgb_mooneye_repro_requires_manifest` (offline guard test); `EXIT` trap removes the build dir |
| WR-04 | warning | fixed | 3c07f7f, a35473f | Internal `src/core/gabbaboy_test.h` shared by core and runner (not installed; install tree ships only `gabbaboy/gabbaboy.h`); last-refused-address semantics kept and documented, because `cgb_visibility_deferred_latch_interrupt` pins it; no-host-clock allowlist updated |
| IN-01 | info | fixed | b633688 | Comments and `docs/model-gates.md` GATE-23/GATE-38 text updated together; scanner passes |
| IN-02 | info | fixed | 1d094d5 | Workflow YAML still parses |
| IN-03 | info | fixed | e9faf3c | `cgb_bench_ab_missing_elapsed`; overrides honoured only with `GBB_AB_TEST_HOOKS=1` |
| IN-04 | info | fixed | bbd55c4 | Headline `status=pass-with-expected-unsupported`, asserted by `cgb_mooneye_required_suite`; MBC suites unchanged |
| IN-05 | info | no_change_needed | — | MIT licence requires the upstream copyright line verbatim |

These commits follow PR #66 head `0902058`; exact-head hosted CI on the pushed head is still required before merge.
