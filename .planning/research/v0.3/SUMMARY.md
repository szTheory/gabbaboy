# v0.3 research summary: Save States & Host Contract

Updated: 2026-10-24, at the v0.3 kickoff. This document reconciles seven research lenses and one adversarial review. The owner confirmed the resulting v0.3 scope, the LIM defaults and the v0.2.1 patch release on 2026-10-24.

Sibling observations are evidence about other projects. They are not GabbaBoy results until a GabbaBoy check reproduces them (D-019).

## Inputs

| Lens | Document | One-line finding |
|---|---|---|
| Glueyneo (Neo Geo) | [SIBLING-GLUEYNEO.md](SIBLING-GLUEYNEO.md) | Review rounds must converge. Machine-check hidden state (struct inventory and `nm` writable-global CTest) before writing a state codec |
| Nesturbator and muhtari | [SIBLING-NESTURBATOR-MUHTARI.md](SIBLING-NESTURBATOR-MUHTARI.md) | Shipped save-state design in 10 plans. Cap tooling machinery. Rolling roadmap with RM ids, statuses and triggers |
| Genewhip, schwaystation, cogmaster, earthbound-recomp | [SIBLING-YOUNGER-CORES.md](SIBLING-YOUNGER-CORES.md) | Round caps, no quotas, a visitor-driven state codec with `_Static_assert` tripwires, the closure property, compiled behavior first |
| Playstead (consumer) | [PLAYSTEAD-CONTRACT.md](PLAYSTEAD-CONTRACT.md) | Hash-pinned macOS process adapters, with no libretro or FFI. GB/GBC already ships through mGBA 0.10.5. Save states are not in Playstead v1, and a second adapter is unscheduled |
| Save-state design | [SAVE-STATES.md](SAVE-STATES.md) | Hidden-state inventory, about 97 KB (DMG) and 143 KB (CGB) plus cart RAM, fixed per ROM. Validate-then-apply. BESS later and export-first |
| GabbaBoy delivery | [DELIVERY-VELOCITY.md](DELIVERY-VELOCITY.md) | v0.2 used 6.1 plans per requirement, and about 45% of the calendar went to post-feature closeout. CI grew from 1.5 to about 25 min, with 30% of runs red. Carry-over dispositions |
| Long-term horizons | [ROADMAP-HORIZONS.md](ROADMAP-HORIZONS.md) | Capability ladder, rights-clear CGB game candidates (Potion Panic, µCity), acid2/gbmicrotest admission paths, and what v1.0 means |
| Draft and critique | [SYNTHESIS-DRAFT.md](SYNTHESIS-DRAFT.md), [ADVERSARIAL-REVIEW.md](ADVERSARIAL-REVIEW.md) | The review reversed the draft's order: STATE-01 now precedes the full Playstead contract |

## Reconciled conflicts

1. **STATE-01 versus INT-01 first.** The horizons lens proposed putting the consumer first. The adversarial review found INT-01's only reachable exit in v0.3 is a GabbaBoy-side harness. Playstead has no scheduled second adapter, its relevant files are partly uncommitted, and GB already works there via mGBA.
   - **Resolution:** STATE-01 goes in v0.3, plus INT-01a, the part of the host contract that is valuable on its own: raw `.sav`, atomic flush, SIGTERM save-and-exit, exit codes.
   - The INT-01b pin and continuation protocol are parked until Playstead schedules a second adapter (RM-020).
2. **RTC footer interop.** It was a draft P18 item, but Playstead's restore gate matches exact format strings and forbids cross-emulator clock claims.
   - **Resolution:** GabbaBoy declares its own save-format ids (MBC3 + RTC is 32,789 B). mGBA/BGB footer import/export is parked as a demand-triggered import feature (RM-021). This supersedes the D-026 deferral note (D-104).
3. **Closeout policy.** The draft normalised `override_closeout`.
   - **Resolution:** aim for a verified closeout. Phase verification stays bound to its boundary commit, and the milestone audit runs the full suite at the exact final head. An override stays a disclosed exception (D-103).
4. **Round caps versus correctness.** Caps stay. A finding still open at the cap becomes a recorded disposition the audit lists. An unresolved correctness or security finding in new code forces a rescope; it is never turned into a seed (D-102).
5. **Quotas versus caps.** No throughput quotas, wall clocks or run counters count as verification evidence. Plan caps are planning budgets enforced by a CTest with a negative control (D-102).
6. **Planning-only CI lane.** A single required aggregator check passes on an explicit classification, so a skipped check never counts as a pass. The classifier has a negative control: a `src/` or `tests/` change never classifies as planning-only (D-105).

## Adopted v0.3 shape

Phases 16–19, at most about 40 plans in total:

| Phase | Plan cap | What it delivers |
|---|---|---|
| 16 Tune-up | 8 | <ul><li>Helpers move out of phase directories, enforced by a lint, then the v0.2 phase records are archived</li><li>Phase 8 verifiers wired into CTest; PRs #78–92 closed as superseded; LIM defaults applied</li><li>A one-plan perf attribution (default exit: accept with attribution); a cumulative instruction-count gate against `v0.2.0` plus a realtime multiple with FIFO headroom</li><li>CI hygiene; LESSONS ids deduplicated with a uniqueness test; STATE.md trimmed; stale Playstead docs corrected</li><li>v0.2.1 shipped from PR #75 once its blockers clear and the exact-tag rehearsal is green</li></ul> |
| 17 STATE-01 core | 12 | <ul><li>A struct-inventory checker and an `nm` writable-global CTest first</li><li>A 64-byte header and one field list for size, write, validate and apply; same-version only</li><li>Validate-then-apply; 64-bit time bounded at 2^62</li><li>Fork matrix with a coverage gate, closure property, field-drop mutants, fuzzing and pinned cross-platform digests</li></ul> |
| 18 Player slots + INT-01a | 10 | <ul><li>Player save slots</li><li>`--rom`/`--save-dir` mode; O_EXCL temp files in the save dir; symlinked targets refused; ROM basename sanitised</li><li>Raw `.sav` bounded by the size the cartridge header implies</li><li>SIGTERM handled as an adapter-only `sig_atomic_t` flag; exit-code table; GabbaBoy save-format ids</li><li>Windows exempt from the POSIX signal tests</li></ul> |
| 19 Release v0.3.0 | 8 | The exact-tag rehearsal runs on the version PR before tagging; release hardening happens in this phase, not after the tag |

## Watch out for

- Validate-then-apply depends on the two passes staying symmetric. Drive both from one field list and add `_Static_assert` size tripwires.
- A state that passes range checks may still be unreachable. The closure property (accepted state, run N, still saves to an accepted state) catches the dangerous subset.
- Rebuilding the PPU (v0.5) will change state contents. Same-version-only states before 1.0 make that a code change, not a compatibility break.
- The perf gate must be named before measuring: a Linux hosted Release build, a cachegrind instruction count against `v0.2.0`, and a realtime multiple.
