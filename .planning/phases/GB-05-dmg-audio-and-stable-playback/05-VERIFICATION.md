---
phase: GB-05-dmg-audio-and-stable-playback
verified: 2026-10-09T19:26:49Z
status: passed
score: 17/17 truths verified
covered_files:
  - .github/workflows/preview.yml
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-01-PLAN.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-01-SUMMARY.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-02-PLAN.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-02-SUMMARY.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-03-PLAN.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-03-SUMMARY.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-04-PLAN.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-04-SUMMARY.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-05-PLAN.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-05-SUMMARY.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-06-PLAN.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-06-SUMMARY.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-07-PLAN.md
  - .planning/phases/GB-05-dmg-audio-and-stable-playback/05-07-SUMMARY.md
  - CMakeLists.txt
  - README.md
  - docs/audio-and-playback.md
  - docs/preview.md
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - src/player/audio.c
  - src/player/audio.h
  - src/player/input.c
  - src/player/input.h
  - src/player/limitations.h
  - src/player/main.c
  - tests/CMakeLists.txt
  - tests/expected-tests.txt
  - tests/player/CMakeLists.txt
  - tests/player/expected-tests.txt
  - tests/player/test_audio.c
  - tests/player/test_input.c
  - tests/player/test_limitations.c
  - tests/player/test_reset_transition.c
  - tests/scripts/measure-audio-playback.sh
  - tests/scripts/verify-phase3-player.sh
  - tests/test_apu.c
  - tests/test_audio.c
covered_digest: "v3:sha256:1f0ea1e926506fbb3ef86ac6091ba3a05eaf47b3f4039066f746640cb817570d"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 22/22 (prior report table contained 17 distinct truths)
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 5: DMG Audio and Stable Playback Verification Report

**Phase Goal:** As a player, I want to play DMG games with paced sound, so that controls remain responsive through device changes.  
**Verified:** 2026-10-09T19:26:49Z
**Status:** passed  
**Re-verification:** No — the prior report had no `gaps` section, so this follows the workflow's initial-mode truth derivation while refreshing stale evidence.

## User Flow Coverage

User story: “As a player, I want to play DMG games with paced sound, so that controls remain responsive through device changes.”

| Step | Expected | Evidence | Status |
|------|----------|----------|--------|
| Start a DMG session | The packaged macOS player loads the project-owned demo and runs its guest loop. | Current-revision player package verifier, 50/50 checks; its SDL dummy smoke opens, streams, closes, and recovers. | ✓ Software path verified |
| Play with sound | Guest APU output reaches the bounded PCM API and SDL stream while host pacing remains outside the guest clock. | Core audio tests, player ring/pacing/gain tests, and the current-revision 300-frame measurement receipt below. | ✓ Software signal and dummy-stream path verified; no listening claim |
| Use controls through host changes | Keyboard/controller source ownership releases held buttons on focus loss/removal and starts a reconnected controller neutral. | Named player input source, focus, and reconnect tests; app event handlers route SDL events into those paths. | ✓ VERIFIED |
| Recover the current session | Pause, reset, replacement, and audio-device changes clear or preserve state according to the documented transition contract. | `player_reset_transition` drives Space pause/resume and R reset through the app event loop, plus device/replacement tests. It checks PCM flush bytes and APU continuation against an uninterrupted guest. | ✓ Software transition behavior verified |
| Reach the outcome | Sound is paced and controls remain responsive through the software event/device transition paths. | Deterministic core/player tests and receipt. Physical audio device, perceptual quality, and physical controller hotplug were not tested or claimed. | ✓ Software outcome verified; no physical/perceptual claim |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | All four scoped DMG channels, registers, and divider sequencer produce expected digital results with approximation limits documented. | ✓ VERIFIED | src/core/gabbaboy.c; tests/test_apu.c; named apu_sequencer, apu_timeline, apu_wave, apu_noise, and apu_power tests; docs/audio-and-playback.md states the software model and analog/revision limits. |
| 2 | Core PCM is deterministic and bounded, with documented format/resampling/lifetime/backpressure; stepping neither allocates nor silently loses required output. | ✓ VERIFIED | Public contract in include/gabbaboy/gabbaboy.h; preflight and per-instance DSP in src/core/gabbaboy.c; audio_capacity, audio_partition, audio_no_alloc, signal/filter/rounding/saturation tests; caller-owned output count and error behavior. |
| 3 | The macOS player provides gain and paced sound without changing guest clock semantics; sustained play records bounded queue and application underflow/backpressure evidence. | ✓ VERIFIED | src/player/audio.c ring and callback; src/player/main.c guest pacing/gain controls; player gain, pacing, concurrency, lifecycle, and device tests; exact current-revision receipt below. |
| 4 | Keyboard/basic controller input recovers across focus loss and disconnect/reconnect without leaving guest buttons stuck. | ✓ VERIFIED | Source-owned contributions and release retry in src/player/input.c; SDL wiring in src/player/main.c; named player_input_sources, player_input_focus, player_input_reconnect, and player_input_focus_audio tests. |
| 5 | Pause/resume, reset, ROM replacement, and audio-device transitions avoid stale cross-session input/video/audio/battery state. | ✓ VERIFIED | `player_reset_transition` behaviorally exercises Space pause/resume and normal R save-before-reset, failed-save preservation, cancel/retry, input/audio clearing, and persisted battery recovery; device and replacement cases pass. |
| 6 | An authored pulse-register guest emits 48 kHz PCM into the SDL playback path; output capacity failure stops before a whole instruction. | ✓ VERIFIED | Current player smoke, audio_tracer, and audio_capacity; core caller buffer flows into the ring and callback. |
| 7 | Both pulse channels obey modeled register controls and divider edges, including DIV writes, HALT, STOP, reset, and chunk boundaries. | ✓ VERIFIED | apu_pulse, apu_mixer, apu_sweep, apu_envelope, apu_sequencer, and apu_timeline; implementation clocks APU from the emulated divider timeline. |
| 8 | Wave/noise patterns and all-channel power, reset, and channel-disable mixing behave as documented. | ✓ VERIFIED | apu_wave, apu_noise, and apu_power exercise authored register programs and expected digital patterns. |
| 9 | Equivalent emulated time split into supported run partitions yields identical PCM frames/counts; resampler/filter outputs stay within declared analytical bounds. | ✓ VERIFIED | audio_partition, signal/filter/rounding/saturation tests and exact cross-partition receipt digest; limits and assumptions are documented. |
| 10 | Caller buffers are not overrun or silently shorted, and insufficient capacity leaves the next instruction unstarted. | ✓ VERIFIED | audio_capacity, audio_api_edges, and core run-output capacity regressions assert produced counts, guard bytes, and retryable state. |
| 11 | SDL callback consumes published PCM only, zero-fills shortages, and does not run guest work; gain defaults to 100% and controls are discoverable. | ✓ VERIFIED | src/player/audio.c, ring/callback/gain tests, package help/title assertions, and player smoke. |
| 12 | Queue high-water, application PCM underflow, producer backpressure, and stream-write failure have separate bounded metrics. | ✓ VERIFIED | Adapter counters and saturation tests; current receipt reports each metric separately and records zero SDL stream-write failures. |
| 13 | Focus loss and gamepad removal release only owned button contributions; reconnect starts neutral. | ✓ VERIFIED | Source-specific state and named input source/focus/reconnect behavioral tests; no physical controller claim. |
| 14 | Pause preserves guest APU history and clears host backlog; reset and successful replacement clear state only after the battery transition. | ✓ VERIFIED | `player_reset_transition` sends Space events through `pump_events()`, checks pause/input state and exact flushed PCM bytes, resumes, then compares PCM against an uninterrupted guest after equal pre-pause progress. The same test verifies save-before-reset, failed-save cancel/retry, and persisted battery recovery; replacement transition tests pass. |
| 15 | Failed ROM replacement preserves the active session; audio-device removal/reopen clears stale host PCM without changing guest-clock semantics. | ✓ VERIFIED | player_smoke covers failed/successful replacement session behavior; player_audio_device checks removal/addition recovery and stale-buffer clearing; main event dispatch is wired to the adapter and does not advance or reset the guest. |
| 16 | Sustained authored playback records revision, PCM digest/count, ring limits/high-water, software underflow/backpressure/discard, and SDL queued input bytes. | ✓ VERIFIED | Current-revision measurement script and machine-readable receipt; exact sample count and digest agree across frame and 792-half-dot partitions. |
| 17 | Consumer docs and player help/status describe format, gain, recovery, and evidence boundaries without hardware/listening overclaims. | ✓ VERIFIED | docs/audio-and-playback.md, docs/preview.md, README.md; package help/status assertions; review and security reports. |

**Score:** 17/17 distinct plan truths verified; all five roadmap success criteria map to these truths; 0 behavior-unverified.

### Roadmap Contract Coverage

| Roadmap success criterion | Plan truths verified |
|---------------------------|----------------------|
| Four scoped DMG channels, registers, and divider sequencer produce expected digital results with limits stated. | 1, 7, 8 |
| Deterministic bounded PCM has documented format/resampling/lifetime/backpressure; stepping allocates nothing and loses no required output. | 2, 9, 10 |
| The macOS player provides gain and paced sound without guest-clock changes; sustained play records queue and underflow/overrun behavior. | 3, 6, 11, 12, 16 |
| Keyboard/controller input recovers from focus loss and disconnect/reconnect without stuck guest buttons. | 4, 13 |
| Pause/resume, reset, ROM replacement, and audio-device transitions avoid stale cross-session state and follow flush/recovery rules. | 5, 14, 15 |

### Deferred Items

None. The report does not count physical DMG analog/revision qualification, perceptual listening quality, physical controller enumeration, or real-device audio hotplug as required behavior; those are explicit scope exclusions rather than deferred Phase 5 work.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| include/gabbaboy/gabbaboy.h, src/core/gabbaboy.c | Caller-owned bounded PCM API and per-instance DMG APU/DSP | ✓ VERIFIED | Substantive public contract, channel/sequencer state, capacity preflight, sample generation, and error/count behavior. |
| tests/test_apu.c | Register/timing tests for four DMG channels | ✓ VERIFIED | Authored guest programs assert channel output and modeled timing values. |
| tests/test_audio.c, tests/test_audio_no_alloc.c | PCM limits, deterministic partitions, analytical bounds, allocation contract | ✓ VERIFIED | Active CTest registrations; behavioral/value assertions cover guards, count, partition equality, signal limits, and no allocation. |
| src/player/audio.c, src/player/audio.h | Bounded SPSC transport, gain, SDL callback, lifecycle/device recovery | ✓ VERIFIED | Imported by the player and test adapter; fixed ring and callback path are live. |
| src/player/input.c, src/player/input.h | Source-owned keyboard/controller contributions and recovery | ✓ VERIFIED | Imported by player event handling; active source/focus/reconnect tests. |
| src/player/main.c | Guest-to-PCM pacing, controls, focus/device/reset/replacement event routing | ✓ VERIFIED | Main loop calls audio-aware core API and submits to ring; routes SDL events. `player_reset_transition` exercises actual Space pause/resume and normal R-reset event-loop paths. |
| tests/player/test_reset_transition.c | App-level Space pause/APU continuity and battery-safe R-reset behavior | ✓ VERIFIED | Registered as `player_reset_transition`; drives Space and R through `pump_events()`, checks exact audio flush bytes, resumed PCM against an uninterrupted guest, save failure/cancel/retry, reset cleanup, and persisted battery recovery. |
| tests/player/test_audio.c, tests/player/test_audio_counters.c, tests/player/test_input.c | Player adapter/input concurrency and transition tests | ✓ VERIFIED | Registered in the fixed player inventory; all player checks passed. |
| tests/scripts/verify-phase3-player.sh, tests/scripts/measure-audio-playback.sh | Package/device smoke and reproducible sustained receipt | ✓ VERIFIED | Both executed successfully at current HEAD; receipt binds data to revision/build/workload. |
| CMakeLists.txt, tests/CMakeLists.txt, tests/expected-tests.txt, tests/player/CMakeLists.txt, tests/player/expected-tests.txt | Build and fixed test inventories | ✓ VERIFIED | Core and player tests are registered; full inventories pass without missing tests. |
| docs/audio-and-playback.md, docs/preview.md, README.md | Consumer contract, limitations, help and evidence interpretation | ✓ VERIFIED | State format, sample rate, gain, lifetime, backpressure, queue metrics, evidence classes, model limits, and exclusions. |

The GSD artifact/key-link query helper returned total 0 for these plan declarations because artifact paths are listed as strings and each plan's key_links is a narrative sentence, rather than the helper's structured object schema. That empty helper result is not treated as a pass; the paths above and links below were manually checked against current source, tests, and docs.

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Emulated divider/APU | Core caller PCM | Per-instance APU edges and audio-aware run API | ✓ WIRED | advance_devices_to advances divider/APU/sample phase; gbb_run_audio writes bounded caller frames. |
| Core PCM API | Player SPSC ring | Main loop capacity calculation and player_audio_submit | ✓ WIRED | Guest receives no more capacity than ring free space; callback only consumes published frames. |
| SDL event loop | Source-owned input state | Keyboard, focus, gamepad button/add/remove handlers | ✓ WIRED | Event handlers call the corresponding source/focus operations; named behavioral tests cover ownership and recovery. |
| SDL audio-device events | Audio adapter recovery | Main event handler calls player_audio_handle_device_event | ✓ WIRED | Adapter device test covers remove/add, unavailable sink and stale-buffer cleanup. |
| Save transition | App reset/ROM replacement and host clear | Save resolution before finish_transition; clear after success | ✓ WIRED AND BEHAVIORALLY VERIFIED for normal R-reset | `player_reset_transition` drives ordinary R, injected save failure, Escape cancel, and successful retry; it asserts preservation of queued state until success, input/audio reset, and persisted-byte recovery in an independent guest. |
| Space pause/resume | SDL key event → `toggle_pause` → guest APU history and audio backlog | Space branch calls `toggle_pause`; pause clears host PCM without calling core reset | ✓ WIRED AND BEHAVIORALLY VERIFIED | The named test sends real Space KEYDOWN events through `pump_events()`, checks paused/input state and exact flush byte count, resumes, and compares subsequent PCM with an uninterrupted reference guest after equal pre-pause progress. |
| Measurement script | Player workload and receipt | Bounded --audio-measure route, revision/build-bound JSON | ✓ WIRED | Current script run created a passed receipt for the current source revision. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|----------|---------------|--------|--------------------|--------|
| Core APU/PCM | Channel events and output frames | Emulated guest instructions and register writes in the machine instance | Yes | ✓ FLOWING |
| Player ring/callback | Published PCM frames | gbb_run_audio caller buffer from the active guest session | Yes | ✓ FLOWING |
| Measurement receipt | PCM digest and queue metrics | Authored workload executed by the packaged player and dummy SDL stream | Yes | ✓ FLOWING; software/dummy evidence only |
| Player input | Held-button state and guest events | SDL keyboard/focus/controller events | Yes | ✓ FLOWING |

There is no dynamic web/database-rendered value in this phase; a UI data-flow trace is not applicable.

### Behavioral Spot-Checks

| Behavior | Command / evidence | Result | Status |
|----------|--------------------|--------|--------|
| Core APU/PCM and full core regression inventory | `cmake --preset phase1 -DGABBABOY_BUILD_PLAYER=OFF && cmake --build --preset phase1 --parallel 2 && ctest --preset phase1 --output-on-failure --no-tests=error` | **179/179 passed** in the dirty integrated worktree at HEAD `4d52df7aa0594bad2a3b0f0dc91e92e5612a2f4c`. | ✓ PASS |
| Player package and software SDL smoke | `env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home SDL_AUDIO_DRIVER=dummy bash tests/scripts/verify-phase3-player.sh` | **50/50 passed**, including `player_reset_transition`, new CLI help assertions for S versus R/C/Escape recovery, package smoke, and SDL dummy open/stream/close/recovery. Candidate package SHA-256 `adb4ba71d023ba20a06b6a2160e39ec07095588d8d176965e325e09caede11c8`. | ✓ PASS |
| Normal app-level pause/resume and R-reset transitions | Included as `player_reset_transition` in the 50/50 player verifier at the integrated worktree HEAD above. | The test drives actual Space and R SDL events through the app loop and asserts PCM flush/continuity, save failure/cancel/retry, and battery recovery. | ✓ PASS |
| Sustained 300-frame workload | env HOME=/private/tmp/gabbaboy-validation-home CFFIXED_USER_HOME=/private/tmp/gabbaboy-validation-home bash tests/scripts/measure-audio-playback.sh | Passed at current HEAD. Two partitions each produced 241,094 exact in-window s16le stereo frames and matching digest 8667279ae7d3bf3cdd76a278b13d2cdfe9992d64325c15e4eef9449778eaeec4. | ✓ PASS |
| Named core audio/APU behavioral cases | audio_capacity, audio_partition, audio_no_alloc, apu_sequencer, apu_timeline, apu_wave, apu_noise, apu_power | All passed. | ✓ PASS |
| Named player input/audio transition cases | player_input_sources, player_input_reconnect, player_input_focus_audio, player_audio_lifecycle, player_audio_device, player_audio_replacement, player_reset_transition | All passed; `player_reset_transition` tests both Space pause/resume APU continuity and the normal R-reset route. | ✓ PASS |

Current receipt: `build/phase3-player/audio-measurement/4d52df7aa059-w8jl5pmr/receipt.json`. It records Release/macOS arm64, 48,000 Hz signed 16-bit little-endian interleaved stereo, scoped DMG-CPU-B software model, authored MIT workload, 300 target video frames, and 42,134,424 elapsed half-dots versus 42,134,400 requested. Both partitions produced 241,094 frames with PCM SHA-256 `8667279ae7d3bf3cdd76a278b13d2cdfe9992d64325c15e4eef9449778eaeec4`. Ring target/ceiling/high-water were 1,606/3,214/3,214 frames; each partition recorded 1,024 application underflow frames, 2,502 intentionally discarded host frames, zero stream-write failures, zero queued-input bytes, and 3,203/3,211 producer backpressure events. Dummy SDL passed; no default physical audio device was available. The receipt is bound to HEAD `4d52df7aa0594bad2a3b0f0dc91e92e5612a2f4c` but records `source_tree_state: dirty`; it is not clean-checkout or hosted CI evidence.

### Probe Execution

Not applicable. The seven plans declare no probe paths, and this is not a migration/tooling phase.

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|----------------|-------------|--------|----------|
| AUDIO-01 | 05-01, 05-02, 05-03, 05-04, 05-07 | Four scoped DMG channels/registers/sequencer with analog/revision limits | ✓ SATISFIED | APU register/timing and authored-pattern tests; model and approximation docs. |
| AUDIO-02 | 05-01, 05-04, 05-05, 05-07 | Deterministic bounded PCM contract without allocation or required-output loss | ✓ SATISFIED | API, capacity, partition, filter, allocation and ring tests; documentation. |
| AUDIO-03 | 05-01, 05-05, 05-07 | Paced macOS player, volume, queue evidence | ✓ SATISFIED | Player tests and current-revision sustained receipt. |
| HOST-01 | 05-06, 05-07 | Input recovery on focus loss and controller disconnect/reconnect | ✓ SATISFIED | Source-ownership, focus, reconnect tests and SDL event wiring. |
| HOST-02 | 05-06, 05-07 | Pause/reset/replacement/device cleanup without stale cross-session state | ✓ SATISFIED | App-level `player_reset_transition` covers Space pause/resume APU continuity and battery-safe R-reset; device and replacement behavior tests pass. |

No additional requirements are mapped to Phase 5 without a claiming plan; no orphaned phase requirement was found.

### Test Quality Audit

| Test File | Linked Requirement | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|--------------------|--------|---------|----------|-----------------|---------|
| tests/test_apu.c | AUDIO-01 | Yes | 0 | 0 | Value/behavior | PASS — authored register programs assert digital patterns and timing. |
| tests/test_audio.c, tests/test_audio_no_alloc.c | AUDIO-02 | Yes | 0 | 0 | Value/behavior | PASS — fixed analytical expectations, exact partition comparison, capacity and allocator checks. |
| tests/player/test_audio.c, tests/player/test_audio_counters.c | AUDIO-02, AUDIO-03, HOST-02 | Yes | 0 | 0 | Value/behavior | PASS — ring, concurrency, gain, lifecycle, device and replacement assertions. |
| tests/player/test_input.c | HOST-01 | Yes | 0 | 0 | Value/behavior | PASS — source ownership, release, focus and reconnect sequences. |
| tests/scripts/measure-audio-playback.sh | AUDIO-03 | Yes | 0 | 0 | Behavioral/output digest | PASS — checks exact count and equal partition digest; it is not an independent hardware or perceptual oracle. |
| tests/player/test_reset_transition.c | HOST-02 | Yes | 0 | 0 | Behavioral | PASS — actual SDL Space and R event paths, PCM flush plus resumed-PCM equivalence, failed-save cancel/retry, session preservation, input/audio reset and persisted battery recovery; no disabled or circular assertions found. |

**Disabled tests on requirements:** 0. **Circular expected-value patterns detected:** 0. **Insufficient assertions:** 0 for the claims these tests make.

### Decision Coverage

All trackable CONTEXT decisions are honored by shipped artifacts: 12/12, with no unhonored decisions. The decision-coverage gate is warning-only and does not affect status.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found in the reviewed phase files. | — | Debt-marker scan found no unreferenced TODO/FIXME/XXX/HACK/placeholder markers; no stub implementation or disabled requirement test was found. |

The security report records zero open high-severity threats and all 14 unique threat IDs mitigated or accepted. The clean code review covers 26 phase files and reports zero findings; its prior callback-accounting finding is recorded as fixed and covered by tests and the receipt.

### Human Verification Required

N/A for additional manual UAT. All scoped software behaviors, including app-level pause/resume and reset ordering, are covered by named automated tests. Physical DMG analog/revision qualification, subjective listening, real controller enumeration, and real-device hotplug remain outside the evidence boundary and are not claimed.

### Gaps Summary

All 17 distinct plan truths and all five roadmap success criteria/requirements are verified. The app-level transition test exercises Space pause/resume, proves the exact host PCM flush and resumed output equivalence with an uninterrupted guest, and covers R-reset save failure/cancel/retry and battery recovery. Core, player/package and sustained measurement checks pass locally in a dirty integrated worktree; they do not establish clean-checkout or hosted-CI status. Physical hardware, perceptual quality, physical controller enumeration, and real-device hotplug remain explicitly unclaimed and outside this phase's software acceptance boundary.

---

_Verified: 2026-10-09T19:26:49Z_
_Verifier: the agent (gsd-verifier)_
