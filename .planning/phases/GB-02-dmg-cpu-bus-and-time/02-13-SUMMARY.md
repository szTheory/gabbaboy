---
phase: GB-02-dmg-cpu-bus-and-time
plan: 13
subsystem: testing
tags: [mooneye, wla-dx, fixture-reproduction, cross-host]
requires:
  - phase: GB-02-07
    provides: Three pinned Mooneye ROMs and immutable source/tool/font provenance
provides:
  - Pinned all-case reproduction and bounded per-byte mismatch artifacts
  - Exact hosted evidence isolating WLA-DX section ordering as the cross-host divergence
affects: [GB-02-corpus, CPU-05, T-02-14]
actuals:
  tokens: 4324
  tasks: 2
  commits: 2
commits: 2
plan_head_before: 257bc7b39bb3706f0e7dfd48731d39eb98e5d23d
plan_head_after: 95fdabac8c6b41a43ea2b4877cf1f59b41ed63d4
tech-stack:
  added: []
  patterns: [Explicit networked fixture preparation outside ordinary CTest, all-case byte comparisons]
key-files:
  created: [tests/scripts/reproduce-mooneye.sh]
  modified: [.github/workflows/fixture-repro.yml, fixtures/mooneye/SOURCES.md]
key-decisions:
  - Keep checked-in ROMs and the three-case denominator unchanged until a deterministic cross-host linker recipe is qualified.
  - Leave T-02-14 and verification gap 7 open after exact hosted compare failure.
requirements-completed: []
duration: 8min
completed: 2026-10-06
status: complete
---

# Phase GB-02 Plan 13: Mooneye Reproduction Summary

**All three ROMs now have pinned local and hosted byte reports; WLA-DX's tied-section ordering causes cross-host payload differences, so fixture qualification remains open.**

## Accomplishments

- Added a single explicit preparation script that verifies pinned suite and tool revisions/trees, WLA-DX archive and versions, original replacement-font generator and generated font digests. It builds DAA and both timers, retains both ROMs and symbols, and reports every changed byte plus a first-difference window. `--diagnose` returns success after complete mismatch reporting; `--compare` fails on any byte or digest mismatch.
- The separate hosted workflow invokes `--compare` and retains bounded per-case evidence. Ordinary CTest still uses checked-in bytes without preparation network access.
- Compared local macOS/arm64 and exact-revision hosted Linux/x86_64 results. Source, tool, font and flags match; pinned `wlalink/write.c` `_sections_sort` returns `-1` for equal priority/size sections and is passed to `qsort`. Retained symbol maps show tied sections swapping addresses. Payload and checksum bytes differ across hosts.

## Task Commits

1. Task 1 — diagnose every reproduced byte difference: `6afd54b` (`feat`).
2. Task 2 — investigate the proven recipe difference and record its open gate: `95fdaba` (`docs`).

## Verification Evidence

At source `95fdabac8c6b41a43ea2b4877cf1f59b41ed63d4`, `bash tests/scripts/reproduce-mooneye.sh --compare fixtures/mooneye` passed on local Darwin/arm64 for all three 32,768-byte ROMs. The exact-revision [hosted run 37548730397](https://github.com/szTheory/gabbaboy/actions/runs/37548730397) built all three and failed the comparison on Linux/x86_64, with downloadable ROM pairs and all-offset reports. The original tracer fixture job passed in that run. `bash -n` and `git diff --check` passed.

| ROM | Manifest and local SHA-256 | Hosted rebuilt SHA-256 | Changed bytes |
|---|---|---|---:|
| DAA | `96cd0e02a85f6f035b1c1947d36a8ad2d8e51963f636b833f05559f021eef57e` | `262f110744705dc4ee0f4b42473dd1e260c2dace8f999117a540a1e33c19de87` | 83 |
| tim00 | `6edc430a09522294c96d1eef63a0f1a99078f4401060980048ec5a68640e11bd` | `a006ae787a76f90c7040c901940af5a112436f1d2c03b7f086d7d528b3e6288e` | 209 |
| tim00_div_trigger | `468d426c4fe6a850a28f4116bd127d471be6adf2ef5dd0f89f2db67ffe212242` | `a6b8b1c3387acbb251111f9e4fa0936e7646d666b6963194885e290d6431d0b5` | 209 |

All first differences are at offset 334. DAA offset 335 is `9e` checked-in and `2a` hosted. DAA also differs at payload offset 488 and later; each timer first differs in payload at 18423. These are not checksum-only variations. The pinned inputs are Mooneye `31510e12eea6286d36eea060a6adde755e1067aa` / tree `2b8c52424a49a2a7466cf631fd8992c53d0de2fa`, WLA-DX `91c52b1f4ef3cc8ba3c0638f7536539579af6a9f` / tree `8495d61b96847950e65b1809bf9c7daaccdbd20b` / archive SHA-256 `24a95d77a79feeb70d1de87d66749c006e37337308ce9c00e44efac4c46ab976`, and generated font SHA-256 `23ba65cb93433b65e7ddcae5f8a7dd2ca232491793848644e625875c6dd6ae43`.

## Deviations from Plan

Task 2 could not establish a byte-identical deterministic linker command within the declared source/tool/fixture boundaries. The observed WLA-DX comparator violates the `qsort` ordering contract; adding a tie rule or using `-nS` changes section layout and requires a separately reviewed tool recipe and fixture qualification. No ROM, manifest digest, eligibility, or denominator was changed. The requested successful cross-host comparison remains unmet; this plan records the failing gate rather than accepting unexplained output.

## Open Issues

- T-02-14 and verification gap 7 remain open. CPU-05 is not complete, and corpus admission is halted. Phase GB-02 remains executing. T-02-15's unsupported-LY reporting path is separate and also open.
- The next gap work must qualify a deterministic linker rule or an appropriately re-qualified fixture set with rights and exact cross-host byte evidence. Phase 3 — Visible Interactive DMG — remains paused.

## Self-Check: PASSED

The three declared files exist; task commits `6afd54b` and `95fdaba` are ancestors of HEAD; no fixture ROM or manifest bytes changed. The exact hosted artifact contains all three comparison reports and ROM pairs.
