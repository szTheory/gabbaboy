# Phase 20: Fixture Admission Tune-up - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `20-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-10-31
**Phase:** 20-Fixture Admission Tune-up
**Areas discussed:** Component rights evidence, fixture admission record, product package boundary

---

The owner asked to consider all relevant areas, use parallel role-based research and primary sources where useful, run an adversarial pass, and automatically adopt coherent recommendations. Three independent advisor passes covered rights evidence, record shape, and package controls; a fourth pass checked the synthesis for gaps. The recommendations were kept within the approved Phase 20 scope and existing dependency preference.

## Component rights evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Separate explicit grant/license for every file | Maximizes directness but may require redundant per-file terms where an upstream license clearly covers a whole repository. | |
| Positive source-grounded coverage per component | Record each distributed/embedded component and its terms; allow a repository-wide grant only when its scope and pinned provenance support the mapping. Unresolved components block admission. | ✓ |
| Infer permission from public availability or source history | Minimal record, but visibility, hashes, and commit history do not establish permission or scope. | |

**Owner's direction:** Auto-adopt the coherent recommendation after fanout and adversarial review; retain root MIT and separate component terms.
**Notes:** Build-only tools are pinned and recorded separately from distributed/embedded fixture content. Hashes confirm identity, not rights. Existing historical fixture dispositions are preserved; Libbet's documented asset inference is not a blanket precedent for new admissions.

---

## Fixture admission record

| Option | Description | Selected |
|--------|-------------|----------|
| Versioned per-fixture manifest plus notice index | Keep component terms and provenance with each fixture; retain `THIRD_PARTY_NOTICES.md` as the digest-bound human index. | ✓ |
| Central admission registry | Makes cross-fixture queries easy but adds another source of truth and synchronization work. | |
| JSON Schema validator | Validates structure, but not rights scope or byte identity; adds tooling beyond existing CMake/Python support. | |

**Owner's direction:** Auto-adopt the coherent recommendation and prefer a smaller dependency tree.
**Notes:** Pin approved identities independently to an immutable baseline; a control must reject coordinated changes to fixture bytes, self-declared digests, and notice rows. A small product-only exact file inventory is allowed when it is checked against fixture manifests and actual package contents.

---

## Product package boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Path/name rules only | Simple, but renamed or extensionless bytes and unexpected files under allowed fixture directories can bypass the policy. | |
| Existing scanners plus exact product identities | Scan actual staged/extracted package bytes, restrict allowed fixture files by exact paths and identities, and retain the existing CMake/release flows. | ✓ |
| Separate general package registry | Centralizes policy but creates a broader source of truth than this bounded three-plan tune-up needs. | |

**Owner's direction:** Auto-adopt the recommendation within the approved Phase 20 cap.
**Notes:** Preserve the three original smoke fixtures, their local notices, and the root MIT declaration at established package locations. Test inserted, renamed, and extensionless bytes inside an allowed subtree. Source archives may carry admitted fixture content and terms; binary product packages follow the exact allowlist. The adversarial pass also required checking package notices at their actual distribution locations rather than requiring source-only `THIRD_PARTY_NOTICES.md` in binary packages.

---

## the agent's Discretion

- Exact field names and small checker organization within existing CMake/Python standard-library tooling.
- Whether the exact product file inventory is a small policy file or derived from fixture manifests, as long as one source of truth is enforced against actual package bytes.
- Keep the work in the existing test and CI lanes; no new dependency or duplicated full matrix.

## Deferred Ideas

None.
