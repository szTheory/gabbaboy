# Proposed bounded pre-tag repair: immutable Git text decoding

Status: approved by the owner on 2026-10-30, recorded as D-123. The owner selected “Approve bounded repair (Recommended)” for this exact linked recovery proposal. The release window remains stopped until the repair is reviewed, qualified, merged and regenerated; no W, release merge, tag or publication occurred.

## Verified cause

At corrected version head `ca1f120a56a41a4454c983e712b5967842d164d1`, PR CI run 41072242915 failed Windows `state_pin_planning`. `run_git()` in `tests/scripts/verify-state-pins.py` uses implicit locale decoding through `subprocess.run(..., text=True)`. Windows Python selected cp1252 and could not decode UTF-8 byte 0x9d in immutable DECISIONS.md. A subprocess reader failed and reference validation then received no text. This is a verifier defect already on main `cb3055c9b1c4a0bbe0f93e22f978e3418a1ea391`, not version content or an emulator failure.

The prior release-row base and wording defects were corrected within Plan 19-07's authorized content-restart path. The independent review and both exact future event-base checks passed at the corrected head. Those fixes do not solve this separate encoding defect. Old failed/cancelled runs remain non-proof.

## Concrete candidate and local evidence

Ignored `build/phase19-window/encoding-rescope/candidate.patch` changes only `run_git()`: capture Git output as bytes, decode successful stdout strictly as UTF-8, and refuse malformed output with `immutable-source-encoding`. Nonzero Git results and `allow_missing` behavior stay intact; anchors, immutable references and compatibility checks are unchanged.

`python3 -I build/phase19-window/encoding-rescope/reproduce.py` tested immutable main code and actual corrected version/base:

- RED: main checker reproduces the cp1252 failure with the actual UTF-8 decision text.
- GREEN: candidate validates the actual version head against the actual PR base under the same simulated Windows default.
- Exact UTF-8 bytes round-trip; missing anchor and malformed UTF-8 refuse; missing optional file remains absent.
- Existing state-pin self-test passes all 22 controls.

The patch and reproducer are local ignored artifacts, not tracked source changes or hosted qualification. `reproduce.log` retains the output. Physical Windows validation is still required.

## Approved scope amendment

Authorize one additional pre-tag hardening PR for this encoding defect and its regression controls. This is an explicit exception to the single pre-window main push in D-01 and one additional bounded source fix/review round after the two original rounds and consumed D-121 resolver allowance; none of those earlier rounds is reset or erased.

1. Add the strict UTF-8 helper repair and persistent positive/negative regression controls to the existing state-pin CTest. Keep immutable checks, existing rejection behavior, performance limits, timeouts, dependencies and package policy unchanged. No emulator code or unrelated cleanup.
2. Review the complete small diff independently and require exact-head protected CI, including actual Windows exercise of non-ASCII immutable references. Merge only the qualified revision with `--match-head-commit`; no bypass or auto-merge.
3. Preserve the original PR A squash in facts. Record the new hardening squash separately as the new window base; amend Plan 19-07's base/pin assumptions explicitly. Observe release-please regeneration at that new base before resuming. Only after those repair prerequisites pass, snapshot and retire the obsolete pre-tag rehearsal attempt with an exact-head/terminal-run/no-tag guard, then create the fresh R1 ref; never force-update the version branch or reuse the old attempt. No silent reassignment of historical facts.
4. Restart Task 1 with fresh version content, exact-base compatibility row, revision-bound corpus receipt, CI and R1. Then retain the original R1/R2 ordering, W/nightly/pre-tag gate, exact-tree guarded merge, immutable tag/draft, publication/readback and PR B requirements. Earlier failed/cancelled runs cannot qualify the new source.
5. Carry the local planning reconciliation and user communication preferences in the appropriate reviewed hardening or post-release PR, keeping them out of version content H/W. Preserve owner config/state JSON edits.

The reserved 19-08 post-tag gap slot and performance limit are unchanged. Any unrelated correctness/security finding stops again for rescope; this proposal is not an open-ended repair allowance. Stop after Phase 19 execution and hand off to `/gsd-verify-work 19`.

## Current safety state and continuation

Main remains at the original PR A squash. PR #131 and `rehearsal/v0.3.0` point to the corrected version head; no v0.3.0 tag exists. Superseded live jobs are being cancelled with exact run/head checks and preserved outcomes. The rehearsal ref is retained and must not be moved or deleted while the stop is unresolved.

Completed stage: Phase 19 execution through Plan 19-06; Plan 19-07 stopped during Task 1 qualification. Next intended stage remains Phase 19 — Qualified v0.3.0 Release, execution, under the approved bounded recovery. Exact continuation command: `/gsd-execute-phase 19`. D-123 authorizes the repair work; this command does not bypass the remaining qualification guards. Verification remains the later phase handoff, not an action to start now.

The scope decision is required by AGENTS.md: “An unresolved correctness or security finding forces a rescope, never a seed,” and Plan 19-07's explicit stop for a pre-tag failure caused by code on main that needs a second main push. No acknowledgment is required merely to keep the release stopped.
