---
phase: "GB-03"
slug: "visible-interactive-dmg"
status: executing
nyquist_compliant: false
wave_0_complete: true
created: "2026-10-07"
---

# Phase GB-03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | CTest with native C test executables and a fail-closed expected-test inventory |
| **Config file** | `tests/CMakeLists.txt`, `cmake/ExpectedTests.cmake`, `tests/expected-tests.txt` |
| **Quick run command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^(frame_composition_|ppu_timing_|dma_|joypad_)'` |
| **Full suite command** | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` |
| **Estimated runtime** | Not measured; record from the first integrated tracer run |

---

## Sampling Rate

- **After every task commit:** Run the task's focused CTest selection after the `phase1` build.
- **After every plan wave:** Run the full offline core suite and the strict expected-test inventory; run the optional SDL3/macOS package lane on the exact revision when player or packaging tasks change.
- **Before `$gsd-verify-work`:** The full suite, fixture digest/reproduction check, and exact-revision package checks must be green.
- **Max feedback latency:** Record the first integrated tracer baseline; keep focused suites under 30 seconds where practical.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 03-01 | 1 | VIDEO-01, VIDEO-03, VIDEO-05 | T-03-01, T-03-02 | Owned ROM, independently expected frame, timestamped polling response | unit / integration | Focused tracer/digest selection; full `ctest --preset phase1` | tests/test_tracer.c; visible fixture manifest | passed focused selection; full suite 107/107; fixture reproduced with pinned RGBDS digest |
| 03-02-01 | 03-02 | 2 | VIDEO-01, VIDEO-05 | T-03-05 | Separate authored BG/window/object composition images | unit / regression | Plan 03-02 verification selection | tests/test_tracer.c; tests/test_ppu.c | passed 14/14 plan verification selection |
| 03-02-02 | 03-02 | 2 | VIDEO-01, VIDEO-05 | T-03-06, T-03-07 | Mode/STAT/fetch boundaries have source/profile qualification | unit / regression | Plan 03-02 verification selection | tests/test_ppu.c | passed 14/14 combined plan verification selection; hardware timing remains unclaimed |
| 03-03-01 | 03-03 | 3 | VIDEO-02, VIDEO-05 | T-03-08, T-03-10 | DMA progress, mapping, HRAM access and partitions are bounded | unit / regression | ctest --preset phase1 --output-on-failure --no-tests=error -R '^dma_.*$' | tests/test_dma.c | passed 9/9 locally and under Linux ASan/UBSan |
| 03-03-02 | 03-03 | 3 | VIDEO-02, VIDEO-05 | T-03-09, T-03-10 | Lockouts/contention distinguish initiators and model applicability | unit / regression | ctest --preset phase1 --output-on-failure --no-tests=error -R '^(dma_.*|ppu_timing_.*|frame_composition_.*|joypad_gameplay_tracer|bus_(preflight|unsupported_stack|unsupported_fetch))$' | tests/test_dma.c; docs/dmg-video-evidence.md | passed 23/23; disputed PPU/DMA collision outcome remains unqualified |
| 03-04-01 | 03-04 | 4 | VIDEO-03 | T-03-14, T-03-16 | Queue and active-low matrix behavior is atomic and deterministic | unit / regression | ctest --preset phase1 --output-on-failure --no-tests=error -R '^(joypad_selection|joypad_queue_atomic|joypad_equal_time|joypad_partition)$'; full offline suite | tests/test_joypad.c | passed 4/4 focused; full suite passed 129/129 locally |
| 03-04-02 | 03-04 | 4 | VIDEO-03 | T-03-15 | Exact IF assertions are added only after the D-08 source gate closes | source qualification / evidence gate | Retained by design: no interrupt tests registered because exact DMG-CPU-B cases remain unsupported by available evidence | docs/dmg-video-evidence.md; 03-RESEARCH.md | D-08 remains open; no guessed IF behavior; VIDEO-03 remains incomplete |
| 03-05-01 | 03-05 | 5 | VIDEO-03, VIDEO-04, VIDEO-05 | T-03-21, T-03-23 | Optional SDL input/render path stays outside the default core graph | integration / build | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_input.c`; `src/player/main.c` | passed 4/4; official SDL 3.4.18 source digest verified; smoke used offscreen renderer because no desktop display is available |
| 03-05-02 | 03-05 | 5 | VIDEO-03, VIDEO-04 | T-03-21, T-03-22 | Host time conversion, repeats, pause/reset and focus-loss release capacity are tested | integration / regression | `bash tests/scripts/verify-phase3-player.sh`; full `ctest --preset phase1` | `tests/player/test_input.c` | passed 4/4 optional tests and full core suite 129/129; no live-window perceptual check available |
| 03-06-01 | 03-06 | 6 | VIDEO-04, VIDEO-05 | T-03-25, T-03-27 | ROM replacement is transactional and limitation/status text is visible | integration / adapter | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c`; `src/player/main.c`; `docs/preview.md` | passed injected success/failure event path and bounded invalid-file cases within optional suite 14/14; live desktop text check unavailable |
| 03-06-02 | 03-06 | 6 | VIDEO-04 | T-03-26 | Drawable geometry is integer-scaled, centered and overflow-safe | unit / adapter | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_presentation.c`; offscreen renderer checks in `src/player/main.c` | passed native, odd, letterbox, high-DPI, undersized and large-bound cases; optional suite 14/14 |
| 03-07-01 | 03-07 | 7 | VIDEO-01, VIDEO-05 | T-03-28, T-03-30 | Invalid frame copies preserve caller storage and metadata | unit / regression | ctest --preset phase1 --output-on-failure --no-tests=error -R '^(frame_copy_|frame_generation_|independent_instances)$' | Planned in 03-07 | pending |
| 03-07-02 | 03-07 | 7 | VIDEO-03 | T-03-29, T-03-31 | Invalid queues reject atomically; installed C/C++ consumers exercise public API | unit / consumer | bash tests/scripts/verify-phase2-installed.sh | Planned in 03-07 | pending |
| 03-08-01 | 03-08 | 8 | VIDEO-05 | T-03-32 | Rebuilt fixture bytes match checked-in size and digest | fixture / provenance | bash tests/scripts/reproduce-visible-demo.sh | Planned in 03-08 | pending |
| 03-08-02 | 03-08 | 8 | VIDEO-05 | T-03-32, T-03-33 | Hosted fixture job uses pinned tool and exact checkout receipt | hosted CI | Exact-head fixture-repro lane | Planned in 03-08 | pending |
| 03-09-01 | 03-09 | 9 | VIDEO-04, VIDEO-05 | T-03-34, T-03-36 | Optional macOS lane uses the pinned dependency and nonempty player smoke | hosted build / integration | Exact-head opt-in macOS player job | Planned in 03-09 | pending |
| 03-09-02 | 03-09 | 9 | VIDEO-04, VIDEO-05 | T-03-35 | Downloaded package digest/notices and extracted-byte smoke match exact revision | package / consumer | Exact-head downloaded-package smoke | Planned in 03-09 | pending |

---

## First feedback slice

This is an MVP phase. To keep the first planned work a real tracer rather than setup-only scaffolding, Wave 0 readiness is embedded tests-first in the first production task, 03-01-01. That task creates and runs the owned ROM-to-frame/gameplay oracle before later plans deepen timing, DMA, host UX, API failure behavior and packaging. No separate Wave 0 plan is required. The frontmatter flag wave_0_complete remains false until those tests have actually been added and run.

---

## Manual-Only Verifications

All scoped software behavior has an automated verification path. Physical DMG-CPU-B observation is unavailable in this environment, so no hardware-backed claim is part of this phase's acceptance evidence.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or explicit evidence-gate dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] First feedback slice covers validation gaps without a foundation-only lead plan
- [ ] No watch-mode flags
- [ ] Feedback latency measured and recorded
- [ ] `nyquist_compliant: true` set in frontmatter after audit

**Approval:** pending
