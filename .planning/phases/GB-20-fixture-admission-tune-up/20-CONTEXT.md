# Phase 20: Fixture Admission Tune-up - Context

**Gathered:** 2026-10-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish one checked fixture and distribution boundary for new evidence before game or diagnostic fixture bytes enter public automation. The boundary records exact fixture/source/build identities and source-grounded redistribution terms for each relevant component, rejects incomplete or changed records, keeps controlled game ROM bytes out of installed and product-release packages, and preserves the notices those packages actually ship.

Phase 20 establishes the admission and packaging contract. It does not admit either game candidate, search for additional candidates, migrate or re-audit historical fixture approvals, change the root MIT license, repair accepted v0.3 debt, or start the later Phase 21/22 fixture work. RIGHTS-01 remains owned here and its contract is consumed by those later phases.
</domain>

<decisions>
## Implementation Decisions

### Component rights evidence

- **D-01: Require positive, source-grounded rights coverage for each distributed or embedded fixture component.** Record applicable terms and evidence for code, art, audio driver, build inputs, and notices, and state whether the permission covers repository and public-CI use. A repository-wide grant can cover a component when the grant's published scope and pinned source provenance support that mapping. Public availability, a digest, repository visibility, or commit history alone does not establish permission. An unresolved or conflicting component is a no-go; record the reason instead of admitting its bytes.
- Record build-only tools separately from fixture content. Pin their source/version and terms for reproducibility, and state whether they are copied, linked, or shipped. A tool not included in the distributed fixture is not described as a redistributed fixture component; copied or embedded tool material needs its own applicable rights record.
- Do not treat hashes as legal evidence. Automated checks can validate required record fields, pinned identities, notices, and byte digests; they cannot decide whether an external grant legally covers a component. Keep that evidence review explicit and fail closed when scope is unclear.
- Preserve the disposition of existing fixtures. Do not turn this tune-up into a retroactive rights re-audit or treat the documented Libbet asset-rights inference as a blanket precedent for new admissions.

### Admission record and verification

- **D-02: Keep fixture provenance and terms with each fixture's existing manifest.** Introduce a consistent, versioned admission record there and retain `THIRD_PARTY_NOTICES.md` as the human-readable index with digest bindings. Use the existing CMake/Python standard-library path; do not add a general central registry, JSON Schema validator, or other dependency without a demonstrated need.
- Bind exact fixture bytes, source/build inputs, component terms, notices, and permitted repository/public-CI use. Missing components must be explicitly marked absent rather than left ambiguous. Independently pin admitted identities to an immutable baseline so changing fixture bytes together with self-declared manifest and notice digests still fails. Include a negative control for that coordinated change. A digest confirms identity, not rights.
- Keep the fixture manifest as the rights/provenance source of truth. A small product-package inventory is allowed where needed to specify exact product paths and identities; it must be checked against fixture manifests and actual package contents so it does not become a conflicting rights registry.

### Product distribution boundary

- **D-03: Enforce package policy against actual staged or extracted bytes and exact identities.** Extend existing install, preview, and release package checks. Product packages may contain only the exact currently approved original smoke fixtures: `tracer`, `visible-demo`, and `mbc1-continuation`, with their component notices and GabbaBoy's root MIT declaration at the established package-specific locations. Reject extra or changed fixture content even inside an allowed directory; path names and ROM suffixes are insufficient.
- Exercise a clean package as the positive control and reject controlled game bytes copied under a renamed path, without a ROM suffix, and inside each otherwise allowed fixture subtree. Check for missing or changed package notices and root MIT bytes as well as fixture leakage.
- Keep source archives distinct from binary products. Source archives may contain admitted game or diagnostic fixture bytes with their verified terms and notices. Binary products must not contain controlled game/diagnostic ROMs. Do not require source-only `THIRD_PARTY_NOTICES.md` inside binary packages: the core release carries `gabbaboy-notices.txt`, and the macOS player uses `share/licenses/GabbaBoy` and `share/licenses/SDL3`.

### the agent's Discretion

- Choose the versioned manifest field names and the smallest checker organization that fits existing CMake and Python patterns.
- Represent the exact product fixture inventory in a small policy file or derive it from existing fixture manifests, provided there is one clear source of truth and the installed and release archive checks reject unknown additions and stale identities.
- Use the existing CTest and CI lanes. Keep new controls local and automated; do not create a duplicated full CI matrix or a new external dependency.
- The owner asked for relevant role-based fanout, primary-source research where useful, an adversarial pass, and automatic adoption of a coherent recommendation. This discussion used those instructions; the recommendations above stay inside the approved Phase 20 scope and three-plan cap.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and adopted project decisions
- `.planning/ROADMAP.md` §Phase 20 and §Phases 21–22 — success criteria, three-plan cap, preserved debts, and downstream use of the admission contract.
- `.planning/REQUIREMENTS.md` RIGHTS-01 and Out of Scope — per-component rights, repository/public-CI permission, package exclusions, root MIT, and explicit boundaries.
- `.planning/context/DECISIONS.md` D-069, D-096, D-137–D-139 — automated checks with negative controls, dependency preference, retained v0.3 dispositions, and owner-approved v0.4 scope.
- `.planning/research/2026-10-31-LICENSE-AUDIT.md` — root/fixture license distinctions and the limits of the current ownership/provenance audit.
- `.planning/research/2026-10-31-GAME-FEEDBACK-REVIEW.md` — candidate/build/rights gates and distinction between admission failure and emulation failure.

### Existing admission and package controls
- `THIRD_PARTY_NOTICES.md` — current fixture/component terms, source archive notices, and manifest/license digest index.
- `fixtures/libbet/manifest.json` and `fixtures/libbet/SOURCES.md` — detailed precedent and its documented per-asset rights limitation; do not generalize its inference to new admissions.
- `fixtures/tracer/manifest.json`, `fixtures/visible-demo/manifest.json`, and `fixtures/mbc1-continuation/manifest.json` — existing product fixture identities and local notices.
- `cmake/VerifyFixtureManifest.cmake` — current fixture file size/SHA-256 checks.
- `cmake/ScanForbiddenFixtures.cmake` — current path, known-digest, symlink, and installed fixture-directory scan.
- `cmake/VerifyInstalledPackage.cmake` and `cmake/PreviewPackageSmoke.cmake` — installed-prefix and extracted preview package contracts.
- `CMakeLists.txt` and `tests/CMakeLists.txt` — explicit install rules, existing package scans, and negative controls.
- `tests/scripts/verify-libbet-admission.py` — fail-closed manifest, build-closure, notice, and identity-check pattern.
- `tests/scripts/verify-v02-source-archive.py` — source-archive/product-package distinction; product fixture directory and exact-content checks.
- `tests/scripts/verify-phase3-player.sh` and `tests/scripts/verify-release-candidate.sh` — established player license paths and core-release notice sidecar.

### Primary external references
- `https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/` — expressions can represent combined terms; an expression does not itself prove ownership or coverage.
- `https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository` — a public repository without a license does not grant ordinary reproduction/distribution permissions.
- `https://www.copyright.gov/circs/circ16a.pdf`, `https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title17-section106`, and `https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title17-section201` — primary references for rights scope and ownership distinctions; not a legal clearance of any fixture.
- `https://cmake.org/cmake/help/v3.25/command/string.html` — built-in CMake JSON access available to the existing project toolchain.
- `https://cmake.org/cmake/help/v3.29/command/install.html` — CMake install rules and staged installation behavior; package contents should be checked after staging.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `fixtures/<id>/manifest.json` plus each fixture's local `LICENSE.txt`/`SOURCES.md` — existing home for byte identities, provenance, and local rights notes.
- `cmake/VerifyFixtureManifest.cmake` — checks declared fixture file sizes and SHA-256 digests.
- `cmake/ScanForbiddenFixtures.cmake` — scans staged trees by known manifest digest and path, including renamed files and file symlinks.
- `tests/scripts/verify-libbet-admission.py` — stdlib-only example for a rights manifest, source/build closure, notice checks, and negative controls.
- `tests/scripts/verify-v02-source-archive.py` — parses downloaded source/product archives and keeps their fixture policies distinct.

### Established Patterns
- Tests commonly include positive package checks and seeded mutations for missing fields, altered identities, renamed payloads, and link-based bypasses.
- `THIRD_PARTY_NOTICES.md` binds fixture manifest/license digests; manifests and notices are checked through existing CTest/CI flows.
- Existing project-authored smoke fixtures are deliberately installed/packaged with their local notices; third-party corpus fixtures are repository/source-archive evidence only.
- The current product checker allowlists three fixture directories, which does not by itself restrict every file inside those directories. Package admission needs exact allowed file identities and must bind them to the actual staged/extracted bytes.

### Integration Points
- CMake install rules feed installed-prefix and extracted preview checks.
- `cmake/PreviewPackageSmoke.cmake` checks the staged macOS player archive; `tests/scripts/verify-phase3-player.sh` checks player package notice locations.
- `tests/scripts/verify-v02-source-archive.py` checks the core release archive; `.github/workflows/release.yml` carries the separate core notice sidecar.
- New checkers belong in `tests/scripts/`, use immutable commit facts, and enter CTest with negative controls.
</code_context>

<specifics>
## Specific Ideas

Preserve the root MIT declaration and the distinct terms of each fixture component. Prefer a small direct extension of existing manifest and package-checking code over a new dependency. Do not claim that machine-checked hashes prove redistribution permission, or that package scans prove rendering/game correctness.
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 20 scope.
</deferred>

---

*Phase: 20-Fixture Admission Tune-up*
*Context gathered: 2026-10-31*
