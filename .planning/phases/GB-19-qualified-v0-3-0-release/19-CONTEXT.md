# Phase 19: Qualified v0.3.0 Release - Context

**Gathered:** 2026-10-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver REL-01: `v0.3.0` is published from its exact tag. Three things must be true:
- The exact-tag producer rehearsal ran green on the version PR before tagging. A check rejects a rehearsal that names a different revision or postdates the tag.
- A v0.3.0 support ledger scopes the save-state and host-contract claims by model, corpus and platform. Its check rejects a seeded unscoped claim.
- The consumer, package, fuzz and perf-gate receipts are bound to the tag, and the published asset readback reconciles.

Release hardening happens before the tag, not after. D-112 (v0.2.1) found three defects only after the tag, which cost three owner-waived gap rounds. This phase is designed so that discovery happens in a pre-flight, main receives exactly one pre-window push, and every new check runs before the tag.

The plan cap is 8: 7 primary plans plus one reserved gap slot. The milestone total stays within its cap at 27 + 8 = 35 ≤ 38.

**Entry blockers carried in:**
- RM-027;
- WR-C03;
- the `candidate-performance` re-citation;
- RM-031.

**Out of scope:**
- the sibling XFER scan and the FUTURE-MILESTONES refresh, the `v0.3` GSD milestone tag and the milestone audit (all belong to `/gsd-complete-milestone`);
- Windows host mode, Playstead live play (RM-020), state or RTC interop (RM-021/022), libretro;
- signing and notarisation;
- GitHub immutable releases and SLSA provenance actions;
- renaming the `v02-*` evidence;
- scrubbing personal paths from archived v0.1 plans.

**Method.** The owner directed deep multi-lens fan-out, an adversarial pass and automatic adoption at diminishing returns. Five parallel tracks ran:
- A: entry blockers and review leftovers;
- B: version-PR, rehearsal, tag and post-tag choreography;
- C: support-ledger scoping;
- D: tag-bound receipts and readback;
- G: a gap sweep, including sibling cores muhtari, cogmaster and nesturbator.

An independent adversarial review of the merged draft then found 2 blockers, 8 majors and 7 minors, verified against the code at `origin/main` `f80bdf54`. All of them are folded in below. Every decision is adopted. Revisit one only on a concrete contradiction, a failed discriminator, changed evidence or owner direction. Small direct or copied helpers are preferred over new dependencies.
</domain>

<decisions>
## Implementation Decisions

### Ordering and the single main push

- **D-01: Every hardening change lands on main as one squashed phase PR ("PR A") before the version-PR window opens.**
  - PR A carries all of 19-01..19-06.
  - Every push to main regenerates release-please PR #131 (D-112, RM-028), so PR A is the only pre-window main push.
  - No new verifier or CTest is created inside the window (D-112 amendment 1).
  - **Exception:** the two run dispatches in D-05 and D-06 happen at current main (`f80bdf54`) *before* PR A, so their re-citations ride PR A. If PR A changes the body of a cited job, disclose it in the row's `sizing_basis`.
- **D-02: Leave PR #131 alone until PR A merges.**
  - #131 (`chore(main): release 0.3.0`, head `55ac5b75`, 3 files) is reused, not closed. It regenerates once when PR A lands.
  - Merging it creates the tag at once, so it is merged only at the end of D-21's sequence.
  - It has no checks: PRs created with GITHUB_TOKEN trigger no workflows (sibling MU-REL-002). Required checks run only after a non-release-please push to its branch.
- **D-03: Release-mechanics PRs use non-releasable conventional types (`ci`, `test`, `docs`, `chore`).**
  - Every `feat`/`fix` squash title becomes a public changelog bullet.
  - A `fix:` after the tag would open a 0.3.1 PR, because `exclude-paths` covers only `.github/workflows` and `.github/scripts`.
  - `bump-minor-pre-major` is **not** added. #131 already computes 0.3.0, and the flag is a managed window input. It is deferred to v0.4.

### Entry blockers (19-01)

- **D-04: RM-027 is closed with one general citation form: a tree-equal anchor plus an optional predecessor job name. No version-expiry rule is added.**
  - **New optional row fields in `.github/ci-timeouts.json`:**
    - `tree_equal_sha`: a commit on main;
    - `cited_tree`: the cited run head's tree;
    - `cited_job_name`: the job's display name at the cited run, when it was renamed later.
  - **Offline check:** `cited_tree == tree(tree_equal_sha)` from git objects, and `tree_equal_sha` is an ancestor of main. It never resolves the cited run head.
  - **Online check:** `verify_cited` (`.github/scripts/verify-workflow-policy.py` ~2367) confirms the run's head tree through the API instead of `merge-base --is-ancestor`, which wrongly marks tree-equal rows provisional today.
  - **Rehearsal rows:** `judge`, `corpus`, `aggregate` and `performance` cite run 40257161612.
    - That run's head is `c6dc575`. Its tree `b02c14bb` equals the tree of `b93137f`, the v0.2.1 tag on main.
    - `performance` cites under its predecessor name.
    - `aggregate`'s body changed in #130: disclose it as a predecessor-body sample. The 75-minute cap still holds.
  - **Release rows:** `candidate-fuzz` and `attach-v02-evidence` cite run 40332345735 (`113b98c`, an ancestor of main) as plain citations.
    - Disclose that attach ran in retry mode and that its body moved into `release-evidence-lifecycle.sh`.
  - **Rename rule:** every row for a renamed job cites its green predecessor job with a disclosure. A red run dispatched on main is never used.
  - **Negative controls:**
    - tree mismatch;
    - anchor not on main;
    - cited job name absent from the run;
    - ceil(2 × p50) above the timeout;
    - a scratch tree with VERSION 0.3.0 must pass `--check --release-head` (exit 0);
    - a `rehearsal/vX.Y.Z` branch deleted while a row cites its head.
  - **Branch retention:** keep each `rehearsal/vX.Y.Z` branch while any row cites its head. A check enforces this.
  - **Do not edit `state_boundary.py` or `state_boundary_controls`.** They pin the Phase 16 boundary commit `d53ec9c` point-in-time (`tests/CMakeLists.txt` ~5569-5577) and are unaffected. Update only `docs/release.md` ~255-258 and the policy self-test mutants (~3601-3608).
- **D-05: `release.yml:candidate-performance` uses D-04's predecessor-name citation. There is no new `release_bound` row and no D-110 amendment.**
  - Cite the green `exact-tag-paired-performance-qualification` job of run 40332345735 as the predecessor of `exact-tag-advisory-paired-performance-observation`, with a disclosure that the old samples were a reuse path.
  - The "refuses a seventh row" rule is kept.
- **D-06: WR-C03.**
  - Before PR A, dispatch `gh workflow run nightly-asan.yml --ref main -f report_red_dry_run=true`, then re-cite `nightly-asan.yml:report-red` as non-provisional in PR A. The cited sha must be an ancestor of main.
  - No CTest parses REJECT lines. `--check --release-head` exits 1 on its first rejection, so a pending-set filter would hide later rules, and a permanent `--release-head` CTest would outlaw the provisional rows D-20 allows during development.
  - The blocker is visible through D-04's scratch-0.3.0 control, the rehearsal judge at H and at W, and D-19's pre-flight.
- **D-07: RM-031.**
  - Rename the player-source variant executables (`gabbaboy-player-mutant-rb-swap`, `-mutant-dmg-path`, `test_player_session_mutant_ignores_flag`) to `*-playervariant-*`, following 18-04's `hostvariant` precedent. CTest names do not change.
  - Drop the duplicate `GabbaBoy::core` link (`tests/player/CMakeLists.txt:192`), since `gabbaboy_accept` already brings it.
  - Widen the player lane filter in `verify-phase3-player.sh:471` to `^(player_|core_linkage_)`.
  - Negative controls: restoring the `mutant` name, or restoring the double link, each makes `core_linkage_links` fail on the player build.

### Review leftovers (19-02)

- **D-08: Fix before the tag.**
  - **WR-C04:** the budget checker runs from `git show "$BUDGET_BASE:tests/scripts/verify-test-budget.py"` with no head fallback, because main has had the file since Phase 16. Add a policy pin and a mutant that runs the head copy. The head copy's `--self-test` stays as a separate step.
  - **IN-05 (IN-B02):** fuzz-receipt source binding.
  - **IN-08 (IN-C02):** `persist-credentials: false`, and `libbet-repro.yml` joins `READONLY_WORKFLOWS`.
  - **IN-07 (IN-C01):** the retry paragraph in docs/release.md says "identity and consistency check", not tamper detection.
  - **IN-02:** a limitation note.
  - Each fix gets a negative control.
- **D-09: WR-A05 plus IN-01 are included, without partial mutation.**
  - Move the BOOL/COUNT/EVENT_KIND range predicate of `state_store_host_value` (`src/core/gabbaboy.c` ~4145) into `state_validate`, so the check runs before any write.
  - Make the apply-time raw-to-host conversion infallible and shared by `state_apply` (~4723) and the store path, then delete the duplicate switch.
  - Do not use an `assert` on a fallible return in the apply path: it does nothing in NDEBUG builds, and the instance would be partly written.
  - Guard the test-only helpers behind the test seam flag (IN-01).
  - **Controls:**
    - the 153 continuation rows, `state-goldens-v1.json` and the state pins stay byte-identical;
    - a mutant that drops the new range check makes a refusal test fail.
  - **Rationale:** v0.3.0's headline is loading untrusted state, and the fix is small. The perf risk is nil because the load path is not in the tracer workload.
  - If 19-02 overruns, WR-A05 is the first item cut. Record it as deferred again with the reason.
  - **Reversibility:** reversible.
- **D-10: Deferred to RM-024 with the reason recorded:** IN-03, IN-04 and IN-06. They are test-quality items with no open defect. WR-C05 is already fixed on main (in squash `f4082a65`).

### v0.3.0 support ledger (19-03)

- **D-11: Scoped claims are validated managed input, rendered by the generator.** Hand prose is never accepted: the generator fixed point already rejects it as `ledger-not-generated`.
  - The new `tests/data/support-claims-v0.3.json` follows the `release-disclosure.json` precedent. It holds:
    - `schema_version`, `kind: scoped-support-claims`, `applies_from_version: 0.3.0`;
    - `claims[]`: `id`, `requirements`, `statement`, `models`, `modes`, `corpus`, `platforms`, `surface`, `evidence` (CTest names), `non_claims`;
    - `non_claims[]`.
  - The checker, not the data file, holds the list of required non-claim ids.
  - **Renderer:** copy `render_v2_ledger` to a new `render_v3_ledger`, so the v0.2.0/v0.2.1 fixed points stay byte-exact. `validate_data_v2` (~585) hard-rejects any version that is not 0.2.x, so v0.3 gets its own validation branch.
  - **Derived values:** the validator recomputes every count and enum from the source artifacts and rejects drift:
    - `state-forks.json` `expected_case_count` (153);
    - the state goldens and their release;
    - the `docs/host-contract.json` rows;
    - `tests/expected-tests.txt`;
    - the `if(WIN32)` exclusion list in `cmake/ExpectedTests.cmake`.
  - The disclosure block renders unchanged (`applies_after_version` 0.2.1 < 0.3.0). Do not edit `release-disclosure.json`.
- **D-12: Keep the attached sidecar `support-ledger.json` at schema 2 if at all possible.**
  - The claims are bound through `ledger_blob` (the tagged ledger's blob digest).
  - The release gates hard-require sidecar schema 2 (`verify-release-gates.sh` ~256, ~423, release.yml ~1038, replay fixtures).
  - If the planner finds the sidecar must change, 19-05 owns the gate and replay updates and depends on 19-03.
- **D-13: The claims.** Scope axes:
  - model: DMG-CPU-B, CGB-CPU-E;
  - mode: dmg, cgb-compat, cgb-native;
  - corpus: named, with a count;
  - platform: linux-x64, macos-arm64, windows-x64;
  - surface: core-api, runner-host-mode, macos-player;
  - boot: skipped.

  | id | Scope |
  |---|---|
  | `state-api`, `state-continuation`, `state-refusal`, `state-canonical-pins`, `state-battery-rtc` | Both models, all modes, all three platforms, surface core-api. Cross-platform byte equality is claimed only if it is backed by the three `state-pins-*` artifacts from one exact-source push run, bound through the sidecar or fuzz-reader evidence |
  | `host-raw-save`, `host-signals-exit`, `host-format-table` | linux-x64 and macos-arm64, runner-host-mode |
  | `player-slots` | macos-arm64, macos-player. The SDL-free engine is also tested on Linux |

  **Required non-claims:**
  - no cross-version or cross-build state loading (D-113);
  - no third-party state import or export (BESS, mGBA, SameBoy, BGB), and no claim that raw `.sav` is interoperable;
  - no power-loss durability;
  - no Windows host mode (it is refused with exit 2);
  - no Linux or Windows player;
  - no CGB game-level evidence; physical CGB-E remains UNKNOWN/POLICY;
  - no oracle replay from forks;
  - no authentication from the CRC or ROM digest;
  - no recorded runner wall-clock time;
  - no Playstead live integration.
- **D-14: Negative controls for "unscoped claim".** Each is paired with an unrelated positive control in the same run, following `self_test_disclosure`.
  1. A missing or empty `models`, `platforms`, `corpus` or `surface` → `claim-scope-missing`.
  2. A wildcard or out-of-enum platform → `claim-platform-unpackaged`.
  3. A platform where the deciding test is excluded, such as windows on `host_signal_term` → `claim-platform-unexercised`.
  4. `macos-player` on a non-macOS platform → `claim-platform-unexercised`.
  5. Empty evidence → `claim-unbacked`; an unregistered CTest name → `claim-evidence-unregistered`.
  6. A drifted corpus count → `claim-corpus-drift`.
  7. Pins whose release is not the tree's version → `claim-pins-stale`.
  8. A required non-claim deleted → `non-claim-missing`.
  9. A sentence hand-inserted into the ledger → `ledger-not-generated`.
  10. Unscoped, cross-version, durability or Windows-host claims in README, preview or release notes → new adoption patterns.
  11. An interop claim naming SameBoy, BGB or BESS → `verify-no-interop-claims.py` widened beyond mGBA, and the v0.3.0 ledger added to its FILES.
- **D-15: The release-notes checker gains v0.3 rules** (`verify-v02-adoption.py --release-notes`, ~587), each with controls in `run_self_test_release_notes`.
  - It requires "Save states load only in the exact GabbaBoy release that wrote them." and "Host mode is POSIX-only; Windows refuses `--save-dir`."
  - v0.2.0-specific phrases become version-aware (~260, ~719-727, `FALSE_PUBLICATION_CLAIM`).
  - The Ir figure disclosed in the notes is regenerated, not copied. It currently says +8.3% from attribution head `711f4fd`, while the actual figure at `4ace5e37` is about +9.5% (ratio 1.095).
- **D-16: The `v02-*` evidence names are kept.** `v02` is the evidence-schema family. Receipts are bound by `tag` and `source_sha`, not by name. A docs note says so, and the rename goes on the v0.4 roadmap.

### Rehearsal binding and the window lifecycle (19-04)

- **D-17: Two rehearsals, with an explicit order and roles.**
  1. R1 runs green on `rehearsal/v0.3.0` at the reviewed version-PR head H.
  2. Run `verify-version-window.py --digest`, fill in R1 and the CI run identities, and commit only the record as W.
  3. Fast-forward `rehearsal/v0.3.0` to W. The branch has `concurrency: cancel-in-progress`, so push only after R1 is complete.
  4. R2, nightly-asan and the required CI run at W.

  Roles:
  - The record's `rehearsal` entry is R1, the review-time run. A record cannot name a run at its own commit.
  - R2 is the release-binding run, selected as the newest successful run whose tree equals the tag.
  - The trust-path judges get **no one-path tree allowance**.
  - **Control:** R2 red while R1 is green must refuse the release, never fall back to R1.
- **D-18: SC1 is checked before the tag and again after it.**
  - **Before the tag (new):** a `pull_request`-triggered gate on the version PR, active only when the tracked record is active. It runs from the trusted base revision with the PR head as data:
    - `verify-version-window.py --check` with `--rev` = PR head W, `--base` = PR base, and the body from the event payload;
    - the same `validate_rehearsal_run` predicate against R2's run JSON (`head_sha == W`, workflow path, push or dispatch event, success, repository and fork, tree).
    - Merge only when it is green.
  - **After the tag (defence in depth, fatal):** `validate_rehearsal_run` gains `pr_head` and `not_after`.
    - `pr_head`: the run's `head_sha` equals the version PR's head at merge, from `commits/{sha}/pulls`.
    - `not_after`: the pinned reused `run_attempt`'s max job `completed_at` (from `runs/{id}/attempts/{n}/jobs`) is ≤ the PR's `merged_at`. These are server-recorded order facts, like the nightly gate's timestamp ordering. They are not a clock or expiry.
    - It runs in step 1 of the `candidate` job (which already has `actions: read`) and in `nightly-gate`.
    - Refusals: `rehearsal-not-version-pr-head`, `rehearsal-postdates-tag`.
    - The binding is fatal. Only the performance *reuse* keeps its fresh-measurement fallback.
  - **The rehearsal refuses to run if `vX.Y.Z` already exists remotely.**
  - **Controls:**
    - a postdated run;
    - attempt 2 finishing after the merge;
    - a tree-equal commit that is not the PR head;
    - a missing `merged_at`;
    - another run id;
    - a `pull_request` event, a fork or another workflow path;
    - an inactive record at W.
- **D-19 is in "Pre-flight and docs (19-06)" below.**
- **D-20: The version-window record rule reads the tree only.**
  - An active record is legal only when its `release_version` equals the tree's own version, so a version bump with a stale active record is rejected. Add a negative control.
  - It never consults tags or live refs. The ci.yml run at the tag commit fetches tags, so a tag-reading rule would turn that run red and strand `candidate-fuzz`. Checkers read immutable commits (D-105).
  - The post-release PR resets the record to inactive (D-23).
- **D-21: Close the gap in post-tag lifecycle replay coverage before the window.**
  - Enumerate every `gh` endpoint and response member that the post-tag path uses. About 4.1k lines of `release.yml`, `verify-release-gates.sh`/`.py`, `verify-release-source-proof.py` and the new `release-evidence-lifecycle.sh` changed since v0.2.1.
  - Require `verify-release-lifecycle.py` replay coverage for each one, including every new step and asset from D-18 and 19-05.
  - Refresh `tests/data/release-api/` captures with read-only GETs of the published v0.2.1, sanitized as recorded in `SOURCES.md`.

### Tag-bound receipts and readback (19-05)

- **D-22: The evidence added for v0.3.0 adds no job that runs only after the tag.**
  - **Perf gate:** the existing `candidate-fuzz` trusted reader also reads the `perf-gate` result of the same exact-source ci.yml push run. It binds:
    - the SHA, the v0.2.0 base SHA and the limits blob;
    - Ir for both repeats, the digests, the realtime figure, the tool identity, the run and the attempt.
    It verifies them with a new `verify-perf-gate.py --verify-receipt` and binds them into an existing attached receipt. It adds no new job, so it needs no ledger row.
  - **New assets:** a new asset is allowed only if the planner finds one unavoidable. It must then go into every asset-name list (`release-evidence-lifecycle.sh` ~52-274, `--check-attached-evidence`), the policy pins and the replay.
  - **Controls:** ratio over the limit, another SHA, a PR event, a wrong limits blob.
  - **Fuzz:** hostile-state fuzz is already in `v02-fuzz-receipt.json` (`STATE_SEED_SPECS`, the state target digest, the witnesses). The ledger cites it; no new receipt.
  - **Host-contract smoke on shipped bytes:** `tests/scripts/test_installed_host.py --prefix <extracted archive>` runs in the rehearsal `package` job on the rehearsal archive, which is pre-tag and bound to the tag by tree equality. It also runs in the release `candidate` job on the downloaded archive (Linux and macOS). `v02-consumer-receipt.json` gains `host_smoke {result, continuation, preload}`, and `validate_consumer_receipt` requires it. The consumer state round-trip is already covered by `tests/consumers/{c,cpp}`.
  - **Profile string:** `release-evidence-lifecycle.sh:277` hardcodes "DMG-CPU-B deterministic software profile only". Replace it with a version-aware scope string and add a control.
- **D-23: The readback reuses the existing schema.**
  - Extend `verify-v03-dispositions.py`'s `release_readback {path, sha256}` receipt instead of writing a parallel checker. It must reconcile:
    - tag → SHA and tree from git objects;
    - `is_draft: false`;
    - the exact asset-name set and asset ids against the pre-publish inventory;
    - each API `digest` against its `SHA256SUMS` line;
    - the `release-receipt` digests against the assets;
    - the sidecar `ledger_blob` against the blob of `docs/support/v0.3.0.md` at the tag.
  - Each element gets a control.
  - The receipt is read with `git show <rev>:`. If it lives under `.planning/phases`, it needs a count-pinned allowlist row in `verify-no-phase-paths.py`, or a path argument.
  - The `FORBIDDEN_TEXT` privacy scan (`verify-release-lifecycle.py` ~164) is extended to the committed readback and receipt JSON.
- **D-24: The perf policy does not change.**
  - Ir is measured against v0.2.0 (`ab301aa`) with the immutable limits base, and paired timing stays advisory (D-113).
  - Measured at `4ace5e37`: the ratio is about 1.095 against a limit of 1.10, so the headroom is about 0.5%.
  - No Ir exception can pass on hosted runs. A breach means a perf fix or a rescope; it is never a waiver.

### Pre-flight and docs (19-06)

- **D-19: Pre-flight a synthetic 0.3.0 tree before PR A merges.**
  - On the phase branch, build a tree with the #131 bump applied, a ledger rendered by `--write-current`, and the version-PR content.
  - That content includes the **hand-authored `release-change` disposition row** in `tests/data/state-compatibility.json`. `verify-state-pins.py` ~294 refuses to relabel 0.2.1 pins. The row is named, pre-drafted here, and committed in the window as reviewed, non-generated content.
  - Push it to a scratch rehearsal branch. Run:
    - the full CTest suite, including a `GBB_BUILD_PLAYER` tree (GB-GSD-030);
    - the lifecycle replay;
    - `--release-notes` on a drafted body;
    - `--check --release-head`.
  - Fix every version literal on the phase branch first:
    - about 11 checker files pin `0.2.1`;
    - `REHEARSAL_TAG = "v0.2.1"` (`verify-release-source-proof.py:271`);
    - `LEDGER_BOUND_LAST_VERSION`;
    - `verify-state-pins.py`, `verify-state-contract.py`, `verify-v03-dispositions.py`.
  - The version PR then carries only:
    - generated content;
    - the rendered ledger and pins;
    - the `release-change` row;
    - links;
    - the notes preface;
    - the window record.
- **D-25: Update the docs together in 19-06** (AGENTS rule).
  - `docs/release.md`:
    - the v0.3 intro;
    - upgrade and rollback guidance for slots, the undo file and host `.sav`: back up the preference directory; slots do not survive an upgrade; battery and host raw `.sav` do;
    - the operator sequence of D-17, D-18 and D-26;
    - the stale perf receipt name and the dispatch-input text.
  - `docs/native-integration.md`: fix the stale v0.1.0 ledger link (~395) and the `gabbaboy-v0.2.0` prefix (~148), and add a link check.
  - `docs/support/unreleased.md` becomes a "reconciled into v0.3.0" stub.
  - `unreleased_host_entries` (`tests/cmake/host-contract.cmake` ~131-155) is retargeted at the v0.3.0 ledger or retired in favour of the claim validator.
  - **CHANGELOG:** move the stale top `## Unreleased` (Phase 9 MBC3) block under 0.2.0, and add a check that the first `## ` heading is a version. Otherwise #131 inserts `## [0.3.0]` under "Unreleased".
  - **Links to `v0.3.0.md`** in README (`check_binding`), preview (`LEDGER_VERSION`), release.md and native-integration.md change in the version PR, where the ledger exists.

### Window, tag, publish, post-release (19-07) and the gap slot (19-08)

- **D-26: The window sequence.**
  1. PR A squash-merges and #131 regenerates.
  2. On #131: render the ledger and pins, add the `release-change` row, the links and the preface under `## [0.3.0]` (D-112(5)). This is head H.
  3. Required CI and R1 run at H.
  4. Run `--digest` and commit the record as W.
  5. Fast-forward `rehearsal/v0.3.0`; R2, nightly-asan and required CI run at W.
  6. The D-18 pre-tag gate goes green; `--check` passes at W against the current main.
  7. Squash-merge #131 and assert tree(squash) == tree(W).
  8. The release run builds and attaches the draft, runs the final gate and publishes.
  9. Commit the readback.

  **Rules:**
  - No main push of any kind during the window, planning commits included.
  - Never push or rerun `rehearsal/v0.3.0` after the merge.
  - The PR body is the release notes, and regeneration overwrites it. Run `--release-notes` on the body itself.
  - The squash commit must classify as `full` in ci.yml, so the fuzz and perf-gate jobs run at S.
- **D-27: Post-tag failure policy.**
  - The tag and draft are never moved, deleted or replaced.
  - Classify each failure first:
    - **The fix is outside the tagged tree** (a judge, the lifecycle or a workflow): fix it on main with a non-releasable type, capture the failing real response into `tests/data/release-api/`, replay the remaining stages, fix everything in one PR (find all, then fix once), and redispatch with `retry=true`.
    - **The tagged tree itself is wrong:** stop and hand it to the owner (a v0.3.1 decision).
  - All post-tag recovery uses only 19-08, the one reserved gap round. A second failure goes to the owner. No gap-cap waiver is requested.
- **D-28: The post-release PR (PR B, in 19-07) is the phase boundary.**
  - It resets `tests/data/version-window.json` to inactive.
  - It optionally re-cites the predecessor-name rows from the v0.3.0 run.
  - It adds the readback receipt and closes the `verify-v03-dispositions.py` pending rows to pending=0.
  - It records REL-01 traceability and the SUMMARYs.
  - `boundary_sha` goes in a file the verifier does not cover (GB-GSD-027).
  - Checks read the boundary commit, never HEAD.
  - After PR B squashes, STATE routes to `/gsd-verify-work 19`. Both automatic advance flags stay false, and the phase stops. The full re-verify at the final head belongs to the milestone audit (D-103).
- **D-29: Plans and waves.**

  | Plan | Wave | Content |
  |---|---|---|
  | 19-01 | W1 | Entry blockers (D-04..D-07) |
  | 19-02 | W1 | Review leftovers (D-08..D-10) |
  | 19-03 | W1 | Ledger (D-11..D-16) |
  | 19-04 | W2 | Rehearsal binding and window (D-17, D-18, D-20, D-21) |
  | 19-05 | W3 | Receipts and readback (D-22..D-24); depends on 19-03 if the sidecar changes |
  | 19-06 | W4 | Pre-flight, docs and PR A merge (D-19, D-25) |
  | 19-07 | W5 | Window, release and PR B (D-26..D-28) |
  | 19-08 | — | Reserved gap slot (D-27) |

  19-01..19-03 touch largely disjoint files. 19-04 and 19-05 share the trust-path scripts, so they run in sequence.
- **D-30: Branch hygiene.**
  - Phase work uses `gsd/phase-19-qualified-v0-3-0-release`, from `origin/main`.
  - Keep `rehearsal/v0.2.1`, which D-04's retention check requires.
  - Prune `rehearsal/phase-15.1-*` and the merged `gsd/phase-18` remote branch at milestone close.
  - The uncommitted owner `.planning/config.json` effort change and the stale Codex `milestone.lock` stay out of phase commits and are left for the owner.

### Owner-only items (none block planning)

- **Immutable releases.** Left **off** for v0.3.0, because enabling them is an unrehearsed change to the publish path. They become a v0.4 option. If the owner wants them now, enable them only before the window opens.
- A defective tagged tree, which would mean a v0.3.1 decision.
- Any Ir limit widening. It cannot pass on hosted runs, so the only routes are a fix or a rescope.
- Any waiver beyond the one gap round. None will be requested.

### Claude's Discretion

- The exact field names for D-04 and D-18, the refusal codes, and whether the pre-tag gate is a new workflow or a job in `ci.yml`. Whichever is chosen must satisfy `verify-workflow-policy.py` exact-set pins.
- Wording of the v0.3.0 notes preface and of the claim statements, within D-13 and D-15.
- Whether the WR-A05 conversion helper is a function or a table.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and rules
- `.planning/ROADMAP.md` §Phase 19 (~209-222): goal, SC1-3, cap 8.
- `.planning/REQUIREMENTS.md` REL-01 (~93-96).
- `AGENTS.md`: phase pause, D-102..D-105 caps, checkers on immutable commits, automated verification.
- `.planning/context/DECISIONS.md`:
  - D-20, D-110, D-111 (timeout ledger and `release_bound`);
  - D-112 (the v0.2.1 window and post-tag recovery);
  - D-113 (exact-version state, advisory paired timing);
  - D-114..D-119;
  - D-120 (this context).
- `.planning/context/FUTURE-MILESTONES.md` RM-027, RM-028, RM-031, RM-024.
- `.planning/context/LESSONS.md`:
  - GB-RELEASE-001..003;
  - GB-GSD-025..030;
  - GB-CI-010..013.

### Release machinery
- `docs/release.md`: the whole runbook (window, lifecycle, nightly gate, review approval, perf reuse, rehearsal privilege split).
- `.github/workflows/release.yml`, `release-rehearsal.yml`, `release-please.yml`, `nightly-asan.yml`, `ci.yml`; `release-please-config.json`.
- `.github/scripts/verify-workflow-policy.py`:
  - timeout ledger, `verify_cited` ~2336-2367;
  - `LEDGER_BOUND_LAST_VERSION` ~2224-2280;
  - self-test mutants ~3598-3632.
- `.github/scripts/release-evidence-lifecycle.sh`, `verify-release-gates.sh`, `verify-release-source-proof.py` (`validate_rehearsal_run` ~123-164, `REHEARSAL_TAG` 271), `produce-release-evidence.sh`.
- `.github/ci-timeouts.json`.
- `tests/scripts/verify-version-window.py`, `tests/data/version-window.json`.
- `tests/scripts/verify-release-lifecycle.py`, `tests/data/release-api/` (with `SOURCES.md`).
- `tests/scripts/verify-release-gates.py`, `verify-perf-gate.py`, `run-perf-gate.sh`, `tests/baseline/perf-gate-v1.txt`.
- `tests/scripts/verify-v03-dispositions.py`, `state_boundary.py` (read only; do not edit for RM-027).
- `.planning/phases/GB-17-native-save-state-core/17-REVIEW.md` (WR-C03, WR-C04, WR-A05, IN-*) and `17-REVIEW-DISPOSITION.md`.

### Ledger and docs
- `tests/scripts/verify-support-ledger.py` (`require_generated` ~2865, `check_disclosure_generator` ~2903, `validate_data_v2` ~585, `DISCLOSED_LEDGERS` ~2824).
- `tests/data/release-disclosure.json`.
- `docs/support/v0.2.1.md`, `docs/support/unreleased.md`.
- `tests/scripts/verify-v02-adoption.py`, `verify-no-interop-claims.py`, `verify-host-contract.py`, `verify-state-pins.py`.
- `tests/data/state-forks.json`, `tests/data/state-compatibility.json`, `docs/host-contract.json`, `cmake/ExpectedTests.cmake`, `tests/expected-tests.txt`.
- `docs/state-format.md` (~37-44, ~437-438), `docs/native-integration.md`, `docs/preview.md`, `README.md`, `CHANGELOG.md`.
- `.planning/phases/GB-17-native-save-state-core/17-VERIFICATION.md` and `.planning/phases/GB-18-player-save-slots-and-host-contract/18-VERIFICATION.md`, for what was actually proven.

### External (primary sources)
- [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
- [release-please customizing](https://github.com/googleapis/release-please/blob/main/docs/customizing.md)
- Savestate-compatibility precedent:
  - [SameBoy releases](https://github.com/LIJI32/SameBoy/releases) (an explicit cross-version floor, BESS);
  - [Dolphin](https://bugs.dolphin-emu.org/issues/11815) (version-bumped states; in-game saves are the cross-version path).
- Sibling lessons: `/Users/jon/projects/muhtari/.planning/LESSONS.md` (MU-REL-001/002, XFER-026) and `/Users/jon/projects/cogmaster/.planning/LESSONS.md` (XFER-008, -027, -039, -064).
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Tree-equality machinery** (`verify-release-source-proof.py validate_rehearsal_run`, `verify-v02-performance.py --verify-reuse --tag-tree`): extend it for D-04 and D-18; do not add a parallel path.
- **Generator fixed point** (`verify-support-ledger.py --write-current`, `require_generated`) and the managed disclosure input: the template for the D-11 claims file.
- **Lifecycle replay** (`verify-release-lifecycle.py` with the `gh` stand-in and sanitized captures): the place where every post-tag step must be covered (D-21).
- **`verify-v03-dispositions.py` `release_readback` schema**: extend it for D-23.
- **`test_installed_host.py --prefix`**: already exists and is reused on extracted archives (D-22).
- **18-04 `hostvariant` naming**: the precedent for D-07.

### Established Patterns
- Every refusal prints `REJECT code: reason` and exits 1. Every new rule gets a mutant or negative control in `--self-test` or `controls` mode.
- Workflows are judged by `verify-workflow-policy.py` as exact sets. A new step, job or permission needs a policy pin.
- Trusted judges run from the default-branch revision with the tagged or PR tree as data.
- Point-in-time boundary checks read one commit (`--rev`). Live refs and tags are never consulted.

### Integration Points
- PR A touches the trust path: the policy, the lifecycle, the source proof, the gates, the ledger generator and the core `state_validate`/`state_apply`.
- The version PR touches only generated or reviewed release content.
- PR B touches only `tests/data/version-window.json`, `ci-timeouts.json` re-citations and the readback/planning files.
</code_context>

<specifics>
## Specific Ideas

- Live facts at discussion time:
  - `origin/main` is `f80bdf54`;
  - `--check --release-head` on main prints `REJECT timeout-ledger-provisional: nightly-asan.yml:report-red` (exit 1);
  - `--verify-cited` fails 1/45 rows (`release.yml:candidate-performance`);
  - immutable releases are disabled; no rulesets;
  - required checks are `required-native`, `fixture-repro` and `preview-package-smoke`;
  - 0 open issues; the only open PR is #131.
- The perf gate at `4ace5e37` (CI run 40872007088): tracer 1.095, libbet 1.094, visible-demo 1.094, realtime_min 8.402.
- The phrasing follows SameBoy and Dolphin: states are temporary and exact-version; in-game (battery) saves are the cross-version path.
</specifics>

<deferred>
## Deferred Ideas

- **v0.4 candidates:**
  - GitHub immutable releases with `gh release verify`;
  - an optional ruleset protecting `v*` tags;
  - SLSA build provenance (would need a new action, which goes against copy-over-dependency);
  - renaming `v02-*` to version-agnostic evidence names;
  - `bump-minor-pre-major`;
  - moving the paired-timing baseline off v0.1.0.
- **RM-024:** IN-03, IN-04, IN-06 from the Phase 17 review.
- **Owner decision:** scrubbing `@/Users/...` paths from the archived v0.1 plans (already public in v0.1.0..v0.2.1).
- **`/gsd-complete-milestone`:**
  - the sibling XFER scan;
  - the FUTURE-MILESTONES refresh;
  - the `v0.3` GSD tag;
  - pruning the stale branches;
  - the milestone audit.
- **Carried from Phase 18 (unchanged):**
  - Windows host mode, power-loss durability claim, advisory save-dir locking;
  - player SIGTERM, packaging the runner for Playstead;
  - fullscreen and VoiceOver slot status;
  - converging the player `.gbb` atomic_save with `gabbaboy_host`;
  - RM-020, RM-021, RM-022.
</deferred>

---

*Phase: 19-qualified-v0-3-0-release*
*Context gathered: 2026-10-29*
