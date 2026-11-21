---
phase: "24"
slug: "resolve-remaining-v0-4-evidence-and-verification-gaps"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-11-16"
---

# Phase 24 — Security

> ASVS L1 review of the bounded evidence assessment and its production checker controls.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Report fields → accepted evidence | Locally authored assessment claims are checked against immutable source facts and preserve unresolved authority gates. | Report rows, requirement owners/statuses, source paths and blob digests |
| Revision argument → immutable source | Full commit identities select Git objects rather than mutable refs or dirty checkout contents. | Input, baseline, checker/report, and handoff commit identities |
| Historical outcome → current disposition | Historical passes and metadata do not promote current freshness, rights, or requirement completion. | Prior verification outcomes, current audit disposition, freshness and remaining gates |
| Roadmap exception → execution budget | D-205 permits only the exact sixth phase and one ordinary plan under the actual 40-plan ceiling. | Phase names, declared caps, plan paths, and approval record |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-24-01 | Tampering | v04-gap-assessment report parser | high | mitigate | Exact row/key/source checks plus causal production-CLI controls for false completion, owner drift, and freshness promotion; the complete 632-control self-test passed at `65b31a69840bfec232806f808f03fb44c6e21174`. | closed |
| T-24-02 | Tampering / Repudiation | Git snapshot and evidence boundary | high | mitigate | Full immutable input and baseline commits, source digests, historical-byte comparison, and substitution/dirty-tree controls; immutable controls pass at `65b31a69840bfec232806f808f03fb44c6e21174`. | closed |
| T-24-03 | Elevation of privilege | Evidence and pending-verification handoff | high | mitigate | Production handoff validation preserves Pending owners, `open`/`gaps_found`, the independent D-103 gate, and phase-verification routing; immutable controls pass at `65b31a69840bfec232806f808f03fb44c6e21174`. | closed |
| T-24-04 | Tampering | D-205 plan-cap exception | high | mitigate | Candidate `65b31a69840bfec232806f808f03fb44c6e21174` strips exactly one leading BOM before the canonical fence match and fails closed on repeated BOMs. Immutable production-CLI controls pass with 632 controls; the exact-candidate deep review is clean; only the two configured CTests passed with TIMEOUT=30 and the 125-control floor. See `24-RECOVERY-REVIEW.md` and `24-VALIDATION.md`. | closed |
| T-24-05 | Denial of service | planning_hygiene_controls | medium | mitigate | Reused bounded fixtures and the existing 30-second timeout; only `plan_cap` and `planning_hygiene_controls` ran at candidate `65b31a69840bfec232806f808f03fb44c6e21174`, preserving the 125-control floor. | closed |
| T-24-SC | Tampering | Package installs | high | mitigate | No dependency or package-manager installation was introduced; the checker uses the existing Python standard library and CMake tooling. | closed |

*Status: verified — all six threats are mitigated; no accepted risk or requirement status changed*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-16 | 6 | 5 | 1 | Orchestrator; T-24-04 reopened by exact-candidate code review |
| 2026-11-17 | 6 | 6 | 0 | Orchestrator; exact-candidate recovery review and focused checks |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** recovery mitigation verified for Phase 24 assessment scope; original requirements and milestone gates remain open
