# Phase 21: CGB Game Progress and Scene Regressions - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in 21-CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-01
**Phase:** 21-CGB Game Progress and Scene Regressions
**Areas discussed:** CGB harness fallback, progress predicate, CGB observations and scene oracle, scene triage and privacy

---

## CGB harness fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Rely only on an admitted game; if both candidates fail, leave the CGB progress path unproven | Fewer original fixture files, but the new runner path would lack a positive CGB control. | |
| Use a small original native-CGB harness fixture if neither candidate is admitted | Exercises the runner and controls independently; clearly label it as harness evidence, not game evidence. | ✓ |

**User's choice:** Recommended option, adopted under the owner's direction to consider all relevant decisions and follow the coherent recommendation.
**Notes:** The original fixture does not satisfy an admitted-game progress claim. Keep the exact two-candidate limit and preserve the reasoned absence outcome.

---

## Progress predicate

| Option | Description | Selected |
|--------|-------------|----------|
| Stop at the first playable screen | Easier to bound, but a frame alone can pass without meaningful guest progress. | |
| Reach one clear input-driven in-game state change with an independent guest predicate | Distinguishes meaningful input from no-input/wrong-input and stays deterministic. | ✓ |
| Require a larger title-specific checkpoint | More gameplay evidence, but longer runs and candidate-dependent routes add cost without being required by this phase. | |

**User's choice:** Recommended option, adopted under the owner's direction to consider all relevant decisions and follow the coherent recommendation.
**Notes:** Use a bounded scripted action after entering playable state; no long playthrough or game-completion milestone.

---

## CGB observations and scene oracle

| Option | Description | Selected |
|--------|-------------|----------|
| Treat a frame/PCM digest as the expected result for every scene | Simple repeatability check, but cannot independently establish rendering or audio correctness. | |
| Bind digests as observations and add an independent symptom-specific oracle for correctness | Keeps repeatability distinct from accuracy; static and dynamic symptoms can use different minimal expectations. | ✓ |
| Store raw frame sequences/clips in CI for review | Easier human inspection, but increases artifact/privacy costs and is not an automated correctness oracle by itself. | |

**User's choice:** Recommended option, adopted under the owner's direction to consider all relevant decisions and follow the coherent recommendation.
**Notes:** A fault-specific negative control is required. Existing DMG visual/audio gates do not silently become CGB game criteria.

---

## Scene triage and privacy

| Option | Description | Selected |
|--------|-------------|----------|
| Require owner play and a full reproduction package before triage | Raises the evidence bar but conflicts with the no-mandatory-owner-play contract. | |
| Accept title/scene/symptom, then let the agent recover metadata and reproduce; use private media locally only if explicitly provided for that investigation | Keeps intake light and sensitive media out of Git/public CI; automate later with original/admitted fixtures. | ✓ |
| Turn any repeatable screenshot/digest into a golden regression | Fast, but risks preserving a rendering bug or animation phase as the expected output. | |

**User's choice:** Recommended option, adopted under the owner's direction to consider all relevant decisions and follow the coherent recommendation.
**Notes:** Classify core, conversion, host, original behavior, or unknown. If independent expectation or a useful reproducer is unavailable, retain the blocker as triage rather than force a regression.

---

## the agent's Discretion

- Select the smallest original CGB fixture and independent predicate.
- Choose bounded checkpoint timing and run budget for the selected route.
- Keep a report in triage where source, rights, or oracle evidence is insufficient.

## Deferred Ideas

No new ideas were added. Third-candidate search, Libretro/Steam Deck qualification, Phase 22 diagnostics, and Phase 23 release work remain outside this phase.
