---
phase: "GB-03"
slug: "visible-interactive-dmg"
status: validated
nyquist_compliant: true
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
| 03-04-02 | 03-04 | 4 | VIDEO-03 | T-03-15 | Exact IF assertions are added only after the D-08 source gate closes | source qualification / evidence gate | Superseded by adopted D-025 software-model policy and Plan 03-13 guest regression | docs/dmg-video-evidence.md; 03-RESEARCH.md | Hardware phase and low-duration qualification remain open; no physical CPU-B result is claimed |
| 03-05-01 | 03-05 | 5 | VIDEO-03, VIDEO-04, VIDEO-05 | T-03-21, T-03-23 | Optional SDL input/render path stays outside the default core graph; smoke checks rendered shade before, during and after Z | integration / build | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_input.c`; `src/player/main.c` | player smoke passed locally with isolated save storage; exact-revision macOS package CI is now required for every PR |
| 03-05-02 | 03-05 | 5 | VIDEO-03, VIDEO-04 | T-03-21, T-03-22 | Host time conversion, repeats, pause/reset and focus-loss release capacity are tested | integration / regression | `bash tests/scripts/verify-phase3-player.sh`; full `ctest --preset phase1` | `tests/player/test_input.c` | passed 4/4 optional tests and full core suite 129/129; no live-window perceptual check available |
| 03-06-01 | 03-06 | 6 | VIDEO-04, VIDEO-05 | T-03-25, T-03-27 | ROM replacement is transactional and limitation/status text is visible | integration / adapter | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_session.c`; `src/player/main.c`; `docs/preview.md` | passed injected success/failure event path and bounded invalid-file cases within optional suite 14/14; live desktop text check unavailable |
| 03-06-02 | 03-06 | 6 | VIDEO-04 | T-03-26 | Drawable geometry is integer-scaled, centered and overflow-safe | unit / adapter | `bash tests/scripts/verify-phase3-player.sh` | `tests/player/test_presentation.c`; offscreen renderer checks in `src/player/main.c` | passed native, odd, letterbox, high-DPI, undersized and large-bound cases; optional suite 14/14 |
| 03-07-01 | 03-07 | 7 | VIDEO-01, VIDEO-05 | T-03-28, T-03-30 | Invalid frame copies preserve caller storage and metadata | unit / regression | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(frame_copy_failures|frame_generation_lifecycle|independent_instances)$'` | `tests/test_api.c`; `tests/test_ppu.c` | passed 3/3; offline suite passed 132/132 |
| 03-07-02 | 03-07 | 7 | VIDEO-03 | T-03-29, T-03-31 | Invalid queues reject atomically; installed C/C++ consumers exercise public API | unit / consumer | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(event_queue_atomic|event_queue_failure_precedence|event_queue_order|event_partition|event_time_overflow|joypad_selection|joypad_queue_atomic|joypad_equal_time|joypad_partition|frame_copy_failures|frame_generation_lifecycle)$'`; `bash tests/scripts/verify-phase2-installed.sh` | `tests/test_events.c`; `tests/consumers/c/main.c`; `tests/consumers/cpp/main.cpp` | focused cases passed 11/11; relocated installed inventory 137/137 and core-only inventory 132/132 passed, no skips |
| 03-08-01 | 03-08 | 8 | VIDEO-05 | T-03-32 | Rebuilt fixture bytes match checked-in size and digest | fixture / provenance | bash tests/scripts/reproduce-visible-demo.sh | tests/scripts/reproduce-visible-demo.sh | passed locally with pinned macOS RGBDS v1.0.1; wrong-version and mutated-byte controls failed closed |
| 03-08-02 | 03-08 | 8 | VIDEO-05 | T-03-32, T-03-33 | Hosted fixture job uses pinned tool and exact checkout receipt | hosted CI | Exact-head fixture-repro lane | .github/workflows/fixture-repro.yml | passed at 53f9f56cacbe6676b2c0db1dddf12dd0e44fa4f3 in run 37683636738; uploaded receipt identity verified |
| 03-09-01 | 03-09 | 9 | VIDEO-04, VIDEO-05 | T-03-34, T-03-36 | macOS lane uses pinned dependency and nonempty player smoke | hosted build / integration | Exact-head macOS player job on every pull request | CI run 37942469774 at `de966868057c1fb5b3bca5b4cdac50cadf3bae57`; `macos-player-package` and `required-native` passed | passed |
| 03-09-02 | 03-09 | 9 | VIDEO-04, VIDEO-05 | T-03-35 | Downloaded package digest/notices and extracted-byte smoke match exact revision | package / consumer | Exact-head downloaded-package smoke | Preview run 37942469925 at `de966868057c1fb5b3bca5b4cdac50cadf3bae57`; Linux and macOS package consumers, `player-package-smoke-macos`, and `preview-package-smoke` passed | passed |
| 03-13-01 | 03-13 | gap 12 | VIDEO-03 | T-03-43 | Ordered selected-pin transitions request guest-visible IF.4 | unit / guest regression | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error -R '^joypad_'` | `tests/test_joypad.c`; `tests/CMakeLists.txt`; `tests/expected-tests.txt` | passed 6/6 including P10–P13, selected/unselected, held-selector, second-pin, duplicate, shared-pin releases, sticky IF, IE=0, equal-time ordering, and FF00/FF0F partition-equivalent results; CPU-B pulse/sample phase remains unmeasured |
| 03-13-02 | 03-13 | gap 12 | VIDEO-02 | T-03-44 | Owned guests check mode-2 overlap, mode-3 word boundaries, CPU mode access, and same-dot DMA/PPU/CPU result | unit / guest regression | `ctest --preset phase1 --output-on-failure --no-tests=error -R '^(dma_ppu_overlap|dma_active_mode_matrix|dma_ppu_word_boundaries|dma_ppu_cpu_collision)$'` | `tests/test_dma.c`; `tests/CMakeLists.txt`; `tests/expected-tests.txt` | passed 4/4: baseline/partial/ended-before-scan controls; before/after byte-boundary pixels; active DMA VRAM/OAM reads/writes in modes 0–3; same-half-dot DMA byte, PPU fetch, CPU `$FF` read; scan/tie partition equivalence; CPU-B timing and revision scope remain unmeasured |
| 03-13-03 | 03-13 | gap 12 | VIDEO-02, VIDEO-03 | T-03-45 | Source provenance and claim limits reconcile to execution evidence | full core regression | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error && git diff --check` | `docs/dmg-video-evidence.md`; `03-VERIFICATION.md`; `03-13-SUMMARY.md`; `03-REVIEW.md` | passed 141/141 after review fixes, including `dma_oam_entry39` and `dma_oam_entry39_reset`; focused review selection passed 17/17 with zero findings; VIDEO-04 visible packaged-window/key evidence and exact CPU-B timing remain unclaimed |

---

## First feedback slice

This is an MVP phase. To keep the first planned work a real tracer rather than setup-only scaffolding, Wave 0 readiness is embedded tests-first in the first production task, 03-01-01. That task creates and runs the owned ROM-to-frame/gameplay oracle before later plans deepen timing, DMA, host UX, API failure behavior and packaging. No separate Wave 0 plan is required. The frontmatter flag wave_0_complete remains false until those tests have actually been added and run.

---

## Manual-Only Verifications

Scoped software behavior has an automated verification path. The user confirmed the current packaged window's visible Z response on 2026-10-09; the player suite now automates the corresponding offscreen rendered-pixel assertion. Physical DMG-CPU-B observation is unavailable in this environment, so no hardware-backed claim is part of this phase's acceptance evidence.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or explicit evidence-gate dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] First feedback slice covers validation gaps without a foundation-only lead plan
- [x] No watch-mode flags
- [x] Feedback latency measured and recorded
- [x] `nyquist_compliant: true` set after all focused tests and the full suite passed

Plan 03-09's two automated package tasks passed. Plan 03-13 adopts confidence-qualified software behavior with original guest checks. The registered matrix covers ordered JOYP edges, all active-DMA CPU VRAM/OAM cells in PPU modes 0–3, mode-2 overlap controls, adjacent DMA-byte/fetch boundaries, and a same-half-dot three-way collision. Follow-up review regressions cover OAM entry 39 and scan-cursor reset. The full current CTest suite passed 179/179 on the Phase 3 refresh branch after correcting the test helper's unsequenced `rn` access. The 2026-10-09 user observation confirms the current window displays the demo and responds to Z; the player smoke now asserts the rendered shade changes and restores, and every-PR macOS package CI carries that assertion into the extracted artifact. Tests do not claim physical CPU-B pulse phase, lane timing, or PPU-revision qualification.

**Approval:** automated validation refreshed 2026-10-09 after the combined CTest suite passed 229/229. Test 34's current packaged-player observation is recorded as a user pass in `03-UAT.md`; the pinned local package verifier passed 50/50 player tests, and exact-head macOS package CI passed in run 37942469774 with the downloaded-package consumer and aggregate passing in run 37942469925 at `de966868057c1fb5b3bca5b4cdac50cadf3bae57`. Physical DMG-CPU-B pulse phase, lane timing, and PPU-revision qualification remain outside the evidence.

## Automation Follow-up 2026-10-09

- `player_smoke` now reads the software-rendered target tile before input, after SDL Z-down while held, and after SDL Z-up. It checks shade 1 → shade 2 → shade 1 and the guest's matching press/release markers.
- `player_smoke` uses a build-local `HOME` and `CFFIXED_USER_HOME`; the package verifier gives extracted-byte smoke a unique temporary home and removes it on exit. Synthetic save/lock checks therefore stay out of the developer's normal SDL save directory without changing product save routing.
- The exact-head macOS package build and downloaded-package consumer are required on every pull request. The consumer reruns the rendered-pixel assertion against extracted package bytes. This automates the reproducible application pipeline while leaving actual native-window visibility and human-perceived output to the recorded user observation.
- Local pinned SDL 3.4.18 build/package verification passed all 50 player tests and the extracted-package Z/rendered-pixel, audio, and MBC1 continuation smoke. The combined current CTest inventory passed 229/229; `actionlint`, shell syntax, and `git diff --check` passed. Exact-head `required-native`, `fixture-repro`, and `preview-package-smoke` passed in runs 37942469774, 37942469816, and 37942469925 respectively for `de966868057c1fb5b3bca5b4cdac50cadf3bae57`.

## Validation Audit 2026-10-09

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

## Verification Freshness Follow-up 2026-10-09

- Hardened `verify-phase3-player.sh` so caller-selected verified-output directories are never recursively deleted. The stdlib helper rejects filesystem roots and every repository descendant, rejects candidate overlap and artifact-path directory collisions, removes only the two expected output files, and preserves unrelated files and symlink targets. Its default verified-output directory is under the runner/system temporary root rather than inside the checkout.
- Added four focused regressions for unrelated-file preservation, safe artifact-symlink removal, unsafe root rejection, and directory-collision rejection. The test is registered as `player_verified_output_directory` in the optional player CTest inventory.
- The refreshed optional player CTest suite passed 51/51. `bash -n tests/scripts/verify-phase3-player.sh`, the direct Python regression suite (4/4), `git diff --check`, and the full core CTest suite (179/179) passed. A package-verification run using a caller-selected output directory also preserved an unrelated sentinel file while producing the expected archive and receipt.
- Package smoke still asserts rendered Z-down/Z-up shade changes and MBC1 continuation. It reuses the existing owner-observed packaged-window result in `03-UAT.md`; no additional manual UAT was performed. Physical CPU-B timing and PPU revision qualification remain unclaimed.

## Nyquist Refresh 2026-10-09

| Gap | Requirement behavior | Test | Result |
|---|---|---|---|
| GB03-OUTPUT-DIR-OVERLAP | Verified artifact output must not delete caller/candidate data when the selected output path overlaps the candidate directory. | `PYTHONDONTWRITEBYTECODE=1 python3 tests/scripts/test_verified_player_output_dir.py -v` | **RESOLVED.** The first audit reproduced deletion of a candidate-owned archive. `prepare_output_dir` now rejects resolved equality and either ancestor/descendant overlap before creating or cleaning paths, then rechecks after directory creation. The preservation regression passes; the focused helper suite passes 8/8. |

The failing regression exposed a real destructive edge case and was retained as a passing preservation test after the implementation fix. Direct and symlink-resolved aliases, both nested-path directions, unrelated output files, expected-file symlinks, roots, and artifact-name directory collisions are covered. The full core CTest suite passes 179/179; the isolated macOS player/package lane passes 51/51 plus extracted-package input/render, audio recovery, and fresh-process MBC1 continuation checks. These results describe the dirty worktree contents copied into a disposable clone; they are not a clean-checkout or hosted-CI claim.

## Validation Refresh After Overlap Fix — 2026-10-09

- `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error`: 179/179 passed in the project worktree.
- `PYTHONDONTWRITEBYTECODE=1 python3 tests/scripts/test_verified_player_output_dir.py -v`: 9/9 passed, including rejection of a repository `.git` descendant with both artifact-name sentinels preserved.
- `bash tests/scripts/verify-phase3-player.sh --build-package`, run in a disposable clone with current worktree files copied over shared `HEAD` `bb8fd654d03969e3d207fcdc92c345cc60be3298`: optional player CTest passed 51/51; SDL 3.4.18 package and extracted-byte smoke passed; package SHA-256 `0016796835439b1fdba8fe15365137e85e8b6973cd28795966afa655a7f62fcc`; dummy-audio recovery, guest audio, MBC1 continuation, and rendered Z-down/Z-up shade transition passed. The clone used a dirty source overlay and is not represented as a clean checkout or hosted result.
- `bash -n tests/scripts/verify-phase3-player.sh` and `git diff --check` passed. The existing build scratch was left intact.

OpenGSD initially resolved this CMake-only repository's generic regression command to `true`. Set `workflow.test_command` to the full `phase1` CMake/CTest command above, then reran the canonical timed regression gate; it passed 179/179. Future phase regression gates now execute the actual core suite.
