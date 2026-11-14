---
phase: GB-23-qualified-v0-4-0-release
plan: "05"
subsystem: qualified-release
requires:
  - phase: GB-23-qualified-v0-4-0-release
    provides: Reviewed claims, disclosure, implementation and actual 0.4.0 state/version output.
provides:
  - Exact-source v0.4.0 publication through the existing trusted lifecycle.
  - Actual public-byte inventory and platform consumer/source/notice/fixture proof.
affects:
  - 23-06
  - milestone-audit
key-files:
  created:
    - .planning/phases/GB-23-qualified-v0-4-0-release/23-05-SUMMARY.md
  modified:
    - .planning/phases/GB-23-qualified-v0-4-0-release/23-EVIDENCE.md
key-decisions:
  - Preserve the approved permanent product/tag source and all original asset bytes through scoped control-plane recovery.
  - Consume the single carried conditional publication request before submission; no additional hosted retry.
requirements-completed: []
coverage:
  - id: VERSION-WINDOW-REHEARSAL
    description: Actual generated 0.4.0 output, reviewed H, record-only W, R1/R2 and exact-tree nightly qualify source S.
    human_judgment: false
    verification:
      - kind: e2e
        ref: "23-EVIDENCE.md final qualification table; actual R1 43245302329, R2 43258530932 and nightly 43269869181; production active-window/merged-source/nightly gates passed again in publisher 43526085579 at S."
        status: pass
  - id: QUALIFIED-PUBLICATION
    description: The existing trusted publisher publishes the approved exact-source v0.4.0 draft after all real platform, corpus, consumer and final byte gates.
    human_judgment: false
    verification:
      - kind: e2e
        ref: "Actual release-please 43526085579 attempt 1 on control fbea1e2cc70f7c2ab9ea5820fa92ca18ddf997e8 completed success; live release 443425157 published 2026-11-14T00:04:34Z with direct tag 3de1b0e427f37a202be4469dd818266f359c8b20. D183 authority and single carried D191/D192 request recorded separately."
        status: pass
  - id: PUBLIC-BYTE-READBACK
    description: All 22 public assets match the qualified inventory; original 20 tuples and notes remain fixed, and actual products/source/consumers retain their declared limits.
    human_judgment: false
    verification:
      - kind: integration
        ref: "23-EVIDENCE.md independent public-byte readback; production published-assets/final-receipt/source/evidence checks pass, four real product positives and four product-fixture-leak insertion refusals pass, and exact public archive hashes bind current native hosted plus post-publication macOS consumers."
        status: pass
status: complete
completed: 2026-11-14
---

# Phase 23 Plan 05 — Qualified v0.4.0 publication

[v0.4.0](https://github.com/szTheory/gabbaboy/releases/tag/v0.4.0) is published from permanent product source S. The reviewed correction, actual merged-main qualification, source/rehearsal/nightly chain and final publisher are distinguished in [23-EVIDENCE.md](23-EVIDENCE.md). The original owner publication decision remained valid; the final single conditional request was consumed before submission and succeeded without renewal or tag/asset replacement.

The independent readback verifies all 22 actual public downloads and actual pre-publish inventory, the fixed original 20 tuples/body, receipt/checksum bindings, source archive, owner evidence families, product positives and insertion refusals. Linux/Windows consumers execute natively in the same successful publisher run on bytes with the exact public hashes; native macOS public-byte consumers and host continuation also pass locally. Local restored-tag and cross-platform command setup failures remain recorded rather than being called product passes.

No CGB game or real diagnostic fixture was newly admitted or executed. Four fixture/rights/diagnostic requirements remain Pending; unsigned/not-notarized and model/hardware/perception/timing/platform limits are unchanged. Plan 06 reconciles REL-01 and automated release closure; Plan 08 owns final milestone lessons and the owner-controlled phase boundary.
