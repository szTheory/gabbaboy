---
phase: "GB-05"
slug: "dmg-audio-and-stable-playback"
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| **Quick run command** | `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_|audio_)'` |
| **Full suite command** | `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error && mkdir -p /private/tmp/gabbaboy-validation-home && env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home SDL_AUDIO_DRIVER=dummy bash tests/scripts/verify-phase3-player.sh && env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home bash tests/scripts/measure-audio-playback.sh` |
| **Measured runtime** | At `206e107`: core build + 174 CTests completed in 2.19 s; player verifier CTest completed in 1.01 s (50 tests). Player commands need an isolated writable `HOME`/`CFFIXED_USER_HOME` in this sandbox. |

---

## Sampling Rate

- **After every task commit:** Run that task's exact `<automated>` command. Named cases become available only in their owning task.
- **After every plan wave:** Run the new named cases plus existing impacted core/player inventory; run the full core/player scripts at Wave 7.
- **Before `$gsd-verify-work`:** Full suite and exact revision package/fixture evidence must be assessed; no skipped check becomes a pass.
- **Feedback latency:** Core focused cases target under 60 seconds; optional SDL package verification is a separately timed integration gate.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | Coverage files / cases | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | AUDIO-01/02/03 | T-05-01/02 | Whole-instruction preflight, callback isolation | tracer + player smoke | Full core CTest; `bash tests/scripts/verify-phase3-player.sh` | `audio_tracer`, `audio_capacity`, `player_smoke`, authored pulse SDL smoke | ✅ green |
| 05-01-02 | 01 | 1 | AUDIO-01/02 | T-05-01 | Sentinel/capacity guard | core CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^audio_(tracer|capacity)$'` | `tests/test_audio.c`; `audio_tracer`, `audio_capacity` | ✅ green |
| 05-02-01 | 02 | 2 | AUDIO-01 | T-05-03 | Bounded pulse/register handling | model CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_(pulse|mixer)|audio_tracer)$'` | `apu_pulse`, `apu_mixer`, `apu_sweep`, `apu_envelope`, `audio_tracer` | ✅ green |
| 05-02-02 | 02 | 2 | AUDIO-01 | T-05-03 | Edge/timeline bounded | model CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_(sequencer|timeline)|timer_|halt_|stop_)'` | `apu_sequencer`, `apu_timeline`, timer/HALT/STOP regressions | ✅ green |
| 05-03-01 | 03 | 3 | AUDIO-01 | T-05-04 | Fixed wave RAM and indices | model CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^apu_wave$'` | `apu_wave`: register, active alias, high/low nibble pattern comparisons | ✅ green |
| 05-03-02 | 03 | 3 | AUDIO-01 | T-05-04 | Bounded noise period/LFSR | model CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(apu_noise|apu_power)$'` | `apu_noise`: repeatable 7/15-bit output distinction; `apu_power` matrix | ✅ green |
| 05-04-01 | 04 | 4 | AUDIO-01/02 | T-05-06 | Predeclared signal limits; checked DSP arithmetic | authored signal vectors and exact partition PCM | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^audio_(signal|fractional_edges|partition|filter|rounding|saturation)$'` | `audio_signal`, `audio_fractional_edges`, `audio_partition`, `audio_filter`, `audio_rounding`, `audio_saturation`; `docs/audio-and-playback.md` | ✅ green |
| 05-04-02 | 04 | 4 | AUDIO-02 | T-05-05 | Caller buffer guard | API CTest | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(audio_|run_output_capacity$|independent_instances$)'` | `audio_capacity`, `audio_api_edges`, `audio_no_alloc`, existing output/instance cases | ✅ green |
| 05-05-01 | 05 | 5 | AUDIO-02/03 | T-05-07/08 | Request-bounded fixed-chunk callback, SPSC wrap/quiescence | player adapter integration | `bash tests/scripts/verify-phase3-player.sh` | `player_audio_ring`, `player_audio_concurrent`, `player_audio_counter_saturation` (including partial bytes, int boundary, wrap, 100k ordered frames, saturating counters) | ✅ green |
| 05-05-02 | 05 | 5 | AUDIO-03 | T-05-07 | No-device sink bounded | SDL adapter + player verifier | `bash tests/scripts/verify-phase3-player.sh` | `player_audio_pacing`, `player_audio_gain`, `player_audio_unavailable`, `player_smoke` | ✅ green |
| 05-06-01 | 06 | 6 | HOST-01 | T-05-09 | Per-source release | player input integration | `bash tests/scripts/verify-phase3-player.sh` | `player_input_sources`, focus release and controller event wiring in `src/player/main.c` | ✅ green |
| 05-06-02 | 06 | 6 | HOST-01 | T-05-09 | Per-source release | player input CTest | `bash tests/scripts/verify-phase3-player.sh` | `player_input_sources`, `player_input_reconnect`, `player_input_focus_audio` | ✅ green |
| 05-06-03 | 06 | 6 | HOST-02 | T-05-10/11 | Commit before host clear and callback quiescence | injected events + pinned-SDL3 dummy smoke | `bash tests/scripts/verify-phase3-player.sh` | `player_audio_lifecycle`, `player_audio_device`, `player_audio_replacement`; dummy open/stream/close/recovery | ✅ green |
| VERIFY-05-HOST-02-RESET | Execution follow-up | Final | HOST-02 | T-05-10 | Save before reset; preserve active session on failed save/cancel | Deterministic app event-loop test | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_reset_transition.c`; `player_reset_transition` drives Space pause/resume and R reset through the SDL event loop, verifies APU continuation/host PCM clearing, save failure/cancel/retry, input/audio reset, and persisted battery recovery | ✅ green |
| 05-07-01 | 07 | 7 | AUDIO-03 | T-05-12/13 | Bounded receipt and fixture rights | sustained dummy-driver measurement | `bash tests/scripts/verify-phase3-player.sh && bash tests/scripts/measure-audio-playback.sh` | `tests/scripts/measure-audio-playback.sh`; MIT fixture digest/manifest; revision-linked JSON receipt | ✅ green |
| 05-07-02 | 07 | 7 | AUDIO-01/02/03, HOST-01/02 | T-05-12/13 | Consumer truthfulness | full inventory + package/script | Full CTest, player verifier, sustained measurement | `docs/audio-and-playback.md`, `docs/preview.md`, README/help assertions, package metadata assertions | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

**Complete.** Existing CTest and player infrastructure cover the phase's software requirements. The seven plans add named cases and fixed-inventory entries; the final core inventory and player verifier both pass at the current source revision. No dependency installation was needed.

## Executed Evidence at Current HEAD

Source revision under test: `206e107210e750ff0fe647a19b82600b17e98ee3`. The measurement receipt identified the relevant source tree as clean at that revision. Unrelated pre-existing planning scratch remains outside the Phase 5 commit scope.

| Evidence | Command / observation | Result |
|---|---|---|
| Complete core inventory | `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error` | **174/174 passed**, 2.44 s total CTest time. The core player option is off because this host's system SDL differs from the pinned SDL 3.4.18 used by the dedicated player verifier. |
| Complete player verifier | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home SDL_AUDIO_DRIVER=dummy bash tests/scripts/verify-phase3-player.sh` | **50/50 passed**, including `player_reset_transition` for Space pause/resume and R reset, counter saturation, SDL dummy open/stream/close/recovery, ring/pacing, input-source, package and smoke checks. Candidate package SHA-256: `a2a67310ff987199524d9c537ae0b671198eb2a05ae999f1f1d8e0ea0ac17826`; pinned SDL license SHA-256: `1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd`. |
| Sustained playback receipt | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home bash tests/scripts/measure-audio-playback.sh` | **Passed** for frame-sized and 792-half-dot partitions. Both produced exactly 241,094 signed-16 stereo PCM frames for the 300-frame target with identical PCM SHA-256 `8667279ae7d3bf3cdd76a278b13d2cdfe9992d64325c15e4eef9449778eaeec4`. Both recorded 42,134,424 elapsed half-dots against a 42,134,400 target; the bounded whole-instruction tail is excluded from PCM. Receipt: `build/phase3-player/audio-measurement/206e107210e7-so9lvm0q/receipt.json`. Dummy SDL opened, streamed, closed and recovered. |

The latest receipt records 1,024 application PCM underflow frames and 2,502 intentionally discarded host frames for each partition; producer backpressure events differ (3,772 / 3,793) under host scheduling. These are software counters, not claims of hardware starvation or audible dropout. No default physical audio device was available; the SDL dummy backend is the evidence boundary. Exact in-window PCM count and digest match across partitions.

---

## Manual-Only Verifications

These are deliberately excluded from the software Nyquist gate; they are not unmet automated software requirements.

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Physical DMG-CPU-B analog output/revision qualification | AUDIO-01 | No identified unit, probe chain or board measurement is in phase scope | No physical hardware result is claimed. If later requested, record board/revision, capture chain and comparison limits. |
| Perceived audio quality and real-device end-to-end latency | AUDIO-03 | Software callback and SDL queued-byte counters cannot prove hearing or hardware playout time | No listening-quality or latency result is claimed. A specific listener/device observation would be a separate acceptance activity. |
| Physical controller enumeration and audio-device hotplug | HOST-01/HOST-02 | CI exercised injected controller/device events and pinned-SDL3 dummy lifecycle, not real peripherals | No physical device result is claimed; software event and transition paths are covered by automated tests. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Focused core feedback stays under 60 seconds; player integration duration is recorded separately
- [x] `nyquist_compliant: true` set in frontmatter

**Validation result:** the software requirements listed in this phase's task map are covered by named automated cases and passed the current full core/player/measurement commands above. This validates the test map; it does **not** mark Phase 5 execution complete or replace `$gsd-verify-work 5`. Physical hardware, perceptual quality and real-device latency remain explicitly unclaimed.

## Spec-less Edge Assumptions (11 reviewed)

The phase has no standalone SPEC. Each fallback probe below was reconciled against source and an automated behavioral test or explicitly bounded as a caller/hardware contract. Count: applicable 11, ten behavioral probes have named automated cases, one probe records the single-caller-per-core API contract, unresolved software gaps 0. The two originally unclassified probes are resolved by the automated receipt/evidence-boundary and input-source matrix checks.

| Requirement | Probe category | Observed evidence / disposition |
|---|---|---|
| AUDIO-01 | adjacency | `apu_timeline`, timer/DIV, HALT and STOP cases exercise equal-time and before/after sequencing. The test verifies the declared modeled ordering; exact silicon coincidence behavior outside this model is not claimed. |
| AUDIO-01 | empty | `audio_api_edges` checks no-ROM, zero-budget and invalid calls without output mutation; `audio_capacity` checks capacity failure behavior. |
| AUDIO-01 | ordering | `apu_timeline`, `apu_sequencer`, and timer interaction tests check deterministic modeled event order. |
| AUDIO-01 | idempotency | `apu_power` and reset/lifecycle cases check channel power and reset transitions. |
| AUDIO-01 | concurrency | `independent_instances` proves independent-instance isolation; player ring/concurrent cases prove the callback SPSC contract. Concurrent calls on one core instance remain excluded by the public single-caller contract. |
| AUDIO-02 | boundary | `audio_api_edges` and `audio_capacity` cover null, zero, short/exact capacities, overflow-sized requests, guards and no mutation on failure. There is no separate finite public maximum beyond representable/requested capacity. |
| AUDIO-02 | precision | `audio_rounding`, `audio_saturation`, `audio_filter`, and exact partition PCM cases check signed Q15 tie rounding, clamping, filter and deterministic sample output. `player_audio_counter_saturation` seeds private counters near `UINT_FAST64_MAX` in a test-only white-box harness and exercises the production submit/callback/clear paths; production counter saturation is behaviorally checked without attempting an infeasible natural runtime. |
| AUDIO-03 | originally unclassified | Reviewed through the named `audio_*` software tests, `player_audio_*` cases, and sustained receipt. The receipt labels software underflow/discard/queue metrics and states the dummy-device evidence boundary. It makes no hardware or listening claim. |
| HOST-01 | originally unclassified | `player_input_sources`, reconnect and focus-audio cases exercise per-source key ownership, release and recovery for injected focus/controller events. Physical controller enumeration is excluded. |
| HOST-02 | boundary | `player_audio_pacing`, lifecycle, device and replacement tests exercise full-ring clearing, pause/removal/addition, commit ordering, stale queued frames and recovery through injected events/dummy SDL. |
| HOST-02 | precision | Player ring tests check partial bytes and bounded frame accounting; the receipt checks exact deterministic counters and partition agreement. `tests/player/test_input.c` exercises timestamp conversion overflow and boundary behavior against `src/player/input.c`; `player_audio_counter_saturation` checks the audio counters through production paths. Real-device timestamp/latency arithmetic is not claimed. |

## Fallback value prohibitions

Verified by the fixed fixture manifest/digest tests and package assertions: only the authored MIT demo fixture is used for the sustained workload. The receipt and playback documentation identify the DMG scoped software model and state that dummy SDL/software queue results do not establish hardware output, latency or perceptual quality.

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
| RESEARCH | Resolved resampler criteria: independent authored references, predeclared numeric limits, exact count/partition PCM; no perceptual/hardware claim | 04-01 | COVERED by authored signal/filter/partition cases and identical sustained partition digests. No standalone wall-clock throughput claim is made. |
| RESEARCH | Resolved callback sizing: current positive int byte bound, fixed chunks, partial-frame/empty/over-ring/arithmetic cases, quiescence | 05-01 | COVERED by player ring/concurrent tests and the 50/50 verifier. |
| RESEARCH | Resolved CI transition smoke: pinned SDL3 dummy backend required, open/stream/close, injected added/removed events, stale-buffer clearing | 06-03, 07-01 | COVERED by player lifecycle/device/replacement tests and passing dummy smoke; physical hardware remains unclaimed. |
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

Deferred CGB audio, VIN, board calibration, external DSP libraries, device-selection UI and physical/perceptual qualification are exclusions under 05-CONTEXT.md, not coverage gaps. The three research questions are covered by the executed signal/partition tests, player verifier and sustained measurement receipt. No physical hotplug, audible quality or hardware result is marked passing.
