---
phase: "17"
slug: "native-save-state-core"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-28"
---

# Phase 17 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

`gsd-security-auditor` audited the plan-time threat register (plans 17-01..17-11, T-17-01..29) at branch head `e8ea47a`. The final source head is `6199487`. The auditor checked each mitigation against the implementation and re-ran the matching tests. That covered 280 CTests (`state_*`, `release_*`, `perf_*`, `workflow_policy*`, `support_ledger*`, `summary_coverage*`, `uat_closure*`, the installed consumers and the package smoke) and 9 hygiene and budget CTests. It also covered the self-tests of `verify-release-source-proof.py`, `check-required-native.py`, `verify-v02-delivery.py`, `verify-version-window.py`, `verify-support-ledger.py` and `verify-release-gates.sh`. All passed. Every mitigation below has a negative control that fails when the mitigation is removed. Hosted exact-head CI for `6199487` was still in progress during the audit, so no hosted result counts as evidence here. The one exception is the `report-red` dry run 40749683012, which the auditor read directly.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Host → core state API | Untrusted serialized state bytes from any frontend or save file | Header, identity, CRC, 198-field body |
| ROM → core identity | The loaded ROM binds which states are accepted | SHA-256 and CRC32 identity, mode, mapper |
| Core time and event admission | Host-scheduled inputs, spans and run lengths over a 2^62 horizon | Timestamps, event queues, wrapper calls |
| PR head → CI | Untrusted PR content judged by trusted workflow code | Workflows, scripts, allowlists, timeout ledger, generated release content |
| Rehearsal and prior release → release | Evidence reused at release time | Performance receipts, attached assets, SHA256SUMS, manifests |
| Owner → release gate | The owner's approval of a deterministic Ir exception | Issue comment identity, digest, timestamps |
| Workflow token scope | Jobs that hold write or read tokens | `issues: write` (report-red), `actions: read` (publish), `contents: write` (release) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-17-01 | Tampering | decoder | high | mitigate | `gbb_load_state` checks magic, version, identity, exact size, overlap, CRC, reserved bytes and full validation before a non-failing apply (`src/core/gabbaboy.c:4885-4925`); `state_refusal`, apply-before-validation mutant and control, `state_semantic_bounds` | closed |
| T-17-02 | Info disclosure | wire fields | high | mitigate | Explicit field-by-field codec via `state_walk`; pointers, test/diagnostic members and observer counters excluded (`gabbaboy.c:636-741`); `state_inventory(_controls)`, `state_globals(_controls)` | closed |
| T-17-03 | Denial of service | size/audio arithmetic | high | mitigate | 524288-byte body maximum, overflow-refusing size sum and total cap (`gabbaboy.c:747`, `:1014`, `:1031`); `state_size_bound`, `state_audio_bound`, `state_precodec_gate` | closed |
| T-17-04 | Spoofing | ROM identity | high | mitigate | One SHA-256 per validated ROM, installed only after allocation succeeds; full SHA compared on load (`gabbaboy.c:5332-5338`, `:4899`); equal-CRC/different-SHA pair and hash-count checks in `state_identity` | closed |
| T-17-05 | Tampering | canonical fields | high | mitigate | Read-only `state_validate_fields`/`state_validate_relations` before apply; `state_canonical`, `state_semantic_bounds`, `state_codec_mutant_controls` | closed |
| T-17-06 | Tampering | load atomicity | high | mitigate | Whole-instance and RAM byte-equality oracle after each refusal; apply-before-validation, counter, short-prefix and save-tail mutants killed (`state_refusal(_controls)`) | closed |
| T-17-07 | Tampering | RTC/palette/observers | high | mitigate | Projected battery equality and observer apply on load (`gabbaboy.c:4920-4922`); `state_rtc_palette`, `state_observers`, 11 `state_observer_mutant_*` pairs | closed |
| T-17-08 | Denial of service | state calls | high | mitigate | No allocation, hash or tail write during size or save; `state_purity(_controls)` with allocation, hash and tail-write mutants | closed |
| T-17-09 | Denial of service | time arithmetic | high | mitigate | `state_time_fits` keeps time under 2^62 (`GBB_STATE_TIME_LIMIT`), with 15 named `GBB_HORIZON_GUARD` sites; `state_horizon`, `state_horizon_wrappers`, `state_horizon_sentinels` | closed |
| T-17-10 | Tampering | event admission | high | mitigate | `validate_accept_input_span` checks the limit, overlap, ordering and time cap before admitting a span; `state_horizon_events`, 128 `state_horizon_closure_*` shards | closed |
| T-17-11 | Tampering | closure evidence | high | mitigate | Each guard mutant counts as a kill only with its witness line; a compile failure never counts (`tests/scripts/verify-state-horizon.py`); `state_horizon_mutants`, `state_horizon_mutant_controls` | closed |
| T-17-12 | Tampering | fork coverage | high | mitigate | Field and category witnesses parsed from real fork output (`verify-state-forks.py:357-364`); `state_fork_census(_controls)`, 16 matrix shards | closed |
| T-17-13 | Repudiation | mutation proof | medium | mitigate | `state_fork_mutants` (16 shards), `state_fork_mutant_controls` | closed |
| T-17-14 | Tampering | portable pins | high | mitigate | Base read from git, and a compatibility disposition with current evidence required (`verify-state-pins.py:80`, `:208-236`); `state_portable_pins`, `state_pin_controls` | closed |
| T-17-15 | Denial of service | hostile state input | high | mitigate | State fuzz target in the real campaign dispatcher (`tests/fuzz_core.c:1159`, `:1444`); `state_load_fuzz`, `state_fuzz_controls` | closed |
| T-17-16 | Repudiation | hosted qualification | medium | mitigate | `state_portable_pins` runs on Linux, macOS and Windows (`.github/workflows/ci.yml:151`, `:270`, `:358`). Present in code; hosted receipts for the final head are checked at phase verification | closed |
| T-17-17 | Tampering | performance policy | high | mitigate | Limits base pinned to `947d6a9` (`run-perf-gate.sh:26`, `:159`); `ir-limit-widening-unapproved` rejection (`verify-perf-gate.py:418`); `perf_limit_ratchet`, `perf_repeat_controls`, `perf_gate_canned_*` | closed |
| T-17-18 | Spoofing | timing receipt | high | mitigate | Receipt source, build and workload binding (`verify-v02-performance.py:175`, `:303`); `perf_advisory_pipeline(_controls)`, v02-delivery self-test (48 rejections) | closed |
| T-17-19 | Tampering | generated release content | high | mitigate | Bounded inputs and checks of the tag blob, working copy and block digests (`verify-support-ledger.py:33-35`, `:227-235`); `release_disclosure_generator(_controls)` | closed |
| T-17-20 | Repudiation | review window | medium | mitigate | Read-only `version-window` job running the checker from trusted main with `persist-credentials: false` (`release-please.yml:53-109`); `release_window_contract(_controls)`, version-window self-test (27 controls) | closed |
| T-17-21 | Spoofing | GitHub API evidence | high | mitigate | Trusted App 15368 required on evidence (`verify-release-source-proof.py:18-20`, `verify-release-gates.sh:196`); source-proof self-test (54 defects), `check-required-native.py` (19 controls) | closed |
| T-17-22 | Tampering | retry assets | high | mitigate | Independent identity and consistency check before reusing attached bytes (it compares attachments with the digests GitHub reports for the same assets, so it detects identity drift and corruption, not a swap of the live asset; 17-REVIEW IN-C01) (`release-evidence-lifecycle.sh:50-91`); `release_lifecycle_controls` including reorder and removed-check mutants | closed |
| T-17-23 | Elevation of privilege | replay publication | high | mitigate | The replay `gh` stand-in refuses unlisted endpoints, flags, repositories, mutations and reshaped responses (`verify-release-lifecycle.py:319-413`); `release_lifecycle_replay` | closed |
| T-17-24 | Spoofing | performance reuse/check apps | high | mitigate | Reuse bound to the workflow path, event, run attempt and head SHA or tree (`verify-release-source-proof.py:88-131`) | closed |
| T-17-25 | Tampering | manifests/historical/budget | high | mitigate | Duplicate asset names rejected; Phase 8 tag peels to `96d5eec`; `new-row-ref-reused`; plan cap with suffixed names; `test_budget(_controls)`, `plan_cap`, `phase8_*_selftest`, `planning_hygiene_controls` Residual: the CI budget step still runs `verify-test-budget.py` and its allowlist from the PR head (carried Phase 16 WR-04; 17-REVIEW WR-C04, deferred) | closed |
| T-17-26 | Elevation of privilege | report-red | high | mitigate | `timeout-minutes: 5` on both the job and the step, `issues: write` only, no checkout, exact title and label dedupe; 14 policy mutants plus a body replay; hosted dry run 40749683012 (success in 4 s, both writes printed as `DRY-RUN not sent`) cited in `.github/ci-timeouts.json` | closed |
| T-17-27 | Spoofing | Ir OWNER approval | high | mitigate | OWNER, issue, empty owner fields and comment-after-issue checks (`verify-release-gates.py:255-284`, 8 mutants); ratchet consumes only the gate-written receipt, and the self-attested `GBB_PERF_EXCEPTION_RECEIPT` path is removed and refused by policy; `release_review_approval(_controls)` **Reopened by CR-C01, closed by `c66430f`:** `--repository` (default `szTheory/gabbaboy`, `$GITHUB_REPOSITORY` in `run-perf-gate.sh`) binds the issue URL, the approving login and the comment link to this repository (`review-wrong-repository`, `review-not-owner`; 8 new controls); policy rule `ir-exception-env` refuses any workflow that supplies `GBB_IR_EXCEPTION_*` or assigns `GITHUB_REPOSITORY` (mutants CR-C01-1..9), so hosted runs fail closed for a widened Ir limit | closed |
| T-17-28 | Elevation of privilege | nightly/release decision | high | mitigate | Trusted `nightly-gate` runs immediately before `publish-draft` (`release.yml:1356-1359`); publish job holds exactly `actions: read` (policy mutants G17-09/G17-10); `release_nightly_gate(_controls)` | closed |
| T-17-29 | Repudiation | phase boundary | medium | mitigate | `verify-state-contract.py --boundary` reads facts from the literal `boundary_sha` `d53ec9c`; `state_boundary_controls`; both auto-advance flags false | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|

No risks were accepted in Phase 17. The Phase 16 accepted and deferred risks covered by RM-030 now have production gates. AR-16-01 is replaced by the `--review-approval` gate (T-17-27). AR-16-02 is replaced by the `--nightly-gate` gate (T-17-28). AR-16-04 (WR-01) is closed by run-bound receipt reuse (T-17-24). AR-16-05 (WR-03/IN-01) is closed by the strict `SHA256SUMS` and manifest parse and by the retry-order tamper check (T-17-22/T-17-25).

Non-blocking residuals. None of these is a mitigation gap:

1. **T-17-27, comment source (CR-C01 fixed in `c66430f`).** The approval gate judges a saved comment JSON file. No trusted workflow fetches that comment from the GitHub API yet, so the OWNER check is only as authentic as the file. On hosted runs this fails closed, because no workflow sets `GBB_IR_EXCEPTION_*` and a widened Ir limit is refused. There is also no hosted path yet for a genuine approval to pass.
2. **`state_fuzz_controls` reads the live HEAD.** It refuses, never accepts, when the build is configured at a different revision than HEAD. Reconfigure before running it.
3. **`release.yml:candidate-performance`.** This timeout row was added in Phase 16 (`26a2b97`). Its cited run predates the job's rename, so `verify-workflow-policy.py --check --verify-cited` fails it. Re-citing needs the next release run.
4. **RM-027.** The six `release_bound` rows remain Phase 19 entry blockers by design.

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-28 | 29 | 29 | 0 | gsd-security-auditor (verdict SECURED; no unregistered SUMMARY threat flags) |
| 2026-10-28 | 29 | 28 | 1 (high) | orchestrator: T-17-27 reopened by 17-REVIEW.md CR-C01 (repository binding absent, env-var path unguarded by policy); closes only with a fix and a negative control |
| 2026-10-28 | 29 | 29 | 0 | orchestrator after review-fix round 1: T-17-27 closed by `c66430f` (repository binding + `ir-exception-env` policy rule, each with negative controls, independently checked: an injected `GBB_IR_EXCEPTION_DECISION` env in `ci.yml` is refused) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-28 after review-fix round 1
