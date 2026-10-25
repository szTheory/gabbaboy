---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: "09"
subsystem: release
tags:
  - release-workflow
  - exact-tag-evidence
  - ctest-inventory
  - github-actions
requires:
  - phase: "Phase 15 Plan 08"
    provides:
      - "verify-release-gates.sh draft/final gate and verify-v02-delivery.py that require the new evidence assets"
  - phase: "Phase 15 Plan 04"
    provides:
      - "verify-v02-adoption.py --check docs/game, --self-test and --release-notes"
  - phase: "Phase 15 Plan 03"
    provides:
      - "verify-v02-consumers.py --prefix/--self-test"
provides:
  - "release.yml produces and attaches the corpus receipt, schema-2 sidecar, Clang 18 libFuzzer receipt, paired performance receipt, downloaded consumer receipt and source-archive receipt at their real producers on the exact tag, before the aggregate manifest and publication"
  - "Eleven v02_* CTest contracts registered exactly once in tests/CMakeLists.txt and tests/expected-tests.txt"
  - "Gate self-test pins every producer invocation and transfer, producer ordering ahead of publication, retained platform smoke and the exact-once inventory (33 controls)"
  - "verify-support-ledger.py --check-ledger (receipt-free) and --evidence-only (downloaded sidecar verification without the producer build)"
affects:
  - "Plan 15-10 performs the first hosted exact-tag execution of this workflow; none of the new workflow jobs has run hosted"
actuals:
  tokens: 11800
  tasks: 2
  commits: 4
commits: 4
plan_head_before: 208e278dd1d0c9f7178b495b6c294fac7ed57139
plan_head_after: 9d508574989d2c8ca2c06a3641c83c90b19bd973
tech-stack:
  added: []
  patterns:
    - "Evidence is transported through the unpublished draft: generated once at the producer, never overwritten, read back and re-validated by the owner validator after download"
    - "CTest contracts run through expect_exit.cmake so exit code 0 and a nonzero success count are both required (PASS_REGULAR_EXPRESSION alone would ignore the exit code)"
key-files:
  created: []
  modified:
    - .github/workflows/release.yml
    - .github/scripts/verify-release-gates.sh
    - tests/CMakeLists.txt
    - tests/expected-tests.txt
    - tests/scripts/verify-support-ledger.py
    - tests/scripts/verify-v02-consumers.py
    - tests/scripts/verify-v02-delivery.py
    - docs/support/v0.2.0.md
    - docs/cgb-corpus.md
key-decisions:
  - "Receipts that embed per-run identity (corpus, consumer, fuzz, performance) are attached once and a retry reuses the attached bytes; deterministic ones (source-archive receipt) must be byte-identical. Nothing is ever replaced."
  - "The corpus and sidecar pair is attached sidecar first, receipt last; a retry that finds only one of them refuses to regenerate."
  - "The fuzz job names the tagged source through GITHUB_SHA in step env because the producer records GITHUB_SHA and this workflow runs on main."
  - "The performance job passes the plan-05 reviewed shared-run-loop disclosure so the +5% trigger resolves to accepted-with-disclosed-regression; it is recorded only when the trigger fires."
  - "v02_support_ledger is the receipt-free static ledger check; the receipt-bound --check-current runs in the release corpus job after the receipt exists, because the full CTest stream that produces the receipt cannot depend on it."
requirements-completed:
  - CGB-11
  - SHIP-09
  - SHIP-10
  - SHIP-11
coverage:
  - id: D1
    description: "The exact-tag Linux candidate path runs the final-notes adoption contract, the downloaded relocated C and C++ consumer proof, the GitHub-generated source archive inspection and the combined candidate/product/archive verification, and attaches the consumer and source-archive receipts to the draft without replacing existing assets."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash .github/scripts/verify-release-gates.sh --self-test"
        status: pass
      - kind: other
        ref: "actionlint .github/workflows/release.yml"
        status: pass
  - id: D2
    description: "New exact-tag corpus, Clang 18 libFuzzer and paired performance jobs regenerate the support-ledger sidecar and corpus receipt, fuzz receipt and performance receipt on the tagged checkout, validate them before upload and after download, and the aggregate manifest waits for all three; deleting any required invocation or transfer, moving producers after publication or dropping a needs entry is rejected."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash .github/scripts/verify-release-gates.sh --self-test"
        status: pass
      - kind: integration
        ref: "bash tests/scripts/verify-release-candidate.sh --self-test"
        status: pass
  - id: D3
    description: "A downloaded sidecar is verified by the real support-ledger owner without the producer build tree (opt-in --evidence-only) while an outside receipt without the opt-in and an altered present build file are still rejected, and the delivery checker passes the flag to the real owner."
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-support-ledger.py --self-test"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-delivery.py --self-test"
        status: pass
  - id: D4
    description: "The eleven v02 contracts are registered exactly once in the configured CTest set and the required inventory, each requires exit code 0 and a nonzero success count, all pass, the executed full inventory of 1144 cases matches exactly with none skipped, and an empty selection, a missing required name, a duplicated name and an unregistered contract are each rejected."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "ctest --test-dir build -R ^v02_ --output-on-failure --no-tests=error"
        status: pass
      - kind: integration
        ref: "bash .github/scripts/verify-test-inventory.sh build/v02-full.xml tests/expected-tests.txt --core-only"
        status: pass
  - id: D5
    description: "The tracked v0.2.0 ledger is current against its covered source inputs and the fresh complete nonce-bound corpus receipt (107 of 107 cases, 25 guest passes, 82 matched expected failures, 4959 assertion rows), with a receipt-free static check whose changed-input, missing-input and unparseable-ledger controls are rejected."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-support-ledger.py --check-current --receipt build/cgb-corpus-receipt.json"
        status: pass
      - kind: integration
        ref: "python3 -I tests/scripts/verify-support-ledger.py --self-test"
        status: pass
duration: "about 3 hours"
completed: "2026-10-20"
status: complete
---

# Phase 15 Plan 09: Exact-Tag Evidence Wiring and v02 Contract Registration Summary

**The release workflow now generates the corpus, schema-2 sidecar, Clang 18 libFuzzer, paired performance, downloaded-consumer and source-archive evidence from the exact tag, attaches each to the unpublished draft without replacement, and the eleven v02 contracts are exact-once members of the CTest and required inventories (full run 1144/1144).**

## Accomplishments

- **Linux candidate job** (`release.yml`): final release notes must pass `verify-v02-adoption.py --release-notes`; the downloaded core archive is extracted outside the checkout and proved by `verify-v02-consumers.py --prefix`; the GitHub generated archive is downloaded over HTTPS with a size bound, inspected with the plan-07 checker against the checkout and re-checked from its receipt; `verify-release-candidate.sh --verify-final` binds candidate receipt, product package and archive receipt.
- **Three new exact-tag producer jobs** (`candidate-corpus`, `candidate-fuzz`, `candidate-performance`), each guarded by the trusted-main, tag-to-source and single-draft checks and each recognising already attached evidence so a retry reuses it:
  - corpus: native preset build, `--begin-run`, one full CTest stream, `--from-ctest`, claims check, `--check-current`, inventory check, then sidecar generation and `--verify-sidecar` from the same receipt;
  - fuzz: pinned Clang 18, ASan/UBSan preset, `run-bounded-fuzz.sh --explore --receipt`, `verify-v02-fuzz.py --verify` before upload and again on the downloaded copy;
  - performance: `measure-release-baseline.sh --qualify-v02`, `verify-v02-performance.py --verify` before upload and after download.
- The aggregate manifest job waits for all three, validates the attached evidence families through `verify-release-gates.sh --check-v02-evidence`, and its expected asset set, download patterns and manifest fields now use the v0.2 evidence names. Publication is unchanged and still downstream of the final gate.
- **Gate self-test** pins 21 invocation/transfer counts (each removed once: 21 controls), producers-after-publication, three dropped `needs` entries, three retained-platform controls (macOS player smoke, Windows consumer smoke, unsigned/not-notarized declaration), a shared-readback-directory control and five inventory mutations: 33 controls through the real `check_config` entry point.
- **CTest**: `gbb_add_v02_contract` registers `v02_game_claims`, `v02_game_claims_controls`, `v02_support_ledger`, `v02_support_ledger_controls`, `v02_adoption_docs`, `v02_adoption_docs_controls`, `v02_consumer_controls`, `v02_performance_controls`, `v02_fuzz_controls`, `v02_source_archive_controls` and `v02_delivery_controls`, each through `expect_exit.cmake` (exit 0 plus nonzero success count), and `expected-tests.txt` names each once.
- `verify-support-ledger.py` gained `--check-ledger` (receipt-free, 3 controls) and `--evidence-only` (verification of a downloaded sidecar; 3 controls). `verify-v02-consumers.py` self-test honours `GBB_TEST_BUILD_DIR` so the sanitizer build tree works.

## Task Commits

1. **Task 1 (tracer): Linux exact-tag path to strict downloaded qualification** - `a6d28b9` (`feat`)
2. **Task 2: register contracts and expected inventory** - `1f583b1` (`feat`)
3. **Task 2 follow-up: refreshed v0.2.0 ledger snapshot** - `721c579` (`docs`)
4. **Task 2 follow-up: exact-once inventory controls in the gate self-test** - `9d50857` (`test`)

## Verification Evidence

Tracer gate (rerun after each change; `verify-release-candidate.sh --self-test` requires a clean implementation tree, so it was rerun after commit):

- `bash .github/scripts/verify-release-gates.sh --self-test` exit 0; reports `workflow-wiring-controls=33`.
- `bash tests/scripts/verify-release-candidate.sh --self-test` exit 0.
- `python3 -I tests/scripts/verify-v02-delivery.py --self-test` exit 0: 4 positives, 36 rejected controls, 2 real-owner rejections. A mutant that drops `--evidence-only` from the production call fails it.
- `actionlint .github/workflows/release.yml` exit 0.
- `python3 -I tests/scripts/verify-support-ledger.py --self-test` exit 0 (positive=5, rejected_controls=24 in the sidecar suite, static suite positive=1 rejected_controls=3).

Task 2 gate:

- `cmake --preset phase1 && cmake --build --preset phase1` succeeded.
- `ctest --test-dir build -R '^v02_' --output-on-failure --no-tests=error`: 11/11 passed (88 s).
- Full `ctest --test-dir build --output-on-failure --no-tests=error --output-junit build/v02-full.xml`: 1144/1144 passed (384 s). `verify-test-inventory.sh build/v02-full.xml tests/expected-tests.txt --core-only`: "Verified 1144 executed CTest cases; none skipped."
- Negative controls through real entry points: `ctest -R '^v02_nonexistent$' --no-tests=error` exits 8; the inventory check exits 1 when `v02_fuzz_controls` is removed from the required file.
- `bash tests/scripts/verify-dmg-baseline.sh` and `--junit build/v02-full.xml --inventory core`: baseline status=pass.
- Corpus receipt (producer revision `1f583b130c5dd5f44f03796ddffd3a7a8bff5e00`, nonce-bound full stream, 1144 CTest cases): 107/107 cases, 25 guest passes, 82 matched expected failures, 4959 assertion rows (2845 pass, 2114 fail). `verify-cgb-corpus-claims.py --receipt` and `verify-support-ledger.py --check-current` passed.
- Local rehearsal of the Linux consumer step: `verify-v02-consumers.py --prefix` over an install outside the checkout wrote a passed receipt bound to the checkout HEAD.

Not run, by instruction: nothing was tagged, released, pushed, merged or published; PR #70 is untouched; no hosted workflow ran. v0.2.0 is not published.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The real support-ledger owner could never verify a downloaded sidecar**
- **Found during:** Task 1 (reading the owner against the plan-08 gate)
- **Issue:** `verify-support-ledger.py --verify-sidecar` requires the receipt to sit at `build/cgb-corpus-receipt.json` inside the checkout and re-hashes the producer's build files from the working tree. The plan-08 gate passes a downloaded receipt from a temporary directory in a job that never built the product, so it could not pass on a real draft; the plan-08 positive path used stub owners.
- **Fix:** opt-in `--evidence-only` (only with `--verify-sidecar`) takes the receipt path from the ledger identity and skips only build files that are absent; source inputs, receipt content and any present build file are still checked. The delivery checker passes it. Generation and `--check-current` are unchanged. Controls added for an outside receipt without the opt-in, an absent build without the opt-in and a tampered present build file.
- **Files modified:** `tests/scripts/verify-support-ledger.py`, `tests/scripts/verify-v02-delivery.py`
- **Commit:** `a6d28b9`

**2. [Rule 3 - Blocking] Gate self-test pinned the retired performance and readback workflow text**
- **Found during:** Task 1
- **Issue:** `verify-release-gates.sh` asserted the old `release-performance-receipt.json` step and its readback directories, which the new producers replace.
- **Fix:** replaced those validators with count-based producer, ordering, retained-platform, readback-directory and inventory validators plus mutations for each.
- **Files modified:** `.github/scripts/verify-release-gates.sh`
- **Commit:** `a6d28b9`, `9d50857`

**3. [Rule 3 - Blocking] `v02_support_ledger` cannot depend on its own run's receipt**
- **Found during:** Task 2
- **Issue:** the plan asks `v02_support_ledger` to check a current complete corpus receipt, but the receipt is built after the full CTest stream and `--begin-run` replaces it with an incomplete record, so an in-stream check is circular. The local receipt was also stale.
- **Fix:** `--check-ledger` is a receipt-free currency check of the tracked ledger (schema, inventory validator and every covered source input); the receipt-bound `--check-current` runs in the release corpus job after the receipt is produced. The test still fails if the ledger or any covered input is missing or changed.
- **Files modified:** `tests/scripts/verify-support-ledger.py`, `tests/CMakeLists.txt`
- **Commit:** `1f583b1`

**4. [Rule 3 - Blocking] Registering the tests changed covered ledger inputs**
- **Found during:** Task 2 (`v02_support_ledger` failed)
- **Issue:** `tests/CMakeLists.txt` and `tests/expected-tests.txt` are covered inputs of `docs/support/v0.2.0.md`.
- **Fix:** committed the registration, produced a fresh nonce-bound complete receipt from that revision, ran `--write-current`, and updated the three identity strings in `docs/cgb-corpus.md`. No support claim, count or limitation changed.
- **Files modified:** `docs/support/v0.2.0.md`, `docs/cgb-corpus.md`
- **Commit:** `721c579`

**5. [Rule 3 - Blocking] Consumer self-test assumed `build/`**
- **Issue:** it installed from `ROOT/build`, which does not exist in the sanitizer job.
- **Fix:** `GBB_TEST_BUILD_DIR` (already used by the corpus report tests) selects the build tree; CTest sets it.
- **Files modified:** `tests/scripts/verify-v02-consumers.py`
- **Commit:** `1f583b1`

**Total deviations:** 5 (1 Rule 1, 4 Rule 3). Impact: four files outside the plan's `files_modified` changed; each was required for a real draft to pass or for a registered test to pass.

## Known Limitations and Hosted Risks for Plan 15-10

- None of the new workflow jobs has executed hosted. Local proof is actionlint, YAML parse, the gate's static self-test controls and the owner self-tests. Unverified hosted assumptions: overriding `GITHUB_SHA` in the fuzz step environment is honoured; the performance qualification and full corpus stream fit their 45 and 60 minute limits; the Windows and sanitizer jobs run the three new self-test registrations (the consumer self-test takes about 35 seconds locally).
- `--check-current` is not run by `ci.yml`; it first runs hosted in the release corpus job.
- A retry that finds only the sidecar or only the corpus receipt attached refuses to regenerate; the attached asset must be removed deliberately.
- The performance disclosure text is recorded only if the hosted +5% trigger fires; a hosted measurement could instead show no trigger or a different magnitude, and the receipt records whichever occurs.

## Known Stubs

None.

## Threat Flags

None. New jobs use `contents: write` only on the draft-upload jobs, reuse the existing trusted-main, tag-to-source and single-draft guards, fetch the source archive over HTTPS with a size bound and make no new network endpoints beyond the GitHub archive URL already used by the plan-08 gate.

## Next

Ready for 15-10 (hosted exact-tag execution, PR review and protected merge). Phase 15 is not complete; no auto-advance.

## Self-Check: PASSED
