---
phase: "19"
slug: qualified-v0-3-0-release
status: draft
threats_open: 4
asvs_level: 1
created: "2026-10-30"
---

# Phase 19 — Security

This interim audit covers the authored threat register in plans 19-01..19-07. The independent ASVS L1 audit at `29f6ae2b818fdc4dac8b73b3107b5a9722e10578` found two implementation gaps under T-19-22. The focused re-audit of the complete six-file correction diff at `b0beb4fd8d1c2290d89b707860bf23c899e12fac` closed both gaps. With the existing acceptance recorded as AR-19-01, 26/35 unique threats are closed and nine operational verifications remain pending; four meet the high blocking threshold. This report does not certify publication or phase completion.

## Trust Boundaries

| Boundary | Data crossing |
|----------|---------------|
| Untrusted PR subject → trusted workflow judge | Commit/tree IDs, workflow declarations and receipts |
| Serialized state → portable core | Bounded state bytes validated before application |
| Build/archive → external consumer | Installed package bytes, host smoke and platform identity |
| Rehearsal/CI → release qualification | Run/attempt, exact source, performance and corpus receipts |
| Draft release → public release | Frozen API asset IDs, names and digests |
| GitHub API → committed readback | Sanitized source-bound metadata and raw pre-publish inventory |
| Operator → Git refs | Guarded pushes, merges, immutable tag and draft lifecycle |

## Threat Register

Evidence paths below are relative to `tests/scripts/` unless otherwise qualified. Unchanged rows retain the initial audit's evidence at29f6ae2b; T-19-22 uses the b0beb4fd re-audit.

| Threat ID | Category | Component | Severity | Disposition | Mitigation / remaining evidence | Status |
|-----------|----------|-----------|----------|-------------|---------------------------------|--------|
| T-19-01 | Spoofing | Ledger citations | high | mitigate | `.github/scripts/verify-workflow-policy.py:2473,2491,2639,2657`: anchor ancestry/tree, retained release object, cited job and API tree | closed |
| T-19-02 | Repudiation | Git evidence | medium | mitigate | Policy checker fails closed at2454; rehearsal full-history trusted judge and explicit Git root | closed |
| T-19-03 | Tampering | Trusted policy | high | mitigate | CI extracts checker from BUDGET_BASE; policy pins base-copy commands | closed |
| T-19-04 | Information disclosure | Repro workflow credentials | low | mitigate | libbet-repro disables persisted credentials and belongs to READONLY_WORKFLOWS | closed |
| T-19-05 | Repudiation | Player linkage | low | mitigate | Corrected core links; verify-phase3-player.sh Debug linkage check; auditor observed66 targets, zero violations | closed |
| T-19-06 | Tampering | State application | high | mitigate | gabbaboy.c validates before shared infallible conversion; range-removal mutant control | closed |
| T-19-07 | Repudiation | Fuzz source binding | low | mitigate | verify-v02-fuzz.py includes public header and header-edit control | closed |
| T-19-08 | Repudiation | Managed claims | high | mitigate | verify-support-ledger.py exact keys, enums, derived counts and evidence registration | closed |
| T-19-09 | Tampering | Generated ledger | medium | mitigate | Exact generator bytes and hand-edit refusing control | closed |
| T-19-10 | Repudiation | Interop claims | medium | mitigate | verify-no-interop-claims.py scans optional v0.3 ledger with widened pattern and controls | closed |
| T-19-11 | Repudiation | Performance claims | medium | mitigate | verify-v02-adoption.py requires full measured head and historical-head/tag-bound wording | closed |
| T-19-12 | Tampering | Version window inputs | high | mitigate | verify-version-window.py includes and digests managed claims | closed |
| T-19-13 | Spoofing | Rehearsal source proof | high | mitigate | Exact PR head/tree and run-attempt jobs; R2-red control | closed |
| T-19-14 | Tampering | Postdated rehearsal | high | mitigate | Source proof compares merge/completion timestamps; judge refuses existing tag | closed |
| T-19-15 | Elevation of privilege | Version PR gate | high | mitigate | PR-only trigger, read permissions, trusted base checkout, data-only subject and environment body; policy pins | closed |
| T-19-16 | Tampering | Active window version | medium | mitigate | Window checks tree version; release requires active record at SOURCE_SHA | closed |
| T-19-17 | Denial of service | API replay coverage | medium | mitigate | verify-release-lifecycle.py inventories endpoint forms and rejects uncovered routes | closed |
| T-19-18 | Information disclosure | API captures | medium | mitigate | Lifecycle sanitizer; bounded bytes, digest and private-text/email refusal | closed |
| T-19-19 | Spoofing | Perf receipt handoff | high | mitigate | Release selects named artifact at run/attempt; verifier binds source/event/workflow/run/attempt/limits | closed |
| T-19-20 | Tampering | Performance policy | high | mitigate | Shared exact predicate and immutable limits checks; frozen limits unchanged | closed |
| T-19-21 | Repudiation | Consumer host smoke | medium | mitigate | Policy orders host smoke and platform-bound receipts for every writer; consumer verifier checks results | closed |
| T-19-22 | Tampering | Publication inventory/readback | high | mitigate | Full API inventory includes final metadata; checksum/receipt coverage uses payload names; shared verifier binds complete name/ID/digest maps and release/run/source identity before publication. Independent post-gate removal refuses with draft=true and zero publication decisions; omitted-guard mutant publishes then refuses. | closed |
| T-19-23 | Information disclosure | Readback | medium | mitigate | verify-v03-dispositions.py privacy scan and immutable lifecycle pattern parity | closed |
| T-19-24 | Repudiation | Release profiles | low | mitigate | Lifecycle derives profiles/ledger from tag; profile control | closed |
| T-19-25 | Denial of service | Final synthetic preflight | medium | mitigate | Final-head hosted producers, bump-only negative and transient branch deletion pending | open — below high threshold |
| T-19-26 | Tampering | PR A merge | high | mitigate | Exact-head required checks and guarded squash with match-head pending | open |
| T-19-27 | Tampering | PR titles/file set | medium | mitigate | Observed PR A title and regenerated #131 title/file set pending | open — below high threshold |
| T-19-28 | Repudiation | Documentation | low | mitigate | Doc links and first CHANGELOG heading contract checks with refusing controls | closed |
| T-19-29 | Tampering | Version PR merge | high | mitigate | W go/no-go, guarded #131 merge and observed tree(S)==tree(W) pending | open |
| T-19-30 | Tampering | Main during window | high | mitigate | Main equals PR A squash before each step, single post-merge commit pending | open |
| T-19-31 | Tampering | Tag/draft lifecycle | high | mitigate | Actual immutable tag/draft operations and failure routing pending | open |
| T-19-32 | Spoofing | Post-merge rehearsal | medium | mitigate | Actual no-push/no-rerun observation against merge timestamp pending | open — below high threshold |
| T-19-33 | Repudiation | Release body | medium | mitigate | Live body validation before merge and W body digest equality pending | open — below high threshold |
| T-19-34 | Information disclosure | Committed readback | medium | mitigate | Actual readback privacy and registered v03_readback check pending | open — below high threshold |
| T-19-SC | Tampering | Package installations | high | accept | Existing plan-time acceptance recorded as AR-19-01 | closed |

## Implementation Findings and Round 1 Closure

CR-01 / T-19-22: the publisher excludes `SHA256SUMS` and `release-receipt.json` from their payload lists, uploads both, then snapshots every API asset. Readback incorrectly requires both payload lists to cover the complete inventory. Independent reproduction: payload-only fixture passes; replacing its inventory with the production full shape and rehashing raw bytes rejects `readback-digest-mismatch`. Correct coverage must distinguish payloads and separately bind final metadata IDs/digests, preserving complete inventory comparison.

CR-02 / T-19-22: the final gate precedes nightly. `publish-draft` performs its asset comparison after `gh release edit --draft=false`. Independent replay with unmodified production scripts: final-gate=0; nightly-gate=0; remove qualified `gabbaboy-core-linux-x64.tar.gz`; publish-draft=1 with `REJECT published-assets`, but draft=false and a publish decision already recorded. Require fresh complete frozen-inventory comparison immediately before publication, with a control proving a changed asset leaves draft=true and zero publication decisions. Retain post-publication comparison. This finding concerns an already present change, distinct from the residual race between separate API requests.

Both historical findings above are fixed at b0beb4fd. The independent auditor ran all48 readback controls against the full production-shaped inventory, the shared asset verifier self-test, and the focused lifecycle control against immutable b0beb4fd inputs with the real validation/final/nightly prelude. Unchanged assets publish once; a post-gate removal leaves draft=true and zero publication decisions; the omitted-guard mutant publishes once and then refuses. The complete post-tag replay reports3 positives,84 controls and23 endpoints. The four CTest-wired controls passed4/4 at the same source SHA. Evidence: `build/preflight/runs/b0beb4fd8d1c2290d89b707860bf23c899e12fac/review/round1-evidence.md` and adjacent logs (ignored local evidence).

The code review additionally found WR-01: changed-path closure accepted internal `..` components. Canonical repository-path validation and a traversal negative control now refuse it. Integration also exposed IR-01: the judge helper's CLI contradicted its documentation; the documented `--key STDERR --exit N` grammar now has positive and refusing CLI controls. Neither is a new authored threat ID.

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-19-01 | T-19-SC | The existing acceptance in all seven authored plans states no package installation: stdlib Python, CMake and gh; existing pinned actions only. The auditor verified that premise at the reviewed commit. This entry records that existing disposition and grants no new risk acceptance. | Plan-time disposition in19-01..19-07; independently rechecked by gsd-security-auditor | 2026-10-30 |

## Audit Trail and Limits

| Date | Source | Closed | Open | Blocking open | Audit |
|------|--------|--------|------|---------------|-------|
| 2026-10-30 |29f6ae2b818fdc4dac8b73b3107b5a9722e10578|24|11|6|Independent initial audit; T-19-SC log absent |
| 2026-10-30 |Same source; acceptance logged here|25|10|5|Orchestrator records existing AR-19-01; two independently confirmed T-19-22 gaps remain |
| 2026-10-30 |b0beb4fd8d1c2290d89b707860bf23c899e12fac|26|9|4|Independent gsd-security-auditor focused re-audit closes both T-19-22 implementation gaps; existing AR-19-01 verified |

No missing subject-ancestry dependency was established: ancestry/object checks use full-history trusted-judge; subject derivation reads CMake/manifest; fuzz exact-tree/blob validation follows fetching the subject commit. The local differential uses full-history worktrees and does not exercise a shallow subject checkout; this is a coverage limitation, not a verified defect. The five completed summaries have no explicit Threat Flags sections; that is not proof of an exhaustive attack-surface inventory.

Audit-time linkage, managed claims, interop scan, CHANGELOG heading and doc link checks passed. Reproductions were isolated; no remote mutation occurred. The final-head synthetic rehearsal has not yet run after the fixes, so T-19-25 remains open. Publication operations and REL-01 remain pending. No security or phase-completion sign-off is claimed.
