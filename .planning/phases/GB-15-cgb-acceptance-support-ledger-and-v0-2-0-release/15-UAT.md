---
status: complete
phase: GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release
source: 15-01-SUMMARY.md, 15-02-SUMMARY.md, 15-03-SUMMARY.md, 15-04-SUMMARY.md, 15-05-SUMMARY.md, 15-06-SUMMARY.md, 15-07-SUMMARY.md, 15-08-SUMMARY.md, 15-09-SUMMARY.md, 15-10-SUMMARY.md
started: 2026-10-20T15:34:11.015728+00:00
updated: 2026-10-20T15:34:11.015728+00:00
---

## Automated Evidence

OpenGSD 1.18.0 classifies every one of the 42 structured SUMMARY deliverables across 10 plans as automated: zero present entries and zero errors. D-069 and the owner instruction authorize automated closure without a confirmation-only checkpoint. Both auto-advance flags remain false.

All 10 bounded commit windows end at reachable ancestors of the UAT head. 15-01, 15-04, 15-06 and 15-07 record their claim in the legacy `actuals.commits` location, which produces a top-level-field warning; their counts were checked directly. Nine windows match exactly. The 15-06 window `0cbecc9..bd7a7f5` holds 23 commits because the plan was parked and resumed, so 15-02, 15-04 and 15-07 commits and the pause commit fall inside it. A manual recount finds exactly the 9 commits tagged `15-06` that the SUMMARY claims, so this is not a lost or invented commit.

| Plan | Base | After | Claimed / measured |
|---|---|---|---|
| 15-01 | `380cae907d524095930d12d9b958889cc4ac7b24` | `e2c002e1cfdb6c5f51fc9c43df036ce7dcd6fc65` | 4 / 4 |
| 15-02 | `1f67527a9ec4f8629f9b2b26ce74e1857ae791f0` | `9ab24c92b883a9ec4e8c38093efeba22467668f9` | 5 / 5 |
| 15-03 | `f81a3508ad83dc4177bc63949421ab77832bd639` | `a03b0c2d11ef60a4f960436aaea4266018deb77e` | 4 / 4 |
| 15-04 | `954ca111c7e6de1a8d27038c7b6b462206847e2c` | `338edc1bfc04b83ea75c304555645c02ac618f80` | 2 / 2 |
| 15-05 | `f44b7e9f7c5ec70838f4558b5e708d6058f8c8e1` | `86659914e2a3ba829a347ad0326a6be43e592afb` | 4 / 4 |
| 15-06 | `0cbecc9bc1582e76c88153dfb4f898b116e6bafd` | `bd7a7f579d92387bf99801ee91c15123fa2d4c04` | 9 / 9 tagged (23 interleaved) |
| 15-07 | `06ef6246058a5e1845c48d8c1fe85702547086e6` | `0f9cf11db53f8129fc5560477221ea3974134cc2` | 4 / 4 |
| 15-08 | `1243222809c134b4ce5e4a8e041d9376a95c8db2` | `e023e171151f68ddb3f2400b0c313a3fb55428cf` | 2 / 2 |
| 15-09 | `208e278dd1d0c9f7178b495b6c294fac7ed57139` | `9d508574989d2c8ca2c06a3641c83c90b19bd973` | 4 / 4 |
| 15-10 | `1e4f2d3a6cd1ac091632547c40580f61bfd45888` | `9ab8303b876aa9ca3a1f188ebbeb447727c50d37` | 14 / 14 |

Phase gates already on record:
- Goal verification in `15-VERIFICATION.md` passed 12/12, and CGB-11, SHIP-09, SHIP-10 and SHIP-11 are traced complete.
- Security records 21/21 threats closed with zero open.
- Nyquist validation is compliant.
- Code review is advisory: zero critical findings, and 8 warnings plus 8 info items remain open in `15-REVIEW-DISPOSITION.md` as v0.2.1 follow-ups. None of them invalidates a v0.2.0 claim.

Release `v0.2.0` is published from tag source `ab301aa` with 22 assets. A fresh readback reports that the published release, tag, assets and final readback agree with live state. The phase PR #72 and the follow-up fix PRs #73 and #74 merged only after their exact-head checks passed. Bookkeeping head `c5ff479` passed preview-package-smoke, required-native and fixture-repro before squash-merging as `f5a3bd5` (#77). Release PR #75 (0.2.1) stays open by design. The final UAT revision needs its own exact-head checks before merge.

A fresh local re-run with nonce `9bbaaf68` produced a complete 107/107 corpus receipt: 25 observed passes, 82 matched expected failures and 4,959 assertions. The support ledger reports a current pass for version 0.2.0. The installed-package C and C++ consumers pass all four behavioral checks.

Every per-task verification command re-ran green. The 15-02, 15-03-1, 15-05-1 and 15-10-2 commands needed their current argument forms because later hardening superseded the planned ones: a nonce-bound corpus flow, refusal to overwrite existing outputs, and explicit published/validation directories.

The verify-pre API gate passes: `COVERAGE.md` declares no external API integration. Scope is release, documentation and verification tooling, with no browser or perceptual checkpoint. Hardware CGB-E, analog and perceptual output, IR peers and CGB game-level acceptance remain unqualified, as the shipped docs state.

`python3 -I .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/verify-uat-contract.py --self-test` preserves every SUMMARY, coverage id, criterion and evidence mapping. It rejects weakened closures. Phase 15 is the last v0.2 phase; the next owner-selected command is `/gsd-audit-milestone`.

## Current Test

[testing complete]

## Tests

### 1. The game-acceptance guide states that no CGB game-level evidence exists and records the bounded Rebound outcome while retaining Libbet's DMG acceptance.
expected: "The game-acceptance guide states that no CGB game-level evidence exists and records the bounded Rebound outcome while retaining Libbet's DMG acceptance."
result: pass
source: automated
summary_file: 15-01-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --check game && python3 -I tests/scripts/verify-v02-adoption.py --self-test game"]

### 2. README states the CGB game-evidence boundary, distinguishes software corpus evidence, and links to the scoped corpus and game-acceptance records.
expected: "README states the CGB game-evidence boundary, distinguishes software corpus evidence, and links to the scoped corpus and game-acceptance records."
result: pass
source: automated
summary_file: 15-01-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --check docs && python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"]

### 3. The adoption checker emits positive JSON summaries and rejects missing or contrary CGB game claims through isolated real-CLI controls.
expected: "The adoption checker emits positive JSON summaries and rejects missing or contrary CGB game claims through isolated real-CLI controls."
result: pass
source: automated
summary_file: 15-01-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --self-test game && python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"]

### 4. The v0.2.0 support ledger records model, mode, cartridge, evidence, corpus, denominator, failure, exclusion, and known-issue scope from the actual receipt.
expected: "The v0.2.0 support ledger records model, mode, cartridge, evidence, corpus, denominator, failure, exclusion, and known-issue scope from the actual receipt."
result: pass
source: automated
summary_file: 15-02-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-support-ledger.py --check-current --receipt build/cgb-corpus-receipt.json", "python3 -I tests/scripts/verify-support-ledger.py --self-test", "python3 -I tests/scripts/verify-support-ledger.py --check-current --receipt build/cgb-corpus-receipt.json (two independent nonces 30504086ec6f506391cbb43d9b0e31e8a7a6555c75a221ef6769fa9f43675d8c and 84304bc51314373e9c1ddd310a5feaec1d4a8d6218ccdbed61c1ac4d906ea359; each full CTest stream 108 selected/1138 total)"]

### 5. The v0.2.0 support ledger is selected exactly for v0.2.0 and binds release sidecars to the tagged ledger, receipt, inventory, and source inputs.
expected: "The v0.2.0 support ledger is selected exactly for v0.2.0 and binds release sidecars to the tagged ledger, receipt, inventory, and source inputs."
result: pass
source: automated
summary_file: 15-02-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-support-ledger.py --self-test (schema-2 positive=2, rejected_controls=15; accepts CTest total 1133+ with selected denominator fixed)", "python3 -I tests/scripts/verify-support-ledger.py --self-test (temporary Git sidecar fixture: positive=4, rejected_controls=21; clean checkout requires no build artifacts)", "Sidecar production-path controls: changed case outcome, assertion observation, tagged source bytes, build artifact bytes, and old sidecar after supplied receipt bytes change"]

### 6. The unreleased document is a bounded pointer to the reconciled v0.2.0 ledger, and the claim checker rejects missing or contrary statements.
expected: "The unreleased document is a bounded pointer to the reconciled v0.2.0 ledger, and the claim checker rejects missing or contrary statements."
result: pass
source: automated
summary_file: 15-02-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-cgb-corpus-claims.py --self-test (15 rejection controls)"]

### 7. The CGB corpus guide cites current producer evidence while separating guest outcomes from assertion outcomes and preserving evidence limits.
expected: "The CGB corpus guide cites current producer evidence while separating guest outcomes from assertion outcomes and preserving evidence limits."
result: pass
source: automated
summary_file: 15-02-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json --source-revision 9ab24c92b883a9ec4e8c38093efeba22467668f9 --allow-ancestor", "python3 -I tests/scripts/verify-cgb-corpus-inventory.py --bindings"]

### 8. Schema-1 behavior remains covered while schema-2 ledger and sidecar paths reject malformed, stale, narrowed, duplicated, or forged evidence.
expected: "Schema-1 behavior remains covered while schema-2 ledger and sidecar paths reject malformed, stale, narrowed, duplicated, or forged evidence."
result: pass
source: automated
summary_file: 15-02-SUMMARY.md
coverage_id: D5
evidence: ["python3 -m py_compile tests/scripts/verify-support-ledger.py tests/scripts/verify-cgb-corpus-claims.py", "python3 -I tests/scripts/verify-support-ledger.py --self-test", "python3 -I tests/scripts/verify-support-ledger.py --self-test (selected CTest count stays fixed; total-count and source/build byte-binding controls)"]

### 9. The consumer verifier runs relocated C and C++ clients and publishes source, package, compiler, behavior, and isolation evidence only after success.
expected: "The consumer verifier runs relocated C and C++ clients and publishes source, package, compiler, behavior, and isolation evidence only after success."
result: pass
source: automated
summary_file: 15-03-SUMMARY.md
coverage_id: D1
evidence: ["cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-v02-consumers.py --run --output build/v02-consumers-plan15-03.json", "python3 -I tests/scripts/verify-v02-consumers.py --self-test (9 tests, 6 negative controls, 5 positive successes)"]

### 10. Native integration guidance describes the relocated package path, receipt contents, CGB API calls, and evidence limits.
expected: "Native integration guidance describes the relocated package path, receipt contents, CGB API calls, and evidence limits."
result: pass
source: automated
summary_file: 15-03-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-v02-consumers.py --run --output build/v02-consumers-plan15-03.json", "python3 -I tests/scripts/verify-v02-consumers.py --self-test (profile, probe/info, RGB555, RTC, and rejection controls)"]

### 11. Cartridge and save guidance preserves the 21-byte RTC block, host-owned clock, and existing save contract.
expected: "Cartridge and save guidance preserves the 21-byte RTC block, host-owned clock, and existing save contract."
result: pass
source: automated
summary_file: 15-03-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-v02-consumers.py --self-test (RTC catch-up behavior and failure controls)"]

### 12. The public header documents the software-profile boundary without changing public declarations or runtime behavior.
expected: "The public header documents the software-profile boundary without changing public declarations or runtime behavior."
result: pass
source: automated
summary_file: 15-03-SUMMARY.md
coverage_id: D4
evidence: ["cmake --preset phase1 && cmake --build --preset phase1 && python3 -I tests/scripts/verify-v02-consumers.py --self-test"]

### 13. Model, mode, raw RGB555, digital PCM, dummy SDL and physical/perceptual limit guidance in the CGB profile, audio and preview guides is checked as prose, including claim markers parsed by the production CGB claim parser.
expected: "Model, mode, raw RGB555, digital PCM, dummy SDL and physical/perceptual limit guidance in the CGB profile, audio and preview guides is checked as prose, including claim markers parsed by the production CGB claim parser."
result: pass
source: automated
summary_file: 15-04-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --check docs"]

### 14. Every gbb_ or GBB_ name in the public surfaces resolves in the public header or a verified internal-source allowance; an undeclared or removed symbol is rejected.
expected: "Every gbb_ or GBB_ name in the public surfaces resolves in the public header or a verified internal-source allowance; an undeclared or removed symbol is rejected."
result: pass
source: automated
summary_file: 15-04-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"]

### 15. Removed API, RTC, save and model phrases, comment-only limits and false hardware, game, signing, publication, platform and fuzz claims each fail the real command line with a named reason.
expected: "Removed API, RTC, save and model phrases, comment-only limits and false hardware, game, signing, publication, platform and fuzz claims each fail the real command line with a named reason."
result: pass
source: automated
summary_file: 15-04-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"]

### 16. The release guide separates source archives, fixture-free product packages, tested runner labels, installed versus downloaded native proof, exact-tag sidecars and the unsigned/not-notarized macOS state.
expected: "The release guide separates source archives, fixture-free product packages, tested runner labels, installed versus downloaded native proof, exact-tag sidecars and the unsigned/not-notarized macOS state."
result: pass
source: automated
summary_file: 15-04-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --check docs"]

### 17. THIRD_PARTY_NOTICES lists every admitted fixture directory with manifest and notice digests recomputed from committed bytes, carries the source-archive distinction and rejects stale, missing, unknown and Rebound-attribution entries.
expected: "THIRD_PARTY_NOTICES lists every admitted fixture directory with manifest and notice digests recomputed from committed bytes, carries the source-archive distinction and rejects stale, missing, unknown and Rebound-attribution entries."
result: pass
source: automated
summary_file: 15-04-SUMMARY.md
coverage_id: D5
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"]

### 18. The --release-notes PATH mode requires the exact version, the absence sentence, the unsigned/not-notarized statement and an exact-version ledger link, and rejects wrong-version, missing, comment-only and contrary notes.
expected: "The --release-notes PATH mode requires the exact version, the absence sentence, the unsigned/not-notarized statement and an exact-version ledger link, and rejects wrong-version, missing, comment-only and contrary notes."
result: pass
source: automated
summary_file: 15-04-SUMMARY.md
coverage_id: D6
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"]

### 19. Clean v0.1.0 and candidate Release builds produce a validated 3-warmup, 30-pair interleaved DMG receipt with immutable source, build, binary, and workload identities.
expected: "Clean v0.1.0 and candidate Release builds produce a validated 3-warmup, 30-pair interleaved DMG receipt with immutable source, build, binary, and workload identities."
result: pass
source: automated
summary_file: 15-05-SUMMARY.md
coverage_id: D1
evidence: ["bash tests/scripts/measure-release-baseline.sh --qualify-v02 --output build/v02-performance-receipt.json --review-regression <source-backed disposition>", "python3 -I tests/scripts/verify-v02-performance.py --verify build/v02-performance-receipt.json"]

### 20. The verifier rejects forged or stale identities, altered digests or uncertainty, invalid sample order, privacy leaks, missing review and resource evidence, and receipt collisions.
expected: "The verifier rejects forged or stale identities, altered digests or uncertainty, invalid sample order, privacy leaks, missing review and resource evidence, and receipt collisions."
result: pass
source: automated
summary_file: 15-05-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-v02-performance.py --self-test (19 tests, 18 negative controls, 1 positive success)"]

### 21. Receipt includes digest-bound DMG trace/no-trace timing and peak-RSS samples plus candidate CGB-CPU-E compatibility-mode resource samples.
expected: "Receipt includes digest-bound DMG trace/no-trace timing and peak-RSS samples plus candidate CGB-CPU-E compatibility-mode resource samples."
result: pass
source: automated
summary_file: 15-05-SUMMARY.md
coverage_id: D3
evidence: ["build/v02-performance-receipt.json resource_observations verified by tests/scripts/verify-v02-performance.py"]

### 22. A Clang 18 libFuzzer ASan/UBSan fuzz_core binary performed an actual bounded campaign on the hosted Linux sanitizer job for the exact pushed source, recording nonzero executions, elapsed time over 60 seconds, exit code 0, a non-synthetic result and the bounded libFuzzer arguments, and the existing validator accepted it for that SHA.
expected: "A Clang 18 libFuzzer ASan/UBSan fuzz_core binary performed an actual bounded campaign on the hosted Linux sanitizer job for the exact pushed source, recording nonzero executions, elapsed time over 60 seconds, exit code 0, a non-synthetic result and the bounded libFuzzer arguments, and the existing validator accepted it for that SHA."
result: pass
source: automated
summary_file: 15-06-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-v02-fuzz.py --verify-hosted --source-sha bd7a7f579d92387bf99801ee91c15123fa2d4c04"]

### 23. Unsupported runtime, absent or zero-run campaigns, fast-only checks, fabricated or stale receipts, relaxed bounds, and a workflow that drops the exploration, the strict validator or the pinned compiler or broadens workers are each rejected by the real production entry points.
expected: "Unsupported runtime, absent or zero-run campaigns, fast-only checks, fabricated or stale receipts, relaxed bounds, and a workflow that drops the exploration, the strict validator or the pinned compiler or broadens workers are each rejected by the real production entry points."
result: pass
source: automated
summary_file: 15-06-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-v02-fuzz.py --self-test", "bash tests/scripts/run-bounded-fuzz.sh --self-test"]

### 24. The DMG-profile speed scenarios that the first hosted campaign minimized to a 518-byte input no longer fail the harness, while the CGB-profile speed seeds still require a speed switch and KEY1 reads and the inverted-oracle mutant is still rejected.
expected: "The DMG-profile speed scenarios that the first hosted campaign minimized to a 518-byte input no longer fail the harness, while the CGB-profile speed seeds still require a speed switch and KEY1 reads and the inverted-oracle mutant is still rejected."
result: pass
source: automated
summary_file: 15-06-SUMMARY.md
coverage_id: D3
evidence: ["build/tests/test_fuzz_core cgb_speed", "ctest fuzz and v02 selection of 15 tests in build"]

### 25. A generated tar.gz or zip source archive of an exact tag is accepted only when its embedded commit, single root, tagged Git tree, admitted fixture manifests, LICENSE notices and ROM digests all match the notice digest table, and the receipt records the archive, source tree, notice and fixture identities.
expected: "A generated tar.gz or zip source archive of an exact tag is accepted only when its embedded commit, single root, tagged Git tree, admitted fixture manifests, LICENSE notices and ROM digests all match the notice digest table, and the receipt records the archive, source tree, notice and fixture identities."
result: pass
source: automated
summary_file: 15-07-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-v02-source-archive.py --self-test"]

### 26. Missing notice, altered licensed fixture digest, unauthorized or unadmitted fixture and ROM, wrong tag or source, tree mismatch, traversing or absolute or duplicate or overlong paths, links, special members, oversize members and entry or size limits each fail the real command line for their own coded reason, and the real committed repository tree is accepted and rejected when a notice is removed.
expected: "Missing notice, altered licensed fixture digest, unauthorized or unadmitted fixture and ROM, wrong tag or source, tree mismatch, traversing or absolute or duplicate or overlong paths, links, special members, oversize members and entry or size limits each fail the real command line for their own coded reason, and the real committed repository tree is accepted and rejected when a notice is removed."
result: pass
source: automated
summary_file: 15-07-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-v02-source-archive.py --self-test"]

### 27. The installed core archive is checked through the real --verify entry point: a bundled third-party fixture directory and a renamed third-party ROM are rejected as product-fixture-leak even though the receipt verifier alone accepts them, and the clean package is accepted.
expected: "The installed core archive is checked through the real --verify entry point: a bundled third-party fixture directory and a renamed third-party ROM are rejected as product-fixture-leak even though the receipt verifier alone accepts them, and the clean package is accepted."
result: pass
source: automated
summary_file: 15-07-SUMMARY.md
coverage_id: D3
evidence: ["bash tests/scripts/verify-release-candidate.sh --self-test"]

### 28. Source archives and product packages cannot be interchanged in either direction, the final gate requires the source archive receipt as its own evidence and rejects a source or build receipt, a stale archive digest, another tag or source SHA and an empty fixture inventory, and a skipped or omitted downloaded consumer smoke result is rejected by the actual release validator.
expected: "Source archives and product packages cannot be interchanged in either direction, the final gate requires the source archive receipt as its own evidence and rejects a source or build receipt, a stale archive digest, another tag or source SHA and an empty fixture inventory, and a skipped or omitted downloaded consumer smoke result is rejected by the actual release validator."
result: pass
source: automated
summary_file: 15-07-SUMMARY.md
coverage_id: D4
evidence: ["bash tests/scripts/verify-release-candidate.sh --self-test", "python3 -I tests/scripts/verify-v02-source-archive.py --self-test"]

### 29. A complete draft inventory with the schema-2 sidecar, corpus, performance, fuzz, consumer and source-archive evidence reaches the aggregate and final gates, and omitting any single required asset, altering bytes after the platform manifest, a schema-1 sidecar or an incomplete final inventory is rejected for the expected reason.
expected: "A complete draft inventory with the schema-2 sidecar, corpus, performance, fuzz, consumer and source-archive evidence reaches the aggregate and final gates, and omitting any single required asset, altering bytes after the platform manifest, a schema-1 sidecar or an incomplete final inventory is rejected for the expected reason."
result: pass
source: automated
summary_file: 15-08-SUMMARY.md
coverage_id: D1
evidence: ["bash .github/scripts/verify-release-gates.sh --self-test"]

### 30. The delivery checker runs the owner validators and binds every receipt to the exact tag and source; mismatched corpus, ledger, SHA, version, workflow attempt, unsupported or fast-only campaign, incompatible benchmark, missing C or C++ result and unjustified or covered-input-changing reuse are each rejected with the expected code.
expected: "The delivery checker runs the owner validators and binds every receipt to the exact tag and source; mismatched corpus, ledger, SHA, version, workflow attempt, unsupported or fast-only campaign, incompatible benchmark, missing C or C++ result and unjustified or covered-input-changing reuse are each rejected with the expected code."
result: pass
source: automated
summary_file: 15-08-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-v02-delivery.py --self-test"]

### 31. Stage receipts for the phase PR and the published release are compared with simulated live PR, check, run, tag, release and asset readback; stale, failed, forged, duplicated, extra and reused-validation evidence is rejected.
expected: "Stage receipts for the phase PR and the published release are compared with simulated live PR, check, run, tag, release and asset readback; stale, failed, forged, duplicated, extra and reused-validation evidence is rejected."
result: pass
source: automated
summary_file: 15-08-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-v02-delivery.py --self-test"]

### 32. Recovery reads live release state first and decides published-verified, draft-reuse or upload-only-missing; changed or resized attachments, duplicates, missing digests, concurrent or stale attempts and altered published assets are rejected and never overwritten.
expected: "Recovery reads live release state first and decides published-verified, draft-reuse or upload-only-missing; changed or resized attachments, duplicates, missing digests, concurrent or stale attempts and altered published assets are rejected and never overwritten."
result: pass
source: automated
summary_file: 15-08-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I .github/scripts/verify-published-release-assets.py --self-test", "bash .github/scripts/verify-release-gates.sh --self-test"]

### 33. The exact-tag Linux candidate path runs the final-notes adoption contract, the downloaded relocated C and C++ consumer proof, the GitHub-generated source archive inspection and the combined candidate/product/archive verification, and attaches the consumer and source-archive receipts to the draft without replacing existing assets.
expected: "The exact-tag Linux candidate path runs the final-notes adoption contract, the downloaded relocated C and C++ consumer proof, the GitHub-generated source archive inspection and the combined candidate/product/archive verification, and attaches the consumer and source-archive receipts to the draft without replacing existing assets."
result: pass
source: automated
summary_file: 15-09-SUMMARY.md
coverage_id: D1
evidence: ["bash .github/scripts/verify-release-gates.sh --self-test", "actionlint .github/workflows/release.yml"]

### 34. New exact-tag corpus, Clang 18 libFuzzer and paired performance jobs regenerate the support-ledger sidecar and corpus receipt, fuzz receipt and performance receipt on the tagged checkout, validate them before upload and after download, and the aggregate manifest waits for all three; deleting any required invocation or transfer, moving producers after publication or dropping a needs entry is rejected.
expected: "New exact-tag corpus, Clang 18 libFuzzer and paired performance jobs regenerate the support-ledger sidecar and corpus receipt, fuzz receipt and performance receipt on the tagged checkout, validate them before upload and after download, and the aggregate manifest waits for all three; deleting any required invocation or transfer, moving producers after publication or dropping a needs entry is rejected."
result: pass
source: automated
summary_file: 15-09-SUMMARY.md
coverage_id: D2
evidence: ["bash .github/scripts/verify-release-gates.sh --self-test", "bash tests/scripts/verify-release-candidate.sh --self-test"]

### 35. A downloaded sidecar is verified by the real support-ledger owner without the producer build tree (opt-in --evidence-only) while an outside receipt without the opt-in and an altered present build file are still rejected, and the delivery checker passes the flag to the real owner.
expected: "A downloaded sidecar is verified by the real support-ledger owner without the producer build tree (opt-in --evidence-only) while an outside receipt without the opt-in and an altered present build file are still rejected, and the delivery checker passes the flag to the real owner."
result: pass
source: automated
summary_file: 15-09-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-support-ledger.py --self-test", "python3 -I tests/scripts/verify-v02-delivery.py --self-test"]

### 36. The eleven v02 contracts are registered exactly once in the configured CTest set and the required inventory, each requires exit code 0 and a nonzero success count, all pass, the executed full inventory of 1144 cases matches exactly with none skipped, and an empty selection, a missing required name, a duplicated name and an unregistered contract are each rejected.
expected: "The eleven v02 contracts are registered exactly once in the configured CTest set and the required inventory, each requires exit code 0 and a nonzero success count, all pass, the executed full inventory of 1144 cases matches exactly with none skipped, and an empty selection, a missing required name, a duplicated name and an unregistered contract are each rejected."
result: pass
source: automated
summary_file: 15-09-SUMMARY.md
coverage_id: D4
evidence: ["ctest --test-dir build -R ^v02_ --output-on-failure --no-tests=error", "bash .github/scripts/verify-test-inventory.sh build/v02-full.xml tests/expected-tests.txt --core-only"]

### 37. The tracked v0.2.0 ledger is current against its covered source inputs and the fresh complete nonce-bound corpus receipt (107 of 107 cases, 25 guest passes, 82 matched expected failures, 4959 assertion rows), with a receipt-free static check whose changed-input, missing-input and unparseable-ledger controls are rejected.
expected: "The tracked v0.2.0 ledger is current against its covered source inputs and the fresh complete nonce-bound corpus receipt (107 of 107 cases, 25 guest passes, 82 matched expected failures, 4959 assertion rows), with a receipt-free static check whose changed-input, missing-input and unparseable-ledger controls are rejected."
result: pass
source: automated
summary_file: 15-09-SUMMARY.md
coverage_id: D5
evidence: ["python3 -I tests/scripts/verify-support-ledger.py --check-current --receipt build/cgb-corpus-receipt.json", "python3 -I tests/scripts/verify-support-ledger.py --self-test"]

### 38. The Phase 15 PR merged under strict, admin-enforced protection at the exact reviewed and tested head with the three required checks successful from the GitHub Actions app, and an independent live read confirms the merge, head, checks and workflow attempts; wrong head, stale attempt and narrowed required checks are each rejected.
expected: "The Phase 15 PR merged under strict, admin-enforced protection at the exact reviewed and tested head with the three required checks successful from the GitHub Actions app, and an independent live read confirms the merge, head, checks and workflow attempts; wrong head, stale attempt and narrowed required checks are each rejected."
result: pass
source: automated
summary_file: 15-10-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-v02-delivery.py --stage phase-pr --receipt .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-delivery-receipt-phase-pr.json", "python3 -I tests/scripts/verify-v02-delivery.py --self-test"]

### 39. The v02 contracts hold on hosted Linux, macOS, Windows, sanitizer and CMake-floor jobs at the merged head; the full local inventory of 1144 cases passes on the final tree.
expected: "The v02 contracts hold on hosted Linux, macOS, Windows, sanitizer and CMake-floor jobs at the merged head; the full local inventory of 1144 cases passes on the final tree."
result: pass
source: automated
summary_file: 15-10-SUMMARY.md
coverage_id: D2
evidence: ["ctest --preset phase1 --output-on-failure --no-tests=error", "GitHub ci workflow run 39385131364 on head 6b83695 (required-native success)"]

### 40. The exact-tag producers (corpus and schema-2 sidecar, Clang 18 libFuzzer campaign, paired performance, relocated consumers, source archive) and the release gate's owner-validator aggregate ran hosted before tagging in a non-publishing rehearsal on the version PR tree, and found three defects that were fixed before and after the tag.
expected: "The exact-tag producers (corpus and schema-2 sidecar, Clang 18 libFuzzer campaign, paired performance, relocated consumers, source archive) and the release gate's owner-validator aggregate ran hosted before tagging in a non-publishing rehearsal on the version PR tree, and found three defects that were fixed before and after the tag."
result: pass
source: automated
summary_file: 15-10-SUMMARY.md
coverage_id: D3
evidence: ["GitHub release-rehearsal workflow run 39396554673 on head b53d82e (five jobs success)", "bash .github/scripts/verify-release-gates.sh --self-test"]

### 41. v0.2.0 is published from the tag source after the bounded final gate; the live release, tag, 22 assets and a fresh download agree with the receipt, and altered-digest, other-tag and shared-directory controls are rejected through the production entry point.
expected: "v0.2.0 is published from the tag source after the bounded final gate; the live release, tag, 22 assets and a fresh download agree with the receipt, and altered-digest, other-tag and shared-directory controls are rejected through the production entry point."
result: pass
source: automated
summary_file: 15-10-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-v02-delivery.py --stage published --receipt .planning/phases/GB-15-cgb-acceptance-support-ledger-and-v0-2-0-release/15-delivery-receipt.json --published-dir PUBLISHED_FINAL_DIR --validation-dir EARLIER_DRAFT_DIR", "GitHub release-please workflow run 39406047351 attempt 1 (all jobs success, release published)"]

### 42. The published release notes carry the exact version, the absence sentence, the unsigned and not-notarized limit and the exact-version ledger link, and the downloaded product package is fixture-free in its shipped layout.
expected: "The published release notes carry the exact version, the absence sentence, the unsigned and not-notarized limit and the exact-version ledger link, and the downloaded product package is fixture-free in its shipped layout."
result: pass
source: automated
summary_file: 15-10-SUMMARY.md
coverage_id: D5
evidence: ["python3 -I tests/scripts/verify-v02-adoption.py --release-notes LIVE_RELEASE_BODY", "python3 -I tests/scripts/verify-v02-source-archive.py --self-test"]

## Summary

total: 42
passed: 42
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
