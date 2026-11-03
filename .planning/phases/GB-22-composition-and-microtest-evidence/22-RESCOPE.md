# Phase 22 owner-approved rescope

**Status:** Owner-approved on 2026-11-03; implementation remains within Phase 22.

## Decision

After Plan 22-02's metadata-only review, the owner accepted the recommendation to rescope Phase 22. The assessment did not establish the evidence needed to admit real acid2 or gbmicrotest fixtures. Seven gates remain unresolved: acid2 derivative build reproducibility; acid2 component rights and repository/public-CI output scope; acid2 reference applicability to DMG-CPU-B and CGB-CPU-E; gbmicrotest prebuilt ROM/logo rights and output scope; SHA-256 identities for 513 actual prebuilt ROM payloads; per-case model applicability; and independent expected results.

Phase 22 now closes the synthetic composition tracer and a source-bound, metadata-only assessment of the diagnostic candidates. It records a no-go for real fixture admission while those gates remain unresolved. It does not fetch or retain upstream ROM/reference payloads, run upstream builds or programs, admit any real fixture, or claim real diagnostic results.

## Acceptance boundary

- Preserve and verify the original synthetic composition tracer and its source-anchored mask, exact unmasked comparison, and identity/refusal controls.
- Preserve the complete named metadata inventory and each unresolved admission gate, with a machine-checkable approval command that refuses while any required gate lacks positive evidence.
- Document the no-go and the limits of the synthetic evidence. Do not describe the no-go as an upstream license prohibition or as evidence that any real fixture passed.
- Keep the root MIT license and existing fixture package boundaries unchanged. No real diagnostic fixture bytes or third-party fixture notices are added under this rescope.
- Keep DIAG-01, DIAG-02, and RIGHTS-01 Pending in REQUIREMENTS.md. The owner accepts a phase-scoped override for Phase 22's revised roadmap criteria; this does not change or complete those requirement definitions.
- Any future attempt to admit these real fixtures requires new source-backed evidence and a separately selected scope.

## Verification and handoff

Automated local checks must prove the synthetic controls pass and that unresolved diagnostic gates remain refused. Complete the normal Phase 22 review, security, local verification, and exact-head remote checks required by the project workflow. At the Phase 22 boundary, leave both automatic-advance flags false and route to `/gsd-discuss-phase 23` (Qualified v0.4.0 Release).
