# Phase 23 execution contract

The eight plans implement REL-01 within the nine-plan cap; one slot remains unused. Execution order is 23-01 → 02 → 03 → 04 → 07 → 05 → 06 → 08: the existing state-version dependency is resolved by 07 before the release content window. Plan 23-06 owns downloaded-release reconciliation and automated release-evidence closure; Plan 23-08 owns milestone lessons, bookkeeping and final completed-summary closure/handoff. Do not execute superseded Phase 22 plans, refresh Phase 20–22 boundary qualification, or fetch/build/run/admit a real game or diagnostic fixture. Actual CGB candidate and diagnostic inputs remain read-only. Both auto-advance flags stay false.

Every task's runnable check is followed by its observable failure condition. Commands run only during execution. Reconfigure when a source revision changes because CMake-generated tests embed immutable source IDs. Full final implementation qualification belongs to Plan 23-04; H/R1/W/R2 and actual downloaded-release qualification are separate required existing boundaries. Do not rerun earlier phases as new release evidence.

Existing source paths named in the plans were checked with `git ls-files`. The intentionally new source file is `tests/data/support-claims-v0.4.json`; the new generated public output is `docs/support/v0.4.0.md`. New Phase 23 planning/review/evidence artifacts are intentionally new. Build-directory previews, API snapshots and downloaded artifacts are transient outputs, never ignored runtime mirrors used as source authority. No dependency install, new release mechanism, application API or database schema is planned.

The leading plan is a production-quality tracer: immutable candidate facts → selected profile → existing production generator → reader-visible Markdown → exact-output/negative CTest. It uses a disposable committed 0.4.0 subject while real main remains 0.3.0; the actual tracked ledger is generated only when the actual 0.4.0 version PR exists. This proves the architecture without pretending that synthetic version selection is hosted release output.

Use the installed OpenGSD phase branch, protected PR, review and commit paths. Before opening a final PR with known automatic review, finish internal review and accepted fixes; check any open-time base property immediately before opening. Merge only the reviewed/tested revision with latest required hosted checks. No skipped or stale check is green evidence. Preserve the configured supported native/compiler/CMake/player/platform matrix, sanitizers, fuzz, performance and release authority. No speculative CI scheduling change is planned; collect durations, queue/dependency waits and timeout headroom, and record a justified no-change finding when appropriate.

At most two review-fix rounds and one gap round cover the whole phase, including the generated version delta. Unresolved correctness/security findings force rescope rather than a follow-up seed. A demonstrated release-please target-version blocker can use a scoped reserve plan after evidence and plan review; RM-032 is not a default work list. Do not manufacture feature history to force a bump. Exact 0.4.0 actual output precedes freeze, rehearsal and tag. Any unsupported tag/source/asset mutation remains held for a concrete recovery decision.

The source audit preserves the unclassified REL-01 edge and two bespoke transparency prohibitions as descriptor-less, flagged-unverified fallback items. Their automated project controls are required; their workflow classification must not be silently auto-resolved or converted into fictional human UAT. Software acceptance, workflow probe classification and the one-way authority decision are distinct facts.

## SUMMARY coverage schema

Every plan summary uses this exact block shape, one entry per delivered capability. Populate real source-bound evidence and actual completed results. Use `unit`, `integration`, `e2e`, `automated_ui` or `other`; never use `ctest` as a kind, flow-style objects or inline comments.

```yaml
coverage:
  - id: RELEASE-CLAIMS
    description: "Concrete observable outcome established by the cited evidence."
    human_judgment: false
    verification:
      - kind: integration
        ref: "Actual command/result and immutable source or retained evidence reference."
        status: pass
```

The release checkpoint records authority for a one-way action, not a software deliverable requiring human judgment. Credential failures are handled only when observed. Do not invent gameplay, perception or document-reading UAT. Shared closure is generated and checked with `tests/scripts/verify-uat-closure.py`, always using `23-UAT-EVIDENCE.md` as the `--write` evidence input to generate `23-UAT.md`; never hand-write UAT. Plan 23-06 generates closure for completed release-evidence coverage without claiming Plan 23-08 is complete. Plan 23-08 first requires all eight completed summaries, then regenerates and validates/self-tests closure against that full set before final handoff. The shared tool checks existing summary coverage, so its success alone cannot prove that a missing future summary is complete. Boundary facts use their immutable boundary commits and never current-HEAD ancestry or live continuation assertions.

Phase 23 ends after qualification and closeout. The next stage is the owner-controlled v0.4 milestone audit through `/gsd-audit-milestone`; do not start it as part of these plans.
