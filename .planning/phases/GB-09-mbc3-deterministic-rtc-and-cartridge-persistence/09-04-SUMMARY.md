---
phase: 09-mbc3-deterministic-rtc-and-cartridge-persistence
plan: 04
subsystem: persistence-fixtures
tags: [save-envelope, v0.1.2, corpus, fixtures, CART-06]
requires: []
provides:
  - "fixtures/save-envelope-v1: 8 KiB and 32 KiB save envelopes written by the released v0.1.2 player writer"
  - "tests/scripts/generate-save-envelope-v1.sh with offline --check mode (check=pass / check=fail:<reason>)"
affects: [09-13]
tech-stack:
  added: []
  patterns: ["frozen-tag generator builds old source via git archive in a scratch dir; field-by-field envelope decode in --check"]
key-files:
  created:
    - tests/scripts/generate-save-envelope-v1.sh
    - fixtures/save-envelope-v1/mbc1-8k.gbb
    - fixtures/save-envelope-v1/mbc1-32k.gbb
    - fixtures/save-envelope-v1/manifest.json
    - fixtures/save-envelope-v1/LICENSE.txt
  modified: []
key-decisions:
  - "Driver compiled directly with cc against the v0.1.2 session.c and core sources (reusing the digest-pinned SDL3 3.4.18 prefix) rather than a full CMake configure of the old tree"
  - "--generate accepts an optional OUT_DIR so reruns can be compared without touching committed fixtures"
requirements-completed: [CART-06]
status: complete
duration: 15 min
completed: 2026-10-11
commits: 2
plan_head_before: 2fd95317469f7a948cea485417ba4806f920d3ff
plan_head_after: 8433e7b6e9d314fa1071f923ee7adbb5619baca7
actuals:
  tokens: 14000
  tasks: 2
  commits: 2
coverage:
  - deliverable: "v0.1.2-written 8 KiB and 32 KiB envelopes committed with provenance manifest"
    verification:
      - kind: command
        ref: "bash tests/scripts/generate-save-envelope-v1.sh --check"
        status: pass
    human_judgment: false
---

# Phase 9 Plan 04: v0.1 Save Corpus Summary

Two save envelopes (8243 and 32819 bytes) produced by the released v0.1.2 `player_session_save_battery`, with a manifest recording tag, commit, SDL, toolchain, recipe ROM digests and envelope digests, plus an offline checker.

## Accomplishments

- Generator builds the v0.1.2 tag (`git archive` into a scratch dir), drives the real load/import/save path for synthetic MBC1 $03 recipe ROMs, and copies out the produced envelope.
- `--check` decodes magic, version, ROM SHA-256, type, RAM length, IEEE CRC-32, payload pattern and the manifest digest field by field; prints `check=pass`.
- Reproducibility: second generate run into a separate directory: mbc1-8k.gbb rerun=identical, mbc1-32k.gbb rerun=identical (byte-compared with `cmp`).

## Task Commits

1. Task 1 (tracer): 64f9c80 - 8 KiB envelope, generator, manifest, licence
2. Task 2: 8433e7b - 32 KiB envelope and manifest entry

## Deviations from Plan

None - plan executed exactly as written. (Both envelopes were generated in one run; the task 1 commit carried a manifest trimmed to the 8 KiB entry, then task 2 added the full manifest.)

## Verification

- `--check` prints check=pass; sizes exactly 8243 and 32819; manifest has 2 envelopes; home-path grep empty.
- Full `ctest --preset phase1`: 329/329 passed.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED
