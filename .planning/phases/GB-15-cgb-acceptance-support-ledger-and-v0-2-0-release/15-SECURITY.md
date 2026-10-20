---
phase: "15"
slug: "cgb-acceptance-support-ledger-and-v0-2-0-release"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-20"
---

# Phase 15 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Evidence/input bytes → adopter or release claim | Untrusted, stale or partial content must not become supported behavior or published qualification. | Receipts, sidecars, archives, release assets (integrity-sensitive, public) |
| Hosted CI / GitHub API → local verification | Run, artifact and release readback crosses the network; credentials must not leak and stale/different-SHA runs must not count. | Workflow run metadata, artifacts (token-authenticated reads) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-15-01 | Tampering | tests/scripts/verify-v02-adoption.py | high | mitigate | `--self-test docs` 39/39 controls rejected; v02_adoption_docs(+_controls) CTest | closed |
| T-15-02 | Tampering | tests/scripts/verify-v02-adoption.py | high | mitigate | `--self-test docs` 39/39 controls rejected; v02_adoption_docs(+_controls) CTest | closed |
| T-15-03 | Tampering | docs/support/v0.2.0.md | high | mitigate | Ledger regenerated from fresh nonce-bound receipt; `verify-support-ledger.py --check-ledger`/`--check-current` (release corpus job) | closed |
| T-15-04 | Tampering | tests/scripts/verify-support-ledger.py | high | mitigate | ledger 15 + sidecar 21 rejection controls; v02 CTest | closed |
| T-15-05 | Tampering | tests/scripts/verify-v02-consumers.py | high | mitigate | relocated C/C++ consumers, 6 negative controls; downloaded consumer receipt in release run 39406047351 | closed |
| T-15-06 | Tampering | tests/scripts/verify-v02-consumers.py | high | mitigate | relocated C/C++ consumers, 6 negative controls; downloaded consumer receipt in release run 39406047351 | closed |
| T-15-07 | Tampering | tests/scripts/verify-v02-adoption.py | high | mitigate | `--self-test docs` 39/39 controls rejected; v02_adoption_docs(+_controls) CTest | closed |
| T-15-08 | Tampering | tests/scripts/verify-v02-adoption.py | high | mitigate | `--self-test docs` 39/39 controls rejected; v02_adoption_docs(+_controls) CTest | closed |
| T-15-09 | Tampering | tests/scripts/measure-release-baseline.sh | high | mitigate | paired v0.1.0 measurement receipt; candidate-performance job green in 39406047351 | closed |
| T-15-10 | Tampering | tests/scripts/measure-release-baseline.sh | high | mitigate | paired v0.1.0 measurement receipt; candidate-performance job green in 39406047351 | closed |
| T-15-11 | Tampering | tests/scripts/run-bounded-fuzz.sh | high | mitigate | hosted campaign run 39357838513 (exact SHA bd7a7f5) validated by `--verify-hosted`; receipt a658e06d… | closed |
| T-15-12 | Tampering | .github/workflows/ci.yml | high | mitigate | linux-asan-ubsan campaign + policy controls; exact-head required checks green on PR #72 | closed |
| T-15-13 | Tampering | tests/scripts/verify-v02-source-archive.py | high | mitigate | `--self-test` 7 accepted / 44 rejected; live tag archive checked against source-archive-receipt.json | closed |
| T-15-14 | Tampering | tests/scripts/verify-release-candidate.sh | high | mitigate | `--self-test` 2 accepted / 25 rejected incl. fixture-leak and substitution controls | closed |
| T-15-15 | Tampering | .github/scripts/verify-release-gates.sh | high | mitigate | `--self-test` exit 0 (20 omission + 33 wiring + recovery controls) | closed |
| T-15-16 | Tampering | .github/scripts/verify-release-gates.sh | high | mitigate | `--self-test` exit 0 (20 omission + 33 wiring + recovery controls) | closed |
| T-15-17 | Tampering | .github/workflows/release.yml | high | mitigate | final-gate-and-publish only after strict aggregate; release run 39406047351 all jobs success; rehearsal 39396554673 | closed |
| T-15-18 | Tampering | .github/workflows/release.yml | high | mitigate | final-gate-and-publish only after strict aggregate; release run 39406047351 all jobs success; rehearsal 39396554673 | closed |
| T-15-19 | Tampering | .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-DELIVERY.md | high | mitigate | `verify-v02-delivery.py --stage phase-pr` and `--stage published` readback PASS with 6 negative controls | closed |
| T-15-20 | Tampering | .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-DELIVERY.md | high | mitigate | `verify-v02-delivery.py --stage phase-pr` and `--stage published` readback PASS with 6 negative controls | closed |
| T-15-SC | Tampering | Package installation | high | mitigate | No npm/pip/cargo install in workflows or scripts (grep-verified 2026-10-20) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

Audit note: plan 15-06 also fixed a credential-forwarding defect in `tests/scripts/verify-v02-fuzz.py` (bearer token was forwarded to the signed-blob redirect); `Authorization` is now dropped on redirect (commit bd7a7f5).

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-20 | 21 | 21 | 0 | gsd-secure-phase (L1, plan-time register) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-20
