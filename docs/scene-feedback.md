# Scene feedback intake and reproduction

This workflow turns a concise title, scene, and symptom into an agent-owned investigation. A report begins as unresolved triage; it is not evidence that GabbaBoy has a defect. The 2026-10-31 scene shortlist is research only and does not identify a current GabbaBoy failure.

## Start with three text fields

Create a local report with the title, scene, and symptom. The other two fields below only select the checkout and output directory:

```sh
python3 -I tests/scripts/verify-scene-report.py --new \
  --title 'Game and release if known' \
  --scene 'What screen or short moment was visible' \
  --symptom 'What appeared wrong' \
  --repo-root .
```

`--output` may select a directory under `build/scene-reports`; otherwise reports go there by default. The CLI refuses paths outside that local directory, symlinked output paths, empty or oversized fields, duplicate JSON keys, and malformed reports. It does not search the filesystem, open a ROM, save, state, image, video, or audio file, or ask the owner to play a route. On POSIX, the report directory and file are restricted to the current user. That build directory is ignored by Git.

The initial record uses the stages `triage`, `reproduced`, and `regression-ready`. A new report is `triage`, has classification `unknown`, and records the next metadata-recovery step. Its missing release, source revision, build, ROM identity, model, execution mode, route, and reproduction are deliberately unknown. This is useful unresolved intake, not a failed test or reproduced defect.

## Agent-owned investigation

1. Recover public title/release/region/revision, source and build identity, ROM digest/header, and the selected GabbaBoy model/profile and actual execution mode. Keep patched images and revisions distinct.
2. Read the game's public source, manual, or other independent statement of original behavior. Research leads can help find a short route; they do not establish the route, expected output, rights, or a GabbaBoy defect.
3. Select only original project data or a fixture admitted for repository and public-CI use. Run a bounded deterministic sequence at the existing runner/core boundary. Record the exact source, fixture, model, route, budget, and evidence. Do not use a private game image as a test fixture.
4. Compare raw core output first, then color conversion, then host presentation. For visual reports use native RGB555 frames where possible; for sound use bounded PCM or a semantic audio event. Check conversion, scaling, shaders, frame blending, pacing, and host rendering before assigning a layer.
5. Reproduce or record a concrete blocker. Classify the result as `core`, `conversion`, `host`, `original-behavior`, or `unknown`. A missing route, identity, permission, model, or independent oracle stays an explicit blocker; `unknown` is a valid outcome.

Ask the owner for one specific missing detail only when it changes the next reproduction step. Owner play is optional and is never a recurring prerequisite. Do not ask the owner to search indefinitely for a historical challenge scene whose exact release or route is unknown.

Personal ROMs, battery saves, save states, screenshots, videos, and audio remain outside Git and hosted CI. Never place them in the repository or public CI. Do not open private media unless the owner explicitly provides it for that particular local investigation. Any private media reference stays local to triage; it cannot be promoted or copied into public evidence. Do not disrupt or replace a daily-play save for a test.

## Validate and promote

```sh
python3 -I tests/scripts/verify-scene-report.py --validate \
  build/scene-reports/REPORT.json --repo-root .
```

Validation checks the strict bounded JSON schema and stage claims. Add `--source-revision <full-commit>` when validating a reproduced report. That value binds checker, CMake-registration, and procedure reads to one immutable commit; unavailable commits and working files that differ from that commit are rejected.

Promotion to `regression-ready` is a separate gate. It requires an exact model/profile/mode/source and fixture identity; a minimized permitted fixture; a deterministic route and finite budget; reproduction and classification evidence; an independently reasoned expected behavior; a registered executable check bound to immutable source; and passing positive and fault-targeted negative controls. The fixture must be original project-authored data or pass the Phase 20 fixture-admission gate for repository and public CI. A local private capture is never eligible.

Use the smallest expectation that matches the reported behavior. A genuinely static scene may use independently derived pixel values. Moving, timing, and audio behavior require a bounded sequence or semantic/event invariant at the relevant boundary. A digest or screenshot captured from GabbaBoy's failing output cannot become its own oracle. A no-input progress control does not test a scene expectation and cannot serve as its negative control.

The CLI's `--promotion-check REPORT --source-revision <full-commit>` evaluates this evidence gate and executes the two registered CTests from the matching configured build. The same immutable revision must identify the report, source checks, and runnable CTest registration. `--self-test [intake|controls|contract]` runs synthetic contract subjects only; those controls do not name a live game, claim reproduction, or establish rights. `--synthetic-control` is reserved for isolated self-test intake. Do not create a tracked live report when no owner symptom is available.
