---
phase: GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release
verified: 2026-10-20T12:00:00Z
status: passed
score: 12/12 must-haves verified
covered_files:
  - .github/workflows/release.yml
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-01-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-01-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-02-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-02-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-03-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-03-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-04-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-04-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-05-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-05-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-06-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-06-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-07-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-07-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-08-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-08-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-09-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-09-SUMMARY.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-10-PLAN.md
  - .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-10-SUMMARY.md
  - README.md
  - docs/game-acceptance.md
  - docs/support/v0.2.0.md
  - tests/expected-tests.txt
  - tests/scripts/verify-support-ledger.py
  - tests/scripts/verify-v02-adoption.py
  - tests/scripts/verify-v02-delivery.py
covered_digest: "v3:sha256:f2d69194bfffbb74cf495a2e286d974d688b08cd546f304a326d9dbab4fddecb"
behavior_unverified: 0
overrides_applied: 0
advisory:
  - finding: "Measured DMG slowdown vs v0.1.0 (+14.86%, margin 1.62%) is disclosed in the published performance receipt and docs/release.md but not in the release notes body or support ledger prose"
    category: other
    reason: "SHIP-11 requires a measured comparison to ship, which it does; user-facing visibility is a polish item. The receipt states no equivalent-speed claim is made."
    evidence_status: "receipt regression_disposition read from the live asset"
  - finding: "Open review warnings WR-01..WR-08 (release-pipeline hardening: write token on producer jobs, constant performance review note, tarball byte stability, verifier trust boundary, self-attested fuzz/consumer receipts)"
    category: security
    reason: "All affect future-release robustness, not the correctness of the v0.2.0 evidence that was read back independently. Recommend scheduling before v0.2.1."
    evidence_status: "15-REVIEW.md / 15-REVIEW-DISPOSITION.md, 0 critical"
---

# Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release Verification Report

**Phase Goal:** Adopters get a qualified v0.2.0 release whose ledger, docs and consumers accurately state what DMG-CPU-B and CGB-CPU-E support has been proven.
**Verified:** 2026-10-20
**Status:** passed
**Re-verification:** No, initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | CGB-11: guide and README state "No CGB game-level evidence exists"; removal or a game claim fails the entry point | VERIFIED | `docs/game-acceptance.md:14`, `README.md:16`, and the live release body all contain the sentence. `verify-v02-adoption.py --check game` passes (14 checks) and `--self-test game` exits 0 (its negative controls reject). |
| 2 | Rebound attempt closed, Libbet remains the DMG game acceptance, no CGB game bytes admitted | VERIFIED | `docs/game-acceptance.md:18` states it. No CGB game fixtures were added. |
| 3 | SHIP-09: ledger names DMG-CPU-B and CGB-CPU-E with mapper matrix, evidence class, denominators, xfails, exclusions | VERIFIED | `docs/support/v0.2.0.md` has per-suite, model, mode and speed denominator rows (for example samesuite 74/74 eligible, 12 pass, 62 matched xfail) and an evidence-class paragraph. Physical CGB-E is stated as UNKNOWN/POLICY. |
| 4 | Ledger is bound to a nonce-bound corpus receipt and the exact source | VERIFIED | The published `support-ledger.json` has `corpus_receipt_producer_revision` = ab301aa (the tag), `source_relation` exact, and receipt sha c9fbb22c.... This matches the sha in 15-DELIVERY.md. |
| 5 | SHIP-10: C and C++ consumers exercise profile selection, probe, RGB555 and RTC through a relocated package | VERIFIED | The published `v02-consumer-receipt.json` shows result passed, `isolated_prefix` true, `prefix_origin` supplied-relocated-install, source_sha ab301aa. The local `v02` CTest label ran 11/11. |
| 6 | Adoption docs, notices and notes name only shipped behavior, unsigned/not-notarized macOS and the limits | VERIFIED | `verify-v02-adoption.py --release-notes` over the live body passes (8 checks). The body states the unsigned status and that physical CGB-E remains UNKNOWN/POLICY. |
| 7 | SHIP-11: paired v0.1.0 vs candidate DMG performance measured | VERIFIED | The published `v02-performance-receipt.json` has 30 paired samples, result passed, and a +14.86% slowdown with a 1.62% margin. It is recorded as accepted-with-disclosed-regression with no equivalent-speed claim. See advisory. |
| 8 | Actual 60 s bounded fuzz campaign | VERIFIED | The published fuzz receipt has `synthetic` false, `execution_count` 539, `elapsed_seconds` 61.4, `outcome` passed, `source_sha` ab301aa. Hosted run 39357838513 at bd7a7f5 succeeded. |
| 9 | Exact-tag source archive keeps licensed fixture notices; binary packages are fixture-free | VERIFIED | `source-archive-receipt.json` is published. `--stage published` runs `verify-v02-source-archive.py --check-receipt` over a fresh GitHub tag archive and passes. |
| 10 | Release qualification is bound to exact evidence; publication only after strict aggregate gate | VERIFIED | Release run 39406047351 concluded success at 08e7309. `verify-v02-delivery.py --stage published` over a fresh download of all 22 assets returned `PASS: published release, tag, assets and final readback agree with live state`. |
| 11 | v0.2.0 is published, exact tag, protected merges, nothing left in draft | VERIFIED | `gh release view v0.2.0`: `isDraft` false, published 2026-10-20T10:25:34Z, 22 assets. The tag resolves to ab301aa. PRs #70, #72, #73, #74 and #76 are merged. No open issues. Only #75 (0.2.1) is open and intentionally unmerged. |
| 12 | Phase stops; no auto-advance | VERIFIED | `15-DELIVERY.md` records the stop. The working tree has only planning-state edits, no code changes. |

**Score:** 12/12 truths verified (0 behavior-unverified, 0 overrides)

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CGB-11 | 01, 02, 04, 09, 10 | SATISFIED | The ledger and docs state explicitly that no CGB game-level evidence exists (truths 1, 2 and 6). This is the second branch of the requirement's "or". |
| SHIP-09 | 02, 04, 08, 09, 10 | SATISFIED | Truths 3 and 4. |
| SHIP-10 | 03, 04, 07, 08, 09, 10 | SATISFIED | Truths 5 and 6. |
| SHIP-11 | 05, 06, 07, 08, 09, 10 | SATISFIED | Truths 7 through 11. |

All four IDs are marked `[x]` and Complete in REQUIREMENTS.md. There are no orphaned Phase 15 requirements.

### Behavioral and Probe Checks

| Check | Result |
|-------|--------|
| `verify-v02-adoption.py --check game` and `--self-test game` | PASS |
| `verify-v02-adoption.py --release-notes <live body>` | PASS (8 checks) |
| `verify-v02-delivery.py --stage published` against a fresh `gh release download` of all 22 assets | PASS |
| `ctest --test-dir build -R v02_` | 11/11 pass |
| Live GitHub state (read-only) | Release published, tag ab301aa, release run and fuzz run success |

### Code Review Assessment

15-REVIEW.md reports 0 critical findings, 8 warnings and 8 info items, all open and advisory. The independent live readback verified the actual v0.2.0 artifacts, so none of the open findings falsifies a claim made about this release:
- WR-04 (constant performance note): the measured regression is real and recorded accurately, not hidden. The gate is weak for future releases.
- WR-05, WR-06, WR-02 and WR-08 (tarball byte stability, verifier trust boundary, receipt self-attestation): these are trust-model hardening. The release passed the gates on this occasion and was read back independently.
- WR-01 (write token on producer jobs) and WR-07 (DMG KEY1 oracle seeds): future-hardening items.

### Human Verification

None. Physical CGB-E hardware and CGB game-level evidence are stated limits in the ledger, not phase deliverables.

### Anti-Patterns

No unreferenced TBD, FIXME or XXX markers were hunted exhaustively. The phase relies on dedicated contract validators with negative controls, and those validators passed.

---

_Verified: 2026-10-20_
_Verifier: Claude (gsd-verifier)_
