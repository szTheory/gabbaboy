---
phase: "GB-05"
slug: "dmg-audio-and-stable-playback"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-08"
updated: "2026-10-10"
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

## Evidence Refresh 2026-10-10 (source revision f1995ad)

Verification-freshness refresh against the tree at `f1995ad` (code-identical to `cb4a96c`; the only later change is `05-VALIDATION.md`). The previous phase verification ran at `7b1c491`. Between `7b1c491` and `f1995ad` the only source changes in or near phase scope are `src/player/session.c` (one line), `tests/player/test_session.c`, `tests/scripts/verified_player_output_dir.py` (new), its test `tests/scripts/test_verified_player_output_dir.py`, and `tests/scripts/verify-phase3-player.sh`. `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h`, `src/player/audio.c`, `src/player/input.c`, `src/player/main.c`, and `tests/scripts/measure-audio-playback.sh` are unchanged, so the earlier closures still hold. The line references below are current.

| Threat ID | Current evidence |
|-----------|------------------|
| T-05-01 | `src/core/gabbaboy.c:1602-1607` `audio_preflight` checks remaining capacity before each step; callers return `GBB_STOP_OUTPUT_FULL` before mutation at `:2140`, `:2162`, `:2194`, `:2203`. |
| T-05-02 | `src/player/audio.c:51-54`, `:82-96`, `:223`, `:269`: ring indices use acquire loads and release stores; the core instance is never touched from the SDL callback (`player_audio_transfer`, `:65`). |
| T-05-03 | `src/core/gabbaboy.c:2114` and `:2141` refuse to advance past `UINT64_MAX` emulated half-dots (`GBB_STOP_INVALID_STATE`). |
| T-05-04 | `src/core/gabbaboy.c:1505` wraps the wave position `& 31u`; `:213` indexes the 16-byte wave RAM with `position >> 1`; `:563-564` reads the noise divisor from a fixed 8-entry table using `polynomial & 7u`. |
| T-05-05 | `src/core/gabbaboy.c:2265-2297` `gbb_run_audio` rejects capacity multiplication overflow, address-range overflow, and overlap between frames and `out_frame_count` before any state is touched; it zeroes the count first and clears the run binding on exit. |
| T-05-06 | `src/core/gabbaboy.c:146-147` `audio_saturate_s16`, applied at `:182-189` to the rounded Q15 output and the high-pass state. |
| T-05-07 | `src/player/audio.c:65-100`: bounded `PLAYER_AUDIO_CALLBACK_CHUNK` stack block, unsigned byte count, `memset` zero-fill on shortage; no allocation, lock, logging, or guest work on the callback path. |
| T-05-08 | `src/player/audio.c:150-159` requires lock-free atomics; `:234-269` `player_audio_clear` pauses and locks the stream before resetting indices; `:325-330` keeps userdata alive when quiescence cannot be established. |
| T-05-09 | `src/player/input.c:291-341` `player_input_retry_focus_releases` retries failed releases for the owning source only. |
| T-05-10 | `src/player/main.c:1066-1071` saves battery RAM before a transition completes; `:894-935` `replace_session_rom` stages the candidate machine, ROM, and lock, swaps state only after success, then clears audio (`:935`). The ROM read the candidate depends on is hardened further (see below). |
| T-05-11 | `src/player/audio.c:286-320` bounded reopen; `:343` a missing sink is a supported state; `:206` counts dropped frames in `unavailable_frames`. |
| T-05-12 | `tests/scripts/measure-audio-playback.sh:60-76` binds a full 40-hex revision, the pinned Release build, and the fixture digest and license; `:106-172` requires model `DMG-CPU-B`, workload, labeled application counters, and `pcm_sha256`. |
| T-05-13 | `tests/scripts/measure-audio-playback.sh:76` requires the manifest's `sha256` and `license` for the authored demo fixture; `tests/scripts/verify-phase3-player.sh:227-234` checks the package's audio metadata claims. |
| T-05-SC | No dependency change since `7b1c491`; the new helper uses only the Python standard library. |

### Changed-file threat assessment

- **`src/player/session.c:104` (PR #43): closes a residual DoS on T-05-10 / T-05-11.** `read_rom_file` now opens with `O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK`. Before this, choosing a FIFO with no writer as the replacement ROM blocked `open()` on the player's main loop indefinitely, before the existing `fstat`/`S_ISREG` bound (`:109-115`) could reject it. That would have stalled the guest and audio producer during a session transition. Now `open()` returns at once, the regular-file check rejects the path with "not a bounded regular file", and the current session stays unchanged. Regression: `tests/player/test_session.c:121-130` (`player_session_replacement_failure`) creates a FIFO, asserts the rejection and the unchanged session, and confirms the FIFO itself is left in place. `O_NONBLOCK` has no effect on regular-file reads, so the bounded read loop (`:123-137`) is unchanged.
- **`tests/scripts/verified_player_output_dir.py` (new) with `verify-phase3-player.sh:296-303`: strengthens publication integrity (related to T-05-12 / T-05-13).** This replaces the earlier `rm -rf -- "$FINAL_ARTIFACT_DIR"` of a caller-supplied path. The helper rejects output directories that overlap the candidate directory, the filesystem root, or the repository (`:70-80`). It walks directories with `O_DIRECTORY|O_NOFOLLOW` descriptor-relative opens (`:31-56`), unlinks only the two named outputs, publishes through `O_EXCL|O_NOFOLLOW` temp files linked into place (`:127-187`), and withdraws partial output by inode-checked unlink (`:207-221`). The receipt now also binds the candidate `package_sha256` from the build receipt. This adds no new threat to this phase; the default output location moved outside the repository build tree to `${RUNNER_TEMP:-${TMPDIR:-/tmp}}`.

### Commands run (2026-10-10, tree at f1995ad, macOS arm64)

| Command | Result |
|---------|--------|
| `cmake --build build/phase3-player/gabbaboy` | up to date (`ninja: no work to do`), so the build matches current sources |
| `ctest --test-dir build/phase3-player/gabbaboy -R "session\|audio\|input"` | 45/45 passed |
| `ctest --test-dir build/phase3-player/gabbaboy -R session_replace` | 2/2 passed (includes the FIFO regression) |
| `python3 tests/scripts/test_verified_player_output_dir.py` | 20 tests, OK |
| Reused from the Nyquist refresh at `cb4a96c` (`f1995ad`) | core CTest 179/179; player verifier 51/51 |

## Evidence Refresh after Phase 06.1 (2026-10-10, source revision ac3cb6e)

Verification-freshness refresh after PR 54 (merge `ab76d09c2ee27ba09fc5f3c2510af016aebfdecb`). The tree at `ac3cb6e` differs from `ab76d09` only under `.planning/`. Since `f1995ad`, the in-scope source changes are `src/player/session.c`, `tests/player/test_session.c`, `tests/scripts/test_verified_player_output_dir.py` and `tests/scripts/verify-phase3-player.sh` (a comment only). `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h`, `src/player/audio.c`, `src/player/input.c`, `src/player/main.c`, `tests/scripts/verified_player_output_dir.py` and `tests/scripts/measure-audio-playback.sh` are unchanged, so the T-05-01 to T-05-12 references above still hold. Current line references for the shifted files:

| Threat ID | Current evidence at `ac3cb6e` |
|-----------|-------------------------------|
| T-05-10 / T-05-11 | `src/player/session.c:107` opens the replacement ROM with `O_RDONLY \| O_CLOEXEC \| O_NOFOLLOW \| O_NONBLOCK \| O_NOCTTY`; `:113-117` rejects non-regular or oversized files; `:142-151` now reports the 2 MiB read bound and a close failure as separate errors, freeing the buffer on both. `tests/player/test_session.c:133-137` asserts the 2097153-byte case reports "2 MiB read bound" and leaves the session unchanged; `:151-157` keeps the FIFO regression. The close-failure branch is verified by inspection only. |
| T-05-13 | `tests/scripts/verify-phase3-player.sh:232-239` checks the package's audio metadata claims; `:301-308` publishes through `verified_player_output_dir.py`. The new comment at `:15-19` documents that the `GBB_VERIFIED_OUTPUT_DIR` fallback matters only for local `--verify-package` runs (P5 IN-01, `ecb0db7`). |
| T-05-SC | No dependency change since `f1995ad`. |

The PR 54 changes add no new threat in this phase's scope. `O_NOCTTY` only narrows `open()` behaviour on terminal paths, and splitting the error branches does not change which inputs are rejected.

### Commands run (2026-10-10, tree at ac3cb6e, macOS arm64)

| Command | Result |
|---------|--------|
| `ctest --preset phase1 --output-on-failure --no-tests=error` | 184/184 passed |
| `SDL_AUDIO_DRIVER=dummy bash tests/scripts/verify-phase3-player.sh` (isolated `HOME`) | 51/51 passed, exit 0 |
| `ctest --test-dir build/phase3-player/gabbaboy -R "session\|audio\|input"` | 45/45 passed |
| `ctest --test-dir build/phase3-player/gabbaboy -R session_replace` | 2/2 passed (FIFO and size-bound regressions) |
| `python3 tests/scripts/test_verified_player_output_dir.py` | 21 tests, OK |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-08 | 14 unique IDs (20 plan-register rows) | 14 | 0 at/above high threshold | gsd-security-auditor and orchestrator |
| 2026-10-10 | 14 unique IDs (freshness refresh at f1995ad) | 14 | 0 | orchestrator (L1 evidence refresh; short-circuit, ASVS 1) |
| 2026-10-10 | 14 unique IDs (freshness refresh after 06.1 at ac3cb6e) | 14 | 0 | orchestrator (L1 evidence refresh; short-circuit, ASVS 1) |

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-08; evidence refreshed 2026-10-10 at `f1995ad` and again after Phase 06.1 at `ac3cb6e`. Physical device hotplug, analog DMG output, and perceptual audio remain outside this software security verification.

## Security Audit 2026-10-09

| Metric | Count |
|---|---|
| Threats found | 14 |
| Closed | 14 |
| Open | 0 |
