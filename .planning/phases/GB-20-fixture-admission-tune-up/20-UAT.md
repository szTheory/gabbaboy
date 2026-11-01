---
status: complete
phase: GB-20-fixture-admission-tune-up
source: 20-01-SUMMARY.md, 20-02-SUMMARY.md, 20-03-SUMMARY.md, 20-04-SUMMARY.md, 20-05-SUMMARY.md, 20-06-SUMMARY.md, 20-07-SUMMARY.md, 20-08-SUMMARY.md, 20-09-SUMMARY.md
started: 2026-11-01T18:42:18.466732+00:00
updated: 2026-11-01T18:42:18.466732+00:00
---

## Automated Evidence

Final automated evidence at implementation head 39eb048e7770652b84a3fc5da7aaa3890adbd70c: configure/build passed; the full CTest run passed 1,708 tests, and its three configure-time revision-snapshot controls passed after reconfigure/build in a focused retest. The source-archive controls and release-candidate replay passed. Exact-head pull-request and push CI matrices passed, including native Windows/macOS/Linux, sanitizer, CMake floor, and required-native gates. The separate preview workflow passed Linux/macOS installed-package smoke, downloaded macOS player receipt verification, and its aggregate gate. Security audit and final archive/path review are clean. No fixture was admitted; RIGHTS-01 remains pending because automated checks do not establish legal permission or grant scope. No manual UAT is required.

## Current Test

[testing complete]

## Tests

### 1. Fixture admission rejects coordinated rewrites, missing pins, unregistered repository changes, and changed root license bytes.
expected: "Fixture admission rejects coordinated rewrites, missing pins, unregistered repository changes, and changed root license bytes."
result: pass
source: automated
summary_file: 20-01-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-fixture-admission.py --self-test", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'"]

### 2. CI and release workflow policy requires admission before fixture consumption and compares actual core bytes before reuse or consumer execution.
expected: "CI and release workflow policy requires admission before fixture consumption and compares actual core bytes before reuse or consumer execution."
result: pass
source: automated
summary_file: 20-01-SUMMARY.md
coverage_id: D2
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_(group_(ci|release_jobs)|coverage(_controls)?|check)$'", "python3 -I .github/scripts/verify-workflow-policy.py --check --root ."]

### 3. Core and player product trees use distinct exact path maps, protected byte identities, optional MIT sidecar verification, and complete stage inventories.
expected: "Core and player product trees use distinct exact path maps, protected byte identities, optional MIT sidecar verification, and complete stage inventories."
result: pass
source: automated
summary_file: 20-01-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout core", "python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player", "Actual non-testing core install and existing player package stage accepted; extracted core tree matched the written inventory."]

### 4. Real installed and extracted core products are checked against shared policy and accepted stage inventory before consumers start.
expected: "Real installed and extracted core products are checked against shared policy and accepted stage inventory before consumers start."
result: pass
source: automated
summary_file: 20-02-SUMMARY.md
coverage_id: D1
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'"]

### 5. Core archive and extracted-tree controls reject hidden payloads, fixture mutations, and notice changes while preserving source-archive policy.
expected: "Core archive and extracted-tree controls reject hidden payloads, fixture mutations, and notice changes while preserving source-archive policy."
result: pass
source: automated
summary_file: 20-02-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-v02-source-archive.py --self-test", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^preview_package_smoke$'", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'"]

### 6. Release checks validate actual core archive and gabbaboy-notices.txt bytes and reject missing, altered, or misnamed sidecars.
expected: "Release checks validate actual core archive and gabbaboy-notices.txt bytes and reject missing, altered, or misnamed sidecars."
result: pass
source: automated
summary_file: 20-02-SUMMARY.md
coverage_id: D3
evidence: ["bash tests/scripts/verify-release-candidate.sh --self-test", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^v02_source_archive_controls$'", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$'", "python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs"]

### 7. Source receipt and Linux/core archive parsing enforce decompressed stream, per-header metadata, aggregate metadata byte, and extension chain count bounds before metadata payload reads while preserving trusted source identity checks.
expected: "Source receipt and Linux/core archive parsing enforce decompressed stream, per-header metadata, aggregate metadata byte, and extension chain count bounds before metadata payload reads while preserving trusted source identity checks."
result: pass
source: automated
summary_file: 20-02-SUMMARY.md
coverage_id: D4
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^v02_source_archive_controls$'", "bash tests/scripts/verify-release-candidate.sh --self-test", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(plan_cap|planning_hygiene_controls|summary_coverage_live)$'"]

### 8. Archive-wide extension-header counting survives ordinary members, rejects the first over-limit header before parsing its payload, and preserves independent long-path source positives.
expected: "Archive-wide extension-header counting survives ordinary members, rejects the first over-limit header before parsing its payload, and preserves independent long-path source positives."
result: pass
source: automated
summary_file: 20-02-SUMMARY.md
coverage_id: D5
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^v02_source_archive_controls$'", "bash tests/scripts/verify-release-candidate.sh --self-test", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(plan_cap|planning_hygiene_controls|summary_coverage_live)$'"]

### 9. The real player stage passes the production policy wrapper, and an isolated seeded ROM is rejected before player execution.
expected: "The real player stage passes the production policy wrapper, and an isolated seeded ROM is rejected before player execution."
result: pass
source: automated
summary_file: 20-03-SUMMARY.md
coverage_id: D1
evidence: ["bash tests/scripts/verify-phase3-player.sh --check-package-policy build/phase3-player/package-stage/installed-prefix; seeded Mooneye ROM rejected as product-fixture-leak"]

### 10. Real-tree controls reject renamed and suffixless fixture bytes, unknown subtree members, changed fixture identities, and missing or changed fixture, GabbaBoy, and SDL notices.
expected: "Real-tree controls reject renamed and suffixless fixture bytes, unknown subtree members, changed fixture identities, and missing or changed fixture, GabbaBoy, and SDL notices."
result: pass
source: automated
summary_file: 20-03-SUMMARY.md
coverage_id: D2
evidence: ["bash tests/scripts/verify-phase3-player.sh --self-test-package-policy build/phase3-player/package-stage/installed-prefix; all 21 isolated mutation cases rejected and candidate inventory preserved"]

### 11. The shared portable product checker continues to exercise the player layout policy independently of the macOS build lane.
expected: "The shared portable product checker continues to exercise the player layout policy independently of the macOS build lane."
result: pass
source: automated
summary_file: 20-03-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-fixture-admission.py --self-test-packages --layout player"]

### 12. Direct manifest and repository walks reject excess directory entries, while Git output byte and record overflows are rejected during streaming with child cleanup.
expected: "Direct manifest and repository walks reject excess directory entries, while Git output byte and record overflows are rejected during streaming with child cleanup."
result: pass
source: automated
summary_file: 20-04-SUMMARY.md
coverage_id: BOUNDED-INPUT
evidence: ["python3 -I tests/scripts/verify-fixture-admission.py --self-test", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'"]

### 13. Documentation states all enforced filesystem, Git stdout, Git record, manifest-file, and retained-stderr limits and rejection tokens.
expected: "Documentation states all enforced filesystem, Git stdout, Git record, manifest-file, and retained-stderr limits and rejection tokens."
result: pass
source: automated
summary_file: 20-04-SUMMARY.md
coverage_id: BOUNDED-DOCS
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^fixture_(admission|product_).*'"]

### 14. Product validation rejects a modified complete policy and coordinated forbidden inventory mutation, and accepts only one supported configuration export.
expected: "Product validation rejects a modified complete policy and coordinated forbidden inventory mutation, and accepts only one supported configuration export."
result: pass
source: automated
summary_file: 20-05-SUMMARY.md
coverage_id: PRODUCT-POLICY-PIN
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_(core|player)_controls|installed_runner_smoke|preview_package_smoke)$'", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^test_budget(_controls)?$'"]

### 15. Forbidden fixture bytes are rejected at required and one_of generated product paths for both layouts while clean products and exact pinned file identities remain accepted.
expected: "Forbidden fixture bytes are rejected at required and one_of generated product paths for both layouts while clean products and exact pinned file identities remain accepted."
result: pass
source: automated
summary_file: 20-05-SUMMARY.md
coverage_id: FORBIDDEN-GENERATED-BYTES
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_core_controls|fixture_product_player_controls)$'", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(fixture_product_(core|player)_controls|installed_runner_smoke|preview_package_smoke)$'", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^v02_source_archive_controls$'", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^(plan_cap|planning_hygiene_controls|summary_coverage_live)$'"]

### 16. Trusted publisher verifies macOS and Windows downloaded products before draft validation; hostile archives, altered bytes, and unsafe paths reject.
expected: "Trusted publisher verifies macOS and Windows downloaded products before draft validation; hostile archives, altered bytes, and unsafe paths reject."
result: pass
source: automated
summary_file: 20-06-SUMMARY.md
coverage_id: PLATFORM-ARCHIVE-TRUST
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$' (installed-product positives and archive policy negatives, including hidden metadata limits and cleanup/retry)", "python3 -I .github/scripts/verify-workflow-policy.py --self-test --group release_jobs --root ."]

### 17. The independent workflow source snapshot and stable control registry cover the platform archive trust implementation and its mutations.
expected: "The independent workflow source snapshot and stable control registry cover the platform archive trust implementation and its mutations."
result: pass
source: automated
summary_file: 20-06-SUMMARY.md
coverage_id: PLATFORM-ARCHIVE-COVERAGE
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_coverage$' (exact reviewed checker and bounded-helper source/AST pins)", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_coverage_controls$' (86 negative controls, including independent resource/cleanup/path registry removal checks)"]

### 18. Product archives are bounded before hidden metadata or payload consumption, and missing-checker/late-rejection failures leave a retryable clean destination.
expected: "Product archives are bounded before hidden metadata or payload consumption, and missing-checker/late-rejection failures leave a retryable clean destination."
result: pass
source: automated
summary_file: 20-06-SUMMARY.md
coverage_id: BOUNDED-ARCHIVE-METADATA-CLEANUP
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$'", "python3 -I .github/scripts/safe_extract_package.py --self-test"]

### 19. Windows drive and alternate-stream archive names reject, and directory/file targets are proven inside the extraction root before any creation.
expected: "Windows drive and alternate-stream archive names reject, and directory/file targets are proven inside the extraction root before any creation."
result: pass
source: automated
summary_file: 20-06-SUMMARY.md
coverage_id: WINDOWS-ARCHIVE-PATH-CONTAINMENT
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_release_jobs$' (drive, ADS, injected directory/file escape controls, unchanged outside sentinels, zero outside write attempts)", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_(coverage|coverage_controls)$' (exact source pin and independent removal checks for all four path controls)"]

### 20. Fixture admission workflow calls must match exact parsed command words and repository root, while missing subject inputs fail before copying.
expected: "Fixture admission workflow calls must match exact parsed command words and repository root, while missing subject inputs fail before copying."
result: pass
source: automated
summary_file: 20-07-SUMMARY.md
coverage_id: EXACT-WORKFLOW-GATE
evidence: ["python3 -I .github/scripts/verify-workflow-policy.py --self-test --group ci --root .", "ctest --preset phase1 --output-on-failure --no-tests=error -R '^workflow_policy_group_ci$'"]

### 21. Notice checks require the reviewed core/player product distinction and reject missing or contradictory product inventory claims.
expected: "Notice checks require the reviewed core/player product distinction and reject missing or contradictory product inventory claims."
result: pass
source: automated
summary_file: 20-08-SUMMARY.md
coverage_id: NOTICE-INVENTORY-CLAIM
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^(v02_adoption_docs|v02_adoption_docs_controls|v02_support_ledger_controls|release_disclosure_generator|release_disclosure_controls|support_claims)$'"]

### 22. A source-only mutant passes admission through a separately verified fixed baseline object store while its build remains unknown and unqualified.
expected: "A source-only mutant passes admission through a separately verified fixed baseline object store while its build remains unknown and unqualified."
result: pass
source: automated
summary_file: 20-09-SUMMARY.md
coverage_id: SOURCE-ONLY-BASELINE
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^acceptance_dense_input_controls$'"]

### 23. Missing and empty baseline stores reject with baseline-object-unavailable; changed fixture bytes fail closed before consumer execution.
expected: "Missing and empty baseline stores reject with baseline-object-unavailable; changed fixture bytes fail closed before consumer execution."
result: pass
source: automated
summary_file: 20-09-SUMMARY.md
coverage_id: SOURCE-ONLY-NEGATIVES
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error -R '^(acceptance_dense_input_controls|fixture_admission_controls|fixture_admission_repository)$'"]

## Summary

total: 23
passed: 23
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
