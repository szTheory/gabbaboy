# Phase 13: CGB HDMA - Pattern Map

**Mapped:** 2026-10-14
**Files analyzed:** 24 target groups (companion paths grouped by responsibility)
**Tracked analog groups found:** 24 / 24 (7 exact, 17 role or partial matches); no exact HDMA scheduler or SameSuite admission analog.

## File Classification

| New/Modified File | Role | Data Flow | Closest tracked Analog | Match Quality |
|---|---|---|---|---|
| `src/core/gabbaboy.c` | model | event-driven, transform | `src/core/gabbaboy.c` | partial: OAM/time seams only |
| `tests/test_cgb_hdma_internal.c` (new) | test | event-driven | `tests/test_cgb_speed_internal.c` | role-match |
| `tests/test_cgb_hdma.c` (new) | test | request-response | `tests/test_cgb_visibility.c` | role-match |
| `tests/test_cgb_hdma_partition.c` (new) | test | transform | `tests/test_cgb_partition.c` | role-match |
| `tests/test_api.c`, `tests/test_cgb_profile.c`, `tests/fuzz_core.c` | test | lifecycle, batch | same paths | role-match |
| `tests/test_cgb_visibility.c` | test | request-response | same path | exact |
| `tests/test_magentests.c` | test | request-response | same path | role-match; existing screen oracle |
| `tests/test_samesuite_hdma.c` (new) | test | request-response | `tests/test_magentests.c` | role-match only |
| `fixtures/cgb-hdma/{hblank.asm, manifest.json, LICENSE.txt, hblank.gb}` (new) | fixture/config | transform | `fixtures/cgb-colour/` | role-match |
| `fixtures/samesuite/{manifest.json, SOURCES.md, ELIGIBILITY.md, LICENSE.txt, selected ROMs}` (new) | fixture/config | batch | `fixtures/magentests/` | role-match; suite admission is new |
| `fixtures/magentests/{manifest.json,SOURCES.md,ELIGIBILITY.md,hblank_vram_dma.gbc}` | fixture/config | batch | same paths | exact |
| `tests/scripts/reproduce-magentests.sh` | utility | batch | same path | exact |
| `tests/scripts/reproduce-samesuite.sh` (new) | utility | batch | `tests/scripts/reproduce-magentests.sh` | role-match |
| `tests/external/cgb-hdma-dispositions.json` and `tests/scripts/verify-cgb-hdma-dispositions.py` (new) | config, utility | transform | `tests/external/cgb-speed-dispositions.json`, `tests/scripts/verify-cgb-speed-dispositions.py` | role-match |
| `cmake/P13Mutants.cmake` (new), `cmake/P12Mutants.cmake`, `tests/test_cgb_speed_internal.c` | utility, test | transform | same P12 paths | role-match |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt` | config | batch | same paths | exact |
| `docs/model-gates.md`, `tests/scripts/verify-model-gates.py` | config, utility | transform | same paths | exact |
| `docs/cgb-profile.md`, `tests/external/cgb-speed-dispositions.json` | config | transform | same paths | role-match |
| `docs/native-integration.md`, `docs/support/unreleased.md`, `docs/preview.md`, `README.md` | documentation | request-response | same paths | role-match |
| `src/player/limitations.h`, `src/player/main.c`, `.github/workflows/preview.yml`, `tests/player/claims_agree.cmake` | config, component, test | request-response | same paths | role-match |
| `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp` | test | request-response | same paths | exact |
| `tests/player/cgb_smoke.cmake`, `tests/player/CMakeLists.txt`, `tests/player/expected-tests.txt` | test, config | request-response | same paths | role-match |
| `CMakeLists.txt`, `cmake/PreviewPackageSmoke.cmake`, `cmake/ScanForbiddenFixtures.cmake` | config, test | batch | same paths | exact; preserve explicit package set |
| `.github/workflows/fixture-repro.yml` | config | batch | same path | role-match |

The HDMA fixture and SameSuite names above are suggested phase paths; finalize them in the plan. Keep the original inline guests self-contained in installed C/C++ tests. Third-party ROMs remain repository test fixtures and stay outside the install allow-list.

## Pattern Assignments

### `src/core/gabbaboy.c` (model, event-driven + transform)

**Analog:** `src/core/gabbaboy.c` (tracked; current mapper, OAM DMA, master-time scheduler and run-loop seams).

**Storage dispatch** (`wram_byte`, lines 1082-1095; `cart_read`, lines 1552-1564):

```c
static const uint8_t *wram_byte(const gbb_instance *m, uint16_t address) {
    unsigned offset = (unsigned)address & 0x1FFFu;
    unsigned bank = offset < GBB_WRAM_BANK_SIZE ? 0u : m->wram_bank;
    return &m->wram[bank][offset & (GBB_WRAM_BANK_SIZE - 1u)];
}
```

HDMA should use emulated addresses and reviewed mapper/WRAM storage paths, then write to the selected VRAM bank through its own transfer semantics. `dma_source_read` at lines 2738-2763 is OAM's source envelope and is only a partial analog; do not reuse it wholesale or route through CPU `read8`/`write8` lockouts.

**Master-time scheduling** (lines 2864-2870, 2953-2956):

```c
static void advance_devices_to(gbb_instance *m, uint64_t target) {
    while (m->time_half_dots < target) {
        ++m->time_half_dots;
        apply_input_events_now(m);
```

The scheduler advances bounded device state one half-dot at a time; OAM currently advances before PPU phase at lines 2953-2955. Preserve the existing order unless a discriminating HDMA collision justifies a narrow change.

**Whole-instruction accounting** (`gbb_run_internal`, lines 4137-4159, 4164-4173):

```c
uint8_t cost = instruction_cost(instance, d);
if (cost > budget_half_dots - result.consumed_half_dots) return result;
if (!audio_preflight(instance, cost)) { result.reason=GBB_STOP_OUTPUT_FULL; return result; }
```

Execution is synchronous; timed bus reads/writes advance devices inside `execute`, then the loop accounts nominal `cost`. There is no resumable CPU instruction cursor. Do not invent one or silently return mid-instruction. The D09 scratch probe records an in-flight HBlank seam, not a selected silicon steal point; use the pending-safe-boundary policy only after the first real-transfer tracer proves budget/time conservation, order, output bounds and partition equivalence.

### New private and public guest tests

**Private analog:** `tests/test_cgb_speed_internal.c` (tracked; white-box seam tests and inline original guest).

```c
#ifdef GBB_P12_CORE_SOURCE
#include GBB_P12_CORE_SOURCE
#else
#include "../src/core/gabbaboy.c"
#endif
```

Its inline CGB guest at lines 114-149 builds a ROM, executes through `gbb_run`, then checks a CPU snapshot and memory. Use that pattern for private HBlank-edge setup and exact hidden-state assertions; do not reuse its speed-switch assumptions. Keep private assertions distinct from guest-visible acceptance.

**Public guest analog:** `tests/test_cgb_visibility.c` (lines 41-59, 92-105) assembles a small program into a ROM and runs the public API; its `keep_io` path saves actual guest reads to HRAM. Use real guest reads of FF55 and guest-visible destination bytes/status. Cover DMG, CGB and compatibility where the visibility contract changes; preserve the phase's CGB-E software-model labels.

`tests/test_cgb_hdma_internal.c` (new, event-driven) should own bounded state/address/time edge cases and the first seam tracer. `tests/test_cgb_hdma.c` (new, request-response) should own original CPU-executed GDMA/HDMA, cancel, HALT/wake and negative-trigger controls. For manually generated ROMs, keep a tiny bounded emitter and checksum helper like `test_cgb_visibility.c:35-60,92-103`.

### `tests/test_cgb_hdma_partition.c` (new, transform)

**Analog:** `tests/test_cgb_partition.c` (tracked, lines 357-428 and 468-520, 609-725).

It copies private instance state for a test-only snapshot, detaches owned buffers, validates ROM identity on restore and explicitly hashes CPU, stalls, DMA, PPU, memory, output streams and event state. For HDMA, add every independent remainder/latch/cursor and VRAM/status observation to the digest; compare one uninterrupted run with bounded cuts around trigger, bytes, block end, cancel and wake. This is a test snapshot, not a save-state format. The existing digest explicitly lists fields: adding state to `gbb_instance` without adding it to the digest weakens the oracle.

### Lifecycle and hostile guest coverage

**Analogs:** `tests/test_api.c:40-64,90-109`; `tests/test_cgb_profile.c:250-268`; `tests/test_loader_matrix.c:8-16`; `tests/fuzz_core.c:145-205`.

```c
REQUIRE(gbb_reset(a) == GBB_OK);
REQUIRE(gbb_peek_ram(a, 0xC000) == 0);
```

Extend lifecycle coverage for reset/new instance/successful load clearing active HDMA, failed replacement preserving active progress, independent instances, zero/tiny budgets, bounded audio/trace, maximum 128-block work and near-`UINT64_MAX` rejection before mutation. Follow the loader matrix's before/after guard and fuzz harness's per-operation budget cap; use fixed hostile FF51-FF55 seeds with reproducible failures. Do not claim a fuzz campaign unless one is run.

### Original fixture, SameSuite and Magen admission

**Original guest fixture analog:** `fixtures/cgb-colour/manifest.json:1-29` binds project-authored assembly sources, per-source hashes, license, assembler version/archive and reproduction recipe. Use the manifest/rebuild identity pattern for an optional visible-player original HDMA guest; keep its evidence and player output predicate structural.

**Magen analog:** `fixtures/magentests/manifest.json:1-9,37-66`, `SOURCES.md:17-46`, `ELIGIBILITY.md:26-44,69-79`, and `tests/scripts/reproduce-magentests.sh:18-34,53-77,81-124` bind source revision, license closure, ROM digests, build options, reproducibility and eligibility. Extend these tracked files for `hblank_vram_dma`; the existing MIT notice is tracked. The selected result is SameBoy-assisted differential evidence, not CGB-E hardware evidence. `tests/test_magentests.c:120-190` is a capture/pixel oracle analog, but Phase 13 must derive explicit data and structural pass predicates plus wrong-bank/no-transfer/HALT controls before trusting a digest.

**No existing SameSuite admission analog:** the four selected cases are exactly `dma/gbc_dma_cont`, `dma/gdma_addr_mask`, `dma/hdma_lcd_off`, `dma/hdma_mode0` at the pinned revision. SameSuite is not vendored. New fixture metadata/rebuild code should copy Magen provenance/reproduction conventions and document the existing X11/CC0 rights basis; do not expand to unrelated `dma/*` cases. Mealybug stays optional, reports `not-run:rights-gate-G1` without authorized bytes, and any result is labeled CGB-C informational evidence.

### Runtime mutants, registration and exact inventories

**Analog:** `cmake/P12Mutants.cmake:151-213` validates each source anchor occurs once and registers a failing mutant beside a mask-zero control. Existing P12 tags such as `P12-M13`, `P12-M14`, `P12-M18`, `P12-M25` are in `src/core/gabbaboy.c`; tests and anchors live in `tests/test_cgb_speed_internal.c` and `tests/CMakeLists.txt:2610-2641`.

Add a small phase-specific HDMA mutant set only for meaningful no/duplicate transfer, wrong bank/count, lost steal, trigger and remainder failures. Preserve/migrate any P12 anchors whose source sites move; keep their positive controls and sensitivity, and retain the P12 stale-row contract. Measure incremental Debug/ASan and mutant-build time; register in existing CTest lanes rather than adding a hosted job by default. A crash or timeout alone is not a detected behavior.

`tests/CMakeLists.txt:703-731` shows fixture digest and named-test registration; `tests/expected-tests.txt:447-460,875-897` is the exact test inventory. Add every new normal, control, fixture and claim-contract CTest name to the inventory.

### Claims, installed consumers and packaged player

**C/C++ consumer analogs:** `tests/consumers/c/main.c:171-253` and `tests/consumers/cpp/main.cpp:354-466` construct self-contained CGB ROMs, run bounded `gbb_run` partitions through the installed public API, and exercise a deliberately unarmed failing twin. Extend both with the same original DMA guest, partition bounds, FF55/data checks and a mutation/failing twin; no HDMA getter or new ABI is needed.

**Package boundary:** `CMakeLists.txt:128-143` has an explicit installed-fixture list; `cmake/PreviewPackageSmoke.cmake:28-44,66-78,91-126` installs, relocates, scans exact fixture directories, then builds/runs external C and C++ consumers. Preserve the closed allow-list for SameSuite and Magen ROMs; inline the consumer guest so no third-party fixture needs packaging. `cmake/ScanForbiddenFixtures.cmake:121-138` checks exact installed fixture children.

**Player smoke:** extend `tests/player/cgb_smoke.cmake` and its existing `tests/player/CMakeLists.txt` registrations only if the original HDMA guest proves a visible result. Keep a guest-derived structural predicate and pair it with the current output digest pattern; avoid creating another UI flow. Track its CTest name in `tests/player/expected-tests.txt`.

**Docs/contracts:** `tests/scripts/verify-model-gates.py:13-19,37-49` enforces source tags against `docs/model-gates.md`; add HDMA tags/rows with explicit CGB/UNKNOWN policy and never erase unresolved silicon limits. `tests/scripts/verify-cgb-speed-dispositions.py:99-129,142-145` ties disposition pins to inventories and the `docs/cgb-profile.md` mirror. Update only Phase 13 rows and the relevant Phase 12 HBlank-across-stall pin, retaining UNKNOWN and CGB-C labels. `tests/player/claims_agree.cmake:20-50` checks shared player/README/preview wording; extend its phrase lists for implementation/support limits. Update native guide, support/preview, README, player help/limitations and preview workflow claims together.

## Shared Patterns

- **Bounded time/output:** preflight budget, audio and trace/diagnostic capacity before mutation; keep DMA time in master half-dots and account every consumed half-dot.
- **Explicit guest/model evidence:** keep private probes, original guest assertions, author ROMs, emulator differentials and hardware evidence labeled separately. No physical CGB-E claim follows from this software model.
- **Negative controls:** pair each important mutant/claim/fixture predicate with a passing positive control and assert the intended failure reason.
- **Fixture and package rights:** pin revision, license notices, size/digest, model/boot applicability and rebuild result. Test fixtures stay out of the installed exact-child set.
- **No new dependency/job by default:** reuse current C17, CMake/CTest, fixture-reproduction, sanitizer, installed-consumer and preview-player lanes; measure runtime before adding more mutation work.

## No Analog Found

| File/Behavior | Role | Data Flow | Reason |
|---|---|---|---|
| HDMA register state, pending visible-HBlank latch and block-steal scheduler | model | event-driven | OAM DMA is nearby but has different source rules and does not implement HBlank/VRAM transfer. |
| `fixtures/samesuite/*` admission and reproducibility | fixture/config | batch | No SameSuite corpus or exact four-case ROM manifest is currently tracked. |
| CGB-E sub-instruction steal point, overflow FF55 status and same-half-dot arbitration | model | event-driven | Current source and software oracles do not establish these hardware edges; keep them UNKNOWN/POLICY. |

## Metadata

**Analog search scope:** core, public/private C tests, fixture admission/reproduction, mutant CMake, CTest inventories, docs/model gates, installed consumers and player/package smokes.
**Tracked-source gate:** all named analog paths were confirmed with `git ls-files`; no runtime mirror paths are used.
**Pattern extraction date:** 2026-10-14.
