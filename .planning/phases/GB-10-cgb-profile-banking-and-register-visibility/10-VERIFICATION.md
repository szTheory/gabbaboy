---
phase: GB-10-cgb-profile-banking-and-register-visibility
verified: 2026-10-12T00:00:00Z
status: passed
score: 4/4 must-haves verified
covered_files:
  - ".planning/context/DECISIONS.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-01-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-01-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-02-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-02-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-03-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-03-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-04-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-04-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-05-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-05-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-06-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-06-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-07-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-07-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-08-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-08-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-09-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-09-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-10-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-10-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-11-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-11-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-12-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-12-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-13-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-13-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-14-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-14-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-15-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-15-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-16-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-16-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-17-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-17-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-18-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-18-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-19-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-19-SUMMARY.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-20-PLAN.md"
  - ".planning/phases/GB-10-cgb-profile-banking-and-register-visibility/10-20-SUMMARY.md"
  - "docs/cgb-profile.md"
  - "docs/model-gates.md"
  - "fixtures/cgb-banking/banking.asm"
  - "include/gabbaboy/gabbaboy.h"
  - "src/core/gabbaboy.c"
  - "src/runner/acceptance.c"
  - "tests/expected-tests.txt"
covered_digest: "v3:sha256:ca607084f40593302434d8c9ba14f4a9493e220438e8af238c172f479423a7d8"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 10: CGB Profile, Banking and Register Visibility Verification Report

**Phase Goal:** A caller can select the CGB-CPU-E profile and run CGB software with correct execution mode, post-boot state, VRAM/WRAM banking and model-gated register visibility, without changing DMG output.
**Status:** passed (local evidence at HEAD 798433c; hosted exact-head CI pending, see below)
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Caller selects `GBB_PROFILE_CGB_CPU_E`, probes a ROM, queries model and execution mode; CGB-only ROMs load on DMG with an informational flag; post-boot state has per-field provenance; DMG row byte-identical | VERIFIED | `gbb_probe_rom` and `gbb_get_info` are in `include/gabbaboy/gabbaboy.h` (lines 349, 357). Tests `cgb_profile_*`, `cgb_probe_*`, `cgb_info_*`, `cgb_postboot_*` and `cgb_tables` passed in my run. `cgb_postboot_dmg_pin` and `verify-dmg-baseline.sh` give `baseline status=pass`, rows=0 changes. |
| 2 | Every DMG-specific behavior tagged by model in code and docs; visibility matrix has a passing test per cell; KEY0 locked | VERIFIED | `verify-model-gates.py` run by me: `pass functions=147 gates=76 unknown=40`. 18 self-test mutants plus real-file controls pass under `model_gates*`. `cgb_visibility_*` and `cgb_key0_lock` pass. The `io_visibility` table in `gabbaboy.c` marks KEY0 (FF4C) as locked, reading `$FF`, writes ignored. The decode is gated by `model_is_cgb` (lines 1602, 2000). |
| 3 | VRAM 2x8 KiB, WRAM 8x4 KiB banking; echo follows WRAM bank; model-correct OAM DMA source; original fixtures | VERIFIED | `banking_*` (DMG flat-reference metamorphic test plus echo and DMA mutant controls) and `cgb_banking_*` passed. Original fixture `fixtures/cgb-banking/` has `banking.asm`, `banking-cgb.gb`, `banking-dmg.gb`, a manifest and a LICENSE. Reproduction check is recorded in 10-VALIDATION.md. |
| 4 | Half-dot timeline decision recorded in DECISIONS.md; banking-indirection benchmark shows DMG cost against Phase 7 baseline | VERIFIED | D-070 (half-dot ADR) and D-071 are present in `.planning/context/DECISIONS.md`. `cgb_adr_half_dot_*` passed. `10-BENCH.md` and `10-BENCH.json` record headline medians of 105.6 to 107.3 percent of baseline (advisory; trigger fired; owner decision per D-016). `cgb_bench_ab_*` passed. |

**Score:** 4/4 truths verified, 0 behavior-unverified.

### Own checks run at HEAD 798433c

| Check | Result |
|-------|--------|
| Build `phase1` | up to date |
| Full `ctest --preset phase1` | 541/541 passed (191 s) |
| Subset `^(cgb_\|banking_\|model_gates)` | 130/130 passed |
| `tests/scripts/verify-model-gates.py` | pass, functions=147 gates=76 unknown=40 |
| `tests/scripts/verify-dmg-baseline.sh` | bench=ok, changes=ok rows=0, status=pass |

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CGB-01 | 10-01..10-07 (plan frontmatter, with overlaps) | SATISFIED | Truth 1 |
| CGB-02 | 10-09..10-11 and others | SATISFIED | Truth 2 |
| CGB-03 | 10-08, 10-12, 10-13 | SATISFIED | Truth 3 |

All three IDs appear in plan frontmatter and in REQUIREMENTS.md. No orphaned requirements. REQUIREMENTS.md traceability still reads "Pending" for CGB-01..03. The orchestrator should flip them to Complete when the phase closes.

### Anti-Patterns

Code review disposition (10-REVIEW-DISPOSITION.md): 0 critical, 4 warnings and 4 infos fixed, 1 no-change, 0 open. Each fix has a named test. 10-SECURITY.md: threats_open 0. 10-VALIDATION.md: nyquist_compliant true. No unreferenced TBD/FIXME/XXX blockers were found in my review. I did not run a full marker scan across every modified file.

### Pending items (not gaps in the phase goal)

1. **Hosted CI is not green for the current head.** The remote branch is at 0902058, where hosted CI exists. Local HEAD 798433c has unpushed commits (Nyquist test, security and review docs, review fixes). Per AGENTS.md, remote green must not be claimed for them. They must be pushed and the exact-head checks must pass before merge.
2. **Owner veto items remain open before merge:**
   - `gbb_info` ABI
   - PGB rejection on CGB
   - `gbb_copy_frame` unsupported on CGB
   - DMG FF4C-FF7F fail-closed
   - the benchmark review trigger, which fired at about +6-7 percent (advisory, measured on a loaded host)
   - CGB IE bits 5-7 (D-071)
3. **`phase1-asan` cannot configure on macOS.** Sanitizer evidence relies on the hosted linux-asan-ubsan job, which was green at 0902058 only.
4. **Benchmark attribution is inconclusive.** The cost could not be split between Phase 9 and Phase 10 (10-BENCH.md).

### Human Verification Required

None. Every deliverable has an automated check with a negative control (D-069).

### Gaps Summary

No gaps. The phase goal is achieved in the codebase as measured locally. Merge readiness depends on pushing the head and obtaining exact-head hosted CI, plus the owner veto decisions.

---

_Verified: 2026-10-12_
_Verifier: Claude (gsd-verifier)_
