# Phase 16: Tune-up and v0.2 Debt Closure - Research

**Researched:** 2026-10-24
**Domain:** Repo hygiene and CI/CD gating for a portable C emulator core (CMake/CTest, Python checkers, GitHub Actions, release-please). No `src/` or `include/` change.
**Confidence:** HIGH for in-repo facts (all read or run this session); MEDIUM for hosted-runner behaviour (valgrind on ubuntu-24.04, release-please regeneration), which only hosted runs can confirm.

## Summary

CONTEXT.md (D-01..D-33) already fixes the design. This research supplies the repo facts the planner needs to turn it into at most 8 plans. The main findings are corrections or sharpenings, not alternatives.

1. **Several named artifacts do not exist yet.**
   - There are no `GBB_LIVE_PHASES_DIR` or `GBB_V02_PHASES_DIR` CMake variables.
   - There is no `tests/ci/` directory.
   - `tests/cmake/` holds only the `timeout-policy` sub-project, not per-area `*.cmake` includes.
   - `tests/data/` has 3 tracked files.
   - `.github/ci-timeouts.json`, `nightly-asan.yml`, `tests/baseline/perf-gate-v1.txt` and `docs/support/v0.2.1.md` are all absent.
   - 16-01 must create the include mechanism before 16-02..05 can parallelize.
2. **`verify-workflow-policy.py` is NOT a CTest.** It runs only in the release rehearsal judge and `verify-release-gates.sh`; `tests/expected-tests.txt` has no workflow-policy entry. The self-test takes about 15 s, with `negative_controls=164`.
   - TUNE-04's timeout-ledger controls must be reachable from CTest, or "fails on negative controls" is unenforced on PRs.
   - Add CTest wrappers (`--check`, `--self-test`), or put the ledger logic in a new `tests/scripts/` checker that the policy script also calls.
3. **The CTest set that reads `.planning/phases` is small and fully enumerated** (see Archive Facts): 3 lines in `tests/CMakeLists.txt` plus 7 scripts. The archive move is mechanical. The risk is vacuous passes on an empty or missing directory (D-08 minimums).
4. **The Phase 8 verifiers already pass locally** (`rejected_controls=157`, and the player self-test passes). `96d5eec` is not an ancestor of `main` and exists only on `gsd/phase-08-cartridge-seam-mbc5-and-mbc2` (verified with `git merge-base --is-ancestor` and `git branch -a --contains`). The D-12 tag is a hard prerequisite for any CTest that runs them in CI.
5. **The D-20 timeout rule forces YAML timeout increases in `ci.yml`.** With p50 over the last 5 green main runs and the 2x rule:
   - native-linux needs at least 31 min (timeout is 30);
   - Windows needs at least 46 (timeout is 30);
   - macOS needs at least 38 (timeout is 30);
   - ASan-acceptance needs at least 51 (timeout is 45), so it must be sharded first (D-19).
   See Pitfall 4.
6. **Release path state (read-only `gh`).** PR #75 is OPEN and MERGEABLE, titled `chore(main): release 0.2.1`, with an empty `statusCheckRollup`. Branch protection requires exactly `required-native`, `fixture-repro` and `preview-package-smoke` (strict). The latest 4 main CI runs are green. `nightly-asan.yml` does not exist (404). Release jobs run as a reusable workflow under the `release-please` workflow, not as `release.yml` runs.

**Primary recommendation:** Follow CONTEXT D-02's 7-plan partition in order. Make 16-01 land the shared scaffolding: archive, `GBB_LIVE_PHASES_DIR` / `GBB_V02_PHASES_DIR`, a `tests/cmake/` include hook, the lint and the D-12 tag. Put every new CTest in a per-area include. Require every new checker to ship a negative control and a minimum-count anti-vacuity guard.

<user_constraints>
## User Constraints (from 16-CONTEXT.md)

The full locked text is `16-CONTEXT.md` lines 28-264 (decisions D-01..D-33). It is binding and must be read alongside this file. Headline decisions, verbatim titles:

### Locked Decisions
- **D-01: Release last.** Every `tests/`, `cmake/`, `.github/` and docs change lands on main before the v0.2.1 window opens (D-31).
- **D-02: Partition. Cap 8; target 7 plans, keeping one slot for the single gap round. The planner may merge plans but not exceed the cap.** Plans 16-01..16-07 as listed in CONTEXT; order 16-01 → 16-02 → 16-03 → 16-04 → 16-05 → 16-06 → 16-07 (D-02a).
- **D-03: No `feat:` titles before the v0.2.1 tag.** Use `fix`, `perf`, `test`, `ci`, `docs`, `chore` or `build`.
- **D-04: No `src/` or `include/` change in Phase 16.** If any TUNE item needs `src/`, stop and escalate to the owner.
- **D-05: Archive.** `git mv` exactly the 10 directories GB-07 … GB-15.1 (578 tracked files) to `.planning/milestones/v0.2-phases/`; leave GB-16; move `.planning/verify-v02-milestone-audit.py` beside the v0.2 audits.
- **D-06: Lint `tests/scripts/verify-no-phase-paths.py` plus a CTest** (count-pinned allowlist, anti-vacuity floor, controls per spelling).
- **D-07 (owner: disclosed interpretation):** live reads of the current milestone go through the one allowlisted `GBB_LIVE_PHASES_DIR`. Do not edit REQUIREMENTS.md or D-105. Remove the Python default `--phases-dir .planning/phases`.
- **D-08: Retargeting v0.2 readers** through `GBB_V02_PHASES_DIR`; every directory-sweeping test gets a minimum count.
- **D-09: HDMA helpers** extracted to `tests/scripts/verify-hdma-lane.py`; retire `phase13-handoff-continuity.test.cjs`.
- **D-10: Broken 15.1-VALIDATION rows** (34-1, 34-2, 35-2, 35-3, 36-1, 36-2, 36-3).
- **D-11: Wire six CTests through `expect_exit.cmake`** for the two Phase 8 verifiers (pass, `--self-test`, wrong `--boundary`).
- **D-12: Pin the boundary** with annotated tag `historical/phase-08-boundary` on `96d5eec`.
- **D-13 (owner decision): accept with attribution. No performance fix in Phase 16.** New seed RM-023.
- **D-14 / D-15 / D-16 / D-17:** Ir gate (cachegrind), limit 1.10, guards, canned-output CTest, hosted `perf-gate` job, attribution receipt via a hosted `workflow_dispatch`.
- **D-18 / D-19 / D-20 / D-21 / D-22 / D-23:** static `TIMEOUT` ratchet, ASan sharding with bounded PR replay and `nightly-asan.yml`, `.github/ci-timeouts.json`, planning-only classifier feeding `required-native`, planning-label lint, temp hygiene.
- **D-24..D-27:** plan-cap check, LESSONS id renumber and check, STATE.md bound, Playstead docs.
- **D-28..D-33:** v0.2.1 ledger and version binding, two-digest freeze of the v0.2.0 ledger (D-29 owner decision), paired-gate performance qualification via the D-101 path, release window, PRs #78-92 closure, disposition record.

### Claude's Discretion
Exact script names, the per-area CMake fragment layout, allowlist file formats, the measured lint floor and the STATE bound, all within the rules above. Whether to merge plans further below 7.

### Deferred Ideas (OUT OF SCOPE)
- RM-023 perf recovery (empty-queue input early-out, Phase 7 mixer cost).
- A PPU-heavy, cleanly licensed perf workload and a longer workload id.
- Planning-only classification for `fixture-repro` and `preview`.
- Folding the three required contexts into one aggregator.
- A title lint for `feat` before patch releases.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TUNE-01 | No test or CTest entry reads from `.planning/phases` (read per D-07). | Archive Facts: exact reader list, `GBB_LIVE_PHASES_DIR` design, 404-file lint floor, move atomicity. |
| TUNE-02 | Phase 8 verifiers run in CTest, each rejecting a seeded defect. | Phase 8 Facts: both verifiers' CLIs, boundary non-ancestry, `--boundary` addition, `expect_exit.cmake` min-key pattern. |
| TUNE-03 | Cumulative DMG perf gate plus attribution receipt. | Perf Facts: `measure_core` CLI, tag SHAs, commit sets, valgrind not local. |
| TUNE-04 | CI budget gates with negative controls. | CI Facts: job timeouts and p50s, `required-native`, policy reader limits, ASan test structure. |
| TUNE-05 | Planning hygiene checks. | Hygiene Facts: LESSONS duplicate ids, STATE.md size, Playstead stale lines, ROADMAP cap lines. |
| TUNE-06 | Ledger freeze, v0.2.1 publication, PR closures, dispositions. | Release Facts: ledger digests, hard-coded `0.2.0` sites, PR #75 state, protections. |
</phase_requirements>

## Project Constraints (from AGENTS.md; no CLAUDE.md exists)

- **Stop after the phase.** Never auto-advance. `workflow.auto_advance` and `workflow._auto_chain_active` stay false (verified in `.planning/config.json`).
- **Verification is automated and shifted left (D-069).**
  - Every deliverable gets an automated check with a negative control.
  - Plan SUMMARY `coverage:` entries use the GSD block schema: `id`, `description`, `human_judgment`, block-style `verification` items with `kind` of unit/integration/e2e/automated_ui/other, `ref`, `status: pass`. No `{...}` flow items, no `ctest` kind, no inline `#` comments. The `summary_coverage` CTest rejects violations.
  - Use `tests/scripts/verify-uat-closure.py <phase-dir> --write <evidence> | --self-test`; never hand-write UAT.md.
  - Boundary checks read point-in-time facts from the boundary commit, never live HEAD ancestry or routes.
- **Phase limits (D-102..D-105):** at most 12 plans per phase; at most 2 review-fix rounds and 1 gap round; an unresolved correctness or security finding forces a rescope. No quotas, clocks or run counters as evidence. Checkers live in `tests/scripts/`, read an immutable commit, and are wired into CTest when created.
- **Git.**
  - Use phase branches and PRs; do not bypass branch protection.
  - Never treat a skipped, stale or local pass as proof of a remote green.
  - Squash-merge phase PRs when exact-head CI is green (memory: pre-authorized).
  - Privacy-safe Git author. No personal paths, emails or secrets in public artifacts.
  - `.planning/config.json` has uncommitted owner edits: stage by path, never sweep it into a phase PR.
- **Engineering.**
  - No Nintendo boot ROMs, commercial images or unlicensed fixtures. Every third-party fixture needs a redistribution record and a digest.
  - Benchmarks must record revision, build, hardware, workload, model, output digest, warm-up, samples and uncertainty.
  - Prefer copying small code over adding dependencies (memory); flat dependency tree; no third-party actions (D-096).
- **Complete means evidence.** Re-inspect current verification evidence; an earlier agent's completion claim is insufficient.

## Architectural Responsibility Map

This phase is repo and CI tooling, not an application, so the tiers are repo layers.

| Capability | Primary tier | Secondary | Rationale |
|------------|--------------|-----------|-----------|
| Phase-path lint, planning hygiene checks | `tests/scripts/*.py` checkers | `tests/cmake/*.cmake` registration | Checkers are pure Python and CTest-labelled `planning`, so a planning-only PR can run them without a build. |
| Phase 8 historical verifiers | `tests/scripts/` | git tag `historical/phase-08-boundary` | They read an immutable commit via `git show`; the tag is the only durable input. |
| Perf Ir gate and attribution receipt | Hosted workflow job (valgrind) | Valgrind-free CTest on canned data | Valgrind is Linux-only and absent locally; CTest validates parser, arithmetic and receipt shape everywhere. |
| Per-test budget ratchet | CTest (`--show-only=json-v1`) checker | `tests/ci/test-budget-allowlist` | Deterministic static check, no wall clock (D-102). |
| Timeout ledger | `.github/ci-timeouts.json` | `verify-workflow-policy.py` plus a CTest wrapper | Policy script already owns `timeout-minutes` arithmetic; it is not currently in CTest. |
| Planning-only classifier | `ci.yml` `changes` job | `required-native` aggregator | Branch protection names stay unchanged. |
| Release publication | release-please PR #75 + `release.yml` reusable workflow | rehearsal and trusted judge | Judge runs main-branch code against tagged data. |

## Standard Stack

No external packages are installed by this phase; this is Python stdlib, CMake, bash and GitHub Actions.

### Core
| Tool | Version in use | Purpose | Evidence |
|------|----------------|---------|----------|
| CMake / CTest | floor 3.25 (CMakePresets `cmakeMinimumRequired` 3.25.0); local 4.4.3 | Test registration, `--show-only=json-v1` | [VERIFIED: CMakePresets.json:3, `cmake --version`] |
| Python 3, `-I` isolated, stdlib only | local 3.14.4 | All checkers | [VERIFIED: `python3 --version`] |
| `tests/expect_exit.cmake` | n/a | Exact exit code, regex, `GBB_FORBID_REGEX`, `GBB_EXPECT_MIN_KEY`/`VALUE` | [VERIFIED: tests/expect_exit.cmake:1-60] |
| Valgrind cachegrind (`--cache-sim=no`) | apt on pinned `ubuntu-24.04` | Ir proxy | [ASSUMED] hosted version not checked; D-14 requires recording gcc and valgrind versions |
| `gh` CLI | present at `/opt/homebrew/bin/gh` | Read-only release and run facts | [VERIFIED: `which gh`] |

### Supporting
| Tool | Purpose | When |
|------|---------|------|
| `tests/scripts/measure-release-baseline.sh --ab` | Existing paired wall-clock A/B on the frozen workload (30 samples, 3 warmups). | v0.2.1 paired gate (D-30). |
| `tests/scripts/verify-v02-performance.py` | Receipt-bound `accepted-with-disclosed-regression` path (`verify_reviewed_disposition`, ~line 141). | D-30. |
| `.github/scripts/verify-workflow-policy.py` | Restricted-YAML workflow judge, 164 negative controls. | D-20, D-21, D-19. |

### Alternatives Considered
None. CONTEXT fixed every choice; do not re-open them. Do not add `pyyaml` or any YAML library, because the policy script's own reader is intentionally restricted (Pitfall 2).

**Installation:** no new packages. Valgrind installs in the hosted job only: `sudo apt-get install -y valgrind`, retried once inline (D-14).

## Package Legitimacy Audit

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| valgrind | Ubuntu apt (not npm, PyPI or crates) | Not applicable to `gsd-tools package-legitimacy` (apt) | Approved: distro package, installed in a hosted job only. Version `[ASSUMED]` until the first hosted run records it. |

**Packages removed due to SLOP verdict:** none. **Packages flagged SUS:** none. No npm, PyPI or crates package is introduced, so the package-legitimacy seam was not run.

## Architecture Patterns

### System Architecture Diagram

```
 PR / push ──► ci.yml  changes (classifier; base commit's copy decides)
                  │ kind=planning ──► planning-checks (configure; ctest -L planning)
                  │ kind=full     ──► native-linux/macos/windows, ASan tests,
                  │                    ASan acceptance (sharded), cmake-floor,
                  │                    perf-gate (Ir vs v0.2.0), macos-player-package
                  ▼
            required-native (if: always(); needs.*.result aggregator)
                  │  full:     all heavy jobs == success
                  │  planning: changes + planning-checks success, heavy jobs == skipped
                  ▼
            branch protection: required-native, fixture-repro, preview-package-smoke

 schedule / workflow_dispatch ──► nightly-asan.yml (full stall replay)
        red ─► inline gh issue step opens/comments one `nightly-red` issue

 workflow_dispatch (2 merges: workflow first, artifact PR later)
        ──► perf attribution job ──► artifact ──► committed JSON receipt
                                       └► valgrind-free CTest recomputes deltas

 v0.2.1 window (D-31):  freeze main ─► #75 regenerates ─► edit #75 body ─►
        push version-bound commits as user ─► rehearsal/v0.2.1 (rehearsal + judge
        + dispatched nightly-asan green) ─► squash #75 ─► tree-equality check ─►
        release.yml publish ─► readback ─► planning-only disposition flip
        (= Phase 16 verification boundary, D-103)
```

### Recommended Project Structure
```
tests/
├── CMakeLists.txt            # one new include() line near the end (16-01 owns it)
├── cmake/                    # NEW per-area includes: archive.cmake, phase8.cmake, perf.cmake,
│   │                         #   cibudget.cmake, hygiene.cmake, release.cmake
│   └── timeout-policy/       # EXISTING sub-project; do not touch
├── ci/test-budget-allowlist  # NEW (D-18)
├── baseline/perf-gate-v1.txt # NEW (D-14)
├── data/                     # NEW canned cachegrind/timing outputs, 14-UAT-REVIEW seed, short stall case
└── scripts/                  # new checkers (verify-no-phase-paths.py, verify-hdma-lane.py, ...)
.github/ci-timeouts.json      # NEW (D-20)
.github/workflows/nightly-asan.yml  # NEW (D-19)
docs/support/v0.2.1.md        # created only in the D-31 window, on the #75 branch
```
`include()` runs in the same directory scope, so tests registered there are seen by `gabbaboy_verify_registered_tests()` (`get_property(DIRECTORY PROPERTY TESTS)`), provided the include precedes that call. Every added test is also a line in `tests/expected-tests.txt`; the call fails configure on any mismatch. [VERIFIED: cmake/ExpectedTests.cmake:1-30]

### Pattern 1: Negative-control CTest via `expect_exit.cmake`
**What:** wrap a Python checker, assert the exact exit code, a regex on combined output, and a parsed minimum. **When:** every new checker (rejecting variant plus accepting twin plus minimum).
```cmake
# Source: tests/CMakeLists.txt, gbb_add_summary_coverage_test and uat_closure_controls (read this session)
add_test(NAME expect_exit_min_count_rejects_lower
  COMMAND ${CMAKE_COMMAND} -DGBB_CMD=${CMAKE_COMMAND}$<SEMICOLON>-E$<SEMICOLON>echo$<SEMICOLON>controls=19
    -DGBB_EXPECT_CODE=0 -DGBB_EXPECT_REGEX=controls
    -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=20
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
```
The helper requires exactly one `KEY=<digits>` in the output, so a checker must print its count exactly once.

### Pattern 2: Immutable-boundary reads
Both Phase 8 verifiers use `git show <BOUNDARY>:<path>`, so they need full history and the tag. CI checkouts use `fetch-depth: 0`. The `planning-checks` job must also use `fetch-depth: 0`, and the rehearsal/native jobs must have the new tag fetched (a normal `actions/checkout` with depth 0 fetches tags).

### Anti-Patterns to Avoid
- **Live HEAD reads for historical checks.** Repoint to the archive or a boundary commit, never `.planning/phases`.
- **Vacuous sweeps.** `summary_coverage` passes on an empty directory today. Every sweep needs a minimum (D-08).
- **Editing archived content.** The 15.1 records digest-pin it (D-05).
- **`feat:` titles** (D-03).
- **Adding a CTest in only one of CMake or `expected-tests.txt`.**

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---------|-------------|-------------|-----|
| Exit-code/regex/minimum assertions | New wrapper scripts | `tests/expect_exit.cmake` | Already handles min-key, forbid-regex, file freshness. |
| Per-test timeout inventory | Grep of CMake text | `ctest --show-only=json-v1` | A static grep finds about 40 literal values over 60 but misses computed ones (D-18). Precedent: `verify-cgb-apu-dispositions.py:153`. |
| Workflow YAML parsing | A new YAML parser | `read_workflow()` in `verify-workflow-policy.py` | The trusted judge must parse the subject as data with no third-party code. |
| UAT closure files | Hand-written UAT.md | `verify-uat-closure.py --write` | AGENTS.md rule. |
| First-parent commit selection in the receipt test | Re-implementing selection | `git rev-list --first-parent` | D-17 requires equality with it. |
| Ir measurement | Wall-time proxy | cachegrind `Ir` | Deterministic; wall time is noise-limited (D-102). |
| Release notes/versions | Hand edits in CHANGELOG | #75 body edit (D-31) | release-please regenerates CHANGELOG; any main push wipes hand edits. |

**Key insight:** this repo has a mature pattern: checker script, self-test with named mutants, CTest wrapper with a regex and a minimum. Copy it; do not invent a new harness.

## Archive Facts (TUNE-01, D-05..D-10)

**Tracked files per directory** (`git ls-files .planning/phases`): GB-07 45, GB-08 35, GB-09 48, GB-10 55, GB-11 45, GB-12 58, GB-13 51, GB-14 70, GB-15 38, GB-15.1 133, GB-16 2. The ten v0.2 directories total 578. [VERIFIED: git ls-files, this session]

**Everything outside `.planning/` that mentions `.planning/phases`** (full grep of tracked text):
| File:line | What it does |
|-----------|--------------|
| `tests/CMakeLists.txt:1208` | `GBB_HDMA_CLOSURE_CHECKER` path to `GB-13-cgb-hdma/verify-hdma-closure.py` |
| `tests/CMakeLists.txt:2670` | `--phases-dir "${PROJECT_SOURCE_DIR}/.planning/phases"` for summary coverage |
| `tests/CMakeLists.txt:2687` | `GBB_UAT_CLOSURE_PHASE` = the GB-15 dir |
| `tests/scripts/verify-summary-coverage.py:300` | `default=".planning/phases"` |
| `tests/scripts/verify-closeout-dispositions.py:37,64` | `PHASE_REL` (15.1) and `published_receipt` (GB-15 delivery receipt) |
| `tests/scripts/verify-closeout-scan.py:31,66,155,161,168,378,402` | GB-14 UAT-REVIEW, plus temp-fixture layout strings (`:155,:402`) |
| `tests/scripts/verify-historical-limitations.py:39,99,673` | `PHASE_DIR` (15.1), glob `GB-12-*/12-REVIEW-FOLLOWUP.md`, a literal in a self-test |
| `tests/scripts/test-cgb-red-evidence-privacy.py:12` | GB-14 phase dir |
| `tests/scripts/test_hdma_remote_evidence.py:13` | `CHECKER_PATH` to GB-13 |
| `tests/scripts/phase13-handoff-continuity.test.cjs:7,12` | Orphaned; D-09 retires it |
| `tests/scripts/verify-phase8-closure-contract.py:15` | `PHASE` constant (used inside boundary reads) |
| `docs/mbc1-evidence.md:64-93` | Links into `.planning/milestones/v0.1-phases/...` (the allowed archive spelling); the lint must accept it, which makes it a ready-made positive control. |

`tests/scripts/verify-dense-input.py:103` only skips a `.planning` directory name; it is not a phase-path read.
`.planning/verify-v02-milestone-audit.py:38-53` reads `.planning/phases` by `git ls-tree` at a revision, so it is inside `.planning/` and out of lint scope.

**Anti-vacuity numbers.** 404 tracked, non-empty text files exist outside `.planning/` (`git ls-files | grep -v '^\.planning/' | xargs grep -Il .`), matching CONTEXT. Total tracked files are 1424. `summary_coverage` today prints `files=143 entries=546` (CONTEXT). Re-measure after the move.

**Live (current-milestone) reads.** After the move only GB-16 remains under `.planning/phases`. `GBB_LIVE_PHASES_DIR` is the single allowlisted spelling. Consumers: the summary-coverage live sweep and the D-24 plan-cap check.

**15.1 `summary_coverage --since 9`** currently sweeps live phases 9..15.1. After the move the v0.2 part must read the archive via `GBB_V02_PHASES_DIR` with a minimum file count, and the live part reads GB-16 (empty until plans are summarized, so the floor must be conditional or the live sweep must tolerate zero).

**HDMA lane extraction (D-09).** `verify-hdma-closure.py` defines `lane_contract` (line 80), `lane_self_test` (150), `validate_remote_evidence` (701) and `load_remote_evidence` (679). Its modes include `--lane`, `--lane-self-test`, `--prohibitions`, `--self-test`, `--handoff`. Existing CTests `cgb_hdma_lane_contract`, `cgb_hdma_lane_contract_selftest` and `cgb_hdma_remote_evidence_selftest` (tests/CMakeLists.txt about 1213-1230) must keep their names. `test_hdma_remote_evidence.py` loads the checker by path with `importlib`, so its `CHECKER_PATH` becomes `tests/scripts/verify-hdma-lane.py`.

## Phase 8 Facts (TUNE-02, D-11, D-12)

- Both verifiers hard-code `BOUNDARY = 96d5eec977bee99a0629499b89c737415e24184c`.
  - Closure also uses `OLD = '5673bed'` (`:77`) for `'old:'+path` reads, so `5673bed` (Phase 7 merge, an ancestor of main) must stay reachable. The `--boundary` argument must not break the `OLD` reads.
  - Closure CLI has only `--self-test`; player CLI has `--self-test`. Neither has `--boundary` yet. [VERIFIED: closure :121-126; player :140]
- Verified outputs today:
  - Closure plain run: `phase8-closure-contract PASS boundary=96d5... files=65 rejected_controls=0` (the plain run prints `=0`; the `--self-test` run prints `=157`).
  - Player: `phase8-player-contract: PASS boundary=... startup=replacement=stderr=copy=save-guard`, and `phase8-player-contract self-test: PASS controls=warning-removed,pinned-copy-changed,branch-removed,status-call-removed,stderr-call-removed`.
- Wrong-boundary expectations (D-11): closure expects `missing historical clause`; player expects `phase8-player-contract: FAIL`. Confirm both strings against real output when implementing: a wrong-boundary closure run that cannot read a file prints `cannot read ...` first, which is a different failure class. Use a boundary that exists but is the wrong commit (e.g. `v0.2.0`, as D-11 states) so the failure is a clause miss, not a read error.
- `96d5eec` is a commit object locally, is not an ancestor of main, and is contained only by `gsd/phase-08-cartridge-seam-mbc5-and-mbc2` (local and `origin/`). [VERIFIED: git]
- **D-12 tag creation is a push to the remote** (a mutating action, performed during execution, not research). It must precede any branch cleanup and precede the first CI run of the new CTests, or CI fails closed with the unreadable-tag error. Plan it as the first action of the plan that wires TUNE-02.
- Tag ordering hazard: CI jobs check out with `fetch-depth: 0`, which fetches tags. `cmake-floor` and sanitizer jobs must also have full history, or these tests fail there. `verify-cmake-floor.sh` and the ASan shards use `fetch-depth: 0` in `cmake-floor`; confirm the other jobs when wiring.

## Perf Facts (TUNE-03, D-13..D-17)

- `tests/measure_core.c` (151 lines). CLI `measure_core (--trace|--no-trace) <rom>` or `--no-trace --profile cgb <rom>`. It prints one line with `workload=original-wram-tracer-1m-half-dots-v1 ... consumed_half_dots=... correctness_digest_fnv1a64=...` and exits non-zero when anything is off. ROM size cap is 32768 bytes (`MAX_ROM_BYTES`). [VERIFIED: tests/measure_core.c:19-20, 95-150]
  - The digest comes from WRAM `0xC000-0xDFFF` and HRAM `0xFF80-0xFFFE` after the run.
  - Consequence: libbet (32768 B) fits; confirm the visible-demo ROM is at most 32768 bytes before relying on it.
  - The pinned tracer digest `4c7a57ff3d50d228` also appears in `measure-release-baseline.sh --ab` (`expected_digest`) and in the Phase 8 closure contract.
- `measure-release-baseline.sh` modes are `--self-test`, `--ab <base> <head>`, `--qualify-v02 --output <json> [--review-regression <note>]` (783 lines). `--ab` honours test hooks only when `GBB_AB_TEST_HOOKS=1`. The D-14 gate is a new script; do not stretch this one.
- **Tags:** `v0.2.0` and `v0.2.0^{commit}` both resolve to `ab301aa69b1f085050fd66bf7b1378863a0821f2` (lightweight tag); `v0.1.0^{commit}` is `e30d168f7fc61de8db0a3801e7b1736362912cb7`. [VERIFIED: git rev-parse]
- **Commit sets for D-17** (first-parent, verified):
  - `v0.1.0..v0.2.0` has 58 first-parent commits, of which **14 touch `src/` or `include/`**.
    - Phase merges and feature commits: #63 `5673bed` (Phase 7), #64 `30230b2` (Phase 8), #65 `d7e2e0a`, #66 `3012e8f`, #67 `70c441b`, #68 `8091fb5`, #69 `261c660`, #71 `c771b1b`, #72 `04fe3c6`.
    - Others: #35 `96f76de`, #40 `8c80d59`, #43 `bce8564`, #45 `2463a38`, #54 `ab76d09`.
  - `v0.2.0..main` has 14 first-parent commits; exactly 3 touch `src/` or `include/`: `79e20f3`, `2d25a47`, `09805f3`. `git diff --stat v0.2.0 main -- src include` shows 5 files changed (401 insertions, 117 deletions) and none under `include/`.
  - The receipt's commit-selection rule must be stated explicitly. D-17 says "every first-parent merge", but the 58-commit set is mostly docs, which cannot change Ir. Recommend measuring the 14 `src/include`-touching commits plus `v0.1.0`, `v0.2.0`, `HEAD`, with the selector rule recorded in the receipt and re-derived by the CTest (`git rev-list --first-parent <range> -- src include`). Confirm with the owner only if D-17 is read literally; it costs about 17 hosted builds either way. (Open Question 2, RESOLVED: all 20 `--first-parent --merges` commits plus the 14 `src`/`include` commits; see there.)
- **Valgrind is not installed locally** (`which valgrind` empty; macOS). Real Ir work is hosted-only or Linux-container-only. The valgrind-free canned-output CTest (D-15) is the only locally runnable part: design the parser and arithmetic first, then the hosted job.
- Plan to record Ir numerics from CONTEXT only as expectations: 1.081-1.083 head/v0.2.0 today, limit 1.10. The mutation patch of about 12 Ir per half-dot inside `advance_devices_to` adds about 12M Ir (about +5%) on top of 1.083, which just crosses 1.10. That margin is thin; compute it from the first hosted run and size the patch from it, not from this note.

## CI Facts (TUNE-04, D-18..D-23)

**Workflows** (`.github/workflows`): `ci.yml` (435 lines), `fixture-repro.yml`, `libbet-repro.yml`, `preview.yml`, `release-please.yml`, `release.yml` (reusable, 1554 lines), `release-rehearsal.yml`. [VERIFIED: ls]

**ci.yml triggers:** `pull_request` types opened/synchronize/reopened, and `push` with no branch filter (so push-to-main and every branch push). Top-level `permissions: contents: read`.

**`timeout-minutes` and measured p50** (last 5 green main runs, via `gh run view`; script in scratchpad):
| Job | timeout | p50 (min) | 2x p50 | OK today? |
|-----|---------|-----------|--------|-----------|
| native-linux-x64 | 30 | 15.1 (range 10.3-22.1) | 31 | NO |
| native-macos-arm64 | 30 | 18.9 | 38 | NO |
| native-windows-x64 | 30 | 22.9 | 46 | NO |
| linux-asan-ubsan (fuzz) | 45 | 2.8 | 6 | yes |
| linux-asan-ubsan-tests | 45 | 17.9 | 36 | yes |
| linux-asan-ubsan-acceptance | 45 | 25.4 (range 11.5-26.3) | 51 | NO |
| cmake-floor-3.25.3 | 40 | 16.9 | 34 | yes |
| player-gate / required-native | 2 / 5 | 0.1 | 1 | yes |
| macos-player-package | 45 | n/a on main (PR only) | | needs PR-run citation |

`fixture-repro.yml` jobs: timeouts 15/30/30/30/30/20/45 against p50 0.1-0.4 min, all fine. The `rtc3test-repro` job is the 45-minute one. `preview.yml` jobs: 55/55/60/5. Preview runs only on `pull_request` (the latest 6 runs are all PR events), so its citations must be PR runs and therefore `provisional` under D-20 unless a main run exists. `release.yml` jobs (10, 35, 60, 35, 60, 112, 45, 15, 25, 20 min) run as a reusable workflow under `release-please`, not as `release.yml` runs, so data comes from `release-please` workflow runs. `release-rehearsal.yml` jobs: 60/45/45/35/75/15; the last three rehearsals (runs 40043165875, 39866157056, 39645769068) all concluded `failure`, so they cannot supply green samples for a p50. Inventory the real job count (about 40) before sizing 16-04.

**D-20 consequence:** the ledger forces edits to `timeout-minutes` in `ci.yml` (native-linux to at least 31, macOS to 40, Windows to 50, as CONTEXT says). It also forces the ASan-acceptance shard (the job is at 25.4 of 45 today, over the 50% line). D-20 states the ASan acceptance rows come only from post-shard runs, so 16-03 and 16-04 ordering is load-bearing: take the cited run after sharding lands on main.

**`required-native`** is an inline `if: always()` aggregator over `needs.*.result`. [VERIFIED: ci.yml:395-435]
- `needs`: native-linux, native-macos, native-windows, linux-sanitizers, linux-sanitizers-tests, linux-sanitizers-acceptance, cmake-floor-3-25-3, player-gate, macos-player-package.
- A loop requires each of the first 8 to be exactly `success`. `check-player-result.sh` handles the player pair.
- `verify-workflow-policy.py` pins `CI_REQUIRED_NATIVE_NEEDS` (set equality, line 1251), the `if: always()` text, the per-job `env` mapping for 5 variables, and exact required `run` commands (`CI_REQUIRED`, `CI_SANITIZER_SHARDS`, lines 1225-1242). Any change to the `needs` list or the ASan `ctest` command lines must update these constants in the same plan. Serialized-hotspot rule D-02a applies.

**Restricted workflow YAML reader (critical).** [VERIFIED: verify-workflow-policy.py:44-172]
- It rejects tabs and CR, flow maps `{`, anchors `&`, aliases `*`, tags `!`, `<<`, and nested flow collections. Flow lists `[a, b]` are allowed only without nested brackets or braces.
- Keys must match `^[A-Za-z0-9_][A-Za-z0-9_.-]*:`.
- Any `uses:` must be `owner/repo@<40-hex>` or `./`.
- Every new workflow or job must be written in this subset or the judge rejects the whole tree (`workflow-unsupported-yaml`).
- A job `if:` is normalized by `_normalise_if` (line 1183).
- `ci` forbids any write permission in any job (`producer-write-authority`, `check_ci`). The `changes` and `planning-checks` jobs must stay read-only.
- `WORKFLOWS` (line ~1607) lists the six workflow files copied into the self-test fixture, and `READONLY_WORKFLOWS` (line 1343) is `("ci.yml","fixture-repro.yml","preview.yml")`. A new `nightly-asan.yml` needs a decision on where it is judged: its `issues: write` job conflicts with the read-only rule, so use the `CREDENTIAL_EXEMPT`-style pattern or a dedicated check. It also needs adding to `WORKFLOWS` or the self-test fixture will not contain it.

**Sanitizer tests.**
- `cmake/ScaleSanitizerTimeouts.cmake` multiplies every registered test's TIMEOUT by 3 when `GABBABOY_ENABLE_SANITIZERS`. It is called once after the final registration, and TIMEOUT is directory-scoped at the 3.25 floor. New tests in included fragments are covered as long as the include precedes the call at the end of `tests/CMakeLists.txt`.
- `tests/CMakeLists.txt` near line 4662 asserts exact scaled values for 6 named tests, such as `age_stall_window=720`, in sanitizer builds. Renaming or resharding those silently breaks that block, so keep them.
- `acceptance_stall_diagnosis` (`tests/acceptance/CMakeLists.txt:536-545`): `verify-stall-report.py` runs the runner twice on case `libbet` with `--mutate drop:START --failure-dir`, with `--runner-timeout 300` (1800 s under sanitizers). TIMEOUT is 1200 and COST 1200. The libbet case budget is `budget_half_dots=505612800`.
- **A bounded replay needs no `src/` change.** Case budgets are data: `cases.txt` lines carry `budget_half_dots`, and `libbet-no-input` / `libbet-select` already use 168537600 with `model_fail=... expect_fail_reason=predicate-not-reached`. A short-budget `drop:START` case in a separate cases file under `tests/data` (not `tests/acceptance/cases.txt`, which other tests count) exercises the same stall report cheaply. Check the case file and pin digests first: the ROM is pinned by `rom_sha256`/`rom_size`.
- `v02_consumer_controls` (TIMEOUT 900) calls `verify-v02-consumers.py --self-test`, whose CLI has only `--run`/`--self-test` today. Splitting per consumer means adding a selector argument there (no existing per-consumer mode).

**Existing CI-shape CTests that will break if the YAML changes:** `ci_asan_parallel_contract` and `ci_asan_parallel_serial_selftest` (scope `name: linux-asan-ubsan-tests`, phrase `ctest --preset phase1-asan --parallel 4`) and `ci_floor_parallel_contract` / `ci_floor_parallel_serial_selftest` (`CTEST_PARALLEL_LEVEL: 4`, scope `name: cmake-floor-3.25.3`) read `ci.yml` text. `verify-cgb-corpus-inventory.py:716` also encodes the two ASan shards. Resharding the acceptance job must update these in the same commit. `tests/CMakeLists.txt` re-configures on `ci.yml` change (`CMAKE_CONFIGURE_DEPENDS`).

**Per-test budget (D-18).** 40 `TIMEOUT` values over 60 s in `tests/CMakeLists.txt`, `tests/acceptance/CMakeLists.txt` and `tests/player/CMakeLists.txt` (static grep; the ratchet must use json-v1, which also reflects computed values). Seeds include `acceptance_stall_diagnosis` 1200, `v02_consumer_controls` 900 and `cgb_samesuite_apu_suite` 600. The ratchet's "against the base commit" rule needs `git show <base>:tests/ci/test-budget-allowlist`. At PR time the base is the merge base; on push-to-main, the parent.

**Planning-only classifier (D-21).**
- Nothing like it exists in `ci.yml`. The aggregator currently treats a `skipped` heavy job as a failure, so the `kind=planning` branch is a deliberate loosening. The workflow-policy mutations for `required-native` must be updated and extended (new controls: a `src/` or `tests/` file offered to the classifier; success-criterion 3).
- The classifier script should live under `.github/scripts/` or `tests/scripts/` as pure Python so a CTest can feed it name-status fixtures and assert `kind`. Policy: only `.planning/**` and `AGENTS.md`.
- `ctest -L planning` needs a configured tree but no build: all `planning`-labelled tests must run with no target (D-22).
- The D-22 lint must know which tests read `.planning/` or `AGENTS.md`. Today that set is the phase-path scripts above, `verify-historical-limitations`, `verify-closeout-*`, summary coverage, UAT closure, the red-evidence privacy test and the HDMA lane tests. Some read `.planning/` only indirectly through a Python script, so the lint must resolve the script file (use json-v1 `command` arguments and scan referenced scripts), not just grep CMake.

**Temp hygiene (D-23).** `check_sanitizer_timeout_policy.cmake` creates `${GBB_BINARY_DIR}/sanitizer-timeout-policy-<8 hex>` on every run and never removes it (lines 5-8). It must clean on success, keep on failure and sweep stale siblings at start.

## Hygiene Facts (TUNE-05, D-24..D-27)

- **ROADMAP cap lines** [VERIFIED: ROADMAP.md:76,89,102,115]: `**Plan cap**: 8`, `12`, `10`, `8` for Phases 16-19 (sum 38). Line 57 states the budget as 8 + 12 + 10 + 8. The checker can parse the real tree and the limits hold (each at most 12, sum at most 40).
- **LESSONS duplicate ids** [VERIFIED: grep this session]: `GB-FIXTURE-001` at lines 75, 225, 846; `GB-TEST-001` at lines 162, 234. The ids `GB-FIXTURE-002` (line 854), `GB-TEST-002` (279) and `GB-TEST-006` (837) exist; `GB-FIXTURE-003`, `GB-FIXTURE-004` and `GB-TEST-007` are free. The renumbering in D-25 is therefore collision-free: 225 becomes `GB-FIXTURE-003`, 846 becomes `GB-FIXTURE-004`, 234 becomes `GB-TEST-007`.
  - Line 294 says `existing lesson GB-TEST-001` inside a lesson sourced from `tests/player/...` and `verify-phase3-player.sh`, so it plausibly means the macOS-preference lesson being renumbered to `GB-TEST-007` (D-25 says fix this inbound reference). Read the lesson body at plan time to confirm.
  - Line 46 (XFER-016) mentions the duplicates. Leave history with a note.
  - **No test reads LESSONS.md at HEAD.** `verify-phase8-closure-contract.py` reads LESSONS only at the immutable boundary (`GB-CART-001..006`). So renumbering cannot break CTest. The checker must find ids with the exact `### <ID> /` heading format.
- **STATE.md.** 639 lines, 76,810 bytes (`wc`), matching CONTEXT. Sections by line: Current Position 31, historical blocks 44-139, Performance Metrics 140, Decisions 339-585, Pending Todos 586, Blockers 590, Session Continuity 629, Operator Next Steps 637. Nothing in `tests/` reads STATE.md at HEAD (only the Phase 8 closure verifier at the boundary, and the retired `phase13-handoff-continuity.test.cjs`). `verify-closeout-dispositions.py:522` mentions `.planning/STATE.md` only as a mutated string. So the trim carries no test risk, but GSD runtime writes the frontmatter and Current Position. Keep those byte-compatible (the file head, lines 1-43, shows `gsd_state_version`, `progress:` block and `state_head`). Read `.planning/STATE.md` growth per phase from `git log -p` before fixing the bound (D-26).
- **Playstead stale statements** [VERIFIED: grep]:
  - `README.md:46-47` says "GBA/mGBA through an external process" (line 47).
  - `docs/native-integration.md:278-281` pins `a102d6082968bc09ca00fefbf5c552ecf979fd63` and says "uses an external process for GBA/mGBA".
  - `.planning/research/PRECEDENT.md:24` (table row `1de3e95`, 2026-09-28) and `:98-104` (`blocked-capability`, P-08).
  - Authority: `PLAYSTEAD-CONTRACT.md` §5 (line 84; row 88) says "GBA+GB+GBC through mGBA 0.10.5, on Playstead main `234bd45b21` (Phase 4.6)". The remote-main line cites `234bd45b21` (2026-10-15).
  - Hits are also in `.planning/research/v0.3/*` (contract and sibling research). Those are historical research and outside the check's scope; confine the new docs check to README, `docs/native-integration.md` and PRECEDENT.
  - **Required sentences (must survive):** `verify-v02-adoption.py:143` requires "Playstead remains a future integration" in README, and `:152` requires "it is not a live GabbaBoy/Playstead integration" in `docs/native-integration.md`. D-27's rewrite must keep both verbatim or update the verifier in the same commit. Lines 140 and 198-225 also pin `v0.2.0` ledger link text.
  - The README sentence at line 46 sits in a paragraph about a different topic (the ledger link and publication claim); change only the Playstead sentence.

## Release Facts (TUNE-06, D-28..D-33)

- **PR #75** [VERIFIED: `gh pr view 75`]: state OPEN, mergeable MERGEABLE, base `main`, head `release-please--branches--main--components--GabbaBoy`, title `chore(main): release 0.2.1`, `statusCheckRollup` empty. Its body lists three `fix` entries: #97, #94 and #74. Note it does not list #93; verify what the final regenerated body contains after the Phase 16 merges, since `perf`/`test`/`ci`/`docs`/`chore` do not alter the version.
- **release-please config:** `release-type: simple`, `draft: true`, `force-tag-creation: true`, `include-v-in-tag: true`, `exclude-paths: [.github/workflows, .github/scripts]`, `extra-files: [CMakeLists.txt]`, manifest `".": "0.2.0"`. [VERIFIED: release-please-config.json]. `exclude-paths` means commits that touch only workflow/script paths are excluded from the release PR. This partially insulates the CI plans, but mixed commits still count.
- **Branch protection** (`gh api`): `required_status_checks` strict true; contexts `required-native`, `fixture-repro`, `preview-package-smoke`. [VERIFIED]
- **Open PRs now:** #75 and #78-92, 16 in total. #78-92 are docs/test PRs per their titles (e.g. "#78 test(15): complete Phase 15 automated UAT", "#92 docs(phase-12): refresh metadata..."). CONTEXT D-32 states none touches `src/` or `include/`; spot-check with `gh pr diff --name-only` before closing (read-only).
- **Ledger digests** [VERIFIED: shasum this session]: `git show v0.2.0:docs/support/v0.2.0.md | shasum -a 256` gives `a542a5c01e236246f83d4f1b67aba20f2a9200e74e5ffe70b930daf9f3af2b8f`; the working file gives `c47ff12b089fd386ebe1dd1a16d4ceaefc9fd60d072acdce510267c3dff19a9e`. Both match D-29. `docs/support/` holds `unreleased.md`, `v0.1.0.md`, `v0.2.0.md`.
- **Hard-coded `0.2.0` sites to parameterize in 16-06:**
  - `verify-support-ledger.py`: lines 378, 827, 872-874, 961-963, 1108-1111, 1125-1141, 1239-1240, 1437, 1469-1502, 1633-1707, 1755-1766 (`select_ledger` self-test already encodes `("v0.2.1", "v0.2.0.md")` at :1757, which flips to `v0.2.1.md` once that ledger exists), 1823-1824, 1896-1899, 2013-2046. About 84 occurrences across the three scripts.
  - `verify-v02-adoption.py:41` (`LEDGER`), `:45` (`RELEASE_VERSION = "0.2.0"`), `:140,198,220,225` (ledger link text), `:552`, `:666-691`, `:817`, `:935`.
  - `release-rehearsal.yml:23` (`REHEARSAL_TAG: v0.2.0`; also used at :42, :156, :212).
  - `tests/CMakeLists.txt:1405` (regex `version=0.2.0`) and the neighbouring `v02_support_ledger` contract.
- `select_ledger` already implements "newest ledger with the same major.minor and version ≤ tag" and names the exact-0.2.0 failure. [VERIFIED: verify-support-ledger.py:64-84]. The D-28 binding rule (newest ledger ≤ CMake/manifest version) is a small extension of it.
- **`--check-current` is receipt-bound** (`--receipt build/cgb-corpus-receipt.json`; it errors "requires --receipt PATH" otherwise). It runs only in `release-rehearsal.yml` (lines 66, 223) and `release.yml:1032`, never in CTest. The CTest-visible static form is `--check-ledger` (`v02_support_ledger`). Success criterion 5's "passes `--check-current`" is therefore a hosted fact at the rehearsal head, not a local CTest.
- **Rehearsal** triggers on `push` to `rehearsal/**`, `contents: read` only, and its `judge` job `needs` corpus, fuzz, performance, package and aggregate. All three recorded rehearsals failed. The `v0.2.0` ledger is still read through `REHEARSAL_TAG`.
- **Wall-clock gate (D-30).** `verify_reviewed_disposition` (`verify-v02-performance.py:141-175`) requires `schema_version` 1, an `https` `review_reference`, `review_type == "independent"`, `decision == "accepted-with-disclosed-regression"`, and bindings to `measurement_receipt_sha256`, `source_pair` and `workload`. "Independent" is a schema string, but the review itself is a human or owner judgment; per AGENTS.md the owner already decided D-13, so cite that decision as the reviewer identity, and have the plan state who the reviewer is explicitly. (Open Question 3)
- **Tree-equality check (D-31 step 6):** `git rev-parse <squash-sha>^{tree}` against the rehearsed head's tree. Squash merges rewrite the commit but keep the tree if the base is unchanged, which strict protection plus the freeze guarantees.

## Common Pitfalls

### Pitfall 1: Vacuous pass after the move
**What goes wrong:** `summary_coverage` and other sweeps print `pass` on an empty directory. **Why:** no minimum. **Avoid:** D-08 minimum counts via `--min-files` / `GBB_EXPECT_MIN_KEY`, plus a control that points the sweep at an empty directory and must fail. **Signs:** `files=0`.

### Pitfall 2: Restricted YAML reader rejects the new workflow
**What goes wrong:** the trusted judge exits `workflow-unsupported-yaml` for `{ }`, anchors, tabs, multi-document or nested flow lists. **Avoid:** write only block mappings and sequences, simple scalars and `|` blocks; run `python3 -I .github/scripts/verify-workflow-policy.py --check` locally (about 0.1 s) after every workflow edit, and `--self-test` (about 15 s) after editing the script.

### Pitfall 3: Ledger pins invalidate on any later CTest addition
**What goes wrong:** the support ledger pins `tests/CMakeLists.txt`, `tests/expected-tests.txt` and verifier scripts (D-01). A CTest added after the v0.2.1 ledger is generated breaks `--check-current`. **Avoid:** release last; generate `v0.2.1.md` from the #75 head tree in the D-31 window.

### Pitfall 4: Timeout rule vs current YAML
**What goes wrong:** the ledger rejects the tree on day one because native-linux, macOS, Windows and ASan-acceptance fail the 2x rule (table above). **Avoid:** in the same plan edit the YAML timeouts, ledger and policy script, and never cite a pre-shard run for ASan acceptance. A `provisional` row at the release head fails, so re-cite from main before the window.

### Pitfall 5: A main push in the release window wipes the #75 edits
**What goes wrong:** release-please regenerates #75 on every main push. **Avoid:** D-31's freeze; push the version-bound commits under a user identity, because `GITHUB_TOKEN` pushes start no `pull_request` workflows (GitHub docs, cited in CONTEXT).

### Pitfall 6: A `feat:` title turns #75 into 0.3.0
**Avoid:** D-03 vocabulary; fallback `Release-As: 0.2.1` footer.

### Pitfall 7: Stall-replay bounding creeping into `src/`
**Avoid:** use a data-only short-budget case (see CI Facts). Escalate if impossible (D-04).

### Pitfall 8: Tag-dependent tests in a shallow checkout
**What goes wrong:** Phase 8 verifiers and the freeze test need `historical/phase-08-boundary` and `v0.2.0`; a shallow or tagless checkout fails them. **Avoid:** `fetch-depth: 0` in every job that runs the full suite, including `planning-checks`.

### Pitfall 9: Dispatch-only workflows can't run before they reach main
**What goes wrong:** `workflow_dispatch` workflows must exist on the default branch to be dispatched (the nightly workflow's 404 shows this). **Avoid:** two-merge flow of D-02a; the receipt PR comes after the workflow PR. A dispatched job never pushes to protected main.

### Pitfall 10: Planning-labelled test that needs a build
**What goes wrong:** `ctest -L planning` in the `planning-checks` job runs on an unbuilt tree and fails with "executable not found". **Avoid:** the D-22 lint plus a control; use `--no-tests=error` so an empty label set fails.

## Code Examples

### Boundary-pinned read with a fail-closed tag (target shape for D-12)
```python
# Source: pattern from tests/scripts/verify-phase8-player-contract.py:27-36 (read this session), extended
BOUNDARY_TAG = "historical/phase-08-boundary"
def read_boundary(rev: str, path: str) -> str:
    result = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"could not read {path} at {rev}: {result.stderr.strip()}")
    return result.stdout
```
Resolve the tag with `git rev-parse --verify <tag>^{commit}` and fail if it is unreadable; do not fall back to the literal SHA when the tag is missing in CI, or the fail-closed contract is lost.

### Count-pinned allowlist idea for the lint (D-06)
```python
# (file, max_hits, reason); a row whose observed hits are below max is stale and fails
ALLOW = (("tests/CMakeLists.txt", 1, "GBB_LIVE_PHASES_DIR definition"),)
```

### Reading the ctest inventory (D-18)
`ctest --test-dir build --show-only=json-v1` emits `tests[].properties[]` with `name == "TIMEOUT"`. The existing parser in `verify-cgb-corpus-report.py:520` and `verify-cgb-apu-dispositions.py:153` is the precedent. Do not extend the CGB-specific GB-CI-007 parser (D-18); write a small neutral reader.

## State of the Art

| Old approach | Current approach | Impact |
|--------------|------------------|--------|
| Wall-clock perf compare (v0.2.0 shipped at +14.86% via disclosed review) | Deterministic cachegrind Ir plus a coarse realtime floor | Gate cannot flake; blind spots must be named (PPU, sprite, DMA, banking barely exercised; about 87% of Ir in `advance_devices_to`). |
| Whole-run ASan acceptance replays on every PR | Bounded PR replay plus a nightly full replay | Closes LIM-ASAN-STALL-TIMING; release binding goes through a dispatched `nightly-asan` run. |
| Completed-milestone phases left in `.planning/phases` | `.planning/milestones/vX.Y-phases/` (the v0.1 layout) | Lint can forbid `.planning/phases` reads outside the allowlist. |

## Runtime State Inventory (archive/rename work)

| Category | Items found | Action |
|----------|-------------|--------|
| Stored data | None: the repo keeps no database keyed on the phase path. Verified by grepping tracked text. | None |
| Live service config | GitHub branch protection names three contexts, which Phase 16 deliberately leaves unchanged (`gh api` read). | None |
| OS-registered state | None identified. | None |
| Secrets and env vars | None reference phase paths. `.gitignore` mentions `.planning`-adjacent ignores only. | None |
| Build artifacts | `build/`, `build-asan/` etc. are gitignored and may hold CMake caches with the old `PROJECT_SOURCE_DIR/.planning/phases/...` paths in generated test lists. `__pycache__` exists in `.planning/`, `tests/` and `.github/scripts/`. | Reconfigure after the move; do not rely on cached `build/`. |
| Tracked planning pointers | `.planning/HANDOFF.json:6` (`phase_dir` GB-15.1), `.planning/PROJECT.md:14,174`, `.planning/MILESTONES.md:34`, `.planning/STATE.md:633` (live GB-16 pointer, stays), `.planning/context/LESSONS.md:707,905,907`, `.planning/context/DECISIONS.md:113` (quote of D-105, historical, keep). `.planning/research/INDEX.md` has no hit. | Repoint only live navigation (HANDOFF, PROJECT, MILESTONES); leave dated lessons and decisions. |

The move is a code edit plus a data move (git rename), with no data migration. Every `uat_closure_*`, summary and disposition CTest changes its input path and needs a green run before and after the `git mv` in the same commit.

## Environment Availability

| Dependency | Required by | Available locally | Version | Fallback |
|------------|-------------|-------------------|---------|----------|
| cmake / ctest | all CTests | yes | 4.4.3 (floor 3.25 is a hosted job) | none needed |
| python3 | checkers | yes | 3.14.4 | none |
| ninja | presets | yes | present | none |
| gh | read-only release facts | yes (authenticated for this session) | present | none |
| node | `phase13-handoff-continuity.test.cjs` (retired) | yes | via asdf | none |
| valgrind | D-14, D-17 | **no** (macOS) | | hosted `ubuntu-24.04` job; local work uses canned outputs in `tests/data/` |
| Docker / Linux box | local Ir probes | not checked | | hosted-only |

**Missing with no local fallback:** valgrind (hosted job only, and the hosted result is the authority per CONTEXT). Planning must not require a local valgrind run for any acceptance check.

## Assumptions Log

| # | Claim | Section | Risk if wrong |
|---|-------|---------|---------------|
| A1 | Valgrind installs via apt on `ubuntu-24.04` within one retry, and cachegrind `--cache-sim=no` Ir is deterministic across hosted runs. | Perf Facts | The gate's `proxy-nondeterministic` guard fires; fall back to D-14's recorded failure mode. |
| A2 | The visible-demo ROM is at most 32768 bytes and loads in `measure_core`. | Perf Facts | The third workload ROM needs a different harness or an exclusion; check at plan time. |
| A3 | (Retired by Open Question 2: the receipt measures all 20 first-parent merges literally plus the 14 `src`/`include` commits for attribution, 39 revisions in total.) | Perf Facts | none |
| A4 | Preview and release workflow jobs have too few main-branch samples to cite non-provisionally. | CI Facts | If not, rows need no `provisional` flag. |
| A5 | LESSONS.md:294 refers to the macOS-preference lesson (line 234), so it should become `GB-TEST-007`. | Hygiene Facts | If it means the HRAM lesson (line 162), it stays `GB-TEST-001`. |
| A6 | (Retired: all four v0.3 phases carry `**Plan cap**` lines, 8/12/10/8 = 38, verified at ROADMAP.md:76,89,102,115.) | Hygiene Facts | none |

## Open Questions (RESOLVED)

1. **Phase-path links in `docs/mbc1-evidence.md`.**
   RESOLVED: the file only links to `.planning/milestones/v0.1-phases/`, which the lint allows. No allowlist row is needed.
2. **Commit set for the attribution receipt** (A3).
   RESOLVED: 16-02 honors D-17 literally and adds a resolution set. The receipt measures 39 revisions:
   - v0.1.0;
   - `merge_set`, which equals exactly `git rev-list --first-parent --merges v0.1.0..v0.2.0` (20 merge commits; only `261c660` changes `src/` or `include/`);
   - `resolution_set`, which equals exactly `git rev-list --first-parent v0.1.0..v0.2.0 -- src include` (14 commits);
   - v0.2.0;
   - `post_v020_set`, which equals exactly `git rev-list --first-parent v0.2.0..<head> -- src` (3 commits);
   - HEAD.

   The union of merge_set and resolution_set has 33 commits, measured 2026-10-24. The checker re-derives each set with its own command, recomputes every delta and every `affects_binary` flag, and rejects any mismatch.

   The resolution set is needed because the phase PRs, including Phase 7 `5673bed`, landed as squash commits, not git merges. Measuring only the 20 merges would lump Phases 7-12 into one delta, and success criterion 2 ("assigns the v0.2 slowdown to phase merges") could not be met. The earlier 17-commit Ir-path selection and the 14-commit-only recommendation are both superseded.

   `tests/measure_core.c` does not exist at v0.1.0. The receipt-head harness is therefore overlaid on each revision's `src/` and `include/`, and the receipt records the harness SHA-256.
3. **Reviewer identity for the D-30 `independent` review type.**
   RESOLVED: the owner is the reviewer.
   - In 16-07 Task 1, Claude opens one GitHub review issue with a drafted decision, but only if the paired trigger fires.
   - The owner approves by commenting (checkpoint Task 2). That comment URL is the `https` `review_reference`, and the owner's handle is `reviewer_identity`.
   - D-13 is cited in the rationale. Claude never fills or approves the decision on the owner's behalf.
4. **Where `nightly-asan.yml` is judged by `verify-workflow-policy.py`.**
   RESOLVED: 16-03 adds `nightly-asan.yml` to `WORKFLOWS` (not `READONLY_WORKFLOWS`) and a dedicated `check_nightly()`.
   - It pins the schedule and workflow_dispatch triggers.
   - It requires a read-only `asan-full-replay` job and a separate `report-red` job, which holds `issues: write` only, runs no checkout, and carries no `timeout-minutes`.
   - Four mutations are rejected.
5. **ROADMAP cap lines.**
   RESOLVED: ROADMAP.md has cap lines at 76, 89, 102 and 115 (8, 12, 10, 8; sum 38, within the 40 limit). The checker can parse the real tree.
6. **Timeout-ledger scope breadth.**
   RESOLVED: 16-04 seeds every row from a real completed job, with a documented `samples` count that may be 1. A row is `provisional` only when it cites an unmerged PR or a non-main probe ref. Real runs are scheduled for every new job:
   - `perf-gate` and `changes` cite main pushes.
   - `perf-attribution` and `nightly-asan` cite their main-ref dispatches.
   - The rehearsal `perf-gate` cites a `rehearsal/ledger-probe-16-04` push at the main head.
   - Existing rehearsal jobs, including the judge, cite green v0.2.0-era rehearsals such as run 39401388702.
   - Preview jobs cite merged PR runs.
   - `planning-checks` first cites a stacked probe PR (provisional). Then 16-04 delivers its SUMMARY as a genuinely planning-only PR B, whose main push runs `planning-checks`.
   - `report-red` runs only on failure and is out of scope.

   16-06 re-cites every provisional row from main runs, including planning-checks from the PR B push. `--check --release-head` then passes before the D-31 window.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest (CMake floor 3.25, hosted native Linux/macOS/Windows plus ASan lane) with Python 3 stdlib checkers |
| Config file | `CMakePresets.json` (`phase1`, `phase1-asan`, `cmake-3.25.3`); registrations in `tests/CMakeLists.txt` and, new, `tests/cmake/*.cmake` |
| Quick run command | `ctest --preset phase1 -L planning --no-tests=error` (after the label exists), or `ctest --preset phase1 -R '^<new_test_prefix>' --no-tests=error` |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` (the `workflow.test_command` in config) |
| Workflow policy | `python3 -I .github/scripts/verify-workflow-policy.py --check` and `--self-test` (about 0.1 s and about 15 s); to be wrapped as CTests |

### Phase Requirements → Test Map
| Req | Behavior | Test type | Automated command | Negative control | Exists? |
|-----|----------|-----------|-------------------|------------------|---------|
| TUNE-01 | No tracked text outside `.planning/` names `.planning/phases` except allowlisted spellings; floor of scanned files. | unit/lint | `ctest -R '^no_phase_paths'` running `verify-no-phase-paths.py` | Seeded fixture per spelling (literal, joined segments, backslash, `${PROJECT_SOURCE_DIR}`) and per scope root rejects; clean `milestones/v0.2-phases` passes; stale zero-hit allowlist row fails | Wave 0 |
| TUNE-01 | Retargeted v0.2 readers pass from the archive with minimum counts. | integration | existing `summary_coverage`, `closeout_dispositions_*`, `historical_limitations_*`, `cgb_red_evidence_privacy*`, `uat_closure_*` | Point one at an empty dir (must fail on `--min-files` / `GBB_EXPECT_MIN_KEY`); embedded-path file missing fails | partly exists |
| TUNE-02 | Both Phase 8 verifiers pass, self-test, reject a wrong boundary. | integration | 6 CTests (`phase8_closure_*`, `phase8_player_*`) via `expect_exit.cmake` | `--boundary v0.2.0` expecting `missing historical clause` / `phase8-player-contract: FAIL`; self-test `GBB_EXPECT_MIN_KEY=rejected_controls` value 157 | Wave 0 |
| TUNE-03 | Perf gate parser, Ir arithmetic, schema, realtime floor on canned data. | unit | `ctest -R '^perf_gate'` (valgrind-free) | Canned over-limit Ir fails `ir-budget-exceeded`; canned multiple under floor fails; changed digest `workload-digest-mismatch`; nondeterministic/vacuous canned inputs fail | Wave 0 |
| TUNE-03 | Hosted gate rejects a seeded regression. | hosted integration | `perf-gate` job scratch-tree patch (about 12 Ir/half-dot) | Patch must fail with digest equal; no-op twin passes; missing anchor fails loudly; missing valgrind fails | Wave 0, hosted |
| TUNE-03 | Attribution receipt consistent. | unit | `ctest -R '^perf_attribution'` | Dropped commit, altered raw row, altered delta each rejected; digests constant | Wave 0 |
| TUNE-04 | Per-test TIMEOUT ratchet over json-v1. | unit/integration | `ctest -R '^test_budget'` | Over-budget fixture fails; ceiling raised vs base fails; expired allowlist row fails | Wave 0 |
| TUNE-04 | Timeout ledger rules. | unit | CTest wrapping `verify-workflow-policy.py` ledger check | Edited timeout, missing row, p50 over 50%, stale value, new job without row, `provisional` at release head | Wave 0 |
| TUNE-04 | Bounded ASan stall replay. | integration | sharded `acceptance_stall_diagnosis_*` (single replay each) | Lane definition control: PR lane without the bounded case or with the full replay fails | Wave 0 |
| TUNE-04 | Planning-only classifier. | unit | CTest feeding name-status fixtures | `src/` or `tests/` file, rename out of `src/`, `..`, symlink, empty diff, tag all classify `full` | Wave 0 |
| TUNE-04 | Planning-label lint. | unit | CTest | Unlabelled fixture test reading `.planning/` fails | Wave 0 |
| TUNE-05 | Plan-cap check. | unit | `ctest -R '^plan_cap'` | Over-cap fixture fails; missing cap line fails; cap above 12 fails | Wave 0 |
| TUNE-05 | LESSONS unique ids. | unit | `ctest -R '^lessons_unique'` | Fixture with duplicate `### ID` fails | Wave 0 |
| TUNE-05 | STATE size bound. | unit | `ctest -R '^state_size'` | Oversized fixture (not the live file) fails | Wave 0 |
| TUNE-05 | Playstead docs. | unit | `ctest -R '^playstead_docs'` | Fixture with `a102d608`, "GBA/mGBA", `1de3e95` blocked-capability each fails; required `verify-v02-adoption.py` sentences remain | Wave 0 |
| TUNE-06 | v0.2.0 ledger freeze. | unit | `ctest -R '^ledger_freeze'` | Flipped byte, wrong pin, extra edit outside the appended block each fail; missing tag fails in CI | Wave 0 |
| TUNE-06 | Version-agnostic ledger/adoption checks. | integration | existing `v02_support_ledger*`, `v02_adoption_docs*` (regex made version-agnostic) | Selection test for v0.2.1 binding to `v0.2.1.md`; wrong-version fixture rejected | partly exists |
| TUNE-06 | Release-note needles. | unit | `verify-v02-adoption.py --release-notes` self-test | Notes without the +8.3% disclosure rejected | Wave 0 |
| TUNE-06 | Disposition record. | unit | CTest on the new v0.3 disposition record | `pending-release` row accepted before tag, closure without tag-bound digests rejected | Wave 0 |
| TUNE-06 | Publication facts. | boundary (point-in-time) | Post-release commit checker reading that commit: release published, readback reconciled, PRs closed, dispositions | Receipt digests tampered; closure without readback fails | Wave 0 (16-07) |

### Sampling Rate
- **Per task commit:** the targeted `-R` regex for the area touched, plus `python3 -I .github/scripts/verify-workflow-policy.py --check` after any workflow edit.
- **Per wave merge:** full `ctest --preset phase1` and `--self-test` of every checker added or changed.
- **Phase gate:** full suite green at the exact head, hosted `required-native`, `fixture-repro` and `preview-package-smoke` green, rehearsal and judge green at the release head, then `verify-uat-closure.py` for zero human checkpoints. The verification boundary is the post-release disposition commit (D-103).

### Wave 0 Gaps
- [ ] `tests/cmake/` per-area include mechanism and its one-line `include()` before `gabbaboy_verify_registered_tests()` (owned by 16-01).
- [ ] The checkers and fixtures named above (`verify-no-phase-paths.py`, `verify-hdma-lane.py`, perf parser and receipt checker, test-budget checker, classifier, plan-cap, LESSONS, STATE, Playstead, ledger freeze, disposition record), each with a CTest and its `expected-tests.txt` line.
- [ ] `tests/data/` canned cachegrind and timing outputs; a copy of the 2.4 KB `14-UAT-REVIEW.md` seed for `verify-closeout-scan.py`.
- [ ] `ci-timeouts.json`, `tests/ci/test-budget-allowlist`, `tests/baseline/perf-gate-v1.txt`.
- [ ] CTest wrappers for `verify-workflow-policy.py --check` and `--self-test`, since neither is in CTest today.
- [ ] No framework install needed.

## Security Domain

`security_enforcement` is not disabled in `.planning/config.json` (`security_enforcement: true`, ASVS level 1, `security_block_on: high`). This phase builds no network service, so ASVS applicability is limited to supply chain and CI trust.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard control |
|---------------|---------|------------------|
| V2 Authentication | no | n/a |
| V3 Session Management | no | n/a |
| V4 Access Control | yes (CI authority) | Job-scoped permissions, `contents: read` default, `issues: write` only on the nightly job, enforced by `verify-workflow-policy.py`; no `pull_request_target` (D-21) |
| V5 Input Validation | yes | Checker inputs (git paths, name-status lists, JSON receipts) validated with bounded size, `..`/symlink/case rejection; classifier fails closed to `full` |
| V6 Cryptography | yes (integrity only) | SHA-256 pins for ledger blobs and fixtures via stdlib `hashlib`; never hand-roll |
| V14 Config / Supply chain | yes | Actions pinned to 40-hex SHAs (`_check_actions`), no third-party actions (D-096), valgrind from the distro, retry inline |

### Known Threat Patterns
| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Planning-only classifier bypass: a `src/` change smuggled as planning (rename out of `src/`, `..`, case variant, symlink, submodule) | Elevation/Tampering | `--name-status --no-renames`, fail-closed to full, base commit's classifier decides, allowlist only `.planning/**` and `AGENTS.md` |
| Workflow edit by the PR author changes the judge | Tampering | Trusted judge runs main-branch code against the subject as data (existing); keep classifier logic out of PR-controlled paths where possible |
| Nightly `issues: write` token abuse | Elevation | Job-scoped only; no checkout of untrusted code in that job; `workflow_dispatch --ref` binds to a rehearsal head by tree equality |
| Tag/branch deletion orphaning verifier input | Denial | D-12 annotated tag first; verifiers fail closed |
| Secrets/paths in artifacts (receipt, rehearsal evidence) | Information disclosure | Existing privacy verifiers (`verify_privacy` in `verify-v02-performance.py`); receipt names hardware class only, no host/user names |
| `GITHUB_TOKEN` push silently skips CI | Repudiation | User-identity push for version-bound commits (D-31 step 4) |

## Sources

### Primary (HIGH confidence): in-repo, read or run this session
- `.planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-CONTEXT.md` (all decisions)
- `tests/CMakeLists.txt` (lines 1195-1230, 1380-1414, 2385-2440, 2655-2760, 4615-4687)
- `tests/expect_exit.cmake`, `cmake/ExpectedTests.cmake`, `cmake/ScaleSanitizerTimeouts.cmake`, `tests/check_sanitizer_timeout_policy.cmake`
- `tests/scripts/verify-phase8-closure-contract.py`, `verify-phase8-player-contract.py` (read and executed `--self-test`: pass)
- `tests/scripts/verify-support-ledger.py`, `verify-v02-adoption.py`, `verify-v02-performance.py`, `measure-release-baseline.sh`, `tests/measure_core.c`, `tests/scripts/verify-stall-report.py`
- `.github/workflows/ci.yml`, `release-rehearsal.yml`, `fixture-repro.yml`, `preview.yml`, `release.yml`; `.github/scripts/verify-workflow-policy.py` (read; `--check` and `--self-test` executed: pass, 164 negative controls)
- `release-please-config.json`, `.release-please-manifest.json`, `CMakePresets.json`, `.planning/config.json`
- `.planning/context/LESSONS.md`, `.planning/STATE.md`, `.planning/research/v0.3/PLAYSTEAD-CONTRACT.md`, `README.md`, `docs/native-integration.md`, `.planning/research/PRECEDENT.md`
- Git: `rev-parse`, `rev-list --first-parent`, `merge-base --is-ancestor`, `ls-files`, `branch --contains`, `diff --stat`, `shasum`
- Read-only `gh`: `pr view 75`, `pr list`, `api .../branches/main/protection`, `run list`, `run view` (job durations), `release list`

### Secondary / Tertiary
- None. No external documentation was fetched: every question was answerable from the repository, and the CONTEXT external references (release-please, valgrind manual, GitHub docs) were not re-fetched, so statements about them rest on CONTEXT and are `[ASSUMED]` until the hosted runs confirm them.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH (nothing new is introduced)
- Architecture and file inventory: HIGH (read, grepped and executed in repo)
- CI timing numbers: MEDIUM (5 recent green main runs; small sample, one machine class)
- Hosted valgrind and release-please behaviour: MEDIUM/LOW until the hosted receipts exist

**Research date:** 2026-10-24
**Valid until:** about 7 days for CI timing and PR state (main moves fast and release-please regenerates #75); repo-structure facts stay valid until the first Phase 16 merge.

**Provenance note:** no `[CITED]` tags are used. In-repo values are `[VERIFIED]` by reading or running in this session and quoted inline where they matter (digests, ids, commit SHAs, line numbers).
