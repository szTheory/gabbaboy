---
phase: GB-03-visible-interactive-dmg
plan: "09"
subsystem: macos-player-package
tags: [sdl3, macos-arm64, package-provenance, github-actions]

# Dependency graph
requires:
  - phase: GB-03-visible-interactive-dmg
    provides: Optional SDL3 player, owned demo fixture, and exact-revision fixture provenance
provides:
  - Opt-in exact-head macOS arm64 build and package candidate using pinned SDL3 3.4.18
  - Downloaded-package consumer smoke and receipt binding source, package, SDL, and fixture identities
  - Package-relative demo lookup and a single executable-relative SDL RPATH
affects: [phase-3-verification]

# Actuals
actuals:
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns: [run-scoped package candidate, extracted-byte consumer receipt, exact executable-relative RPATH]

key-files:
  created: []
  modified:
    - .github/workflows/ci.yml
    - .github/workflows/preview.yml
    - src/player/main.c
    - tests/scripts/verify-phase3-player.sh
    - docs/preview.md

key-decisions:
  - "Keep SDL acquisition and the player build in an opt-in macOS arm64 job; the portable core lane remains offline and SDL-free."
  - "Bind candidate artifacts to an exact PR head and run attempt, then verify downloaded archive bytes, license notices, metadata, and the real SDL guest/frame smoke before publishing the longer-lived preview artifact."
  - "Require exactly one packaged SDL RPATH, @executable_path/../lib, so the installed player does not rely on a build-host path."
  - "Treat the result as an unsigned preview; do not claim signing, notarization, physical hardware qualification, or release readiness."

patterns-established:
  - "A package consumer must verify the artifact receipt before extraction and must launch the extracted binary against package-relative assets."
  - "Separate the one-day build candidate from the 14-day artifact that has passed downloaded-byte verification."

requirements-completed: [VIDEO-04, VIDEO-05]

coverage:
  - id: D1
    description: "The exact clean source revision builds the optional player with pinned SDL3, runs a nonempty player test inventory, and packages all runtime, fixture, and license files."
    requirement: VIDEO-04
    verification:
      - kind: integration
        ref: "CI run 37686137977 at fd62c48d84b8339435fefd008147f0c06f696e0e; macos-player-package and required-native passed; local optional CTest passed 14/14."
        status: pass
    human_judgment: false
  - id: D2
    description: "The downloaded exact-head package has matching source, package, SDL, license, and fixture identities and passes an extracted-byte SDL event/guest/frame smoke."
    requirement: VIDEO-05
    verification:
      - kind: integration
        ref: "Preview run 37686137834 at fd62c48d84b8339435fefd008147f0c06f696e0e; final artifact downloaded, receipt and SHA-256 checked, then safely extracted and locally smoke-launched."
        status: pass
    human_judgment: false

# Metrics
duration: 24 min
completed: 2026-10-07
status: complete
---

# Phase GB-03 Plan 09 Summary

**The optional macOS player now has an exact-revision package and downloaded-byte smoke path, with the ordinary core build still independent of SDL.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-10-07T20:40:21Z
- **Completed:** 2026-10-07T21:04:10Z
- **Tasks:** 2
- **Files modified:** 5 implementation files; this summary and phase traceability are follow-up metadata.

## Accomplishments

- Added a `run-macos-player` opt-in lane that checks out the full PR head SHA, verifies the clean source tree, builds official SDL3 3.4.18 from the SHA-256-pinned source, checks the nonempty `player_*` CTest inventory, and uploads a one-day run-scoped candidate only after success.
- Packaged the executable, bundled SDL dylib, original 32 KiB demo ROM and manifest, project/demo/SDL notices, documentation, and source/tool/fixture metadata. The extracted executable resolves its demo relative to its installed path and has only `@executable_path/../lib` as its runtime search path.
- Added a separate exact-head consumer job that locates the successful matching CI attempt, downloads that candidate, verifies the receipt and bytes before extraction, checks licenses and source/SDL/fixture identities, and launches the extracted binary through SDL events to a completed guest frame. It uploads the qualified preview and receipt for 14 days only after the smoke passes.
- Verified GitHub's current [hosted-runner table](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) lists `macos-14` as an M1 arm64 runner; the script also fails unless the runtime reports `Darwin/arm64`.
- Documented artifact contents, local and hosted launch paths, opt-in label, retention, and the unsigned, unnotarized, non-hardware-qualified preview limits.

## Verification Evidence

- Full offline CTest passed **132/132** at implementation revision `fd62c48d84b8339435fefd008147f0c06f696e0e`.
- The optional SDL player suite passed **14/14**. The strict clean-revision local build and extracted-package smoke passed on the same revision.
- Exact-head CI run [37686137977](https://github.com/szTheory/gabbaboy/actions/runs/37686137977) passed `macos-player-package` and `required-native`. Exact-head preview run [37686137834](https://github.com/szTheory/gabbaboy/actions/runs/37686137834) passed both installed-package consumers, `player-package-smoke-macos`, and `preview-package-smoke`.
- Downloaded preview artifact `preview-player-macos-arm64-37686137834-1`; its receipt binds build run `37686137977/1`, consumer run `37686137834/1`, exact source revision, SDL archive/license, and the 32 KiB demo fixture. The downloaded package SHA-256 is `cd0ce476c34a91ab9de2a6ee5e084a0ecff94b95f5015d1aa7b41bc9f88e175f`; SDL license SHA-256 is `1c040b8271b37e5076359f8fd54240e371114112924d2df81ef87c7d6a1dfdfd`.
- The final downloaded artifact was also safely extracted locally and its packaged player passed the SDL event, failed/successful ROM replacement, and completed-frame smoke (`frame=1`). A wrong expected-source SHA and a one-byte-mutated archive were rejected before qualification.
- `actionlint`, all workflow `bash -n` blocks, the player script syntax check, and `git diff --check` passed.

## Task Commits

1. **Build and consume the exact-head optional player package** — `ee43cf9` (`feat(GB-03-09): package optional macOS SDL player`)
2. **Require only the package-relative SDL RPATH** — `fd62c48` (`fix(GB-03-09): restrict packaged SDL rpath`)

## Decisions Made

- Kept the host package fully opt-in and retained the ordinary core lane's offline, SDL-free dependency graph.
- Verified package identity before extraction and checked the actual downloaded artifact again after the hosted consumer job; a local build result alone does not qualify a hosted artifact.
- Required the package itself to launch from extracted bytes, rather than relying on a build-tree ROM or the SDL build prefix.

## Deviations from Plan

The player startup path in `src/player/main.c` was included because the installed archive must find its demo ROM relative to the executable. A review also tightened the consumer check from rejecting one known build path to requiring the single approved package-relative RPATH.

## Remaining Phase Gaps

Plan 03-09 is complete and VIDEO-04/VIDEO-05 are covered. Phase 3 is **not** complete: VIDEO-02 still lacks qualified simultaneous CPU/PPU/DMA collision evidence, and VIDEO-03 still lacks the primary model-applicable D-08 JOYP interrupt edge/selection evidence. The native window has not had a live desktop perceptual check, and no physical DMG-CPU-B observation occurred. The phase remains executing; do not start Phase 4 or claim full Phase 3 completion.

## Next Phase Readiness

The nine currently planned Phase 3 plans are complete, but the phase verifier must preserve the VIDEO-02/VIDEO-03 evidence gaps and recommend a focused Phase 3 gap plan. Phase 4 remains the next roadmap phase (**MBC1 and Safe Battery Continuation**), but it must not start until the owner chooses to continue after Phase 3 gap review.

---
*Phase: GB-03-visible-interactive-dmg*
*Completed: 2026-10-07*

## Self-Check: PASSED

- The optional player lane and artifact consumer both passed on the exact PR head; downloaded build and consumer receipts, package digest, and fixture/license identity were independently checked.
- Full offline CTest passed 132/132 and the optional player suite passed 14/14; no extra dependency was introduced.
- VIDEO-04 and VIDEO-05 are mapped to exact evidence. VIDEO-02 and VIDEO-03 remain open; this plan summary does not mark the phase complete.

## Automation Follow-up 2026-10-09

The original opt-in package lane is now required on every pull request. `player_smoke` asserts the initial shade, the darker rendered tile while SDL Z is held, and restoration after SDL Z-up, along with the guest's press/release markers. The downloaded-package consumer reruns that same assertion against extracted artifact bytes. CTest and package verification isolate synthetic save files under test-only preferences. Local verification passed all 50 player tests and the package smoke; exact-revision hosted CI evidence is pending.
