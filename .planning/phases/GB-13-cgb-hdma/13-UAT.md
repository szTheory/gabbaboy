---
status: complete
phase: GB-13-cgb-hdma
source: 13-01-SUMMARY.md, 13-02-SUMMARY.md, 13-03-SUMMARY.md, 13-04-SUMMARY.md, 13-05-SUMMARY.md, 13-06-SUMMARY.md, 13-07-SUMMARY.md, 13-08-SUMMARY.md, 13-09-SUMMARY.md, 13-10-SUMMARY.md, 13-11-SUMMARY.md, 13-12-SUMMARY.md
started: 2026-10-20T23:27:41.090801+00:00
updated: 2026-10-20T23:27:41.090801+00:00
---

## Automated Evidence

Fresh refresh at unchanged source `a5f0d5962acb5eefa0143f7cde5942725ad2ac79`: configure/build succeeded; complete core regression passed 1,144/1,144 in 438.76 seconds and rebuilt SDL player selection passed 98/98 in 19.87 seconds; zero skips. Frozen DMG baseline has zero changed rows. All twelve bounded before/after task windows reconcile. Current focused evidence is recorded in 13-REFRESH-GATES.md. Canonical closure maps 45 deliverables and rejects 19 controls; zero human checkpoints.

Boundary-only route and pause facts read an archive of completed boundary `e7ba52c81446096a9f6b5bf660d7721ea561eaa4`: the original pure handoff function passes and rejects four route/flag controls. The original full closeout wrapper pins OpenGSD 1.16.0 and refuses installed 1.18.0; that compatibility limitation is retained. The actual current prohibition producer separately passes saved-descriptor fail-first/clean/live proof. Historical hosted, fixture rebuild, sanitizer and benchmark receipts retain original revisions. Current full regression includes installed consumer/package checks. RGBDS 1.0.4 differs from required 1.0.1, so no fresh local fixture rebuild is claimed. No new physical, perceptual, release or hosted qualification.

The historical duplicate-library warning remains deferred and appeared during the fresh build. Reuse canonical UAT unless covered behavior changes, contrary evidence appears, or evidence is stale/unavailable. This refresh does not replay implementation.

## Current Test

[testing complete]

## Tests

### 1. Both late instruction seams complete before a bounded 16-byte HBlank transfer at normal and double speed.
expected: "Both late instruction seams complete before a bounded 16-byte HBlank transfer at normal and double speed."
result: pass
source: automated
summary_file: 13-01-SUMMARY.md
coverage_id: D1
evidence: ["ctest:cgb_hdma_tracer_ld_sp,cgb_hdma_tracer_cb", "ctest:cgb_hdma_tracer_partition,cgb_hdma_tracer_outputs"]

### 2. CGB guest-visible FF51-FF55 reads, masks, active/completed status, and DMG/compatibility distinctions are checked through guest execution.
expected: "CGB guest-visible FF51-FF55 reads, masks, active/completed status, and DMG/compatibility distinctions are checked through guest execution."
result: pass
source: automated
summary_file: 13-01-SUMMARY.md
coverage_id: D2
evidence: ["ctest:cgb_hdma_visibility", "ctest:cgb_hdma_visibility_controls", "ctest:cgb_visibility_matrix_cgb,cgb_visibility_matrix_dmg,cgb_visibility_matrix_compat"]

### 3. CGB support and timing claims match the executable model-gate, I/O-table, speed-disposition, and frozen DMG contracts.
expected: "CGB support and timing claims match the executable model-gate, I/O-table, speed-disposition, and frozen DMG contracts."
result: pass
source: automated
summary_file: 13-01-SUMMARY.md
coverage_id: D3
evidence: ["ctest:model_gates,cgb_tables_io,cgb_speed_dispositions", "bash tests/scripts/verify-dmg-baseline.sh"]

### 4. Guest-visible transfer state, initial kicks, genuine HBlank triggers, and bounded byte cadence remain covered.
expected: "Guest-visible transfer state, initial kicks, genuine HBlank triggers, and bounded byte cadence remain covered."
result: pass
source: automated
summary_file: 13-02-SUMMARY.md
coverage_id: CGB-07-STATE
evidence: ["ctest:cgb_hdma_state_matrix,cgb_hdma_trigger_matrix,cgb_hdma_timing_policy", "ctest:cgb_hdma_state_matrix_controls,cgb_hdma_trigger_matrix_controls,cgb_hdma_timing_policy_controls", "ctest:cgb_visibility_deferred_stop,cgb_visibility_deferred_latch_interrupt,cgb_visibility_matrix_cgb,cgb_visibility_cross_column_control"]

### 5. ROM, cartridge RAM, and WRAM endpoints and between-block bank changes use mapped storage paths; invalid windows leave the rejected block unchanged.
expected: "ROM, cartridge RAM, and WRAM endpoints and between-block bank changes use mapped storage paths; invalid windows leave the rejected block unchanged."
result: pass
source: automated
summary_file: 13-02-SUMMARY.md
coverage_id: CGB-07-MAP
evidence: ["ctest:cgb_hdma_address_matrix", "ctest:cgb_hdma_address_matrix_controls", "ctest:cgb_speed_xfail_hdma_fails_closed,cgb_speed_xfail_hdma_fails_closed_negative"]

### 6. Destination 9FF0 completion, A000 continuation rejection, restart, and explicit reprogramming preserve FF55 status without wrapping.
expected: "Destination 9FF0 completion, A000 continuation rejection, restart, and explicit reprogramming preserve FF55 status without wrapping."
result: pass
source: automated
summary_file: 13-02-SUMMARY.md
coverage_id: CGB-07-OVERFLOW
evidence: ["ctest:cgb_hdma_overflow_policy", "ctest:cgb_hdma_overflow_policy_controls"]

### 7. Model/profile claims, D-06 provenance, and partial-execution memory contract match tested behavior and preserve the frozen DMG baseline.
expected: "Model/profile claims, D-06 provenance, and partial-execution memory contract match tested behavior and preserve the frozen DMG baseline."
result: pass
source: automated
summary_file: 13-02-SUMMARY.md
coverage_id: CGB-07-POLICY-DOCS
evidence: ["ctest:model_gates", "bash tests/scripts/verify-dmg-baseline.sh", "python3 -I phase13-policies bounded-section contract and per-field deletion controls"]

### 8. A public guest remains halted across an ineligible HBlank, wakes on a timer IRQ, dispatches naturally, and admits work only at a later genuine edge.
expected: "A public guest remains halted across an ineligible HBlank, wakes on a timer IRQ, dispatches naturally, and admits work only at a later genuine edge."
result: pass
source: automated
summary_file: 13-03-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^cgb_hdma_guest_(halt|controls|banks)$'"]

### 9. A public guest timing discriminator detects omitted CPU stealing while preserving identical final-data controls.
expected: "A public guest timing discriminator detects omitted CPU stealing while preserving identical final-data controls."
result: pass
source: automated
summary_file: 13-03-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^cgb_hdma_guest_steal(_no_steal_mutant|_no_steal_control)?$'"]

### 10. HDMA and both speed-pause directions advance independently, with boundary-sampled timer wake and DMA retirement before interrupt dispatch.
expected: "HDMA and both speed-pause directions advance independently, with boundary-sampled timer wake and DMA retirement before interrupt dispatch."
result: pass
source: automated
summary_file: 13-03-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build -R '^cgb_hdma_competing_stalls(_controls)?$'"]

### 11. STOP preserves pending DMA and device remainders without inventing a missed HBlank edge.
expected: "STOP preserves pending DMA and device remainders without inventing a missed HBlank edge."
result: pass
source: automated
summary_file: 13-03-SUMMARY.md
coverage_id: D4
evidence: ["ctest --test-dir build -R '^cgb_hdma_stop_policy(_controls)?$'"]

### 12. OAM sampling precedes same-tick HDMA commit, which precedes PPU HBlank publication.
expected: "OAM sampling precedes same-tick HDMA commit, which precedes PPU HBlank publication."
result: pass
source: automated
summary_file: 13-03-SUMMARY.md
coverage_id: D5
evidence: ["ctest --test-dir build -R '^cgb_hdma_oam_order(_controls)?$'"]

### 13. Model claims and inherited speed anchors retain automated provenance and negative controls.
expected: "Model claims and inherited speed anchors retain automated provenance and negative controls."
result: pass
source: automated
summary_file: 13-03-SUMMARY.md
coverage_id: D6
evidence: ["cmake --preset phase1 && cmake --build --preset phase1 && ctest --test-dir build --output-on-failure --no-tests=error --parallel 4", "python3 -I tests/scripts/verify-speed-domains.py src/core/gabbaboy.c", "bash tests/scripts/verify-dmg-baseline.sh"]

### 14. CPU-programmed HDMA produces equal explicit state, guest memory, and timestamped output across critical cuts, both speed directions, and deterministic multi-cut schedules; lost-phase and ordering controls detect their named defects.
expected: "CPU-programmed HDMA produces equal explicit state, guest memory, and timestamped output across critical cuts, both speed directions, and deterministic multi-cut schedules; lost-phase and ordering controls detect their named defects."
result: pass
source: automated
summary_file: 13-04-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^(cgb_hdma_partition_|cgb_partition_|cgb_hdma_guest_|summary_coverage)' --output-on-failure --no-tests=error"]

### 15. Create, reset, successful and failed load, and independent instances clear, preserve, or isolate every HDMA field as specified.
expected: "Create, reset, successful and failed load, and independent instances clear, preserve, or isolate every HDMA field as specified."
result: pass
source: automated
summary_file: 13-04-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^(cgb_hdma_(lifecycle|resource_bounds|hostile_seeds|partition_)|api_|cgb_instance_isolation$|summary_coverage)' --output-on-failure --no-tests=error"]

### 16. Finite transfer headroom, maximum block work, trace/audio/diagnostic capacities, and deterministic FF51–55 seeds stay bounded and non-mutating on named rejection controls.
expected: "Finite transfer headroom, maximum block work, trace/audio/diagnostic capacities, and deterministic FF51\u201355 seeds stay bounded and non-mutating on named rejection controls."
result: pass
source: automated
summary_file: 13-04-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build -R '^(cgb_hdma_(lifecycle|resource_bounds|hostile_seeds|partition_)|api_|cgb_instance_isolation$|summary_coverage)' --output-on-failure --no-tests=error", "bash tests/scripts/verify-dmg-baseline.sh"]

### 17. The model-gate source and documentation stay in bijection and the complete inherited regression suite passes.
expected: "The model-gate source and documentation stay in bijection and the complete inherited regression suite passes."
result: pass
source: automated
summary_file: 13-04-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-model-gates.py", "ctest --test-dir build --parallel 4 --output-on-failure"]

### 18. The shared runtime mask causes every selected HDMA fault, including no-steal and no-copy, to fail its named behavioral predicate; each mask-zero control and the anchor guard pass.
expected: "The shared runtime mask causes every selected HDMA fault, including no-steal and no-copy, to fail its named behavioral predicate; each mask-zero control and the anchor guard pass."
result: pass
source: automated
summary_file: 13-05-SUMMARY.md
coverage_id: p13-05-runtime-fault-pairs
evidence: ["ctest --test-dir build -R '^cgb_hdma_mutant_' --output-on-failure --no-tests=error (29/29)", "ctest --test-dir build -R '^(cgb_hdma_mutant_|cgb_hdma_timing_policy|cgb_speed_mutant_|cgb_partition_mutant_)' --output-on-failure --no-tests=error (123/123)", "ctest --test-dir build -R '^(cgb_hdma_mutant_no_steal|cgb_hdma_mutant_no_steal_control|cgb_hdma_mutant_no_copy|cgb_hdma_mutant_no_copy_control)$' --output-on-failure --no-tests=error (4/4; each case 0.01s)"]

### 19. Signed timing offsets exercise the internal byte-commit predicate, and the public guest discriminator's sub-byte blind window is stated explicitly.
expected: "Signed timing offsets exercise the internal byte-commit predicate, and the public guest discriminator's sub-byte blind window is stated explicitly."
result: pass
source: automated
summary_file: 13-05-SUMMARY.md
coverage_id: p13-05-timing-sensitivity
evidence: ["ctest --test-dir build -R '^cgb_hdma_timing_sensitivity$' --output-on-failure --no-tests=error"]

### 20. Inherited P12 mutation anchors and the complete native suite retain their registered behavior, including the frozen DMG baseline.
expected: "Inherited P12 mutation anchors and the complete native suite retain their registered behavior, including the frozen DMG baseline."
result: pass
source: automated
summary_file: 13-05-SUMMARY.md
coverage_id: p13-05-inherited-regression
evidence: ["ctest --test-dir build --parallel 4 --output-on-failure (971/971)", "ctest --test-dir build -R '^(model_gates|dmg_baseline)$' --output-on-failure --no-tests=error (2/2)", "cmake --preset phase1 && cmake --build --preset phase1 --parallel 4 (166 build actions; real 3.65s)"]

### 21. Four approved SameSuite DMA ROMs and their complete source/license provenance reproduce byte-identically.
expected: "Four approved SameSuite DMA ROMs and their complete source/license provenance reproduce byte-identically."
result: pass
source: automated
summary_file: 13-06-SUMMARY.md
coverage_id: D1
evidence: ["bash tests/scripts/reproduce-samesuite.sh --compare-pinned", "bash tests/scripts/reproduce-samesuite.sh --self-check"]

### 22. Provenance, exact-set, D-06 expectation, and rebuilt-byte mutations are rejected with specific diagnostics.
expected: "Provenance, exact-set, D-06 expectation, and rebuilt-byte mutations are rejected with specific diagnostics."
result: pass
source: automated
summary_file: 13-06-SUMMARY.md
coverage_id: D2
evidence: ["bash tests/scripts/reproduce-samesuite.sh --self-test"]

### 23. The existing fixture-repro job requires the full SameSuite set, its pinned RGBDS archive, and independent build comparison.
expected: "The existing fixture-repro job requires the full SameSuite set, its pinned RGBDS archive, and independent build comparison."
result: pass
source: automated
summary_file: 13-06-SUMMARY.md
coverage_id: D3
evidence: ["bash tests/scripts/reproduce-samesuite.sh", ".github/workflows/fixture-repro.yml#Reproduce all approved SameSuite DMA fixture bytes; workflow job-set and pin-parser contract"]

### 24. Eligibility records rights, bootless software-model applicability, the retained D-06/Pan Docs conflict, and the absence of physical CGB-E proof.
expected: "Eligibility records rights, bootless software-model applicability, the retained D-06/Pan Docs conflict, and the absence of physical CGB-E proof."
result: pass
source: automated
summary_file: 13-06-SUMMARY.md
coverage_id: D4
evidence: ["bash tests/scripts/reproduce-samesuite.sh --self-check && bash tests/scripts/reproduce-samesuite.sh --self-test"]

### 25. The admitted Magen HDMA image, rights/source closure, and RGBDS reproduction match their pinned digests.
expected: "The admitted Magen HDMA image, rights/source closure, and RGBDS reproduction match their pinned digests."
result: pass
source: automated
summary_file: 13-07-SUMMARY.md
coverage_id: D1
evidence: ["bash tests/scripts/reproduce-magentests.sh --self-check && bash tests/scripts/reproduce-magentests.sh --self-test && bash tests/scripts/reproduce-magentests.sh --compare-pinned", "PYTHONPATH=tests/scripts python3 -m unittest -v test_reproduce_magentests"]

### 26. Guest VRAM/status/HALT and fresh source-derived green frames gate the digest; no-transfer, wrong-bank, and wrong-HALT controls fail their intended predicates.
expected: "Guest VRAM/status/HALT and fresh source-derived green frames gate the digest; no-transfer, wrong-bank, and wrong-HALT controls fail their intended predicates."
result: pass
source: automated
summary_file: 13-07-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^(magentests_hblank_vram_dma$|cgb_hdma_magen_controls|magentests_.*(digest|repro|manifest)|cgb_hdma_guest_halt$)' --output-on-failure --no-tests=error", "PYTHONPATH=tests/scripts python3 -m unittest -v test_magentests_hdma_registration", "python3 -c 'from pathlib import Path; lines=Path(\\\"tests/expected-tests.txt\\\").read_text().splitlines(); names=(\\\"magentests_hblank_vram_dma\\\",\\\"cgb_hdma_magen_controls\\\"); counts={n:lines.count(n) for n in names}; print(\\\"inventory-counts:\\\", counts); raise SystemExit(0 if all(v==1 for v in counts.values()) else 1)'", "ctest --test-dir build -R '^summary_coverage$' --output-on-failure --no-tests=error"]

### 27. Original CGB guest reports successful banked HBlank transfers and source-derived RGB555 pixels, while the no-transfer twin records its named failure markers and white frame.
expected: "Original CGB guest reports successful banked HBlank transfers and source-derived RGB555 pixels, while the no-transfer twin records its named failure markers and white frame."
result: pass
source: automated
summary_file: 13-08-SUMMARY.md
coverage_id: D1
evidence: ["build/tests/test_cgb_hdma --fixture fixtures/cgb-hdma/hblank.gb --check-controls", "bash tests/scripts/reproduce-cgb-hdma.sh --self-check && bash tests/scripts/reproduce-cgb-hdma.sh --self-test", "GBB_RGBDS_ARCHIVE=build/13-08-rgbds/rgbds-macos.zip GBB_RGBDS_ARCHIVE_SHA256=2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645 bash tests/scripts/reproduce-cgb-hdma.sh --compare-pinned"]

### 28. The unchanged player path checks 40 source-derived quadrant samples for both the original guest and its no-transfer failure twin before comparing RGBA digests.
expected: "The unchanged player path checks 40 source-derived quadrant samples for both the original guest and its no-transfer failure twin before comparing RGBA digests."
result: pass
source: automated
summary_file: 13-08-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build-player --show-only=json-v1 | python3 -c 'import json,sys; names={t[\\\"name\\\"] for t in json.load(sys.stdin)[\\\"tests\\\"]}; required={\\\"player_cgb_hdma_smoke\\\",\\\"player_cgb_hdma_smoke_no_transfer\\\"}; missing=required-names; print(\\\"missing-required-tests:\\\",sorted(missing)); sys.exit(bool(missing))'", "ctest --test-dir build-player -R '^player_cgb_hdma_smoke' --output-on-failure --no-tests=error", "Run hdma-positive predicate against the generated no-transfer ROM; rejected with 'hdma distinct colours 1, expected 4' before digest comparison."]

### 29. The existing fixture-repro job runs the pinned original guest rebuild and its provenance and negative controls without changing the job set or fixture allow-list.
expected: "The existing fixture-repro job runs the pinned original guest rebuild and its provenance and negative controls without changing the job set or fixture allow-list."
result: pass
source: automated
summary_file: 13-08-SUMMARY.md
coverage_id: D3
evidence: ["python3 -c 'import yaml; yaml.safe_load(open(\\\".github/workflows/fixture-repro.yml\\\"))'", "RGBDS 1.0.1 --self-check, --self-test, and --compare-pinned passed locally with the official macOS archive SHA-256 pin."]

### 30. Four unmodified, pinned SameSuite ROMs execute to their guest pass result and source-derived HDMA data and register predicates.
expected: "Four unmodified, pinned SameSuite ROMs execute to their guest pass result and source-derived HDMA data and register predicates."
result: pass
source: automated
summary_file: 13-09-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^(samesuite_hdma_gbc_dma_cont|samesuite_hdma_gdma_addr_mask|samesuite_hdma_hdma_lcd_off|samesuite_hdma_hdma_mode0)$' --output-on-failure --no-tests=error", "ctest --test-dir build --output-on-failure --parallel 4"]

### 31. The no-copy and corrupted-result twins fail the guest predicate, while Magen's no-transfer, wrong-bank, and wrong-HALT controls reject their named defects.
expected: "The no-copy and corrupted-result twins fail the guest predicate, while Magen's no-transfer, wrong-bank, and wrong-HALT controls reject their named defects."
result: pass
source: automated
summary_file: 13-09-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^(samesuite_hdma_|magentests_hblank_vram_dma$|cgb_hdma_(magen_controls|dispositions|original_fixture)|cgb_speed_dispositions|model_gates)' --output-on-failure --no-tests=error"]

### 32. The provenance ledger, model labels, result observations, denominator, Phase 12 boundary, and CGB-C hardware-claim boundary are enforced with mutation controls.
expected: "The provenance ledger, model labels, result observations, denominator, Phase 12 boundary, and CGB-C hardware-claim boundary are enforced with mutation controls."
result: pass
source: automated
summary_file: 13-09-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-cgb-hdma-dispositions.py --self-test", "python3 -I tests/scripts/verify-cgb-hdma-dispositions.py --complete"]

### 33. The research index navigates to current admission and result evidence while recording the G1 gate and partial Phase 13 execution.
expected: "The research index navigates to current admission and result evidence while recording the G1 gate and partial Phase 13 execution."
result: pass
source: automated
summary_file: 13-09-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I -c 'from pathlib import Path; text=Path(\\\".planning/research/INDEX.md\\\").read_text(); section=text.split(\\\"<!-- phase13-evidence-begin -->\\\",1)[1].split(\\\"<!-- phase13-evidence-end -->\\\",1)[0]; required=[\\\"tests/external/cgb-hdma-dispositions.json\\\",\\\"fixtures/samesuite/ELIGIBILITY.md\\\",\\\"fixtures/magentests/ELIGIBILITY.md\\\",\\\"not-run:rights-gate-G1\\\",\\\"CGB-C informational\\\",\\\"execution partial\\\"]; valid=lambda value: all(token in value for token in required); assert valid(section), \\\"phase13-memory-contract\\\"; assert all(not valid(section.replace(token,\\\"\\\")) for token in required), \\\"phase13-memory-negative-control\\\"'"]

### 34. The frozen DMG behavior and the previous CGB HDMA, visibility, model, and speed controls remain green.
expected: "The frozen DMG behavior and the previous CGB HDMA, visibility, model, and speed controls remain green."
result: pass
source: automated
summary_file: 13-09-SUMMARY.md
coverage_id: D5
evidence: ["ctest --test-dir build -R '^(cgb_hdma_|cgb_visibility_|model_gates|cgb_speed_)' --output-on-failure --no-tests=error --parallel 4", "bash tests/scripts/verify-dmg-baseline.sh"]

### 35. Relocated C and C++ installed consumers execute bounded inline CGB DMA guests at normal and double speed and diagnose a disabled-transfer twin.
expected: "Relocated C and C++ installed consumers execute bounded inline CGB DMA guests at normal and double speed and diagnose a disabled-transfer twin."
result: pass
source: automated
summary_file: 13-10-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R '^(installed_consumer_(c|cpp)$|cgb_consumer_symbol_coverage|preview_package_smoke$)' --output-on-failure --no-tests=error --parallel 4"]

### 36. The relocated package preserves its exact fixture child set and rejects forbidden SameSuite and Magen ROM bytes even when renamed.
expected: "The relocated package preserves its exact fixture child set and rejects forbidden SameSuite and Magen ROM bytes even when renamed."
result: pass
source: automated
summary_file: 13-10-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R '^(cgb_hdma_not_installed|magentests_not_installed|age_not_installed|preview_package_smoke$|installed_consumer_(c|cpp)$)' --output-on-failure --no-tests=error --parallel 4"]

### 37. Native consumer claims describe bounded GDMA and HBlank DMA behavior, unchanged public calls, and the selected software model's evidence limits.
expected: "Native consumer claims describe bounded GDMA and HBlank DMA behavior, unchanged public calls, and the selected software model's evidence limits."
result: pass
source: automated
summary_file: 13-11-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-cgb-hdma-claims.py --native", "python3 -I tests/scripts/verify-cgb-hdma-claims.py --self-test", "ctest --test-dir build -R '^(cgb_native_guide_contract|model_gates|summary_coverage)$' --output-on-failure --no-tests=error"]

### 38. Player, help, README, and preview package claims agree while retaining mode-3, APU, physical-hardware, and game-compatibility limits.
expected: "Player, help, README, and preview package claims agree while retaining mode-3, APU, physical-hardware, and game-compatibility limits."
result: pass
source: automated
summary_file: 13-11-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-cgb-hdma-claims.py --native-player && python3 -I tests/scripts/verify-cgb-hdma-claims.py", "python3 -I tests/scripts/verify-cgb-hdma-claims.py --self-test", "ctest --test-dir build-player -R '^(player_claims_agree|player_claims_agree_mutated|player_limitations|player_cgb_cli)$' --output-on-failure --no-tests=error", "cmake --preset phase1 && cmake --build --preset phase1"]

### 39. Subject snapshots require the exact complete set of surfaces, pass for a clean checkout, and reject a false physical CGB-E qualification with its named diagnostic.
expected: "Subject snapshots require the exact complete set of surfaces, pass for a clean checkout, and reject a false physical CGB-E qualification with its named diagnostic."
result: pass
source: automated
summary_file: 13-11-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-cgb-hdma-claims.py --prepare-prohibition-subjects build/p13-11-subjects", "python3 -I tests/scripts/verify-cgb-hdma-claims.py --subject build/p13-11-subjects/clean.json", "python3 -I tests/scripts/verify-cgb-hdma-claims.py --self-test"]

### 40. Current source revision has machine-proven HDMA claim prohibition and fail-first/clean/live-checkout evidence.
expected: "Current source revision has machine-proven HDMA claim prohibition and fail-first/clean/live-checkout evidence."
result: pass
source: automated
summary_file: 13-12-SUMMARY.md
coverage_id: D1
evidence: ["tests/scripts/cgb-hdma-prohibition.test.cjs#actual OpenGSD prohibition producer proof", "python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py --prohibitions-self-test"]

### 41. The exact native and player inventories, unchanged parallelism/timeouts, and installed consumers pass at the recorded source revision.
expected: "The exact native and player inventories, unchanged parallelism/timeouts, and installed consumers pass at the recorded source revision."
result: pass
source: automated
summary_file: 13-12-SUMMARY.md
coverage_id: D2
evidence: ["build/build/phase13-wave10-native-690c081.xml#993 tests, zero failures/errors/skips", "build-player/build-player/phase13-wave10-player-690c081.xml#1086 tests, zero failures/errors/skips", "build/phase13-wave10-installed-690c081.xml#six relocated consumer/package targets, zero failures/errors/skips"]

### 42. Fixture provenance controls reject altered rights, source, tool and ROM claims while admitted fixtures reproduce byte-identically.
expected: "Fixture provenance controls reject altered rights, source, tool and ROM claims while admitted fixtures reproduce byte-identically."
result: pass
source: automated
summary_file: 13-12-SUMMARY.md
coverage_id: D3
evidence: ["bash tests/scripts/reproduce-samesuite.sh --self-test", "GitHub Actions run 38662784222 at 690c081, 7/7 fixture and reproduction jobs passed"]

### 43. Phase 13 handoff names automated verification as the next stage and keeps Phase 14 unstarted.
expected: "Phase 13 handoff names automated verification as the next stage and keeps Phase 14 unstarted."
result: pass
source: automated
summary_file: 13-12-SUMMARY.md
coverage_id: D4
evidence: ["tests/scripts/phase13-handoff-continuity.test.cjs#handoff stage and exact route", "python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py --handoff"]

### 44. Required source-revision CI and package preview workflows complete successfully at the tested source revision.
expected: "Required source-revision CI and package preview workflows complete successfully at the tested source revision."
result: pass
source: automated
summary_file: 13-12-SUMMARY.md
coverage_id: D5
evidence: ["GitHub Actions PR-event run 38662784214 at 690c081, all eight jobs success", "GitHub Actions preview-package-smoke run 38662784151 at 690c081, all four jobs success"]

### 45. Closeout evidence rejects changed source and misleading remote receipts while preserving the exact completed-stage handoff.
expected: "Closeout evidence rejects changed source and misleading remote receipts while preserving the exact completed-stage handoff."
result: pass
source: automated
summary_file: 13-12-SUMMARY.md
coverage_id: POST_REVIEW
evidence: ["python3 -I .planning/phases/GB-13-cgb-hdma/verify-hdma-source-revision.py", "ctest:cgb_hdma_remote_evidence_selftest", "node --test tests/scripts/phase13-handoff-continuity.test.cjs"]

## Summary

total: 45
passed: 45
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
