---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: "07"
subsystem: testing
tags:
  - release
  - source-archive
  - notices
  - fixtures
  - supply-chain
requires:
  - phase: "Phase 15 Plan 04"
    provides:
      - "THIRD_PARTY_NOTICES.md manifest and notice digest table for all admitted fixture directories and the source-archive versus product-package guidance"
provides:
  - "A bounded stdlib checker for GitHub-generated exact-tag source archives (tar.gz and zip) that never extracts"
  - "A source archive receipt (archive_sha256, tag, source_sha, source_tree_sha256, admitted_fixture_identities, notice_sha256, inspected_members)"
  - "A product-package fixture-leak check wired into the release candidate --verify entry point"
  - "A --verify-final mode that requires the source archive and its receipt as distinct final evidence"
affects:
  - "Later Phase 15 release workflow and delivery plans that download the generated v0.2.0 source archive and call this checker with the frozen tag and SHA"
actuals:
  tokens: 14350
  tasks: 2
  commits: 4
plan_head_before: 06ef6246058a5e1845c48d8c1fe85702547086e6
plan_head_after: 0f9cf11db53f8129fc5560477221ea3974134cc2
tech-stack:
  added: []
  patterns:
    - "Single-pass streaming inspection with declared-size limits checked before any read (100000 entries, 1 GiB total, 64 MiB per member, 4096-byte paths); limit flags can only tighten"
    - "Rejections are coded (REJECT code: reason) and self-tests assert the exact code, so a control that fails for the wrong reason is itself a failure"
    - "A fixture-leak control is proven against the receipt verifier alone first, so only the product check can be the rejecting component"
key-files:
  created:
    - tests/scripts/verify-v02-source-archive.py
  modified:
    - tests/scripts/verify-release-candidate.sh
key-decisions:
  - "Bind the tag to the archive through the commit ID GitHub embeds (tar pax global header, zip archive comment) and, when a checkout is supplied, through the tagged Git tree blob IDs; export-ignore or export-subst therefore cannot silently change an archive."
  - "Without a tagged tree, only relative links staying inside the archive root are tolerated; with --repo the exact tree decides, because the committed tree contains tracked symbolic links."
  - "--verify keeps its ten-argument contract and gains the fixture-leak check; the source archive receipt is required only by the new --verify-final so no existing workflow call changes."
requirements-completed:
  - SHIP-10
  - SHIP-11
coverage:
  - id: D1
    description: "A generated tar.gz or zip source archive of an exact tag is accepted only when its embedded commit, single root, tagged Git tree, admitted fixture manifests, LICENSE notices and ROM digests all match the notice digest table, and the receipt records the archive, source tree, notice and fixture identities."
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-source-archive.py --self-test"
        status: pass
  - id: D2
    description: "Missing notice, altered licensed fixture digest, unauthorized or unadmitted fixture and ROM, wrong tag or source, tree mismatch, traversing or absolute or duplicate or overlong paths, links, special members, oversize members and entry or size limits each fail the real command line for their own coded reason, and the real committed repository tree is accepted and rejected when a notice is removed."
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-source-archive.py --self-test"
        status: pass
  - id: D3
    description: "The installed core archive is checked through the real --verify entry point: a bundled third-party fixture directory and a renamed third-party ROM are rejected as product-fixture-leak even though the receipt verifier alone accepts them, and the clean package is accepted."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-release-candidate.sh --self-test"
        status: pass
  - id: D4
    description: "Source archives and product packages cannot be interchanged in either direction, the final gate requires the source archive receipt as its own evidence and rejects a source or build receipt, a stale archive digest, another tag or source SHA and an empty fixture inventory, and a skipped or omitted downloaded consumer smoke result is rejected by the actual release validator."
    requirement: SHIP-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "bash tests/scripts/verify-release-candidate.sh --self-test"
        status: pass
      - kind: unit
        ref: "python3 -I tests/scripts/verify-v02-source-archive.py --self-test"
        status: pass
duration: "about 45 min"
completed: "2026-10-20"
status: complete
---

# Phase 15 Plan 07: Source Archive and Product Package Proof Summary

**A stdlib checker streams GitHub-generated exact-tag source archives against the notice digest table and the tagged Git tree, a fixture-leak check guards the installed core archive, and a new --verify-final requires the source archive receipt as separate evidence, backed by 44 and 25 real-entry negative controls.**

## Performance

- **Duration:** about 45 minutes (start time was not recorded)
- **Completed:** 2026-10-20
- **Tasks:** 2
- **Files modified:** 2 (one created)

## Accomplishments

- Added `tests/scripts/verify-v02-source-archive.py`. `--archive PATH --tag TAG --source-sha SHA --output PATH [--repo GIT_DIR]` inspects a gzip tarball or zip without extracting, applies the 100000-entry, 1 GiB, 64 MiB and 4096-byte limits from declared metadata before reading, strips only the single expected `<name>-<version>` root, and binds the tag to the embedded commit ID and (with a checkout) to the tagged tree's blob IDs. It then requires every fixture directory in the notice table, its `LICENSE.txt`, and the recomputed manifest and notice digests to match, and rejects ROM-like files not declared by an admitted manifest.
- Added `--check-product-archive`, which keeps the installed package limited to the three original fixtures, rejects renamed third-party ROM bytes (matched by digest against the repository fixtures), links and source-archive content, and requires the header and tracer and MBC1 manifests.
- Added `--check-receipt`, which recomputes the receipt from the archive bytes and rejects any other receipt kind, tag, source SHA, digest or an empty fixture inventory.
- Extended `tests/scripts/verify-release-candidate.sh`: `--verify` (ten arguments, unchanged contract) now runs the product fixture-leak check first; `--verify-final` takes the same ten arguments plus the source archive and its receipt and runs the receipt verifier, the product check and the archive receipt check.
- Both checkers run on the real committed repository: a private tagged clone's generated archive passes with 20 admitted fixtures and 1228 members and is rejected when `fixtures/libbet/LICENSE.txt` is removed.

## Task Commits

1. **Task 1 (tracer): generated tagged source snapshot passes rights and content proof** - `178fe2a` (`feat`)
2. **Task 2: distinguish source and installed distributions** - `0f9cf11` (`feat`), with two small supporting fixes `8783f0a` and `e8a7ffe` (`fix`)

## Verification Evidence

- `python3 -I tests/scripts/verify-v02-source-archive.py --self-test` passed: 7 accepted cases and 44 negative controls, each rejected with its expected code. Runtime about 5 s.
- `bash tests/scripts/verify-release-candidate.sh --self-test` passed on the committed tree (exit 0, about 7 s): the existing receipt, archive and consumer checks plus 2 accepted and 25 rejected entries in this run's log, including both fixture leaks, skipped and omitted consumer smoke, a source receipt, build receipt and tampered receipts as the archive receipt, and substitution in both directions. The self-test runs the CMake install, builds the relocated C and C++ consumers and executes them.
- The fixture-leak control is checked to be the only rejecting component: the receipt verifier alone accepts each leaked archive before the real `--verify` entry rejects it with `REJECT product-fixture-leak`.
- No tag, release, push or publication was created. Tags and archives exist only in private temporary clones and are removed at exit; the real repository is untouched.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Archive open failure surfaced as a traceback**
- **Found during:** Task 2 (self-test setup)
- **Issue:** a missing or unreadable archive path raised `FileNotFoundError` instead of a coded rejection.
- **Fix:** OSError during open is reported as `REJECT archive-unreadable`.
- **Files modified:** `tests/scripts/verify-v02-source-archive.py`
- **Commit:** `8783f0a`

**2. [Rule 1 - Bug] Product link rejection used a source-archive code**
- **Found during:** Task 2 (substitution control)
- **Issue:** a source archive offered as a product package was rejected with `link-not-allowed`, not a product-scoped code, so the substitution control could not assert a product reason.
- **Fix:** renamed to `product-link-not-allowed`.
- **Files modified:** `tests/scripts/verify-v02-source-archive.py`
- **Commit:** `e8a7ffe`

**Total deviations:** 2 auto-fixed (both Rule 1). Impact: scope unchanged; the plan's two files only.

## TDD Gate Compliance

Each task was committed once after its GREEN run; separate RED commits were not made. The substitution control initially failed for the wrong reason (`link-not-allowed` instead of a product code) and the leak control initially could not reach the product check until its receipts were rebuilt around the leaked bytes; both were corrected before commit.

## Known Limits and Pending Evidence

- The checker is not yet registered in CTest or CI and the release workflow does not yet download GitHub's generated v0.2.0 archive or call `--verify-final`; that wiring belongs to later Phase 15 plans. It has been run directly only.
- Self-tests use archives generated locally by `git archive` and Python; GitHub's own generated bytes have not been inspected, and the pax-comment and zip-comment commit binding assumes GitHub follows `git archive` conventions. This is pending hosted evidence.
- Without `--repo`, tag binding rests on the embedded commit ID and root name only; the tagged-tree comparison needs a checkout of the tag.
- No v0.2.0 release, tag or publication exists, and nothing here claims one. Plan 15-06 (fuzz campaign) is parked and was not touched.

## Known Stubs

None.

## Threat Flags

None. T-15-13 and T-15-14 are mitigated by the production-entry controls above. No network surface, install or dependency was added (T-15-SC unchanged).

## Next Phase Readiness

Plan 15-07 is complete. Phase 15 is not complete; stop at Phase 15 and do not advance to another phase. Later plans should register the two self-tests in CTest and wire `--archive` and `--verify-final` into the release workflow with the frozen tag and SHA.

## Self-Check: PASSED

- `tests/scripts/verify-v02-source-archive.py` and `tests/scripts/verify-release-candidate.sh` exist and are committed.
- Commits `178fe2a`, `8783f0a`, `e8a7ffe` and `0f9cf11` are on the branch.
- Both task verification commands pass on the committed bytes.
