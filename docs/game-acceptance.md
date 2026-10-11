# Game acceptance and the DMG regression baseline

This page states what the Phase 7 game acceptance evidence is, what each part proves, and what it does not. It covers one game on one model. It is not game compatibility, not hardware qualification and not a perceptual audio or video judgement.

## Scope

- Game: Libbet and the Magic Floor v0.08 (pinned upstream commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090`), vendored at `fixtures/libbet/libbet.gb`, ROM SHA-256 `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`. Provenance and the rebuild recipe are in `fixtures/libbet/SOURCES.md` and `fixtures/libbet/manifest.json`.
- Model: the deterministic, bootless DMG-CPU-B software profile only. No boot ROM runs; startup values are emulator policy.
- One game is not game compatibility. The evidence is not hardware evidence either: no physical DMG-CPU-B was observed.
- Asset rights are stated as an inference, not a per-asset licence grant: they rest on single-author history (285 of 286 upstream commits by one author, one constants commit by another) plus the repository-wide zlib licence. This matches the `scope_note` in the fixture manifest.

## How acceptance works

- Input is a `gbinput 1` script (`tests/acceptance/inputs/libbet-tutorial.input`) whose times are master-timeline units (one frame is 140448 half-dots). Frame boundaries come from the master timeline, not from a count of completed frames.
- The acceptance gate is a guest-memory predicate, `libbet-tutorial-cleared`, read through `gbb_peek_ram` at ROM-anchored WRAM addresses. It holds when `hw_capability` equals the expected 0, `attract_mode` is 0, `cur_floor` is 0, the floor is 2 by 2, `max_score` is at least 2 and `cur_score` equals `max_score`. The ROM digest and the anchor byte sequences are checked before the first run. The predicate must hold on two consecutive frame boundaries; the first of the two is `T_hit`.
- On a hit the runner keeps running one more second of emulated time, then reports checkpoint frame digests (`title`, `play_start`, `mid`, `hit`), a rolling frame digest and a whole-stream PCM digest.
- Structure gate for the checkpoints: `hit` must differ from `title`; `mid` and `hit` must contain at least 3 distinct shades; `title` and `play_start` must contain at least 2. The locked context decision D-25 asked for 3 shades at every checkpoint, but the pinned title screen is 1-bit text and `play_start` is a two-shade transition, so D-029 relaxed the rule for those two. D-029 is a planning-time refinement of a locked decision and is pending owner confirmation.
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

## Limitations

- Packaged-player game smoke is macOS only; there is no Linux or Windows player packaging. Headless acceptance runs on Linux, macOS and Windows. See [unreleased support-ledger entries](support/unreleased.md).
- `libbet-repro` is `workflow_dispatch` only and the workflow file is not on the default branch, so no hosted reproduction run URL exists yet. The reproduction script was verified byte-identical on macOS arm64 only; the Linux path and the dispatch workflow are unverified.
- Physical hardware, perceptual audio quality and other games are unqualified. The frame inspection behind the baseline freeze was an agent inspection of coarse content only.

## Using the baseline in later phases

- Check: `bash tests/scripts/verify-dmg-baseline.sh`, or the `dmg_baseline` CTest. CI prints `baseline status=pass` on the three native jobs.
- The ledger stores an expected CTest inventory and the frozen observation lines. A change to any line needs a row in `tests/baseline/CHANGES.md` (evidence class and approver) and a dedicated commit whose subject starts `baseline:` and which touches nothing under `src/`.
- There is no update mode. Phase 8 and Phases 11 and later default to zero changed lines; an unexplained difference is a regression to investigate, not a ledger edit.
