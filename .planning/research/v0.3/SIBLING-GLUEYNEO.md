# Glueyneo lessons for GabbaBoy v0.3 (STATE-01 + INT-01) and the rolling roadmap

I inspected the glueyneo repository read-only at HEAD `a525e49a` (2,111 commits) on 2026-10-24. Nothing was built, run or modified there. Paths below are relative to the glueyneo repository root unless they are marked "GabbaBoy".

Each item is labeled **[V]** when I checked it in a file, a commit or with a count. It is labeled **[C]** when it is something glueyneo states in its own research or plans that it has not demonstrated.

## 0. Baseline facts that bound every transfer

- **[V] Glueyneo has not implemented save states.** `src/libretro/libretro_core.c:716-728`: `retro_serialize_size` returns 0, and both serialize and unserialize return false. Its PROJECT.md places "public snapshots and durable saves" in the *next outline* (`.planning/PROJECT.md`, Active; `.planning/workstreams/first-playable-game/ROADMAP.md`, Milestones). All of its save-state material is design research and adversarial review, not implementation experience.
- **[V] Glueyneo has not integrated with Playstead.** INTEG-01 is in the "Revisable Longer Horizon" (`.planning/workstreams/cpu-bus-diagnostic-sdk-alpha/ROADMAP.md:250`, `REQUIREMENTS.md:75`). Its only frontend is a libretro core running in pinned RetroArch 1.22.2.
- **[V] Glueyneo has not published a release.** `docs/releasing.md` ("Current qualification boundary") lists App-token behavior, the protected merge and release publication as pending. GabbaBoy has shipped v0.1 and v0.2.0, so it is ahead on release practice.
- **[V]** `.planning/estimation-calibration.json` holds `samples: []`. There is no effort-calibration data to borrow.

So glueyneo is "most mature" by commit count and by process scar tissue, not by having shipped state or Playstead features. Its most valuable lessons are about process velocity. Its state and Playstead lessons are good design checklists and recorded contracts.

## 1. Process and velocity: what made phases balloon, and what fixed it

### 1.1 Quantified ballooning [V]

Plan counts come from the PLAN/SUMMARY files in each phase directory. Commit counts come from `git log --grep "(NN-"`.

| Phase | Plans | Commits | Dates | Main driver |
|---|---:|---:|---|---|
| 01 CPU acceptance | 29 | 151 | 10-01..10-05 | Stale `gaps_found` routing created repeated gap plans (see 1.3) |
| 02 SDK | 6 | 23 | 10-05..10-06 | normal |
| 03 release qualification | 5 | 23 | 10-06..10-07 | 7 failed hosted attempts before the first green matrix (`03-HOSTED-QUALIFICATION.md:131-139`) |
| **04 public playable tracer** | **65** | **376** | 10-07..10-11 | About 59 plans repaired evidence and governance tooling, not emulation (see 1.2) |
| **05 (old, retired)** | **38** | most of **835** | 10-08..10-16 | Finite-observation quota protocol with one opcode per counted "rerun" (see 1.4) |
| 05 (redone after the reset) | 4 | — | ..10-20 | One coherent repair plan per layer |
| 06 active title control | 4 | 129 | 10-20..10-23 | normal |
| 07 sound (in progress) | 7 | 71 | 10-23.. | normal; headless loop (see 4) |

### 1.2 Phase 04: recursive review of gate tooling [V]

- The phase directory holds `04-REVIEW-GAPS.md` plus R2–R11 and `04-REVIEW-FIX-R6..R9`. Findings per round: R2 2 critical/6 warning, R3 0/5, R4 0/4, R5 0/2, R6 0/3, R7 2/3, R8 0/0, R9 0/1, R10 0/0, R11 0/0.
- Plan objectives 04-07..04-65 are almost entirely about `tools/verify_playable.py`, the security register, review provenance, private-path redaction, rights-inventory digests and the squash-history allowlist. That tool is 2,558 lines and its test file is 3,504. Each round re-ran the RetroArch qualification (04-41, 04-50, 04-53, 04-64).
- The gate tooling was itself the subject of each review, so every repair exposed new fail-open edges in the gate. R7 is an example: "fix commits edited test file but did not update its rights-inventory row", plus "allowlist generated against stale local main".
- **Fix adopted, 2026-10-11:** the "Review-round convergence" rule in `.planning/METHODOLOGY.md:228-238`:
  - A gap plan that repairs review findings carries its own focused review of the repair diff, in the same execute run.
  - The next code-review round is scoped to the repair diff only.
  - If that round finds only Info, or Warnings that are not regressions and do not weaken a gate, the findings are recorded as `open`/`deferred` and the loop closes. No new round starts in that phase.
  - Criticals, repair regressions and gate-weakening Warnings still block.
- The companion rule (METHODOLOGY step 4): review and security findings are routed by policy from a disposition record, not through an owner checkpoint.
- **GabbaBoy gap:** I found no equivalent convergence rule in GabbaBoy's `.planning/context/LESSONS.md`, `.planning/context/DECISIONS.md` or `AGENTS.md`; grep found no hits for convergence, repair-diff or review round. GabbaBoy Phase 15.1 (36 plans, two gap rounds, two re-audits) shows the same dynamic.

### 1.3 Stale verdict routing [V]

- `.planning/preparation/2026-10-04-gsd-verification-loop.md`: OpenGSD 1.15.0 returned `gaps_found` before checking the covered-input fingerprint, so a repaired phase kept routing back to `--gaps` planning. Meanwhile execute-phase skipped re-verification.
- **Rule adopted:** after any gap plan changes covered files, run one fresh whole-phase verifier before creating another gap plan, and never repeat a gap that current evidence has closed. It is also PROJECT-D-46.
- A second footgun in the same incident: a frozen validator required an exact ROADMAP sentence. A prose edit (`c18233c`) turned CPU-05 red.
- GabbaBoy already holds the freshness half (GB-GSD-008, GB-GSD-024). The "exact wording is an interface" half is in glueyneo METHODOLOGY ("When an acceptance check matches exact wording in a planning document, treat that wording as an interface…").

### 1.4 Quota and ceremony protocols that displaced debugging [V]

- The old Phase 05 used a "C1–C50 lifetime counter", consumed test slots, per-run observation owners and publication/pin ceremonies (`.planning/workstreams/first-playable-game/DEVELOPMENT.md`, "Development loop").
- `git log` shows 157 `rerun N` commits from 2026-10-12 to 10-14, plans 05-20..05-27. Each one was a RED/GREEN/record triple for a single opcode or port. Examples: `5fc0e309 feat(05-27): rerun 43 CPU BTST immediate data register`, and `38b2bd46 revert(05-21): withdraw rerun 10 …`.
- On 2026-10-16 the user retired the protocol (PROJECT-D-49; `retired/2026-10-16-development-workflow/README.md` keeps 127 files as history only).
- The redo used one plan, "05-02 Evidence-led coherent CPU/board repair". Phases 05, 06 and 07 then ran at 4, 4 and 7 plans.
- **Transferable rule** (DEVELOPMENT.md, "Development loop"; METHODOLOGY, "Evidence-first delivery"):
  - Ordinary reproduce/fix/regress/rerun work happens inside the authorized step.
  - Bound effort by session time and per-invocation emulated work, never by lifetime counts.
  - Repair a coherent class per plan, not the first fault per cycle.
  - Do not "extend, reset, translate or replace that scheme with a differently named quota".

### 1.5 Other velocity items [V]

- **Forward progress while blocked** (METHODOLOGY, "Forward progress while a phase is blocked"): an external, physical or user acceptance blocker does not justify another gap plan. Downstream work that only consumes verified artifacts may proceed, with the distinction recorded in ROADMAP.
- **Tracked-evidence writers** (METHODOLOGY pre-flight step 5): run them as one plain command from an absolute root, so a permission denial does not force a manual handoff. Tooling should write tracked evidence in the same command that produced and checked it.

## 2. Save-state / snapshot design (research contract, not implementation)

### 2.1 Design contract [C, well sourced]

From `.planning/preparation/C-CORE-ARCHITECTURE.md:85-95`, `.planning/research/PITFALLS.md:108-118` (P7), `.planning/preparation/ADVERSARIAL-REVIEW.md:33-41` (A-03) and `.planning/preparation/DECISIONS.md:53-58` (D-23, D-25):

- **Format:** explicit fields or chunks with magic, format version, sizes, a machine/content compatibility fingerprint and an integrity check. No pointers, padding, callback addresses or raw structs.
  - Bound every length and allocation.
  - Reject unknown *required* chunks and inconsistent combinations.
- **Transactional apply:** validate into temporary state, then commit atomically, so a bad snapshot cannot half-mutate a running machine.
- **Complete hidden state:** CPU partial execution (if supported), scheduler deadlines and phases, pending interrupts, bus latches, video state, chip/audio history and pending outputs.
  - Rebuild derivable caches deterministically and exclude them from the format.
  - Document that snapshots require an execution boundary. Do not expose arbitrary-cycle snapshots early.
- **Separate identities:** library release, native ABI, snapshot schema, replay behavior and battery-save compatibility each get their own version.
  - Guest-state hashes exclude host-only counters, diagnostics and delivery/acknowledgment bookkeeping.
- **Battery interaction:** the battery has a monotonic dirty generation plus host acknowledgment.
  - Restoring an old snapshot may rewind the guest's battery bytes, but it must not roll the host generation backwards.
  - An old acknowledgment arriving late must not clear newer writes.
  - This maps directly onto GabbaBoy STATE-01's "preserve good disk battery data under explicit restore policy" (GabbaBoy `.planning/milestones/v0.1-REQUIREMENTS.md:82`).
- **Gate** (P7 "Bounded evidence gate"):
  - Compare an uninterrupted run with save → destroy → fresh instance → restore, at *equal output-consumption boundaries*.
  - Malformed state must leave the live machine intact.
  - Test restore after newer durable writes, and a late old acknowledgment.
  - Warning signs: "nonempty save file called continuation proof; dump of native struct; reset-on-boot counter as restore oracle". The last one comes from Playstead's `savetest` ROM (`.planning/preparation/PROJECT-DNA.md:44,107`).
- **Libretro:** rewind wants a stable serialize size and layout. Check it against the pinned header (C-CORE-ARCHITECTURE.md:93).

### 2.2 Mechanisms glueyneo did build that apply to "hidden in-flight state" [V]

- **Machine-checked state inventory:** `tools/owned_cpu/inventory.py` with `experiments/owned_cpu/state-inventory.json`.
  - It regex-parses `struct owned_cpu` and the private `owned_cpu_state` record. Any unparsed declaration line is an error.
  - It fails on missing, extra or changed fields, on an empty `capture_disposition`, on a host-binding field that does not name its destination ownership, on stale source hashes and on hidden file-scope globals (`inventory.py:153-260, 285-330`).
  - A `self-test` mutates the inventory and requires each named failure (`inventory.py:532-600`).
  - Each field records classification, mutation sites, `capture_disposition` and `reset_disposition`.
  - For STATE-01, this pattern turns "did we forget a latch?" into a test that fails at the commit that adds a new machine field.
- **No-mutable-globals audit:** `tests/tools/check_runtime_storage.py`, registered as CTest `runtime_writable_storage` (`CMakeLists.txt:1127-1135`; `docs/testing.md`, "Runtime writable-storage audit").
  - It runs `nm` over the runtime library and fails on *any* writable data, BSS, common or TLS symbol. There is no allowlist; a table that is never written is made `const`.
  - It cannot pass vacuously ("no symbols parsed" fails), and an unsupported platform reports skip 77 rather than a pass.
  - This proves the instance struct is the complete state universe, which is the precondition for a complete snapshot.
  - GabbaBoy has nothing equivalent; grep for `nm`/bss/writable-storage in GabbaBoy `tests`, `cmake` and `CMakeLists.txt` found nothing. GabbaBoy only has `_Static_assert` layout checks (GabbaBoy `src/core/gabbaboy.c:364-365`).
- **Rejection invariants with peer isolation:** `tests/fuzz/regressions.json:22ff`. Each rejected media case asserts an exact status *and* "live target and peer remain unchanged". The harness is deterministic seeded xorshift with 1,024 iterations, a named corpus and a failure-ID-preserving minimizer (`tests/fuzz/minimize.py`; `docs/testing.md:60-86`).
  - For STATE-01 load fuzzing, assert the exact error, that the target is byte-identical (via a state hash), and that an independent peer instance is unchanged.

### 2.3 Continuation-comparison lesson from actual audio work [V]

`07-LEARNINGS.md` GN-DEV-L002: complete PCM equality was justified only after showing a common stage (callback PCM before resample or mute) and an endpoint at an actual completed frame boundary. A partial final batch had to be rejected. For STATE-01, continuation equivalence should compare video, audio and battery output at the same emulated boundary and stage, and reject truncated tails.

## 3. Playstead / libretro / frontend integration

### 3.1 Playstead [V, as recorded by glueyneo at an inspected Playstead revision]

- Playstead integrates by **launching an external emulator process**. There is no native C/FFI seam (`C-CORE-ARCHITECTURE.md:53`; PROJECT.md, Context).
- Glueyneo's INTEG-01 defines "host-process" as Playstead launching an existing frontend with the core's libretro module, or a future shared host. It explicitly excludes a core-owned GUI.
- **Target contract** (`cpu-bus-diagnostic-sdk-alpha/REQUIREMENTS.md:75`, `ROADMAP.md:250`):
  - ROM path plus an explicit save-directory override.
  - Never write saves beside the ROM.
  - Flush battery saves periodically and on request, with a stated maximum-loss window.
  - Stop cleanly on SIGTERM.
  - Distinct exit codes for normal completion, guest error and host error.
- **Actual Playstead behavior at revision `1de3e954` (2026-10-02)**, from `AdapterPin.json` and `SUPPORT-MATRIX.md`:
  - Saves go to `{saveDir}/{romBaseName}.sav`.
  - Periodic flush every 24 s, with no on-demand flush, so the loss window is 24 s.
  - SIGTERM is classified as *killed*, not a graceful save-and-quit.
  - Glueyneo says to "Recheck the live launcher contract when planning this work."
- **Playstead's own continuation gate was blocked:** the installed emulator could not qualify noninteractive script loading, deterministic input or a repeatable visible-state oracle (`PROJECT-DNA.md:40`). Playstead also had a shared process registry that could kill another test's emulator (PROJECT-DNA.md:76).
- **Implication for GabbaBoy INT-01:**
  - Start with a read-only spike on the *live* Playstead adapter contract (AdapterHost/AdapterPin/SaveCompatibilityGate, DNA-01/02).
  - Decide early whether "qualified Playstead adapter" means a process adapter (GabbaBoy's runner or player, launched by Playstead) or a libretro module. GabbaBoy has no libretro adapter; its research chose native API plus the SDL player (GabbaBoy `.planning/research/SUMMARY.md:73`).
  - GabbaBoy's headless runner can supply exactly the deterministic-input and visible-state oracle that Playstead lacked.

### 3.2 Libretro adapter footguns, if GabbaBoy adds one [V]

- In a shared build, the installed core linked `libglueyneo.dylib` with no rpath, so RetroArch could not open it. **Fix:** a single self-contained module in both build modes, plus a package check that rejects a core depending on the library (`docs/first-playable-build.md:76`; commit `5e6a3b8f`).
- Batch-first audio with a per-sample fallback. A failed frame submits a blank frame and no audio (`libretro_core.c:700-720`). NEST-XFER-01 (`.planning/preparation/2026-10-09-sibling-lessons.md`) compares adapter callback PCM with a separately stepped native instance and checks failed-frame silence.
- RetroArch quirks (07-LEARNINGS S001–S003):
  - The WAV recorder writes a 56-byte padded header, sometimes under a `.mkv` name.
  - The first-frame AV announcement restarts the recorder.
  - Localized logs hid the driver-selection message.
  - Rule: use exact format checks, not extension or regex inference. Process exit 0 is not proof that capture completed.
- A run must be bound to the *current-source* core. `bef780b3 fix(06-04): reject stale frontend core builds` and `e2f0faf5` both rejected stale builds.

### 3.3 Adapter vs core boundary [V/C]

- The host owns files, archives, windowing, device audio, input mapping, pacing and network. The core owns deterministic guest time (PROJECT.md, Context). GabbaBoy already follows this.
- Persistence: the core exports bytes, a medium identity and a dirty generation. The host acknowledges a generation after its own durability policy succeeds (`C-CORE-ARCHITECTURE.md:48`). The core never decides that a disk write was committed. GabbaBoy's battery block should be checked against this for INT-01, because a Playstead periodic flush is a host durability policy.

## 4. Test architecture, corpus, CI and release

- **Cheapest decisive check first** (07-LEARNINGS GN-DEV-D001..D004, P002) [V]:
  - A fresh full frontend campaign took about 24 min with repeated foreground windows.
  - Re-evaluating the 60 retained PNGs took 4.0–4.3 s.
  - A headless libretro replay comparing every PCM byte took 58 s.
  - Keep retained *acquisition* separate from current *evaluation*, labeled `new_frontend_observation=false`, `device_evidence=not-refreshed`.
  - Treat the shared desktop as a resource: explain the missing fact, window count and duration before any foreground run, and never fall back silently from headless to GUI.
  - GabbaBoy's SDL player smoke and Playstead process tests should default to headless in the same way.
- **First-seam isolation** (GN-DEV-L003, commits `aaf43548`, `07bc1dee`) [V]: the visual-first runner spent eight visual boots before reaching the audio tracer. Ordering the new seam first, plus a seam-only flag, made faults reachable. For INT-01 that means a save/flush/SIGTERM tracer before any full play matrix.
- **Prose-claim gates are expensive** [V]: plans 04-17..04-21 include `a9645b14 reject alternate frontend claim wording` and `4e8ebf69 reject affirmative frontend guide claims`. Regex over documentation wording kept finding new phrasings.
  - The durable fix was a *generated* status block written from the receipt (`--record-frontend-evidence`, then `--check-docs`; `docs/first-playable-build.md:82`).
  - Prefer generated blocks to wording scanners.
- **Release design** [V design, not exercised in publication]:
  - A draft-first release; the tag must resolve to the tested commit.
  - Three hosted jobs re-download the staged assets and rebuild offline.
  - Partial-upload recovery keeps only matching assets and stops on extra or replaced ones (`docs/releasing.md:1-50`).
  - GabbaBoy already rehearses exact-tag producers. Glueyneo's partial-draft recovery cases (`tests/workflow/test_release_recovery.py`) are a checklist only if GabbaBoy's release ever partially uploads.
- **Hosted CI failures** (`03-HOSTED-QUALIFICATION.md:131-139`): GCC qualifiers, MSVC alignment, CRLF fixture bytes, Windows `.lib`/`.exe` suffixes, DUMPBIN exit code. GabbaBoy already covers these (GB-FIXTURE-001 CRLF, GB-CI-008 native artifact names), so they are not new.

## 5. Roadmap structure

- **[V]** The rolling structure is "In progress / Next outline / Longer horizon" (first-playable ROADMAP, Milestones; PROJECT-D-41–44: "detail the current deliverable, outline the next milestone and keep the longer horizon revisable"). GabbaBoy's FUTURE-MILESTONES.md already does the same.
- **[V] Two workstreams diverged:** v0.1 "CPU/bus diagnostic SDK alpha" is still open, with release pending, while the first-playable-game workstream ran Phases 04–07. PROJECT.md notes that the workstream "does not complete the open v0.1 lifecycle or assign a release version."
  - **Lesson:** a parallel workstream can leave a milestone open indefinitely and decouple work from releases. GabbaBoy's single milestone line with a release per milestone is better; keep it.
- **[V] Snapshots kept slipping.** Research said "State and persistence belong within that interactive acceptance scope; they are not postponed" (`.planning/research/SUMMARY.md:129`), but snapshots were later deferred behind gameplay and sound.
  - GabbaBoy is about to do STATE-01 as a first-class milestone; that matches glueyneo's own original recommendation.
- **[V] What they would do differently** (METHODOLOGY, "Evidence-first delivery"): "Reach the first useful executable emulator result early. Governance scripts, audit dashboards and evidence plumbing must stay proportional to the failure they prevent."

## 6. Where GabbaBoy is already better: do not import glueyneo's approach

- **Squash-merge evidence binding.** Glueyneo built a per-row `docs/history-allowlist.json`, plans 04-59..04-65, a 37-test `SquashMergeHistoryTest` and a user-accepted residual risk G6WR-01 (`docs/testing.md:212-240`), all to tolerate rows citing squashed-away revisions. GabbaBoy binds evidence to the merge commit or boundary commit instead (GB-EVID-002, GB-GSD-024, GB-VERIFY-002). That is simpler; keep it.
- **Shipped releases.** GabbaBoy has a qualified release practice; glueyneo has none published.
- **Shared UAT closure.** GabbaBoy's single `tests/scripts/verify-uat-closure.py` plus helpers in `tests/scripts/` (GB-GSD-024, GB-GSD-026) is ahead of glueyneo's phase-specific gate tooling (`tools/verify_playable.py`, which is Phase-04-bound).
- **Lessons register.** GabbaBoy LESSONS.md, with IDs, cause, evidence and applicability, is already equivalent to glueyneo's LEARNINGS discovery index.

## 7. Ranked recommendations for v0.3

1. **Adopt a review-round convergence rule before v0.3 execution** (glueyneo METHODOLOGY.md:228-238; Phase 04 had 65 plans and 11 rounds). This is the largest expected saving, given GabbaBoy 15.1's 36 plans.
2. **Plan STATE-01 around a machine-checked state inventory plus an `nm` no-writable-globals CTest with negative controls**, before writing the codec (`tools/owned_cpu/inventory.py`; `tests/tools/check_runtime_storage.py`; `CMakeLists.txt:1127`). This catches hidden in-flight state at the commit that adds it, rather than through later continuation failures.
3. **Write the STATE-01 acceptance contract from P7 and A-03 up front:**
   - continuation against a fresh instance at equal output boundaries;
   - malformed or truncated state leaves the target *and* a peer unchanged;
   - battery generations stay monotonic across restore, and a late old acknowledgment is tested;
   - separate snapshot, ABI and battery versions;
   - an execution-boundary-only snapshot.
4. **Run a read-only Playstead contract spike as INT-01's first plan.** The recorded contract was saves at `{saveDir}/{romBaseName}.sav`, a 24 s flush with no on-demand flush, and SIGTERM treated as killed (cpu-bus REQUIREMENTS.md:75). Decide between a process adapter and a libretro module before planning more.
5. **Bound effort by session and work, not quotas; plan coherent repair classes.** The old Phase 05 had 157 single-opcode rerun commits; the redo took 4 plans.
6. **Default the integration tests to headless and seam-first, and separate retained acquisition from evaluation** (07-LEARNINGS D001–D004, L003).
7. **Generate status and claim blocks from receipts instead of regex-gating prose** (plans 04-17..04-21; `docs/first-playable-build.md:82`).
8. **If a libretro module is chosen:** a self-contained core plus a package check against library dependencies (`5e6a3b8f`), a stable serialize size, and exact-format recorder parsing.
