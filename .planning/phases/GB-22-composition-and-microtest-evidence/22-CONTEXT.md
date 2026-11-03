# Phase 22: Composition and Microtest Evidence - Context

**Gathered:** 2026-11-03
**Status:** D-141 no-go scope, D-142 bounded Windows-CI rescope, and D-143 one-time C1 OSC review-cycle exception are owner-approved. PR #142 remains open and blocked pending a corrected, fully qualified exact head.

**Scope amendment:** The owner accepted the Phase 22 rescope recorded in [22-RESCOPE.md](22-RESCOPE.md). For this phase, retain the synthetic tracer and source-bound metadata-only assessment, record the no-go for real diagnostic fixture admission, and leave DIAG-01, DIAG-02, and RIGHTS-01 Pending. The amendment supersedes the original admission/build/run deliverables below for Phase 22 only; their evidence requirements remain available for a future owner-selected scope. On 2026-11-03, the owner approved D-142's bounded rescope for the exact-head Windows CI failures recorded for PR #142. After the final D-142 review found an 8-bit C1 OSC payload leak, the owner approved one additional, narrowly scoped fix-and-independent-review cycle under D-143. Amend existing plan 22-12 in place; do not add a plan or reopen the gap round. This exception ends after that C1 fix and review; any further blocking finding stops Phase 22 for owner scope resolution. D-143 changes no Phase 22 acceptance claim, fixture-admission gate, or global review-round policy.

<domain>
## Phase Boundary

Establish model-qualified, independently expected diagnostic evidence from the font-substituted `dmg-acid2` and `cgb-acid2` derivatives and an admitted `gbmicrotest` cohort. Preserve exact source and ROM identities, build/provenance records, component rights, explicit text masking, per-case model applicability, and complete eligible/executed/excluded accounting. These results are controlled composition and microtest evidence only; they do not establish mode-3 timing, game-level progress, broad compatibility, or physical CGB-E behavior.

The admission contract from Phase 20 applies. If source, binary, art, reference-image, or model-applicability evidence remains unresolved, fail closed and request scope resolution; a populated manifest or matching digest does not clear a rights gate. Keep diagnostic ROMs out of installed and binary product packages and preserve the root MIT license.

Phase 21 is complete and merged on `main`. The Phase 22 branch has a candidate boundary, but PR #142 at `46c6696e57299be9601e88c17f0a19709a7f7367` remains blocked: local CTest passed 1,732/1,732, while the exact-head Windows job failed 10 of 1,594 tests. The owner approved a bounded replan to address those failures. Keep the current PR open and update its existing phase branch after the revised plan is reviewed. Both automatic-advance settings remain false.

</domain>

<decisions>
## Implementation Decisions

### Acid2 derivatives and independent image oracle

- **D-01: Build both derivatives from pinned upstream source and preserve the upstream image as the pass/fail reference.** Use `dmg-acid2` v1.0 and `cgb-acid2` v1.1 as the current source candidates, resolve and pin immutable source/submodule commits, patch/build inputs, toolchain, resulting ROM bytes, and upstream reference-image bytes. Reuse the project's existing RGBDS reproduction pin where it applies. The current `tests/acid2/manifest.json` only records upstream ROM/reference identities and explicitly keeps those files out of the repository while the `mgblib` font rights gate is open.
- Replace the upstream font data with original project-authored glyphs. Do not copy or retain the `mgblib` font in the derivative. Record the replacement glyph source and identity. Review rights for upstream code, all remaining art, reference images, build tools, and the derivative separately under Phase 20; font replacement alone does not clear those gates.
- Compare the derivative against the unchanged upstream reference using the documented DMG shade mapping and CGB RGB555 expansion. The reference must not be generated from GabbaBoy output. A second emulator may inform investigation, but is not the pass/fail oracle. Do not add a source-derived PPU renderer for this phase; testing replacement-glyph rendering would require a separately scoped independent expectation.
- Label the result as controlled composition evidence. The upstream CGB test explicitly says it is not a mode-3 timing torture test, and the mask excludes glyph rendering from this comparison.

### Text mask scope and validation

- **D-02: Define the mask from the pinned source's text tile layout.** Keep a readable allowlist of only the text tile cells affected by the replacement, mapped to fixed screen coordinates. Generate a fixed-size mask and a reviewable overlay from that allowlist. Include each displayed text area affected by substitution, including the greeting and footer when present; do not mask adjacent anatomy, background, or other composition.
- Pin the allowlist, generated mask identity, and the source/layout identity used to derive coordinates. Enforce a bounded masked area and a minimum unmasked comparison area. Compare every remaining pixel exactly; do not use a tolerance that could hide unrelated differences.
- The mask intentionally makes text pixels outside the comparison claim. Check replacement-glyph source and identity separately. Automated controls must reject an altered/broadened mask and still detect a one-pixel mismatch outside the mask; changed ROM/reference/mask identities must not silently pass.

### gbmicrotest cohort, model applicability, and accounting

- **D-03: Start from one immutable upstream inventory and keep exclusions visible.** Use upstream `aappleby/gbmicrotest` commit `463eb6bc0fe31d61781ef63060ad6d74090c0255` as the candidate inventory. Scouting found 513 source/ROM pairs at that revision; retain all names in the roster. The 482 cases using the shared verdict protocol are the initial runnable candidates. Keep the other 31 explicitly excluded unless a case-specific independent oracle is reviewed. Planning must verify the inventory and counts against the pinned commit before implementation.
- Bind every case to its exact source path/commit, ROM path/size/digest, redistribution evidence, expected-result protocol, and declared applicability. The upstream README makes a suite-wide, uncertain DMG-CPU-08 hardware claim; it does not provide per-case revision qualification. Record that upstream reference model separately from GabbaBoy's execution profile. A DMG-CPU-B run may be reported as a cross-model diagnostic, never as CPU-B hardware qualification. Do not infer CGB-CPU-E applicability; a case needs source-backed evidence for any additional profile or it remains excluded with a reason.
- The MIT file is not by itself proof that generated ROM bytes or every embedded component are covered. Review the exact source and binary scope, including the shared `.nintendologo` header directive, under Phase 20's component-rights rules. The upstream build script does not pin WLA-DX; do not claim reproducible ROM builds unless the assembler/build closure is pinned and verified. Exact prebuilt ROM identities may be recorded separately from any build claim.
- Require complete, disjoint eligible/executed/excluded case sets. Every eligible case must execute; every exclusion must name a concrete rights, oracle, or applicability reason. Missing, duplicated, reclassified, or unexecuted required cases fail the suite accounting. Add negative controls for altered source/ROM identity, incorrect applicability, dropped/duplicated cases, unexplained exclusion, and missing execution.
- If rights or model applicability cannot be established, do not imply successful fixture admission by running a partial or relabeled suite. Record the blocker and trigger scope resolution.

### Shared constraints and agent discretion

- Preserve Phase 20's fixture manifests, notices, source-archive/binary-product separation, and package exclusions. Keep original authored code under the existing MIT license; third-party terms remain separate.
- Prefer existing CMake/CTest and Python standard-library tooling. Do not add a dependency unless research demonstrates a need that the existing tools cannot meet.
- The owner asked for parallel, role-relevant analysis, primary sources where useful, an adversarial pass, and automatic adoption of the coherent recommendation. The areas discussed were the independent acid2 oracle, text-mask scope, and microtest cohort/accounting; the decisions above apply that instruction.
- The implementation may choose manifest field names, checker organization, exact mask encoding/overlay generation, and plan decomposition within the approved 12-plan Phase 22 cap, provided the invariants above remain automated and include meaningful negative controls.

### Windows exact-head CI qualification

- **D-04: Resolve the observed Windows failures without changing the evidence or gate contract.** The owner approved one bounded corrective plan after PR #142 head `46c6696e57299be9601e88c17f0a19709a7f7367` failed the protected Windows test-inventory job. Keep the 1,594-test Windows inventory, every CTest name and assertion, the existing 60-second control timeout, exact expected-test policy, and all required branch-protection checks. Do not skip or waive a test, raise a timeout/budget, or weaken the checker.
- The reported Windows failures are: seven CGB progress/history checks fail with `self-test-source-history-git-init-failed`; `phase22_evidence_contract` fails with `expected-test-policy-failed`; `phase22_evidence_controls` hits `subprocess-timeout` at 58.81 seconds under its 60-second limit; and `planning_labels_controls` rejects the evidence test's configured build-directory reference. The preview workflow also failed at its required-CI aggregation step; its dependent artifact job did not independently run.
- Keep the existing D-141 synthetic-plus-metadata/no-go boundary. No real upstream ROM/reference payload, upstream build/program, fixture admission, or diagnostic result is in scope. DIAG-01, DIAG-02, and RIGHTS-01 stay Pending.
- Add one live plan within the existing 12-plan on-disk cap. It must target these Windows failures, preserve cross-platform build-directory behavior, and use the project's existing tests and negative-control patterns. Require focused Windows-relevant tests, independent review/security review, a final full local suite, and fresh exact-head required CI/artifacts for the updated PR. Prior review/fix/gap history remains historical; this rescope does not reset it. If resolution would exceed the approved plan or remaining review limits, stop and report the concrete blocker for owner scope resolution.
- **D-143: Apply one explicit Phase 22 review-cycle exception to the existing 22-12 plan.** Address only the confirmed 8-bit C1 OSC payload leak (`U+009D … U+009C`) in bounded diagnostics, add a regression control, and obtain one fresh independent review of the correction. This is one additional review-fix cycle beyond D-142's original cap; it does not reset prior rounds, change the single used gap round, permit a new plan, or relax any preserved tests, timeouts, evidence gates, branch protections, or requirements. If the C1 fix or its independent review reveals another blocking correctness/security issue, stop for owner scope resolution. If the review is clean, continue the already authorized Phase 22 local and exact-head qualification on the same PR; Phase 23 remains unstarted.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase boundary and project policy
- `.planning/ROADMAP.md` §Phase 22 — goal, DIAG-01/02 success criteria, rights/model/oracle scope-resolution rule, and 12-plan cap.
- `.planning/REQUIREMENTS.md` §Diagnostic Evidence and §Fixture Admission and Rights — DIAG-01, DIAG-02, and RIGHTS-01.
- `.planning/PROJECT.md` — v0.4 evidence scope and root MIT constraint.
- `.planning/STATE.md` — Phase 21 closure, current Phase 22 route, and accepted evidence limits.
- `.planning/phases/GB-21-cgb-game-progress-and-scene-regressions/.continue-here.md` — Phase 21 evidence and Phase 22 planning handoff.
- `.planning/phases/GB-22-composition-and-microtest-evidence/22-11-SUMMARY.md` and `22-EVIDENCE.md` — candidate boundary, local suite result, and exact-head gate outcome.
- `build/phase22/remote-evidence.json` — local PR #142 runs, job statuses, and Windows CTest failure record; ignored local evidence, not a source artifact.
- `.planning/context/DECISIONS.md` D-026, D-069, D-096, and D-138–D-139 — mgblib/font fixture boundary, automated negative controls, dependency preference, and approved v0.4 scope.
- `.planning/research/SUMMARY.md` — project evidence classes and confidence limits.

### Fixture admission and existing implementation
- `.planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md` — component-level rights, immutable fixture identity, notices, package exclusions, and no-dependency policy.
- `.planning/phases/GB-21-cgb-game-progress-and-scene-regressions/21-CONTEXT.md` — model-qualified evidence, claim boundaries, and reusable acceptance patterns.
- `THIRD_PARTY_NOTICES.md` and `LICENSE` — current notice bindings and GabbaBoy's root MIT text.
- `tests/acid2/manifest.json` — existing acid2 upstream ROM/reference pins and unresolved font-rights note.
- `tests/scripts/run-acid2-local.py` — standard-library PNG/PPM comparison, input pins, exact all-pixel comparator, and synthetic-only required CI controls.
- `tests/scripts/verify-libbet-admission.py`, `cmake/VerifyFixtureManifest.cmake`, and `cmake/ScanForbiddenFixtures.cmake` — reusable provenance, identity, and package-boundary patterns.
- `tests/external/cgb-corpus-inventory.json` and `tests/scripts/verify-cgb-corpus-inventory.py` — source-bound corpus accounting precedent.
- `tests/scripts/verify-cgb-progress.py`, `verify-diagnostic-evidence.py`, `verify-planning-labels.py`, and `verify-no-phase-paths.py` — current self-test, immutable evidence, planning-inventory, and path contracts implicated by the Windows failures.
- `tests/CMakeLists.txt`, `tests/cmake/ci-lanes.cmake`, and `tests/expected-tests.txt` — CTest registrations, lane configuration, labels, and exact test inventory.
- `.github/workflows/ci.yml` and `.github/scripts/verify-pr-evidence.sh` — protected native, sanitizer, package, and exact-head qualification workflow.
- `tests/acceptance/cases-cgb-colour.txt` and `tests/acceptance/CMakeLists.txt` — model-specific case and explicit-exclusion test patterns.
- `docs/cgb-profile.md` — current CGB evidence labels and model-qualification limits.

### Primary upstream sources
- [DMG acid2 v1.0 README](https://github.com/mattcurrie/dmg-acid2/blob/v1.0/README.md) and [source](https://github.com/mattcurrie/dmg-acid2/blob/v1.0/src/dmg-acid2.asm) — reference comparison and displayed text/source layout.
- [CGB acid2 v1.1 README](https://github.com/mattcurrie/cgb-acid2/blob/v1.1/README.md) and [source](https://github.com/mattcurrie/cgb-acid2/blob/v1.1/src/cgb-acid2.asm) — RGB555 conversion, composition details, and timing-claim boundary.
- [gbmicrotest pinned README](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/README.md), [license](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/LICENSE), [build script](https://github.com/aappleby/gbmicrotest/blob/463eb6bc0fe31d61781ef63060ad6d74090c0255/build.sh), [sources](https://github.com/aappleby/gbmicrotest/tree/463eb6bc0fe31d61781ef63060ad6d74090c0255/tests), and [ROMs](https://github.com/aappleby/gbmicrotest/tree/463eb6bc0fe31d61781ef63060ad6d74090c0255/bin) — cohort, expected-result protocol, stated model, source/build identity, and terms requiring review.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/acid2/manifest.json` pins current upstream ROM/reference identities and defines the existing DMG/CGB color conversions; it currently notes that font rights prevent vendoring.
- `tests/scripts/run-acid2-local.py` uses only the Python standard library, refuses unpinned input before use, and has synthetic comparison/decoder controls. It currently compares all pixels and runs fixture-free in required CI.
- `tests/scripts/verify-libbet-admission.py` and the Phase 20 CMake checkers demonstrate source-bound manifests, immutable identities, component-rights records, and package exclusion checks.
- `tests/external/cgb-corpus-inventory.json`, its verifier, and `docs/cgb-profile.md` show how to keep named model-applicable cases and evidence dispositions synchronized.

### Established Patterns
- CMake/CTest registers automated checks; Python standard-library scripts are used for bounded source/provenance and report validation.
- Suite exclusions are explicit data with a reason; they are not represented as silent CTest skips. Corpus verifiers check complete accounting and negative controls.
- Fixture manifests and `THIRD_PARTY_NOTICES.md` record terms and identities, while binary packages exclude controlled game/diagnostic ROMs.
- Digests establish byte identity only. Rights and model applicability require separate evidence and review.

### Integration Points
- Extend the existing optional acid2 comparison path and its manifest; required CI currently exercises synthetic controls, not acid2 bytes.
- Add any admitted fixture provenance to its own manifest and notices, then connect the source-qualified cohort to CTest and its case-accounting verifier.
- Preserve the existing install/release package scans and source-archive notices. Keep Phase 22 claims and reports distinct from game acceptance and mode-3 timing evidence.

### Windows qualification failure context
- The Phase 1 local full suite passed 1,732/1,732 at the PR #142 source, but the protected Windows job ran 1,594 tests and failed ten. Seven history self-tests failed at temporary Git initialization; the Phase 22 immutable evidence contract refused the Windows expected-test policy; the controls reached their existing 60-second timeout at 58.81 seconds; and the planning-label control rejected the configured build-directory reference.
- Linux, macOS, Linux ASan/UBSan, CMake-floor, and fixture-reproduction jobs passed at that PR head. Preview failed because its required-native prerequisite failed; it produced no independent preview artifact. The PR evidence helper therefore reports required checks incomplete, and no merge occurred.
- The rescope targets cross-platform command/configuration behavior and control runtime. It preserves each assertion, test membership, fixed timeout/budget, all required jobs, and the PR branch-protection policy.

</code_context>

<specifics>
## Specific Ideas

- Prefer a source-anchored allowlist of masked text tile cells with a generated, reviewable overlay over broad rectangles or an opaque hand-edited mask.
- Use the upstream acid2 image as the pass/fail reference and keep every unmasked pixel exact.
- Keep `gbmicrotest`'s upstream reference model distinct from the GabbaBoy execution profile; record the current CPU-08 versus CPU-B mismatch as a diagnostic limit, not a hardware result.
- Treat unresolved component rights or model applicability as a scope-resolution gate rather than accepting a hash, MIT label, or partial denominator as proof.
- Resolve the exact Windows failures in one bounded, reviewed plan. Keep all tests and budgets intact, require a fresh all-green exact-head CI run on the updated PR, and stop if the approved rescope or remaining review limits cannot contain the fix.
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 22 scope.
</deferred>

---

*Phase: 22-Composition and Microtest Evidence*
*Context gathered: 2026-11-02*
