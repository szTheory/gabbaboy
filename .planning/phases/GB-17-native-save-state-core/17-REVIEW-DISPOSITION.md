---
phase: 17
review: 17-REVIEW.md
titles: json
findings:
  - id: CR-01
    review_id: CR-A01
    severity: critical
    disposition: fixed
    title: "Valid mid-frame state is un-saveable because `ppu_objects_stalled` keeps stale bits"
  - id: CR-02
    review_id: CR-A02
    severity: critical
    disposition: fixed
    title: "Any CGB game that writes a palette high byte with bit 7 set makes the machine un-saveable"
  - id: CR-03
    review_id: CR-A03
    severity: critical
    disposition: fixed
    title: "Accepted state with `dma_active=1, dma_index>=160` causes an out-of-bounds write in the OAM DMA tick"
  - id: WR-01
    review_id: WR-A01
    severity: warning
    disposition: fixed
    title: "`ly` is unvalidated, although `docs/state-format.md:362` says it is 0..153"
  - id: WR-02
    review_id: WR-A02
    severity: warning
    disposition: fixed
    title: "Active HDMA with `destination_cursor == 0` is accepted, contradicting 'active destination spans stay within VRAM'"
  - id: WR-03
    review_id: WR-A03
    severity: warning
    disposition: fixed
    title: "The 'refused load leaves the target unchanged' helper cannot see heap state, so cartridge RAM mutation is untested"
  - id: WR-04
    review_id: WR-A04
    severity: warning
    disposition: fixed
    title: "Nothing checks that reachable machine states are saveable, and the state fuzzer is scenario-based rather than byte-level"
  - id: WR-05
    review_id: WR-A05
    severity: warning
    disposition: deferred
    title: "`state_apply` re-implements the decoder instead of calling the validated store path"
  - id: IN-01
    review_id: IN-A01
    severity: info
    disposition: deferred
    title: "Test-only helpers compile into the production core and trip `-Wall -Wextra`"
  - id: IN-02
    review_id: IN-A02
    severity: info
    disposition: deferred
    title: "Save/size error for an invalid *live* state is undocumented"
  - id: IN-03
    review_id: IN-A03
    severity: info
    disposition: deferred
    title: "The parity-sweep negative control was narrowed, and several flag fields have no canonical-value rule"
  - id: CR-04
    review_id: CR-B01
    severity: critical
    disposition: fixed
    title: "All three `state_purity_mutant_*` controls build the same CRC-omission mutant, not the allocation, hash or tail-write mutants they name"
  - id: WR-06
    review_id: WR-B01
    severity: warning
    disposition: fixed
    title: "`state_boundary_controls` spawns about 1,050 git processes, which is above the GB-CI-012 limit on Windows"
  - id: WR-07
    review_id: WR-B02
    severity: warning
    disposition: fixed
    title: "Seven horizon mutants pass the 'intended discrepancy was reported' check without that check being able to fail"
  - id: WR-08
    review_id: WR-B03
    severity: warning
    disposition: fixed
    title: "The new `perf_advisory_*` CTests have no parsed minimum, and a Windows run reports 'pass controls=1' for a fully skipped test"
  - id: IN-04
    review_id: IN-B01
    severity: info
    disposition: deferred
    title: "The installed-tracer step never re-checks the library or proof-executable hashes it records"
  - id: IN-05
    review_id: IN-B02
    severity: info
    disposition: deferred
    title: "`state_fuzz_controls` does not compare the public header against the revision, though the probes build from it"
  - id: IN-06
    review_id: IN-B03
    severity: info
    disposition: deferred
    title: "The `v02_fuzz_controls` self-test prints hand-maintained constants as its control counts"
  - id: CR-05
    review_id: CR-C01
    severity: critical
    disposition: fixed
    title: "The OWNER approval of an Ir exception can be forged from committed files, and the 'fails closed on hosted runs' claim is not enforced"
  - id: WR-09
    review_id: WR-C01
    severity: warning
    disposition: fixed
    title: "The release-please entrypoint and the non-release workflows are barely constrained by the policy checker"
  - id: WR-10
    review_id: WR-C02
    severity: warning
    disposition: fixed
    title: "The policy judges the lifecycle script by region and the pin base by substring, so a one-line edit disables either gate"
  - id: WR-11
    review_id: WR-C03
    severity: warning
    disposition: deferred
    title: "The shipped tree fails the rehearsal judge's `--release-head`, so no release can pass the nightly gate until a follow-up commit lands"
  - id: WR-12
    review_id: WR-C04
    severity: warning
    disposition: deferred
    title: "Phase 16 WR-04 is only half closed; the budget checker and allowlist still come from the PR head"
  - id: WR-13
    review_id: WR-C05
    severity: warning
    disposition: fixed
    title: "The state-pin base step fails on every force-push and rebase, unlike the budget base step"
  - id: IN-07
    review_id: IN-C01
    severity: info
    disposition: deferred
    title: "The retry tamper check cannot detect a post-attachment swap and is described as if it could"
  - id: IN-08
    review_id: IN-C02
    severity: info
    disposition: deferred
    title: "`libbet-repro.yml` and `fixture-repro.yml` are outside the 'persist-credentials: false' rule set for some jobs"
open: 0
total: 26
recorded: 2026-10-28T22:07:16.000Z
---

# Phase 17: Code Review Disposition

Review-fix round 1 of 2. All 5 critical findings and 10 of 13 warnings are fixed; each fix has a negative control that fails on the defect. The ledger IDs are sequential for the disposition parser; the Source column names the slice ID used in 17-REVIEW.md, commit messages and policy mutant names. Outside the review, the same round fixed the Windows `workflow_policy_controls` floor (`e9e2d57`, 394 POSIX / 375 WIN32) and the Windows `sanitizer_timeout_policy_selftest` cost (`2756e41`). No deferred item is an open correctness or security defect: WR-C03 is a release precondition, WR-C04 is the carried Phase 16 residual on T-17-25, and the rest are hardening or wording.

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | CR-A01; round 1 fix 1eb3082 with a negative control |
| CR-02 | critical | fixed | CR-A02; round 1 fix e73b998 with a negative control |
| CR-03 | critical | fixed | CR-A03; round 1 fix cbe4c4b, 46bb6f9 with a negative control |
| WR-01 | warning | fixed | WR-A01; round 1 fix fbdaa1c, 7df3a46 with a negative control |
| WR-02 | warning | fixed | WR-A02; round 1 fix 92463dd, 535aa68 with a negative control |
| WR-03 | warning | fixed | WR-A03; round 1 fix b2acaa7 with a negative control |
| WR-04 | warning | fixed | WR-A04; round 1 fix a05f4ba, ca698d8 with a negative control |
| WR-05 | warning | deferred | WR-A05; refactor `state_apply` onto `state_store_host_value`; now guarded by the refusal and reachable-saveable properties. Follow-up, owner to schedule |
| IN-01 | info | deferred | IN-A01; guard test-only helpers behind the test seam flag together with WR-A05 |
| IN-02 | info | deferred | IN-A02; document that size/save return `GBB_STATE_INVALID_CONTENT` for a live machine that breaks an invariant; after CR-A01/A02 not expected for emulator-produced states |
| IN-03 | info | deferred | IN-A03; restore a sweep-level parity control and tighten two flag fields, each first checked against the reachable-saveable property |
| CR-04 | critical | fixed | CR-B01; round 1 fix 08bd666 with a negative control |
| WR-06 | warning | fixed | WR-B01; round 1 fix 165438a with a negative control |
| WR-07 | warning | fixed | WR-B02; round 1 fix 2708d50 with a negative control |
| WR-08 | warning | fixed | WR-B03; round 1 fix c281431 with a negative control |
| IN-04 | info | deferred | IN-B01; re-check library/proof-executable hashes in `run_tracer`; small follow-up |
| IN-05 | info | deferred | IN-B02; add the public header to the `verify-v02-fuzz.py` source list; small follow-up |
| IN-06 | info | deferred | IN-B03; derive `v02_fuzz_controls` counts from the executed suite with a parsed minimum |
| CR-05 | critical | fixed | CR-C01; round 1 fix c66430f with a negative control |
| WR-09 | warning | fixed | WR-C01; round 1 fix 6228b3f with a negative control |
| WR-10 | warning | fixed | WR-C02; round 1 fix f2ce8e7 with a negative control |
| WR-11 | warning | deferred | WR-C03; release precondition, not a code defect: after merge, dispatch the report-red dry run on main and re-cite the provisional `nightly-asan.yml:report-red` row before any release; recorded with RM-027 entry blockers |
| WR-12 | warning | deferred | WR-C04; carried Phase 16 WR-04 residual: run `verify-test-budget.py` from the base commit; recorded on T-17-25 |
| WR-13 | warning | fixed | WR-C05; round 1 fix f2ce8e7 with a negative control |
| IN-07 | info | deferred | IN-C01; wording: T-17-22 corrected in 17-SECURITY.md to an identity and consistency check; detecting a swap would need first-attempt digests |
| IN-08 | info | deferred | IN-C02; add `persist-credentials: false` to libbet-repro; write escalation is already refused by the WR-C01 rule |
