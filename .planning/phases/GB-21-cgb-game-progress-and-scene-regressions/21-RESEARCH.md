# Phase 21: CGB Game Progress and Scene Regressions - Research

**Researched:** 2026-11-01
**Domain:** Native C Game Boy Color acceptance runner, rights-controlled ROM fixtures, scene regression evidence
**Confidence:** HIGH for the in-repo harness/API contract; MEDIUM for public candidate documentation; LOW for candidate source/build/ROM correspondence until each bounded admission attempt is performed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)

None were added in this discussion. Existing out-of-scope items remain deferred by .planning/ROADMAP.md and D-138: third-candidate search, Libretro/Steam Deck qualification, Phase 22 diagnostics, and Phase 23 release work.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GAME-01 | The shared game-acceptance runner supports CGB RGB555 frame observations and guest-progress predicates on the CGB-CPU-E software profile while preserving the existing DMG acceptance path. | Reuse the public RGB555 copy/info APIs and shared acceptance drive; add RGB555 handling at the progress callback and preserve existing DMG identity checks. [VERIFIED: .planning/REQUIREMENTS.md:11; include/gabbaboy/gabbaboy.h:344-396,415-433] |
| GAME-02 | A CGB game result binds the exact ROM digest, profile and mode, scripted inputs, progress predicate, and observation data; a positive progress case and no-input/wrong-input or deliberately broken-predicate controls distinguish real guest progress from a vacuous pass. | Extend the receipt with explicit profile and API-reported execution mode; retain digest-pinned script/predicate and add positive plus targeted negative controls. [VERIFIED: .planning/REQUIREMENTS.md:12; src/runner/acceptance.c:1174-1195; 21-CONTEXT.md, D-03-D-06] |
| FIXT-01 | Game-fixture search is bounded to Potion Panic (GB Compo 2025 demo) first and µCity 1.3 as the sole fallback; each attempt verifies the exact source/build, ROM digest, cartridge header, and CGB mode, and failure of both candidates produces a reasoned absence without a third search. | Two separate bounded candidate gates; Phase 20 admission and notice checks; exact source/build/ROM/header/mode records; honest no-go reasons. [VERIFIED: .planning/REQUIREMENTS.md:16; 21-CONTEXT.md, D-01-D-02] |
| FEED-01 | A concise title/scene/symptom report is enough to start agent-owned reproduction and classification; any resulting automated scene regression has an independent expected behavior and a negative control, while personal ROMs, saves, states, and captures remain outside the repository. | Reuse the lightweight report-to-reproduction workflow; classify the fault boundary before test design; retain unresolved reports when independent oracle or rights evidence is missing. [VERIFIED: .planning/REQUIREMENTS.md:26; 21-CONTEXT.md, D-07-D-09] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- GabbaBoy targets Game Boy and Game Boy Color. Keep the original portable C core, explicit ownership and errors, bounded public operations, and host services in adapters. [VERIFIED: AGENTS.md:23,45-50]
- Use the existing C API, CMake/CTest path, and standard library before proposing new dependencies. Every deliverable needs an automated contract check with a meaningful negative control; do not create human UAT for behavior a contract checker can cover. [VERIFIED: AGENTS.md:32-38,47-48]
- Keep the phase within the existing cap of 12 plans, including the one-plan-per-candidate bound. Keep both automatic-advance flags false and stop at the Phase 21 boundary. [VERIFIED: AGENTS.md:29-35; .planning/ROADMAP.md:60-74]
- Keep software-model progress, independent-oracle results, metamorphic checks, private game observations, and physical-hardware observations distinct. State model applicability, exclusions, and expected failure reasons. [VERIFIED: AGENTS.md:51]
- Do not add Nintendo boot ROMs, commercial images, unlicensed homebrew, private content, or personal media to repository/CI evidence. Every third-party fixture needs documented redistribution terms and a digest; game fixtures stay outside installed and product-release packages under the Phase 20 contract. [VERIFIED: AGENTS.md:52; .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md]
- Keep public artifacts free of personal paths, emails, machine identifiers, and secret values. [VERIFIED: AGENTS.md:53]

## Summary

The project already has the right shared acceptance primitives: bounded ROM and script parsing, ROM/input digest checks, a digest-bound guest predicate, scripted input, named frame checkpoints, PCM observation, receipts, CMake/CTest helpers, and separate model applicability. The main implementation seam is narrow: progress runs currently reject the CGB profile in the per-step frame callback, while the independent frame-digest path already copies and digests RGB555. Bridge that gap without changing the public ABI or weakening existing DMG assertions. [VERIFIED: src/runner/acceptance.c:182-220,697-724,952-1089; src/runner/acceptance.h:22-56,86-111; tests/acceptance/CMakeLists.txt:686-717]

Native CGB mode must be read after load through gbb_get_info and recorded as actual execution mode; a CGB profile and a cartridge header flag are not enough. The current receipt binds ROM/input hashes, predicate, budget, build/revision and observations, but its emitted receipt fields do not explicitly bind the actual API-reported mode. Add that result field and test native-mode acceptance plus explicit rejection of compatibility mode. [VERIFIED: include/gabbaboy/gabbaboy.h:344-350,364-376,390-396; src/runner/acceptance.c:1174-1195; phase decision D-03 in 21-CONTEXT.md]

Candidate choice remains gated by exact source/build identity and Phase 20 rights evidence. The public Potion Panic page separates MIT code and CC BY-NC-SA assets; the µCity author README describes GPL-header-scoped files, a separate BSD-2-Clause GBT Player component, and CC BY-SA media. These labels are evidence to investigate per component, not clearance. Research did not build, run, copy, or download either candidate; it also did not fetch candidate ROMs or assets. [CITED: https://deved.itch.io/potion-panic; https://github.com/AntonioND/ucity; VERIFICATION SCOPE: researcher session]

No concrete current GabbaBoy scene defect with a pinned game release, exact route, and independently specified expected behavior appears in the reviewed phase research. The shortlist contains proposed scenes and historical bug-fix leads from other emulators, explicitly not current GabbaBoy failures. FEED-01 can be planned as a lightweight report-to-reproduction/classification contract; if no actionable symptom is available, retain it as triage instead of inventing a regression. [VERIFIED: .planning/research/2026-10-31-GAME-SCENE-SHORTLIST.md:1-10,36-61; .planning/research/2026-10-31-GAME-FEEDBACK-REVIEW.md:46-74; D-08/D-07 in 21-CONTEXT.md]

**Primary recommendation:** Extend the existing acceptance run path with profile-aware RGB555 progress observation and actual-mode receipt binding; add an original native-CGB harness control and fault-targeted negative controls; run only the ordered, rights-gated two-candidate attempt; keep scene reports unresolved unless reproduction and an independent expectation justify a regression. [VERIFIED: 21-CONTEXT.md, D-01-D-10; src/runner/acceptance.c:182-220,952-1195]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CGB profile execution, actual mode, guest predicate | API / Backend (native C API and runner) | — | Loaded-ROM mode and guest RAM are exposed at the core API boundary; the runner owns deterministic inputs and predicate orchestration. [VERIFIED: include/gabbaboy/gabbaboy.h:364-396; src/runner/acceptance.c:952-1089] |
| RGB555 and PCM observations plus receipt | API / Backend (acceptance adapter) | — | The runner copies completed frames and receives PCM through existing callbacks, then emits the bound result. [VERIFIED: src/runner/acceptance.c:170-220,697-724,1174-1195] |
| Fixture source/build/rights admission | Database / Storage (manifest and static fixture policy) | API / Backend (runner admission gate) | Provenance and notices are static records checked before a fixture is included in the runner's cases. [VERIFIED: tests/scripts/verify-libbet-admission.py; fixtures/libbet/manifest.json; cmake/VerifyFixtureManifest.cmake; cmake/ScanForbiddenFixtures.cmake] |
| Scene report reproduction and classification | API / Backend (native runner plus report workflow) | — | Report metadata starts an agent-owned investigation; only a minimized case with independent expected behavior becomes an automated test. [VERIFIED: 21-CONTEXT.md, D-07-D-09; .planning/research/2026-10-31-GAME-FEEDBACK-REVIEW.md:46-74] |
| Automated verification | API / Backend (CMake/CTest) | — | Existing acceptance and fixture checks use the project CMake/CTest test tree; new checks should follow the same path. [VERIFIED: tests/acceptance/CMakeLists.txt:142-158,686-717] |

## Standard Stack

### Core

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Existing portable C core and public API | Existing project code | CGB profile, loaded execution mode, frame copy, RAM predicate reads | It already owns emulator state and exposes bounded operations; do not create a parallel emulator or public ABI. [VERIFIED: AGENTS.md:45-50; include/gabbaboy/gabbaboy.h:344-396,415-433] |
| Existing shared acceptance runner | Existing project code | Input scripts, guest predicates, observations, receipt and model accounting | It already implements all acceptance concerns except RGB555 progress-frame integration. [VERIFIED: src/runner/acceptance.c:182-243,952-1195] |
| CMake and CTest | Project test configuration | Build/register positive, negative, and fixture-policy checks | Current CGB digest and progress-refusal cases are registered here. [VERIFIED: tests/acceptance/CMakeLists.txt:686-717] |
| Python standard library | No third-party package | Source/build/fixture provenance and static contract checker, where needed | The fixture-admission checker precedent is a standalone Python checker integrated into project checks. [VERIFIED: tests/scripts/verify-libbet-admission.py; .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md] |

### Supporting candidate build tools

| Tool | Publicly stated role | Environment observation | Planning consequence |
|------|----------------------|-------------------------|----------------------|
| RGBDS | Potion Panic source README requires RGBDS; µCity author README says a recent RGBDS is needed. [CITED: https://github.com/gbcompo25/potion-panic; https://github.com/AntonioND/ucity] | rgbasm and rgbfix are present at v1.0.4. [VERIFIED: command availability/version probe, 2026-11-01] | Pin the required tool version and exact source before build; presence alone does not prove candidate compatibility. |
| Python 3 | Potion Panic source README lists it as a build requirement. [CITED: https://github.com/gbcompo25/potion-panic] | Python 3.14.4 is present. [VERIFIED: command availability/version probe, 2026-11-01] | Do not infer support from presence alone; check the pinned source's own scripts during admission. |
| GNU make | µCity README directs running make after RGBDS is available. [CITED: https://github.com/AntonioND/ucity] | GNU Make 3.81 is present. [VERIFIED: command availability/version probe, 2026-11-01] | Pin build inputs and command/flags in the candidate record. |
| SuperFamiconv | Potion Panic source README lists it as a build requirement. [CITED: https://github.com/gbcompo25/potion-panic] | Not found on PATH. [VERIFIED: command availability probe, 2026-11-01] | Potion Panic build is currently blocked if the pinned build uses it; do not silently omit or replace it. The research task did not install it. |

**Installation:** No project dependency installation is in scope. Phase decisions prefer existing CMake/CTest and standard-library tooling. Candidate-specific build-tool acquisition was not done during research. [VERIFIED: 21-CONTEXT.md, D-10; researcher session]

**Package Legitimacy Audit:** Not applicable: this phase adds no application package dependency. Candidate ROM build tools are environment tools, not dependencies to add to GabbaBoy. [VERIFIED: 21-CONTEXT.md, D-10]

## Architecture Patterns

### System Architecture Diagram

```text
Rights/source/build gate (candidate-specific, ordered)
    -> pinned ROM bytes + manifest + notices
    -> shared runner validates ROM/script digests and predicate anchors
    -> create selected software profile and load ROM
    -> read loaded-ROM mode via public info API
       -> reject non-native CGB mode for the CGB-positive case
       -> retain DMG behavior on the established DMG case
    -> deterministic scripted input + bounded drive
       -> guest predicate at frame boundary
       -> completed RGB555 frame observation + PCM observation
    -> bound receipt (ROM/input/predicate/profile/mode/budget/checkpoints/build)
    -> CTest assertions: positive, wrong/no input, broken predicate, wrong mode

Scene report (title + scene + symptom)
    -> recover exact title/release/model/route metadata
    -> reproduce at lowest useful boundary
    -> classify core / conversion / host / original behavior / unknown
       -> minimized case + independent expected behavior + targeted negative control
          -> automated regression
       -> missing oracle/rights/reproduction evidence
          -> unresolved triage with concrete blocker
```

The diagram is the recommended path through the locked candidate, harness and scene contracts. Existing code validates case/input/ROM data before guest creation, then invokes shared acceptance driving with the script, predicate, fixed budget and callbacks. [VERIFIED: 21-CONTEXT.md, D-01-D-10; src/runner/acceptance.c:952-1089]

### Recommended Project Structure

No parallel test framework or new public API is needed. Keep case data and scripts under the established acceptance tree; keep fixture admission records beside the fixture; put reusable source-bound checkers in tests/scripts/ and register them from CMake/CTest. [VERIFIED: 21-CONTEXT.md, code_context; tests/acceptance/CMakeLists.txt; tests/scripts/verify-libbet-admission.py; cmake/VerifyFixtureManifest.cmake]

### Pattern 1: Read actual execution mode after ROM load

**What:** Query gbb_get_info on the live instance after successful gbb_load_rom and assert the reported mode is native CGB before recording a CGB positive. Keep profile selection, raw cartridge CGB header, and execution-mode output as separate fields. [VERIFIED: include/gabbaboy/gabbaboy.h:344-396]

The public enum is:

    GBB_MODE_NONE = 0,
    GBB_MODE_DMG = 1,
    GBB_MODE_CGB = 2,
    GBB_MODE_CGB_DMG_COMPAT = 3

This exact enum and the mode field's meaning are defined in [VERIFIED: include/gabbaboy/gabbaboy.h:344-350,364-376,390-396]. The header says the reported mode is the loaded ROM's profile-plus-header execution mode, remains constant across reset, and changes only when a load succeeds. Use this value in the result receipt and negative-control assertion; do not infer native mode from the profile or raw header alone. [VERIFIED: include/gabbaboy/gabbaboy.h:344-350,390-396; 21-CONTEXT.md, D-03]

The selected profile values are:

    GBB_PROFILE_DMG_CPU_B = 1,
    GBB_PROFILE_CGB_CPU_E = 2

The runner's model tokens are:

    dmg-cpu-b / cgb-cpu-e

These values are quoted from the public profile enum and runner mapping comments. [VERIFIED: include/gabbaboy/gabbaboy.h:13-16; src/runner/acceptance.h:94-107]

### Pattern 2: Add CGB RGB555 to the progress callback without regressing DMG

**What:** Keep one shared acceptance drive and dispatch frame copy by profile: use the existing DMG copy path for DMG and gbb_copy_frame_rgb555 for the CGB profile. Preserve generation checks, named checkpoint handling, predicate boundary tracking and callback error propagation. [VERIFIED: src/runner/acceptance.c:182-243,697-724]

**Why this is the seam:** The progress callback currently sets the error string to the exact value “frame-unsupported-profile” for CGB before copying a frame; the separate capture path already selects RGB555 and uses the CGB frame-copy API. Existing CTest explicitly asserts the refusal, and existing CGB digest cases assert RGB555 output and flipped-reference failure. Replace the obsolete refusal expectation only after a positive CGB progress path and mode controls exist. [VERIFIED: src/runner/acceptance.c:182-220,697-724; tests/acceptance/CMakeLists.txt:686-717]

The public frame API defines 160x144 RGB555 values, bit 15 clear, and explicit little-endian byte serialization for digests. The raw RGB555 output is a deterministic observation; it has no built-in color correction or correctness oracle. [VERIFIED: include/gabbaboy/gabbaboy.h:415-433]

### Pattern 3: Bind a positive predicate to exact input, ROM and observations

**What:** Reuse the case format's ROM SHA-256/size, input script/SHA-256, profile/model applicability, predicate name and fixed half-dot budget. Keep the predicate tied to the ROM digest and source-anchored bytes; require meaningful input-driven state transition within budget. Record the loaded mode explicitly with profile and named frame/PCM checkpoint observations. [VERIFIED: src/runner/acceptance.h:37-56,86-111; src/runner/acceptance.c:973-1015,1017-1089,1174-1195]

Use independent proof layers: positive input reaches a guest predicate; no-input or wrong-input fails that predicate; deliberately broken predicate also fails; compatibility-mode input is rejected for the native-CGB requirement. Each negative control must assert the raw failing reason, so expected-failure wrapping cannot convert unrelated setup or parser errors into a green control. Existing DMG tests assert raw predicate failure separately from strict expected-failure mapping. [VERIFIED: tests/acceptance/CMakeLists.txt:142-158; 21-CONTEXT.md, D-05]

### Pattern 4: Treat scene reports as evidence intake, not self-validating oracles

**What:** Accept title, scene and symptom as sufficient to begin metadata recovery and agent-owned reproduction. Record release/content identity, profile plus actual mode, script/route, guest-time/frame boundary, capture layer, expected behavior, suspected alternatives and uncertainty as they become available. Classify core behavior separately from conversion, host presentation, original-game behavior and unknown. Promote only a minimized reproducible case with an independently derived expectation and a relevant fault-specific negative control. [VERIFIED: 21-CONTEXT.md, D-07-D-09; .planning/research/2026-10-31-GAME-FEEDBACK-REVIEW.md:46-74]

**When to use:** Use static independent pixel expectations only for a genuinely static scene. Use a bounded frame sequence or semantic/event invariant for motion, timing and audio. A game's own failed output or a deterministic self-captured digest is not the expected result. [VERIFIED: 21-CONTEXT.md, D-06-D-07]

### Anti-Patterns to Avoid

- **Use profile/header as proof of native mode:** Read the loaded instance's mode and bind it. Profile is the selected silicon model, while the mode is determined by profile plus the loaded ROM header. [VERIFIED: include/gabbaboy/gabbaboy.h:344-350,390-396]
- **Reuse DMG acceptance gates blindly for CGB:** Existing shade-count and audible-PCM thresholds belong to a specific established case; require an independent reason before applying them to a CGB game. [VERIFIED: 21-CONTEXT.md, D-07]
- **Promote output digest as accuracy oracle:** Digests only bind repeatable output. A self-derived golden can faithfully preserve the defect. [VERIFIED: 21-CONTEXT.md, D-06-D-07; .planning/ROADMAP.md:74]
- **Treat candidate gate failure as emulator failure:** Rights, exact source/build, tooling and predicate-feasibility failures are candidate no-go reasons; a reproduced core defect is separate and must not be hidden by absence. [VERIFIED: 21-CONTEXT.md, D-02; .planning/ROADMAP.md:68-74]
- **Treat legal labels or free downloads as permission:** Verify each code, art, audio/driver, build-input and notice component for repository/public-CI use under Phase 20. [VERIFIED: 21-CONTEXT.md, D-02; .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md]
- **Make a new regression from a report screenshot/hash:** Keep reports unresolved when there is no independent expectation or targeted negative control. Personal artifacts remain private. [VERIFIED: 21-CONTEXT.md, D-07-D-09]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ROM/script parsing, size bounds and SHA checks | Another file/parser or generic game runner | Existing case parser, file reader and SHA helpers | Existing runner performs bounds, digest, syntax, ROM-size and predicate-anchor validation before instance creation. [VERIFIED: src/runner/acceptance.c:952-1015; src/runner/acceptance.h:22-35,63-84] |
| Guest progress and input replay | A host-side screen heuristic or a second play harness | Existing input scripts, gbb_accept_drive and guest-memory predicate | Existing proof is deterministic guest state under scripted input; UI appearance is a different evidence layer. [VERIFIED: src/runner/acceptance.c:222-243,1076-1089; docs/game-acceptance.md:22-30] |
| CGB frame copy and digest serialization | Custom framebuffer access or host color conversion | gbb_copy_frame_rgb555 and existing RGB555 digest helper | Public API defines bounds, bit layout, and little-endian digest bytes. [VERIFIED: include/gabbaboy/gabbaboy.h:415-433; src/runner/acceptance.c:713-724] |
| Fixture admission/forbidden-package checks | A second rights schema or ad-hoc ROM ban | Phase 20 manifest/notice and package-boundary checks | Reuse the adopted contract and its mutation-tested checks. [VERIFIED: .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md; cmake/VerifyFixtureManifest.cmake; cmake/ScanForbiddenFixtures.cmake] |
| Scene automation from a screenshot | Pixel golden from the observed failing output | The smallest independent pixel, sequence, semantic, or event expectation plus a targeted negative control | Output repeatability is not correctness; the expected behavior has to be reasoned independently. [VERIFIED: 21-CONTEXT.md, D-06-D-07] |

**Key insight:** The project already separates progress predicates from RGB555/PCM observations. Keep that separation: guest state demonstrates input-driven progress; observations make an exact run reproducible; independent expectations and targeted controls are required to make a scene regression detect a fault. [VERIFIED: docs/game-acceptance.md:22-59; 21-CONTEXT.md, D-04-D-07]

## Candidate Source, Build, and Provenance Constraints

### Potion Panic — first and only primary attempt

- The creator page labels code MIT and assets CC BY-NC-SA 4.0, lists A jump, B shoot, left/right move, and Start pause, and names the downloadable artifact as the GB Compo 2025 demo. These creator-page facts are not a complete per-component license review or permission for project redistribution. [CITED: https://deved.itch.io/potion-panic]
- The creator page links to Codeberg at DevEd/potion-panic, but that source page could not be fetched by the research browser. The separately indexed GitHub repo identifies itself as a fork of DevEd2/potion-panic; its README says to clone DevEd2's repo recursively, lists RGBDS, Python 3 and SuperFamiconv, then run build.sh, and says macOS buildability is unverified by that maintainer. Pin the creator-controlled upstream identity, source commit, recursive submodules and any generated/bundled assets before a phase build. Do not assume that the fork's current tree, itch ROM or an older candidate digest is the matching source-built result. [CITED: https://deved.itch.io/potion-panic; https://github.com/gbcompo25/potion-panic]
- Planning lead only: the page controls make a short input route conceivable, but the exact source/state variable, title transition, ROM header and CGB execution mode have not been source-verified here. The admission attempt must establish a source-anchored progress predicate and exact build/artifact identity before adding a positive case. [CITED: https://deved.itch.io/potion-panic] [ASSUMED]
- Phase 20 gate: resolve code, artwork, audio/driver, tool/build inputs and notices independently, then bind exact source/build, ROM size/digest, parsed cartridge metadata, raw CGB flag and loaded API mode. If any rights or identity field is unresolved, record no-go; do not label it an emulator failure. [VERIFIED: 21-CONTEXT.md, D-01-D-02; .planning/REQUIREMENTS.md:14-17]

### µCity 1.3 — sole fallback after recorded primary no-go

- The author README calls µCity 1.3 a Game Boy Color-only game, identifies ucity.gbc as the preferred ROM, and distinguishes ucity_compat.gbc by its lower save capacity. Phase scope selects only the preferred ucity.gbc artifact. The README points to Codeberg releases; pin an exact release/source commit rather than a mutable default branch before the attempt. [CITED: https://github.com/AntonioND/ucity; VERIFIED: 21-CONTEXT.md, D-01]
- The author README says recent RGBDS plus make builds the game. It describes GPLv3+ only for source files carrying the GPL header, separately licensed GBT Player under BSD-2-Clause, and graphics/music under CC BY-SA 4.0. This mixed-component statement is a map for per-file/source/media review, not a blanket clearance. [CITED: https://github.com/AntonioND/ucity]
- The manual says random-map seeds recreate the same map and describes SELECT for the build menu, B for movement without the cursor, A to identify a tile, and simulation steps that can temporarily prevent actions. These facts can guide a source-inspection hypothesis for a short progress predicate; they do not prove a guest-memory predicate, route, or run budget. Inspect exact source variables and then validate with an independent input/no-input pair. [CITED: https://github.com/AntonioND/ucity/blob/master/manual.rst] [ASSUMED]
- Keep this attempt distinct from the Potion Panic attempt and run it only after its no-go is recorded. If it also fails a real gate, name its exact blocker and the harness result. No third candidate is in scope. [VERIFIED: 21-CONTEXT.md, D-01-D-02; .planning/ROADMAP.md:68-74]

### Required record for either candidate

1. Exact upstream repository and immutable commit/tag plus recursively fetched submodule identities; build script, build inputs, tool versions and flags. [VERIFIED: 21-CONTEXT.md, D-02; .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md]
2. Resulting ROM byte size and SHA-256, source/build-to-ROM relationship, parsed title/mapper/ROM/RAM size/CGB flag, and loaded gbb_info mode from the profile instance. A profile label or header-only parse is insufficient for native-mode admission. [VERIFIED: .planning/REQUIREMENTS.md:16; include/gabbaboy/gabbaboy.h:364-396]
3. Per-component redistribution terms/notices for code, art, audio driver, generators/converters, and other build inputs; exact notice files/hashes and Phase 20 admission decision. Public availability, a digest or a title-level license label alone does not clear this gate. [VERIFIED: 21-CONTEXT.md, D-02; .planning/REQUIREMENTS.md:16-17]
4. Acceptance case binding ROM and input hashes, progress predicate and anchors, profile and actual mode, deterministic half-dot budget, named observation checkpoints and build/revision-qualified receipt. [VERIFIED: src/runner/acceptance.h:37-56; src/runner/acceptance.c:1174-1195; 21-CONTEXT.md, D-04]
5. Explicit candidate disposition: admitted with evidence; no-go for rights, source/build identity, missing tooling/build failure, no feasible independent predicate, harness failure, or reproduced emulator defect. An unresolved correctness/security defect is not an acceptable candidate-absence explanation. [VERIFIED: 21-CONTEXT.md, D-02; .planning/ROADMAP.md:68-74]

## Common Pitfalls

### Pitfall 1: CGB observation paths diverge

**What goes wrong:** Frame-digest observation succeeds but progress acceptance still returns the explicit refusal “frame-unsupported-profile”. [VERIFIED: src/runner/acceptance.c:182-195,713-718]

**Why it happens:** The progress callback always calls the DMG frame-copy API after checking capture profile and rejects CGB before observing a completed frame; the separate checkpoint path already copies RGB555. [VERIFIED: src/runner/acceptance.c:182-195,697-724]

**How to avoid:** Add CGB RGB555 dispatch inside the shared progress observation path, keep generation/boundary semantics unchanged, and preserve a DMG before/after identity assertion. [VERIFIED: 21-CONTEXT.md, D-03; tests/acceptance/CMakeLists.txt:658-684]

**Warning signs:** The CGB digest case passes but any positive CGB predicate case still reports the old refusal; or the DMG receipt changes unexpectedly. [VERIFIED: tests/acceptance/CMakeLists.txt:658-717; 21-CONTEXT.md, D-03]

### Pitfall 2: Selected CGB profile is mistaken for native CGB execution

**What goes wrong:** A compatibility-mode run can be reported as native CGB because the runner requested the CGB profile or parsed a supporting header byte. [VERIFIED: include/gabbaboy/gabbaboy.h:344-350,390-396; 21-CONTEXT.md, D-03]

**How to avoid:** Read gbb_info after loading the ROM, require the native CGB mode for the positive case, add compatibility-mode rejection control, and bind reported mode in the receipt. [VERIFIED: include/gabbaboy/gabbaboy.h:364-396; 21-CONTEXT.md, D-03-D-05]

### Pitfall 3: Progress control fails for the wrong reason

**What goes wrong:** A missing or wrong input control passes as an expected failure because a parser error, ROM mismatch, unsupported model or mode rejection prevented the predicate from running. [VERIFIED: src/runner/acceptance.c:973-1015; tests/acceptance/CMakeLists.txt:142-158]

**How to avoid:** Assert the raw predicate failure separately from the strict expected-failure mapping. The existing documented raw control status is “status=fail model=dmg-cpu-b reason=predicate-not-reached”; test deliberate predicate corruption separately and keep mode rejection as its own control. [VERIFIED: docs/game-acceptance.md:38-51; tests/acceptance/CMakeLists.txt:142-158; 21-CONTEXT.md, D-05]

### Pitfall 4: Digests become a self-confirming oracle

**What goes wrong:** Repeating the same emulator output or selecting a failing screenshot as its own reference freezes an incorrect result. [VERIFIED: 21-CONTEXT.md, D-06-D-07]

**How to avoid:** Bind digest and checkpoint time as observation. Derive expected behavior from independently specified game behavior, source logic, a rights-cleared independent oracle, or a justified property. For moving/audio reports use a bounded sequence or semantic invariant. [VERIFIED: 21-CONTEXT.md, D-06-D-07]

### Pitfall 5: Source/build/asset identity is incomplete

**What goes wrong:** A game title, mutable branch, ROM download, one root license or matching digest is treated as proof for all bytes and build inputs. [VERIFIED: 21-CONTEXT.md, D-02; .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md]

**How to avoid:** Pin exact source and recursive inputs, reconcile build outputs and all code/art/audio/tool/data licenses and notices, record ROM bytes/header and loaded mode, then apply package exclusion checks. [VERIFIED: .planning/REQUIREMENTS.md:16-17; .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md]

### Pitfall 6: A report is made into an artificial bug or golden

**What goes wrong:** A historical issue in another emulator or a vague “this looks wrong” is assigned as a GabbaBoy defect without exact content/scene/expected behavior. [VERIFIED: .planning/research/2026-10-31-GAME-SCENE-SHORTLIST.md:36-40]

**How to avoid:** Recover title/revision/model/scene metadata and compare core output, color conversion and host presentation before assigning a boundary. If no independent expectation or targeted negative control exists, retain triage and name the missing evidence. [VERIFIED: .planning/research/2026-10-31-GAME-FEEDBACK-REVIEW.md:61-74; 21-CONTEXT.md, D-07-D-09]

### Pitfall 7: Candidate tooling assumptions hide a no-go

**What goes wrong:** The first game's build is presumed runnable because some RGBDS binaries exist, even though the source README also lists Python and SuperFamiconv; µCity says “recent RGBDS” but does not pin the version in the README. [CITED: https://github.com/gbcompo25/potion-panic; https://github.com/AntonioND/ucity]

**How to avoid:** Record exact candidate build closure and required versions before spending time on the runner. If a required tool is absent or version fit is unknown, distinguish that blocker from emulator behavior. Do not install or silently substitute build tools during a rights/source research gate. [VERIFIED: environment availability probe, 2026-11-01; 21-CONTEXT.md, D-02]

## Code Examples

### Mode-check and capture sequence

    after successful ROM load:
        initialize the public info structure using its current size handshake
        call gbb_get_info on the loaded instance
        require info.mode == native CGB execution mode for the CGB positive case
        copy completed frames with gbb_copy_frame_rgb555 on the CGB profile
        serialize each 16-bit pixel as little-endian bytes for the frame digest
        bind the API-reported mode and the named observations into the receipt

The exact mode enum and frame byte contract are quoted above from the header. [VERIFIED: include/gabbaboy/gabbaboy.h:344-350,390-396,415-433]

### Candidate independent-predicate design

    source pin + build closure + rights decision
        -> inspect an externally meaningful guest state transition
        -> bind digest and expected state/anchor bytes to that ROM
        -> choose deterministic input event(s) and fixed guest-time budget
        -> positive: input reaches predicate
        -> negative: no/wrong input does not reach predicate
        -> negative: deliberately altered predicate does not pass
        -> negative: compatibility mode is rejected when native CGB is required

This is a plan shape, not a verified predicate for either candidate. The exact state field and route remain source/build-gated. [VERIFIED: 21-CONTEXT.md, D-02-D-05] [ASSUMED]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CGB checkpoint capture only | CGB checkpoint capture exists; CGB progress callbacks still explicitly refuse the profile | Existing implementation; Phase 21 closes the integration gap | Reuse RGB555 and add progress-mode handling rather than replace the runner. [VERIFIED: src/runner/acceptance.c:182-195,713-718; tests/acceptance/CMakeLists.txt:686-717] |
| Emulator output digest used as a result label | Predicate-based progress with digests bound as observations | Existing project acceptance contract | Progress and output repeatability stay separate evidence claims. [VERIFIED: docs/game-acceptance.md:22-59; 21-CONTEXT.md, D-04-D-07] |

**Deprecated/outdated:**

- The existing CGB progress-refusal case is valid regression evidence for the pre-Phase-21 gap. Once native CGB progress is implemented, replace it with a targeted mode/profile refusal or a new assertion that the admitted CGB progress path is supported; do not delete the rejection without replacing its behavior coverage. [VERIFIED: tests/acceptance/CMakeLists.txt:715-717; 21-CONTEXT.md, D-03-D-05]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Potion Panic's exact source exposes a stable guest-state predicate reachable with a short scripted route. [ASSUMED] | Candidate source/build constraints | If false, the primary attempt can be a valid predicate-feasibility no-go after its source/build/rights gates; it must not become a screen heuristic. |
| A2 | µCity 1.3's pinned source exposes a bounded predicate that changes under a short deterministic action from a reproducible start. [ASSUMED] | Candidate source/build constraints | If false, fallback records predicate-feasibility no-go; manual controls and a fixed map seed alone are insufficient. |
| A3 | A small original native-CGB control ROM can exercise the runner's positive, input-negative, predicate-negative and mode-negative paths with the existing software profile. [ASSUMED] | Architecture and validation | If false, harness failure is reported separately from candidate absence and requires rescope rather than a claimed fixture success. |

## Open Questions (RESOLVED)

These questions are resolved for planning by the bounded execution contracts below. Exact candidate identity, rights, tool compatibility and build/progress results remain unverified execution evidence; the resolution does not admit a fixture or claim that an unknown fact has been established.

1. **Potion Panic exact source/build/rights closure (RESOLVED for planning):** Which creator-controlled immutable source commit and recursive submodules produce the GB Compo 2025 demo, and can all art/audio/tool inputs be admitted for repository and public-CI use?
   - What we know: The creator page separates code and asset license labels; the available GitHub page is a fork whose README points back to the upstream recursive clone. [CITED: https://deved.itch.io/potion-panic; https://github.com/gbcompo25/potion-panic]
   - What is unclear: The live Codeberg source was not retrievable through the research browser, and this research did not establish exact source-to-ROM identity or per-component clearance. [VERIFIED: researcher source-fetch attempt; 21-CONTEXT.md, D-02]
   - Planning resolution (RESOLVED): Plan 21-04 Task 1 is the single primary attempt. It must establish creator-controlled source authority, immutable recursive inputs, component grants and one reproducible toolchain before building or admitting bytes. Any source/rights/build identity that cannot be established becomes a concrete no-go with later observations marked not-observed. An available build runs only after its restricted environment and denial probes are established; unavailable isolation is a build-isolation no-go. This is a resolved plan branch, not verified candidate evidence. [VERIFIED: 21-04-PLAN.md, Task 1; 21-CONTEXT.md, D-01-D-02]

2. **Potion Panic builder environment (RESOLVED for planning):** Is SuperFamiconv required by the exact pinned source, and is the locally installed RGBDS version compatible?
   - What we know: The indexed README lists RGBDS, Python 3 and SuperFamiconv; local RGBDS/Python/make exist but SuperFamiconv does not. [CITED: https://github.com/gbcompo25/potion-panic; VERIFIED: command availability/version probe, 2026-11-01]
   - What is unclear: Exact upstream build closure and version compatibility. [VERIFIED: researcher source-fetch attempt; CITED: https://github.com/gbcompo25/potion-panic]
   - Planning resolution (RESOLVED): Plan 21-04 Task 1 inspects the pinned recipe to determine whether SuperFamiconv is required and which tool versions are compatible. A necessary build-only tool may be acquired and digest-verified in the temporary acquisition area under the existing plan, then exposed read-only inside the restricted build environment. A required tool that is unavailable, unpinnable, incompatible with the single documented recipe, or unusable under the isolation policy produces a concrete build no-go. No global installation, repeated tool-version search or project runtime dependency is authorized. Tool compatibility remains pending execution evidence. [VERIFIED: 21-04-PLAN.md, Task 1; 21-CONTEXT.md, D-02/D-10]

3. **µCity 1.3 fallback exact release (RESOLVED for planning):** Which immutable author release/source commit corresponds to preferred ucity.gbc and provides a complete rights/build manifest?
   - What we know: The author README names preferred ucity.gbc and links Codeberg releases; the default and compatibility ROMs differ. [CITED: https://github.com/AntonioND/ucity]
   - What is unclear: Exact release digest, source-built correspondence, per-file/media terms, and required recent RGBDS version. [VERIFIED: researcher source-review scope; CITED: https://github.com/AntonioND/ucity]
   - Planning resolution (RESOLVED): Plan 21-05 is eligible only after the checked primary no-go. Its first task pins the author-controlled µCity 1.3 release/source and preferred ucity.gbc, component grants, recursive inputs and compatible toolchain; inability to establish identity, rights, the bounded build or its isolation produces a concrete no-go. An admitted primary instead yields a checked not-needed fallback record. No other release/artifact or third game is substituted. Exact fallback evidence remains pending the eligible execution branch. [VERIFIED: 21-05-PLAN.md, Task 1; 21-CONTEXT.md, D-01-D-02]

4. **Actionable current scene report (RESOLVED for planning):** Is there a specific title/scene/symptom report available to reproduce now?
   - What we know: Existing research provides scouting scenes and historical issue leads, not a confirmed GabbaBoy defect with a reproducible expected behavior in the reviewed phase sources. [VERIFIED: .planning/research/2026-10-31-GAME-SCENE-SHORTLIST.md:1-10,36-61; .planning/research/2026-10-31-GAME-FEEDBACK-REVIEW.md:46-74]
   - What is unclear: Exact current report, content release, observed boundary and independent oracle. [VERIFIED: reviewed phase-research scope; 21-CONTEXT.md, D-07-D-09]
   - Planning resolution (RESOLVED): The reviewed sources contain no current actionable GabbaBoy report. Plan 21-06 therefore delivers and tests title/scene/symptom intake, agent-owned metadata recovery/classification and the independent-expectation promotion contract with synthetic subjects. If a real report arrives it follows that contract; if none arrives, the final record states no live scene regression was available. A report without permitted reproduction or an independent expectation stays triage. No invented defect, captured golden or mandatory owner play fills that evidence limit. [VERIFIED: 21-06-PLAN.md, Tasks 1-2; 21-CONTEXT.md, D-07-D-09]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| CMake | Existing project verification | ✓ | 4.4.3 | — [VERIFIED: command availability/version probe, 2026-11-01] |
| CTest | Existing project verification | ✓ | 4.4.3 | — [VERIFIED: command availability/version probe, 2026-11-01] |
| Python 3 | Candidate scripts and stdlib fixture checker | ✓ | 3.14.4 | — [VERIFIED: command availability/version probe, 2026-11-01] |
| GNU make | µCity author build instructions | ✓ | 3.81 | — [VERIFIED: command availability/version probe, 2026-11-01] |
| RGBDS rgbasm/rgbfix | Both candidate source build leads | ✓ | 1.0.4 | —; confirm exact-source version compatibility. [VERIFIED: command availability/version probe, 2026-11-01] |
| SuperFamiconv | Potion Panic indexed README build requirements | ✗ | — | No evidenced substitute; Plan 21-04 permits bounded pinned acquisition only for the exact recipe and restricted build. If the required tool cannot be established, record build no-go. [CITED: https://github.com/gbcompo25/potion-panic; VERIFIED: command availability probe, 2026-11-01; 21-04-PLAN.md, Task 1] |

**Missing dependencies with no fallback:**

- SuperFamiconv, if the pinned Potion Panic source's build closure requires it. The missing tool has not been installed and no candidate build has been attempted. [VERIFIED: command availability probe, 2026-11-01; CITED: https://github.com/gbcompo25/potion-panic]

**Missing dependencies with fallback:**

- None verified.

The project's configured full validation command is:

    cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error

This was read from the project workflow config; it was not run during this research task. [VERIFIED: .planning/config.json:54]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | CMake/CTest, existing project suite |
| Config file | Existing project CMake preset referenced by the workflow config; acceptance cases are registered in tests/acceptance/CMakeLists.txt. [VERIFIED: .planning/config.json:54; tests/acceptance/CMakeLists.txt] |
| Quick run command | After the configured build, run ctest --preset phase1 --output-on-failure -R 'acceptance_cgb_progress|cgb_runner_profile_dmg_identity_acceptance'. Plan new short-budget cases under the acceptance_cgb_progress prefix. |
| Full suite command | cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error |

The full-suite command is configured in .planning/config.json. Phase 21's new cases belong in the current CMake/CTest path and should be bounded. [VERIFIED: .planning/config.json:54; tests/acceptance/CMakeLists.txt:142-158,658-717]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| GAME-01 | CGB profile copies RGB555 frames during predicate-driven progress; DMG acceptance still has byte-identical receipt/output behavior. | integration | ctest --preset phase1 --output-on-failure -R 'acceptance_cgb_progress|acceptance_cgb_colour|cgb_runner_profile_dmg_identity_acceptance' (planned progress prefix plus existing controls). | CGB digest and DMG identity patterns exist; CGB progress support does not yet exist. [VERIFIED: tests/acceptance/CMakeLists.txt:658-717] |
| GAME-02 | Positive input reaches a source-bound predicate; no/wrong input and broken predicate fail; result binds ROM/script/predicate/profile/mode/observations. | integration | ctest --preset phase1 --output-on-failure -R 'acceptance_cgb_progress' (planned positive, raw no-input/wrong-input, broken-predicate and mode controls). | DMG analogues exist; new CGB case/controls needed. [VERIFIED: tests/acceptance/CMakeLists.txt:142-158,715-717; src/runner/acceptance.c:1174-1195] |
| FIXT-01 | Exactly two ordered, bounded candidate gates with source/build/ROM/header/mode/rights record and reasoned two-candidate absence. | unit/integration | ctest --preset phase1 --output-on-failure -R 'phase21_fixture_admission' (proposed selector for the admission checker positive and mutation controls). | Phase 20 checker and manifest patterns exist; Phase 21 candidate record needed. [VERIFIED: tests/scripts/verify-libbet-admission.py; cmake/VerifyFixtureManifest.cmake; 21-CONTEXT.md, D-01-D-02] |
| FEED-01 | Minimal title/scene/symptom starts agent-owned triage/classification; any promoted regression has independent expected behavior and targeted negative control; private artifacts excluded. | unit/automated | ctest --preset phase1 --output-on-failure -R 'phase21_scene_report' (proposed selector for minimal-report acceptance and promotion-contract negative controls). | Existing project privacy and test-contract patterns exist; no current actionable GabbaBoy scene report was found in reviewed research. [VERIFIED: AGENTS.md:32,51-53; 21-CONTEXT.md, D-07-D-09] |

### Sampling Rate

- Per task commit: run the smallest focused CTest for the changed acceptance, fixture, or report contract. [VERIFIED: AGENTS.md:32-38]
- Per wave merge: run the full configured CTest command. [VERIFIED: .planning/config.json:54; AGENTS.md:32-38]
- Phase gate: final suite must be green before verify-work. Preserve current phase-level limits on review/fix and gap rounds. [VERIFIED: AGENTS.md:33-38]

### Wave 0 Gaps

- [ ] Add a small original native-CGB control ROM and explicit provenance/build record if no candidate is admitted; use it for harness proof only. [VERIFIED: 21-CONTEXT.md, D-05]
- [ ] Add CGB progress positive and mode/input/predicate negative tests in the existing CMake/CTest acceptance path. [VERIFIED: tests/acceptance/CMakeLists.txt:686-717; GAME-01/GAME-02]
- [ ] Add or extend an immutable-source fixture admission checker for both candidate records and its meaningful malformed-record controls. [VERIFIED: .planning/phases/GB-20-fixture-admission-tune-up/20-CONTEXT.md; tests/scripts/verify-libbet-admission.py]
- [ ] Add a report-intake/scene-promotion contract check if a real symptom cannot be promoted in this phase. No report should be invented to fill this gap. [VERIFIED: 21-CONTEXT.md, D-07-D-09]

## Security Domain

Security enforcement is enabled at ASVS level 1. [VERIFIED: .planning/config.json:48-50]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No authentication surface is added by the local runner/fixture workflow. [VERIFIED: phase scope in 21-CONTEXT.md] |
| V3 Session Management | No | No sessions or network user accounts are in the phase boundary. [VERIFIED: phase scope in 21-CONTEXT.md] |
| V4 Access Control | No | No server-side authorization boundary is added; filesystem and package scope still require checks. [VERIFIED: AGENTS.md:47,52-53] |
| V5 Input Validation | Yes | Reuse bounded case/script/ROM readers, path checks, SHA/size checks, and reject malformed or mismatched input before instance creation. [VERIFIED: src/runner/acceptance.c:973-1015; src/runner/acceptance.h:22-35,63-84] |
| V6 Cryptography | Limited | Do not create crypto or treat SHA-256 as authorization; reuse the project digest helper only for byte identity and receipt binding. [VERIFIED: src/runner/acceptance.c:978-1007,1174-1195; AGENTS.md:50] |

### Known Threat Patterns for the native runner and fixture pipeline

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Oversized or malformed case/script/ROM input | Tampering / denial of service | Preserve size caps, line/event bounds, exact digests, path containment and validation before guest creation. [VERIFIED: src/runner/acceptance.h:22-35,63-84; src/runner/acceptance.c:973-1015] |
| A wrong fixture is accepted under a trusted game identity | Spoofing / tampering | Pin source/build closure, result size/digest/header/CGB flag and loaded actual mode; assert meaningful mutations fail. [VERIFIED: 21-CONTEXT.md, D-02-D-05; .planning/REQUIREMENTS.md:16] |
| Private ROM/save/state/capture leaks into Git or public CI | Information disclosure | Use only original or rights-admitted test fixtures; retain personal data outside repository/CI and keep privacy-safe paths out of public artifacts. [VERIFIED: AGENTS.md:52-53; 21-CONTEXT.md, D-09] |
| Expected-failure test masks a setup failure | Tampering / false assurance | Assert the raw expected predicate failure reason separately from expected-failure mapping; add fault-specific negative controls. [VERIFIED: docs/game-acceptance.md:38-51; tests/acceptance/CMakeLists.txt:142-158] |

## Sources

### Primary in-repo sources (HIGH confidence)

- [AGENTS.md](../../../AGENTS.md) — project constraints; lines 23-53.
- [21-CONTEXT.md](21-CONTEXT.md) — locked decisions D-01 through D-10 and approved phase boundary.
- [REQUIREMENTS.md](../../REQUIREMENTS.md) — GAME-01, GAME-02, FIXT-01 and FEED-01; lines 9-26.
- [ROADMAP.md](../../ROADMAP.md) — Phase 21 success criteria and plan cap; lines 60-74.
- [gabbaboy.h](../../../include/gabbaboy/gabbaboy.h) — execution-mode enum, info API and RGB555 contract; lines 344-433.
- [acceptance.c](../../../src/runner/acceptance.c) and [acceptance.h](../../../src/runner/acceptance.h) — shared run, predicate, callbacks, observations, receipt and bounds.
- [acceptance CMake tests](../../../tests/acceptance/CMakeLists.txt), [game acceptance docs](../../../docs/game-acceptance.md), and Phase 20 admission checker/manifests — controls and fixture-check precedent.

### Primary public candidate sources (MEDIUM confidence; mutable until pinned)

- [Potion Panic creator page](https://deved.itch.io/potion-panic) — creator statements about separate code and asset license labels, controls, download listing and source link.
- [Potion Panic indexed GitHub fork](https://github.com/gbcompo25/potion-panic) — fork identity and README build instructions; not treated as the authoritative exact source/build tree.
- [µCity author README repository](https://github.com/AntonioND/ucity) — author description, preferred ROM name, build information and mixed component license statements; points to Codeberg releases.
- [µCity author manual](https://github.com/AntonioND/ucity/blob/master/manual.rst) — controls and game simulation behavior useful for source-inspection leads.

### Secondary project research

- [Game feedback review](../../research/2026-10-31-GAME-FEEDBACK-REVIEW.md) — runner gap, evidence distinctions, report workflow and candidate gates.
- [Game scene shortlist](../../research/2026-10-31-GAME-SCENE-SHORTLIST.md) — proposed routes and historical leads; explicitly not a current GabbaBoy test report.
- [License audit](../../research/2026-10-31-LICENSE-AUDIT.md) — prior component-term review and limits.
- [Phase 20 context](../GB-20-fixture-admission-tune-up/20-CONTEXT.md) — accepted fixture-admission and package-policy checks.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — based on the checked-in public C API, runner, and CMake/CTest tests; candidate-tool versions are not accepted until pinned-source compatibility is checked. [VERIFIED: include/gabbaboy/gabbaboy.h:344-433; src/runner/acceptance.c; tests/acceptance/CMakeLists.txt]
- Architecture: HIGH — based on current source callbacks, mode API, RGB555 capture path and receipt implementation. [VERIFIED: include/gabbaboy/gabbaboy.h:344-433; src/runner/acceptance.c:182-243,697-724,1174-1195]
- Candidate provenance: MEDIUM — public creator/author pages state leads but the exact immutable source/build/ROM pair and redistribution rights remain unverified. [CITED: https://deved.itch.io/potion-panic; https://github.com/AntonioND/ucity]
- Scene workflow: MEDIUM — locked report contract is clear; no current GabbaBoy symptom with an independent oracle was identified in the reviewed research. [VERIFIED: 21-CONTEXT.md, D-07-D-09; .planning/research/2026-10-31-GAME-SCENE-SHORTLIST.md:1-10,36-61]
- Security: HIGH — bounded parsing and fixture/privacy rules are specified in code and project instructions. [VERIFIED: src/runner/acceptance.h:22-35,63-84; AGENTS.md:32,47-53]

**Research date:** 2026-11-01
**Valid until:** 2026-12-01 for in-repo architecture; recheck mutable candidate pages and exact source at each admission attempt.
