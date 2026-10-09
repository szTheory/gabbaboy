---
phase: "GB-05"
slug: "dmg-audio-and-stable-playback"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-08"
updated: "2026-10-08"
---

# Phase 5 — Security

> Threat mitigations and accepted package-scope risk for DMG audio and stable playback.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Core caller to audio output | Public callers supply a bounded frame buffer and receive PCM from the deterministic core. | Capacity, address ranges, audio frames, and result counts. |
| Core APU to host audio adapter | Guest-generated PCM crosses from the instance-owned core into a bounded single-producer/single-consumer transport. | Signed 16-bit stereo frames and atomic ring indices. |
| Host input events to guest queue | Keyboard, focus, and controller events affect guest-visible held-button state. | Stable controller IDs and bounded timestamped button events. |
| Save transaction to host session | Reset and ROM replacement may clear host audio/input state only after the existing battery transaction succeeds. | Save status, ROM/session state, queued PCM, and input contributions. |
| Authored workload and receipt to publication | Test workload and queue measurements support published feature claims. | Authored ROM bytes, fixture license/digest, revision, build, PCM digest, and labeled software counters. |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-01 | Denial of Service | Core frame preflight | high | mitigate | Validate frame extent and capacity before guest mutation; cover output-full and buffer boundaries with core tests. | closed |
| T-05-02 | Tampering | SPSC publication | high | mitigate | Keep the core instance off the SDL callback; publish through C17 acquire/release indices and verify bounded callback/ring behavior. | closed |
| T-05-03 | Denial of Service | Pulse and sequencer clocks | medium | mitigate | Bound edge advancement and reject emulated-time overflow; cover divider/timeline boundaries. | closed |
| T-05-04 | Denial of Service | Noise period and wave index | medium | mitigate | Use checked fixed-size indices and bounded period arithmetic; test wave nibble/alias and noise-width behavior. | closed |
| T-05-05 | Tampering | PCM buffer | high | mitigate | Reject size overflow and output overlap before writes; preserve output count and guest state on invalid/output-full calls. | closed |
| T-05-06 | Denial of Service | Resampler accumulator | high | mitigate | Bound edge/table work, use checked wide intermediates, documented rounding, and signed-16 saturation; exercise rounding and extremes. | closed |
| T-05-07 | Denial of Service | Callback variable request | high | mitigate | Service requested bytes in bounded chunks, zero-fill shortage, and avoid guest work, allocation, locks, or logging on the callback path. | closed |
| T-05-08 | Tampering | Ring reset and wrap | high | mitigate | Verify atomic widths and ordered ring behavior; quiesce callback before clearing or destroying transport state. | closed |
| T-05-09 | Tampering | Input ownership | medium | mitigate | Track bounded per-source contributions and retry failed releases without releasing another source's held button. | closed |
| T-05-10 | Tampering | Session transition | high | mitigate | Preserve battery save ordering; clear host state only after successful reset/replacement and callback quiescence. | closed |
| T-05-11 | Denial of Service | Device reopen | medium | mitigate | Bound device recovery; use a counted unavailable sink without blocking the guest loop or carrying stale PCM forward. | closed |
| T-05-12 | Repudiation | Playback receipt | medium | mitigate | Bind revision, build, model, authored workload, PCM digest, sample count, ring bounds, and explicitly labeled application counters in a reproducible receipt. | closed |
| T-05-13 | Tampering | Fixture rights | high | mitigate | Use authored/licensed fixture bytes with recorded source, license, and digest; verify package and measurement inputs. | closed |
| T-05-SC | Tampering | Package installs | low | accept | No new package is introduced for the audio model or player path; existing pinned SDL3 is reused. The phase's seven plans explicitly accept this bounded dependency-scope risk. | closed (accepted) |

**Status note:** `threats_open` counts open threats at or above `workflow.security_block_on` (high). The security auditor found 13 mitigated threats closed. The repeated low-severity `T-05-SC` plan entries are consolidated here and documented as an accepted risk; no blocking threat remains.

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| GB-05-AR-01 | T-05-SC | This phase adds no package dependency. The SDL3 adapter uses the project's existing pinned SDL3 package; DSP and transport logic are implemented directly in the project. | Phase 5 plan | 2026-10-08 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-08 | 14 unique IDs (20 plan-register rows) | 14 | 0 at/above high threshold | gsd-security-auditor and orchestrator |

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-08. Physical device hotplug, analog DMG output, and perceptual audio remain outside this software security verification.

## Security Audit 2026-10-09

| Metric | Count |
|---|---|
| Threats found | 14 |
| Closed | 14 |
| Open | 0 |
