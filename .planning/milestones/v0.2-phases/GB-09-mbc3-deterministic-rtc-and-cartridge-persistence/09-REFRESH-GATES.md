---
phase: GB-09-mbc3-deterministic-rtc-and-cartridge-persistence
reviewed: 2026-10-20T20:49:33Z
scope: stale-verification refresh gate evaluation
result: passed
---

# Phase 9 verification refresh gate evaluation

This note evaluates whether Phase 9's existing validation, security, UI and review
evidence can be reused for a stale-verification refresh. It does not repeat the
implementation or claim a fresh full code review.

## Requirement and task coverage

All 18 plans declare one or more of CART-04/05/06 and RTC-01/02/03. The plans
contain 44 tasks, each with an automated `<verify>` command. Plan requirement
counts match the existing verification map: CART-04 (6 plans), CART-05 (4),
CART-06 (9), RTC-01 (6), RTC-02 (5), RTC-03 (9). The six IDs are all present in
the phase verification report and marked satisfied.

The existing 14-row automated UAT maps the requirements and their failure
controls as follows:

| Requirement | UAT evidence | Negative or boundary control |
|---|---|---|
| CART-04 | Rows 1–2: MBC3 mapping and MagenTests OOB SRAM | MBC30 rejection; tampered and empty manifests; `$149=$03` fail-shade ROMs; paired screen negative control; renamed-ROM install-scan self-test |
| CART-05 | Rows 3–4: loader contradiction matrix and 8 MiB bound | Rejected combinations preserve the prior ROM; one-under/one-over and `SIZE_MAX` length classes |
| CART-06 | Rows 10–12: v2 envelope, v1 compatibility, fresh-process continuation and fixture reproduction | 17-field save rejection matrix, seven write-fault points, wrong-ROM rejection, byte-identical fixture rebuilds |
| RTC-01 | Rows 5–6: rtc3test, deterministic rate/latch/halt/carry/day behavior, no-host-clock proof | rtc3test non-terminating negative control, five RTC mutants, no-host-clock source/object negative controls |
| RTC-02 | Rows 7, 9 and 14: catch-up API, installed C/C++ consumers and guide contract | Negative elapsed time, non-RTC cartridge, import-does-not-advance; guide phrase and identifier mutants |
| RTC-03 | Rows 8, 11 and 14: RTC block, save reopen and host guide | Corrupt block matrix; rollback, halt, unavailable/missing clock, wrong-ROM and fresh-process controls |

The row-level evidence and commands are in `09-UAT.md`; its summary records
14/14 pass, zero issues, and zero pending rows. `09-VALIDATION.md` records a
passed validation audit and `nyquist_compliant: true`. Those results are prior
receipts, not a fresh run on the current branch.

A verifier identified two backstop claims that were not directly exercised for
MBC3: 09-03's concurrent independent loads and 09-11's independent RTC
instances. The added coverage is folded into the existing
`concurrent_independent_instances` test in `tests/test_instance_concurrency.c`,
so the CTest and published expected-test inventories remain unchanged at 1,144.
Two threads own separate instances and synthetic RTC+battery ROMs; 128 bounded
rounds verify each guest marker and its lane-specific RTC image after distinct
catch-up values and a second three-second increment. After both workers join,
the negative control imports lane 1's actual battery image into lane 0 and
requires the same matcher to report a mismatch and return 1; the enclosing CTest
expects that control result and exits successfully. This directly tests the
isolation oracle without concurrent calls on one instance.

The historical Phase 9 `coverage:` blocks in plans 09-04, 09-11, 09-13 and
09-16 use the legacy `deliverable`/flow-style form; the 09-UAT notes that those
deliverables were mapped manually to the automated rows above. This is an
intentional legacy boundary: `tests/CMakeLists.txt` runs `summary_coverage`
with `--since 11`, and `verify-summary-coverage.py` documents that Phases 9–10
used the rejected schema. The separate Phase 10 negative-control test confirms
the checker rejects the old form. No current Phase 9 coverage CTest is being
silently treated as green, and historical summaries were not rewritten.

## Security gate

All 18 plan files contain a plan-time `<threat_model>`. `09-SECURITY.md`
consolidates that register, reports 45 threats closed and zero open at ASVS
level 1, and records the one accepted low-severity performance risk. With the
register authored at plan time, zero blocking threats and L1 configured,
`secure-phase.md` explicitly permits reuse without dispatching another
auditor.

Spot checks of the current shared core support the reused mitigations:

- `src/core/gabbaboy.c:281-293` advances RTC state from supplied emulated
  half-dots; it has no ambient clock source. The existing two-layer
  `no_host_clock` test checks source and linked symbols and has negative
  controls (`09-UAT.md`, row 6).
- `src/core/gabbaboy.c:3525-3562` applies the MBC3 RAM allow-list and rejects
  MBC30 markers after size/checksum validation.
- `src/core/gabbaboy.c:3841-3888` checks exact battery-image size, parses the
  RTC block into a local copy before mutation, and commits the parsed fields
  only after validation.
- `src/core/gabbaboy.c:3901-3914` rejects negative catch-up before conversion,
  handles non-RTC and halted cartridges, and saturates the generation counter.

The original security audit is dated 2026-10-12. Current full-core regression
passed 1,144/1,144 after the gate audit; this note does not substitute the
historical audit for that run.

## UI and status-text applicability

There is no Phase 9 UI-SPEC or UI-REVIEW. The phase does touch one visible text
surface: reopening a battery-backed RTC save may set a catch-up status in the
player window title (`src/player/main.c:1104-1119`, `766-790`). The formatter
uses bounded output and provides explicit messages for missing timestamps,
clock failure/rollback, halted clocks and elapsed time (`src/player/catch_up_policy.c:30-63`).
`player_session_apply_catch_up` gates the action to an accepted RTC save and
records the once-per-open state (`src/player/session.c:744-784`).

This is a deterministic text/status contract, not a new visual layout. Existing
policy and continuation tests assert exact status values for advance, rollback,
halt, no-clock and missing-timestamp cases (`tests/player/test_continuation.c`,
including the `player_continuation_mbc3_rtc_*` cases; UAT row 11). The current
focused player gate reported 28/28 passed. No human perceptual checkpoint or
separate UI-REVIEW artifact is needed for this refresh.

## Code-review gate and reuse limits

`09-REVIEW-DISPOSITION.md` is the current disposition authority: 13 total
findings, zero open. It records 11 fixed and two skipped findings. The latest
`09-REVIEW.md` is explicitly a scoped re-review of the host-guide contract
checker; it is not a clean full-phase review. Reuse the dispositions without
claiming that a new full-source review occurred.

The installed OpenGSD evaluation-scope resolver (`GSD_RUNTIME=codex`, runtime
identity `@opengsd/gsd-core` 1.18.0) returns `status: degraded`,
`source: phase-range`, reason `no-reachable-task-commits`, with six task commit
hashes unreachable on this branch. Therefore it cannot establish a precise
fresh Phase 9 review file scope. This is not a verification failure because
the review disposition is being reused; if a new code review is requested,
its scope must be resolved before making a full-review claim.

## Current regression receipt

The configured command `cmake --preset phase1 && cmake --build --preset phase1 &&
ctest --preset phase1 --output-on-failure --no-tests=error` passed 1,144/1,144
in 375.09 seconds at source `28b3c10`; this is the full-suite baseline before
the new test code. The separate rebuilt SDL player slice passed 28/28 in 1.03
seconds, including continuation, v1 compatibility, classification drift,
host-clock and documentation negative controls. No source core or player code
changed during these checks.

The attempted separate registration of two additional CTests was rejected by
`v02_support_ledger_controls`, which pins the published test inventory. Those
registration and inventory edits were reverted. The final bundled test path
then passed the focused four-test selection: `concurrent_independent_instances`,
`cgb_instance_isolation`, `v02_support_ledger`, and
`v02_support_ledger_controls` (4/4, 16.18 seconds; receipt
`/tmp/gabbaboy-phase9-gap-tests.log`). Thus the inventory stays at 1,144 and
the ledger controls pass on the final test arrangement. The existing
duplicate-library linker warning remains Phase 13 debt; this refresh does not
accept or resolve it.

The historical 411/411 CTest result in the previous `09-VERIFICATION.md` is
retained only as historical evidence.

## Gate conclusion

Reuse the prior Nyquist map, threat register, and review dispositions with the
limits stated above. The deterministic RTC status text has source-to-test
coverage, and the two previously indirect concurrency backstops now have a
direct positive case and an effective contamination negative control. Review
of the added test path found no correctness or thread-lifecycle defect. The
full-core and player receipts above remain baseline evidence; the focused
four-test receipt verifies the final test change and preserved ledger. No fresh
full-phase source review is claimed.
