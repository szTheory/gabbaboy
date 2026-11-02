# Phase 21: CGB Game Progress and Scene Regressions - Pattern Map

**Mapped:** 2026-11-01<br>
**Files analyzed:** 8 likely or conditional files<br>
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/runner/acceptance.c` | utility / runner adapter | scripted input and core callbacks; event-driven frame/PCM observations to receipt | `src/runner/acceptance.c:182-220,697-724,952-1015,1063-1089,1174-1193` | exact |
| `src/runner/acceptance.h` (only if case syntax or internal options must change) | model / internal contract | parsed case data to runner call; request-response | `src/runner/acceptance.h:37-56,141-179` | exact |
| `tests/acceptance/cases-cgb-colour.txt` or a sibling CGB progress case file | test data / case manifest | file input to the runner; batch | `tests/acceptance/cases-cgb-colour.txt:4-8` and `tests/acceptance/cases.txt:1-3` | exact |
| `tests/acceptance/inputs/<progress-script>.input` | test data / input stream | time-ordered scripted button events to the runner; streaming | `tests/acceptance/inputs/libbet-tutorial.input:1-50` | exact |
| `tests/acceptance/CMakeLists.txt` | test registration / config | CTest invokes runner/checker and asserts exit/output; request-response | `tests/acceptance/CMakeLists.txt:61-87,658-718` | exact |
| `fixtures/<original-cgb-control>/...` (conditional, only if both candidates are no-go) | fixture / build and provenance input | pinned source and build recipe produce exact ROM bytes; transform | `fixtures/cgb-colour/attr.asm` and `fixtures/cgb-colour/manifest.json:1-45` | strong |
| `tests/scripts/verify-fixture-admission.py` (reuse or extend; a new phase-specific checker is optional) | utility / repository file and Git evidence | manifest, files, notices, and immutable commit to admission result; file I/O | `tests/scripts/verify-fixture-admission.py:601-682,759-808` | exact |
| `docs/game-acceptance.md` | documentation / static reference | evidence and limitations to maintainers; static | `docs/game-acceptance.md:12-30,38-59` | exact |

All analogs above are tracked source files (`git ls-files` confirmed them). Do not add game ROMs to fixture or test paths unless the Phase 20 component-rights and exact-identity gates pass. An original harness ROM is conditional and must remain labeled as harness evidence.

## Pattern Assignments

### `src/runner/acceptance.c` — RGB555 observation and mode-bound progress

**Analog:** The existing shared progress callbacks and independent RGB555 capture path in this file.

`on_after_step` currently refuses a CGB instance before copying a frame, then performs generation checks, digesting, ring-buffer retention, and checkpoint resolution for DMG. Preserve those bounded frame semantics while dispatching the copy operation by the selected frame format.

```c
if (capture_format(instance) == 1u) {
    /* D-43 covers frame-digest cases only; a silent "no completed frame" would hide the gap. */
    st->error = "frame-unsupported-profile";
    return;
}
if (gbb_copy_frame(instance, st->scratch, sizeof(st->scratch), FRAME_PITCH, &info) != GBB_OK) {
    return; /* no completed frame yet (or since reset) */
}
if (info.generation == st->last_generation) return;
if (info.generation != st->last_generation + 1u) {
    st->error = "frame-skipped";
    return;
}
```

Source: `src/runner/acceptance.c:182-199`.

For profile-selected capture, reuse the existing sized `gbb_info` handshake and RGB555 branch. This helper detects the instance profile, so it is a frame-format selector; native-mode acceptance must separately read `gbb_info.mode` after `gbb_load_rom` and require `GBB_MODE_CGB` for the native-CGB case.

```c
info.struct_size = GBB_INFO_SIZE_V1;
if (gbb_get_info(instance, &info) != GBB_OK) return CAPTURE_FORMAT_UNKNOWN;
return info.profile == (uint32_t)GBB_PROFILE_CGB_CPU_E ? 1u : 0u;
```

```c
if (format == 1u) {
    return gbb_copy_frame_rgb555(instance, frame->pixels555, sizeof(frame->pixels555), FRAME_PITCH555,
                                 &frame->info) == GBB_OK;
}
```

Source: `src/runner/acceptance.c:697-703,713-719`. The actual mode values and API contract are declared in `include/gabbaboy/gabbaboy.h:344-396`: `GBB_MODE_CGB = 2`, `GBB_MODE_CGB_DMG_COMPAT = 3`, and `gbb_get_info` reports the loaded ROM mode. Do not equate the profile or header flag with the execution mode.

Keep validation order from `src/runner/acceptance.c:973-1015`: validate the input digest and syntax, validate ROM size and digest, find a predicate bound to that ROM digest, and verify its anchor bytes before creating the guest. Then follow the create/load/configure/drive sequence at `1063-1089`. The receipt pattern at `1174-1193` binds ROM and input hashes, predicate, budget, build/revision, checkpoint digests, rolling frame digest, and PCM observations; add the actual mode there without claiming those digests are correctness oracles.

### `src/runner/acceptance.h` — bounded internal case contract (conditional)

**Analog:** `gbb_case` stores fixed-size paths/digests, declared model applicability, budget, and the predicate name (`src/runner/acceptance.h:37-56`). `gbb_acceptance_options` carries the chosen model and strict raw/expected-failure controls (`141-179`).

```c
char rom[GBB_CASES_MAX_PATH + 1u];
char rom_sha256[65];
uint32_t rom_size;
char input_script[GBB_CASES_MAX_PATH + 1u];
char input_sha256[65];
uint64_t budget_half_dots;
char model_pass[GBB_CASES_MAX_MODELS][GBB_CASES_MODEL_LEN + 1u];
char model_fail[GBB_CASES_MAX_MODELS][GBB_CASES_MODEL_LEN + 1u];
char predicate[49];
```

Only change this internal contract if the existing case format cannot express the needed predicate or applicability. Native execution mode can be queried and recorded within the runner; do not add or change the public core ABI for this phase.

### CGB progress case and deterministic input script

**Analogs:** `tests/acceptance/cases-cgb-colour.txt:4-8` declares CGB-specific frame cases and the currently expected progress refusal. `tests/acceptance/cases.txt:1-3` shows progress cases bound to exact ROM bytes, a named predicate, script path/digest, fixed budget, and model pass/fail. The current refusal control must be updated when CGB progress is supported; replace it with a negative that reaches and fails the intended predicate, rather than preserving an obsolete unsupported result.

**Input analog:** `tests/acceptance/inputs/libbet-tutorial.input:1-50` uses `gbinput 1`, master-timeline waits, named checkpoint marks, and explicit taps. Follow its syntax and digest binding; choose only the shortest meaningful route allowed by the phase context.

### `tests/acceptance/CMakeLists.txt` — positive and fault-specific controls

**Analog:** Existing acceptance CTests use a shared exit assertion helper and assert both expected code and output. Current CGB case registrations are at `658-718`; the progress refusal at `715-718` is the behavior being replaced.

```cmake
gbb_add_acceptance_exit(acceptance_cgb_colour_excluded_dmg 4
  "status=excluded reason=unsupported-model model=dmg-cpu-b" 30
  "--acceptance;${GBB_CGB_COLOUR_CASES};--case;cgb-colour-hblank;--model;dmg-cpu-b")
```

Source: `tests/acceptance/CMakeLists.txt:699-701`. For negative cases with richer controls, `gbb_add_negative` asserts a precise error and forbids any pass/fail/unsupported status before guest execution (`69-79`). For progress controls, follow the paired raw-verdict/strict expected-failure precedent at `147-158`, and assert the intended predicate or mode reason so setup errors cannot masquerade as a valid negative.

### Conditional original fixture and candidate provenance

**Analog:** The original CGB colour fixture documents authored source, a pinned assembler and build recipe, and per-ROM size/digest (`fixtures/cgb-colour/attr.asm:1-17`; `fixtures/cgb-colour/manifest.json:1-45`). Use that shape if an original native-CGB harness fixture is needed after both candidate no-go decisions. Its independent guest predicate must be source-derived; the frame digest remains an observation only.

For a third-party fixture, use the Phase 20 record contract rather than copying the older Libbet manifest schema. `tests/scripts/verify-fixture-admission.py` requires an approved, reviewed record and exact `repository`/`public_ci` scope (`601-644`), bounded exact inputs/build tools (`646-682`), component-by-component file coverage (`684-740`), and an immutable admission commit plus exact manifest/file/notice bytes (`759-808`). A candidate that cannot pass rights or source/build identity is a recorded no-go, not an admitted fixture manifest.

### `docs/game-acceptance.md` — evidence classes and absence path

**Analog:** The existing CGB evidence section separates candidate outcome, harness evidence, and physical/perceptual limits (`docs/game-acceptance.md:12-20`); the acceptance and controls sections distinguish predicate success from frame/PCM observations (`22-59`). Update the current CGB outcome from actual Phase 21 records. State the selected profile and API-reported mode, candidate dispositions, harness-only evidence where applicable, and limitations. Do not turn a digest, screenshot, test-ROM pass, or unverified rights label into an accuracy, compatibility, or legal-clearance claim.

## Shared Patterns

### Validate identity and bounds before guest creation

**Sources:** `src/runner/acceptance.c:973-1015` and `src/runner/acceptance.h:22-29,63-84`. Keep paths, case sizes, script sizes, and ROM sizes bounded. Validate input syntax/digest, ROM identity, and predicate anchors before `gbb_create`; ensure malformed-input negatives assert that no guest status line was emitted.

### Bind actual results; keep expected behavior independent

**Sources:** `src/runner/acceptance.c:1174-1193`, `tests/acceptance/cases-cgb-colour.txt:1-8`, and `docs/game-acceptance.md:53-59`. Receipts bind reproducible observations. For scene regressions, derive expected behavior from source, a documented semantic invariant, or an independent reference; add a control that targets that exact behavior. A progress no-input control does not validate a scene oracle.

### Separate fixture admission from package exclusion

**Sources:** `tests/scripts/verify-fixture-admission.py:601-808`, `cmake/VerifyFixtureManifest.cmake:1-30`, and `cmake/ScanForbiddenFixtures.cmake:1-21,65-95,106-162`. Repository fixture permission, exact-byte verification, and package exclusion are separate checks. Preserve all three boundaries for any admitted candidate; do not add fixture bytes to installed or release products.

## No Analog Found

No current project file records a reproducible GabbaBoy scene defect with an independent expected behavior. Research found only candidate scene leads and historical observations. If no actionable report can be reproduced with an independent oracle and targeted negative control, retain the intake as unresolved triage rather than creating a report-specific golden.

## Metadata

**Analog search scope:** `src/runner/`, `include/gabbaboy/`, `tests/acceptance/`, `tests/scripts/`, `fixtures/`, `cmake/`, and `docs/`.<br>
**Files scanned:** 12 tracked analogs plus the Phase 21 context and research documents.<br>
**Pattern extraction date:** 2026-11-01
