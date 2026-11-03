# Phase 21: CGB Game Progress and Scene Regressions - Context

**Gathered:** 2026-11-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the shared game-acceptance path so a CGB-CPU-E software-profile run can confirm the loaded ROM's native CGB execution mode, observe RGB555 frames, and bind meaningful scripted input to an independently specified guest-progress predicate while preserving the current DMG acceptance behavior. Attempt only Potion Panic first and µCity 1.3 as the sole fallback, recording a reasoned outcome. Turn useful title/scene/symptom reports into agent-owned reproduction and controlled regressions without requiring owner play.

A CGB profile, a frame or PCM digest, an original harness fixture, or a diagnostic ROM does not by itself establish an admitted game's progress, rendering accuracy, perceptual quality, physical CGB-E behavior, mode-3 timing, or general compatibility. If neither named game clears its gate, an original native-CGB fixture may prove the harness, explicitly as harness evidence; do not relabel it as game evidence. Preserve the Phase 20 admission and product-package boundary. Do not start a third candidate search, add a RetroArch/Steam Deck path, or expand into Phase 22/23 work.

</domain>

<decisions>
## Implementation Decisions

### Candidate and admission outcome

- **D-01: Keep the approved candidate order and limit.** Assess Potion Panic first in one bounded plan. Only after a recorded no-go may the single µCity 1.3 preferred-ucity.gbc fallback plan run. Do not search for a third game.
- **D-02: Carry the Phase 20 fixture-admission contract into both attempts.** Bind exact source/build inputs, resulting ROM digest and size, cartridge metadata, CGB flag, actual execution mode, component terms/notices, and the Phase 20 rights decision. Public availability, a digest, or a license label alone does not establish permission for repository/public-CI use. An unresolved rights or identity gate is a no-go, not an emulator failure.
- Potion Panic's creator page currently lists MIT code separately from CC BY-NC-SA 4.0 assets. The µCity author README describes GPLv3+ for files carrying that header, a separately licensed BSD-2-Clause GBT Player component, and CC BY-SA 4.0 media. These statements identify terms to verify per component; they are not a legal clearance or a decision that either candidate is admissible.
- A no-game outcome must name the actual rights, build, predicate-feasibility, harness, or reproduced emulation blocker for each attempted candidate and state the concrete harness result. Do not silently treat a harness failure as candidate absence or defer a reproduced correctness/security defect.

### CGB progress and harness proof

- **D-03: Extend the existing runner and API seams.** Confirm the loaded ROM's actual execution mode through the existing information API; neither selecting the CGB-CPU-E profile nor reading the cartridge header alone proves that the guest ran in native CGB mode. Preserve the established DMG path and its receipt.
- **D-04: Define positive progress as one clear input-driven in-game state change.** Reach the playable portion, apply meaningful deterministic scripted input, and observe one externally specified guest-state predicate within a fixed budget. Do not require a long playthrough or a completion milestone. Bind the exact ROM, input script, predicate, profile/mode, and observations.
- **D-05: Prove the runner independently of candidate admission.** If neither named game is admitted, use a small original native-CGB control fixture to exercise the positive path and failing controls. Label its result as harness-only; it proves neither real-game progress nor candidate compatibility.
- Negative controls must distinguish missing input or a wrong input from success, and a deliberately broken predicate must show that the predicate gate itself can fail. Include a control for rejecting compatibility-mode execution where native CGB is required.

### Frame observations and scene regressions

- **D-06: Treat CGB RGB555 and PCM digests as bound observations, not correctness oracles.** Record named checkpoint times/digests and bind them to the result for reproducibility. Do not promote matching a digest, screenshot, or self-derived golden into a rendering-accuracy claim.
- **D-07: Use the smallest independent expectation that fits the reported symptom.** A genuinely static scene can use independently derived pixel expectations. Moving, timing, or audio symptoms need a bounded sequence or semantic/event invariant at the relevant boundary. Every automated regression needs an independent expected behavior and a negative control that targets that behavior; a no-input control only proves the progress gate.
- Reuse the existing input scripts, guest predicates, RGB555 digest path, PCM observation, receipt, and CTest patterns. Keep the existing DMG shade-count and audible-PCM acceptance gates specific to their established case unless independently justified for a CGB candidate.

### Scene triage, privacy, and dependencies

- **D-08: Keep report intake lightweight and investigation agent-owned.** A title, scene, and symptom are enough to start metadata recovery, source research, reproduction, and classification as core, conversion, host, original behavior, or unknown. Owner play is not a recurring or mandatory gate. Ask for one concrete missing detail only when it changes the next reproduction step.
- **D-09: Keep personal media out of tracked and hosted evidence.** Do not read private ROMs, saves, states, or captures unless the owner explicitly provides them for a specific local investigation. Never place them in the repository or public CI. Any automated test must use an original or rights-admitted fixture.
- Promote a report to an automated regression only when a minimized reproducible case, an independently reasoned expectation, and a relevant negative control are available. Otherwise retain it as unresolved triage with its concrete blocker; do not turn a report screenshot/hash into a golden.
- **D-10: Prefer existing helpers and standard-library tooling over another dependency.** Reuse the current C acceptance runner, CMake/CTest wiring, and small Python standard-library checkers where needed, consistent with D-096.

### the agent's Discretion

- Choose the smallest original CGB control ROM and the exact state field for its independent predicate, provided its source/build/digest and native-mode identity are fixed and it remains clearly separate from game evidence.
- Select checkpoint names and a deterministic run budget that fit the chosen candidate's shortest meaningful action without inflating repeated CI runtime.
- Retain a report as triage, rather than force a weak automated regression, when the source, rights, or independent oracle cannot support one.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase boundary and adopted policy
- .planning/ROADMAP.md §Phase 21 — candidate order, plan cap, success criteria, limits on claims, and explicit absence path.
- .planning/REQUIREMENTS.md §CGB Game Acceptance, §Fixture Admission and Rights, and §Scene Feedback — GAME-01/02, FIXT-01, and FEED-01; RIGHTS-01 is owned by Phase 20.
- .planning/PROJECT.md — project purpose and current v0.4 scope.
- .planning/STATE.md — current phase and accepted evidence limitations.
- .planning/context/DECISIONS.md D-069, D-096, and D-138–D-139 — automated negative controls, dependency preference, approved v0.4 scope, and phase pause.
- .planning/research/SUMMARY.md — milestone evidence classes and declared confidence limits.
- .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md — adopted component-rights evidence, fixture manifests/notices, package exclusion rules, and reusable check patterns.
- .planning/research/2026-10-31-GAME-FEEDBACK-REVIEW.md — candidate gates, CGB harness gap, classification workflow, capture/oracle limits, and out-of-scope Deck/Libretro path.
- .planning/research/2026-10-31-GAME-SCENE-SHORTLIST.md — candidate and scene details; routes are scouting leads, not verified tests.
- .planning/research/2026-10-31-LICENSE-AUDIT.md — root MIT and separate component terms; source/ownership review limitations.
- THIRD_PARTY_NOTICES.md — existing fixture terms and notice bindings.
- LICENSE — GabbaBoy's root MIT text, which stays unchanged.

### Existing CGB and acceptance interfaces
- docs/game-acceptance.md — current scripted acceptance case and observation contract.
- include/gabbaboy/gabbaboy.h — profile, sized ROM information, actual execution-mode reporting, RGB555 frame-copy, and bounded core APIs.
- docs/cgb-profile.md — bootless CGB-CPU-E software profile and raw RGB555 output limits.
- src/runner/acceptance.h and src/runner/acceptance.c — shared progress runner, profile-selected frame capture, predicates, checkpoints, observations, receipts, and current CGB progress refusal.
- tests/acceptance/cases.txt and tests/acceptance/inputs/libbet-tutorial.input — existing digest-bound input-driven positive case pattern.
- tests/acceptance/cases-cgb-colour.txt — CGB RGB555 digest cases and current progress-refusal control.
- tests/acceptance/CMakeLists.txt — CGB digest and acceptance negative-control registration patterns.
- tests/scripts/verify-libbet-admission.py and fixtures/libbet/manifest.json — standard-library fixture-provenance and admission-check precedent.
- cmake/VerifyFixtureManifest.cmake and cmake/ScanForbiddenFixtures.cmake — digest and product-boundary checks established in Phase 20.

### Primary external references
- https://deved.itch.io/potion-panic — creator's separate code and asset license labels and candidate description.
- https://github.com/gbcompo25/potion-panic — candidate source/build lead; exact source-to-ROM identity still needs verification.
- https://github.com/AntonioND/ucity — author README, preferred ROM name, mixed component licenses, and CGB scope.
- https://github.com/AntonioND/ucity/blob/master/manual.rst — candidate controls and original simulation behavior relevant to a progress predicate.
- https://github.com/gbdev/pandocs/blob/master/src/The_Cartridge_Header.md — CGB header flag semantics; runtime mode must still be reported by the loaded core.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The public core already exposes the CGB-CPU-E profile, loaded ROM execution-mode information, and raw RGB555 frame copying through include/gabbaboy/gabbaboy.h.
- The shared runner already parses bounded scripted inputs, evaluates guest-state predicates, observes frames and PCM, emits receipts, and has positive/failing DMG cases.
- CGB frame-digest capture already works for frame-digest cases; the CGB progress case in tests/acceptance/cases-cgb-colour.txt intentionally receives frame-unsupported-profile in the progress callback.
- Existing CGB color tests independently validate RGB555 digest vectors and a flipped-digest control. They can inform digest plumbing, but do not provide a game-scene oracle.
- Phase 20 established manifest, notice, exact-identity, and package-exclusion checks. Reuse those patterns for any newly admitted fixture.

### Established Patterns
- New fixtures record source/build/license/notice provenance and exact digests; automated checks have meaningful mutations and fail closed.
- Acceptance cases bind ROM and input digests, model applicability, predicate or frame checkpoint, and expected outcome. Keep unsupported/excluded/no-go distinct from pass/fail and retain an independent denominator.
- Tests belong in the existing CMake/CTest path. Checks should be bounded, negative-controlled, and preferably source/commit-bound where they inspect project state.
- A deterministic digest shows repeatability only. Accuracy claims need an independent oracle and the right model/timing applicability.

### Integration Points
- Extend the existing gabbaboy-runner acceptance path; no new public ABI, general player/recorder, or parallel test framework is needed.
- Register controls and positive cases under tests/acceptance and tests/CMakeLists.txt; keep candidate fixture data under its existing manifest/admission boundary.
- Preserve the current DMG acceptance case while adding explicit native-CGB mode checks and RGB555 progress observations.
- Any CGB game fixture remains repository/source evidence only and must stay out of installed and product-release packages under Phase 20.

</code_context>

<specifics>
## Specific Ideas

- Start from the smallest input-driven state change that a source-anchored guest predicate can distinguish from no-input/wrong-input behavior.
- Keep the two candidate gates separate from harness proof: an original fixture can prove the harness, while candidate failure remains a justified absence and does not create a game compatibility claim.
- Treat scene reports as leads. Compare native core output, conversion, and host presentation before assigning a fault; never select the failing output itself as its own golden.
- Preserve a simple C/standard-library shape and current dependencies; no new external dependency is justified.

</specifics>

<deferred>
## Deferred Ideas

None were added in this discussion. Existing out-of-scope items remain deferred by .planning/ROADMAP.md and D-138: third-candidate search, Libretro/Steam Deck qualification, Phase 22 diagnostics, and Phase 23 release work.

</deferred>

---

*Phase: 21-CGB Game Progress and Scene Regressions*
*Context gathered: 2026-11-01*
