---
phase: GB-17-native-save-state-core
plan: "08"
subsystem: testing
tags: [release-evidence, support-ledger, release-please, workflow-policy, CTest]

requires:
  - phase: GB-17-native-save-state-core/17-07
    provides: "Advisory timing semantics and workflow policy controls that the disclosure interpretation and window gate extend"
provides:
  - "The historical DMG performance disclosure is rendered by the support-ledger generator from validated, tag-bound input"
  - "Tagged v0.2.0 and v0.2.1 ledgers are proved to be exact generator output, and v0.2.1 is proved unchanged from its tag blob"
  - "An immutable-revision version-window checker with an inactive tracked record and a fatal post-regeneration gate in the release-please workflow"
affects: [GB-17, release-evidence, release-please, workflow-policy]

actuals:
  tokens: 24535
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Generated documents are accepted only as fixed points of their generator, so a hand edit is rejected by byte comparison"
    - "A freeze is a content and event rule: bindings are Git-object digests at a resolved 40-hex revision, never a clock or the working tree"

key-files:
  created:
    - tests/data/release-disclosure.json
    - tests/scripts/verify-version-window.py
    - tests/data/version-window.json
  modified:
    - tests/scripts/verify-support-ledger.py
    - docs/release.md
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - .gitattributes
    - .github/workflows/release-please.yml
    - .github/scripts/verify-workflow-policy.py

key-decisions:
  - "Historical facts live in one input whose candidate and baseline sources must be the v0.2.0 and v0.1.0 tag commits and whose fixture digest must be the candidate-source blob digest; a rewritten historical value is well-formed input and is caught by tag-byte comparison and the adoption verifier."
  - "The current advisory interpretation is rendered only for ledgers after v0.2.1, so tagged bytes never change."
  - "A window ends on any change to main, source, release notes, generator inputs or the regenerated PR body between the reviewed head and the revision; only the record file itself may differ."
  - "The window gate runs after release-please regeneration and fails loudly while an active freeze is broken; with no version PR or an inactive record it passes and the existing policy is unchanged."

patterns-established:
  - "Checkers whose fixtures need Git cache immutable-object reads by commit id to keep process counts low on slow hosts."
  - "Workflow-policy mutations address a non-workflow file through a named baseline key (config)."

requirements-completed: []

coverage:
  - id: RM-028-generator
    description: "The historical performance disclosure in a generated support ledger is rendered by the actual ledger renderer from source-bound validated input; the tagged ledgers are exact generator output with v0.2.1 equal to its tag blob; and input omission, an altered historical value, unbound sources, a handwritten-success bypass and a tagged-target rewrite are each rejected with their own diagnostic."
    requirement: RM-028
    verification:
      - kind: integration
        ref: "ada8050e430393526d11a74697b667850bec8fa1: ctest --test-dir build -R '^release_disclosure_(generator|controls)$' --output-on-failure --no-tests=error (2/2 passed; generator ledgers=2 tagged=1, controls positives=4 controls=19)"
        status: pass
      - kind: integration
        ref: "ada8050e430393526d11a74697b667850bec8fa1: python3 -I tests/scripts/verify-support-ledger.py --self-test (exit 0; includes the synthetic-receipt writer round trip, the generated block and the tagged-target refusal)"
        status: pass
    human_judgment: false
  - id: RM-028-window
    description: "An active version-window record is judged from Git objects at a resolved revision; body overwrite, a stale head, a changed source, release-note or generator-input path, a digest not recomputed after regeneration, a moved main and review or rehearsal identity mismatches are rejected, a regenerated and revalidated exact head passes, and the inactive record cannot claim a freeze or readiness."
    requirement: RM-028
    verification:
      - kind: integration
        ref: "ada8050e430393526d11a74697b667850bec8fa1: ctest --test-dir build -R '^release_window_(contract|controls)$' --output-on-failure --no-tests=error (2/2 passed; controls positives=8 controls=27)"
        status: pass
      - kind: integration
        ref: "ada8050e430393526d11a74697b667850bec8fa1: python3 -I tests/scripts/verify-version-window.py --self-test (exit 0; includes the CLI over the frozen head with an intact and an overwritten body)"
        status: pass
    human_judgment: false
  - id: RM-028-production-route
    description: "The release-please workflow judges the regenerated version PR through a fatal post-regeneration gate, and the workflow policy rejects a missing or reordered gate, a skipped or masked judge, write authority, a PR-supplied checker, shallow history, a path-filtered trigger and any release-please path exclusion beyond the existing workflow and script paths."
    requirement: RM-028
    verification:
      - kind: integration
        ref: "ada8050e430393526d11a74697b667850bec8fa1: python3 -I .github/scripts/verify-workflow-policy.py --check (residual_write_jobs=5)"
        status: pass
      - kind: integration
        ref: "ada8050e430393526d11a74697b667850bec8fa1: python3 -I .github/scripts/verify-workflow-policy.py --self-test (286 negative controls including 20 new window controls, 4 positive controls)"
        status: pass
    human_judgment: false
  - id: phase17-08-no-regression
    description: "The new generator, window and policy changes leave every existing test green, including the support-ledger, adoption, freeze, test-budget and summary-coverage checks."
    verification:
      - kind: integration
        ref: "ada8050e430393526d11a74697b667850bec8fa1: ctest --test-dir build -j14 --output-on-failure --no-tests=error after cmake --preset phase1 (1486/1486 passed)"
        status: pass
    human_judgment: false

duration: 22min
completed: 2026-10-28
status: complete
plan_head_before: 2b79ac6eadba5d0808fdf2e5bf8f3989a7e06a12
plan_head_after: ada8050e430393526d11a74697b667850bec8fa1
---

# Phase GB-17 Plan 08: Generated Disclosure and Version-Window Protection Summary

**The historical DMG performance disclosure is now generator output bound to the v0.2.0 and v0.1.0 tags, and a version PR's reviewed content window is enforced from Git objects with a fatal gate after release-please regeneration.**

## Performance

- **Duration:** 22 minutes from the first to the last task commit (12:17 to 12:38 EDT); context reads and design predated the first commit.
- **Tasks:** 3/3.
- **Commit ledger:** 4 commits measured from the persisted plan base to the task head (one RED, three feature commits).
- **Diff-size proxy:** 24,535 (98,140 changed characters divided by four, the summary actuals scale; not measured model-token use and not comparable to the raw plan projection of 43,000).
- **Local timings:** `release_disclosure_controls` about 2.5 s, `release_window_controls` about 4.6 s, ledger `--self-test` about 33 s wall (the existing `v02_support_ledger_controls` budget is 120 s). `test_budget` passes; no allowlist row was added.

## Accomplishments

- `render_v2_ledger` renders the performance disclosure from `tests/data/release-disclosure.json`. Rendering the structured data of the tracked v0.2.0 and v0.2.1 ledgers reproduces both files byte for byte, so the previously hand-inserted block is now generator output, and v0.2.1 still equals its tag blob. The input is strict (every field classified, value domains bounded) and bound to Git: candidate and baseline sources must be the v0.2.0 and v0.1.0 tag commits and the fixture digest must be the candidate-source blob digest.
- `--write-current` gained a disposable `--output`, writes bytes (no Windows newline translation) and refuses to rewrite the tracked ledger of a version that already has its tag. A current advisory interpretation is rendered only for ledgers after v0.2.1.
- `verify-version-window.py` reads the record, the frozen head, main base, managed generator inputs, regenerated files and PR body from objects at a resolved 40-hex revision. Only the record may differ between the reviewed head and the revision. `--digest` recomputes every digest to reopen a window; the tracked record is an inactive example with every window field null.
- The release-please workflow gains a `version-window` job after regeneration. The workflow policy has 20 new mutants for it and for `release-please-config.json`.

## Task Commits

1. **Task 1 RED: fail-first generator fixed-point check** — `ee8c661` (`test`). It failed with `REJECT ledger-not-generated` at line 56 of v0.2.0.md, because the disclosure existed only as hand-inserted prose.
2. **Task 1 GREEN: generate the disclosure from validated inputs** — `2d43165` (`feat`).
3. **Task 2: exact content identity and freeze invalidation** — `037b2a7` (`feat`).
4. **Task 3: window gate in the production regeneration route** — `ada8050` (`feat`).

## Files Modified

- `tests/scripts/verify-support-ledger.py`, `tests/data/release-disclosure.json` — validated, tag-bound input; renderer; `--check-disclosure`, `--self-test-disclosure`, `--output`, tagged-target refusal.
- `tests/scripts/verify-version-window.py`, `tests/data/version-window.json` — the window checker (`--rev/--base/--check/--body/--digest/--check-tracked/--self-test`) and the inactive record.
- `.github/workflows/release-please.yml`, `.github/scripts/verify-workflow-policy.py` — the gate job and its policy rules and mutants.
- `tests/CMakeLists.txt`, `tests/expected-tests.txt` — `release_disclosure_generator`, `release_disclosure_controls`, `release_window_contract`, `release_window_controls`.
- `docs/release.md` — generator invocation, managed inputs, window lifecycle and the future operator sequence.
- `.gitattributes` — LF rules for the two digest-bound JSON files.

## Verification

- `python3 -I tests/scripts/verify-support-ledger.py --self-test` passed; `--check-disclosure` printed `ledgers=2 tagged=1`.
- `ctest -R '^release_disclosure_(generator|controls)$'` and `-R '^release_window_(contract|controls)$'` each passed 2/2 after `cmake --preset phase1`.
- `verify-workflow-policy.py --check` passed (`residual_write_jobs=5`); `--self-test` passed with 286 negative and 4 positive controls; `verify-version-window.py --self-test` passed (8 positives, 27 controls).
- Discriminating power: a 14-mutant kill matrix over the window checker (body compare, body requirement, head diff, base moved, base ancestry, input and generated digests, version, review and rehearsal identity, inactive-claims, ref acceptance, working-tree fallback, unclassified fields) killed all 14. Removing the tagged-target guard from the writer made the ledger `--self-test` fail with `write-current accepted a tagged tracked target`.
- Full suite at `ada8050e430393526d11a74697b667850bec8fa1`: 1486/1486 passed. A first full run reported `cgb_corpus_report_tracer` and `state_fuzz_controls` failing with a stale build revision stamp (the build had been stamped before the new commits); both passed after `cmake --preset phase1` and a rebuild, as did the full rerun.
- `git diff --check` clean; `verify-v02-adoption.py --check docs` passes with the new documentation.

## Decisions Made

- The disclosure input binds sources to tags rather than carrying free text; a changed historical metric is caught by tag-blob comparison and the adoption verifier, not by trusting the input.
- The window record cannot hash itself, so the rule is "the record file is the only path allowed to differ between the reviewed head and the revision".
- The gate reports a broken freeze as a failed job after regeneration. It judges only; it never opens, regenerates or merges a version PR.
- PR body comparison normalizes line endings and trailing newlines because `gh`, the API and the web editor differ in both.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Digest-bound JSON had no eol rule**
- **Found during:** Task 1.
- **Issue:** `release-disclosure.json` and `version-window.json` are hashed from Git blobs and read in checkouts, but nothing pinned their line endings on Windows (lesson GB-CI-011).
- **Fix:** LF rules added to `.gitattributes`, which the plan's file list omits.
- **Commit:** `2d43165`.

**2. [Rule 1 - Bug] PR body digest depended on line-ending and trailing-newline conventions**
- **Found during:** Task 3, while defining the body bytes the gate fetches with `gh`.
- **Fix:** the checker canonicalizes the body before hashing, with a positive control for CRLF and trailing newlines and a negative control for a one-word change. This edits the Task 2 file inside the Task 3 commit.
- **Commit:** `ada8050`.

**3. [Rule 3 - Blocking issue] A new job cannot have a timeout-ledger row**
- **Found during:** Task 3.
- **Issue:** `.github/ci-timeouts.json` requires a cited completed run for any job with `timeout-minutes`; the new job has none, and a provisional row would have borrowed another job's measurements.
- **Fix:** no job-level timeout and no ledger row; every step carries `timeout-minutes: 5` and the workflow policy requires step bounds (mutant W17-09). The first main run of the job should add a cited row.
- **Commit:** `ada8050`.

**4. [Process] Task 2 has no separate RED commit**
- The window checker and its controls were written together, so there is no failing-first commit for it. Its discriminating power is instead shown by the 14-mutant kill matrix above. Task 1 has a real RED commit.

**5. [Scope] `release-please-config.json` is unchanged**
- The existing configuration already satisfies the new rules (exclusions limited to workflow and script paths). Protection is a policy rule with four mutants, so the file needed no edit.

### Auth gates

None.

## Known Stubs

None. The window gate has not run in a live workflow: its first real run is the first main push after merge, where `gh`, checkout and the version-PR lookup are exercised for the first time (with no version PR it passes trivially).

## Deferred Verification and Limits

- A real-receipt run of `--write-current` was not possible: the only local corpus receipt is from a producer revision that is not an ancestor of this branch. The writer tail was driven with a synthetic full-membership receipt in the ledger self-test, and the receipt-validation front half is covered by its existing controls. A real-receipt generation belongs to the future version PR.
- Hosted Windows, Linux and macOS runs of the new checkers (Git fixtures, adoption subprocess) are pending the parent's exact-head CI; no hosted result is claimed here.
- The window checker proves content bindings only. The recorded review and rehearsal run identities name hosted evidence that the required checks on the exact head authenticate; the checker cannot.
- RM-027 (six release-bound timeout citations) is unchanged and remains a Phase 19 entry blocker before VERSION exceeds 0.2.1. RM-028 lifecycle replay, attach, manifest and retry (Plan 17-09) is not delivered here; STATE-05 is untouched by this plan and no claim is made for it.
- No version PR was opened or regenerated, no tag or release was changed, and nothing was pushed.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: ci-data-checkout | .github/workflows/release-please.yml | The gate checks out the regenerated version-PR head as data under `pull-requests: read` and `contents: read`. Mitigated by taking the checker from the trusted main commit, never executing the PR tree, persist-credentials false, and policy mutants W17-05 to W17-15. |

## Self-Check: PASSED

All four commits (`ee8c661`, `2d43165`, `037b2a7`, `ada8050`) are ancestors of the recorded task head, `plan_head_after` equals that head, and `plan_head_before` is the persisted ledger base. The created files `tests/data/release-disclosure.json`, `tests/scripts/verify-version-window.py` and `tests/data/version-window.json` exist. The `summary_coverage` check is run against this file before it is committed.

---
*Phase: GB-17-native-save-state-core*
*Plan: 08*
*Completed: 2026-10-28*
