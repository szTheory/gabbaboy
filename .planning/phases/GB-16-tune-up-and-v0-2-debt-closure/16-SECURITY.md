---
phase: "16"
slug: "tune-up-and-v0-2-debt-closure"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-26"
---

# Phase 16 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Audit of the plan-time threat register (plans 16-01..16-07) by `gsd-security-auditor` at main `be4cee8`. Mitigations were checked against the implementation, and the live self-tests were re-run: `verify-workflow-policy.py` (266 negative and 4 positive controls), `classify-changes.py` (49), `verify-test-budget.py` (38), `verify-v03-dispositions.py` (35), `verify-no-phase-paths.py` (17) and `verify-phase8-closure-contract.py` (rejected_controls=160). No core source changed (`src/`, `include/`).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PR head → CI | Untrusted PR content decides which lanes run and what is judged | Diff paths, workflow YAML, allowlists, timeout ledger |
| Workflow token scope | Jobs that hold write or `actions: read` tokens | `issues: write` (nightly report), `github.token` artifact fetch (rehearsal) |
| Rehearsal → release | Evidence produced on `rehearsal/*` and reused at release | Performance receipt, review decision, nightly run id |
| Owner → release gate | Owner performance review approval | Issue comment identity, digest, timestamps |
| Published release | Assets reconciled after publication | Asset names, ids, SHA-256 digests |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-16-01 | Tampering | verify-no-phase-paths allowlist | medium | mitigate | Count-pinned reasoned rows, must-scan list, file floor 380 (now 498) — `tests/scripts/verify-no-phase-paths.py:116-137` | closed |
| T-16-02 | Tampering | legacy-path rewrite | medium | mitigate | Exact-prefix strip, `archived-record-escape`/`-missing` rejections — `tests/scripts/verify-closeout-dispositions.py:84-99` | closed |
| T-16-03 | Repudiation | archive move | low | mitigate | 578 pure R100 renames in `711f4fd` | closed |
| T-16-04 | Tampering | perf-gate verdict | high | mitigate | In-job v0.2.0 baseline (`run-perf-gate.sh:96-97`), ROM pins, vacuity/determinism guards, seeded control every run (`ci.yml:524-529`) | closed |
| T-16-05 | Elevation | perf jobs | medium | mitigate | `contents: read`, no persisted credentials, SHA-pinned actions; `check_perf_attribution` + mutations | closed |
| T-16-06 | Info disclosure | attribution receipt | low | mitigate | `verify_privacy` (`verify-perf-gate.py:440-469`); hardware class only | closed |
| T-16-SC (16-02) | Tampering | apt-get valgrind | high | mitigate | Signed Ubuntu archive; version logged and in receipt; no third-party actions | closed |
| T-16-07 | Elevation | nightly-asan `issues: write` | high | mitigate | Only checkout-less `report-red` holds write; `check_nightly` + mutations | closed |
| T-16-08 | Tampering | test-budget allowlist | medium | mitigate | Base-commit `BaseView`, fail closed `base-unreadable`, raised-ceiling and ref rejections (residual WR-04 below) | closed |
| T-16-09 | DoS | PR sanitizer lane | medium | mitigate | `CI_SANITIZER_SHARDS` pin, bounded replay, mutations | closed |
| T-16-10 | Elevation | classify-changes.py | high | mitigate | Base-commit copy decides; fail closed on every listed path/diff/ref hazard; `classify_changes_src_rejected` | closed |
| T-16-11 | Tampering | required-native aggregator | high | mitigate | `if: always()` pinned; exact skipped/success rule (`check-required-native.py:43-53`) + mutations | closed |
| T-16-12 | Tampering | `.github/ci-timeouts.json` | medium | mitigate | Ledger=YAML, ratio, whole-run, provisional-at-release-head and VERSION-expiry rules present; six `release_bound` rows (D-110/D-111) not yet re-cited, carried by RM-027 | open — below high threshold (non-blocking) |
| T-16-13 | Elevation | changes / planning-checks jobs | medium | mitigate | `contents: read`, no persisted credentials, `pull_request_target` mutation | closed |
| T-16-14 | Tampering | historical/phase-08-boundary tag | medium | mitigate | Annotated tag peels to `96d5eec` on origin; fail-closed resolve; 160-control minimum (residual WR-02 below) | closed |
| T-16-15 | DoS | Phase 8 input loss | medium | mitigate | Tag created 2026-10-25, before first PR closure 2026-10-26 | closed |
| T-16-16 | Repudiation | STATE trim | low | mitigate | Verbatim blocks in `v0.2-STATE-ARCHIVE.md` naming `458fc71` | closed |
| T-16-17 | Spoofing | performance_decision input | high | mitigate | `verify_reviewed_disposition` (`verify-v02-performance.py:144-212`); decision outside the checkout | closed |
| T-16-18 | Tampering | reused rehearsal receipt | high | mitigate | `--verify-reuse` with tag-tree equality; dispatch-path run checks; policy mutation (residual WR-01 accepted below) | closed |
| T-16-19 | Tampering | docs/support/v0.2.0.md | medium | mitigate | Two-digest freeze plus pinned block; `ledger_freeze` CTest | closed |
| T-16-20 | Repudiation | dispositions closure | medium | mitigate | Tag-bound receipts, readback digest, tree equality (`verify-v03-dispositions.py:225-306`) | closed |
| T-16-21 | Tampering | #75 merge | high | mitigate | Head `c6dc575` and squash `b93137f` share tree `b02c14b`; exact-head required checks green | closed |
| T-16-22 | Spoofing | performance review | high | mitigate | Planned `verify-release-gates.py --review-approval` gate not built; one-time `gh api`/jq check substituted under D-112 and re-confirmed by the auditor — see AR-16-01 | closed (accepted risk) |
| T-16-23 | Repudiation | GITHUB_TOKEN push skipping CI | medium | mitigate | `c6dc575` pushed under the user identity; `pull_request` CI ran green | closed |
| T-16-24 | Tampering | published assets | high | mitigate | `verify-published-release-assets.py` in `release.yml`; 22 reconciled assets, digest-bound readback (residual WR-03 accepted below) | closed |
| T-16-25 | Elevation | publication without nightly | high | mitigate | Planned `--nightly-gate` gate not built; recorded `gh run view` of run 40245698754 (head `c6dc575`, success) substituted under D-112; tree-equality re-check present — see AR-16-02 | closed (accepted risk) |
| T-16-SC (16-01, 03, 04, 05, 06, 07) | Tampering | npm/pip/cargo installs | high | accept | No package installs in the phase diff other than the 16-02 valgrind row — see AR-16-03 | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-16-01 | T-16-22 | The owner approved replacing the planned `--review-approval` gate and its CTest with a one-time `gh api`/jq check during the v0.2.1 window (D-112 amendment 1). The auditor re-confirmed that check: comment 6406576530 has association OWNER, `issue_url` matches #122, it was created after the issue, and it carries the full digest. The scope is v0.2.1 only. Building the gate is an RM-030 item that must be done before the next release. | Owner (D-112, 2026-10-25) | 2026-10-26 |
| AR-16-02 | T-16-25 | Same D-112 amendment: the planned `--nightly-gate` gate was replaced by the recorded `gh run view` of run 40245698754 on head `c6dc575`. Tree equality is re-checked at the boundary; the timestamp re-check is absent. The scope is v0.2.1 only. Building the gate is an RM-030 item that must be done before the next release. | Owner (D-112, 2026-10-25) | 2026-10-26 |
| AR-16-03 | T-16-SC (16-01, 03, 04, 05, 06, 07) | These plans install no packages. The auditor confirmed the only installs in `02776e5..HEAD` are the valgrind lines covered by the 16-02 mitigate row. | Plan-time disposition | 2026-10-26 |
| AR-16-04 | T-16-18 (WR-01) | `release.yml:1166-1168` reuses the newest successful `rehearsal/$TAG` performance artifact without binding the producing run's headSha, workflow and event. Someone with push access could plant a forged receipt for the tag tree. The declared mitigation (tag-tree equality) is present. Deferred in `16-REVIEW-DISPOSITION.md`; RM-030 Phase 17 entry item. | Deferred review disposition | 2026-10-26 |
| AR-16-05 | T-16-24 (WR-03, IN-01) | `verify-release-gates.sh:277-279` collapses duplicate `SHA256SUMS` lines. The v0.2.1 file is unaffected: 20 lines, no duplicates or blanks. IN-01 weakens the recovery-stage tamper check on retry, but the later `--check-v02-evidence` gates still apply. RM-030. | Deferred review disposition | 2026-10-26 |

Non-blocking residuals that stay on RM-030: WR-02 (T-16-14, tag SHA not asserted), WR-04 (T-16-08, new allowlist rows uncapped; checker runs from the head tree) and WR-05 (plan-cap hygiene, no register threat).

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-26 | 32 | 29 | 3 (2 high, 1 medium) | gsd-security-auditor (initial verdict OPEN_THREATS) |
| 2026-10-26 | 32 | 31 | 1 (medium, non-blocking) | orchestrator: T-16-22/T-16-25 closed as owner-accepted under D-112 (AR-16-01/02); T-16-SC accept rows logged (AR-16-03) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-26
