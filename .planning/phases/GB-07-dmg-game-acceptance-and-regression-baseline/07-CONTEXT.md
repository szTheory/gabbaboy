# Phase 7: DMG Game Acceptance and Regression Baseline - Context

**Gathered:** 2026-10-10
**Status:** Ready for planning
**Method:** Four parallel multi-lens advisor researches (each with an adversarial pass) were reconciled into one coherent set. Following the owner's standing instruction ([discuss fan-out, auto-follow]), the recommendations were adopted without asking about each area. Where the researchers disagreed, the reconciliation is stated inline as "Reconciled".

<domain>
## Phase Boundary

Admit one rights-clear DMG game, Libbet and the Magic Floor v0.08, under a fail-closed provenance manifest. Prove that it starts, responds to scripted input and makes guest-observable progress, both headless on Linux/macOS/Windows CI and in the packaged SDL3 player. Extend the runner with:
- a canonical RGB frame digest at `LD B,B` or at an emulated-time checkpoint;
- scripted joypad replay in emulated time;
- per-fixture model applicability.

Then freeze a DMG-CPU-B regression baseline that every later v0.2 phase must match byte for byte (EVID-02). Requirements: GAME-01, GAME-02, GAME-03, EVID-01, EVID-02.

**Not in this phase:** new mappers, CGB behaviour, new player platforms or packaging, save states, mixer redesign, and any "game compatibility" claim beyond this one title.

</domain>

<decisions>
## Implementation Decisions

### A. Libbet admission (GAME-01, gate G5)
- **D-01:** Admit the **vendored, digest-pinned upstream release binary** as `fixtures/libbet/libbet.gb`:
  - SHA-256 `3607412031c8287cf878299ce96e581e85b852dde703806343b95576fa3ff1a9`, 32768 bytes.
  - Header: title `LIBBET`, type `$00`, `$143=$80`, `$146=$03`.
  - Pin the **commit** `46a765a2c01701bffb8c0b7dd6e4be3a6b193090`. The tag `v0.08` is lightweight and mutable, so never pin the tag or `master`.
  - Required CI verifies the bytes, digest, header, manifest and rights completeness. It never fetches upstream.
  - **Reversibility:** costly. The digest is bound into baseline, predicate addresses and acceptance scripts; changing the game invalidates all three.
- **D-02:** Reproducibility is proven by a **separate, non-required, opt-in workflow**, `.github/workflows/libbet-repro.yml` with `tests/scripts/reproduce-libbet.sh`.
  - It rebuilds the pinned commit with **RGBDS 0.7.0**, pinned by archive SHA-256: Linux `f67bc8fdd2b1521f0bed5a3750a09b206de760064fb95bb52790d375c3297210`, macOS `f2aee8235db2e9f020708bcb3c74112366ca50f7eb880d7717d95e385a583a16`.
  - Python 3 with **Pillow 12.3.0** is installed via `pip --require-hashes`.
  - The job compares the rebuild to the vendored bytes and never writes back. It uses `permissions: contents: read` and no secrets.
  - Do **not** fold it into `fixture-repro.yml`, which enforces a single RGBDS 1.0.1 pin. RGBDS 1.0.1 fails to build this tag (it rejects `rgbasm -h`); record that fact.
  - Pillow and RGBDS 0.7.0 exist only inside this job. This satisfies the owner's "copy over dependency" preference because nothing enters the required path.
- **D-03:** **Reproducibility statement.** The research observed a byte-identical local rebuild on macOS (RGBDS 0.7.0 under Rosetta, Pillow 12.3.0, Python 3.14). Record a hosted Linux reproduction only after a real run URL exists, and never claim it before.
- **D-04:** **G5 checklist.** Every item must be present or the manifest verifier fails:
  - (a) The full zlib `LICENSE` as `fixtures/libbet/LICENSE.txt`, with the credit discrepancy noted verbatim. LICENSE names "Damian Yerrick 2018"; README and ROM text add "Martin Korth 2002, 2012; Damian Yerrick 2018, 2024".
  - (b) The README credit excerpt, plus Korth's porting permission quote (`note_from_nocash.md`, 2018-10-03, "Would be fine.") recorded as a **limitation**: it is a permission to port, not a licence grant.
  - (c) A `rights.embedded_assets` entry for every file in the **frozen build closure**, each with path, kind, author, licence, evidence pointer at the pinned commit, and full SHA-256. The closure covers:
    - the `tilesets/*` inputs: `Libbet.png`, `Libbet.ec`, `Libbet_title.png`, `bigdigits.png`, `floorborder.png`, `floorborder-sgb.png`, `floorpieces.png`, `roll32.png`, `sgbborder.png`, and the `vwf7_cp144p.png` font;
    - ROM text in `src/*.z80`;
    - the synthesized-SFX audio driver;
    - `src/hardware.inc` (CC0-1.0);
    - the `tools/*.py` used by the build.

    Record explicitly that there is no music, and that `07-biggar/` and `hopesup/` are outside the build closure.
  - (d) The release digest, plus the upstream asset URL, size and publish time as provenance only.
  - (e) The reproducibility statement and recipe (D-02, D-03).
  - (f) A scope note: the asset rights rest on single-author history (285 of 286 commits by Yerrick, one constants commit by ISSOtm) plus the repo-wide zlib licence. That is an inference, not an upstream per-asset grant. The evidence is "one game", not game compatibility.
- **D-05:** **Fail-closed admission check.** Extend the existing Python verifier pattern (`tests/scripts/verify-support-ledger.py` style, `python3 -I`, stdlib only) or add a sibling script. Admission fails when:
  - `rights.embedded_assets` is missing or empty;
  - any closure file lacks a record;
  - any record has an empty or `unknown` licence, author or digest;
  - the ROM digest or a header byte differs.

  Negative CTest cases run on mutated manifest copies (empty assets, one record removed, licence `unknown`, changed ROM digest, changed header byte). Each must exit non-zero with a distinct message. Add one positive control.
- **D-06:** **Bookkeeping.**
  - Add a `THIRD_PARTY_NOTICES.md` row preserving the zlib text, the Yerrick and Korth credits and the CC0 note.
  - Add a `fixtures/libbet/SOURCES.md` following the Mooneye layout.
  - Add `.gitattributes`: `-text` for the ROM and `eol=lf` for the text files.
- **D-07:** **Fallback rule.**
  - If any G5 item cannot be closed, **stop and report the exact missing item**. Never swap games inside the phase.
  - Tobu Tobu Girl becomes eligible only after G2 (GBDK 2.96a runtime terms) is separately documented as cleared, and it must then pass the same per-asset checklist.
  - Any other candidate needs an owner decision.

### B. Progress predicate, input script and controls (GAME-02, EVID-01)
- **D-08:** **Gate on guest state, not screens.** The predicate is evaluated at frame boundaries via `gbb_peek_ram` and is true when all of these hold:
  - `hw_capability($C5A3) == 0x00` (DMG; per-profile expected value comes from the case file);
  - `attract_mode($C580) == 0`;
  - `cur_floor($C57F) == 0`;
  - `floor_width($C4E8) == 2` and `floor_height($C4E9) == 2`;
  - `max_score($C4EC) >= 2` and `cur_score($C4ED) == max_score`.

  It must hold on **2 consecutive frame boundaries**; record the first hit time `T_hit`. In plain terms: the tutorial floor is fully scored in real play, not in attract mode.

  Rejected alternatives, with measured reasons:
  - Score-only passes in attract mode: Select sets `attract_mode=$04`, and the demo then scores by itself.
  - Cursor variables are overlaid during title/intro.
  - `cur_floor >= 1` depends on the RNG-seeded layout (start times 449–480 never exit).

  **Reversibility:** reversible.
- **D-09:** **Address provenance.** The addresses are hard-coded in a small compiled predicate table in the runner, keyed by the pinned ROM digest. No RGBDS or `.sym` dependency in the required path, since the release ships no `.sym`. Each address carries its source derivation (`main.z80` mainvars, `pads.z80` ram_pads, `floormodel.z80` variable order) and **ROM anchor bytes**:
  - `$C57F` at 0x155C: `AF EA 7F C5 E0 43 E0 42`
  - `$C580` at 0x153A: `E6 04 EA 80 C5`
  - `$C5A3` at 0x14FB: `FA A3 C5 1F 30`
  - `$C4ED` at 0x15A6: init sequence
  - `$C4EB` at 0x1680: `FA EB C4 3C 20`

  A unit test verifies the ROM digest first and then the anchor bytes. The derivation text is also recorded in `fixtures/libbet/manifest.json` and checked by Python.
  - On any Libbet upgrade, re-derive from a rebuilt `.sym` (via D-02) and replace the table.
  - The researchers disagreed on where the predicate lives. **Reconciled:** a named compiled predicate (e.g. `libbet-tutorial-cleared`) is referenced from the case file. This keeps the C parser free of an expression mini-language.
- **D-10:** **Input script grammar v1.** One shared parser source (`src/runner/input_script.c` or similar) compiled into both the runner and the player. That is shared in-repo source, not a dependency. The format is ASCII, one directive per line, with `#` comments and blank lines:
  ```
  gbinput 1
  wait <time>
  press <BTN>
  release <BTN>
  tap <BTN> <time>     # press, wait, release; cursor advances by <time>
  mark <label>         # named checkpoint at cursor time
  ```
  - Buttons are `RIGHT LEFT UP DOWN A B SELECT START`, case-sensitive.
  - There are no loops; generated scripts are committed already expanded.
  - The researchers disagreed on the time base. **Reconciled:** the runner research proposed absolute frame numbers, but completed-PPU-frame counts drift while the LCD is off (Libbet calls `lcd_off` often). The **master-timeline** event grammar was therefore adopted. It maps 1:1 onto `gbb_queue_events` and generalizes to rtc3test (~47 s) and CGB-11.
  - **Reversibility:** costly. Scripts for later phases (rtc3test, CGB-11) will depend on the v1 grammar, which is why it carries a version line.
- **D-11:** **Time unit.** An integer plus suffix:
  - `hd` = half-dot, exact;
  - `f` = 140448 half-dots (one 70224-dot frame), a fixed conversion and not a count of completed frames;
  - `s` = 8388608 half-dots.

  No decimals and no host time. Cursor arithmetic is checked, with a ceiling of 600 emulated seconds. Events carry absolute `at_half_dots`. The runner feeds at most the core queue limit (64) of events per stepping window.
- **D-12:** **Parse bounds and errors.**
  - Limits: file at most 64 KiB, at most 4096 lines, at most 128 bytes per line, at most 16384 events.
  - Rejected: NUL, non-ASCII, a missing or wrong version line, an unknown verb or label, a duplicate label, a double press, a release without press, a button still held at EOF.
  - LF and CRLF are both accepted, but fixtures are `eol=lf` and the case file pins the script's raw-byte SHA-256.
  - Parsing is all-or-nothing before execution. Errors are `invalid-script: line N: <reason>` with exit 2, and nothing runs.
- **D-13:** **Acceptance script content.**
  - Idle until about f500 (the title is ready around f444; Start taps earlier than f449 behave inconsistently).
  - `tap START 3f` at f500.
  - Idle about 200 frames.
  - D-pad sweep RIGHT/UP/LEFT/DOWN, each held 4f with an 8f gap (holds and gaps of at least 3f).
  - Marks `title`, `play_start` and `mid`.
  - Budget cap 3600 frames (60 emulated seconds).

  Measured: score 4/4 at about f894.
- **D-14:** **Controls.** Each one must fail the predicate with exit non-zero, and each is a named CTest case in the inventory.
  - N1: the same script with all events removed. **Required by GAME-02.**
  - N2: SELECT instead of START. It must reach attract mode (`$C580=$04`) and still fail.
  - N3: a runner `--mutate drop:START` control.
  - A predicate truth-table unit test on synthetic RAM snapshots: title garbage, attract, play not yet scored, play hit.
  - A **core-mutant control.** CMake generates a copy of `gabbaboy.c` with one JOYP-row line inverted via `string(REPLACE)`, and configure fails if the pattern is missing. It is built as a separate test-only library, and CTest asserts the mutant fails the gate.
- **D-15:** **Deadline stepping helper** `advance_to(deadline)`.
  - Loop `gbb_run_audio(budget = deadline - now)` and accept `HALTED_IDLE`.
  - If a call consumes 0 half-dots and the remaining time is below the maximum instruction cost (≤48 half-dots), treat the deadline as reached and carry the remainder into the next deadline.
  - Use a hard iteration guard and never a host clock.
  - Share it between the runner and the player smoke.
- **D-16:** **PCM evidence.**
  - (a) A whole-stream SHA-256 over little-endian int16 L,R pairs, recorded as regression evidence.
  - (b) The **non-silence gate**, computed over the window from `play_start` to `T_hit + 1 s`. Each channel needs a peak-to-peak of at least 2048 **and** at least 4800 sample-to-sample changes.
  - "Any non-zero sample" is forbidden as a test, because the no-input title outputs a constant DC level (peak-to-peak 0).
  - Recalibrate the thresholds on the first CI run, and record the observed values.
- **D-17:** **SGB tolerance.** Libbet's `detect_sgb` runs on every DMG boot (MLT_REQ `$89` over FF00, then a JOYP read expecting `$F`).
  - Assert `hw_capability == 0` at f90 and at `T_hit`.
  - Using bounded diagnostics, assert that at least one FF00 reset pulse (`$00` then `$30`) occurred in the first 90 frames.
  - Reaching the gate proves the guest did not hang.
- **D-18:** **Stall diagnosis (GB-GAME-001).** Deterministic two-pass replay:
  - Pass 1 runs without tracing.
  - If the gate is not reached or the run stops abnormally, pass 2 replays to `T_end − window` and records only the final window.
  - The output is bounded: last 4096 trace records, last 64 writes to FF00/IF/IE/LCDC/STAT, an 8-entry PC histogram and the final frame as a PPM, at most 64 KiB in total.
- **D-19:** **Pre-freeze investigations inside this phase.** Defects the game exposes are in scope (FEATURES §game acceptance). Before freezing the baseline (D-31), run two bounded investigations:
  - (i) Gameplay samples reach ±32768 with peak-to-peak 65535. Determine whether the mixer saturates or clips incorrectly against the documented APU output model. Fix it if it is a defect; otherwise record it as expected.
  - (ii) Early repeated Start taps start the game by f270 while single taps at f290–f440 do nothing. Explain this from the Libbet source; fix it only if it shows an emulator defect.

  Each outcome is recorded with evidence. Neither may be left unexplained, because freezing an undiagnosed defect into the baseline is worse than either outcome.

### C. Runner and manifest evolution (EVID-01)
- **D-20:** **Hybrid mechanism.**
  - The compiled Mooneye `cases[]` table and its pinned JSON manifest digest stay **unchanged** in Phase 7. Migration waits for a later phase with a digest-identical guard.
  - New acceptance fixtures go in `tests/acceptance/cases.txt`: one case per line, space-separated `key=value`, `#` comments, ASCII. CRLF is tolerated, but the file is stored `eol=lf`.
  - JSON manifests remain rights and provenance only, checked by Python. The runner never parses JSON (no C JSON parser).
  - **Reversibility:** reversible.
- **D-21:** **Case-file key whitelist.** Keys: `id`, `rom`, `rom_sha256`, `rom_size`, `oracle`, `reference_digest`, `input_script`, `input_sha256`, `budget_half_dots`, `model_pass`, `model_fail`, `expect_fail_reason`, `target_revision`, `predicate`, `expect_hw_capability`.
  - Oracle values: `progress-predicate`, `frame-digest@ldbb`, `frame-digest@t=<half-dots>`.
  - `fibonacci-ldbb`, `screen-text` and `rtc_policy` are **rejected** until the phase that needs them, which keeps the whitelist honest.
  - Unknown keys or oracle values, duplicate keys and duplicate ids are errors and are never ignored.
  - Digests are exactly 64 lowercase hex characters. Numbers are range-checked.
- **D-22:** **Applicability semantics.** One pure function, `case_applicability(case, model, revision)`:
  - model in `model_pass`: expected to pass;
  - model in `model_fail`: a strict expected failure with the declared reason, where an unexpected pass is a failure;
  - model in neither list: `excluded`, reason `unsupported-model`, exit 4;
  - `target_revision` mismatch: `excluded`, reason `target-revision`;
  - model in both lists: a parse error.

  The receipt prints `eligible= executed= excluded= xfail=`. A suite passes only if `eligible>0`, `executed==eligible`, and `excluded` equals the count declared at CTest registration.
  - Never use CTest `SKIP_RETURN_CODE`.
  - Each exclusion has its own named test asserting exit 4 and its reason.
- **D-23:** **CLI.** Existing invocations stay unchanged.
  - Comparison mode: `gbb_runner --acceptance <cases.txt> (--case <id> | --suite) [--model dmg-cpu-b] [--revision R] [--failure-dir <dir>] [--receipt]`. All expectations come from the case file.
  - `--observe` prints the observed digests and cannot write the case file. Flags such as `--input-script`, `--frame-digest-at` and `--pcm-digest` are valid only with `--observe`.
  - Exit codes: 0 pass, 1 fail, 2 invalid input, 3 unsupported/timeout, 4 excluded.
- **D-24:** **Canonical RGB digest.**
  - SHA-256 over the ASCII header `GBB-RGB888-v1 160x144\n` followed by 160×144×3 bytes, row-major, in R,G,B order.
  - DMG shade map: 0→(255,255,255), 1→(170,170,170), 2→(85,85,85), 3→(0,0,0).
  - Later CGB RGB555 expands into the same container as `(x<<3)|(x>>2)`, with no change to DMG digests.
  - On failure only, write a binary PPM P6 of the same pixels to `<failure-dir>/<id>.ppm`. Ids match `[a-z0-9-]`, and a missing or unwritable directory is exit 2.
  - Capture uses the first frame completed at or after the checkpoint time, via the public frame-copy API. A capture with no completed frame is an error, never an all-zero frame.
  - The researchers disagreed on what to hash. **Reconciled:** the predicate research proposed hashing raw shade bytes, but this canonical digest is used everywhere (acceptance, baseline, `LD B,B`) so that one definition serves EVID-01 and EVID-02.
  - **Reversibility:** costly. Every recorded digest in the baseline and later CGB references depends on it, which is why the header carries a version tag.
- **D-25:** **Frame checkpoints for Libbet:** `title`, `play_start`, `mid` and `hit` (at `T_hit`). Each records label, requested time, completion half-dots and digest. Structural assertions: not uniform, at least 3 distinct shades, `hit != title`. Also record one rolling digest over every completed frame in the run, so transient glitches between checkpoints are caught.
- **D-26:** **Digest independence (anti-circularity).**
  - A `reference_digest` for a test-ROM frame oracle must come from an independent source: a hardware-verified reference image converted offline with stdlib `python3 -I`, with provenance recorded.
  - Libbet frame and PCM digests have no independent oracle. They are labelled **regression** class in the ledger and the case file; the predicate is the acceptance gate.
  - Before blessing, inspect the failure-path PPM of each Libbet checkpoint once and record that inspection. Optionally cross-check the static title frame against another emulator **locally only**, as a private observation, never in CI or the repo.
- **D-27:** **ROM buffers move to the heap**, with one 8 MiB cap matching the tracer path. Each case is checked against its exact pinned `rom_size` plus SHA-256 before the core sees it. This avoids an 8 MiB stack array on Windows (1 MiB stack) and a Phase 8 rewrite. The Mooneye path keeps its own pinned 32 KiB expectation.
- **D-28:** **Parser bounds.**
  - Case file at most 64 KiB, at most 1024 characters per line, at most 128 cases.
  - Errors read `invalid-cases: <reason> line=<n>` with exit 2.
  - The whole file is validated before any case runs. Reads go through the existing bounded-read helper.
  - Paths are relative, with no `..`, no leading `/` or `\`, no `:` and no empty segments.
  - Files open only with `rb`/`wb`.
  - A `test_acceptance_parse` boundary matrix (mirroring `loader_boundary_fuzz`) plus negative case files under `tests/acceptance/negative/`: flipped digest, bad script, oversize file, duplicate id, unknown key, path traversal, and the altered-input control.
- **D-29:** **Harness layout.**
  - `tests/acceptance/CMakeLists.txt`, included from `tests/CMakeLists.txt`.
  - `tests/acceptance/{cases.txt,inputs/*.input,negative/}`.
  - Registered tests: `acceptance_<id>`, `acceptance_suite`, `acceptance_parse_*`, the control tests, `acceptance_<id>_excluded_<model>`, and the G5 negative tests.
  - Every new name is added to `tests/expected-tests.txt` in the same change, under the existing exact-inventory and skipped-test rejection (GB-CI-003).

### D. Baseline freeze (EVID-02) and player smoke (GAME-03)
- **D-30:** **Baseline ledger** `tests/baseline/dmg-cpu-b-v1.txt`. Committed, sorted `key<TAB>value` lines, `eol=lf`.
  - Header: `schema 1`, `model DMG-CPU-B`, `frozen_revision <40-hex>`, `frozen_date`, and a coverage statement saying the ledger proves only the listed workloads.
  - Sections:
    - `inventory.*`: frozen core and player test-name lists, with `inventory.sha256` recorded as provenance only;
    - `mooneye.<id>`: register closure, frame count, canonical `LD B,B` frame digest;
    - `acceptance.libbet.*`: checkpoint frame digests, rolling digest, PCM stream digest, `T_hit`;
    - `regression`-class labels;
    - `bench.*`, advisory only.

  No JSON, so no parser is needed in shell or C.
  - **Reversibility:** costly. Phases 8–15 cite this file as their identity contract.
- **D-31:** **Identity definition.**
  - Every frame, PCM and Mooneye line recomputed at the PR head equals the ledger.
  - Inventory identity is a **monotonic superset**: every frozen name still exists, passes and is not skipped in the current JUnit report, and new names are allowed. A removed or renamed frozen name fails unless the change is approved.
  - A missing line, or an unknown extra line inside a frozen section, fails.
  - The check prints one line per category and exits non-zero on any difference.
- **D-32:** **Benchmarks are advisory.** They are excluded from byte identity, per D-016.
  - Each run records revision, build, hardware, workload, model, output digest, warm-up, samples and uncertainty, reusing `tests/measure_core.c` and `tests/scripts/measure-release-baseline.sh`.
  - Only the benchmark's **output digest** is identity-checked. Timing is reported, for example median and spread against the baseline, and never fails the check.
  - Thresholds wait for repeated same-hardware samples, in a later phase.
- **D-33:** **Per-OS rule.** Linux, macOS and Windows must produce identical digests, and there is never a per-OS ledger. A cross-OS mismatch is a defect to investigate.
  - Hash only explicitly serialized byte buffers: never struct memory, float `printf` output or text-mode output.
  - Open files in binary mode.
- **D-34:** **Approved-change protocol.**
  - The ledger changes only in a dedicated `baseline: <reason>` commit that touches nothing in `src/`.
  - `tests/baseline/CHANGES.md` records, for each changed line: old digest, new digest, reason, evidence class and citation, and approver.
  - The checker fails if any digest differing from `frozen_revision` lacks a matching CHANGES entry (an old/new string match).
  - There is no `--update` that rewrites the ledger. A `--print-candidate` mode only writes to stdout.
  - Phase 8 and Phases 11+ default to zero changed lines.
- **D-35:** **Single check placement.** One entry point, `tests/scripts/verify-dmg-baseline.sh`, run under `bash` as the existing Windows CI steps already do.
  - Registered as a CTest test, so it appears in the JUnit inventory and cannot be skipped silently.
  - Runs in all three native CI jobs and feeds the aggregate required gate, using the existing exact-head mechanism (D-017).
  - The digests come from runner `--observe`/receipt output, so the script only compares text.
- **D-36:** **Player smoke mechanism.**
  - Extend the shipped diagnostic family (`--smoke`, `--smoke-package`, `--audio-dummy-smoke`, …) with a bounded `--input-script <file>` on the `--smoke-package` path.
  - Run it on the **packaged, extracted** player under `SDL_VIDEO_DRIVER=dummy` and `SDL_AUDIO_DRIVER=dummy`.
  - Scripted events must enter through the **same session step and input path** as keyboard input; only the event source differs.
  - The player evaluates the same named predicate (D-08) and prints one stable line: `smoke_report rom_sha256=<…> half_dots=<n> predicate=pass pcm_nonsilent=1 pcm_sha256=<…>`. It exits 0 only on pass.
  - The PCM is measured at the session buffer before SDL. Its digest must equal the headless acceptance PCM digest for the same script, which proves the player path adds no corruption.
  - The no-input control also runs through the player and must fail. `tests/player/test_session.c` keeps fast session-level negative controls.
- **D-37:** **Player smoke OS matrix.** Run on **macOS**, in the existing `macos-player-package` job, which is the only packaged player today. GAME-02 headless runs on all three OSes.
  - Do not add Linux or Windows player packaging in this phase: that is new platform scope. Record it as an explicit limitation in the support ledger.
  - Keep the existing rule that a skipped required player job is red. Check that the PR-only `player_required` gating cannot let a merge revision omit the smoke without the aggregate gate failing.
- **D-38:** **Flag policy.**
  - `--input-script` is a developer diagnostic listed in `--help` next to the existing diagnostics.
  - It only reads: one script file and one ROM path, output to stdout only, no save writes, no network.
  - It is bounded by D-12 and rejects bad input before any state mutation.
  - No environment-variable activation and no interactive UI exposure.
  - The attack surface stays equal to that of the existing `--smoke`/`--audio-measure`.

### Claude's Discretion
- Exact source file split inside `src/runner/` (e.g. `cases.c`, `input_script.c`, `digest.c`), the helper names, and the receipt formatting.
- Whether the G5 verifier extends `verify-support-ledger.py` or is a sibling script.
- Exact PCM threshold values after first-run calibration (D-16), recorded with the observed numbers.
- Plan and wave ordering. The suggested order:
  1. Admission and verifier.
  2. Runner parser, digest and stepping.
  3. Acceptance, controls and the pre-freeze investigations (D-19).
  4. Player smoke.
  5. Baseline freeze last.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope, requirements, decisions
- `.planning/ROADMAP.md` §Phase 7 — goal, success criteria, rights gates G5 and G2.
- `.planning/REQUIREMENTS.md` — GAME-01..03, EVID-01..02 (and CGB-11, which reuses this acceptance style).
- `.planning/context/DECISIONS.md` — D-014 (per-asset rights), D-015 (qualified claims), D-016 (benchmarks), D-017 (exact-head checks), D-025, D-026 (Libbet primary).
- `.planning/context/LESSONS.md` — GB-GAME-001 (game-level progress and bounded stall trace), GB-CI-003 (skipped-test rejection), GB-FIXTURE-001, XFER-006.
- `AGENTS.md` — engineering rules (bounded parsing, no raw struct dumps, fixture rights and digests, no invented UAT).

### v0.2 research
- `.planning/research/v0.2/SUMMARY.md` — P1 deliverables, Conflicts Reconciled, gates G2/G5.
- `.planning/research/v0.2/FEATURES.md` — Libbet candidate, SGB-flag note, progress-is-guest-observable rule.
- `.planning/research/v0.2/PITFALLS.md` — V2-01 (DMG regression), V2-26/V2-27 (acceptance pitfalls), V2-17 (game licence).
- `.planning/research/v0.2/STACK.md` — `LD B,B` frame capture, manifest field proposals, notices layout.
- `.planning/research/v0.2/ARCHITECTURE.md` — the DMG digest baseline must exist before array reshaping.
- `.planning/research/PITFALLS.md` — F-01 (denominators), F-10 (negative controls), F-16 (canonical hashing).

### Existing patterns to follow
- `src/runner/main.c` — compiled Mooneye table, SHA-256 implementation, exit codes, bounded reads.
- `fixtures/mooneye/{manifest.json,ELIGIBILITY.md,SOURCES.md}`, `fixtures/*/manifest.json`, `THIRD_PARTY_NOTICES.md`, `.gitattributes`.
- `.github/workflows/{ci,fixture-repro}.yml`, `.github/scripts/check-player-result.sh`.
- `tests/scripts/{verify-support-ledger.py,verify-phase3-player.sh,verify-release-candidate.sh,measure-release-baseline.sh,reproduce-mooneye.sh}`.
- `tests/{CMakeLists.txt,expected-tests.txt}`, `tests/player/{CMakeLists.txt,expected-tests.txt,test_session.c}`, `tests/measure_core.c`.
- `include/gabbaboy/gabbaboy.h` — `gbb_queue_events` (64-event queue), `gbb_run_audio`, `gbb_copy_frame`, `gbb_peek_ram`.
- `src/player/{main.c,session.c,input.c,audio.c}` — the existing diagnostic flags and session step.

### Research evidence produced in this discussion (scratch, not committed)
- `/private/tmp/claude-501/-Users-jon-projects-gabbaboy/80a682e3-79a9-4b29-b922-d91b64a79031/scratchpad/phase7-predicate-report.md` — full predicate/input research with measurements. The scratchpad also holds the Libbet clone, the downloaded ROM and the rebuild. It may be gone by planning; the decisions above carry the needed facts.

### Upstream primary sources
- https://github.com/pinobatch/libbet at commit `46a765a2c01701bffb8c0b7dd6e4be3a6b193090`: `LICENSE`, `README.md`, `makefile`, `src/*.z80`, `tilesets/`, `05-burndown/note_from_nocash.md`.
- https://problemkaputt.de/magicflr.htm — Korth's original (freeware sample, no formal licence).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **SHA-256 in `src/runner/main.c`:** reuse for frame, PCM and script digests; no new library.
- **Public API:** `gbb_queue_events` (scripted input, 64-entry queue), `gbb_run_audio` (stepping plus PCM; returns early on `HALTED_IDLE`), `gbb_copy_frame` (160×144 shades 0–3), `gbb_peek_ram` (predicate reads), and `gbb_run_ex` bounded diagnostics (SGB pulse count, stall trace).
- **Player diagnostics:** `--smoke`, `--smoke-package`, `--audio-dummy-smoke`, `--audio-measure`, `--battery-smoke-*`. Existing scripts already set `SDL_VIDEO_DRIVER=dummy` and `SDL_AUDIO_DRIVER=dummy`.
- **Tooling:** `tests/scripts/verify-support-ledger.py` (stdlib `python3 -I` verifier pattern) and the `measure_core.c` / `measure-release-baseline.sh` benchmark protocol.

### Established Patterns
- Fixture admission:
  - `fixtures/<name>/{manifest.json,LICENSE.txt,SOURCES.md}`;
  - a `THIRD_PARTY_NOTICES.md` row;
  - `.gitattributes`, with `-text` for ROMs and `eol=lf` for digested text;
  - a pinned manifest blob digest.
- Exact test inventory in `tests/expected-tests.txt` (184 names) and `tests/player/expected-tests.txt` (51). Skipped or errored testcases are rejected.
- Runner exit codes 0, 1, 2 and 3; this phase adds 4 (excluded). Its ROM and manifest are stack arrays today (`MAX_ROM 32768`, an exact-size check), and D-27 moves them to the heap.
- CI: `ubuntu-22.04`, `macos-14`, `windows-2022` with `shell: bash`. The macOS player package is PR-only via `player-gate` / `check-player-result.sh`.

### Integration Points
- `tests/CMakeLists.txt` includes the new `tests/acceptance/CMakeLists.txt` and the CMake-generated mutant-core library (D-14).
- `.github/workflows/ci.yml`: the baseline check and acceptance in all native jobs, and the player smoke in `macos-player-package`.
- New `.github/workflows/libbet-repro.yml`, opt-in and non-required.
- Support ledger and docs gain the Libbet scope statement and the player-platform limitation.

</code_context>

<specifics>
## Specific Ideas

- The owner's standing preferences:
  - fan out deep multi-lens research with an adversarial pass, then auto-follow the coherent recommendations;
  - "another copy and paste is better than another dep".

  Every decision above keeps the required path dependency-free. Pillow and RGBDS 0.7.0 appear only in the opt-in repro job.
- Measured facts to keep as citations in plans:
  - title ready at about f444;
  - Start effective from f449;
  - score 4/4 at about f894 with Start at f500;
  - no-input title PCM is DC (peak-to-peak 0);
  - gameplay peak-to-peak 65535 with 10k–42k transitions per 60 frames;
  - `hw_capability` stays `$00` throughout on DMG;
  - `gbb_run_audio` can consume 0 half-dots with a remaining budget of 8.
- Still unverified, to confirm during execution:
  - cross-OS digest identity;
  - PCM thresholds;
  - layout-independence of the 100% gate beyond the start times tried (449–500);
  - SDL dummy-driver behaviour on hosted runners for the macOS packaged path;
  - the zero-consume stop-reason code.

</specifics>

<deferred>
## Deferred Ideas

- Linux and Windows packaged-player smoke: needs player packaging on those platforms, which is a separate scope decision.
- Migrating the Mooneye compiled table into `cases.txt`: in the phase that next touches Mooneye (Phase 8 brings the mbc2/mbc5 derivatives), behind a digest-identical guard.
- `fibonacci-ldbb` oracle in the case file, `screen-text` oracle, `rtc_policy`: Phases 8–9 (rtc3test) and the CGB phases.
- A benchmark regression threshold: after repeated same-hardware samples exist.
- Promoting `libbet-repro` to a required check: an owner choice, with no manifest change needed.
- A second game (Tobu Tobu Girl, for MBC1 and battery coverage): only after G2 clears, as a separate admission.
- Independent-emulator cross-checks of Libbet frames: a private local observation only, never committed.

</deferred>

---

*Phase: 07-dmg-game-acceptance-and-regression-baseline*
*Context gathered: 2026-10-10*
