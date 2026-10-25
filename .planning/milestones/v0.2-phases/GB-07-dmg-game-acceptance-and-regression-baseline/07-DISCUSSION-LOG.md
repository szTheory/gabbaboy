# Phase 7: DMG Game Acceptance and Regression Baseline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-10
**Phase:** 07-dmg-game-acceptance-and-regression-baseline
**Areas discussed:** Libbet admission form; Progress predicate + input script; Runner/manifest evolution; Baseline freeze + player smoke

**How the decisions were made:**
- The owner selected all four areas and attached their generic fan-out instruction: deep multi-lens research per decision, an adversarial pass, coherent one-shot recommendations auto-followed, and "another copy and paste is better than another dep".
- Each area was researched by a parallel advisor researcher at the minimal_decisive calibration tier, with multi-lens and adversarial instructions.
- The four recommendations were reconciled into one coherent set. Nothing was asked area by area.

---

## Libbet admission form

| Option | Description | Selected |
|--------|-------------|----------|
| (a) Vendor release binary only | Digest-pinned bytes; provenance asserted, not shown | |
| (b) Rebuild from source in required CI | Strongest provenance; puts Pillow and RGBDS 0.7.0 into the required path | |
| (c) Vendor binary + opt-in rebuild that must match | Required CI verifies bytes and rights; a separate non-required job proves reproduction | ✓ |

**Choice:** (c), auto-followed recommendation. The researcher rebuilt commit 46a765a with RGBDS 0.7.0 and Pillow 12.3.0, and the result was byte-identical to the release asset. RGBDS 1.0.1 fails to build that commit.
**Notes:** The LICENSE and README credits disagree, so the discrepancy and Korth's porting permission are recorded as limitations. Fallback rule: stop and report; no in-phase game swap.

## Progress predicate + input script

| Option | Description | Selected |
|--------|-------------|----------|
| A. Guest-state predicate + master-timeline event script + paired controls | Tutorial floor fully scored, not in attract mode, held 2 frames | ✓ |
| B. Frame-digest / screenshot acceptance | Blind to attract mode and circular | |

**Choice:** A, auto-followed. Measured false positives drove the choice: score-only passes in attract mode; overlaid cursor variables; DC PCM on the title screen; a floor-exit gate that depends on the layout.
**Notes:** Two in-phase investigations were added before the baseline freeze: possible mixer saturation, and the early-Start-tap anomaly.

## Runner/manifest evolution

| Option | Description | Selected |
|--------|-------------|----------|
| A. Extend compiled table only | No parser; logic and data mixed | |
| B. C JSON-subset parser | Large parser surface, schema drift | |
| C. Hybrid: compiled Mooneye table + line `key=value` case file; JSON for provenance only | Small bounded parser, diff-friendly | ✓ |
| D. Compiled table + data file for input scripts only | Splits a fixture across two places | |

**Choice:** C, auto-followed.

**Reconciled conflicts:**

| Topic | Proposed by | Adopted | Why |
|-------|-------------|---------|-----|
| Input time base | Runner research: absolute-frame input format | Predicate research's master-timeline event grammar | Frame counts drift while the LCD is off |
| Frame hashing | Predicate research: raw shade bytes | Canonical `GBB-RGB888-v1` digest everywhere | One definition serves EVID-01 and EVID-02 |
| Predicate location | Researchers differed | Named compiled predicate referenced from the case file | Avoids an expression language in the parser |

## Baseline freeze + player smoke

| Option | Description | Selected |
|--------|-------------|----------|
| Baseline A1: text ledger + one checker script + CTest wrapper | Diffable, no parser | ✓ |
| Baseline A2: JSON ledger | Needs jq/python in the check | |
| Baseline A3: digests scattered in tests | No single identity report | |
| Baseline A4: compare with previous CI run | No frozen reference | |
| Player B1: extend `--smoke-package` with `--input-script` under SDL dummy drivers | Exercises the real packaged binary | ✓ |
| Player B2: session-level test only | Doesn't exercise the package | (kept as complement) |
| Player B3/B4: OS input injection / Xvfb | New dependencies, flaky | |

**Choice:** A1 + B1, auto-followed.
**Notes:**
- Inventory identity is a monotonic superset.
- Benchmarks are advisory.
- Digests must match on all three OSes.
- The approved-change protocol requires a CHANGES.md entry with old and new digests for every changed ledger line.
- The player smoke stays on macOS only, because it is the only packaged player.

## Claude's Discretion

- Runner source-file split and helper names.
- Verifier placement.
- PCM threshold calibration.
- Wave ordering.

## Deferred Ideas

- Linux and Windows packaged-player smoke.
- Mooneye table migration.
- The `fibonacci-ldbb`, `screen-text` and `rtc_policy` oracles.
- A benchmark threshold.
- Promoting `libbet-repro` to a required check.
- Tobu Tobu Girl after G2 clears.
- Independent-emulator cross-checks, kept private and local.
