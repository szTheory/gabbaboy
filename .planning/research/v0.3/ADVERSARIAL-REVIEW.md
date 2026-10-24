# Adversarial review of SYNTHESIS-DRAFT.md

**Verdict: accept with changes.** The diagnosis and the process caps are sound. The v0.3 ordering is wrong, and three of the process rules weaken rigor.

## Changes, ranked by importance

1. **Swap the order: v0.3 = Tune-up + STATE-01 + host durability. Park INT-01b.**
   - The only exit INT-01 can reach is "our harness says we match their contract". Playstead has no scheduled consumer (CLNT-01 and multi-pin are unselected), and GB already ships there through mGBA.
   - Parts of that contract come from Playstead **uncommitted working-tree files** on a branch with about 1,460 dirty paths (playstead.md §Revisions). A pin or continuation harness built against them will drift.
   - STATE-01 is pure core and gives players something right away (save slots). Its fork-matrix and closure tests also find hidden state before the PPU FIFO work adds more. Nesturbator shipped the same design in 10 plans.
   - New v0.3 shape:
     - P16 Tune-up (≤8 plans)
     - P17 STATE-01 core (≤12 plans)
     - P18 Player slots + INT-01a (≤10 plans). INT-01a covers `--save-dir` raw `.sav`, atomic flush, SIGTERM save-and-exit, and the exit table. These carry durability value without Playstead.
     - P19 Release
   - Park INT-01b (candidate pin, continuation protocol) as RM with the trigger "Playstead schedules CLNT-01/multi-pin on main".
   - Update PROJECT.md Active and FUTURE-MILESTONES to match.

2. **RTC footer conflicts with its own evidence.** playstead.md recommends option (b): GabbaBoy-declared `save_format` ids at 32,789 B. Playstead's gate keys on string equality and forbids cross-emulator clock claims. So mGBA/BGB footer import/export does nothing for Playstead. Park it as a player-facing "import saves from other emulators" item triggered by demand. Record (b) as a D-entry that supersedes the D-026 deferral.

3. **Rule 5 normalises `override_closeout`.** v0.2 treated override_closeout as a regression. The fix is to make verified_closeout reachable: phase verification is bound to its boundary commit (already AGENTS policy), and the milestone audit runs the full suite at the exact final head. Delete "override_closeout accepted".

4. **Rule 1 lets correctness and security warnings become seeds.** Keep the round caps. Any warning still open at the cap becomes a recorded disposition that the audit lists. Unresolved correctness or security findings in new code trigger a rescope, never a seed.

5. **Rules 2 and 3 contradict each other.** Plan caps are quotas. Rule 2 also reads as banning the perf budget, CI timeouts and D-07-style time-boxes. Narrow it to: "no throughput quotas, clocks or run counters as verification evidence." Make the caps mechanical: a CTest that compares the PLAN count per phase dir with the ROADMAP cap and has a negative control. Otherwise they are just prose.

6. **The planning-only CI lane has to keep exact-head gates intact.** Use one required aggregator check that passes on an explicit classification. A skipped check must never count as a pass. The classifier needs a negative control: a `src/` or `tests/` change must not classify as planning-only.

7. **Tune-up risks becoming another 15.1.**
   - Take the 12 LIM rows out of the phase. Present them as one owner-decision batch at `/gsd-new-milestone`, using the velocity.md §2.1 defaults.
   - Perf bisect gets one plan, with "accept with attribution" as the default exit. A fix happens only if a single merge owns more than half the cost; otherwise it goes to v0.5.
   - Name the budget reference up front: a Linux hosted Release build, an instruction-count proxy (cachegrind) cumulative against the `v0.2.0` tag, and a realtime multiple with recorded FIFO headroom.
   - Add the stale Playstead docs (README:46, native-integration.md:277, FUTURE-MILESTONES:8, PRECEDENT, D-005) and the SUMMARY key drift.

8. **PR #75.** The tune-up clears exactly the three release blockers. Ship **0.2.1** from it when the exact-tag rehearsal is green. That gives players the #74/#94/#97 fixes and proves the release path before v0.3.0. Otherwise close it and suppress release-please regeneration.

9. **Host-adapter security and portability (P18).**
   - Derive `romBaseName` with no separators or `..`.
   - Create the temp file with O_EXCL in the save dir and refuse symlinked targets.
   - Bound raw `.sav` imports to the header-derived size, with no partial mutation.
   - Keep SIGTERM handling in the adapter only, as a `sig_atomic_t` flag. The core gets no signal code. Declare Windows as POSIX-signal-exempt.

10. **v0.4–v1.0.**
   - v0.4 becomes the Evidence Floor: acid2 font-substituted derivatives, gbmicrotest, and one time-boxed CGB game. It is the oracle that v0.5 DMG PPU work needs.
   - Owner decisions D-copyleft-fixtures and D-G1-font-strategy are due at v0.4 kickoff, not later.
   - The v1.0 "1 live consumer" depends on an outside party. Redefine it as "≥1 independent embedder (Playstead, libretro or Wasm) or an owner waiver".
   - Audio (v0.8) could swap with CGB timing if game evidence shows audio defects first.

## Accept as is
Tune-up content (helpers out of phase dirs plus lint, Phase 8 wiring, closing #78–92), rules 4, 6, 7 and 9, the STATE-01 design, and the exact-tag rehearsal.
