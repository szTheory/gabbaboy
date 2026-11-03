# Phase 21 bounded rescope: qualification flag ordering and diagnostic escaping

**Status:** Owner-approved; implementation, independent review, final-head qualification, and PR merge complete

**Approval:** User authorized one bounded fix and independent review on 2026-11-02.

**Implementation base:** `f94a8617efdd6cd82f477cd8b26f33e85a020a1f`

## Evidence requiring the rescope

The final delta review found two issues in the CMake compile-database qualification helper:

1. `cmake_build_qualified_value` accepts `-DGBB_BUILD_QUALIFIED=1 -UGBB_BUILD_QUALIFIED` as qualified because it ignores undefine flags. The local C compiler confirms that this option sequence leaves the macro undefined.
2. Candidate source paths are bounded but emitted raw in diagnostics. A path containing a newline or terminal escape can split log output or alter terminal rendering. A local control reproduced both cases at the implementation base.

The findings are recorded in [21-REVIEW.md](21-REVIEW.md). The existing 21-08 plan reserves one gap round and directs a further scope decision if findings remain afterward. This owner-approved correction preserves prior review and gap counts; it does not reset them.

## Approved scope

- Update only `tests/scripts/verify-cgb-candidates.py` and `tests/scripts/test_cgb_candidate_order.py` for these findings.
- Treat `-D`, `/D`, `-U`, and `/U` operations for `GBB_BUILD_QUALIFIED` conservatively and in argv order. Reject qualification if the target macro is undefined, has an unsupported value, or has ambiguous repeated operations.
- Preserve Windows command-string quoting semantics: strip only double-quote wrappers, since single quotes are literal to native Windows command parsing.
- Escape compile-database candidate paths before applying the existing per-path and total diagnostic bounds.
- Add focused negative controls for combined and split define/undefine forms, later unsupported values, literal single-quoted Windows command arguments, and newline/terminal-control paths, with positive controls retained.
- Require independent scoped review, build-bound phase-21 admission controls, the final serial CTest suite, and fresh exact-head required PR and installed-package checks before merge.

## Exclusions and stop conditions

No emulator/product code, candidate source or ROM, rights decision, fixture inventory, workflow trigger, dependency, timeout, performance budget, or later-phase work is in scope. Any unrelated correctness or security finding stops for another scope decision. Do not claim game evidence beyond the existing harness-only CGB result; keep `FIXT-01` pending. Do not start Phase 22.

## Completion evidence

The final reviewed implementation source is `e0845db5841a1d56d8a297cbfaa3e0811af6ad67`. The 18 parser unit tests, configure/build, focused fixture-admission control, independent scoped code/security reviews, and all 1,718 registered local tests have passing evidence across the full serial run plus its one isolated source-archive timeout retest. PR #140 final head `507019f9363bcce375fa8bec3bda0d75fa0583c6` passed all required exact-head CI, fixture-reproduction, installed-consumer and player-package checks. The first hosted macOS CTest run timed out `phase21_fixture_admission_controls` at 60.08 seconds; the same-head full-suite rerun passed all 1,724 tests, including that test in 50.18 seconds. PR #140 was squash-merged to main at `bef2cfbdbdd0fc9b2d78631586827e29e0241b3b`; its merge tree matches the checked PR head. Run links and the full-suite accounting are in [21-UAT-EVIDENCE.md](21-UAT-EVIDENCE.md). Phase 21 closeout is complete; Phase 22 remains unstarted.

### Related review refinement

The independent review also identified that Windows-mode `shlex` groups single quotes even though native Windows command parsing treats them as literal characters. This is within the same qualification-parser scope: the helper now strips only double-quote wrappers on Windows and has a deterministic simulated-Windows negative/positive control. This refinement does not add a new phase or reset prior review/gap counts.
