# Phase 14: CGB-E Model Qualification and Corpus - Pattern Map

**Mapped:** 2026-10-15  
**Files analyzed:** 19 tracked implementation/configuration path groups, plus the new fixture output sets  
**Analogs found:** 19 / 19 path groups (three use a partial or role-match analog)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/core/gabbaboy.c` (modify) | service/core | event-driven, request-response | `src/core/gabbaboy.c` | exact |
| `tests/test_cgb_visibility.c` (modify) | test | request-response | `tests/test_cgb_visibility.c` | exact |
| `tests/test_apu.c` (modify) or `tests/test_cgb_apu.c` (new) | test | request-response | `tests/test_apu.c`, `tests/test_cgb_visibility.c` | role-match |
| `tests/test_cgb_partition.c` (modify) | test | transform / partitioned execution | `tests/test_cgb_partition.c`, `tests/test_audio.c` | exact |
| `tests/test_age.c` (modify) and/or `tests/test_age_m3.c` (new) | test | file-I/O, transform | `tests/test_age.c`, `tests/test_cgb_hdma.c`, `tests/test_cgb_colour.c` | role-match |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt` (modify) | config / inventory | batch | same files | exact |
| `src/runner/acceptance.c`, `src/runner/cases.c`, `src/runner/main.c` (modify only if the current event rows need stable assertion IDs) | controller / parser | request-response, batch | same files | exact |
| `tests/external/cgb-speed-dispositions.json` (modify) | model-result data | batch | same file | exact |
| `tests/external/cgb-apu-dispositions.json` (new; name is planner choice) | model-result data | batch | `tests/external/cgb-hdma-dispositions.json` | role-match |
| `tests/scripts/verify-cgb-corpus-inventory.py` (new) | utility / validator | batch, file-I/O | `tests/scripts/verify-external-dispositions.py`, `tests/scripts/reproduce-age.sh` | role-match |
| `tests/scripts/verify-cgb-corpus-report.py` (new) | utility / validator | batch, file-I/O | `tests/scripts/verify-cgb-hdma-dispositions.py` | role-match |
| `tests/scripts/verify-age-m3-pixels.py` (new, if kept as a separate PNG oracle) | utility / test | file-I/O, transform | `tests/test_cgb_hdma.c`, `tests/test_cgb_colour.c` | partial |
| `tests/scripts/reproduce-age.sh`, `tests/scripts/reproduce-samesuite.sh`, `tests/scripts/reproduce-mooneye-cgb.sh` (modify) | utility / build | file-I/O, batch | same scripts | exact |
| `fixtures/age/{manifest.json,SOURCES.md,ELIGIBILITY.md}` (modify) and six new m3 ROM/reference-image pairs | config / fixture | file-I/O, batch | existing AGE manifest, eligibility and reproducer | role-match |
| `fixtures/samesuite/{manifest.json,ELIGIBILITY.md}` (modify) and 70 new APU ROMs | config / fixture | file-I/O, batch | existing SameSuite manifest, eligibility and reproducer | role-match |
| `fixtures/mooneye-cgb/{manifest.json,SOURCES.md,ELIGIBILITY.md}` (modify) and five new ROMs | config / fixture | file-I/O, batch | existing Mooneye CGB manifest and reproducer | role-match |
| `fixtures/magentests/ELIGIBILITY.md` (modify) | documentation / admission gate | transform | `fixtures/magentests/manifest.json` | exact |
| `docs/model-gates.md`, `docs/cgb-profile.md`, `docs/audio-and-playback.md`, `docs/native-integration.md`, `docs/support/unreleased.md`, `docs/preview.md`, `README.md`, `src/player/limitations.h` (update claims as behavior changes) | documentation / config | transform | corresponding current docs; `docs/model-gates.md` is the source-gate contract | role-match |
| `.github/workflows/ci.yml`, `.github/workflows/fixture-repro.yml` (modify) | config / CI | batch | same workflows | exact |

The new fixture outputs are build data rather than source modules: five Mooneye outputs (the `daa`, `div_write`, `tim00`, `tim00_div_trigger`, and `vblank_stat_intr-C` inventory rows), all 70 selected SameSuite APU outputs, and six AGE m3 ROMs bound to their six PNG references. Keep their source, output, admission, eligible-case, execution, and assertion counts distinct. The existing four Mooneye and four SameSuite DMA outputs are already admitted. The research inventory is a planning artifact; it must not become a runtime manifest.

The new validator/report helper names above are recommendations because CONTEXT delegates local helper names and the report schema. Keep the inventory validator and result parser as separate checks. Use one execution stream for the receipt and terminal summary.

## Pattern Assignments

### `src/core/gabbaboy.c` (service/core, event-driven request-response)

**Analog:** `src/core/gabbaboy.c` itself; tracked. The table is the existing per-model/per-mode visibility policy, and the CGB read/write path is the timed guest bus boundary.

**Register and mode pattern** (lines 1265, 1293-1298, 1378-1393, 1398-1432):

```c
[0x56] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 14), IOC(CONST_FF), IOS_PANDOCS },
[0x72] = { IOC(DMG_STOP), IOC_ST(0x00, 0xFF), IOC_ST(0x00, 0xFF), IOS_SAMEBOY },
[0x76] = { IOC(DMG_STOP), IOC_DEF(DEFERRED_RW, 14), IOC_DEF(DEFERRED_RW, 14), IOS_PANDOCS },
```

Keep the table’s DMG, CGB-native, and CGB-compat columns explicit. `io_read_cgb()` gates on `model_is_cgb()` and returns the cell’s modeled value; `io_write_cgb()` applies the stored write mask or records the refused bus address for deferred cells. Resolve the three ports through the existing timed read path. Do not infer compatibility visibility from silicon identity.

**APU source-state pattern** (lines 557-563, 2286-2305, 3135-3142):

```c
if (m->apu_wave.enabled && m->apu_wave.level != 0u) {
    const uint8_t packed = m->apu_wave.ram[m->apu_wave.position >> 1];
    const uint8_t digital = (m->apu_wave.position & 1u) == 0u
        ? (uint8_t)(packed >> 4) : (uint8_t)(packed & 0x0Fu);
```

This is the host-mix path and currently reads Wave RAM at the active position. PCM76/77 needs values from channel generator state before NR50/NR51 routing or host PCM conversion. The channel-3 fetch/trigger seam is where the research prototype discriminated a sample latch; preserve the same instance-owned APU state, master timeline, and existing DMG behavior.

### `tests/test_cgb_visibility.c` and CGB APU guest tests (test, request-response)

**Analogs:** `tests/test_cgb_visibility.c` and `tests/test_apu.c`; both tracked. `test_cgb_visibility.c` is the stronger mode analog; `test_apu.c` provides compact in-ROM register operations and explicit cleanup.

**Profile and guest image setup** (`tests/test_cgb_visibility.c`, lines 31-59):

```c
rom[0x143] = v == V_CGB ? 0x80 : 0x00;
if (gbb_create(v == V_DMG ? GBB_PROFILE_DMG_CPU_B : GBB_PROFILE_CGB_CPU_E, &machine) != GBB_OK ||
    gbb_load_rom(machine, rom, 32768) != GBB_OK) {
    gbb_destroy(machine);
    machine = NULL;
}
```

Build actual guests for DMG-native, CGB-native, and CGB-CPU-E compatibility. Reuse `probe()`/`run_cell()` (lines 109-139 and 685-758) for guest reads, repeated writes, refusal atomicity, and expected bus stop addresses. Add FF56/76/77 plus FF72-75 cases to that per-column discipline. `tests/test_apu.c:47-70` demonstrates a small authored guest that writes APU registers, reads them back to WRAM, checks the exact result, and destroys its instance.

For CGB digital invariance, assert PCM values remain equal while guest code changes NR50/NR51 and while host audio buffers are absent, full, or drained. `tests/test_audio.c:117-145` compares one long audio run against partitioned runs; extend the CGB partition coverage in `tests/test_cgb_partition.c` so the new latch and guest-time read survive split budgets and speed edges.

### AGE mode-3 output and image oracle (test, file-I/O / transform)

**Analogs:** `tests/test_age.c`, `tests/test_cgb_hdma.c`, and `tests/test_cgb_colour.c`; tracked.

`tests/test_age.c:131-237` is a bounded ROM runner that computes a row mask and SHA-256 signature from individually checked result bytes; `270-280` prints a compact verdict. Keep assertion rows/signatures stable and separate so a mixed pass/failure case cannot become one passing ROM. For pixel acceptance, `tests/test_cgb_hdma.c:463-495` checks frame availability and every RGB555 pixel against an independent predicate; `498-513` runs a disabled-transfer negative control. `tests/test_cgb_colour.c:515-565` adds source-derived fixture predicates and a frame digest. Apply these to AGE’s six ASM/PNG pairs with an automated pixel comparator; preserve the four normal-speed CGB-E targets, two double-speed siblings, and existing normal/double controls as separate identities.

### Fixture reproduction and admission records (utility/config, file-I/O)

**Analogs:** `tests/scripts/reproduce-age.sh`, `tests/scripts/reproduce-samesuite.sh`, `tests/scripts/reproduce-mooneye-cgb.sh`, plus their tracked manifests.

`reproduce-age.sh:52-72` restricts source/output names, verifies each committed byte count and SHA-256 against its manifest, and refuses missing fixture bytes. `reproduce-samesuite.sh:56-88` runs a Python standard-library checker over exact revision, source closure, license and expected outputs; its pinned rebuild checks the RGBDS archive digest (`434-466`). `reproduce-mooneye-cgb.sh:21-40,74-108,189-216` uses a finite source list, checks frozen parent pins and header mode, builds outside the repository, and compares every output byte to the manifest-bound original.

Extend each existing reproduction path to its selected additions rather than adding an unpinned build lane. Keep the 70 SameSuite APU entries explicit in the manifest and use the pinned RGBDS recipe. For AGE, bind each new ROM to its matching source PNG and digest. For Mooneye, preserve the pinned source/WLA-DX/patch/zero-font flow and register exactly the nine selected cases. MagenTests already has a seventh admitted HBlank ROM; only correct the stale “not vendored” sentence in `fixtures/magentests/ELIGIBILITY.md:40-47,106-107`.

### Inventory and report validation (new Python utilities; batch/file-I/O)

**Inventory analogs:** `tests/scripts/verify-external-dispositions.py` and `tests/scripts/verify-cgb-hdma-dispositions.py`. **Receipt analog:** `tests/scripts/verify-cgb-hdma-dispositions.py`; all are tracked and standard-library only.

`verify-external-dispositions.py:42-64,67-103` checks exact row identity, ownership/reason, a docs mirror, and `git ls-files` so source-only rows cannot masquerade as tracked fixtures. `verify-cgb-hdma-dispositions.py:112-159` cross-checks versioned evidence against manifests, exact CTest names, and `tests/expected-tests.txt`. Its `288-321` mutation list proves rejection of changed revisions, hashes, denominators, test bindings, and missing rows.

Use the same fail-closed shape for the finite source-header/selection check and for the report contract: standard library, bounded input, explicit expected ID sets, precise mismatch reason, and negative controls for omitted/duplicate/unknown rows, narrowed denominators, bad digests, wrong mode/model, truncation, timeouts, changed xfail signatures, and xfail counted as pass. The report adapter should parse one `gabbaboy-runner`/CTest run and emit the concise suite summary plus versioned receipt. Stable assertion IDs and per-row expectations belong to the test contract, not inferred from a green process exit.

### CTest inventory, native CI, and documentation gates (config/documentation)

`tests/CMakeLists.txt:391-404,641-648` registers each native test case under a fixed name; `3233-3386` shows how AGE manifest values produce per-case tests and expected pass/failure regexes. Add each new positive and mutation-control CTest by exact name to `tests/expected-tests.txt`. Existing CGB entries at lines 294-302 and 980-994 show the sorted inventory convention.

`.github/workflows/fixture-repro.yml:188-203` reuses the pinned RGBDS artifact for AGE and SameSuite reproducers and runs tamper controls. Add corpus reproduction there. `.github/workflows/ci.yml:76-101` runs the existing acceptance observations, full CTest, required-test inventory check, and DMG baseline on the native path; add report/inventory checks in that established lane and preserve its paired sanitizer coverage.

`docs/model-gates.md:1-35` defines the source-tag/table contract checked by `tests/scripts/verify-model-gates.py`. When core gates or evidence change, update the table plus the audio/profile/native docs and product limitations together. For all fixture records, keep rights, tool/source hashes, model/mode, evidence class, and observed result separate.

## Shared Patterns

### Guest I/O and model gates

**Sources:** `src/core/gabbaboy.c:1178-1198,1265-1298,1378-1432`; `tests/test_cgb_visibility.c:31-59,685-758`. Use the existing per-column visibility table and real guest accesses. PCM is a pre-mix digital observation; channel sample/fetch state stays in the core instance and advances on the same guest timeline.

### Fixture provenance and finite eligibility

**Sources:** `tests/scripts/reproduce-age.sh:52-72`, `tests/scripts/reproduce-mooneye-cgb.sh:21-40,74-108,189-216`, and `fixtures/*/manifest.json`. Verify the exact pinned source/build inputs and each byte digest. Do not let execution results change the predeclared candidate or eligible denominator. Never emit gitignored runtime mirrors as source analogs.

### Observed results and expected failures

**Sources:** `src/runner/acceptance.c:372-382,1297-1331`; `tests/scripts/verify-cgb-hdma-dispositions.py:112-159,288-321`. A matched expected failure returns evaluator success but stays an xfail in the report. Count suite cases and assertion rows separately and mark a timeout as attempted/incomplete.

### Automated test inventory and CI reuse

**Sources:** `tests/CMakeLists.txt:391-404,3360-3386`, `tests/expected-tests.txt`, `.github/workflows/ci.yml:89-101`, `.github/workflows/fixture-repro.yml:188-203`. Add exact positive and negative test names to the checked inventory and run admission/report checks in existing jobs; retain the one-run report path.

## No Analog Found

| File/data | Role | Data Flow | Reason |
|---|---|---|---|
| New Mooneye, SameSuite APU, and AGE ROM/PNG outputs | fixture data | file-I/O | Binary outputs have no code analog. Copy provenance, hash, rights, and reproduction rules from the tracked suite manifests and scripts instead. |
| `tests/scripts/verify-age-m3-pixels.py` (if created) | image-oracle utility | file-I/O / transform | No tracked PNG-to-pixel comparator was found. Reuse the RGB555 predicate and negative-control structure from `tests/test_cgb_hdma.c`; use the AGE PNG only as the independent expected image. |

## Metadata

**Analog search scope:** `src/core/`, `src/runner/`, `tests/`, `tests/scripts/`, `tests/external/`, `fixtures/{age,samesuite,mooneye-cgb,magentests}/`, `docs/`, `.github/workflows/`  
**Tracked-source check:** all named existing analogs were confirmed by `git ls-files`; new files and upstream ROM/image data are labeled separately.  
**Pattern extraction date:** 2026-10-15
