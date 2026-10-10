---
phase: 03
review: 03-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Release workflow passes in-repo output directories that the helper rejects"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Failed withdrawal is swallowed silently"
  - id: WR-01-followon
    severity: warning
    disposition: fixed
    title: "Withdrawal reporting could mask the original publication error"
  - id: WR-02
    severity: warning
    disposition: skipped
    title: "prepare clears the previous verified set before republishing"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "Misleading close() failure message and missing O_NOCTTY in read_rom_file"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Duplicated receipt-field test fixture"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "Withdrawal-report test covers only the outer call site"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "Shallow workflow output-directory guard"
open: 0
total: 8
recorded: 2026-10-10T16:03:16Z
---

# Phase 03: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | `91d11d4`: release smoke uses `$RUNNER_TEMP`, unused job-level in-repo value removed, workflow guard test added |
| WR-01 | warning | fixed | `91d11d4`: withdrawal failures reported on stderr; original error still propagates; regression added |
| WR-01 (follow-on) | warning | fixed | `8151a75`: reporting failures ignored so they cannot replace the publication error; closed-stderr regression (mutant fails) |
| WR-02 | warning | skipped | Intentional: a stale verified archive/receipt pair must not survive a failed verification run and be mistaken for current evidence; reviewer agreed |
| IN-01 | info | fixed | Fixed by Phase 06.1 PR #54, squash merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb` (exact tested head `2a8fd1c`), commit `7b57ed6`. `read_rom_file` opens with `O_NOCTTY` (`read_save_file` intentionally unchanged) and reports a size overrun and a `close()` failure in separate branches (`src/player/session.c:104-107,143-153`). The size-bound message is guarded by the 2097153-byte assertion in `player_session_replacement_failure` (`tests/player/test_session.c:131-136`; mutation-checked in 06.1-02). The `close()` failure branch is verified by inspection only: no fault-injection stage exists for ROM close, so it is not test-covered. Hosted proof: PR-head ci run 38064419789, job `macos-player-package` success. Rechecked clean in the 2026-10-10 post-06.1 re-review. |
| IN-02 | info | fixed | Fixed by Phase 06.1 PR #54, squash merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb` (exact tested head `2a8fd1c`), commit `d7b651d`. One `_receipt_fields()` helper (`tests/scripts/test_verified_player_output_dir.py:27-42`) replaces the inline copies; mutation-checked in 06.1-02; 21 tests OK on the refresh branch. Hosted proof: ci run 38064419789 `macos-player-package` success. |
| IN-03 | info | fixed | Fixed by Phase 06.1 PR #54, squash merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb` (exact tested head `2a8fd1c`), commit `a95c037`. `test_failed_withdrawal_after_link_is_reported_without_masking_sync_error` (`tests/scripts/test_verified_player_output_dir.py:284-312`) reaches the inner withdrawal site after a directory-sync failure (`tests/scripts/verified_player_output_dir.py:180-182`); mutation-checked in 06.1-02. Hosted proof: ci run 38064419789 `macos-player-package` success. |
| IN-04 | info | fixed | `8151a75`: guard scans `.yml`/`.yaml`, requires a runner-temp child path, rejects `..` |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.

The earlier review's CR-01 (unvalidated recursive deletion) was fixed and remains in git history. The 2026-10-10 post-06.1 re-review (`03-REVIEW.md`) is clean: 0 critical, 0 warning, 0 info. IN-01, IN-02 and IN-03 were fixed by Phase 06.1 PR #54.
