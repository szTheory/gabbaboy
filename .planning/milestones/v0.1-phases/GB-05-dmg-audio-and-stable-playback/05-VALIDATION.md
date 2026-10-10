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
| 05-07-02 | 07 | 7 | AUDIO-01/02/03, HOST-01/02 | T-05-12/13 | Consumer truthfulness | full inventory + package/script | Full CTest, player verifier, sustained measurement | `docs/audio-and-playback.md`, `docs/preview.md`, README/help assertions, package metadata assertions; since PR #43/GB-06 the verified package and receipt are published by `tests/scripts/verified_player_output_dir.py`, checked by `player_verified_output_directory` | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

**Complete.** Existing CTest and player infrastructure cover the phase's software requirements. The seven plans add named cases and fixed-inventory entries; the final core inventory and player verifier both pass at the current source revision. No dependency installation was needed.

## Historical Executed Evidence at Implementation HEAD

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

**Historical validation result:** the software requirements listed in this phase's task map were covered by named automated cases at implementation HEAD `206e107210e750ff0fe647a19b82600b17e98ee3`. This is historical evidence; the refreshed evidence below is the current local result. Physical hardware, perceptual quality and real-device latency remain explicitly unclaimed.

## Refreshed Executed Evidence at Integrated HEAD (2026-10-09)

Source revision: `4d52df7aa0594bad2a3b0f0dc91e92e5612a2f4c`. The source tree was dirty during these runs; the sustained receipt records `source_tree_state: dirty`. These are current local results for the integrated worktree, not clean-checkout or hosted CI evidence.

| Evidence | Command / observation | Result |
|---|---|---|
| Complete core inventory | `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error` | **179/179 passed.** |
| Complete player/package verifier | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home SDL_AUDIO_DRIVER=dummy bash tests/scripts/verify-phase3-player.sh` | **50/50 passed**, including the new built-help assertions that distinguish S background-save retry from R/C/Escape blocked-transition recovery. The packaged smoke also checks SDL Z press/hold/release rendering, dummy audio lifecycle/recovery, reset transition behavior, and MBC1 continuation. Candidate package SHA-256: `adb4ba71d023ba20a06b6a2160e39ec07095588d8d176965e325e09caede11c8`. |
| Sustained playback receipt | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home bash tests/scripts/measure-audio-playback.sh` | **Passed** for frame-sized and 792-half-dot partitions. Each produced 241,094 stereo frames with matching PCM SHA-256 `8667279ae7d3bf3cdd76a278b13d2cdfe9992d64325c15e4eef9449778eaeec4`; each recorded 42,134,424 elapsed half-dots against 42,134,400 requested. Receipt: `build/phase3-player/audio-measurement/4d52df7aa059-w8jl5pmr/receipt.json`. |

The receipt identifies Release mode, macOS arm64, the scoped DMG-CPU-B software model, the authored MIT-licensed visible-demo workload, SDL dummy backend, and no available default audio device. Both partitions reported 1,024 application underflow frames, 2,502 intentionally discarded host frames, zero stream-write failures, and zero SDL queued-input bytes; producer backpressure was 3,203/3,211 events. These are software measurements, not physical starvation, latency, hotplug, or perceptual claims. The source tree was dirty, so these results do not establish an exact clean revision or remote CI status.

The focused incremental code review covered `src/player/main.c`, `docs/preview.md`, and `tests/scripts/verify-phase3-player.sh`; it reported zero findings. It confirmed that S handles manual/background-save retry while R/C/Escape handle a blocked final transition.

## Refreshed Executed Evidence at Clean HEAD (2026-10-10)

Source revision: `cb4a96ce3f5bd3f8fe66211e62b650a822e2423a` on `gsd/phase-05-verification-refresh`; the sustained receipt records `source_tree_state: clean` (only planning state files were modified, outside the measured source tree). These are local results, not hosted CI evidence.

**Changed covered files since the 05-VERIFICATION.md baseline (`7b1c491`) and their disposition:**

| File | Change | Phase 5 requirement impact | Automated coverage |
|---|---|---|---|
| `src/player/session.c` | ROM open adds `O_NONBLOCK` so a FIFO/special file cannot block before the `fstat` regular-file guard | HOST-02 session-transition safety: rejected replacement must leave the active session unchanged. No audio, input or device-transition path changed; `O_NONBLOCK` has no effect on regular-file reads. | `player_session` now creates a FIFO at the replacement path, requires the "bounded regular file" error, verifies the machine/session is unchanged and the FIFO is untouched. `player_reset_transition`, `player_audio_lifecycle/device/replacement` still pass. |
| `tests/scripts/verified_player_output_dir.py` (new) | Shared helper that publishes the verified package and receipt as one set outside the checkout | Consumer/package evidence for 05-07-02 only; no runtime behavior | `player_verified_output_directory` (runs `tests/scripts/test_verified_player_output_dir.py`) plus the end-to-end verifier publish step. |
| `tests/scripts/verify-phase3-player.sh` | Uses the helper; also binds the candidate `package_sha256` from the build receipt | Verifier still builds every Phase 5 player case from the fixed inventory and runs the dummy audio smoke | 51-entry fixed inventory (50 prior + `player_verified_output_directory`), all passing. |

| Evidence | Command / observation | Result |
|---|---|---|
| Complete core inventory | `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error` | **179/179 passed** (2.27 s), including every `apu_*` and `audio_*` case named in the task map. |
| Complete player/package verifier | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home SDL_AUDIO_DRIVER=dummy bash tests/scripts/verify-phase3-player.sh` | **51/51 passed**, exit 0. Includes all `player_audio_*`, `player_input_*`, `player_reset_transition`, `player_session`, `player_smoke` and `player_verified_output_directory`. Candidate package SHA-256: `08562bfa223ec3786784c0cd434f6ff872d16d3f34e6436ebdf5331087b5ca77` (pinned SDL 3.4.18). |
| Sustained playback receipt | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home bash tests/scripts/measure-audio-playback.sh` | **Passed** for frame-sized and 792-half-dot partitions: 241,094 stereo frames each, identical PCM SHA-256 `8667279ae7d3bf3cdd76a278b13d2cdfe9992d64325c15e4eef9449778eaeec4` (unchanged from both prior runs), 42,134,424 elapsed half-dots against 42,134,400 requested. Receipt: `build/phase3-player/audio-measurement/cb4a96ce3f5b-3wh_0kwx/receipt.json`. |

The receipt reports Release mode, macOS arm64, DMG-CPU-B scoped software model, MIT authored workload (fixture SHA-256 `38afb54b40f4b6612906c7a68e367199d8bff135508a39d7acdc996bf3d86530`), SDL dummy driver, dummy open/stream/close/recovery passed, 1,024 application underflow frames and 2,502 intentionally discarded host frames per partition, zero stream-write failures, zero SDL queued-input bytes, producer backpressure 3,822/3,807 (host-scheduling dependent). This host now reported a default audio device as available, but the measurement still used the dummy driver; no physical playout, latency or perceptual claim is made.

**Gap result:** AUDIO-01, AUDIO-02, AUDIO-03, HOST-01 and HOST-02 remain COVERED by passing named automated cases. Gaps found 0; no tests added in this refresh.

## Refreshed Executed Evidence after Phase 06.1 (2026-10-10)

Source revision: `ac3cb6e1d2505508e289decfed9d293a163a56ba` on `gsd/phase-06.1-verification-refresh`, which descends from the PR 54 merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb` with only `.planning/` changes after it. The sustained receipt records `source_tree_state: clean`. These are local results; hosted evidence for the same source content is ci run 38064419789 and preview run 38064419803 (PR head) and ci run 38064726000 (merge SHA).

**Changed covered files since the 05-VERIFICATION.md baseline (`f39faac`), all from PR 54:**

| File | Change | Phase 5 requirement impact | Automated coverage |
|---|---|---|---|
| `src/player/session.c` | `read_rom_file` adds `O_NOCTTY`; the 2 MiB size-bound error and the close-failure error become separate branches | HOST-02 session-transition safety only. No audio, input or device-transition path changed. | `player_session` (`player_session_replacement_failure` asserts the 2097153-byte size-bound message and the unchanged session). The close-failure branch is inspection-only: no fault-injection stage exists for ROM close. |
| `tests/player/test_session.c` | Adds the size-bound message assertion | Test-only | Part of the 51/51 player inventory below. |
| `tests/scripts/test_verified_player_output_dir.py` | Shared `_receipt_fields()` helper and an inner-withdrawal-site test | Test-only, package publication evidence for 05-07-02 | 21 tests OK; also `player_verified_output_directory`. |
| `tests/scripts/verify-phase3-player.sh` | Comment documenting the local-only `GBB_VERIFIED_OUTPUT_DIR` default (P5 IN-01, `ecb0db7`) | None; behaviour unchanged | Verifier exit 0 below. |
| `.github/workflows/preview.yml` | Exact-head CI lookup through `wait-exact-head-ci.py`; aggregate requires player success unconditionally | CI wiring only; the preview lanes still run the player verifier and package smoke | preview run 38064419803 success. |

| Evidence | Command / observation | Result |
|---|---|---|
| Complete core inventory | `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 4 && ctest --preset phase1 --output-on-failure --no-tests=error` | **184/184 passed** (3.78 s), including every `apu_*` and `audio_*` case named in the task map. |
| Complete player/package verifier | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home SDL_AUDIO_DRIVER=dummy bash tests/scripts/verify-phase3-player.sh` | **51/51 passed**, exit 0, `source_revision=ac3cb6e1...`. Candidate package SHA-256 `7899404c9be81ad2ff5618e8c4ceda984bb5e29c88c28160eea619e076fb6134`; pinned SDL license SHA-256 `1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd`. |
| Verified-output helper | `python3 tests/scripts/test_verified_player_output_dir.py` | **21 tests OK.** |
| Sustained playback receipt | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home bash tests/scripts/measure-audio-playback.sh` | **Passed** for frame-sized and 792-half-dot partitions: `sample_count` 241,094 each, identical PCM SHA-256 `8667279ae7d3bf3cdd76a278b13d2cdfe9992d64325c15e4eef9449778eaeec4` (unchanged from every prior run), 42,134,424 elapsed half-dots against 42,134,400 requested. Release, macos-arm64, dummy driver, open/stream/close/recovery passed; 1,024 underflow frames and 2,502 discarded host frames per partition, zero stream-write failures, zero queued input bytes, backpressure 3,701/3,742. |

The host reported a default audio device as available, but the measurement used the dummy driver; no physical playout, latency or perceptual claim is made.

**Gap result:** AUDIO-01, AUDIO-02, AUDIO-03, HOST-01 and HOST-02 remain COVERED. Gaps found 0; no tests added in this refresh.

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

## Validation Audit 2026-10-09

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
