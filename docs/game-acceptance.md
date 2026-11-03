# Game acceptance and the DMG regression baseline

This page states what the Phase 7 game acceptance evidence is, what each part proves, and what it does not. It covers one game on one model. It is not game compatibility, not hardware qualification and not a perceptual audio or video judgement.

## Scope

- Game: Libbet and the Magic Floor v0.08 (pinned upstream commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090`), vendored at `fixtures/libbet/libbet.gb`, ROM SHA-256 `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`. Provenance and the rebuild recipe are in `fixtures/libbet/SOURCES.md` and `fixtures/libbet/manifest.json`.
- Model: the deterministic, bootless DMG-CPU-B software profile only. No boot ROM runs; startup values are emulator policy.
- One game is not game compatibility. The evidence is not hardware evidence either: no physical DMG-CPU-B was observed.
- Asset rights are stated as an inference, not a per-asset licence grant: they rest on single-author history (285 of 286 upstream commits by one author, one constants commit by another) plus the repository-wide zlib licence. This matches the `scope_note` in the fixture manifest.

## CGB game evidence

No CGB game-level evidence exists.

### Phase 21 outcome

Phase 21 admitted no game. The ordered candidate records are [Potion Panic](../tests/data/cgb-candidates/potion-panic.json) and [µCity 1.3](../tests/data/cgb-candidates/ucity-1.3.json); the final source-bound checker requires exactly these two attempts and their recorded terminal causes.

- Potion Panic is a rights/source-scope no-go. The creator-linked source could not be reached before a ref or commit identity was returned ([source](https://codeberg.org/DevEd/potion-panic)), so exact component coverage and grant authority remain unestablished. The component-level repository/public-CI scope remains unestablished. No source tree, build, ROM, execution, progress, observations, or receipt were observed. This does not establish a license prohibition.
- µCity 1.3 is a rights/source-scope no-go at exact source commit `d1880a2a112d7c26f16c0fc06a15b6c32fdc9137`. Its required `source/engine/hardware.inc` has SHA-256 `05f43643bf29459f6a86b2fedf00b887133b98038fa4f51112ced0f01a762715`; no identified grant or notice establishes repository/public-CI scope for that component. Toolchain identity, build confinement, ROM bytes, cartridge header, loaded mode, progress, RGB555/PCM observations, and candidate receipt remain not observed. No upstream tool, script, or ROM was run. No fallback fixture, case, input, predicate, or notice row was created. This is an unresolved component-scope gap, not a conclusion that a license prohibits use.

The original native-CGB harness passed on the CGB-CPU-E software model in native CGB mode. It is original harness-only evidence (evidence class `original-harness-only`): an authored control ROM and input test the runner's progress handling. Its independent no-input, wrong-input, impossible-predicate, strict-xfail, and compatibility-mode checks are controls for that authored fixture only. Named RGB555 and PCM digests record same-run reproducibility; they are not accuracy, perceptual, or scene oracles. Scene expectations require their own independent oracle. The harness does not admit a game or describe progress in any game, physical CGB-E behavior, mode-3 timing, perceptual audio/color quality, or general game compatibility.

Reproduce the source-bound outcome and receipt from a configured checkout with:

```sh
cmake --preset phase1
cmake --build --preset phase1
python3 -I tests/scripts/verify-cgb-game-evidence.py --check --runner build/gabbaboy-runner --repo-root . --source-revision "$(git rev-parse HEAD)" --write-evidence build/phase21-evidence/result.json
ctest --preset phase1 --output-on-failure --no-tests=error -R '^phase21_(game_evidence(_controls)?|fixture_admission|scene_report_.*)$'
```

The checker reads the two candidate records, contract documentation, and scene workflow from the same immutable source revision, then runs the current progress, candidate, and scene checkers against that revision and the qualified runner. There is no third candidate. The checker rejects a changed candidate identity, a missing no-go cause or control, and claims that turn harness evidence into admitted-game progress or a claim that any license prohibits use. The complete CTest suite remains required for phase closure. Deck exploration and future Libretro work remain outside this CGB result.

### Historical CGB candidate attempt

Before Phase 21, Rebound was inspected at source commit `cc2966e1643d480d0780fb6cc5b9ef53d5ef6898`. Its pinned build attempt failed with RGBDS v1.0.4; the official RGBDS v1.0.1 archive (SHA-256 `2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`) was also checked and produced 494 assembler errors. No output ROM or ROM digest was produced. Per-asset rights remain unresolved. The older candidate digest `195765b8ca3b0fb7d37b7b92d0242d6c7e01ec71f27f93e565fa081e449cbb92` is unverified historical metadata and is not tied to an admitted ROM.

The earlier attempt ended at the build and rights gates. No broader candidate hunt or runner adaptation was performed, and no CGB game bytes were admitted. Libbet and the Magic Floor v0.08 remains the DMG game acceptance described below; its guest-memory progress predicate is separate from its RGB555 and PCM regression observations and from the CGB test-ROM corpus. See the [CGB corpus contract](cgb-corpus.md) for that software-model evidence.

Physical CGB-E remains UNKNOWN/POLICY. No physical or perceptual audio/color qualification is claimed.

## How acceptance works

- Input is a `gbinput 1` script (`tests/acceptance/inputs/libbet-tutorial.input`) whose times are master-timeline units (one frame is 140448 half-dots). Frame boundaries come from the master timeline, not from a count of completed frames.
- The acceptance gate is a guest-memory predicate, `libbet-tutorial-cleared`, read through `gbb_peek_ram` at ROM-anchored WRAM addresses. It holds when `hw_capability` equals the expected 0, `attract_mode` is 0, `cur_floor` is 0, the floor is 2 by 2, `max_score` is at least 2 and `cur_score` equals `max_score`. The ROM digest and the anchor byte sequences are checked before the first run. The predicate must hold on two consecutive frame boundaries; the first of the two is `T_hit`.
- On a hit the runner keeps running one more second of emulated time, then reports checkpoint frame digests (`title`, `play_start`, `mid`, `hit`), a rolling frame digest and a whole-stream PCM digest.
- Structure gate for the checkpoints: `hit` must differ from `title`; `mid` and `hit` must contain at least 3 distinct shades; `title` and `play_start` must contain at least 2. The locked context decision D-25 asked for 3 shades at every checkpoint, but the pinned title screen is 1-bit text and `play_start` is a two-shade transition, so D-029 relaxed the rule for those two. D-029 is a planning-time refinement of a locked decision; the owner ratified it on 2026-10-11.
- PCM non-silence gate (D-16): over the window from `play_start` to `T_hit` plus one second, each channel needs a peak-to-peak of at least 2048 and at least 4800 sample-to-sample changes. Observed at exact head `b6f982b` (identical on Linux, macOS and Windows): gameplay window 20290 peak-to-peak and 164822 changes; the no-input control window 0 and 0. The calibration rule left both thresholds unchanged. "Any non-zero sample" is not used because the no-input title outputs a constant level.
- SGB tolerance (D-17): Libbet's SGB detection runs on every DMG boot. The receipt shows `hw_f90=00` and at least one FF00 reset pulse (observed `sgb_reset_pulses=2`).
- A failing run with `--failure-dir` writes a bounded stall report (`<id>.stall.txt`, at most 65536 bytes) and at most one 69135-byte final-frame PPM. The 64 KiB cap applies to the text report because a 160 by 144 P6 image alone exceeds it (D-18 owner amendment).

Run it with:

```sh
gabbaboy-runner --acceptance tests/acceptance/cases.txt --case libbet --receipt
```

## Controls

Every control fails the predicate with a non-zero raw outcome, exit 1 with `reason=predicate-not-reached`. Each control's CTest asserts that raw outcome. Separately, the strict expected-failure layer (D-22) is asserted for the two cases declared `model_fail`. Neither assertion replaces the other (D-14 owner clarification, 2026-10-10).

| Control | What it removes | Raw outcome (asserted by) | Strict-xfail mapping (asserted by) |
|---|---|---|---|
| N1 `libbet-no-input` | all input | exit 1, `predicate-not-reached` (`acceptance_libbet-no-input_raw`, run with `--raw-verdict`) | `status=xfail`, exit 0 only when the reason matches; a pass is unexpected-pass, exit 1; any other reason exit 1 (`acceptance_libbet-no-input`) |
| N2 `libbet-select` | SELECT in place of START | exit 1, `predicate-not-reached` (`acceptance_libbet-select_raw`) | `status=xfail`, same rules (`acceptance_libbet-select`) |
| N3 drop START | the START press and release, via `--mutate drop:START` | exit 1, `predicate-not-reached` (`acceptance_libbet_drop_start`) | not applicable |
| Core mutant | the JOYP select test inverted in a test-only copy of the core | exit 1, `predicate-not-reached` (`acceptance_core_mutant`) | not applicable |

Other controls: a predicate truth table (`acceptance_predicate_truth_table`), ROM-anchor checks, the SGB tolerance check, negative case files (flipped digest, altered input, bad script, duplicate id, unknown key, path traversal, oversize) and a declared-exclusion suite control: the suite denominator needs an explicit `--expect-excluded` count, and an undeclared or missing count fails. The suite currently reports `eligible=3 executed=3 excluded=0 xfail=2`.

The core mutant is built only in the test tree; configure fails unless the anchor line in `src/core/gabbaboy.c` occurs exactly once, and nothing is installed.

## Evidence classes

- Acceptance gate: the guest-memory predicate alone.
- Regression class (D-26): the Libbet checkpoint, rolling and PCM digests, and every Mooneye frame digest, including the `daa` LD B,B frame. These were captured from this emulator, are not hardware-verified, and are frozen and byte-compared only in the baseline ledger `tests/baseline/dmg-cpu-b-v1.txt`. The `daa` LD B,B digest is the ledger key `mooneye.daa.frame`; all `mooneye.<alias>.*` keys use the `fixture_case` alias (`daa`, `tim00`, ...). Obtain the image with `--observe --dump-checkpoints`. It is never a reference in a case file.
- `tests/acceptance/ldbb-controls.txt` holds only a mismatch control (`daa-ldbb`) and a not-ready control (`tim00-ldbb`). Their single reference digest is the stdlib `python3 -I tests/scripts/rgb-digest-vector.py --uniform 3` value, enforced at configure time. It claims nothing about any ROM's correct output, and Phase 7 has no test-ROM frame oracle.
- Observations recorded, not claimed: the `daa` LD B,B frame is entirely shade 0 (the ROM reports through registers and never draws), so `mooneye.daa.frame` guards "still blank" only. The `tim00` and `tim00-div-trigger` frames are `not-ready` because LD B,B is reached before the first frame completes.
- The `frame-digest@t` oracle exists in the runner but no CTest covers it; it was exercised once with an uncommitted scratch case.

## Mixer and input investigations

- Mixer (D-027): the core mix had no headroom, and Libbet clipped 3.04 percent of pre-filter samples. Each channel term is now divided by 16. The strengthened `audio_saturation` test was not shown to fail against the pre-fix core; the evidence for the defect is the scratch probe recorded in the 07-03 summary and in D-027.
- Early Start taps (D-028): expected Libbet behaviour, no emulator defect. The 07-17 probe was a scratch replay that is not committed.

## Packaged player smoke

The packaged player runs the same script and predicate with dummy SDL drivers and must produce a PCM digest equal to the headless runner's. The ROM and script are read from the checkout and are not shipped; the package scan fails if either appears in the package. A no-input control must fail, and a registered check keeps the diagnostic path free of environment, network, file-write and save-persistence use. This runs only in the macOS packaged player job.

## Dense input delivery

Dense input delivery uses a private, immutable event span and caller-owned cursor shared by acceptance driving and diagnostic replay. The parser's 16,384-event limit bounds the span. During each run the core refills its existing 64-event queue with due events at the current timestamp, preserving script order and applying every same-time transition before the next guest tick. Future events remain in the caller's span and set the next STOP/idle deadline. The core clears the borrowed reference on every return; the adapter explicitly resumes with its cursor. This does not increase the public queue, alter public ABI or saved-state format, or retain event pointers.

Within the acceptance adapter, custom delivery callbacks remain caller-managed batches of at most 64 events, and the public queue stays bounded. `verify-dense-input.py` replays a 67-event same-time START burst through the actual runner, compares hit timing plus frame and PCM digests with the frozen DMG ledger, requires a bounded failure diagnostic when START is removed, and proves a temporary no-refill source mutant fails.

## Limitations

- Packaged-player game smoke is macOS only; there is no Linux or Windows player packaging. Headless acceptance runs on Linux, macOS and Windows. See [unreleased support-ledger entries](support/unreleased.md).
- `libbet-repro` is `workflow_dispatch` only and the workflow file is not on the default branch, so no hosted reproduction run URL exists yet. The reproduction script was verified byte-identical on macOS arm64 only; the Linux path and the dispatch workflow are unverified.
- Physical hardware, perceptual audio quality and other games are unqualified. The frame inspection behind the baseline freeze was an agent inspection of coarse content only.

## Using the baseline in later phases

- Check: `bash tests/scripts/verify-dmg-baseline.sh`, or the `dmg_baseline` CTest. CI prints `baseline status=pass` on the three native jobs.
- The ledger stores an expected CTest inventory and the frozen observation lines. A change to any line needs a row in `tests/baseline/CHANGES.md` (evidence class and approver) and a dedicated commit whose subject starts `baseline:` and which touches nothing under `src/`.
- There is no update mode. Phase 8 and Phases 11 and later default to zero changed lines; an unexplained difference is a regression to investigate, not a ledger edit.
