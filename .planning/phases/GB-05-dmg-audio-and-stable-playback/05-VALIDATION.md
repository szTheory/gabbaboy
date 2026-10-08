---
phase: "GB-05"
slug: "dmg-audio-and-stable-playback"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-08"
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Existing CMake/CTest C17 targets and optional SDL3 player verifier |
| **Config file** | `CMakeLists.txt`, `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt`, and their fixed inventories |
| **Quick run command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_|audio_)'` after the named cases exist |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && bash tests/scripts/verify-phase3-player.sh && bash tests/scripts/measure-audio-playback.sh` after Plan 05-07 creates the final script |
| **Estimated runtime** | Measure during execution; player package verifier can exceed one minute and has separate result receipts |

---

## Sampling Rate

- **After every task commit:** Run that task's exact `<automated>` command. Named cases become available only in their owning task.
- **After every plan wave:** Run the new named cases plus existing impacted core/player inventory; run the full core/player scripts at Wave 7.
- **Before `$gsd-verify-work`:** Full suite and exact revision package/fixture evidence must be assessed; no skipped check becomes a pass.
- **Feedback latency:** Core focused cases target under 60 seconds; optional SDL package verification is a separately timed integration gate.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | AUDIO-01/02/03 | T-05-01/02 | Whole-instruction preflight, callback isolation | tracer + player smoke | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(instance_lifecycle$\|run_output_capacity$)' && bash tests/scripts/verify-phase3-player.sh` | existing script; extended smoke in task | ⬜ pending |
| 05-01-02 | 01 | 1 | AUDIO-01/02 | T-05-01 | Sentinel/capacity guard | core CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^audio_(tracer\|capacity)$'` | ❌ task creates cases | ⬜ pending |
| 05-02-01 | 02 | 2 | AUDIO-01 | T-05-03 | Bounded pulse/register handling | model CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_(pulse\|mixer)\|audio_tracer)$'` | ❌ task creates cases | ⬜ pending |
| 05-02-02 | 02 | 2 | AUDIO-01 | T-05-03 | Edge/timeline bounded | model CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_(sequencer\|timeline)\|timer_\|halt_\|stop_)'` | ❌ task creates cases | ⬜ pending |
| 05-03-01 | 03 | 3 | AUDIO-01 | T-05-04 | Fixed wave RAM and indices | model CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^apu_wave$'` | ❌ task creates case | ⬜ pending |
| 05-03-02 | 03 | 3 | AUDIO-01 | T-05-04 | Bounded noise period/LFSR | model CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_noise\|apu_power)$'` | ❌ task creates cases | ⬜ pending |
| 05-04-01 | 04 | 4 | AUDIO-01/02 | T-05-06 | Checked DSP arithmetic | independent analytical signal CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^audio_(signal\|partition\|filter)$'` | ❌ task creates cases | ⬜ pending |
| 05-04-02 | 04 | 4 | AUDIO-02 | T-05-05 | Caller buffer guard | API CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(audio_\|run_output_capacity$)'` | ❌ task creates edge case | ⬜ pending |
| 05-05-01 | 05 | 5 | AUDIO-02/03 | T-05-07/08 | SPSC wrap/quiescence | concurrent adapter + player verifier | `bash tests/scripts/verify-phase3-player.sh` | ❌ task creates cases | ⬜ pending |
| 05-05-02 | 05 | 5 | AUDIO-03 | T-05-07 | No-device sink bounded | SDL adapter + player verifier | `bash tests/scripts/verify-phase3-player.sh` | ❌ task creates cases | ⬜ pending |
| 05-06-01 | 06 | 6 | HOST-01 | T-05-09 | Per-source release | existing player input smoke | `bash tests/scripts/verify-phase3-player.sh` | ✅ existing verifier | ⬜ pending |
| 05-06-02 | 06 | 6 | HOST-01 | T-05-09 | Per-source release | player input CTest | `bash tests/scripts/verify-phase3-player.sh` | ❌ task creates cases | ⬜ pending |
| 05-06-03 | 06 | 6 | HOST-02 | T-05-10/11 | Commit before host clear | lifecycle/player CTest | `bash tests/scripts/verify-phase3-player.sh` | ❌ task creates cases | ⬜ pending |
| 05-07-01 | 07 | 7 | AUDIO-03 | T-05-12/13 | Bounded receipt and fixture rights | sustained script | `bash tests/scripts/verify-phase3-player.sh && bash tests/scripts/measure-audio-playback.sh` | ❌ task creates script | ⬜ pending |
| 05-07-02 | 07 | 7 | AUDIO-01/02/03, HOST-01/02 | T-05-12/13 | Consumer truthfulness | full inventory + package/script | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && bash tests/scripts/verify-phase3-player.sh && bash tests/scripts/measure-audio-playback.sh` | scripts exist after 05-07-01 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing CTest and player infrastructure cover all requirements. Each plan adds its named cases and fixed-inventory entries before its verify command runs. No Wave 0 package install is needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Physical DMG-CPU-B analog output/revision qualification | AUDIO-01 | No identified unit, probe chain or board measurement is in phase scope | Leave unclaimed; if later requested, record board/revision, capture chain and comparison limits. |
| Perceived audio quality and real-device end-to-end latency | AUDIO-03 | A software callback/SDL queued-byte count cannot prove hearing or hardware playout time | Leave unclaimed; identified listener/device observation may be added separately. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Focused core feedback stays under 60 seconds; record measured player integration duration separately
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution evidence; this planning document is not a pass claim.

## Spec-less edge assumptions (11 unresolved, including 2 unclassified)

The phase has no standalone SPEC. Every fallback edge probe is retained below as a flagged assumption for the executor/verifier to resolve with source-backed cases; none is silently treated as verified. Count: applicable 11, resolved 0, unresolved 11, unclassified 2.

| Requirement | Probe category | Flagged assumption / resolution path |
|---|---|---|
| AUDIO-01 | adjacency | Simultaneous DIV/channel events use a deterministic documented ordering; test before/at/after boundaries in 05-02-02. |
| AUDIO-01 | empty | Zero-budget/no-ROM/null calls follow existing core error and non-mutation policy; test in 05-02-02/05-04-02. |
| AUDIO-01 | ordering | Equal-time bus/APU transitions preserve declared operation order; test in 05-02-02. |
| AUDIO-01 | idempotency | Repeated reset or power writes produce same declared state; test in 05-02-02/05-03-02. |
| AUDIO-01 | concurrency | One caller at a time per core instance remains required; test two independent instances in 05-04-02 and audit callback isolation in 05-05-01. |
| AUDIO-02 | boundary | Zero, one-short, exact, maximum and one-beyond frame capacities need explicit public precedence; test in 05-01-02/05-04-02. |
| AUDIO-02 | precision | Fixed-point ties, saturation, count overflow and coefficient rounding need exact documented rules; test in 05-04-01/02. |
| AUDIO-03 | unclassified | Probe provides no behavior description; manually review playback receipt/callback/device scope in 05-07-01 before marking complete. |
| HOST-01 | unclassified | Probe provides no behavior description; manually review focus/controller source matrix in 05-06-01 before marking complete. |
| HOST-02 | boundary | Pause/device/ROM transitions at empty/full ring and commit boundary need matrix cases in 05-06-03. |
| HOST-02 | precision | Host-discard/underflow counters and transition timestamp arithmetic need overflow/rounding rules in 05-06-03/05-07-01. |

## Fallback value prohibitions

Flagged-unverified: no unlicensed ROM/audio fixture enters the repository; 05-07-01 checks authored bytes, rights and digest. Flagged-unverified: software signal or queue results are never presented as physical DMG or perceptual qualification; 05-07-02 checks evidence labels. These are owner-value/safety constraints, not routine implementation checks.

## Multi-source coverage audit

| Source | ID / concern | Plan(s) | Status |
|---|---|---|---|
| GOAL | Paced sound and responsive controls through device transitions | 01, 05, 06, 07 | COVERED |
| REQ | AUDIO-01 four scoped DMG channels | 01, 02, 03, 04, 07 | COVERED |
| REQ | AUDIO-02 bounded deterministic PCM | 01, 04, 05, 07 | COVERED |
| REQ | AUDIO-03 SDL playback, gain, pacing and queue evidence | 01, 05, 07 | COVERED |
| REQ | HOST-01 focus/controller source recovery | 06, 07 | COVERED |
| REQ | HOST-02 session/device transition recovery | 06, 07 | COVERED |
| RESEARCH | Core/adapter responsibility boundary, divider timeline and no extra package | 01–05 | COVERED |
| RESEARCH | Original kernel/high-pass and analytical quality floor | 04 | COVERED |
| RESEARCH | Callback request bound, SPSC lock-free/wrap/quiescence | 05 | COVERED |
| RESEARCH | SDL device-open availability and default-device recovery assumption | 05, 06, 07 | COVERED with environment availability flagged |
| RESEARCH | Evidence classes, fixture rights, metric labels and sustained receipt | 01–07 | COVERED |
| CONTEXT | D-01 four channels/registers/DIV sequencer | 01, 02, 03, 07 | COVERED |
| CONTEXT | D-02 fixed-point approximate DMG high-pass | 04, 07 | COVERED |
| CONTEXT | D-03 48 kHz signed-16 interleaved stereo/caller storage | 01, 04, 07 | COVERED |
| CONTEXT | D-04 original bounded band-limited edge resampler | 04 | COVERED |
| CONTEXT | D-05 atomic audio-aware output-full/mute | 01, 04 | COVERED |
| CONTEXT | D-06 SDL callback and C17 SPSC | 01, 05 | COVERED |
| CONTEXT | D-07 tuning bounds/queue interpretations | 05, 07 | COVERED |
| CONTEXT | D-08 gain/help/unavailable sink | 05, 07 | COVERED |
| CONTEXT | D-09 source-owned input/focus | 06, 07 | COVERED |
| CONTEXT | D-10 battery/PCM/session/device transition order | 06, 07 | COVERED |
| CONTEXT | D-11 separated evidence and legal fixtures | 01–07 | COVERED |
| CONTEXT | D-12 exact sustained metrics and limits | 05, 07 | COVERED |

Deferred CGB audio, VIN, board calibration, external DSP libraries, device-selection UI and physical/perceptual qualification are exclusions under 05-CONTEXT.md, not coverage gaps. The three research open questions remain execution-time measurements/assumptions, with explicit tasks above; none is silently accepted as an empirical result.
