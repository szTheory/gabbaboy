---
phase: "20"
slug: fixture-admission-tune-up
# threats_open counts OPEN threats at or above workflow.security_block_on.
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: "2026-10-31"
source_head: ee4fd369d5e318c9d416534f92aeee0d45ecd2e5
---

# Phase 20 — Security

The ASVS L1 audit reviewed all four authored threat registers at `ee4fd369d5e318c9d416534f92aeee0d45ecd2e5`. All 16 authored register entries (13 unique IDs) are mitigated; the repeated T-20-SC entry is counted once per plan register. T-20-04's Git blob read is now streamed under a 32 MiB + 1 byte limit and 30-second deadline, with terminate/reap/reader cleanup verified by the stalled and over-limit controls. `threats_open: 0` counts the authored threat register at the configured `high` threshold.

This register verdict does not close Phase 20. The final code review separately reports three unresolved blockers: the macOS/Windows release checks still trust mutable tagged-workspace files (CR-05), the product allowlist is not immutably pinned (CR-08), and repository-admission workflow calls can be redirected (CR-09). The full local CTest run also has unresolved failures recorded in `20-VALIDATION.md` and `20-VERIFICATION.md`; the owner must authorize a rescope before phase closure.

Plan 20-04 closes the previously recorded directory-walk and `git ls-tree` enumeration gaps: fixture walks now count entries as they are visited, and Git tree output is streamed with byte and record limits plus child cleanup. It does not bound `git show` blob output during consumption, so the broader bounded-read mitigation in T-20-04 is not fully satisfied.

`RIGHTS-01` remains pending because no candidate was admitted and code cannot determine legal grant scope. That requirement is separate from this security threat register and is not counted as an open security threat.

## Trust Boundaries

| Boundary | Data crossing |
|----------|---------------|
| Fixture records and Git objects → admission checker | Untrusted record fields, paths, source revisions, fixture bytes, and repository trees |
| Installed/staged product → archive → extracted consumer | Product files, notices, paths, and inventory identities |
| Player package → extraction and execution | Downloaded archive members and player bytes |
| Dependency declarations → build/test environment | Package-manager or new dependency changes |

## Threat Register

Evidence paths are relative to the repository root. The shared T-20-SC threat appears in each of the four plan registers and is reported once below; the table therefore covers 13 unique IDs / 16 authored register entries.

| Threat ID | Category | Component | Severity | Disposition | Mitigation / remaining evidence | Status |
|-----------|----------|-----------|----------|-------------|---------------------------------|--------|
| T-20-01 | Tampering | Admission identity and component scope | high | mitigate | `tests/scripts/verify-fixture-admission.py:115-133, 456-467, 577-629` requires full commit identities, checks immutable objects and ancestry, pins the manifest and fixture/evidence bytes, and binds the notice index. | closed |
| T-20-02 | Tampering | Product path and inventory policy | high | mitigate | `tests/scripts/verify-fixture-admission.py:665-728, 740-801, 854-920, 929-983` validates the fixed policy, derives expected paths from pinned source bytes, rejects unknown/link/duplicate entries, compares protected size/digests, and requires exact inventory equality. Plan 20-01/20-02 summaries record positive and mutation controls. | closed |
| T-20-03 | Repudiation | Rights, notices, and legal-scope claims | medium | mitigate | `tests/scripts/verify-fixture-admission.py:433-447, 504-576, 617-629` requires reviewer rationale and binds component evidence and scope to pinned paths; `docs/fixture-admission.md:182-189` explicitly leaves legal authority/scope to a maintainer and disclaims automated clearance. | closed |
| T-20-04 | Tampering | JSON, paths, file walking, and bounded reads | medium | mitigate | JSON size/duplicate-key checks, canonical relative-path validation, bounded file reads, and no-follow fixture traversal are present at `tests/scripts/verify-fixture-admission.py:84-105, 141-226, 398-595`. `blob()` streams `git show` under a 32 MiB + 1 byte cap and 30-second deadline and terminates/reaps the child on error/timeout; the fake stalled and overflow controls assert stream closure and cleanup at lines `2025-2100`. | closed |
| T-20-05 | Tampering | Core install and preview inventory | high | mitigate | `cmake/PreviewPackageSmoke.cmake:65-130` validates actual stage/extracted bytes against the shared policy and accepted stage inventory before consumer use; `cmake/VerifyInstalledPackage.cmake:10-34` applies the shared checker to the installed prefix. Plan 20-02 summary records the real-tree and mutation controls. | closed |
| T-20-06 | Repudiation | Fixture notices, core root MIT, and sidecar | medium | mitigate | `tests/scripts/verify-fixture-admission.py:731-746, 897-920` binds the pinned notice index and supplied sidecar; product source identities and notice paths are checked at lines `749-778`. Plan 20-02 summary records missing, changed, and misnamed notice controls. | closed |
| T-20-07 | Tampering | Core release/reuse/download archive handling | high | mitigate | `tests/scripts/verify-v02-consumers.py:316-383` bounds and validates archive members, rejects traversal, duplicate paths and special files, and removes partial extraction; `tests/scripts/verify-v02-source-archive.py:485-507` applies the shared exact product policy to archive bytes. Release and consumer paths invoke extraction and product checks before use (for example, `tests/scripts/verify-release-candidate.sh:16-17, 117-120`). | closed |
| T-20-08 | Information disclosure | Source-to-product fixture leakage | high | mitigate | `tests/scripts/verify-fixture-admission.py:780-801, 854-892` derives forbidden fixture digests from the immutable baseline and current fixture tree, checks product contents independent of filename suffix, and rejects both known fixture digests and unknown paths. Source-archive policy remains separate (`tests/scripts/verify-v02-source-archive.py:485-507`). | closed |
| T-20-09 | Tampering | Player staged/extracted inventory | high | mitigate | `tests/scripts/verify-phase3-player.sh:70-82, 245-254, 783-789` applies the shared player policy and stage inventory to extracted package bytes before player use; `tests/scripts/verify-fixture-admission.py:854-983` enforces actual paths and digests. Plan 20-03 summary records 21 isolated production-wrapper mutation controls. | closed |
| T-20-10 | Repudiation | GabbaBoy, fixture, and SDL licenses | medium | mitigate | `tests/scripts/verify-fixture-admission.py:562-629, 693-704, 731-746, 897-920` pins fixture notices, SDL notice identity, root sidecar identity, and notice-index bytes. Plan 20-03 summary records missing/changed notice controls for the player package. | closed |
| T-20-11 | Tampering | Downloaded player and control isolation | high | mitigate | `tests/scripts/verify-phase3-player.sh:84-90, 245-254` runs isolated temporary mutation controls through the production policy wrapper and invokes extraction before checking the downloaded tree; `.github/scripts/safe_extract_package.py:95-143, 146-205` rejects traversal, duplicate/special members, and unsafe extraction paths. The Plan 20-03 summary records that rejected controls preserve the candidate inventory. | closed |
| T-20-12 | Denial of Service | Fixture filesystem and Git tree enumeration | medium | mitigate | `tests/scripts/verify-fixture-admission.py:45-50, 219-373, 376-415` applies a shared 16,384-entry fixture cap, 16,384-record and 32 MiB Git tree caps while consuming input, drains stderr with bounded retention, uses a deadline, and terminates/reaps/closes/joins on failure. Content-caused controls and fake-process cleanup assertions are at lines `1637-1760`; Plan 20-04 summary records the focused self-test and CTest group passing. | closed |
| T-20-SC | Tampering | Package installations | high | mitigate | Phase 20 implementation changes do not modify dependency/package-manager manifests (`git diff --name-only 8162e280 HEAD -- '*requirements*' pyproject.toml setup.py setup.cfg Pipfile poetry.lock package.json package-lock.json` is empty); the new traversal code uses Python standard-library imports (`tests/scripts/verify-fixture-admission.py:6-24`). The four plan summaries list no added tech-stack dependencies. | closed in all four plan registers |

## Open Authored Threats

None. `threats_open: 0` applies only to the authored plan threat registers. The separate code-review blockers above remain security-relevant phase gaps and prevent Phase 20 closure.

## Threat Flags

No `## Threat Flags` sections or entries were present in the four Plan 20 summaries. No unregistered flag was available to map. This is not evidence that the summaries provide a complete attack-surface inventory; this audit verifies the authored threat registers only.

## Accepted Risks Log

None. All plan dispositions are `mitigate`; no accepted risk was inferred or added. `RIGHTS-01` is a pending requirement, not an accepted security risk or a threat disposition.

## Audit Trail

| Date | Source | Closed entries | Open entries | Blocking open | Audit |
|------|--------|----------------|--------------|---------------|-------|
| 2026-10-31 | `46a80d307dae363e5607d560fc05d2b011937a94` | 15/16 | 1/16 | 0 | Earlier audit after Plan 20-04; T-20-04 remained open for Git blob streaming. |
| 2026-11-01 | `ee4fd369d5e318c9d416534f92aeee0d45ecd2e5` | 16/16 | 0/16 | 0 | Final ASVS L1 register audit after both review-fix rounds; Git blob, filesystem, Git tree, and product traversal bounds are enforced. Phase closure remains blocked by CR-05, CR-08, and CR-09 in `20-REVIEW.md`. |

The prior T-20-04 finding is preserved in `20-04-PLAN.md` under `<gap_closure>`. Plan 20-04 bounded fixture walks and streamed `git ls-tree`; review-fix round 1 bounded `git show`; review-fix round 2 added a deadline for stalled blob reads. The focused controls pass. `RIGHTS-01` remains pending: no fixture was admitted and the code does not determine legal grant scope.
