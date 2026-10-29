# Phase 19: Qualified v0.3.0 Release - Research

**Researched:** 2026-10-29
**Domain:** Release engineering for a C emulator core: exact-tag rehearsal binding, scoped support ledger, tag-bound receipts, GitHub Actions trust path. No new external dependencies.
**Confidence:** HIGH for code anchors and wiring (all opened this session); MEDIUM for remote-GitHub behaviour (inferred from workflows and read-only GETs, never dispatched).
**Scope note:** CONTEXT.md D-01..D-30 are adopted and were not re-litigated. This file verifies their code anchors, lists drift, and makes the plan executable. Where an anchor contradicts a decision, it is called out under "Drift and contradictions" with a recommendation.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
All of D-01..D-30 in `19-CONTEXT.md` are locked (adopted by owner-delegated synthesis, D-120). The planner MUST read that file; it is the contract. Headlines the plans must not contradict:

- **D-01/D-02/D-03** One squashed phase PR ("PR A") carries 19-01..19-06 and is the only pre-window push to main. PR #131 (`chore(main): release 0.3.0`) is reused and merged last. Release-mechanics PR titles use non-releasable conventional types (`ci`, `test`, `docs`, `chore`). `bump-minor-pre-major` is NOT added.
- **D-04..D-07** Entry blockers: RM-027 closes by `tree_equal_sha` + `cited_tree` + optional `cited_job_name` (no version-expiry rule, no new `release_bound` row); `candidate-performance` uses the predecessor-name citation; WR-C03 by a main `report_red_dry_run` dispatch before PR A; RM-031 by renaming player-source variants to `*-playervariant-*`, dropping the duplicate core link, widening the player lane filter. Do not edit `state_boundary.py` / `state_boundary_controls`.
- **D-08/D-09/D-10** Fix before tag: WR-C04, IN-05 (IN-B02), IN-08 (IN-C02), IN-07 (IN-C01), IN-02; WR-A05 + IN-01 without partial mutation (first item cut if 19-02 overruns). IN-03, IN-04, IN-06 deferred to RM-024.
- **D-11..D-16** Scoped claims are validated managed input `tests/data/support-claims-v0.3.json` rendered by a copied `render_v3_ledger`; sidecar stays schema 2; claim list, scope axes, required non-claims, 11 negative controls; release-notes checker gains v0.3 rules; `v02-*` evidence names kept.
- **D-17/D-18/D-20/D-21** Two rehearsals (R1 at reviewed head H, R2 at record commit W); pre-tag `pull_request` gate; fatal post-tag `pr_head` / `not_after` binding; window-record rule reads the tree only; close post-tag lifecycle replay coverage and refresh captures.
- **D-22..D-24** No job that runs only after the tag; perf-gate receipt folded into the existing `candidate-fuzz` reader; host smoke on shipped bytes; version-aware profile string; readback extends `verify-v03-dispositions.py`; perf policy unchanged (Ir vs v0.2.0, limit 1.10, headroom about 0.5%).
- **D-19/D-25** Pre-flight a synthetic 0.3.0 tree before PR A merges; docs updated together in 19-06.
- **D-26..D-30** Window sequence, post-tag failure policy (tag/draft never moved; one gap slot 19-08), PR B is the phase boundary, plan/wave table, branch hygiene.

### Claude's Discretion
- Exact field names for D-04 and D-18, the refusal codes, and whether the pre-tag gate is a new workflow or a job in `ci.yml` (must satisfy `verify-workflow-policy.py` exact-set pins).
- Wording of the v0.3.0 notes preface and of the claim statements, within D-13 and D-15.
- Whether the WR-A05 conversion helper is a function or a table.

### Deferred Ideas (OUT OF SCOPE)
- v0.4 candidates: GitHub immutable releases with `gh release verify`; optional ruleset protecting `v*` tags; SLSA build provenance; renaming `v02-*` evidence; `bump-minor-pre-major`; moving the paired-timing baseline off v0.1.0.
- RM-024: IN-03, IN-04, IN-06 from the Phase 17 review.
- Owner decision: scrubbing `@/Users/...` paths from archived v0.1 plans.
- `/gsd-complete-milestone`: sibling XFER scan, FUTURE-MILESTONES refresh, `v0.3` GSD tag, stale-branch pruning, milestone audit.
- Carried from Phase 18: Windows host mode, power-loss durability claim, advisory save-dir locking, player SIGTERM, packaging the runner for Playstead, fullscreen/VoiceOver slot status, converging player `.gbb` atomic_save with `gabbaboy_host`, RM-020/021/022.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REL-01 | `v0.3.0` is published from its exact tag with save-state and host-contract claims scoped by model, corpus and platform, every receipt bound to that tag; hardening happens before the tag | SC1 -> sections "Rehearsal binding (19-04)" and Validation rows V1-V4; SC2 -> "Support ledger (19-03)" and V5-V7; SC3 -> "Receipts and readback (19-05)" and V8-V10. Pre-flight experiment (below) lists exactly what breaks at VERSION 0.3.0. |
</phase_requirements>

## Summary

Every code anchor in CONTEXT.md resolves in the current tree (`origin/main` = `f80bdf54`, branch head `ebcff840`), at the line numbers CONTEXT gives or within a few lines. The adopted design is executable, but verification found **eight concrete drifts or gaps** the planner must absorb (full list under "Drift and contradictions"). The ones that change task content: (1) the `ci-timeouts.json` normal-row schema is a strict exact set with no field that can carry the "disclosure" text D-04/D-05 require; (2) `ci.yml:perf-gate` emits no machine-readable receipt and uploads no artifact, so D-22's `--verify-receipt` needs an emitter first, and D-22 does not name which existing attached receipt carries the binding; (3) the Phase 16 disposition record is already closed (`pending=0 closed=6`), so D-28's "close the pending rows" is stale and the v0.3.0 readback needs its own entry point in `verify-v03-dispositions.py`; (4) WR-A05's range predicate already exists in validation (`state_field_kind_valid`), so the work is converting `state_apply` onto one shared infallible store, not moving a predicate; (5) the rehearsal `judge` job checks out both trees shallow, so D-04's offline git-object check cannot run there without a deeper checkout; (6) a fourth wrong-core linkage violation (`gabbaboy-player-mutant-ppu-follows-cpu`) exists beyond RM-031's list; (7) the release-notes Ir figure comes from `tests/baseline/perf-attribution-v1.json` (head `711f4fd`), so "regenerated, not copied" needs a hosted `perf-attribution.yml` dispatch (about 150-minute cap) or a different figure source; (8) `release_lifecycle_controls` already takes about 51 s against a 60 s TIMEOUT.

A scratch pre-flight (tree at `f80bdf54` with only VERSION and the manifest bumped to 0.3.0, configured with `cmake --preset phase1`) shows the exact blast radius of the version bump on python-only checks: 11 fail (10 CTests plus the direct `workflow_policy_check` run) until the ledger, pins and docs links exist. This proves D-19's approach is necessary and bounds it.

**Primary recommendation:** Execute D-29 as written, with three serialisation fixes (19-02 after 19-01 inside W1 because both edit `verify-workflow-policy.py` and the `ci-lanes.cmake` floor; 19-06 owns all of `docs/release.md`; 19-05 starts with the perf-gate receipt emitter), resolve the five Open Questions below in plan text before coding, and commit before running any `--rev`-bound CTest (replay, gates, state pins read configure-time `HEAD`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Version-PR content window and record rule | Trusted checker on default branch (`verify-version-window.py`) | `release-please.yml` job `version-window-gate`; new pre-tag `pull_request` gate | Checkers read immutable commits; judge code comes from main, subject tree is data |
| Rehearsal run binding (`pr_head`, `not_after`) | Trusted judge (`verify-release-source-proof.py`) | `release.yml` `candidate`/`candidate-performance` step, `release-evidence-lifecycle.sh nightly-gate` | Server-recorded order facts (`merged_at`, attempt `completed_at`) come from GitHub API, not a clock |
| Timeout-ledger citations | `verify-workflow-policy.py` (offline `--check`) | online `--verify-cited` (advisory, never in CTest) | Offline = git objects only; online confirms run tree via API |
| Scoped support claims | `tests/data/support-claims-v0.3.json` + `verify-support-ledger.py` renderer/validator | `verify-v02-adoption.py`, `verify-no-interop-claims.py` | Managed input rendered by the generator; hand prose fails `ledger-not-generated` |
| Perf-gate / consumer / fuzz receipts | CI producer jobs (`ci.yml`, `release-rehearsal.yml package`) | `candidate-fuzz` trusted reader; `verify-v02-delivery.py` validators | No new post-tag job; verified by trusted reader at release |
| Published-asset readback | `verify-v03-dispositions.py` readback entry | `verify-published-release-assets.py`, `release-evidence-lifecycle.sh` | Committed receipt read with `git show REV:` |
| Core state apply (WR-A05) | `src/core/gabbaboy.c` (`state_validate` then `state_apply`) | tests that `#include` the `.c` | Validation before any write; one shared raw-to-host conversion |
| Branch/PR/tag mechanics | GitHub (remote, owner-authorized `gh`) | local scratch pre-flight | Only the remote can create the tag; everything else is checkable locally |

## Standard Stack

No external packages are installed in this phase. Everything is first-party scripts plus tools already used by the repo.

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| Python 3 stdlib (`python3 -I`, `__debug__` guarded) | system | All checkers; `Fraction` arithmetic for ledger | Existing house style; no third-party imports [VERIFIED: `tests/scripts/verify-version-window.py:1-40`, `.github/scripts/verify-workflow-policy.py:2215-2330`] |
| CMake + CTest + Ninja (`phase1` preset) | CMake >= 3.25 floor | Registration and execution of every check | [VERIFIED: `CMakePresets.json`: `"cmakeMinimumRequired": { "major": 3, "minor": 25, "patch": 0 }`] |
| `gh` CLI | local | Read-only GETs now; owner-authorized writes in 19-06/19-07 | Existing release runbook (`docs/release.md`) |
| bash + jq | system / ubuntu-22.04 | Lifecycle script and its replay | `release-evidence-lifecycle.sh` is bash+jq; replay is POSIX-only |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `tests/scripts/verify-uat-closure.py` | Write/check `{N}-UAT.md` from SUMMARY coverage | `/gsd-verify-work 19` only |
| `tests/scripts/verify-summary-coverage.py` | CTest `summary_coverage_live` sweeps live SUMMARYs `--since 16` | Every SUMMARY authored in this phase |
| `cachegrind` hosted run (`perf-attribution.yml`) | Only if the Ir figure in notes must be regenerated (OQ-3) | Before PR A, hosted only (valgrind is not installable on this macOS host) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Copy `render_v2_ledger` -> `render_v3_ledger` (D-11) | Parameterise one renderer | Rejected by D-11: v0.2.0/v0.2.1 fixed points must stay byte-exact; copy is cheaper than proving equivalence |
| New attached asset for the perf-gate receipt | Embed a verified `perf_gate` block in an existing receipt | See OQ-2; embedding avoids touching about 8 asset-name lists |

**Installation:** none.

## Package Legitimacy Audit

No external packages are installed, added or upgraded by this phase. **Packages removed due to [SLOP] verdict:** none. **Packages flagged as suspicious [SUS]:** none. (`gsd_run query package-legitimacy check` was not run because there is nothing to check; AGENTS.md prefers copying small helpers over new dependencies, D-120.)

## Anchor Verification (CONTEXT claim -> actual)

All paths relative to repo root. Line numbers are from files opened this session.

| CONTEXT anchor | Result | Actual location and note |
|---|---|---|
| `verify-workflow-policy.py` `verify_cited` ~2367 | OK | `def verify_cited` at **2329**; the offline-hostile line is **2367**: `ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", row["cited_sha"], "origin/main"], ...)`. Job match is by display name only (`j["name"] == display[key]`, display for `release.yml` is `f"release-candidate / {name}"`, built at ~2340-2345). Live: `python3 -I .github/scripts/verify-workflow-policy.py --check --verify-cited --root .` printed `FAIL release.yml:candidate-performance: job missing or not successful` and `verify-cited rows=45 failures=1`. |
| self-test mutants ~3598-3632 | OK | `_ledger_mutations()` begins **3568**; release_bound mutants at **3601-3608** (`"ledger: release_bound row under a different key"` ... `"ledger: release_bound row without a sizing basis"`); the VERSION-0.3.0 mutant is **3603-3605** (`"ledger: release_bound row once VERSION is above 0.2.1"`, expects `timeout-ledger-release-bound`). |
| `LEDGER_BOUND_LAST_VERSION` | OK | **2228**: `LEDGER_BOUND_LAST_VERSION = (0, 2, 1)`. Keys **2224-2227** (`LEDGER_RELEASE_BOUND_KEYS`, six). `judge_timeout_ledger` at **2257**, `check_timeout_ledger` **2305**, `_project_version` **2246**. Normal rows: `LEDGER_NORMAL_FIELDS = frozenset({"timeout_minutes", "cited_run_id", "cited_sha", "p50_minutes", "samples", "provisional"})` (**2219**) and the judge enforces `set(row) != LEDGER_NORMAL_FIELDS` (exact set). |
| `verify-release-source-proof.py` `validate_rehearsal_run` ~123-164 | OK | `validate_rehearsal_run` **123-146**; `select_performance_run` **149-165**. It currently checks path, event in `REHEARSAL_EVENTS`, success, branch `rehearsal/{tag}`, repository/fork, head tree equality. It has **no** `pr_head` or `not_after`. |
| `REHEARSAL_TAG:271` | OK, but self-test only | `REHEARSAL_TAG = "v0.2.1"` at **271**; used only in the self-test fixtures (285, 303, 348, 373, 375, 446). Production code takes the tag as a parameter. Making it neutral is cosmetic, not a blocker. |
| `verify-support-ledger.py` `validate_data_v2` ~585 | OK | **582**. First rejection: `if not re.fullmatch(r"0\.2\.[0-9]+", expected_version) or data.get("version") != expected_version:` and the scope must equal the v0.2 scope dict. Also called from `check_ledger_static` (1323), `check_current` (1341), `build_v2_sidecar` (1455) and `create_current_ledger` (1152), so the relaxation must be at the function (one-line regex `0\.[23]\.`), not only in `parse_ledger`. |
| `require_generated` ~2865, `DISCLOSED_LEDGERS`, `check_disclosure_generator` | OK | `DISCLOSED_LEDGERS` **2823-2827**: `("docs/support/v0.2.0.md", None)`, `("docs/support/v0.2.1.md", "v0.2.1")`; `require_generated` **2865** hardcodes `render_v2_ledger(parse_ledger(raw, version), disclosure)`; `check_disclosure_generator` **2903** appends the tree ledger automatically if it is not in the tuple; `self_test_disclosure` **2925**; `render_v2_ledger` **1075**; `load_disclosure` **2780**; CLI `main` **3061**. |
| Sidecar `ledger_blob` | **NAME DRIFT** | There is no key `ledger_blob`. `build_v2_sidecar` (1455) emits `"ledger": {"path": ledger, "git_blob_oid": blob_oid, "sha256": sha256(ledger_raw)}`. Bind on `ledger.git_blob_oid` / `ledger.sha256`. Schema stays 2 (gates hard-require it: `verify-release-gates.sh:256` `if sidecar.get("schema_version") != 2:` and `:423`). |
| `gabbaboy.c` `state_store_host_value` ~4145 | OK, premise differs | **4145**. Callers are tests only: `tests/test_state_codec.c:539,541,543,581` and `tests/test_state_fork.c:769`. |
| `gabbaboy.c` `state_apply` ~4723 | OK | **4723**; `state_validate` **4711**, `state_validate_fields` **4700**, `state_field_kind_valid` **4231**. |
| `release-evidence-lifecycle.sh:277` | OK | Line 277: `"limits": ["DMG-CPU-B deterministic software profile only", "no physical DMG observation", "no Developer ID signature or notarization"],`. Asset-name lists at **52, 62, 71, 88, 108-109, 137-139, 154, 175-181, 199-204, 273-274**; `lifecycle_nightly_gate` **307-328**. |
| `tests/player/CMakeLists.txt:192` | OK | `target_link_libraries(${colour_target} PRIVATE GabbaBoy::core gabbaboy_accept)`. Mutant names at **219, 227** (`gabbaboy-player-mutant-rb-swap`, `-dmg-path`), **250-259** (`test_player_session_mutant_ignores_flag`), **187** (`test_player_colour_mutant_rb_swap`). |
| `verify-phase3-player.sh:471` | OK | `ctest --test-dir "$APP_BUILD" --output-on-failure --no-tests=error -R '^player_' \` then `--output-junit "$APP_BUILD/ctest-player.xml"` and `verify-dmg-baseline.sh ... --inventory player`. |
| `verify-v02-adoption.py` ~587/~260/~719-727 | OK | `check_release_notes` **587**, `perf_disclosure_percent` **573**, `run_self_test_release_notes` **731**, template **~719-727** (`- Instruction count: +@PERCENT@% versus v0.2.0 (receipt: tests/baseline/perf-attribution-v1.json).`), required phrase **260** `("makes no publication claim for v0.2.0", "publication-limit-missing")`, `FALSE_PUBLICATION_CLAIM` **122-126** (`r"\bv?0\.2\.0\s+(?:is|has\s+been|was)..."`), mutant text **~882** `append("v0.2.0 has been published.")`. `tree_identity` **48**; `LEDGER`/`LEDGER_VERSION` derived from the tree at **79-80**. `--release-notes` is run by `release.yml:140` in the `candidate` job. |
| `verify-v03-dispositions.py` `release_readback` | OK, record already closed | `check_readback` **244**, `RELEASE_CLOSURE` **50**, `REQUIRED` **54**. The record `.planning/phases/GB-16-tune-up-and-v0-2-debt-closure/16-DISPOSITIONS.json` is already `closed` for its release-linked rows with tag `v0.2.1` (see Drift 3). |
| `verify-perf-gate.py` | OK, no receipt emitter | Modes today: `--check-limits`, `--evaluate`, `--self-test`, `--emit-attribution`, `--check-attribution`. `evaluate` (409-485) prints one text line `perf-gate pass ratios tracer=... realtime_min=...`; no JSON receipt, no `--verify-receipt`. |
| `host-contract.cmake` ~131-155 | OK | `GBB_UNRELEASED_HOST_PHRASES` **131-147**, `add_test(NAME unreleased_host_entries` **~148**; `doc_contract_unreleased_host_missing_selftest` is registered at **~187**; `doc_no_interop_claims` **223-226** expects `no-interop-claims pass files=6 controls=6`. |
| `docs/native-integration.md` ~148 / ~395 | OK | ~148 `--prefix "$TMPDIR/gabbaboy-v0.2.0"`; ~395 `The tracked [v0.1.0 support ledger](support/v0.1.0.md)`. |
| CHANGELOG top block | OK | `CHANGELOG.md` line 3 `## Unreleased` with four Phase 9 MBC3 bullets, then `## [0.2.1](...)`. |
| `docs/release.md` ~255-258 | OK | Lines 255-258: `The six \`release_bound\` rows ... remain a named Phase 19 entry blocker (RM-027): they must be replaced by verified tree-equality citations before \`VERSION\` exceeds 0.2.1 ...`. Line 6 holds `makes no publication claim for v0.2.0.` (coupled to the adoption pin). Line 44 names `release-performance-receipt.json` (the stale name; adoption line ~250 pins the same literal, so fix both together). |
| `tests/CMakeLists.txt` ~5569-5577 | OK | `GBB_PHASE17_BOUNDARY_SHA "d53ec9c34e42094e6b468f5ca725afe28cb4e819"` and `state_boundary_controls` (`GBB_EXPECT_MIN_VALUE=39`). Untouched. |
| Live facts (CONTEXT specifics) | OK | `origin/main` = `f80bdf54c6c7d81e8e21f0275b43cda6edf6c8c4`; PR #131 head `55ac5b758f902bda60819f67b46e11247120495a`, files `.release-please-manifest.json, CHANGELOG.md, CMakeLists.txt`, `gh pr checks 131` -> `no checks reported`; required checks `["required-native","fixture-repro","preview-package-smoke"]`; rulesets 0; open issues 0; releases `v0.2.1, v0.2.0, v0.1.2, v0.1.0` all non-draft; squash/rebase/merge allowed, `allow_auto_merge: false`. Tag `v0.2.1` -> `b93137f0`, tree `b02c14bb...`; `c6dc575` has the same tree and is NOT an ancestor of main; `113b98c` IS an ancestor; `origin/rehearsal/v0.2.1` = `c6dc575b...`. Run `40257161612` is `release-rehearsal.yml` `workflow_dispatch` on `rehearsal/v0.2.1`, success, jobs include `rehearse-paired-performance-qualification`; run `40332345735` is `release-please.yml` `workflow_dispatch` on `main` at `113b98c`, job `release-candidate / exact-tag-paired-performance-qualification` success. |

## Drift and contradictions (act on these in plan text)

1. **Normal ledger rows have nowhere to put a disclosure (D-04, D-05).** `LEDGER_NORMAL_FIELDS` is an exact set; `sizing_basis` exists only for `release_bound` rows. D-04 says "disclose it in the row's `sizing_basis`". Plan 19-01 must extend the normal-row schema with optional fields `tree_equal_sha`, `cited_tree`, `cited_job_name` **and** an optional free-text field (suggest `disclosure`), and replace `set(row) != LEDGER_NORMAL_FIELDS` with required-subset-plus-allowed-optional logic (keep the duplicate-key and type checks; add mutants for each optional field present alone, e.g. `cited_tree` without `tree_equal_sha`).
2. **Perf-gate has no receipt (D-22).** `ci.yml` job `perf-gate` (line 620) only runs `run-perf-gate.sh --gate`, `--seeded-regression`, `--noop-twin`; there is no `upload-artifact` in it (the fuzz job at ~461-480 uploads `v02-fuzz-${{ github.run_id }}-${{ github.run_attempt }}`). 19-05 must first add a JSON receipt emitter to `verify-perf-gate.py evaluate`, a step in `ci.yml:perf-gate` that uploads it (name pattern `perf-gate-<run_id>-<attempt>`), then the `--verify-receipt` reader. D-22 also does not say which "existing attached receipt" carries the binding; `v02-fuzz-receipt.json` is produced verbatim by a different CI job and verified by `--verify-hosted`, so it cannot be rewritten by the reader. See OQ-2.
3. **Phase 16 disposition record is already closed.** `16-DISPOSITIONS.json` has `receipts.tag = v0.2.1`, `tag_sha = b93137f0...`, all five release-linked rows `closed`, readback committed as `16-release-readback.json` (22 assets, `reconciliation: {verifier, result, compared_with, asset_count: 22}`). `REQUIRED` fixes the exact id set and `check` pins `plan == "16-06"`. So "closes the `verify-v03-dispositions.py` pending rows to pending=0" (D-28) is already true and cannot be the v0.3.0 closure. 19-05 must add a separate entry point (suggest `--check-readback PATH --rev REV [--tag v0.3.0]`) that reuses `check_receipt_file`/`check_readback` and the existing readback schema (`tag, tag_sha, tag_tree, is_draft, is_prerelease, release_id, published_at, url, assets[{name,id,size,digest}], reconciliation, release_run, attach_v02_evidence`), plus controls; PR B then commits a v0.3.0 readback. The existing `v03_dispositions*` CTests stay green and unchanged in meaning.
4. **WR-A05 predicate is already in validation (D-09).** `state_field_kind_valid` (4231) already returns 0 for the same three families during `state_validate`: `if (field->kind == STATE_VALUE_BOOL && raw > 1u) return 0;` / `if (field->kind == STATE_VALUE_COUNT && raw > GBB_INPUT_EVENT_CAPACITY) return 0;` / `if (field->kind == STATE_VALUE_EVENT_KIND && (raw < (uint64_t)GBB_INPUT_STOP_WAKE || raw > (uint64_t)GBB_INPUT_BUTTON_RELEASE)) return 0;`. `state_store_host_value` (4145) is weaker (`if (raw > 1u) return 0;`, `if (raw > SIZE_MAX) return 0;`, `if (raw > (uint64_t)GBB_INPUT_BUTTON_RELEASE) return 0;`) and `state_apply` (4723) has none (`const int v = (int)raw;`, `const size_t v = (size_t)raw;`, `(gbb_input_event_kind)raw`). The real work: one static infallible `state_raw_to_host(address, field, raw)` (switch moved out of `state_apply`), `state_apply` and `state_store_host_value` both call it, `state_store_host_value` keeps its argument checks (tests call it, 5 sites) and may call `state_field_kind_valid` for range. Do NOT `assert` a fallible return. The new negative control is a mutant that removes the range lines from `state_field_kind_valid` (so a body with `BOOL=2` is accepted) and must make a `state_refusal*` test fail; model it on the existing `state_refusal_mutant_*` family (`tests/expected-tests.txt:1477-1483`) built from the immutable `GBB_STATE_SOURCE_REV` source, so the core change must be committed before those tests see it.
5. **IN-01 has no single "test seam flag".** The only guard macro in the file is `GBB_TEST_STATE_HASH_COUNTER` (lines 26, 68), defined only by `tests/test_state_codec.c:4`. 19 test sources plus `tests/CMakeLists.txt`, `tests/cmake/input-clock.cmake` and `verify-cgb-apu-dispositions.py`/`verify-dense-input.py` include `src/core/gabbaboy.c`. Measured: `cc -std=c17 -Wall -Wextra -Iinclude -DGBB_STATE_RELEASE_MAJOR=0 -DGBB_STATE_RELEASE_MINOR=2 -DGBB_STATE_RELEASE_PATCH=1 -c src/core/gabbaboy.c` warns for `STATE_FIELD_TREATMENT` (646), `state_descriptor_max_total_size` (1024), `state_audio_hpf_history_valid` (1046), `state_encode_i64` (4004), `state_crc32` (4048), `state_store_host_value` (4145), `state_record_field` (4787), plus two unrelated warnings at 5896-5897. After the WR-A05 refactor `state_store_host_value` is used by `state_apply` and stops warning only if `state_apply` calls it. Guarding the other six behind a new macro means every includer must define it; the cheaper equivalent is a `GBB_MAYBE_UNUSED` attribute macro. Decide in 19-02 and prove with the same `cc` line (before/after warning count).
6. **RM-031 list is incomplete.** Running `python3 -I tests/scripts/verify-core-linkage.py --check --build-dir build-player` on the existing player tree today prints six violations: `wrong-core` for `gabbaboy-player-mutant-dmg-path`, **`gabbaboy-player-mutant-ppu-follows-cpu`**, `gabbaboy-player-mutant-rb-swap`, `test_player_session_mutant_ignores_flag`; `duplicate-core` (libgabbaboy_core.a 2 times) for `test_player_colour` and `test_player_colour_mutant_rb_swap`. `ppu-follows-cpu` is a real core mutant (library `gabbaboy-player-mutant-core-m1`, `tests/player/CMakeLists.txt:134-152`): its archive name `libgabbaboy-player-mutant-core-m1.a` does not match `MUTANT_CORE = re.compile(r"^libgabbaboy_core_[A-Za-z0-9_]+\.a$")`, and the player adapter still pulls the normal core. D-07 covers the other five. 19-01 must also fix this one (rename the library to `gabbaboy_core_player_mutant_m1` and keep exactly one core on its link line, or exclude the adapter's normal core for that target), and `test_player_colour_mutant_rb_swap` (line 187) needs the `*-playervariant-*` rename too because its name matches `MUTANT_NAME = re.compile(r"(mutant|_p1[0-9]$)")` while it mutates player source only. Prove red-before / green-after with the same command.
7. **D-01 says two pre-PR-A dispatches; D-05 needs none.** D-05 is a citation of existing run `40332345735`. The only required pre-PR-A dispatch is D-06 (`nightly-asan.yml` dry run). A third optional dispatch arises from D-15 (OQ-3).
8. **Retention check vs offline rule (D-04).** The control "a `rehearsal/vX.Y.Z` branch deleted while a row cites its head" needs a ref or object read, while the offline check "never resolves the cited run head". See OQ-1.

Smaller observations (no decision impact): `verify-no-phase-paths.py` allows `.planning/` files to name `.planning/phases` freely (`CLEAN_FILES` has `.planning/phases/GB-16/note.md`), so a v0.3.0 readback under `.planning/phases/...` needs no allowlist row if CTest reads it through `${GBB_LIVE_PHASES_DIR}` (`tests/CMakeLists.txt:16`) rather than a spelled-out path in `tests/`. The consumer round trip in `tests/consumers/{c,cpp}` exists (`gbb_save_state`/`gbb_load_state` at `tests/consumers/c/main.c:39-40`) but the consumer **receipt** records only `BEHAVIORS = ("profile_selection", "probe_info", "rgb555_frame_copy", "rtc_catch_up")` (`tests/scripts/verify-v02-consumers.py:29-34`), so the receipt does not name a state behaviour; adding `state_roundtrip` to `BEHAVIORS` (and the validator's `set(behaviors) == set(BEHAVIORS)`) would bind it.

## Pre-flight experiment (evidence for D-19)

Done in an isolated clone (`git clone --local`, then checkout `f80bdf54`, then `sed` on `CMakeLists.txt` `project(GabbaBoy VERSION 0.2.1` -> `0.3.0` and `.release-please-manifest.json`, scratch commit, `cmake --preset phase1`). Configure succeeds (`tests/CMakeLists.txt` derives `gbb_version_regex` from `PROJECT_VERSION`). Python-only checks then give:

| Check | At VERSION 0.3.0, no ledger/pins/links | Fixed by |
|---|---|---|
| `workflow_policy_check` (`--check`) | `REJECT timeout-ledger-release-bound: release-rehearsal.yml:aggregate: release_bound expired when the project VERSION passed 0.2.1; re-cite it from the release run` | 19-01 (D-04: convert all six `release_bound` rows) |
| `support_ledger_binding`, `v02_support_ledger`, `release_disclosure_generator` (and their `*_controls`) | `no support ledger exists in this release's major/minor scope` | 19-03 (ledger exists) + version PR (render) |
| `v02_adoption_docs`, `v02_game_claims` (+controls) | `verify-v02-adoption fail: support-ledger-missing:0.3.0` | same |
| `state_pin_planning` | `REJECT release-token-mismatch: golden release/format/behavior tokens differ from immutable source`; `state_portable_pins` also needs the built emitter | version PR: regenerate `tests/baseline/state-goldens-v1.json` (`release` triplet in the document, `validate_pin_document` requires `release/format_version/behavior_version`) with the emitter `test_state_codec state_portable_pins` (`verify-state-pins.py:305-318`), plus the hand-authored `release-change` row in `tests/data/state-compatibility.json` (kind handled at `verify-state-pins.py:296-300`; the two existing rows are `pre-first-state-release-evolution` with `tokens_after.release` 0.2.1 and are rejected for relabelling at line 295) |
| `v02_consumer_controls_c/_cpp` | `self-test-package-install-failed` in the scratch tree because nothing was built | not a version failure |
| Pass unchanged at 0.3.0 | `release_window_contract/_controls`, `v03_dispositions*`, `summary_coverage_live`, `ledger_freeze`, `readme_host_mode_contract`, `host_contract_*`, `doc_no_interop_claims`, `unreleased_host_entries`, `no_phase_paths`, `closeout_dispositions`, `release_lifecycle_replay`, `release_nightly_gate`, `release_review_approval`, `v02_delivery_controls`, `perf_attribution*`, `state_boundary_controls` | none |

Not exercised here (needs a build): every compiled test that embeds the release triplet in a state header; run these in the real pre-flight tree. `GBB_STATE_RELEASE_MAJOR/MINOR/PATCH` come from CMake (compiling `gabbaboy.c` without them errors at `gabbaboy.c:755` `#error "CMake must define the validated GabbaBoy state release version"`).

## Version-literal inventory (D-19 "about 11 checker files")

Searched `.github tests cmake CMakeLists.txt README.md docs` for `0.2.1` (excluding captures). Classified by whether the literal breaks or misleads at 0.3.0:

**Must change before or in PR A (production behaviour):**
| File:line | Literal | Action |
|---|---|---|
| `.github/scripts/verify-workflow-policy.py:2228` | `LEDGER_BOUND_LAST_VERSION = (0, 2, 1)` | Keep as is: after D-04 no `release_bound` row remains and the 3603-3605 mutant must still reject one at 0.3.0. Update the comment at 2222-2223 only. |
| `.github/ci-timeouts.json` (5 matches) | `0.2.1` inside `sizing_basis` prose of six rows | Replaced wholesale by D-04 conversion |
| `tests/scripts/verify-v02-adoption.py:260, 122-126, ~882` | `"makes no publication claim for v0.2.0"`, `FALSE_PUBLICATION_CLAIM`, mutant text | Derive from `RELEASE_VERSION`; `docs/release.md:6` changes with it (19-06). Keep `+@PERCENT@% versus v0.2.0` (the perf baseline stays v0.2.0). |
| `tests/scripts/verify-support-ledger.py:582-583` | `0\.2\.[0-9]+` and the "v0.2 ledger" messages | One-line relax + `render_v3_ledger` dispatch in `require_generated`; add the new ledger path to `DISCLOSED_LEDGERS` only after the tag (it is a tag-blob freeze list; the tree ledger is added automatically) |
| `README.md:39`, `docs/preview.md:11` | `docs/support/v0.2.1.md` links | Version PR (links need the ledger to exist: `check_binding` and `LEDGER_VERSION` read the tree) |
| `docs/state-format.md:429`, `docs/release.md` (6 matches) | prose | 19-06 |

**Self-test fixtures only (pass at 0.3.0; leave or make neutral if cheap):** `verify-release-source-proof.py:271`; `verify-version-window.py:436-447`; `verify-state-contract.py:1029,1044,1047,1352`; `verify-v03-dispositions.py:388,398,410,484`; `verify-v02-delivery.py:832,914-921`; `verify-release-gates.py:810,842,932`; `verify-state-pins.py:295,504,510,529,642` (the 295 rule is a historical-row rule, correct to keep); `verify-support-ledger.py` self-tests (lines 165-190, 2940 `ledger_rel = "docs/support/v0.2.1.md"`); `tests/CMakeLists.txt:1442,1473` (comments).

**Do not edit:** `tests/scripts/state_boundary.py:299,363,436` (D-04), `tests/data/state-compatibility.json` historical rows, `tests/data/release-disclosure.json` (`applies_after_version` `0.2.1`, D-11).

Net: only **7** of the ~11 files carry behaviour; the rest are fixtures. The authoritative way to find the rest is the 19-06 pre-flight.

## Architecture Patterns

### System Architecture Diagram

```
 PHASE BRANCH gsd/phase-19-...  (from f80bdf54)
   |  pre-PR-A hosted facts (read-only after the fact)
   |   (a) gh workflow run nightly-asan.yml --ref main -f report_red_dry_run=true   -> run N1 @ f80bdf54
   |   (b) [OQ-3] gh workflow run perf-attribution.yml --ref main                   -> artifact receipt
   v
 19-01 ledger citations (tree_equal_sha/cited_tree/cited_job_name) + RM-031 linkage
 19-02 CI/doc hardening + WR-A05 core refactor           } W1 (19-02 after 19-01: shared files)
 19-03 claims data + render_v3 + validators + notes rules }
 19-04 rehearsal binding + pre-tag gate + window rule + lifecycle replay coverage (W2)
 19-05 perf-gate receipt, host smoke, readback entry, profile string (W3)
 19-06 docs + pre-flight on scratch 0.3.0 tree + PR A (W4)
        |
        |  PR A: gh pr create (ci/test/chore title)  -> exact-head CI -> gh pr merge --squash --match-head-commit
        v
 main (one push) --> release-please regenerates PR #131 (no checks, GITHUB_TOKEN)
        |
 WINDOW (no main push of any kind)                                   D-26
   1. on #131 branch: render ledger/pins, release-change row, links, preface  = head H
   2. push H -> required CI on PR + push H:refs/heads/rehearsal/v0.3.0 -> R1 (release-rehearsal) green
   3. verify-version-window.py --digest (fills R1, CI run) -> commit record only = W
   4. push W to #131 branch; fast-forward rehearsal/v0.3.0 to W (after R1 completes; cancel-in-progress)
        -> required CI @W, R2 (release-rehearsal), nightly-asan @W on rehearsal branch
   5. pre-tag gate (pull_request): window --check --rev W --base main + validate_rehearsal_run(R2)
   6. --release-notes on the PR body; gh pr merge 131 --squash --match-head-commit W; assert tree(S)==tree(W)
        v
 TAG v0.3.0 at S (release-please.yml on main push)
   release.yml: candidate -> candidate-macos/-windows -> candidate-corpus -> candidate-fuzz (+perf-gate receipt)
                -> candidate-performance -> attach-v02-evidence -> platform-manifest -> publish (nightly-gate, final gate)
   post-tag defence: validate_rehearsal_run(pr_head, not_after) in candidate step 1 and nightly-gate
        v
 PR B (docs/chore): version-window inactive, readback receipt, REL-01 traceability, SUMMARYs; STOP.
```

### Recommended Project Structure (new or changed files)
```
tests/data/support-claims-v0.3.json        # NEW managed input (19-03)
tests/scripts/verify-support-ledger.py     # render_v3_ledger, claims validator, new CLI modes (19-03)
tests/scripts/verify-v03-dispositions.py   # --check-readback entry (19-05)
tests/scripts/verify-perf-gate.py          # emit/verify receipt (19-05)
.github/scripts/verify-release-source-proof.py   # pr_head / not_after (19-04)
.github/workflows/<pre-tag gate>           # NEW workflow or ci.yml job (19-04, discretion)
tests/data/version-window.json             # PR B resets inactive; W commit sets active
.planning/phases/GB-19-.../19-release-readback.json   # PR B (19-07)
```

### Pattern 1: Trusted judge, data subject
Judges run from `${{ github.event.repository.default_branch }}` and read the subject tree as data (`release-rehearsal.yml:334-372`, `release-please.yml:53`). New gates must copy this; any step that executes subject code is rejected by policy.

### Pattern 2: Refusal with discriminating controls
`REJECT code: reason` exit 1; each control pairs with an unrelated positive control in the same run so a crash cannot pass as a rejection (`self_test_disclosure`, `verify-support-ledger.py:2925`). The CTest regex plus `GBB_EXPECT_MIN_KEY/VALUE` is a parsed minimum: adding controls is allowed, dropping one fails.

### Pattern 3: Policy mutants
`_m(label, workflow, anchor-region, old, new, expected_code)` in `verify-workflow-policy.py` (examples 2915-2925, 3540-3640). Every new step/job/permission/trigger needs an exact-set pin and a mutant. The `workflow_policy_controls` floor is a parsed minimum in `tests/cmake/ci-lanes.cmake:93-97`: **394 POSIX / 375 Windows** today. Raise both when mutants are added (Windows counts the POSIX-only red-report replay out: 19 fewer).

### Pattern 4: New gate without a ledger row
A new job cannot cite a completed run, so `release-please.yml:53` `version-window-gate` has no job-level `timeout-minutes` and bounds every step instead (`docs/release.md:171-174`). The D-18 pre-tag gate should copy that (and then needs no `ci-timeouts.json` row).

### Pattern 5: Generator fixed point
Tracked ledgers must equal `render(parse(ledger))`; a hand edit fails `ledger-not-generated`. Managed inputs are listed in the window record (`REQUIRED_MANAGED_INPUTS` in `verify-version-window.py`: `tests/data/release-disclosure.json`, `tests/scripts/verify-support-ledger.py`, `release-please-config.json`). **`tests/data/support-claims-v0.3.json` must be added to `REQUIRED_MANAGED_INPUTS`** (and to the self-test fixture list at `verify-version-window.py:442-447`), otherwise a claims edit after review would not end the freeze.

### Anti-Patterns to Avoid
- **Running replay/gate/pin CTests on uncommitted work.** `release_lifecycle_*`, `release_review_*`, `release_nightly_*`, `state_*` pin/mutant tests read `GBB_STATE_SOURCE_REV` = configure-time `git rev-parse HEAD` (`tests/CMakeLists.txt:4937-4943`; the lifecycle foreach at ~5513-5538). Commit, then re-run `cmake --preset phase1` before the verify command.
- **A checker that reads tags or live refs** (D-20/D-105). `ci.yml` at the tag commit fetches tags; a tag-reading rule would strand `candidate-fuzz`.
- **Adding `if(NOT WIN32)` tests casually.** Each needs entries in `tests/expected-tests.txt`, the `if(WIN32)` `list(REMOVE_ITEM ...)` in `cmake/ExpectedTests.cmake:16-134` and the `sed` filter plus self-test list in `.github/scripts/verify-test-inventory.sh:6-150`. Make new checks python-only and cross-platform to avoid the triple edit.
- **Hand-editing generated content** (CHANGELOG sections, ledger, goldens) in PR A.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Tree-equality binding of a rehearsal to a tag | New comparator | Extend `validate_rehearsal_run` / `git_tree_of` (`verify-release-source-proof.py:100-146`) | D-04, D-18; one predicate for judge, nightly gate and candidate |
| Ledger renderer | A second formatter | Copy `render_v2_ledger` (1075) to `render_v3_ledger`, insert one claims section | Byte-exact fixed points for v0.2.x |
| Managed-input validation | Ad hoc JSON checks | Mirror `validate_disclosure` (2731-2780) shape: exact key sets, `ASCII` text regex, bounds | Same hostile-input discipline |
| Release API replay | New transport | `verify-release-lifecycle.py` stand-in `gh` + `tests/data/release-api/captured.json` | Add captures, do not add a harness |
| Window digests | New hash scheme | `verify-version-window.py --digest` | Already content-bound, no clock |
| Readback reconciliation | New checker | `check_receipt_file`/`check_readback` in `verify-v03-dispositions.py` + `verify-published-release-assets.py` | D-23 |
| Sibling-style helper for per-test timeouts | Custom sleeps | `tests/ci/test-budget-allowlist` ratchet | Existing rule set |

**Key insight:** every release-path decision in this repo is already encoded as an exact-set pin plus a mutant. New behaviour is cheap only when it extends an existing predicate; a parallel path doubles the pin surface.

## Runtime State Inventory (remote and generated state; this phase is a version bump, not a rename)

| Category | Items Found | Action Required |
|---|---|---|
| Stored data | `tests/baseline/state-goldens-v1.json` embeds the release triplet; `tests/data/state-compatibility.json` holds two `pre-first-state-release-evolution` rows with release 0.2.1; `.release-please-manifest.json` `{".": "0.2.1"}`; `CMakeLists.txt:2` `project(GabbaBoy VERSION 0.2.1 LANGUAGES C) # x-release-please-version` | Version PR regenerates goldens (data migration) and adds a `release-change` row; PR A must not touch them (D-09 control: goldens and pins byte-identical) |
| Live service config | PR #131 body (becomes release notes; overwritten on regeneration); branch `release-please--branches--main--components--GabbaBoy`; `rehearsal/v0.2.1` (head `c6dc575`, cited by rows) and five `rehearsal/phase-15.1-*` branches; required checks list in GitHub settings (3 contexts); immutable releases OFF; no rulesets | Keep `rehearsal/v0.2.1` (D-30); create `rehearsal/v0.3.0` in the window; the new pre-tag gate is NOT a required check (a repo-settings change is owner-only, see OQ-5) |
| OS-registered state | None found (no launchd/cron on this host for the project; `nightly-asan.yml` has a GitHub `schedule` cron `17 3 * * *`) | None |
| Secrets/env vars | `GITHUB_TOKEN` only; no new secrets; `.env.local` ignored; no key names change | None |
| Build artifacts | Local `build/`, `build-player/` etc. are ignored; hosted artifacts `state-pins-{linux,macos,windows}-<run>-<attempt>` (ci.yml 187/296/398), `v02-fuzz-<run>-<attempt>`, `rehearsal-performance-<run>-<attempt>`, `release-evidence-*` | New: `perf-gate-<run>-<attempt>` (19-05) |

## Common Pitfalls

### Pitfall 1: Shallow trusted-judge checkout cannot do git-object checks
**What goes wrong:** D-04's offline rule needs `tree(tree_equal_sha)` and "ancestor of main". In `release-rehearsal.yml` job `judge`, both `trusted-judge` (default branch) and `subject` are checked out with default depth (lines 334-372: `actions/checkout@... with: ref: ..., path: trusted-judge, persist-credentials: false`, no `fetch-depth`), and the policy runs `git` with `cwd=root` (the `subject` dir). The check would fail or silently skip.
**How to avoid:** set `fetch-depth: 0` on the `trusted-judge` checkout and give the policy a `--git-root` (or always run its ancestry/tree git calls in the checkout that holds history); add the pin and a mutant. Alternatively skip git-object rules in `--release-head` mode and rely on the pre-flight; prefer the first.
**Warning signs:** `fatal: Not a valid object name` in the judge job on the first R1.

### Pitfall 2: `release_lifecycle_controls` is at 51 s of a 60 s TIMEOUT
**What goes wrong:** D-21 adds replay scenarios; the controls test (measured 51.24 s locally; `release_lifecycle_replay` 23.10 s) times out, or under the 3x sanitizer scaling exceeds the budget. The TIMEOUT ratchet (`tests/scripts/verify-test-budget.py`) rejects a raised ceiling and bounds a NEW row at `NEW_ROW_CEILING_MAX` = 180 with a ref that already resolves **at the base commit** and is not a ref already backing a base row (so `D-120` does not resolve on main; use a LESSONS heading or DECISIONS id present at `f80bdf54` that no allowlist row uses).
**How to avoid:** split the controls into two CTests (like the `foreach` at `tests/CMakeLists.txt:5513`), or measure and add one allowlist row. Same for `workflow_policy_controls` (49.90 s of 180, fine) and `v02_delivery_controls` (27.51 s).

### Pitfall 3: Timeout-ledger floors and parsed minimums
`workflow_policy_controls` floor (394/375) and each `release_*_controls` minimum only ratchet up. Compute the new floor from an actual run (`PASS: workflow policy self-test negative_controls=N`), do not guess.

### Pitfall 4: Squash-merge changes the SHA, not the tree
Receipts bind by tree: `validate_rehearsal_run` accepts `head != source_sha` only when `git_tree_of` is equal. R1 (head H) and R2 (head W) differ by the record file, so tree(H) != tree(W): **if R2 is red, the newest successful run is R1 and the tree check refuses it** (`rehearsal run head tree differs from the tagged tree`). D-17's "never fall back to R1" is therefore already structural; add the explicit control.

### Pitfall 5: `--release-head` and `rehearsal/**` concurrency
`release-rehearsal.yml` has `concurrency: cancel-in-progress: true` per ref. Pushing W while R1 is running cancels it. Order is R1 complete -> `--digest` -> commit W -> fast-forward the branch (D-17 step 3).

### Pitfall 6: Release-please regenerates the PR on any main push
Any commit to main in the window (planning commits included) rewrites the PR body and branch. D-26 forbids it; the existing `version-window-gate` job fails when a freeze is broken. Do all planning bookkeeping for 19-07 on the phase branch or in PR B.

### Pitfall 7: Player-lane filter widening and the junit inventory
`verify-phase3-player.sh:471` feeds one `--output-junit` file to `verify-dmg-baseline.sh --inventory player`. In `cmake/VerifyDmgBaseline.cmake:425-448` extra observed keys are findings only for the `mooneye|acceptance|bench` sections, `inventory` reports `removed:` only, so extra `core_linkage_*` rows probably do not fail it. Safer: a **separate** `ctest ... -R '^core_linkage_'` invocation without the junit. Prove either choice with a seeded junit.

### Pitfall 8: Notes Ir figure
`perf_disclosure_percent` takes the max ratio over three ROMs and every repeat in `tests/baseline/perf-attribution-v1.json` (`selection.head` = `711f4fd7...`, gives +8.3%). The regression gate on `4ace5e37` says about 1.095. Notes that say +8.3% would be stale; see OQ-3.

### Pitfall 9: `GITHUB_TOKEN` PRs trigger no workflows
#131 shows `no checks reported`. Required checks start only when the agent pushes a non-release-please commit (H). Pushing W again triggers them at W. `allow_auto_merge` is false, so there is no `--auto`; merge is an explicit `gh pr merge`.

## Code Examples

### Normal ledger row with the D-04 fields (proposed shape)
```json
"release-rehearsal.yml:performance": {
 "timeout_minutes": 45,
 "cited_run_id": 40257161612,
 "cited_sha": "c6dc575b6a84cf51a56688948fce9241ba323400",
 "p50_minutes": "0.14",
 "samples": 1,
 "provisional": false,
 "tree_equal_sha": "b93137f00d07b11dc74e40330e0ddf6029c0677d",
 "cited_tree": "b02c14bbdc9be80b7aa6b6145cb8b89331388cca",
 "cited_job_name": "rehearse-paired-performance-qualification",
 "disclosure": "Predecessor-name citation: the job was renamed to rehearse-advisory-paired-performance-observation; the old sample was a reuse path."
}
```
Facts behind it: run `40257161612` head `c6dc575b...` has tree `b02c14bbdc9be80b7aa6b6145cb8b89331388cca`, the same tree as `b93137f0` (the v0.2.1 tag, an ancestor of main); `c6dc575` is not an ancestor. `p50_minutes` is `ceil(seconds/60 * 100)/100` of the cited job (`verify_cited`): the cited job ran 02:02:59 to 02:03:07 = 8 s, so 0.14, and `ceil(2 x 0.14) = 1 <= 45` holds. Recompute each row the same way. Job durations for run `40257161612` (read-only GET): perf-gate 46 s, fuzz 2m14s, corpus 12m11s, paired-performance 8 s, package 13 s, aggregate 23m40s, trusted-judge 9 s.

### Offline tree-equality rule sketch
```python
# Source: pattern of git_tree_of in verify-release-source-proof.py:100-111
tree = git(["rev-parse", "--verify", f"{row['tree_equal_sha']}^{{tree}}"], cwd=git_root)
if tree != row["cited_tree"]: raise Reject("timeout-ledger-tree-mismatch", key)
if not is_ancestor(row["tree_equal_sha"], "origin/main"): raise Reject("timeout-ledger-anchor-not-on-main", key)
```

### D-18 binding additions (shape)
`validate_rehearsal_run(run, tag, source_sha, repo, tree_of, pr_head=None, not_after=None)`: `pr_head` = the version PR's head at merge from `GET repos/{repo}/commits/{merge_sha}/pulls` -> `head.sha`; `not_after` = `merged_at`; the pinned reused attempt's max `completed_at` from `GET repos/{repo}/actions/runs/{id}/attempts/{n}/jobs` must be <= `merged_at`. Codes: `rehearsal-not-version-pr-head`, `rehearsal-postdates-tag`. Note a squash merge makes `head_sha` of R2 (`W`) the PR head and S the merge commit; `commits/{S}/pulls` lists the PR.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Post-tag discovery of release defects (D-112: three owner-waived gap rounds) | All hardening before the tag; pre-flight a synthetic tree; one gap slot | D-120 | Pre-flight and pre-tag gate are the substance of this phase |
| `release_bound` ledger rows with version expiry | General tree-equal citation, no expiry rule | D-120 | `release_bound` machinery stays but must never hold a row at 0.3.0 |
| Hand-inserted ledger prose | Generator fixed point from managed input | Phase 17 RM-028 | Claims must be data |

**Deprecated/outdated:** `docs/release.md` `release-performance-receipt.json` (use `v02-performance-receipt.json`); `docs/native-integration.md` v0.1.0 ledger link and `gabbaboy-v0.2.0` prefix.

## Plans: files, CTests, wiring and overlaps

Legend: **N** = new file, **E** = edit. "Reg" = registration points to touch if a CTest name is added: `tests/CMakeLists.txt` (or a `tests/cmake/*.cmake` include), `tests/expected-tests.txt` (one name per line; the file is append-ordered, 1678 lines today, so parallel plans appending at the tail will textually conflict), and, only for non-Windows tests, `cmake/ExpectedTests.cmake` `if(WIN32)` list + `.github/scripts/verify-test-inventory.sh` (sed filter and `_self_test_platform_filter_cases` list). Player tests also go in `tests/player/expected-tests.txt` (108 lines). Tests that read `.planning/` need `LABELS planning` (`tests/scripts/verify-planning-labels.py`, CTest `planning_labels`).

### 19-01 (W1) Entry blockers: D-04, D-05, D-06, D-07
Files: `.github/ci-timeouts.json` E (six `release_bound` rows -> normal rows; `release.yml:candidate-performance`; `nightly-asan.yml:report-red` re-cite); `.github/scripts/verify-workflow-policy.py` E (schema 2219-2300, `verify_cited` 2329-2395, mutants 3568-3640, judge job git-root); `.github/workflows/release-rehearsal.yml` E (judge checkout depth, Pitfall 1); `tests/cmake/ci-lanes.cmake` E (floor 394/375); `tests/player/CMakeLists.txt` E; `tests/scripts/verify-phase3-player.sh` E; `docs/release.md` is owned by 19-06 (do not edit here; hand the 255-258 paragraph to 19-06).
Reuse: `workflow_policy_check`, `workflow_policy_controls` (negative controls for D-04 live in `_ledger_mutations`); `core_linkage_links` / `core_linkage_controls` for D-07 (red-before evidence reproduced above).
New CTest: none required. Hosted dispatch (before PR A): D-06.
Negative controls to write (D-04): tree mismatch; `tree_equal_sha` not on main; `cited_job_name` absent from the run (online `--verify-cited`, cannot be CTest; give it a stub-`gh` self-test mode so the control is automated); ceil(2 x p50) above timeout; scratch VERSION 0.3.0 passes `--check --release-head` exit 0; branch-retention (OQ-1); optional field alone is rejected.

### 19-02 (W1, after 19-01) Review leftovers: D-08, D-09, D-10
Files: `.github/workflows/ci.yml` E (budget step at line 146: run `git show "$BUDGET_BASE:tests/scripts/verify-test-budget.py"` copy; head copy `--self-test` as a separate step; `persist-credentials: false` where missing); `.github/workflows/libbet-repro.yml` E; `.github/scripts/verify-workflow-policy.py` E (`CI_BUDGET_COMMANDS` ~1337-1340, `READONLY_WORKFLOWS` **1536** add `libbet-repro.yml`, mutants ~2915); `tests/scripts/verify-v02-fuzz.py` E (`SOURCE_FILES` at 45-63: add `include/gabbaboy/gabbaboy.h`, and `src/core/gabbaboy_test.h` only if it exists and the probes include it; IN-05); `docs/release.md` retry paragraph (IN-07: hand to 19-06) and `docs/state-format.md` limitation note (IN-02); `src/core/gabbaboy.c` E; tests under `tests/test_state_*.c` E as needed; `tests/scripts/verify-state-mutants.py` or `tests/CMakeLists.txt` `state_refusal_mutant_*` E for the new mutant.
Overlap with 19-01: `verify-workflow-policy.py` and `ci-lanes.cmake` floor. Overlap with 19-03: `tests/CMakeLists.txt`, `tests/expected-tests.txt` tail.
Reuse: `state_refusal`, `state_refusal_controls`, `state_refusal_mutant_*`, `state_canonical`, `state_semantic_bounds`, `state_codec_mutant_controls`, `state_portable_pins`, `state_pin_controls` (D-09: continuation rows (153), `state-goldens-v1.json` and pins stay byte-identical), `v02_fuzz_controls`, `test_budget`, `test_budget_controls`, `workflow_policy_*`.
Perf: the load path is not in the tracer workload; the PR-A head's own `ci.yml:perf-gate` run is the ratio check (compare with 1.095, limit 1.10).

### 19-03 (W1) Ledger: D-11..D-16
Files: `tests/data/support-claims-v0.3.json` N; `tests/scripts/verify-support-ledger.py` E (validator branch, `render_v3_ledger`, `require_generated` dispatch, `check_disclosure_generator`, CLI modes, self-tests, claims derived-value checks reading `tests/data/state-forks.json` (`expected_case_count`: 153 [VERIFIED: file read]), `tests/baseline/state-goldens-v1.json`, `docs/host-contract.json` (keys `exit_codes, cadence, rtc_wall_clock, save_formats`), `tests/expected-tests.txt` + `tests/player/expected-tests.txt`, and the `if(WIN32)` list in `cmake/ExpectedTests.cmake`); `tests/scripts/verify-v02-adoption.py` E (version-aware phrases, v0.3 release-notes rules at 587, mutants in 731+, unscoped-claim patterns in README/preview/notes); `tests/scripts/verify-no-interop-claims.py` E (`FILES` line 39 add `docs/support/v0.3.0.md` only when it exists: do the widening with the file list computed from the tree ledger; `PATTERN` line 42 widen beyond mGBA to SameBoy|BGB|BESS; the CTest expects `files=6 controls=6`, so bump in `tests/cmake/host-contract.cmake:225-226`); `tests/CMakeLists.txt` E (ledger contract region 1420-1480); `tests/scripts/verify-version-window.py` E (`REQUIRED_MANAGED_INPUTS` + fixture list: this file is also in 19-04's set; make the edit here and tell 19-04) ; docs note for D-16 (19-06).
Reuse: `v02_support_ledger`, `v02_support_ledger_controls` (note its regex pins `positive=1 rejected_controls=5 controls=changed-covered-input,...`: do not change that output), `release_disclosure_generator`, `release_disclosure_controls` (min controls 15), `support_ledger_binding*`, `v02_adoption_docs*`, `doc_no_interop_claims`.
New CTests (proposal; python-only, label `v02`, TIMEOUT <= 60): `support_claims` (`--check-claims`), `support_claims_controls` (`--self-test-claims`, parsed minimum). Reg: `tests/CMakeLists.txt` via `gbb_add_ledger_contract`, `tests/expected-tests.txt`; no WIN32 edits.
The 11 controls of D-14 map to codes `claim-scope-missing`, `claim-platform-unpackaged`, `claim-platform-unexercised`, `claim-unbacked`, `claim-evidence-unregistered`, `claim-corpus-drift`, `claim-pins-stale`, `non-claim-missing`, `ledger-not-generated`, adoption patterns, interop widening.
Recommended claim wording for byte equality: claim "each of linux-x64, macos-arm64, windows-x64 verified the committed goldens in its own native lane (`state_portable_pins`)" and do not claim cross-platform byte identity beyond that; `docs/state-format.md` (~435) already says a local receipt does not qualify three platforms together and D-13 requires the three `state-pins-*` artifacts from one exact-source run for the stronger claim, which no job reads today.

### 19-04 (W2) Rehearsal binding and window: D-17, D-18, D-20, D-21
Files: `.github/scripts/verify-release-source-proof.py` E (`validate_rehearsal_run` 123, `select_performance_run` 149, CLI 527-560, self-test 271-446); `.github/workflows/release.yml` E (`candidate` step ~1-3 binding; `candidate-performance` select step at 1159-1181; `actions: read` exists at job `candidate` permissions); `.github/scripts/release-evidence-lifecycle.sh` E (`lifecycle_nightly_gate` 307-328); `.github/workflows/release-rehearsal.yml` E (refuse to run if `vX.Y.Z` exists remotely: needs `git ls-remote`/API in `corpus` or `judge`; mind read-only token `permissions: contents: read`); new pre-tag gate workflow or `ci.yml` job E/N; `tests/scripts/verify-version-window.py` E (D-20 rule inside `check_tracked` 379-392: an `active` record is legal only if `record.release_version == tree_version(repo, head)`, reading the tree only; plus controls with a stale active record after a version bump); `tests/data/version-window.json` (stays inactive in PR A); `tests/scripts/verify-release-lifecycle.py` E and `tests/data/release-api/captured.json` + `SOURCES.md` E (D-21: add captures for `commits/{sha}/pulls`, `actions/runs/{id}/attempts/{n}/jobs`, plus every endpoint the post-tag path uses; refresh with read-only GETs of published v0.2.1, sanitized; digest line `- captured.json sha256:` and byte bound 262144 in SOURCES.md; `FORBIDDEN_TEXT` at line 164); `.github/scripts/verify-workflow-policy.py` E (pins and mutants for every new step); `tests/cmake/ci-lanes.cmake` floor; `tests/CMakeLists.txt` minimums for `release_lifecycle_controls` (95), `release_window_controls` (regex `controls=([2-9][0-9]|[1-9][0-9][0-9]+)`).
Reuse: `release_window_contract`, `release_window_controls`, `release_lifecycle_replay` (regex `publish_decisions=2 live_mutations=0`, `uploads` min 7), `release_lifecycle_controls`, `release_nightly_gate` / `release_nightly_controls` (min 37), `workflow_policy_*`.
D-21 method: enumerate endpoints by grepping `gh api`, `gh run`, `gh release` in `release.yml`, `release-evidence-lifecycle.sh`, `verify-release-gates.sh`, `verify-release-source-proof.py`, `produce-release-evidence.sh`; require a replay scenario per endpoint; the lifecycle replay refuses unexpected endpoints already (`c_unexpected_endpoint_in_script`).

### 19-05 (W3) Receipts and readback: D-22, D-23, D-24
Files: `tests/scripts/verify-perf-gate.py` E (emit + `--verify-receipt`); `tests/scripts/run-perf-gate.sh` E (`evaluate_tree` 146-199 writes the receipt); `.github/workflows/ci.yml` E (`perf-gate` job: upload step); `.github/workflows/release.yml` E (`candidate-fuzz` 1056-1131 reads the perf-gate artifact of the same run; `candidate` and `candidate-macos` host smoke steps next to 405-431 / 690-700); `.github/workflows/release-rehearsal.yml` E (`package` job 186-243: host smoke after the consumers step at ~231); `tests/scripts/test_installed_host.py` E (takes `--prefix --work --source-contract`; add a machine-readable result `{result, continuation, preload}`); `tests/scripts/verify-v02-consumers.py` E (call it, embed `host_smoke`; its `--self-test --consumer c|cpp` runs are 600 s CTests: keep new work in the shared static portion); `tests/scripts/verify-v02-delivery.py` E (`validate_consumer_receipt` at 222: require `host_smoke`; the check ignores unknown keys today, so this is additive; update its self-test mutants); `.github/scripts/release-evidence-lifecycle.sh` E (line 277 profile string; receipts; asset lists only if a new asset is added); `.github/scripts/verify-release-gates.sh` E (`REQUIRED_ASSETS` line 21 only if a new asset); `tests/scripts/verify-v03-dispositions.py` E (readback entry, Drift 3); `tests/scripts/verify-release-lifecycle.py` E (extend `FORBIDDEN_TEXT` scan to the committed readback and receipt JSON); `.github/scripts/verify-workflow-policy.py` E.
Overlap with 19-04: `release.yml`, `release-rehearsal.yml`, `release-evidence-lifecycle.sh`, policy, lifecycle verifier, `captured.json`. This is why W3 follows W2.
Reuse: `perf_*` tests in `tests/cmake/perf.cmake` (gate, seeded regression, no-op twin, `perf_attribution`), `v02_delivery_controls`, `v02_consumer_controls_*`, `installed_host_smoke` (`tests/cmake/host-contract.cmake:19`), `v03_dispositions*`.
Sidecar: stays schema 2 (Anchor Verification row); if the planner finds it must change, 19-05 owns `verify-release-gates.sh:256,423`, `release.yml:1038-1045` and the replay and then depends on 19-03.
Hosted-only evidence: the perf-gate receipt and host-smoke-on-archive run only on GitHub; locally prove with fixture receipts (the emitter/validator self-test) and the lifecycle replay.

### 19-06 (W4) Pre-flight, docs and PR A: D-19, D-25
Files: `docs/release.md` E (intro, upgrade/rollback, operator sequence D-17/D-18/D-26, stale receipt name line 44, dispatch-input text, 255-258 paragraph, line 6 publication phrase, IN-07 retry paragraph); `docs/native-integration.md` E (~148, ~395, add link check); `docs/support/unreleased.md` E ("reconciled into v0.3.0" stub: keep the phrases `unreleased_host_entries` requires or retarget that test); `tests/cmake/host-contract.cmake` E (131-155 `GBB_UNRELEASED_HOST_PHRASES`, `unreleased_host_entries` ~148, `doc_contract_unreleased_host_missing_selftest` ~187, `GBB_REV_WIRING_TESTS` list ~232 if names change); `CHANGELOG.md` E (move the stale `## Unreleased` Phase 9 block under `## [0.2.0]`) plus a new check that the first `## ` heading is a version (python-only CTest, e.g. `changelog_first_heading` + `_controls`); a docs link check CTest; `tests/scripts/verify-v02-adoption.py` is 19-03's; scratch pre-flight tree and the `release-change` row draft (kept outside the tree or under the phase directory until the window).
Reg: `tests/CMakeLists.txt` + `tests/expected-tests.txt`, python-only.
Do not edit in PR A: `README.md` / `docs/preview.md` ledger links (version PR), `tests/baseline/state-goldens-v1.json`, `tests/data/state-compatibility.json`, `.release-please-manifest.json`, `CMakeLists.txt` version.
PR A steps: see Autonomy section.

### 19-07 (W5) Window, release, PR B
Files in the window (on the #131 branch): `docs/support/v0.3.0.md` (generated), `tests/baseline/state-goldens-v1.json` (regenerated), `tests/data/state-compatibility.json` (+ `release-change` row), `README.md:39`, `docs/preview.md:11`, `docs/release.md` and `docs/native-integration.md` links, `CHANGELOG.md` preface under `## [0.3.0]`, `tests/data/version-window.json` (record, W). PR B: `tests/data/version-window.json` (inactive), `.github/ci-timeouts.json` optional re-cite, readback JSON, planning files. Nothing else.

### 19-08 Reserved gap slot: created only for a post-tag failure outside the tagged tree (D-27).

## Autonomy map and `gh` commands

Per AGENTS.md, PRs, merges after required checks and releases are authorized in the active phase and there is no GitHub-specific human step; the only owner-only items are the three in CONTEXT ("Owner-only items"). So every plan can be `autonomous: true` with **machine preconditions** (not UAT). The irreversible step is the squash merge of #131 (creates the tag). Recommend a single automated "go/no-go" script assertion before it and explicit stop-and-hand-off triggers: defective tagged tree, any Ir limit widening, any second post-tag failure.

| Step | Local or remote | Write? | Exact commands |
|---|---|---|---|
| Edit/verify plans 19-01..19-06 | local | no | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '<regex>' --output-on-failure --no-tests=error && bash .github/scripts/verify-test-inventory.sh --self-test` |
| Read-only facts | remote GET | no | `gh api repos/{owner}/{repo}/actions/runs/<id>`, `.../jobs?per_page=100`, `gh pr view 131 --json headRefOid,files,body`, `gh pr checks 131`, `gh api repos/{owner}/{repo}/branches/main/protection/required_status_checks -q .contexts`, `python3 -I .github/scripts/verify-workflow-policy.py --check --verify-cited --root .` |
| WR-C03 dispatch (before PR A) | remote | dispatch | `gh workflow run nightly-asan.yml --ref main -f report_red_dry_run=true`; then `gh run list --workflow nightly-asan.yml --branch main --limit 3 --json databaseId,headSha,event,conclusion,status`; `gh run watch <id> --exit-status`; re-cite `report-red` with `cited_run_id`, `cited_sha` = `f80bdf54...` (or main's head at dispatch), `provisional: false` |
| Optional perf-attribution dispatch (OQ-3) | remote | dispatch | `gh workflow run perf-attribution.yml --ref main`; `gh run download <id> --name perf-attribution-receipt-<id>-<attempt>`; commit as `tests/baseline/perf-attribution-v1.json`; hosted cap 150 min |
| Push phase branch, open PR A | remote | push/PR | `git push -u origin gsd/phase-19-qualified-v0-3-0-release`; `gh pr create --base main --title "ci(phase-19): <summary>" --body-file <file>` (non-releasable type, D-03) |
| Wait for exact-head CI | remote | no | `gh pr checks <n> --watch`; required contexts `required-native`, `fixture-repro`, `preview-package-smoke` |
| Merge PR A | remote | merge | `gh pr merge <n> --squash --match-head-commit <head-sha> --subject "ci(phase-19): <summary> (#<n>)"` (squash is pre-authorized when exact-head CI is green; no `--auto`, repo disallows it) |
| Observe #131 regeneration | remote | no | `gh pr view 131 --json headRefOid,body,title,files`; `gh run list --workflow release-please.yml --branch main --limit 2` |
| Version content on #131 | remote | push | `git fetch origin release-please--branches--main--components--GabbaBoy`; branch from it; commit generated content; `git push origin HEAD:release-please--branches--main--components--GabbaBoy` (non-force; triggers the PR CI) |
| R1 | remote | push/dispatch | `git push origin <H>:refs/heads/rehearsal/v0.3.0` (push trigger `branches: ['rehearsal/**']`) or `gh workflow run release-rehearsal.yml --ref rehearsal/v0.3.0`; `gh run watch <id> --exit-status` |
| Record | local | no | `python3 -I tests/scripts/verify-version-window.py --rev <H> --base <main-sha> --digest --body <body-file> --pull-request 131 --ci-run-id <id> --rehearsal-run-id <R1> > tests/data/version-window.json`; commit as W; `--check tests/data/version-window.json` at W |
| R2 + nightly at W | remote | push/dispatch | after R1 completes: `git push origin <W>:refs/heads/rehearsal/v0.3.0`; `gh workflow run nightly-asan.yml --ref rehearsal/v0.3.0`; `gh run list --workflow nightly-asan.yml --branch rehearsal/v0.3.0 --json databaseId,headSha,conclusion,createdAt` |
| Pre-tag gate | remote | no | `gh run list --workflow <gate>.yml --branch release-please--branches--main--components--GabbaBoy --limit 3` then `gh run view <id> --json conclusion,headSha` |
| Notes check | local | no | `gh pr view 131 --json body -q .body > notes.md && python3 -I tests/scripts/verify-v02-adoption.py --release-notes notes.md` |
| Update PR body (preface) | remote | edit | `gh pr edit 131 --body-file notes.md` (then `--digest` after the edit; body is part of the record) |
| **Merge #131 (creates the tag)** | remote | merge, irreversible | `gh pr merge 131 --squash --match-head-commit <W>`; then `git fetch origin main && test "$(git rev-parse origin/main^{tree})" = "$(git rev-parse <W>^{tree})"` |
| Watch release | remote | no | `gh run list --workflow release-please.yml --branch main --limit 3`; `gh run watch <id> --exit-status`; `gh release view v0.3.0 --json isDraft,assets,tagName` |
| Readback | remote GET -> local file | no | `gh api repos/{owner}/{repo}/releases/<id>`, `.../releases/<id>/assets?per_page=100`; `git rev-parse v0.3.0^{commit}` `^{tree}` after `git fetch --tags` |
| Post-tag retry (19-08 only) | remote | dispatch | `gh workflow run release-please.yml --ref main -f retry=true -f tag_name=v0.3.0 -f source_sha=<S> -f release_id=<draft-id>` (inputs verified in `release-please.yml:5-21`) |
| PR B | remote | PR/merge | as PR A with a `docs(phase-19):` or `chore(phase-19):` title |
| Owner-only | n/a | n/a | Immutable-release toggle, defective tagged tree (v0.3.1), any Ir limit widening, any waiver beyond 19-08. None block planning. |

## Common Pitfalls (continued): concrete traps found

- **Gap rounds and caps:** 12 plans per phase, cap 8; do not exceed. If 19-02 overruns, cut WR-A05 first (D-09).
- **`release_bound` rows and `VERSION`:** the instant the version PR head lands, any leftover `release_bound` row fails `workflow_policy_check` on that head. 19-01 must remove all six before PR A.
- **Ledger bytes are digest-bound:** write with bytes, not text mode (`write_generated_ledger`, LF only; GB-CI-011). The ledger must not embed a full release source SHA (`parse_ledger` rejects `source_sha`/`release_source_sha`).
- **Tagged ledgers are frozen after the tag:** `refuse_tagged_target` rejects `--write-current` onto a tagged version; produce the ledger before merging #131.
- **README/preview links:** `check_binding` needs `[versioned support ledger](docs/support/v0.3.0.md)` exactly (`README_LEDGER_LINK`), and the adoption `LEDGER_LINK`/`[v0.3.0 support ledger](support/v0.3.0.md)` in `docs/preview.md` (template at adoption lines ~233, ~255).
- **PR body regeneration overwrites notes.** The release body is the PR body; run `--release-notes` on the body itself.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `refactor`/`perf` conventional types are also non-releasing in release-please defaults, but D-03 lists only `ci`, `test`, `docs`, `chore`; use those four [ASSUMED] for any other type | Autonomy map | A mis-typed title adds a bullet to the public changelog or opens 0.3.1 |
| A2 | Extra `core_linkage_*` rows in the player junit do not fail `verify-dmg-baseline.sh --inventory player` (read from `cmake/VerifyDmgBaseline.cmake:425-448`, not executed) | Pitfall 7 | Player lane red; mitigated by a separate ctest invocation |
| A3 | A `pull_request`-triggered gate on the version PR runs once the agent pushes H or W (non-release-please push), per the observed `no checks` on #131 and D-02 [CITED: 19-CONTEXT D-02, sibling MU-REL-002] | Window | Gate never runs; Merge discipline then rests on the script |
| A4 | `GET repos/{repo}/commits/{sha}/pulls` returns the squash-merged version PR with `merged_at` and `head.sha` for the merge commit S (existing capture has a `pull_request` object, not this endpoint) | Code Examples | `pr_head` binding needs another source (`pulls/{n}` from release-please output) |
| A5 | `GET .../actions/runs/{id}/attempts/{n}/jobs` is readable with the job's existing `actions: read` | 19-04 | Needs a permission pin change |
| A6 | Cross-platform state-pin byte equality should be claimed only as per-lane `state_portable_pins` passes (recommended) rather than via the three `state-pins-*` artifacts (no reader exists) | 19-03 | If the owner wants the stronger claim, a new exact-source reader is a new scope item |
| A7 | The other converted rows (`judge` 9 s, `corpus` 12m11s, `aggregate` 23m40s from run `40257161612`; `attach-v02-evidence` and `candidate-fuzz` from run `40332345735`) have p50 values to compute the same way; only `performance` was worked in the example | Code Examples | A wrong p50 fails the online check or the ratio rule |
| A8 | `release_lifecycle_controls` timing (51.24 s) measured on this Mac; hosted ubuntu-22.04 may differ | Pitfall 2 | Budget rows chosen from local numbers could be tight |

## Open Questions

1. **OQ-1 Branch retention vs "offline never resolves the cited run head" (D-04).**
   - Known: `tree_equal_sha` (on main) + `cited_tree` make the offline check independent of the rehearsal branch; the online `verify_cited` needs the run head tree, which GitHub keeps only while the commit is referenced.
   - Unclear: how to enforce "keep the branch" offline without a live ref read.
   - Recommendation: in `--check --release-head` mode only (rehearsal judge, pre-flight; always full-fetch), require `git cat-file -e <cited_sha>^{commit}` and `tree == cited_tree`, i.e. object readability, not a ref name; document that default `--check` does not do this. Control: scratch repo where the cited commit object is pruned.
2. **OQ-2 Carrier for the perf-gate binding (D-22).**
   - Known: no existing receipt can be rewritten by the reader; release assets are `REQUIRED_ASSETS` (`verify-release-gates.sh:21`, 19 names) and eight more lists.
   - Recommendation: embed a verified `perf_gate` block (run id, attempt, SHA, base SHA, limits blob, Ir for both repeats, digests, realtime, tool identity) in `release-receipt.json` built in `lifecycle_validate_draft` from the verified artifact, with the raw receipt retained as a run artifact; this keeps the asset set unchanged. If the planner needs the raw receipt attached, treat it as the one allowed new asset and update all lists plus replay.
3. **OQ-3 Regenerating the notes Ir figure (D-15).**
   - Known: figure source is `tests/baseline/perf-attribution-v1.json` (head `711f4fd`, +8.3%); `perf-attribution.yml` is a manual dispatch (about 39 revisions, 150-minute cap) that uploads a 14-day artifact; the gate shows about 9.5% at `4ace5e37`.
   - Recommendation: dispatch `perf-attribution.yml --ref main` before PR A and commit the new receipt in PR A (the check `perf_attribution` re-validates sets via `git rev-list --first-parent v0.2.0..<head> -- src`); disclose the head in the notes. If the owner prefers not to run it, the alternative is to point `perf_disclosure_percent` at the committed gate evidence, which is a design change to D-15.
4. **OQ-4 Pre-tag gate location (discretion).** New workflow (`pull_request` on `release-please--branches--main--components--GabbaBoy`, trusted checkout of `base.sha`, PR head as data, per-step bounds, no job `timeout-minutes`) vs a `ci.yml` job (would need `changes` classification and a ledger row). Recommend the new workflow, copying `version-window-gate`.
5. **OQ-5 Is the pre-tag gate enforceable?** Required contexts are fixed in GitHub settings (3 names); making the gate required is an owner/settings change. Merge discipline is therefore a script precondition in 19-07, not a branch-protection fact; state this in `docs/release.md` instead of claiming enforcement.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | all checkers | yes | system | none |
| cmake / ninja / cc (clang) | build, CTest | yes (existing `build/`, 1678 tests) | CMake >= 3.25 | none |
| git | trees, ancestry | yes | system | none |
| gh (authenticated) | read GETs now, owner-authorized writes later | yes (GETs worked) | system | none |
| valgrind | local Ir measurement | no (macOS host) | n/a | hosted `perf-gate` / `perf-attribution` only |
| SDL3 player build tree | RM-031 verification | yes (`build-player/` configured and reproduces the failure) | existing | rebuild SDL via `verify-phase3-player.sh` if stale |
| jq / bash | lifecycle replay (POSIX) | yes | system | replay skipped on Windows |

**Missing dependencies with no fallback:** none. **With fallback:** valgrind (hosted).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | CTest over python3 checkers + C test executables (`expect_exit.cmake` regex/minimum wrapper) |
| Config file | `CMakePresets.json` (`phase1`), `tests/CMakeLists.txt`, `tests/cmake/*.cmake`, `cmake/ExpectedTests.cmake`, `tests/expected-tests.txt` (1678 entries) |
| Quick run command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build -R '<regex>' --output-on-failure --no-tests=error && bash .github/scripts/verify-test-inventory.sh --self-test` |
| Full suite command | `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1 --output-on-failure --no-tests=error` (the configured `workflow.test_command`) plus, for the player lane, `bash tests/scripts/verify-phase3-player.sh` or `cmake -S . -B build-player -DGABBABOY_BUILD_PLAYER=ON ... && ctest --test-dir build-player -R '^(player_\|core_linkage_)'` |

Measured quick-loop times on this host: `workflow_policy_check` 0.18 s, `workflow_policy_controls` 49.9 s, `v02_support_ledger_controls` 18.8 s, `v02_delivery_controls` 27.5 s, `release_lifecycle_replay` 23.1 s, `release_lifecycle_controls` 51.2 s, `release_window_controls` 3.3 s, `v03_dispositions_controls` 7.5 s, `state_pin_controls` 5.8 s. Remember: replay/gate/pin tests read configure-time `HEAD`; commit then reconfigure.

### Phase Requirements -> Test Map

| Req / SC | Behavior | Test Type | Automated Command (regex for `ctest -R`) | Negative control | File Exists? |
|----------|----------|-----------|------------------------------------------|------------------|-------------|
| REL-01 SC1 / V1 | Rehearsal run must be R2 at W, success, tree = tag tree; a run naming another revision or postdating the merge is rejected | unit + replay | `^(release_lifecycle_replay\|release_lifecycle_controls\|release_nightly_gate\|release_nightly_controls)$` and policy `^workflow_policy_(check\|controls)$` | postdated run; attempt 2 finishing after merge; tree-equal non-PR-head; missing `merged_at`; other run id; `pull_request` event / fork / other path; inactive record at W; R2 red while R1 green | partly (extend) |
| SC1 / V2 | Window record legal only when `release_version` == tree version (tree-only) | unit | `^release_window_(contract\|controls)$` | version bump with stale active record rejected | extend |
| SC1 / V3 | Pre-tag gate workflow pinned and fatal | policy | `^workflow_policy_(check\|controls)$` | mutants: gate masked (`continue-on-error`), runs subject code, `pull_request_target`, wrong base | new mutants |
| SC1 / V4 | RM-027/WR-C03/candidate-performance citations are tree-equal, on main, non-provisional; scratch 0.3.0 passes `--check --release-head` | unit | `^workflow_policy_(check\|controls)$`; online `--verify-cited` stub-gh self-test | tree mismatch; anchor not on main; `cited_job_name` absent; ceil(2 x p50) over timeout; branch/object missing | extend |
| SC2 / V5 | Claims file validated and rendered; ledger is generator fixed point | unit | `^(support_claims\|support_claims_controls\|release_disclosure_generator\|release_disclosure_controls\|v02_support_ledger\|v02_support_ledger_controls\|support_ledger_binding\|support_ledger_binding_controls)$` | D-14 controls 1-9 (each paired with an unrelated positive) incl. seeded unscoped claim | new + existing |
| SC2 / V6 | Release-notes rules and adoption patterns | unit | `^(v02_adoption_docs\|v02_adoption_docs_controls\|v02_game_claims\|v02_game_claims_controls)$` | D-14 control 10; missing required sentences; wrong-version phrase | extend |
| SC2 / V7 | No interop claim names SameBoy/BGB/BESS/mGBA, v0.3.0 ledger scanned | unit | `^doc_no_interop_claims$` (regex bump `files=7`) | D-14 control 11 | extend |
| SC3 / V8 | Perf-gate receipt emitted, uploaded, verified by trusted reader | unit | `^(perf_\|v02_delivery_controls)` plus the new `--verify-receipt` self-test CTest | ratio over limit; other SHA; PR event; wrong limits blob | new |
| SC3 / V9 | Consumer receipt carries `host_smoke`; validator requires it | unit | `^(v02_delivery_controls\|v02_consumer_controls_c\|v02_consumer_controls_cpp\|installed_host_smoke)$` | receipt without `host_smoke`; `result` != passed | extend |
| SC3 / V10 | Published-asset readback reconciles; receipt bound to tag | unit | `^(v03_dispositions\|v03_dispositions_controls)$` plus new readback CTest | asset set/id drift; digest vs SHA256SUMS; sidecar blob vs `docs/support/v0.3.0.md` at the tag; draft; tag SHA/tree mismatch; another revision's receipt | new |
| D-07 | Player build linkage clean | integration | `python3 -I tests/scripts/verify-core-linkage.py --check --build-dir build-player` and `ctest --test-dir build-player -R '^core_linkage_'` | restore `mutant` name; restore double link (fixture link lines already in `core_linkage_controls`) | existing |
| D-08 | WR-C04, IN-05, IN-07, IN-08 | policy + unit | `^(workflow_policy_(check\|controls)\|v02_fuzz_controls\|test_budget\|test_budget_controls)$` | mutant that runs the head copy; `libbet-repro.yml` without `persist-credentials: false`; header edit not detected by `state_fuzz_controls` | extend |
| D-09 | WR-A05/IN-01 | unit | `^(state_refusal.*\|state_canonical\|state_semantic_bounds\|state_codec_mutant_controls\|state_portable_pins\|state_pin_controls\|state_continuation.*)$` and `cc ... -Wall -Wextra` warning count | mutant dropping the range check; continuation rows/goldens/pins byte-identical | extend |
| D-21 | Lifecycle replay covers every post-tag endpoint/asset | replay | `^release_lifecycle_(replay\|controls)$` | unexpected endpoint; missing capture | extend |
| D-25 | Docs coherent, links resolve, CHANGELOG first heading is a version | unit | `^(host_contract_docs\|readme_host_mode_contract\|unreleased_host_entries\|doc_contract_.*\|changelog_first_heading.*\|doc_links.*)$` | `## Unreleased` above a version; stale `v0.1.0` ledger link | new |
| D-19 | Pre-flight tree green | integration | scratch clone: `cmake --preset phase1 && cmake --build --preset phase1 && ctest --preset phase1` with GBB_BUILD_PLAYER tree too; lifecycle replay; `--release-notes`; `--check --release-head` | n/a (this is the negative control for the version PR) | procedure |

### Sampling Rate
- **Per task commit:** the narrow `-R` regex for the touched checker (seconds to a minute); commit before any `--rev` bound test.
- **Per wave merge:** union of the wave's regexes plus `workflow_policy_*`, `planning_labels`, `test_budget`, `summary_coverage_live`.
- **Phase gate:** full `ctest --preset phase1`, the player tree run, and the scratch 0.3.0 pre-flight; then exact-head CI on PR A (41 pass, 3 skips was the Phase 18 baseline). Re-verify once at the final head only (D-103).

### Wave 0 Gaps
- [ ] New CTest names (suggested): `support_claims`, `support_claims_controls`, `perf_gate_receipt_controls`, `v03_readback`, `v03_readback_controls`, `changelog_first_heading`, `changelog_first_heading_controls`, `doc_links_versions` (+ controls); register in `tests/CMakeLists.txt` and append to `tests/expected-tests.txt`; add `LABELS planning` to those that read `.planning/`; give each an explicit TIMEOUT <= 60.
- [ ] Raise parsed minimums only after measuring (`workflow_policy_controls` floor; `release_*_controls`).
- [ ] No new framework install needed.

### SUMMARY `coverage:` block (AGENTS.md; enforced by `summary_coverage_live`, `--since 16`)
Every plan SUMMARY frontmatter carries block-style entries, no `{...}` flow items, no inline `#` comments, `kind` one of `unit|integration|e2e|automated_ui|other`, `status: pass`, never a `ctest` kind. Model (from `18-04-SUMMARY.md`):
```yaml
coverage:
  - id: D1
    description: "One sentence naming the observable behaviour and its negative control."
    requirement: REL-01
    human_judgment: false
    verification:
      - kind: unit
        ref: "ctest -R ^support_claims_controls$ (tests/scripts/verify-support-ledger.py --self-test-claims)"
        status: pass
```
At verify-work: `python3 -I tests/scripts/verify-uat-closure.py <phase-dir> --write <evidence>` then `... --self-test`; never hand-write `19-UAT.md` (CTests `uat_closure_controls`, `uat_closure_optimize_refused`). `human_judgment: true` only for true perceptual/hardware/credential items; this phase has none.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (no user auth) | GitHub token scopes only |
| V3 Session Management | no | n/a |
| V4 Access Control | yes | Least-privilege workflow `permissions:`; trusted judge from default branch; `persist-credentials: false`; policy exact-set pins (`READONLY_WORKFLOWS`) |
| V5 Input Validation | yes | Bounded, strict parsers in managed inputs (exact key sets, ASCII regex, size bounds); `state_validate` before any write |
| V6 Cryptography | yes | SHA-256 digests only via `hashlib`/existing helpers; the state CRC/ROM digest is identity, not authentication (stated as a non-claim) |

| Threat Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Forged or stale rehearsal evidence | Spoofing/Tampering | Tree-equality binding, `pr_head`, `not_after` from server-recorded timestamps; R2 selection by newest success |
| Subject code runs in trusted job | Elevation | Subject checked out as data; policy rejects execution of subject paths (W17 mutants) |
| Hostile state file mutates instance | Tampering | `state_validate` complete before `state_apply`; shared infallible conversion; no `assert` on fallible calls |
| Unscoped or interop claim in published text | Repudiation/Info | Claims as data + generator fixed point + interop pattern widening |
| Privacy leak in committed receipts | Info disclosure | `FORBIDDEN_TEXT` scan extended to readback/receipt JSON; no `/Users/`, tokens, keys |
| Release asset swap after attach | Tampering | IN-07 wording only (identity and consistency check, not tamper detection); content gate remains `--check-v02-evidence` |
| Credential persistence in checkouts | Info disclosure | `persist-credentials: false` (IN-08) |

`workflow.security_enforcement` is true, ASVS level 1 (`.planning/config.json`).

## Sources

### Primary (HIGH confidence, opened this session)
- `.planning/phases/GB-19-qualified-v0-3-0-release/19-CONTEXT.md` (D-01..D-30)
- `.github/scripts/verify-workflow-policy.py` (1536, 2215-2400, 3540-3640), `.github/scripts/verify-release-source-proof.py` (100-165, 262-310, 527-560), `.github/scripts/release-evidence-lifecycle.sh`, `.github/workflows/{ci,release,release-please,release-rehearsal,nightly-asan,perf-attribution}.yml`, `release-please-config.json`
- `tests/scripts/{verify-support-ledger,verify-v02-adoption,verify-v03-dispositions,verify-version-window,verify-perf-gate,verify-v02-delivery,verify-release-lifecycle,verify-core-linkage,verify-no-interop-claims,verify-test-budget,verify-summary-coverage,verify-uat-closure,verify-state-pins,test_installed_host,run-perf-gate}.*`, `tests/CMakeLists.txt`, `tests/cmake/{ci-lanes,host-contract,perf}.cmake`, `tests/player/CMakeLists.txt`, `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`, `src/core/gabbaboy.c` (4100-4260, 4695-4790)
- `.planning/phases/GB-17-native-save-state-core/17-REVIEW.md` (WR-A05, WR-C03, WR-C04, IN-A01, IN-B02, IN-C01, IN-C02) and `17-REVIEW-DISPOSITION.md`; `.planning/context/FUTURE-MILESTONES.md` RM-031; `.planning/context/DECISIONS.md` D-112, D-120
- Read-only `gh` GETs of runs `40257161612`, `40332345735`, PR #131, branch protection, rulesets, releases, repo merge settings
- Local runs: `verify-core-linkage.py --check --build-dir build-player`, `verify-workflow-policy.py --check --verify-cited`, the `ctest` timings above, the scratch 0.3.0 pre-flight

### Secondary (MEDIUM)
- `gh pr merge --help`, `gh workflow run --help`, `gh run watch --help` flag availability.

### Tertiary (LOW, flagged [ASSUMED])
- release-please default hidden changelog sections (A1); `commits/{sha}/pulls` payload (A4); attempts/jobs permission (A5).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH (no new dependencies).
- Architecture / wiring: HIGH (all registration points read).
- Pitfalls: HIGH for items measured or read (timings, shallow checkout, linkage failures); MEDIUM for hosted behaviour not exercised.
- Remote steps: MEDIUM (no write/dispatch was run).

**Research date:** 2026-10-29
**Valid until:** until any push lands on `main` (main is frozen by D-26 only during the window); re-check anchor line numbers if PR A work starts after another main merge. The pre-flight used a disposable local clone outside the repository.
