# Phase 23: Qualified v0.4.0 Release - Pattern Map

**Mapped:** 2026-11-03  
**Files analyzed:** 11 likely created or modified files (including generated release outputs and the version-window record)  
**Analogs found:** 5 reusable pattern groups / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/data/support-claims-v0.4.json` | config | transform | `tests/data/support-claims-v0.3.json` + its validator in `tests/scripts/verify-support-ledger.py` | exact |
| `tests/scripts/verify-support-ledger.py` | utility | batch, transform | same script's immutable-input, renderer, and self-test paths | exact |
| `docs/support/v0.4.0.md` | utility (generated documentation) | transform | `docs/support/v0.3.0.md` | exact |
| `tests/data/release-disclosure.json` | config | transform | existing disclosure input and generator checks in `tests/scripts/verify-support-ledger.py` | role-match |
| `tests/scripts/verify-v02-adoption.py` | utility | batch | `check_release_notes()` and its isolated mutation controls | exact |
| `tests/scripts/verify-version-window.py` | utility | batch | same script's managed-input digest and immutable-commit checks | exact |
| `tests/data/version-window.json` | config | event-driven | current inactive record plus `verify-version-window.py` schema | exact |
| `tests/CMakeLists.txt` | config / test registration | batch | existing ledger, disclosure, and version-window CTests | exact |
| `CMakeLists.txt` | config / generated version output | event-driven | `CHANGELOG.md` and `.release-please-manifest.json` release-please version PR outputs | role-match |
| `.release-please-manifest.json` | config / generated version output | event-driven | current manifest and release-window generated-file contract | exact |
| `CHANGELOG.md` | generated documentation / release notes | event-driven | existing v0.3.0 release entry | exact |

The expected source additions are the v0.4 claims profile and generated ledger. The release-please files are reviewed outputs of the existing version PR. `tests/data/version-window.json` is currently an inactive tracked record; update it only as the existing exact-head review/rehearsal window is opened. No new release workflow is implied.

The Phase 21 candidate records (`tests/data/cgb-candidates/potion-panic.json`, `tests/data/cgb-candidates/ucity-1.3.json`) and Phase 22 diagnostic records are immutable evidence inputs. Do not change their dispositions to make a release claim pass.

## Pattern Assignments

### `tests/data/support-claims-v0.4.json` (config, transform)

**Analog:** `tests/data/support-claims-v0.3.json` (tracked).

Use the same bounded claim shape: each row has a stable ID, requirement references, one statement, model/mode/platform/surface scope, corpus counts, evidence IDs, and explicit non-claims. The existing input's first row shows the shape; the v0.4 profile should express the Phase 21/22 outcomes and preserve the Pending requirements instead of copying v0.3 state claims.

**Input shape** (`tests/data/support-claims-v0.3.json`, lines 2-16):

```json
"applies_from_version": "0.3.0",
"claims": [
  {
    "corpus": [
      {"count": 153, "name": "state-forks continuation cases"}
    ],
    "evidence": ["state_format_contract", "state_codec_matrix", "state_portable_pins", "state_refusal", "state_semantic_bounds"],
    "id": "state-api",
    "models": ["DMG-CPU-B", "CGB-CPU-E"],
    "modes": ["dmg", "cgb-compat", "cgb-native"],
    "non_claims": ["no-cross-version-state", "no-third-party-state-interop", "no-power-loss-durability", "no-cgb-game-level-evidence"],
    "platforms": ["linux-x64", "macos-arm64", "windows-x64"],
    "requirements": ["STATE-01", "STATE-02"],
    "statement": "The public state API saves and loads validated state for the supported monochrome and color CPU models.",
    "surface": "core-api"
  }
]
```

### `tests/scripts/verify-support-ledger.py` (utility, batch/transform)

**Analog:** the existing claims profile, validation, rendering, and rejection controls in this tracked script.

Keep version-specific claim paths/profiles explicit so the v0.4 ledger does not silently replace v0.3 history. Read the selected claims and Phase 21/22 evidence through immutable Git objects at the requested full revision; enforce a closed schema and allowlists; recompute counts/identities where source records permit; require exact generator bytes for the tracked ledger. Preserve the current structured `REJECT ...` diagnostics and pair every accepted profile/render path with mutants for missing, changed, or over-promoted evidence.

**Profile and closed-schema pattern** (lines 2861-2871, 2930-2938):

```python
# Support claims are reviewed managed input. Their enums and required
# exclusions live here so editing the JSON cannot widen the supported surface.
CLAIMS_PATH = "tests/data/support-claims-v0.3.json"
MAX_CLAIMS_BYTES = 64 * 1024
CLAIMS_TOP_KEYS = {"schema_version", "kind", "applies_from_version", "claims", "non_claims"}
CLAIM_KEYS = {"id", "requirements", "statement", "models", "modes", "corpus",
              "platforms", "surface", "evidence", "non_claims"}
CLAIM_MODELS = {"DMG-CPU-B", "CGB-CPU-E"}
CLAIM_MODES = {"dmg", "cgb-compat", "cgb-native"}
CLAIM_PLATFORMS = {"linux-x64", "macos-arm64", "windows-x64"}

def validate_claims(data: object, root: pathlib.Path, rev: str) -> dict:
    """Validate claim shape and recompute scope counts from immutable source objects."""
    data = _claims_keys(data, "claims", CLAIMS_TOP_KEYS)
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        _claims_invalid("schema_version must be 1")
    if data["kind"] != "scoped-support-claims" or data["applies_from_version"] != "0.3.0":
        _claims_invalid("kind or applies_from_version is not the v0.3.0 claims profile")
```

**Immutable source and exact-render pattern** (lines 2946-2956, 3201-3218):

```python
raw = immutable_git_file(root, rev, path, MAX_INPUT_BYTES)
source = strict_json(raw, "claim-derived-input")
...
if pin_version != tree_version:
    fail("REJECT claim-pins-stale: state goldens release differs from the CMake tree version")
...
generated = render_v3_ledger(data, disclosure, claims).encode("utf-8")
if generated != raw:
    fail(f"REJECT ledger-not-generated: {label} is not the exact generator output "
         f"(first difference at {first_difference(generated, raw)})")
```

For v0.4, extend the version dispatch and renderer deliberately while retaining the v0.3 path and tag checks. `claim_paragraphs()` at lines 3094-3117 is the compact Markdown rendering pattern. `self_test_claims()` at lines 3222-3268 runs positive paths alongside named mutations and checks the refusal reason; extend that style for omitted evidence, false admission/execution, wrong model/source, and Pending-status promotion.

### `tests/scripts/verify-v02-adoption.py` (utility, batch)

**Analog:** the release-note validator in this tracked script.

Extend the existing release-note contract and `--self-test` mutation controls. It already reads release notes as bounded UTF-8 prose, ignores comments/code as evidence, checks the version and exact ledger link, and rejects false support/signing claims. Add v0.4 candidate reasons, harness-only scope, synthetic/metadata-only distinctions, pending requirements, and hardware/perceptual/timing/platform limits to this same contract. Keep the prose concise; link the ledger for details.

**Release-note checks** (`tests/scripts/verify-v02-adoption.py`, lines 704-729, 757-770):

```python
def check_release_notes(path: Path, root: Path = DEFAULT_ROOT, rev: str | None = None) -> int:
    resolved = path.resolve(strict=True)
    if resolved.stat().st_size > MAX_NOTES_BYTES:
        raise ContractError("release-notes-too-large")
    raw = resolved.read_text(encoding="utf-8")
    text = prose(raw)
    require(text, "release-notes-empty")
    require(VERSION_TOKEN.search(text) is not None,
            f"release-notes-version-missing:{RELEASE_VERSION}")
    require(ABSENCE_SENTENCE in text, "release-notes-absence-missing")
    require(LEDGER_LINK.search(comment_free(raw)) is not None,
            "release-notes-ledger-link-missing")
    ...
    require(FALSE_PUBLICATION_CLAIM.search(text) is None,
            "release-notes-false-publication-claim")
    checks += check_claim_boundaries("release-notes", text)
    require(not unnegated(claims.UNQUALIFIED_CLAIM, text),
            "release-notes-unqualified-hardware-or-game-claim")
```

The workflow already invokes this checker on the rendered notes at `.github/workflows/release.yml:142-146`; retain that call and make its contract version-aware instead of adding another workflow path.

### `tests/scripts/verify-version-window.py` and `tests/data/version-window.json` (utility/config, batch)

**Analog:** the existing exact-content release-window checker and its tracked inactive record.

Add every v0.4 source input that can change the ledger or notes to `REQUIRED_MANAGED_INPUTS`, including the new claims profile. Keep only generated release-please outputs in `REQUIRED_GENERATED_FILES`, and ensure the window reads Git objects at one immutable reviewed revision. The existing record's current `inactive` shape is lines 1-10 of `tests/data/version-window.json`.

**Managed-input and output inventory** (`tests/scripts/verify-version-window.py`, lines 46-54):

```python
# Generator inputs: a change to any of them changes what release-please or --write-current would render.
REQUIRED_MANAGED_INPUTS = (
    "tests/data/release-disclosure.json",
    "tests/data/support-claims-v0.3.json",
    "tests/scripts/verify-support-ledger.py",
    "release-please-config.json",
)
# Regenerated outputs of the version PR (the ledger path is derived from the version).
REQUIRED_GENERATED_FILES = ("CHANGELOG.md", ".release-please-manifest.json")
```

The checker docstring at lines 16-21 is the governing rule: record and digests come from `--rev` Git objects, never from the live working tree. Its fixture builder at lines 442-468 models a generated release PR and proves the tracked version files, changelog, and ledger move together.

### `tests/CMakeLists.txt` (config/test registration, batch)

**Analog:** current release-disclosure, claims, and version-window CTest registration.

Register positive generation/check cases and separate controls using the existing helper functions. Invoke Python isolated with `-I`, use stable output regexes and bounded timeouts, and make the control test assert a nonzero count of rejected mutations. Keep existing v0.3 claims coverage while registering v0.4-specific profile checks.

**Contract helper and disclosure controls** (lines 1478-1486, 1503-1514):

```cmake
function(gbb_add_ledger_contract name regex)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${Python3_EXECUTABLE};-I;${PROJECT_SOURCE_DIR}/tests/scripts/verify-support-ledger.py;${ARGN}"
      -DGBB_EXPECT_CODE=0
      "-DGBB_EXPECT_REGEX=${regex}"
      ${GBB_LEDGER_MIN}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT 60 LABELS "v02")
endfunction()
...
gbb_add_ledger_contract(release_disclosure_generator
  [=[release-disclosure generator pass ledgers=3 tagged=2]=]
  --check-disclosure)
...
gbb_add_ledger_contract(release_disclosure_controls
  [=[release-disclosure controls pass positives=[1-9][0-9]* controls=[1-9][0-9]*]=]
  --self-test-disclosure)
```

**Claims positive/control pair** (lines 5071-5078):

```cmake
gbb_add_ledger_contract(support_claims
  [=[support-claims pass claims=9 non_claims=10 rev=[0-9a-f]+]=]
  --check-claims --rev "${GBB_STATE_SOURCE_REV}")
set(GBB_LEDGER_MIN -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=16)
gbb_add_ledger_contract(support_claims_controls
  [=[support-claims controls pass positives=[1-9][0-9]* controls=[1-9][0-9]*]=]
  --self-test-claims --rev "${GBB_STATE_SOURCE_REV}")
```

### `docs/support/v0.4.0.md` (generated documentation, transform)

**Analog:** `docs/support/v0.3.0.md` (tracked; preserve it byte-for-byte).

Follow its top-level reading order: version/model/mode scope, bounded evidence and explicit game evidence status, limitations, concise scoped claims/non-claims, then the machine-readable receipt block. For v0.4, the prose should name both candidate no-go reasons and make the CGB-CPU-E harness-only and Phase 22 synthetic/metadata-only boundaries clear before the generated claim block. Keep the detailed Phase 21/22 tables in their original evidence records and link to them.

**Scope and limitation wording** (`docs/support/v0.3.0.md`, lines 1-9, 50-58):

```markdown
# GabbaBoy v0.3.0 support ledger

This ledger records implemented scope and the software evidence available for the v0.3.0 release. The CGB corpus is a bounded test-ROM set, not a game library or hardware qualification. Boot ROMs are skipped; the CGB corpus ran on the selected CGB-CPU-E software model. Physical CGB-E remains UNKNOWN/POLICY.

## Models and execution modes

- **DMG-CPU-B:** bootless deterministic DMG software profile. ...
- **CGB-CPU-E:** selected CGB software model, with native CGB mode and DMG compatibility mode selected from the cartridge header. ...

## Game-level evidence, known issues and exclusions

**No CGB game-level evidence exists.** The CGB corpus consists of bounded emulator/test ROMs. ...

Known limitations include skipped boot ROMs; no physical DMG-CPU-B or CGB-CPU-E qualification; no general game compatibility percentage; no CGB mode-3 timing qualification; ...

## Scoped support claims
Applies from v0.3.0 and describes software evidence for v0.3.0.
```

## Shared Patterns

### Claims and evidence provenance

**Sources:** `tests/scripts/verify-support-ledger.py`, `tests/scripts/verify-v02-adoption.py`, and the immutable Phase 21/22 records.  
**Apply to:** claims JSON, generated ledger, release-note validator, and their controls.

Use source records as facts, but do not collapse distinct evidence types. The two CGB candidate records say no candidate was built or run and no game was admitted; describe the reasons as unresolved source/rights scope, not a license ban. Label the CGB-CPU-E harness result harness-only. Phase 22 is a synthetic composition tracer plus metadata-only assessment: 513 named entries, seven unresolved real-fixture gates, zero real fixtures admitted/executed; keep DIAG-01, DIAG-02, and RIGHTS-01 Pending. Digests prove byte identity only.

### Generated copy and version window

**Sources:** `tests/scripts/verify-support-ledger.py`, `tests/scripts/verify-version-window.py`, `tests/data/version-window.json`.  
**Apply to:** both public v0.4 copy surfaces and the reviewed release PR.

The generator owns ledger bytes. The claims input, disclosure facts, renderer, release-please config, and new input inventory belong in the content window. Keep `CMakeLists.txt`, `.release-please-manifest.json`, `CHANGELOG.md`, ledger version, and release tag aligned at exactly 0.4.0 before rehearsal/tagging. Do not alter the historical v0.3.0 ledger.

### Test controls

**Source:** `tests/CMakeLists.txt` lines 1478-1526 and 5071-5084.  
**Apply to:** each new generation or disclosure contract.

Follow each positive contract with a mutation/refusal control. Use the existing CTest wrappers and require stable error categories so a rejection for an unrelated parse failure cannot satisfy the intended guard.

### Release qualification chain

**Sources:** `.github/workflows/release-rehearsal.yml` lines 3-15, `.github/workflows/release.yml` lines 136-146 and 1518-1545, and `docs/release.md` lines 489-534.  
**Apply to:** final Phase 23 qualification; workflow files are existing infrastructure, not expected new targets.

The rehearsal qualifies source-side producers on the reviewed version PR and never publishes or proves draft downloads. After tag/draft creation, the trusted release path separately checks downloaded platform artifacts, installed consumers, notices, forbidden-fixture exclusion, the exact-tree nightly ASan replay, and the final publish gate. Preserve the actual Linux/macOS/Windows core and macOS player matrix; SHA-256 and source binding are not signing or notarization.

## No Analog Found

None for the scoped implementation files. Keep Phase 21/22 outcome records as read-only evidence sources; no implementation should add a new fixture or release mechanism.

## Metadata

**Analog search scope:** `tests/scripts/`, `tests/data/`, `tests/CMakeLists.txt`, `docs/support/`, `.github/workflows/`, `docs/release.md`.  
**Files scanned:** 11 primary analog/input/output files, plus listed release and evidence references.  
**Tracked-source gate:** all named analog files were verified with `git ls-files`; no ignored runtime mirror paths are referenced.  
**Pattern extraction date:** 2026-11-03
