---
phase: "19"
review: 19-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Boolean schema versions are accepted as integer version 1"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "A non-object workflow-policy registry escapes as an uncaught exception"
open: 0
total: 2
recorded: 2026-10-31T14:32:50Z
---

# Phase 19: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | D134 exact approved source d2c0dc95 independently rechecked: exact-integer guards and meaningful malformed-input refusals close the original reproduction while valid integer positives remain. Already strict embedded-perf site remains unchanged/excluded. |
| WR-02 | warning | fixed | D134 recheck confirms non-object roots reject before field access and production CLI emits normal REJECT/exit1. Valid-object positive controls remain. |

The original independent standard-depth review covered the wider72-file fallback and retained all earlier review evidence. Owner-approved D134 applied the exact seven-path correction and strengthened existing test guards. The fresh independent recheck closes both findings at d2c0dc95; fresh security recheck closes all41 threats. Eight affected existing CTests pass without skips.

During adjacent-consumer tracing, WR-03 suggested that the unchanged legacy performance parser should reject integral numeric3.0. The reviewer withdrew it after contract adjudication: no existing protocol requires a lexical integer token there, JSON regards3/3.0 as the same integral numeric value, and actual production probes reject boolean/fractional/string versions and an incorrect workload digest. This is an unsubstantiated hardening suggestion, not an accepted or deferred correctness risk. The adjudication and original observation remain in19-REVIEW.md and build/prb-performance-schema-adjudication.json. No implementation change was made outside the approved seven paths.

No open review finding remains. Full final local/player/consumer qualification, phase-goal verification and exact-head protected hosted PR B/merge remain downstream gates. No further live release action or owner approval is needed.


## D-135 portability recheck

The owner approved the exact two-file repair for the actual Windows CI failures. At e46023c5 the fresh independent recheck is clean: the CTest supplies a repository-relative Git path to the unchanged immutable reader; the exact helper LF rule preserves byte identity without matching the APU unpinned negative. No new finding or change outside the approved implementation diff was found. Existing WR-01/WR-02 fixes and WR-03 withdrawal remain unchanged. Current-head affected/EOL/installed checks pass; fresh actual Windows and all protected checks remain required before the same PR137 squash. No source guard or assertion is waived, no further approval is pending.


## D-136 readiness-marker recheck

The owner approved the pinned one-file repair. At e292db8c the fresh independent code recheck is clean: completed private JSON is atomically published, both original readers and interruption/cleanup/retry assertions remain intact, and the new deterministic regression runs in both existing static partitions. No new correctness/security/quality issue was found. The25 selected CTests pass without skips after revision-bound rebuild/install. Existing WR-01/02 closure, WR-03 withdrawal and D135 evidence remain historical and unchanged. Fresh native Linux sanitizer/Windows/all protected CI and the original guarded PR137 boundary are still pending; no owner approval is pending for this scope.
