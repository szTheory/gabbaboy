---
phase: "GB-06"
slug: "qualified-dmg-release-and-consumer-handoff"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-08"
updated: "2026-10-10"
---

# Phase 6 — Security

> Phase-level threat verification for release automation, downloaded packages, native consumers, bounded emulator inputs, and published evidence.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|---|---|---|
| Contributor changes to privileged automation | Trusted branch events can run release automation with job-scoped `GITHUB_TOKEN` permissions. Untrusted pull-request code must not execute in a privileged release job. | Workflow source, event/ref identity, token scopes, protected-branch checks |
| Tagged source to release candidate | The release workflow builds and attaches packages for one tag and exact source SHA; the candidate remains a draft until downloaded-byte checks finish. | Tag/version/source identity, binaries, manifests, checksums, receipts |
| Downloaded archives to smoke consumers | Release archives and included binaries are treated as untrusted until inventory, digest, and path checks pass. | Compressed archives, paths, extracted files, subprocess inputs and outputs |
| Native library to adopter | Public C/C++ consumers and host applications exchange bounded API data and host-owned battery files. | ROM bytes, frame/audio buffers, save identity and payloads, result codes |
| Test inputs to emulator and fuzz targets | Legal fixtures and hostile byte streams exercise parser, loader, state, and battery boundaries. | ROM/save/state input, decoded work, allocations, elapsed time |
| Evidence to public compatibility claims | The tracked support ledger, post-tag sidecar, performance receipt, and release metadata support narrowly scoped claims. | Source and corpus identity, denominators, digests, measurements, limitations |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|---|---|---|---|---|---|---|
| T-06-01 | Spoofing | Trusted tag/source identity | high | mitigate | Release checks bind trusted repository, exact tag, CMake version, full source SHA, and current protected-main evidence before building. | closed |
| T-06-02 | Tampering | Draft assets and receipt | high | mitigate | Final downloaded archives are hashed; duplicate/conflicting names are rejected; extracted consumer bytes are smoke-tested against source and manifest identity. | closed |
| T-06-03 | Elevation of privilege | Release workflow token | high | mitigate | Release automation uses trusted events and job-scoped permissions; actions are full-SHA pinned; protected exact-head checks guard the merge and publish path. The repository-level create/approve-PR setting is recorded as an accepted residual capability below. | closed |
| T-06-04 | Tampering | Platform archives | high | mitigate | The downloaded inventory must match the expected platform assets and digests before extraction or consumer execution. | closed |
| T-06-05 | Elevation of privilege | Archive extraction | high | mitigate | The bounded safe extractor rejects traversal/link escapes and caps compressed size, members, path components, expanded bytes, and tar input. | closed |
| T-06-06 | Denial of Service | Player smoke and save | medium | mitigate | Smoke processes and inputs are bounded; legal digest-pinned fixtures are used; failed save/session transitions preserve the prior valid state. | closed |
| T-06-07 | Tampering | Relocated example linkage | medium | mitigate | The consumer is configured and built outside the source tree and links through the installed public target without private build-tree or SDL dependencies. | closed |
| T-06-08 | Tampering | Battery file handling | high | mitigate | Battery import/export validates size and identity and uses host atomic-replacement and recovery behavior; failure cases exercise preservation of prior data. | closed |
| T-06-09 | Repudiation | Support ledger | medium | mitigate | The tracked ledger is validated against manifests and a post-tag sidecar binds its tagged blob digest and full source SHA without a self-referential hash. | closed |
| T-06-10 | Tampering | Performance receipt | medium | mitigate | Receipts check source/build/host identity, raw samples, trace-pair output digests, precision, and uncertainty; they do not establish budgets from one noisy sample. | closed |
| T-06-11 | Tampering | ROM and save-state boundaries | high | mitigate | Length and identity checks precede mutation; sanitizer regressions assert guard bytes and active-state preservation for failed operations. | closed |
| T-06-12 | Denial of Service | Fuzz targets | medium | mitigate | Fuzz inputs, decoded work, time, memory, and workers are bounded; findings retain deterministic replay paths. Runtime-absent lanes are not described as fuzz-passed. | closed |
| T-06-13 | Spoofing | Required PR contexts | high | mitigate | Current required contexts are matched to the exact PR head and event; missing, stale, skipped, cancelled, timed-out, or failed checks block eligibility. | closed |
| T-06-14 | Tampering | Public release assets | high | mitigate | The published asset inventory is reconciled to the pre-publish qualified inventory and freshly downloaded bytes, API IDs, sizes, and SHA-256 digests. | closed |
| T-06-15 | Repudiation | macOS trust claim | high | mitigate | The release states that the player is unsigned and not notarized; no Apple-verified or hardware-qualified status is claimed. | closed |
| T-06-16 | Repudiation | Release notices and API coverage | medium | mitigate | Rights and trust statements are reviewed; the capability matrix records which GitHub release operations are used, guarded, or intentionally absent. | closed |
| T-06-17 | Elevation of privilege | Draft-to-public transition | high | mitigate | Publication requires the existing release-please draft, exact source/tag identity, a passing downloaded-byte gate, and one guarded publish transition; the candidate self-test rejects publishing before that gate. | closed |
| T-06-SC | Tampering | Package-manager supply chain | low | accept | Phase 6 adds no npm, pip, or cargo installation. Existing pinned build/test tools remain scoped to their documented workflows. | closed (accepted) |

*Status: open · closed · open — below high threshold (non-blocking).*

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| GB-06-AR-01 | T-06-03 | The repository setting allowing Actions to create and approve pull requests is enabled for the planned Release Please `GITHUB_TOKEN` route. The repository default workflow permission remains read-only; the release job scopes its write permission, trusted branch/event rules constrain execution, and exact-head branch protection gates merging. A token in that trusted job retains the capability to create or approve PRs, so changes to triggers, permissions, or branch protection require re-review. | Phase owner under the authorized Phase 6 release setup | 2026-10-08 |
| GB-06-AR-02 | T-06-SC | No new package-manager dependency was added in this phase. | Phase 6 plan | 2026-10-08 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---:|---:|---:|---|
| 2026-10-08 | 18 unique IDs across seven plan threat registers | 18 | 0 at/above high threshold | Phase executor, ASVS L1 plan and result-artifact classification |
| 2026-10-09 | 18 unique IDs across seven plan threat registers | 18 | 0 at/above high threshold | Phase 6 security re-audit, ASVS L1 code and release-evidence check |
| 2026-10-10 | 18 unique IDs across seven plan threat registers | 18 | 0 at/above high threshold | Rechecked the output cleanup boundary after CR-01; repository descendants are rejected before cleanup and the `.git` preservation regression passes in the 9-test focused suite. |
| 2026-10-10 (publication) | 18 unique IDs across seven plan threat registers | 18 | 0 at/above high threshold | Publication is now all-or-nothing: on failure the helper withdraws only inodes it published and keeps concurrent replacements. Deep re-review clean; focused suite 17/17. |

The 17 planned mitigations and the repeated low-severity package-manager entry have complete plan-time threat-register coverage. The ASVS level is 1, so the workflow permits this classification path without a separate auditor when no blocking threat remains. Phase summaries provide the exact-head, downloaded-byte, bounded-input, and release evidence. The 2026-10-09 re-audit confirmed code presence for declared mitigations and found no new unmapped threat flag in the Phase 6 summaries. The 2026-10-10 CR-01 follow-up verifies that `tests/scripts/verified_player_output_dir.py` rejects every repository descendant before cleanup; the regression preserves both expected artifact files under `.git`, and the focused suite passes 9/9. PR #46 passed exact-head required checks before merge. Future v0.1.1 Release Please PR #41 remains open with merge state `BLOCKED` and no checks reported; it is not green. This operational residual applies to the future version PR. The already published v0.1.0 remains source-bound to `e30d168`, and its 18 live release assets matched API digests on fresh download. No merge or release action is authorized by this report. This report does not claim physical-device, perceptual, signing, or notarization verification.

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks are documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-08. The workflow-token permission tradeoff remains documented; the public release remains explicitly unsigned, not notarized, and limited to the published software evidence.
