# Fixture admission and package identity

The fixture admission checker keeps new Game Boy evidence behind one fail-closed boundary. It
checks the shape of the rights record and binds fixture bytes, source inputs, evidence snapshots,
and the matching notice-index row to immutable Git objects. A matching digest establishes byte
identity; it does not establish ownership or redistribution permission.

## Version 1 admission record

Put the record in the fixture's existing `manifest.json` as a top-level object using
`schema_version: 1`. Preserve the manifest's existing fixture identity fields. The version 1
record requires:

- `fixture_kind` — a short description of the fixture's role.
- `decision` — `status` (`approved` or `no-go`), `reviewer_role`, a source-grounded `rationale`,
  and `component_rationale` mapping every present component to the reviewer's scope rationale. Only
  `approved` records pass the admission gate.
- `permissions` — explicit booleans for `repository` and `public_ci`; both must be true before
  fixture bytes enter repository tests or public automation.
- `source` — the source repository and a full 40-character source revision. A tag, branch, URL
  alone, or mutable reference is not an identity.
- `files` — the exact path, byte length, and SHA-256 of every regular file in the fixture
  directory except `manifest.json` and the adjacent `admission.commit` pin.
- `inputs` — the source/build input subset of `files`, with the same path, size, and digest.
- `build` — a reproducible recipe and a list of tools with source repository, full revision,
  version, terms, and disposition (`build_only`, `copied`, `linked`, or `shipped`). A build-only
  tool is recorded for reproducibility with `component: null` and no copied paths. Copied, linked,
  or shipped tool material names its component and covered fixture paths.
- `components` — exactly `code`, `art`, `audio_driver`, `build_inputs`, and `notices`. Each
  component is either explicitly `absent` with a reason, or `present` with terms, a local grant
  evidence path and digest, the paths that evidence covers, and explicit repository/public-CI
  scope. Missing, conflicting, or unclear coverage is a no-go.
- `notices` — the local notice path and digest plus the path of the human-readable
  `THIRD_PARTY_NOTICES.md` index.

Every fixture file must be covered by a present component. The local notice must be covered by
the notices component. Grant and notice snapshots are ordinary committed files included in the
exact `files` list. The notice index row binds the exact manifest and local notice digests.

### Immutable admission pin

Place one full lowercase commit ID in `fixtures/<id>/admission.commit`. That commit must contain
the exact manifest, all listed fixture/evidence files, and the matching notice-index row. The pin
is separate from the commit it names, avoiding a self-referential commit hash. It must resolve in
the current repository history; the checker never fetches, resolves a branch/tag, or substitutes
`HEAD`. To update an admission, make a reviewed commit with the new record and evidence, then
update the adjacent pin in a following commit. Reviewers must explain the exact byte and evidence
delta before accepting a pin change.

The repository checker uses the separately pinned legacy baseline
`7cc6495e64f3645caa120e7458f754585b788985` in `cmake/FixtureAdmissionPolicy.json`. It preserves
existing fixture dispositions without migrating or re-auditing their rights. Any new or changed
fixture path must carry a valid version 1 record and immutable admission pin. The root `LICENSE`
must remain byte-identical to that baseline.

## Commands

```sh
python3 -I tests/scripts/verify-fixture-admission.py --self-test
python3 -I tests/scripts/verify-fixture-admission.py --check-manifest fixtures/<id>/manifest.json --repo-root .
python3 -I tests/scripts/verify-fixture-admission.py --check-repository --repo-root .
python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout core
python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player
```

`--self-test` sends a complete synthetic record through the real CLI and rejects a coordinated
fixture/manifest/notice rewrite against an unchanged pin. `--check-repository` runs during a
`BUILD_TESTING` CMake configure before fixture-consuming targets are declared. Non-testing source
library builds do not require Git history. The CTest controls exercise both modes.

## Binary product paths and inventories

`check_product_entries(entries, layout, repo_root, inventory=None, sidecar=None)` is the shared
API for already-inspected archive entries and staged directory trees. `entries` maps each
normalized relative path to `{"kind": "file", "size_bytes": N, "sha256": "..."}`; directory
records may use `{"kind": "directory"}`. Links and special files are rejected. The API checks
current source, manifest, local notice and notice-index bytes against the fixed legacy Git
baseline before accepting a product. Fixture and notice digests identify bytes only.

The core layout contains the installed public header and runner, the static core library, the
host contract, the CMake package exports, the root MIT license, and the tracer, visible-demo and
MBC1 continuation fixture members. Its protected and generated paths are:

```text
include/gabbaboy/gabbaboy.h
bin/gabbaboy-runner
bin/gabbaboy-runner.exe
lib/libgabbaboy_core.a
lib/gabbaboy_core.lib
lib/cmake/GabbaBoy/GabbaBoyTargets.cmake
lib/cmake/GabbaBoy/GabbaBoyTargets-release.cmake
lib/cmake/GabbaBoy/GabbaBoyConfig.cmake
lib/cmake/GabbaBoy/GabbaBoyConfigVersion.cmake
share/gabbaboy/host-contract.json
share/gabbaboy/LICENSE.txt
share/gabbaboy/fixtures/tracer/tracer.gb
share/gabbaboy/fixtures/tracer/manifest.json
share/gabbaboy/fixtures/tracer/LICENSE.txt
share/gabbaboy/fixtures/visible-demo/demo.gb
share/gabbaboy/fixtures/visible-demo/manifest.json
share/gabbaboy/fixtures/visible-demo/LICENSE.txt
share/gabbaboy/fixtures/mbc1-continuation/continuation.asm
share/gabbaboy/fixtures/mbc1-continuation/continuation.gb
share/gabbaboy/fixtures/mbc1-continuation/manifest.json
share/gabbaboy/fixtures/mbc1-continuation/LICENSE.txt
```

The player layout is a separate producer contract. It omits tracer and keeps the current
visible-demo and MBC1 continuation subset, the SDL runtime, notices and preview metadata:

```text
bin/gabbaboy-player
lib/libSDL3.0.dylib
share/gabbaboy/fixtures/visible-demo/demo.gb
share/gabbaboy/fixtures/visible-demo/manifest.json
share/licenses/GabbaBoy/visible-demo-LICENSE.txt
share/gabbaboy/fixtures/mbc1-continuation/continuation.asm
share/gabbaboy/fixtures/mbc1-continuation/continuation.gb
share/gabbaboy/fixtures/mbc1-continuation/manifest.json
share/gabbaboy/fixtures/mbc1-continuation/LICENSE.txt
share/licenses/GabbaBoy/mbc1-continuation-LICENSE.txt
share/licenses/GabbaBoy/LICENSE.txt
share/licenses/SDL3/LICENSE.txt
share/gabbaboy/preview-metadata.json
share/doc/GabbaBoy/preview.md
```

The SDL3 notice is pinned to SHA-256
`1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd`. The separate release
notice is `gabbaboy-notices.txt`; its bytes must equal the pinned root `LICENSE`. It is not a
binary-product tree member. `THIRD_PARTY_NOTICES.md` belongs to source archives and is not
required in either binary product. A source archive is not a core or player product and keeps
its existing independent source-archive policy.

The core producer permits exactly one runner name (`bin/gabbaboy-runner` or
`bin/gabbaboy-runner.exe`) and exactly one core library name (`lib/libgabbaboy_core.a` or
`lib/gabbaboy_core.lib`). Release builds include the single
`lib/cmake/GabbaBoy/GabbaBoyTargets-release.cmake` export. These are the producer's explicit
platform/configuration variants; the checker does not learn additional paths from an observed
package. All other listed regular-file paths are required, and unknown or missing files fail.

Use the same checker on the producer stage and on safely extracted archive bytes. Writing an
inventory is allowed only after the tree passes policy; an extracted tree must match every path,
size and SHA-256 in that inventory:

```sh
python3 -I tests/scripts/verify-fixture-admission.py --check-product-tree build/release-stage \
  --layout core --repo-root . --write-inventory build/core-product-inventory.json
python3 -I tests/scripts/verify-fixture-admission.py --check-product-tree build/extracted \
  --layout core --repo-root . --inventory build/core-product-inventory.json
python3 -I tests/scripts/verify-fixture-admission.py --check-product-tree build/player-prefix \
  --layout player --repo-root . --notice-sidecar build/gabbaboy-notices.txt
```

`--notice-sidecar` checks a separate root MIT notice against the same pinned bytes. The checker
scans every product member for known repository-only fixture digests without relying on file
suffixes, rejects extra members inside approved fixture directories, and does not expand its
path set from an inventory. Inventory files bind the exact accepted file map, layout and policy
digest. The package self-tests cover clean layouts, notice and fixture changes, extra and renamed
payloads, inventory mismatch, links, duplicate entries, and the documentation-to-policy contract.

## Rights decision boundary

The checker verifies required fields, full identities, local snapshots, notice bindings, and
actual bytes. It does not decide whether a grant's author had authority, whether a quoted grant's
scope covers a component, or whether repository/public-CI use is legally permitted. A maintainer
must make that decision from source evidence. Public availability, repository visibility, populated
fields, commit history, and matching hashes do not provide that permission. Phase 20 creates this
boundary but does not admit a game or diagnostic candidate.
