---
phase: "GB-04"
slug: "mbc1-and-safe-battery-continuation"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-08"
audited: "2026-10-08"
---

# Phase 4 — Security

The read-only L1 audit checked all seven plan-authored threat registers against
the implementation, named regression cases, local package checks, and published
evidence. The 15 phase-specific threats and seven repeated no-package-install
entries have controls or documented acceptance. The final exact-head CI and
package receipts are recorded separately in `04-VALIDATION.md`. No physical
hardware or power-loss qualification is claimed.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|---|---|---|
| Guest ROM to cartridge core | Untrusted headers, ROM bytes, and guest-controlled mapper registers enter bounded instance state. | ROM bytes, addresses, mapper writes |
| Battery API to caller memory | Caller-owned buffers cross the public C API; invalid operations must not partially mutate cartridge state. | Battery bytes, pointers, lengths, generation |
| Player filesystem to save session | Host files may be malformed, oversized, replaced, symlinked, or concurrently accessed. | Save envelope, path identity, lock state |
| Fixture/tool source to package | Authored source, generated ROM bytes, notices, and tool archives cross into reproduction and package checks. | Digests, license notices, package receipts |
| Test and CI outcomes to support claims | Local and hosted outcomes inform requirements and preview metadata; stale or skipped evidence must not be reported as current. | Test inventories, source SHA, artifact receipts |
| Public evidence to repository readers | Documentation must not expose private saves, local paths, or machine identifiers. | Fixture identifiers, public digests, support limits |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation evidence | Status |
|---|---|---|---|---|---|---|
| T-04-01 | Tampering | ROM loader | high | mitigate | Exact bounded cartridge type/size matrix is validated before candidate allocation or active-state replacement; loader and cartridge matrix regressions. | closed |
| T-04-02 | Tampering | Save envelope | high | mitigate | Version, exact length, ROM identity, cartridge type, RAM size, and CRC are checked before battery import; `player_session_reject_matrix`. | closed |
| T-04-03 | Tampering | MBC1 loader | high | mitigate | Supported banking/header matrix and conservative MBC1M candidate policy are covered by `cartridge_bank_matrix`, `loader_mbc1_matrix`, `loader_mbc1m_variant`, and unsupported-header cases. | closed |
| T-04-04 | Tampering | Battery API | high | mitigate | Pointer/size checks precede one-copy transfer; canaries and failed-import preservation are covered by `battery_errors`, `battery_api_fuzz`, and relocated C/C++ consumers. | closed |
| T-04-05 | Tampering | Envelope parser | high | mitigate | Exact version/identity/size/checksum validation precedes live import; reject-matrix, maximum-size, and payload-mutation cases. | closed |
| T-04-06 | Tampering | Save target | high | mitigate | Regular-file/no-symlink checks, exclusive same-directory temporary file, synchronization, atomic rename, and injected write-stage faults in `src/player/session.c` and `player_session_*` tests. | closed |
| T-04-07 | Denial of service | Save read | medium | mitigate | Accepted envelopes have exact bounded sizes; oversized and special-file inputs are rejected before import or unbounded allocation. | closed |
| T-04-08 | Tampering | Concurrent player | high | mitigate | A nonblocking exclusive lock covers each battery-backed session; `player_session_lock_lifecycle` exercises conflict and release. The guarantee is limited to cooperating processes. | closed |
| T-04-09 | Repudiation | Player status | medium | mitigate | Dirty generation, autosave bounds, persistent failure state, and explicit final-flush choices are exercised by cadence and transition-choice tests. | closed |
| T-04-10 | Spoofing | Continuation oracle | medium | mitigate | Separate-process resume distinguishes missing save, wrong ROM identity, and altered payload through named negative controls and guest markers. | closed |
| T-04-11 | Tampering | Fixture artifact | medium | mitigate | Original source, license, source/ROM digests, pinned RGBDS recipe, and byte-identical reproduction are recorded in the fixture manifest and evidence ledger. Path-specific Git attributes preserve assembly LF and ROM bytes on Windows; fresh Windows checkout and exact-head fixture reproduction passed. | closed |
| T-04-12 | Repudiation | CI inventory | high | mitigate | Named nonempty test inventories fail on missing, skipped, failed, or timed-out cases. Exact PR-head required-native, Linux ASan/UBSan, CMake floor, Linux/macOS/Windows inventories, fixture reproduction, and package consumers passed; run IDs and receipts are recorded in `04-VALIDATION.md`. | closed |
| T-04-13 | Information disclosure | Public logs | medium | mitigate | Logs use repository-relative fixture identifiers and digests, not save payloads or local paths; the public-doc privacy scan was clean. | closed |
| T-04-14 | Repudiation | Support ledger | medium | mitigate | `docs/mbc1-evidence.md` names test denominators, source revision, fixture digests, evidence classes, and the hosted exact-head gate. | closed |
| T-04-15 | Information disclosure | Published evidence | medium | mitigate | Public contract and evidence documents contain no local home paths, save payloads, email addresses, or machine identifiers; privacy scan passed. | closed |
| T-04-SC (04-01) | Tampering | Package-manager supply chain | low | accept | No npm, pip, or cargo package installation was introduced in this plan. | closed |
| T-04-SC (04-02) | Tampering | Package-manager supply chain | low | accept | No npm, pip, or cargo package installation was introduced in this plan. | closed |
| T-04-SC (04-03) | Tampering | Package-manager supply chain | low | accept | No npm, pip, or cargo package installation was introduced in this plan. | closed |
| T-04-SC (04-04) | Tampering | Package-manager supply chain | low | accept | No npm, pip, or cargo package installation was introduced in this plan. | closed |
| T-04-SC (04-05) | Tampering | Package-manager supply chain | low | accept | No npm, pip, or cargo package installation was introduced in this plan. | closed |
| T-04-SC (04-06) | Tampering | Package-manager supply chain | low | accept | No npm, pip, or cargo package installation was introduced in this plan. | closed |
| T-04-SC (04-07) | Tampering | Package-manager supply chain | low | accept | No npm, pip, or cargo package installation was introduced in this plan. | closed |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| AR-04-SC | T-04-SC (04-01 through 04-07) | The plans introduce no npm/pip/cargo installation; the named optional RGBDS and SDL acquisition paths retain their explicit versions and digest checks. | Plan-authored low-severity disposition under project dependency policy | 2026-10-08 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---:|---:|---:|---|
| 2026-10-08 | 22 | 22 | 0 | Phase executor, L1 artifact and source review |
| 2026-10-08 | 22 | 22 | 0 | Phase executor, final Windows fixture and exact-head evidence cross-check |
| 2026-10-10 (freshness after Phase 06.1) | 22 | 22 | 0 | Orchestrator ASVS L1 short-circuit (plan-time register, no open threats) |

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks are documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-08; final exact-head CI, fixture reproduction, and downloaded package receipts passed as recorded in phase validation.

## Security Audit 2026-10-09

| Metric | Count |
|---|---|
| Threats found | 22 |
| Closed | 22 |
| Open | 0 |

## Security Audit 2026-10-10 (freshness after Phase 06.1)

Rechecked the register after Phase 06.1 PR #54 (merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`). The register still holds 22 threat IDs, all closed, so `threats_open: 0` is unchanged; under ASVS level 1 with a plan-time register the workflow short-circuits without an auditor pass. The only covered changes are in the player ROM read path:

- `src/player/session.c` `read_rom_file` (ROM side of T-04-01): adds `O_NOCTTY` to the open flags and splits the size-bound and `close()` failure branches. Both branches still free the buffer and fail before any replacement, and the `O_NONBLOCK`/`O_NOFOLLOW` open plus descriptor-based regular-file and size checks are unchanged, so the FIFO hardening holds. `read_save_file` and the save write path (T-04-06, T-04-07) and the session lock (T-04-08) are unchanged.
- `tests/player/test_session.c`: adds 2097153-byte and 2097154-byte replacement-failure assertions; the existing `mkfifo` assertion is unchanged. The optional player suite passed 51/51 on the refresh branch.

No new threat was introduced.

## Security Audit 2026-10-10

| Metric | Count |
|---|---|
| Threats found | 22 |
| Closed | 22 |
| Open | 0 |
