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
```

`--self-test` sends a complete synthetic record through the real CLI and rejects a coordinated
fixture/manifest/notice rewrite against an unchanged pin. `--check-repository` runs during a
`BUILD_TESTING` CMake configure before fixture-consuming targets are declared. Non-testing source
library builds do not require Git history. The CTest controls exercise both modes.

## Rights decision boundary

The checker verifies required fields, full identities, local snapshots, notice bindings, and
actual bytes. It cannot decide whether a grant's author had authority, whether a quoted grant's
scope covers a component, or whether repository/public-CI use is legally permitted. A maintainer
must make that decision from source evidence. Public availability, repository visibility, populated
fields, commit history, and matching hashes do not provide that permission. Phase 20 creates this
boundary but does not admit a game or diagnostic candidate.
