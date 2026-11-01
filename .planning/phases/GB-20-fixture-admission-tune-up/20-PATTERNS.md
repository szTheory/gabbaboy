# Phase 20: Fixture Admission Tune-up - Pattern Map

**Mapped:** 2026-10-31  
**Files analyzed:** 15 implementation paths and read-only analogs  
**Analogs found:** 15 / 15

The file set groups the scope's existing manifest, notice, install, preview, release, and player checks. The optional product inventory's location is still a planning choice; no separate inventory file is assumed here. Keep implementation within the three-plan phase cap.

## File Classification

The three original smoke-fixture manifests below are read-only references for legacy source and byte identities. Phase 20 does not edit or retroactively re-audit their rights; new admission metadata is exercised with synthetic records and applies to later candidate manifests.

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `fixtures/tracer/manifest.json` | model | batch | `fixtures/visible-demo/manifest.json` | role-match |
| `fixtures/visible-demo/manifest.json` | model | batch | `fixtures/mbc1-continuation/manifest.json` | role-match |
| `fixtures/mbc1-continuation/manifest.json` | model | batch | `fixtures/tracer/manifest.json` | role-match |
| `THIRD_PARTY_NOTICES.md` | config | batch | Existing notice digest table in the same file | exact |
| `tests/scripts/verify-fixture-admission.py` (new) | test | file-I/O, batch | `tests/scripts/verify-libbet-admission.py` | role-match |
| `cmake/VerifyFixtureManifest.cmake` | utility | file-I/O | Same manifest checker | exact |
| `cmake/ScanForbiddenFixtures.cmake` | utility | file-I/O | Same staged-tree scanner | exact |
| `cmake/VerifyInstalledPackage.cmake` | test | file-I/O | Same install verifier | exact |
| `cmake/PreviewPackageSmoke.cmake` | test | file-I/O | Same install/extract smoke | exact |
| `CMakeLists.txt` | config | file-I/O | Existing explicit fixture install rules | exact |
| `tests/CMakeLists.txt` | config | batch | `gbb_add_v02_contract` and `preview_package_smoke` registration | exact |
| `tests/scripts/verify-v02-source-archive.py` | test | file-I/O, batch | Same archive inspector | exact |
| `tests/scripts/verify-release-candidate.sh` | test | file-I/O | Existing `--verify` / `--verify-final` flow | exact |
| `tests/scripts/verify-phase3-player.sh` | test | file-I/O | Same extracted-player verifier | exact |
| `.github/workflows/release.yml` | config | batch | Existing core notice sidecar check/upload | exact |

All named analogs were checked with `git ls-files -- <path>` and are tracked source files. No ignored runtime mirror paths are used.

## Pattern Assignments

### Fixture manifests (`fixtures/{tracer,visible-demo,mbc1-continuation}/manifest.json`) (model, batch)

**Analog:** `fixtures/libbet/manifest.json` for versioned source/rights/provenance structure; the three current project fixture manifests for existing build and byte fields.

The current manifests already pin source/build identities and fixture bytes. For example, the visible demo declares its source digest, assembler version, archived build input, ROM size, and ROM digest:

```json
{
  "id": "original-visible-interactive-dmg",
  "source": "demo.asm",
  "source_sha256": "930a92621fe3b5a862a50aee6f79bdae3f6bb8d8fe24f546a5d5ab737782d1ee",
  "build": {
    "assembler": "RGBDS",
    "version": "1.0.1",
    "archive_sha256": "2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645"
  },
  "rom": "demo.gb",
  "size_bytes": 32768,
  "sha256": "38afb54b40f4b6612906c7a68e367199d8bff135508a39d7acdc996bf3d86530"
}
```

Source: `fixtures/visible-demo/manifest.json` lines 1-18. `fixtures/libbet/manifest.json` lines 1-16 and 49-55 show the existing schema version, immutable upstream commit, license digest, and component/build-closure metadata. Use those structural ideas only. Its documented per-asset rights inference is explicitly limited and is not precedent for new rights decisions.

**Use:** Add explicit, versioned component records to the applicable existing manifest; distinguish content from build-only tools; mark absent components explicitly; record source-grounded terms/evidence and intended repository/public-CI use. Keep fixture hashes as identity checks, not as rights proof. Preserve existing fixture dispositions rather than turning this phase into a historical re-audit.

### `THIRD_PARTY_NOTICES.md` (config, batch)

**Analog:** Existing notice rows and manifest/notice digest table in `THIRD_PARTY_NOTICES.md`.

The first three product rows bind each package fixture to a manifest digest, source/build identity, ROM digest, and local notice digest (lines 19-23). The table introduction states that the digest values are checked against committed files (lines 34-38):

```markdown
### Manifest and notice digests

Every admitted fixture directory has exactly one row below. The digests are the
SHA-256 of that directory's `manifest.json` and `LICENSE.txt` as committed, so a
changed manifest or notice makes this table stale and fails the adoption check.
```

Update the existing human-readable product claim and digest bindings in place. Keep package-specific license paths explicit; do not require this source-only document inside binary packages.

### `tests/scripts/verify-fixture-admission.py` (new test, file-I/O and batch)

**Analogs:** `tests/scripts/verify-libbet-admission.py` for strict manifest validation and synthetic controls; `tests/scripts/state_boundary.py` for reading facts from an immutable Git revision.

The Libbet checker is standard-library-only and isolates strict parsing, validation, notice checks, and self-tests. Its imports establish the project style (lines 10-20):

```python
import argparse
import hashlib
import json
import pathlib
import re
import sys
import tempfile
```

It rejects duplicate keys, invalid UTF-8, non-object JSON, and missing objects with stable failure tokens (lines 88-127):

```python
def fail(token: str, detail: str | None = None) -> None:
    raise ValueError(token if detail is None else f"{token}: {detail}")


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("manifest-invalid", f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def parse_manifest(raw: bytes) -> dict:
    text = raw.decode("utf-8", errors="strict")
    data = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    if not isinstance(data, dict):
        fail("manifest-invalid", "top level is not an object")
    return data
```

Its record checker rejects placeholders and malformed hashes, then validates the versioned record and expected fixture identity (`verify-libbet-admission.py` lines 138-160). The new checker can reuse this fail-closed validation shape, while expressing Phase 20's per-component and explicit-absence rules.

For independent identity, `state_boundary.py` reads named blobs from the supplied commit and checks that the Git object is a blob (lines 103-115):

```python
    def blob(self, rev: str, path: str) -> bytes:
        answer = self.read(f"{rev}:{path}")
        boundary_need(answer is not None and answer[1] == "blob",
                      f"git show {rev}:{path} failed: no such file at the revision")
        return answer[2]
```

`cmake/ResolveContractRevision.cmake` lines 7-23 is the adjacent CMake pattern: resolve once to a full 40-character commit, and return `unknown` / `unreadable` when resolution fails. Keep the phase baseline fixed independently from the mutable manifest and notice values.

The Libbet self-test helper requires each mutation to fail with the expected token (lines 598-605), and the test includes missing/changed rights fields, digest changes, duplicate keys, malformed encoding, and notice controls (lines 734-797):

```python
def expect(token: str, action, label: str) -> None:
    try:
        action()
    except ValueError as error:
        if not str(error).startswith(token):
            fail("self-test", f"{label}: expected {token}, got {error}")
        return
    fail("self-test", f"{label}: mutation was accepted")
```

Use the synthetic-only self-test pattern for both a valid admission record and a coordinated fixture+manifest+notice rewrite that must still fail against the original baseline. Do not invoke candidate builds or fetch sources in that fast check.

### `cmake/VerifyFixtureManifest.cmake` (utility, file-I/O)

**Analog:** Same file; it already checks a nonempty manifest fixture list against actual file sizes and SHA-256 values (lines 1-29):

```cmake
file(READ "${MANIFEST}" manifest_json)
string(JSON count ERROR_VARIABLE json_error LENGTH "${manifest_json}" fixtures)
if(NOT json_error STREQUAL "NOTFOUND" OR count EQUAL 0)
  message(FATAL_ERROR "fixture-manifest-empty: ${MANIFEST}")
endif()
...
file(SIZE "${path}" actual_size)
file(SHA256 "${path}" actual_digest)
if(NOT actual_size EQUAL size OR NOT actual_digest STREQUAL digest)
  message(FATAL_ERROR "fixture-digest-mismatch: ${name}")
endif()
```

Extend in the existing CMake JSON and SHA-256 style only where it belongs in the install/build path. Keep more detailed rights-record validation and the immutable-baseline check in the focused Python checker rather than duplicating a full schema implementation in CMake.

### `cmake/ScanForbiddenFixtures.cmake` (utility, file-I/O)

**Analog:** Same tree scanner. It follows file links to bytes, uses size as a cheap filter before SHA-256, and rejects a forbidden digest regardless of its path (`lines 152-161`). It can also compare the allowed fixture directory names (`lines 164-180`).

```cmake
file(SIZE "${candidate}" candidate_size)
list(FIND forbidden_sizes "${candidate_size}" size_hit)
if(size_hit EQUAL -1)
  continue()
endif()
file(SHA256 "${candidate}" candidate_digest)
list(FIND forbidden_digests "${candidate_digest}" digest_hit)
if(NOT digest_hit EQUAL -1)
  message(FATAL_ERROR "${GBB_FORBIDDEN_LABEL}-installed: ${relative}")
endif()
```

The current directory check validates only the three directory names, not exact files within them. Use a package-specific exact path/digest check alongside this forbidden-content scan; do not treat a fixture-directory allowlist as a complete product inventory.

### `cmake/VerifyInstalledPackage.cmake` and `cmake/PreviewPackageSmoke.cmake` (tests, file-I/O)

**Analog:** The installed-package verifier requires concrete payload and export files (lines 19-35), validates the installed MBC1 ROM/source against manifest digests (lines 37-57), and optionally runs the installed consumer. The preview smoke installs into a clean prefix, archives it, extracts it, then checks the extracted prefix (lines 21-64, 107-117).

```cmake
file(SHA256 "${battery_fixture_dir}/continuation.gb" installed_battery_digest)
file(SHA256 "${battery_fixture_dir}/continuation.asm" installed_battery_source_digest)
if(NOT installed_battery_digest STREQUAL battery_rom_digest OR
   NOT installed_battery_source_digest STREQUAL battery_source_digest)
  message(FATAL_ERROR "Installed battery fixture digest mismatch")
endif()
```

`PreviewPackageSmoke.cmake` already provides a clean extracted-package positive control and an outside-directory renamed-ROM negative control (lines 80-92). Extend that real-byte boundary with unknown files inside each allowed subtree, including suffixless renamed bytes, plus missing/changed fixture notices and root MIT bytes. Keep cleanup of seeded mutations on both pass and failure paths.

### `CMakeLists.txt` and `tests/CMakeLists.txt` (config, file-I/O / batch)

**Analogs:** Existing explicit install rules in `CMakeLists.txt` lines 173-188 and existing CTest helpers in `tests/CMakeLists.txt`.

Install contents are enumerated by file, with each destination tied to its fixture directory:

```cmake
install(FILES
  fixtures/visible-demo/demo.gb
  fixtures/visible-demo/manifest.json
  fixtures/visible-demo/LICENSE.txt
  DESTINATION "${CMAKE_INSTALL_DATADIR}/gabbaboy/fixtures/visible-demo")
```

CTest's `gbb_add_v02_contract` runs Python in isolated mode through `tests/expect_exit.cmake`, then applies timeout and label properties (lines 1422-1435). The existing registration is:

```cmake
gbb_add_v02_contract(v02_source_archive_controls 90
  [=[PASS: source archive checker accepted [1-9][0-9]* cases and rejected [1-9][0-9]* negative controls]=]
  verify-v02-source-archive.py --self-test)
```

Register the new structural checker with an acceptance plus negative-control summary and keep actual staged/extracted package checks in `preview_package_smoke`; do not duplicate the CI matrix. The target is registered at `tests/CMakeLists.txt` lines 1888-1897.

### `tests/scripts/verify-v02-source-archive.py` and `tests/scripts/verify-release-candidate.sh` (tests, file-I/O)

**Analogs:** Both existing checkers. The source archive checker explicitly keeps two contracts separate: admitted fixtures and notices are retained in a source archive, while the core product package has a narrower allowlist (`verify-v02-source-archive.py` lines 1-13).

The product checker rejects links, non-product fixture directories, ROM-like files outside the product roots, known third-party fixture digests, and source-only notices, then requires its product files (lines 484-504):

```python
if any(e.kind == "symlink" for e in inspection.entries):
    raise Reject("product-link-not-allowed", "product package contains a link")
...
if in_fixtures and parts[3] not in PRODUCT_FIXTURES:
    raise Reject("product-fixture-leak", f"product package carries non-product fixture content: {path}")
...
for required in PRODUCT_REQUIRED:
    if required not in files:
        raise Reject("product-package-incomplete", f"product package lacks {required}")
```

The source archive path also binds manifest and license digests to the notice table and rejects unadmitted fixture directories (`lines 345-387`). Keep that source rule distinct. The current product check admits any file beneath an allowed fixture directory, so add exact member path/digest equality there or in one checked product policy; path names and extensions alone are insufficient.

`verify-release-candidate.sh` already dispatches the product archive check and then, for `--verify-final`, verifies a separate source archive receipt (`lines 131-147`). Preserve this split while binding the release notice sidecar and actual core archive bytes to their package-specific expected identities.

### `tests/scripts/verify-phase3-player.sh` and `.github/workflows/release.yml` (test/config, file-I/O / batch)

**Analogs:** Existing player package verification and release notice handling.

The player verifier assigns explicit extracted paths to its fixture payload and package-specific licenses, then fails if any are missing and scans extracted bytes for the third-party Libbet ROM (`verify-phase3-player.sh` lines 115-145):

```bash
local demo_rom="$prefix/share/gabbaboy/fixtures/visible-demo/demo.gb"
local demo_license="$prefix/share/licenses/GabbaBoy/visible-demo-LICENSE.txt"
local project_license="$prefix/share/licenses/GabbaBoy/LICENSE.txt"
local sdl_license="$prefix/share/licenses/SDL3/LICENSE.txt"
...
[[ -s "$demo_license" && -s "$project_license" && -s "$sdl_license" ]] ||
  fail 'extracted package is missing a license notice'
```

Keep the macOS player's central license layout, including the distinct SDL license path. Extend its content checks to exact whole-package path/digest equality and negative controls for missing or changed fixture, GabbaBoy, and SDL notices.

For the core release sidecar, the workflow downloads an existing `gabbaboy-notices.txt` and byte-compares it with `LICENSE`, or uploads a new copy (`.github/workflows/release.yml` lines 400-408):

```bash
cmp -s LICENSE build/existing/gabbaboy-notices.txt || { echo "Existing notice bytes differ." >&2; exit 1; }
...
cp LICENSE build/gabbaboy-notices.txt
gh release upload "$RELEASE_TAG" build/gabbaboy-notices.txt --repo "$GH_REPO"
```

Reuse exact byte comparisons and retain the existing product-specific notice locations. Do not add the source-only `THIRD_PARTY_NOTICES.md` to these binary products.

## Shared Patterns

### Fail closed on incomplete or ambiguous records

**Sources:** `tests/scripts/verify-libbet-admission.py` lines 88-127 and `cmake/VerifyFixtureManifest.cmake` lines 5-13. Use explicit failure tokens/messages and treat missing fields, malformed JSON, unresolved baseline identities, missing blobs, and changed bytes as errors.

### Separate stable identity from rights interpretation

**Sources:** `tests/scripts/state_boundary.py` lines 103-115; `THIRD_PARTY_NOTICES.md` lines 19-24. Read baseline bytes from the fixed commit and bind notices to manifest/license digests. A hash demonstrates bytes match an identity; source-grounded review decides whether permission covers the component and repository/public-CI use.

### Inspect real package bytes with positive and negative controls

**Sources:** `cmake/PreviewPackageSmoke.cmake` lines 21-64 and 80-92; `tests/scripts/verify-v02-source-archive.py` lines 484-504; `tests/scripts/verify-phase3-player.sh` lines 110-145. Check the staged or extracted package contents and exact notice locations. Keep source archive policy distinct from binary products; seed controls for unknown in-directory bytes, renamed/suffixless bytes, missing/changed notices, and root MIT changes.

### Register focused self-tests in existing CTest lanes

**Sources:** `tests/CMakeLists.txt` lines 1422-1435 and 1534-1536. Use the existing isolated Python runner, clear expected-output pattern, timeout, and labels.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| Optional separate exact product inventory file (path undecided) | config | batch | Existing CMake and Python checks each carry partial package rules, but no single tracked file maps every allowed product path to a digest and notice identity. Prefer deriving from fixture manifests plus compact package path mappings; if a new file is chosen, cross-check it against manifests and actual staged/extracted members. |

## Metadata

**Analog search scope:** `fixtures/`, `cmake/`, `tests/scripts/`, `tests/CMakeLists.txt`, `CMakeLists.txt`, and `.github/workflows/release.yml`.  
**Tracked analogs scanned:** 15 named phase files plus the Libbet manifest and immutable-revision helpers.  
**Pattern extraction date:** 2026-10-31
