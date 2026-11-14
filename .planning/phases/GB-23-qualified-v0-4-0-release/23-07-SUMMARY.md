---
phase: GB-23-qualified-v0-4-0-release
plan: "07"
subsystem: native-state-compatibility
tags: [release-token, immutable-pins, same-release-state]
requires:
  - phase: GB-23-qualified-v0-4-0-release
    provides: Protected implementation merge and actual release-please version output.
provides:
  - Actual generated 0.4.0 CMake and manifest agreement before any freeze or tag.
  - Compiled release-token-only native-state pins with an immutable compatibility disposition.
affects: [23-05, state-compatibility]
tech-stack:
  added: []
  patterns:
    - Emit actual compiled state pins and transform only the emission schema label.
key-files:
  created: []
  modified:
    - tests/baseline/state-goldens-v1.json
    - tests/data/state-compatibility.json
    - docs/state-format.md
key-decisions:
  - "Apply D-113/D-120 same-release-only policy concretely to0.4.0; keep format/behavior tokens1 and battery saves as the cross-version path."
requirements-completed: []
coverage:
  - id: ACTUAL-VERSION-OUTPUT
    description: "The real canonical release-please PR generated matching exact0.4.0 CMake and manifest output before content-window or tag operations."
    human_judgment: false
    verification:
      - kind: integration
        ref: "release-please42973594341 release job created PR147 atd4892190, base6c3ffafb. Immutable Git-object CMake VERSION and manifest values both0.4.0; wrong/mixed-version controls retained and release_version_v04_controls passed at78d1cd4c."
        status: pass
  - id: RELEASE-TOKEN-STATE-TRANSITION
    description: "All three compiled synthetic fixture pins advance only the release token, with unchanged format/behavior tokens, fixture descriptors, ROM identities and state sizes."
    human_judgment: false
    verification:
      - kind: integration
        ref: "Compiled test_state_codec state_portable_pins emission at actual0.4 source; schema-only transformation and immutable-base comparison passed. State commitf0345477 binds main6c3ffafb, old goldenb5d9b340 and new golden97a54a14; independent continuation evidencef80bdf54 remains resolvable at that base."
        status: pass
      - kind: integration
        ref: "state_codec_matrix, state_semantic_bounds, state_portable_pins, state_pin_controls, state_pin_planning, state_refusal and state_refusal_controls all passed at78d1cd4c with base6c3ffafb in the22-case focused stream; standalone immutable planning check passed atf0345477. See23-EVIDENCE.md and retained state-transition receipts."
        status: pass
status: complete
completed: 2026-11-11
---

# Phase 23 Plan 07: actual version and native-state pins

The actual release-please output targets0.4.0, and compiled pins now satisfy the existing same-release state policy. No version correction mechanism or new state semantics was introduced.

The exact immutable main base is `6c3ffafb0976e5832863976b1bc1786c88c33753`; actual generated version source is `d4892190cbdc614845f03ca346d964a20d6325b6`. State preparation commit `f0345477794b73a3d3e28e560650748c99b7045b` changes only the golden, compatibility disposition and state-format documentation. Old/new canonical golden digests are `b5d9b3404b627a776268304551d2c2d86cae69f580752d11e3d22fd5666d3750` and `97a54a14637052d63876cb36737adac57b0d7756d63931f1ab662faeaca34979`.

Format and behavior remain1. Cross-release native states remain refused; battery saves remain the cross-version persistence path. Original synthetic fixtures only were used. No game or diagnostic fixture was acquired, admitted or executed.

The first local state check could not start two cases before their test_state_internal target was built; both then passed unchanged. All seven passed again together on the later prepared version subject. This records the setup failure rather than claiming a skipped result as evidence.

Plan23-05 owns generated-copy review, same-source platform receipts, H/R1/W/R2/nightly and the separate one-way publication decision. Its test-fixture failures hold that new boundary; they do not change the passing state transition. No content window, rehearsal, tag or publication has occurred.
