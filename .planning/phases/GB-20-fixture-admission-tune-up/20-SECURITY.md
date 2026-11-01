---
phase: "20"
slug: fixture-admission-tune-up
# threats_open counts OPEN threats at or above workflow.security_block_on.
status: secured
threats_open: 0
asvs_level: 1
block_on: high
created: "2026-10-31"
source_head: 7293eb47a6c799b6455dd854533aca932f4529ad
---

# Phase 20 — Security

The final ASVS L1 audit reviewed all nine authored threat registers at `7293eb47a6c799b6455dd854533aca932f4529ad`. All 29 authored register entries (20 unique IDs plus T-20-SC repeated in each plan) are mitigated. T-20-04's Git blob read is streamed under a 32 MiB + 1 byte limit and 30-second deadline, with terminate/reap/reader cleanup verified by stalled and over-limit controls. `threats_open: 0` counts authored threats at the configured `high` threshold.

The original CR-05/CR-08/CR-09 findings and later archive/path findings were addressed by the authorized rescope. The final source-archive review's WR-01 counter-lifetime warning was closed by commit `7293eb47`: the 256-long-path archive is inspected twice under a total-header cap exactly equal to the first parse's count, so shared counter state would reject the second parse. Final local configure/build, full CTest, and release-candidate replay evidence is recorded in `20-VALIDATION.md` and `20-VERIFICATION.md`; hosted exact-head macOS qualification remains the release gate until its PR check passes.

Plan 20-04 closes directory-walk and `git ls-tree` enumeration gaps: fixture walks count entries as visited, and Git tree output is streamed with byte and record limits plus child cleanup. Follow-up work also bounds `git show` blob output while consuming it and applies a deadline; overflow/stall controls prove child termination, reaping, and reader cleanup.

`RIGHTS-01` remains pending because no candidate was admitted and code cannot determine legal grant scope. That requirement is separate from this security threat register and is not counted as an open security threat.

## Trust Boundaries

| Boundary | Data crossing |
|----------|---------------|
| Fixture records and Git objects → admission checker | Untrusted record fields, paths, source revisions, fixture bytes, and repository trees |
| Installed/staged product → archive → extracted consumer | Product files, notices, paths, and inventory identities |
| Player package → extraction and execution | Downloaded archive members and player bytes |
| Dependency declarations → build/test environment | Package-manager or new dependency changes |

## Threat Register

Evidence paths are relative to the repository root. The shared T-20-SC threat appears in each of the nine plan registers and is reported once below; the table covers 20 unique IDs / 29 authored register entries.

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
| T-20-13 | Tampering | Product policy and forbidden payload bytes | high | mitigate | `tests/scripts/verify-fixture-admission.py` independently pins the product policy and rejects known fixture digests before required/generated/`one_of` path handling in both layouts; core/player mutation controls pass. | closed |
| T-20-14 | Tampering | Trusted macOS/Windows release archive verification | high | mitigate | `.github/scripts/verify-workflow-policy.py` validates downloaded macOS core, macOS player, and Windows core archives using trusted-checkout checker/policy authority; release workflow/archive controls pass. | closed |
| T-20-15 | Tampering | Repository-admission workflow matching | high | mitigate | `.github/scripts/verify-workflow-policy.py` matches required repository-admission commands and arguments exactly; complete isolated mutation subjects reject removal or redirection. | closed |
| T-20-16 | Tampering | Adoption and notice contract consumers | high | mitigate | `tests/scripts/verify-v02-adoption.py` and its contract controls agree on source/product notice distinctions and reject drift; the adoption docs group passes. | closed |
| T-20-17 | Tampering | Dense-input immutable baseline and build identity | high | mitigate | `tests/scripts/verify-dense-input.py` reads baseline evidence from its separately pinned immutable object source while evaluating the source-only mutant checkout; dense-input positives and unqualified-build controls pass. | closed |
| T-20-18 | Denial of Service | Trusted publisher archive metadata and streams | high | mitigate | `.github/scripts/verify-workflow-policy.py` bounds decompressed tar streams and PAX/GNU per-header, aggregate-byte, and count metadata before payload parsing; resource-limit negatives pass. | closed |
| T-20-19 | Tampering | Trusted archive extraction failure cleanup | medium | mitigate | The publisher preflights trusted checker availability and encloses extraction/checking in one cleanup boundary; missing-checker and late-rejection controls prove cleanup and same-destination retry. | closed |
| T-20-20 | Tampering | Windows archive path and extraction containment | high | mitigate | `.github/scripts/verify-workflow-policy.py` rejects drive/ADS syntax and validates directory/file targets and ancestry before creation; controls prove no outside writes, preserved sentinels, and cleanup. | closed |
| T-20-SC | Tampering | Package installations | high | mitigate | Phase 20 adds no package-manager dependency; the traversal/archive code uses Python's standard library. All nine plan summaries list no added dependencies. | closed in all nine plan registers |

## Open Authored Threats

None. `threats_open: 0` applies only to the authored plan threat registers. Rights clearance remains separately pending and is not treated as a threat disposition.

## Threat Flags

No `## Threat Flags` sections or entries were present in the nine Plan 20 summaries. No unregistered flag was available to map. This is not evidence that the summaries provide a complete attack-surface inventory; this audit verifies the authored threat registers only.

## Accepted Risks Log

None. All plan dispositions are `mitigate`; no accepted risk was inferred or added. `RIGHTS-01` is a pending requirement, not an accepted security risk or a threat disposition.

## Audit Trail

| Date | Source | Closed entries | Open entries | Blocking open | Audit |
|------|--------|----------------|--------------|---------------|-------|
| 2026-10-31 | `46a80d307dae363e5607d560fc05d2b011937a94` | 15/16 | 1/16 | 0 | Earlier audit after Plan 20-04; T-20-04 remained open for Git blob streaming. |
| 2026-11-01 | `ee4fd369d5e318c9d416534f92aeee0d45ecd2e5` | 16/16 | 0/16 | 0 | Earlier final audit after two review-fix rounds; the later rescope threats were not yet in scope. |
| 2026-11-01 | `7293eb47a6c799b6455dd854533aca932f4529ad` | 29/29 | 0/29 | 0 | Final ASVS L1 audit across nine plan registers. Trusted release verification, pinned policy, exact workflow matching, bounded parsing/cleanup, Windows containment, dense-input evidence, and exact-cap archive counter-reset control are closed. |

The prior T-20-04 finding is preserved in `20-04-PLAN.md` under `<gap_closure>`. Plan 20-04 bounded fixture walks and streamed `git ls-tree`; follow-up work bounded `git show` and added a deadline for stalled blob reads. The focused controls pass. `RIGHTS-01` remains pending: no fixture was admitted and code does not determine legal grant scope.
