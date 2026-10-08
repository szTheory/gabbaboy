---
phase: GB-05-dmg-audio-and-stable-playback
reviewed: 2026-10-08T17:10:00Z
depth: standard
files_reviewed: 26
files_reviewed_list:
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
  - tests/player/test_audio_counters.c
  - tests/player/test_input.c
  - tests/player/test_limitations.c
  - tests/scripts/measure-audio-playback.sh
  - tests/scripts/verify-phase3-player.sh
  - tests/test_apu.c
  - tests/test_audio.c
  - tests/test_audio_no_alloc.c
  - .github/workflows/preview.yml
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase GB-05: Code Review Report

**Reviewed:** 2026-10-08T17:10:00Z
**Depth:** standard
**Files Reviewed:** 26
**Status:** issues_found

## Summary

Reviewed the Phase GB-05 core audio/APU implementation, SDL playback and input adapters, test and measurement code, public documentation, package workflow, and the current uncommitted help/title updates. One blocker remains in the SDL audio callback error path: PCM has already been removed from the ring before SDL confirms it accepted the data, and a failed write drops that PCM without counting the dropped frames.

## Critical Issues

### CR-01: BLOCKER — SDL stream write failure drops dequeued PCM

**File:** `src/player/audio.c:90-105`
**Issue:** The callback copies frames from the SPSC ring and advances `read_index` at line 93 before calling `write_fn` at line 115. If `SDL_PutAudioStreamData` fails, the function returns after incrementing only `sink_failures`; the already-consumed frames are neither restored nor added to the intentionally-discarded-host-frame accounting. Playback therefore loses audio on a sink write failure while the documented counters do not report that loss.
**Fix:** Preserve each callback chunk until its stream write succeeds, or on failure explicitly count all PCM bytes removed from the ring/pending frame as discarded and transition the sink into a recovery/unavailable state. Add a callback test where the writer rejects a nonempty block and assert no PCM loss is unaccounted for.

## Warnings

## Info

---

_Reviewed: 2026-10-08T17:10:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
