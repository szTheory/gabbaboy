# Phase 13: CGB HDMA - Discussion Log

> Audit trail only. Planning/research/execution consume `13-CONTEXT.md`; this log is not a second decision source.

**Date:** 2026-10-14
**Phase:** 13-CGB HDMA
**Areas discussed:** scope/API/dependencies; register/start/cancel behavior; clock/stall/bus ordering; lifecycle/safety; corpus/rights/oracles; automation/CI/consumer claims.
**Selection authority:** The owner requested broad relevant fan-out, primary sources, adversarial consideration, coherent recommendations and automatic adoption. All areas were selected and resolved under that delegation; no interactive questions were asked and no answers are attributed to the owner beyond that instruction.

## Alternatives and recommendations

| Decision | Viable alternatives and tradeoff | Adopted recommendation |
|---|---|---|
| DMA/consumer surface | Guest-only behind existing runs keeps hosts simple; public DMA controls give debug access but couple hosts to a device and widen ABI. | Guest-only, private test observations (D-01/03/23). |
| Dependency strategy | Local original helper/limited duplication is easy to inspect; another framework reduces some code but adds transitive, security and maintenance costs. | Small flat dependencies; add one only for concrete value (D-02). |
| FF51–54 observations | Exposing live cursors seems useful but conflicts with write-only registers; retaining explicit write-only behavior separates hardware programming from test diagnostics. | Internal advancing cursors, policy `$FF` CPU reads (D-04). |
| Start/cancel conflict | Pan Docs prose is conservative but cannot reproduce two concrete SameSuite expectations; the precise author tests plus SameBoy agree but do not establish physical E. | Exact `$83 → $02 → cancel $00 → $80` model cases, uncertainty/contradiction retained (D-06/07). |
| HBlank trigger | Mode-0 level is simple but can duplicate blocks and mistake LCD-off for HBlank; real visible-entry events need state. | Visible-entry scheduling plus separately named initial kick (D-07). |
| Timing model | Copy instantly is cheap but loses CPU stealing/partitions; timed device progress is more state but matches the observable contract. | Persisted master-time data transfer; independently derive overhead/phase (D-08). |
| In-flight steal | Retire-boundary flag is small but may allow later accesses; immediate nested copy can overrun budgets; reservation or narrowly persisted CPU work costs more state. | Keep public whole-instruction contract, require a focused mechanism prototype and discriminators before fixing the boundary (D-03/09). |
| Competing stalls | One exclusive reason/countdown is compact but can overwrite a still-active cause; composite/separate state preserves independent wake/completion. | Independently represent speed pause and DMA progress (D-10). |
| Bus path | CPU accessor reuse imports lockouts; general initiator framework expands refactor risk; narrow transfer dispatch shares storage without unrelated semantics. | Narrow HDMA path (D-11). |
| Invalid sources/overflow | Universal `$FF`/wrap is deterministic but unqualified; explicit unsupported/model policy is honest and keeps memory bounded. | Research the table, fail closed where evidence ends, test bounds/prefix state (D-12/13). |
| HALT/STOP interaction | “CPU not running” as one predicate is simple but conflates three different clock states. | Test manual HALT, STOP and speed pause separately; real IRQ guest path (D-14). |
| Fixture breadth | External-only misses partition/safety; original-only loses independent guest protocols; entire upstream suites widen scope and rights. | Four SameSuite VRAM cases plus newly admitted Magen HDMA and original guests (D-16/17/19). |
| SameSuite small asset rights | Treating the root license as sufficient is the established G7 basis; demanding new permission absent contrary evidence adds toil. | Record X11 author-work basis and CC0 include, verify closure during admission (D-16). |
| Mealybug | Required vendoring would breach the existing unresolved font gate; removing the cases loses useful CGB-C comparison. | Optional authorized local bytes, digest pin, informative CGB-C only, honest not-run otherwise (D-18). |
| Oracle class | All-green/digest is easy but can hide the wrong cause and overstate independence. | Structural guest predicate first, digests for regression, targeted mutants with matching controls (D-17/19/20). |
| CI placement | Another hosted matrix gives visibility but duplicates existing lanes and sanitizer cost; local-only behavior tests lose recurring protection. | Register recurring checks in existing lanes; one-off discussion/closure checks stay local (D-21/22). |
| Workflow continuation | Auto plan/execute would save a command but violate the owner's stage/phase stop. | Record `/gsd-plan-phase 13`, keep both auto flags false, stop (D-25). |

## Research record and reconciliation

Three independent background investigations completed: hardware contract advisor, code-seam explorer, fixture/evidence advisor. The hardware advisor then completed one targeted adversarial follow-up. No agent changed production code or admitted fixture bytes. Parent read the two SameSuite test sequences and SameBoy's cancellation code to reconcile the source conflict rather than voting by researcher count.

Primary revisions inspected: Pan Docs `0191af06ac49661587dcde3d57a241a626b8df75`; SameBoy `26a56bd6a122a6318a456abd80558408742d5adf`; SameSuite `f15645fb049a47ea235f6d2c9a033e72d8087901`; MagenTests `3f9c090f16e5a721db776febb9ba7d773e1c819c`; Mealybug `70e88fb90b59d19dfbb9c3ac36c64105202bb1f4`. Immutable primary links and actual local admission files are collected in CONTEXT canonical refs.

Material corrections made during synthesis:

- Old milestone prose about readable live counters is superseded by explicit CPU write-only policy/internal cursor separation. Write-only alone does not establish a hardware read byte.
- SameSuite's two precise start/cancel sequences are adopted as software-model behavior despite the Pan Docs prose conflict. The initial conservative advisor preference to leave the whole conflict unresolved was replaced after inspecting actual operations and the matching SameBoy branch; its final adversarial response found no coherence problem with qualified adoption.
- Magen's HDMA ROM is not already vendored. Milestone “Admit” text is a recommendation; the six-ROM manifest and ELIGIBILITY are the actual current state. Its oracle is SameBoy-assisted, not CGB-E hardware evidence.
- The nominal block duration does not prove startup cost or an exact CPU steal point. Whole-instruction preflight/no resume is a material constraint, not an implementation detail to handwave away.
- The existing Phase 12 HDMA expected-failure test does not span an active transfer across the speed pause. Replace that shallow deferred-write pin with actual new coverage when the behavior lands.
- SameSuite scope is four VRAM DMA ROMs; the milestone shorthand “dma/* (6)” includes unrelated cases. G7's repository-license basis is distinct from Mealybug's unresolved G1 font.

The remaining research gates are narrow and assigned: steal boundary/preflight reservation, startup/cadence sensitivity, the full active-register transition table, LCD disable/re-enable, invalid sources and overflow status, bank sampling/crossings, and HALT/STOP/speed/OAM collision order. No routine owner choice is pending. Further fan-out stops here because more generic role lenses add no new observable contract or discriminator.

## Agent discretion

Internal names, economical helper placement and mutant grouping, original guest layout and plan granularity are delegated. A contradictory primary source or failed mechanism prototype can amend a decision with a narrow recorded explanation. This discussion is not `13-RESEARCH.md`, planning, execution, conformance evidence or a physical hardware result.

## Verification receipt

The phase-local `verify-discussion-contract.py --self-test` checks the context structure/decision IDs, canonical local paths, pinned source references, pending requirement, absence of prematurely created research/plans, consistent planning route and disabled auto-advance. Its negative controls deliberately weaken these records. This is a local discussion/handoff check; existing CTest/CI will verify implemented DMA during execution. No emulator suite, new fixture rebuild, hosted run or hardware experiment is claimed by this discussion.

The installed runtime's session update recomputed progress as 7/9 after the empty Phase 13 directory was created, while the active ROADMAP has only six completed v0.2 phases and Phase 13 has zero plans. Corrected only the progress metadata through the runtime frontmatter handler to 6/9 (67%), preserving the completed discussion and pending implementation. The local check compares this count to ROADMAP and rejects a false count. No runtime installation or global config was changed.

Fresh local receipt: `python3 -I .planning/phases/GB-13-cgb-hdma/verify-discussion-contract.py --self-test` returned `discussion-contract pass decisions=25 local_refs=46 negative_controls=10 next=/gsd-plan-phase-13`; `git diff --check` returned exit 0. OpenGSD `init.phase-op 13` detects complete context, no research, zero plans and no verification; discuss pre/post hooks are empty. The owner's existing model/runtime config changes remain outside this commit.

## Deferred ideas

Phase 14 timing/APU and broad corpus; Phase 15 game/release; v0.3 states/integration; speculative public debugging API/frameworks; G1 reopening only on new rights evidence. No outgoing message to test authors was requested or sent.
