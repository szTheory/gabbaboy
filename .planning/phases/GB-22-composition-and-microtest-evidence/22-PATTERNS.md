# Phase 22: Composition and Microtest Evidence - Pattern Map

**Mapped:** 2026-11-02  
**Files analyzed:** 14 file responsibilities (some names/locations remain for the planner to choose)  
**Analogs found:** 12 / 14 (10 exact or near-exact role matches; 2 areas have no close implementation analog)

## File Classification

| New/Modified File or Responsibility | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/acid2/manifest.json` | config | file-I/O / transform inputs | `tests/acid2/manifest.json` | exact baseline to extend |
| Acid2 text-cell allowlist and generated mask/overlay (new; final paths TBD under `tests/acid2/`) | config / utility output | transform | `tests/acid2/manifest.json`; `tests/scripts/run-acid2-local.py` | partial; no source-layout mask generator exists |
| Project-authored replacement glyph source and identity record (new; path TBD) | test fixture/source | transform | `fixtures/visible-demo/demo.asm` and its manifest | partial; no glyph-substitution analog |
| `tests/scripts/run-acid2-local.py` | utility | file-I/O, transform, request-response subprocess | same file; `tests/scripts/run-acid2-local.py` | exact baseline to extend |
| `tests/external/gbmicrotest-inventory.json` (suggested path; final name TBD) | config / model inventory | batch | `tests/external/cgb-corpus-inventory.json` | role-match |
| `tests/scripts/verify-gbmicrotest-inventory.py` (suggested name; final name TBD) | utility / checker | batch, file-I/O | `tests/scripts/verify-cgb-corpus-inventory.py` | exact role/data-flow match |
| New source/ROM/component-rights records for admitted fixtures (location depends on the rights gate) | config / manifest | file-I/O, batch | existing `fixtures/*/manifest.json` records checked by `tests/scripts/verify-fixture-admission.py` | role-match |
| `tests/scripts/verify-fixture-admission.py` | utility / checker | file-I/O, batch | same file | exact baseline to extend |
| `cmake/FixtureAdmissionPolicy.json` | config | file-I/O / product inventory | same file | exact |
| `cmake/ScanForbiddenFixtures.cmake` | utility / package checker | file-I/O, batch | same file | exact |
| `tests/CMakeLists.txt` | config / test registration | request-response | existing corpus, fixture-admission and acid2 registrations in the same file | exact |
| `THIRD_PARTY_NOTICES.md` | documentation / rights index | transform | same file | exact baseline to update |
| `docs/cgb-profile.md` | documentation / evidence labels | transform | its existing acid2 section; `docs/cgb-corpus.md` evidence wording | exact baseline to update |
| `docs/cgb-corpus.md` | documentation / corpus accounting | batch / transform | same evidence contract | exact |

Paths marked TBD are not locked in CONTEXT.md or RESEARCH.md. Keep upstream bytes out of the repository and products unless the component-level rights gate is explicitly cleared. The Phase 20 verifier and product policy remain the admission boundary.

## Pattern Assignments

### Acid2 manifest and local comparator (`tests/acid2/manifest.json`, `tests/scripts/run-acid2-local.py`)

**Analogs:** `tests/acid2/manifest.json`; `tests/scripts/run-acid2-local.py`

The current manifest binds each upstream release, ROM/reference asset, byte size, digest, profile, and color conversion separately. Its two entries are at [manifest lines 7-21 and 23-37](tests/acid2/manifest.json).

**Pinned-byte read pattern** (`tests/scripts/run-acid2-local.py`, lines 32-53): read once, check the digest, and return those same bytes to the consumer.

```python
def read_pinned(path: pathlib.Path, pin: str, what: str, limit: int = 1 << 20) -> bytes:
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
    except OSError as exc:
        raise Refused(f"unreadable input ({exc.__class__.__name__})")
    if len(data) > limit:
        raise Refused("file too large")
    if hashlib.sha256(data).hexdigest() != pin:
        raise Refused(f"{what} sha256 not pinned")
    return data
```

**Exact comparison pattern** (lines 168-172): the pass condition is equality over every compared pixel, with a count on mismatch.

```python
def compare(frame, reference) -> tuple[int, str]:
    differing = sum(1 for a, b in zip(frame, reference) if a != b)
    if differing == 0:
        return 0, "acid2 result=match"
    return 1, f"acid2 result=differs pixels={differing}"
```

The current `self_test()` exercises a synthetic PNG round trip, an exact frame, a one-pixel difference, a refused fake ROM, and return of the pinned bytes ([lines 195-235](tests/scripts/run-acid2-local.py)). Extend this pattern so the one-pixel mutant is outside the text mask, and add a broadened/altered-mask mutant plus ROM, reference, allowlist, and generated-mask identity mutants. Preserve the runner's distinction between refusal, harness error, and image mismatch (`main`, lines 253-276).

**Mask-specific boundary:** add mask membership to the comparator, but keep the upstream image as the immutable oracle and retain exact comparison for all unmasked pixels. Masked-cell counts and the minimum remaining comparison area must be bounded before comparison. The local code has no source-to-screen tile mapping generator; use RESEARCH.md's pinned upstream source/layout discussion for that derivation.

### Text-cell allowlist, generated mask/overlay, and replacement glyph source

**Closest local analog:** the manifest identity pattern above, not an existing mask implementation.

Store a readable allowlist bound to the exact source/layout revision. Generate the fixed-size bitmap and review overlay from that allowlist rather than accepting an independently edited mask. Record hashes for the allowlist and generated outputs beside source/layout, derivative ROM, and unchanged reference-image identities. Keep glyph-source identity separate from the pixels removed from the comparison claim.

No local code maps upstream object/window tile cells into exact image coordinates, or independently verifies the authored replacement glyphs. The mask generator and glyph-source review therefore need new phase-specific rules; the PNG decoder's fixed 160x144 bound in `run-acid2-local.py` (lines 78-103) is only a size/layout precedent.

### `gbmicrotest` roster, per-case applicability, and accounting

**Analogs:** `tests/scripts/verify-cgb-corpus-inventory.py`; `tests/external/cgb-corpus-inventory.json`; `tests/acceptance/cases-cgb-colour.txt`; `tests/acceptance/CMakeLists.txt`

**Immutable source and roster checks** (`verify-cgb-corpus-inventory.py`, lines 120-155):

```python
def check_tree_pins(data: dict) -> None:
    trees = data.get("source_trees")
    need(isinstance(trees, dict) and set(trees) == set(SUITES), "source-tree-set")
    for suite, (commit, tree) in PINS.items():
        row = trees[suite]
        need(row.get("commit") == commit and row.get("tree") == tree, f"source-pin:{suite}")

def check_rosters(data: dict) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    sources = data.get("source_candidates")
    outputs = data.get("outputs")
    cases = data.get("cases")
    need(isinstance(sources, list) and len(sources) <= 300, "source-roster-shape")
    need(isinstance(outputs, list) and len(outputs) <= 300, "output-roster-shape")
    need(isinstance(cases, list) and len(cases) <= 300, "case-roster-shape")
    source_by_id: dict[str, dict] = {}
    output_by_id: dict[str, dict] = {}
    case_by_id: dict[str, dict] = {}

    for row in sources:
        suite = row.get("suite")
        need(suite in SUITES, "source-suite")
        safe_relative(row.get("source_path"), "source-path")
        need(row.get("source_commit") == PINS[suite][0], f"source-row-pin:{suite}")
        need(row.get("id") == f"{suite}:{row['source_path']}", f"source-id:{suite}")
        need(row["id"] not in source_by_id, "duplicate-source-id")
        need(row.get("selection", {}).get("state") in ("required", "excluded"), "source-selection-state")
        need(row.get("selection", {}).get("reason"), "source-selection-reason")
        need(isinstance(row.get("family"), str) and row["family"], "source-family")
        need(isinstance(row.get("applicability"), dict), "source-applicability")
        need(isinstance(row.get("rights"), dict) and row["rights"].get("state") == "clear", "source-rights")
        need(isinstance(row.get("build"), dict) and row["build"].get("toolchain"), "source-build")
        need(isinstance(row.get("oracle"), dict) and row["oracle"].get("class"), "source-oracle")
        source_by_id[row["id"]] = row
```

The full verifier also checks exact per-suite counts and a digest over the named roster (lines 157-180). Copy that identity-first approach: equal aggregate totals must not hide dropped or substituted source names. Bind each row to source path/commit, ROM path/size/digest, verdict protocol, rights decision, upstream reference model, and GabbaBoy execution profile.

The acceptance case format keeps ROM identity, expected-result protocol, model, and work budget on a named row ([`cases-cgb-colour.txt`, lines 1-6](tests/acceptance/cases-cgb-colour.txt)). Its CTest contract uses explicit exclusion reasons and separately checks declared versus undeclared exclusions ([`acceptance/CMakeLists.txt`, lines 124-147 and 167-175](tests/acceptance/CMakeLists.txt)). Use that for model dispositions; don't encode excluded cases as skipped CTests.

Represent eligibility and terminal outcome as separate dimensions: every eligible row must be executed, every ineligible row must have a concrete exclusion reason, and the roster must be fully accounted for. RESEARCH.md identifies that D-03's phrase “disjoint eligible/executed/excluded sets” conflicts with “every eligible case executes”; follow its recommended interpretation rather than asserting eligible and executed are disjoint.

### Component rights and source admission (`verify-fixture-admission.py`, policy, notices)

**Analogs:** `tests/scripts/verify-fixture-admission.py`; `cmake/FixtureAdmissionPolicy.json`; `THIRD_PARTY_NOTICES.md`

`verify-fixture-admission.py` uses strict, bounded JSON parsing and normalized repository-relative paths (`lines 87-117`):

```python
def parse_json(raw: bytes, where: str) -> dict:
    if len(raw) > MAX_MANIFEST_BYTES:
        raise Reject("json-size-limit", where)
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError, Reject) as error:
        if isinstance(error, Reject):
            raise
        raise Reject("json-invalid", f"{where}: {error}") from None
    if not isinstance(value, dict):
        raise Reject("json-invalid", f"{where} must be an object")
    return value

def relative_path(value: object, where: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise Reject("path-invalid", where)
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts) or str(path) != value:
        raise Reject("path-invalid", f"{where}: {value!r}")
    return value
```

The manifest self-test mutates source/build revisions, missing component evidence, public-CI scope, unsafe paths, and notice digests and requires a specific rejection (`lines 1690-1732`). Extend those component-level controls for acid2 and `gbmicrotest`; a license name or digest is not an authorization decision.

`cmake/FixtureAdmissionPolicy.json` is a positive allowlist of exact product file hashes and destinations (`lines 4-20`); preserve its closed product inventory so controlled diagnostic ROMs and references remain absent from binary packages. `THIRD_PARTY_NOTICES.md` binds each admitted fixture to rights, source/manifest digest, ROM digest, and notice digest (table lines 23-37), and states that controlled game/diagnostic material stays out of binary products (lines 11-21). Keep those claims synchronized only after the rights decision is resolved.

### Package exclusion (`cmake/ScanForbiddenFixtures.cmake`, `tests/CMakeLists.txt`)

**Analogs:** `cmake/ScanForbiddenFixtures.cmake`; `tests/CMakeLists.txt`

The package scan reads exact ROM and optional reference size/digest pairs from manifests (`ScanForbiddenFixtures.cmake`, lines 65-95), rejects forbidden path components, follows file symlinks where they expose bytes, and compares actual package bytes (`lines 99-160`). It also checks the exact allowed installed fixture directories (`lines 164-180`). Reuse the actual-tree scan for renamed files; a path-only exclusion is insufficient.

**CTest control pattern** (`tests/CMakeLists.txt`, lines 1355-1370):

```cmake
add_test(NAME cgb_corpus_inventory
  COMMAND "${Python3_EXECUTABLE}" -I
    "${PROJECT_SOURCE_DIR}/tests/scripts/verify-cgb-corpus-inventory.py" --bindings)
set_tests_properties(cgb_corpus_inventory PROPERTIES TIMEOUT 30
  PASS_REGULAR_EXPRESSION "cgb-corpus-inventory pass mode=bindings")
add_test(NAME cgb_corpus_inventory_selftest
  COMMAND "${Python3_EXECUTABLE}" -I "${PROJECT_SOURCE_DIR}/tests/scripts/verify-cgb-corpus-inventory.py" --self-test)
```

The same file registers fixture admission positive/negative controls (lines 1440-1454), package scans and renamed-ROM/PNG mutants (lines 2245-2265), plus synthetic-only acid2 controls (lines 3652-3670). Use isolated synthetic inputs and explicit timeouts; don't put unresolved fixture bytes in required CI.

**Schema compatibility to resolve:** the package scanner currently expects `fixtures[]` rows containing `size_bytes` and `sha256`, with optional `reference` objects. `tests/acid2/manifest.json` instead uses `kinds`, `rom_size`, `rom_sha256`, and `reference_sha256`. Planning should either provide a separately bound package-scan manifest view or deliberately extend the scanner schema; it must keep both ROM and reference-image bytes covered.

### Documentation and evidence labels

**Analogs:** `docs/cgb-corpus.md`; `docs/cgb-profile.md`

The corpus document states the exact evidence class and its limits: “This is software-model evidence only” and it does not qualify physical CGB-E or general compatibility (`docs/cgb-corpus.md`, lines 51-65). The profile's existing acid2 section calls a local match a differential comparison against the upstream image, not hardware evidence, and explains that required CI runs synthetic controls only (`docs/cgb-profile.md`, lines 920-926). Carry the same precision to composition and microtest reports: distinguish upstream expectation, model applicability, GabbaBoy execution profile, run result, and rights status; do not label the new evidence as mode-3 timing or physical-model qualification.

## Shared Patterns

### Bind and consume the same bytes

**Sources:** `tests/scripts/run-acid2-local.py:32-53`; `tests/scripts/verify-fixture-admission.py:87-117`  
**Apply to:** image/reference/ROM inputs, source manifests, generated mask inputs, and package identities.

Bound input size and path syntax, compute the digest over bytes actually read, and pass those bytes onward. Keep path/source identity, byte identity, rights, build reproducibility, expected-result protocol, and model applicability as separate fields and checks.

### Complete named accounting and explicit exclusions

**Sources:** `tests/scripts/verify-cgb-corpus-inventory.py:130-180`; `tests/acceptance/CMakeLists.txt:124-175`  
**Apply to:** every `gbmicrotest` source/ROM pair and its result disposition.

Check the complete source-bound roster, reject duplicate identities, require each eligible row to execute, and require each exclusion to carry a concrete reason. Preserve the upstream CPU-08 statement separately from per-case applicability and the GabbaBoy run profile.

### Package checks inspect real product trees

**Sources:** `cmake/ScanForbiddenFixtures.cmake:65-180`; `tests/CMakeLists.txt:2237-2265`; `cmake/FixtureAdmissionPolicy.json:4-20`  
**Apply to:** installed core and player binary package checks.

Use manifest identities as well as path labels, test renamed fixture bytes, and retain the exact product allowlist. Do not add diagnostic fixture destinations to the product policy.

### Every checker has an automated negative control

**Sources:** `tests/CMakeLists.txt:1355-1370,1443-1454,3652-3670`; `tests/scripts/run-acid2-local.py:195-235`  
**Apply to:** new image-mask and microtest-accounting checks.

Register self-tests/controls with CTest, use Python isolated mode (`-I`) for Python tools, set explicit timeouts, and require a specific failure for each mutant. Acid2 controls should include broadened mask rejection and a one-pixel mismatch outside the mask; roster controls should cover changed identity/model, missing/duplicate cases, unexplained exclusions, and missing executions.

## No Analog Found

| File or responsibility | Role | Data Flow | Reason |
|---|---|---|---|
| Source-derived acid2 text-cell coordinate allowlist and mask/overlay generator | utility / config | transform | No local tool maps upstream object/window tile layout to exact screen cells or validates bounded masking. Extend the fixed-size image conventions in `run-acid2-local.py`, but derive cells from the pinned upstream assembly/layout as RESEARCH.md describes. |
| Original replacement-glyph source and rendering identity | test fixture/source | transform | Existing fixtures do not substitute upstream diagnostic-font data while separately excluding those glyph pixels from an independent oracle. Keep this as original authored content and identify it separately from the image mask. |

## Metadata

**Analog search scope:** `tests/acid2/`, `tests/external/`, `tests/scripts/`, `tests/acceptance/`, `tests/CMakeLists.txt`, `cmake/`, `THIRD_PARTY_NOTICES.md`, and `docs/`.  
**Tracked-source gate:** every named code/document analog was confirmed by `git ls-files -- <path>`; no ignored runtime mirror is referenced.  
**Pattern extraction date:** 2026-11-02
