---
status: testing
phase: GB-03-visible-interactive-dmg
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md, 03-06-SUMMARY.md, 03-07-SUMMARY.md, 03-08-SUMMARY.md, 03-09-SUMMARY.md, 03-10-SUMMARY.md, 03-11-SUMMARY.md, 03-12-SUMMARY.md, 03-13-SUMMARY.md]
started: 2026-10-08T00:52:50Z
updated: 2026-10-09T13:20:39Z
---

## Current Test

[testing: current packaged-window check remains]

## Tests

### 1. 03-01-SUMMARY.md D1
expected: "The production core returns independently checked 160x144 DMG background shade frames through a bounded caller-owned copy."
result: pass
source: automated
coverage_id: D1

### 2. 03-01-SUMMARY.md D2
expected: "Timestamped A press/release toggles and restores the visible tile with equal whole and partitioned execution results."
result: pass
source: automated
coverage_id: D2

### 3. 03-01-SUMMARY.md D3
expected: "The original fixture has explicit MIT rights, bootless profile/protocol metadata, and reproducible pinned-tool bytes."
result: pass
source: automated
coverage_id: D3

### 4. 03-02-SUMMARY.md D1
expected: "Authored frames cover BG/window/sprite maps, palettes, scrolling, clipping, transparency, priority, flips, object size, and the ten-object line limit."
result: pass
source: automated
coverage_id: D1

### 5. 03-02-SUMMARY.md D2
expected: "Guest-visible LCD modes, SCX/window/object transfer penalties, STAT edges, LYC, VBlank, LY wrap, and run partition invariance have independent checks."
result: pass
source: automated
coverage_id: D2

### 6. 03-02-SUMMARY.md D3
expected: "Every asserted timing case is linked to a pinned primary documentation snapshot with CPU-B and electrical-FIFO limitations stated."
result: pass
source: automated
coverage_id: D3

### 7. 03-03-SUMMARY.md D1
expected: "Guest OAM DMA progress, selected source mapping, HRAM execution, and CPU read/write blocking are observable."
result: pass
source: automated
coverage_id: D1

### 8. 03-03-SUMMARY.md D2
expected: "Guest VRAM/OAM reads and writes observe LCD-off and mode 0/1/2/3 access rules around mode transitions."
result: pass
source: automated
coverage_id: D2

### 9. 03-03-SUMMARY.md D4
expected: "Image composition, PPU timing, and scripted gameplay remain separately checked from DMA/access behavior."
result: pass
source: automated
coverage_id: D4

### 10. 03-04-SUMMARY.md D1
expected: "Active-low JOYP row selection, independent instances, atomic queue behavior, equal-time ordering, reset, and partition determinism are covered by finite guest tests."
result: pass
source: automated
coverage_id: D1

### 11. 03-05-SUMMARY.md D1
expected: "The opt-in SDL player copies a completed frame and an injected A press/release reaches the owned demo's deterministic guest result."
result: pass
source: automated
coverage_id: D1

### 12. 03-05-SUMMARY.md D2
expected: "Checked time conversion, stable event ordering, key mapping, repeat handling, pause/resume, reset and focus-loss release recovery are covered."
result: pass
source: automated
coverage_id: D2

### 13. 03-06-SUMMARY.md D1
expected: "ROM replacement and session controls use bounded loading; invalid, oversized, truncated, or unsupported files preserve the current guest while successful replacement resets it."
result: pass
source: automated
coverage_id: D1

### 14. 03-06-SUMMARY.md D2
expected: "Player layouts preserve integer scale, pixel alignment, centering, and undersize handling across native, odd, letterboxed, and high-density drawable sizes."
result: pass
source: automated
coverage_id: D2

### 15. 03-07-SUMMARY.md D1
expected: "Frame-copy success and failure paths preserve output boundaries, stable completed generations, reset invalidation, and per-instance isolation."
result: pass
source: automated
coverage_id: D1

### 16. 03-07-SUMMARY.md D2
expected: "Malformed and over-capacity event batches reject atomically with documented precedence; timestamp ordering and run partition behavior remain stable."
result: pass
source: automated
coverage_id: D2

### 17. 03-07-SUMMARY.md D3
expected: "Relocated C and C++ consumers load the installed fixture, submit timestamped button edges, run the core, and copy a completed frame using public declarations only."
result: pass
source: automated
coverage_id: D3

### 18. 03-08-SUMMARY.md D1
expected: "The authored visible-demo source rebuilds to the exact checked-in 32 KiB ROM with its manifest digest using pinned RGBDS 1.0.1."
result: pass
source: automated
coverage_id: D1

### 19. 03-08-SUMMARY.md D2
expected: "Fixture CI verifies the exact source revision and uploads a small receipt naming the run, RGBDS archive, source SHA, ROM size, and ROM SHA."
result: pass
source: automated
coverage_id: D2

### 20. 03-09-SUMMARY.md D1
expected: "The exact clean source revision builds the optional player with pinned SDL3, runs a nonempty player test inventory, and packages all runtime, fixture, and license files."
result: pass
source: automated
coverage_id: D1

### 21. 03-09-SUMMARY.md D2
expected: "The downloaded exact-head package has matching source, package, SDL, license, and fixture identities and passes an extracted-byte SDL event/guest/frame smoke."
result: pass
source: automated
coverage_id: D2

### 22. 03-11-SUMMARY.md D1
expected: "Player help states that audio and battery-save persistence are not implemented, with exact automated coverage."
result: pass
source: automated
coverage_id: D1

### 23. 03-11-SUMMARY.md D2
expected: "The downloaded preview package consumer rejects absent or contradictory audio and battery-persistence metadata."
result: pass
source: automated
coverage_id: D2

### 24. 03-12-SUMMARY.md D1
expected: "Active FF46 reads and restart writes preserve the latest register value and bounded replacement transfer behavior."
result: pass
source: automated
coverage_id: D1

### 25. 03-13-SUMMARY.md D1
expected: "The guest observes selected JOYP pin falling edges as IF.4, with negative controls, sticky IF, IE independence, event ordering, and partition invariance."
result: pass
source: automated
coverage_id: D1

### 26. 03-13-SUMMARY.md D2
expected: "The guest asserts the D-025 DMA/PPU scan/fetch model, active-DMA access matrix, word boundaries, and same-half-dot tie outcomes."
result: pass
source: automated
coverage_id: D2

### 27. 03-03-SUMMARY.md D3
expected: "D-025 acceptance: DMA/PPU collision behavior is covered by the confidence-qualified deterministic software model, with exact CPU-B behavior explicitly unclaimed."
result: pass
source: evidence-review
evidence: "D-025 supersedes this historical CPU-B-only checkpoint. Plan 03-13's dma_ppu_overlap, dma_ppu_word_boundaries, and dma_ppu_cpu_collision guests pass for the adopted software model; exact physical CPU-B collision behavior remains unmeasured and is not claimed."
coverage_id: D3

### 28. 03-04-SUMMARY.md D2
expected: "D-08's exact DMG-CPU-B JOYP interrupt timing is explicitly retained as an unresolved evidence gate."
result: pass
source: evidence-review
evidence: "Exact DMG-CPU-B sampling remains explicitly unmeasured; the selected falling-edge software contract is implemented and tested under D-025."
coverage_id: D2

### 29. 03-05-SUMMARY.md D3
expected: "The packaged SDL player displays the demo and responds to a mapped key; holding Z darkens the tile and releasing Z restores it."
result: pass
source: user
reported: "yeah when i hold Z keyboard key it changes from a lighter green to a darker green, then back again when i release"
coverage_id: D3

### 30. 03-06-SUMMARY.md D3
expected: "The native window shows the demo and Running/Ready status with controls, and the mapped Z press/release visibly changes and restores the tile."
result: pass
source: desktop-observation
evidence: "The packaged player showed demo.gb, Running/Ready status, and controls. The user confirmed the Z press darkened the visible tile and release restored the lighter green."
coverage_id: D3

### 31. 03-10-SUMMARY.md D1
expected: "DMA collision evidence is limited to source-supported behavior, with unsupported CPU-B outcomes left open."
result: pass
source: evidence-review
evidence: "D-025's DMA/PPU software model is documented and tested; exact CPU-B behavior remains clearly unclaimed."
coverage_id: D1

### 32. 03-10-SUMMARY.md D2
expected: "JOYP threshold and circuit path are traceable while exact CPU-B interrupt timing remains unresolved."
result: pass
source: evidence-review
evidence: "The source trail and selected JOYP software contract are recorded; physical CPU-B threshold/sample timing remains explicitly unmeasured."
coverage_id: D2

### 33. 03-12-SUMMARY.md D2
expected: "DMA evidence records exact pinned assertions, source provenance limits, D-024, and unresolved arbitration boundaries."
result: pass
source: evidence-review
evidence: "Pinned source provenance and unresolved arbitration boundaries are recorded; D-025 permits the source-backed model without a physical CPU-B claim."
coverage_id: D2

### 34. Current packaged preview and live key response
expected: "The current packaged Mac player visibly displays the bundled legal demo; holding Z darkens the target tile and releasing Z restores its lighter shade."
result: pass
source: user
reported: "I see the square go from lighter green to darker green when I press and hold, and back to lighter green when I release."
evidence: "On 2026-10-09, the user confirmed the current packaged GabbaBoy player displayed the bundled demo and the target square darkened while Z was held, then returned to lighter green on release."
coverage_id: VIDEO-04

## Summary

total: 34
passed: 34
issues: 0
pending: 0
skipped: 0

## Gaps

- None. The current packaged preview and live Z press/release behavior were confirmed on 2026-10-09.

## Evidence Notes

- The user opened the visible demo and reported that holding Z changed a tile from light green to dark green and releasing Z restored it.
- The live window used the packaged executable, SDL library, and owned demo fixture in a temporary local macOS app wrapper. The title and status were visible; no product source or dependency changed for the wrapper.
- That observation remains valid for the package tested on 2026-10-08. It does not qualify the current package after subsequent Phase 5 keyboard/event changes; see pending test 34.
- The 2026-10-09 user observation closes test 34 for the package built with the Phase 5 keyboard/event integration.
- Exact CPU-B collision and JOYP sampling measurements remain unclaimed. D-025 supersedes the historical CPU-B-only collision checkpoint with a documented, confidence-qualified deterministic software-model acceptance criterion.
