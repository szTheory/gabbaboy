# Phase 14 — UI Review

**Audited:** 2026-10-15  
**Revision:** `e6125120134baaef42b394690dd47bc274e1f5ed` (phase base `261c660`)  
**Baseline:** No UI-SPEC.md; phase UI safety gate reports `frontend=false`, `hasUiFiles=false`, `block=false`.  
**Screenshots:** Not captured; this phase changed player limitation copy, with no frontend or layout files.  
**Interaction captures:** off (workflow.ui_interaction_capture is false)

## Scope

The player-facing change in scope is the CGB digital DAC limitation sentence in `src/player/limitations.h`. The surrounding product and support copy was checked for the same software-model, compatibility-mode, hardware, analog-audio, and game-compatibility boundaries. No control, flow, layout, or visual style changed, so this review does not assign visual scores or claim perceptual or hardware evaluation.

## Pillar Assessment

| Pillar | Assessment | Evidence |
|--------|------------|----------|
| 1. Copywriting | 3/4 | The new sentence preserves the CGB-CPU-E software-model and DMG playback boundaries. The exact-string `player_limitations` check is stale and fails against the changed text. |
| 2. Visuals | N/A | No frontend files, hierarchy, icons, or layout changed; the phase UI safety gate has no UI block. |
| 3. Color | N/A | No UI color or style changes; there is no visual surface change to score. |
| 4. Typography | N/A | No UI typography changes; there is no visual surface change to score. |
| 5. Spacing | N/A | No layout or spacing changes; there is no visual surface change to score. |
| 6. Experience Design | N/A | No interaction, task flow, or UI state behavior changed; this audit covers copy only. |

**Overall:** N/A (one applicable pillar scored; no `/24` aggregate is reported).

## Priority Fixes

1. **Refresh the exact player limitations expectation** — player-enabled validation currently fails even though the new copy states the intended boundary — update `tests/player/test_limitations.c` to include the FF76/FF77 clause, or replace the full-string comparison with assertions for the stable required claims.

No additional copy or UI fix is supported by the changed scope.

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- **WARNING — stale copy assertion:** `src/player/limitations.h:5` now says CGB-profile playback still uses the DMG APU model, while native CGB guest reads on the CGB-CPU-E software model expose FF76/FF77 digital DAC inputs and compatibility mode reads `$FF`. This keeps register observations distinct from player playback and does not claim physical CGB-E or analog qualification. However, `tests/player/test_limitations.c:7-8` still expects the pre-change exact string. Compiling and running that existing test against the current header exited 1 with `player limitation text differs from the supported preview claim`. Update the expected copy or make the contract assertion phrase-based so this check tracks the supported claims without duplicating the whole paragraph.
- The configured `build` has no `test_player_limitations` target, so the CTest target could not be invoked there; the existing test source was compiled and executed directly. The other focused copy contracts passed: `python3 -I tests/scripts/verify-cgb-corpus-claims.py --self-test` accepted the current static claims (107 cases, 31 gates, 70 APU sources) and all 15 negative controls; `python3 -I tests/scripts/verify-cgb-hdma-claims.py` passed across 8 surfaces. The corpus controls include omitted compatibility/analog limits, false hardware claims, and xfail-inflated counts.

### Pillar 2: Visuals (N/A)

No changed frontend component or visual composition is in scope. No screenshot was captured or used as evidence.

### Pillar 3: Color (N/A)

The changed file contains product copy only; no color tokens or visual styles changed.

### Pillar 4: Typography (N/A)

The changed file contains product copy only; no type styles changed.

### Pillar 5: Spacing (N/A)

The changed file contains product copy only; no layout or spacing changed.

### Pillar 6: Experience Design (N/A)

No interaction, loading/error/empty state, destructive action, or task flow changed. Physical CGB-E, analog/perceptual audio or color, real IR peers, and game acceptance remain outside the software-copy claims and were not treated as human checkpoints.

## Files Audited

- `src/player/limitations.h`
- `tests/player/test_limitations.c`
- `tests/player/claims_agree.cmake`
- `tests/player/CMakeLists.txt`
- `tests/scripts/verify-cgb-corpus-claims.py`
- `tests/scripts/verify-cgb-hdma-claims.py`
- `tests/CMakeLists.txt`
- `README.md`
- `docs/preview.md`
- `docs/support/unreleased.md`
- `docs/cgb-profile.md`
- `docs/audio-and-playback.md`
- `docs/cgb-corpus.md`
- Phase 14 plans and summaries `14-01` through `14-13`, plus `14-CONTEXT.md`, `14-EXECUTION.md`, `14-RESEARCH.md`, `14-VALIDATION.md`, `14-SECURITY.md`, and `14-HISTORY-REDACTION.md`.

## Finding Disposition and Fresh Verification

The sole warning is fixed: `tests/player/test_limitations.c` now includes both the explicit analog-output limitation and the native FF76/FF77 versus compatibility-mode clause. The exact-string check is retained, so unintended public-copy changes still fail. The original failed observation above remains part of this audit.

After the fix, the player build was reconfigured and `test_player_limitations` rebuilt. `ctest --test-dir build-player --output-on-failure --no-tests=error -R '^player_(limitations|claims_agree)' --output-junit phase14-copy-review.xml` passed **3/3** checks, including the mutated-copy negative control. The corpus-claims self-test passed all **15** negative controls; the HDMA claims validator passed all **8** surfaces. No warning remains open. The applicable copywriting assessment after remediation is **4/4**; visual pillars and the overall score remain N/A.
