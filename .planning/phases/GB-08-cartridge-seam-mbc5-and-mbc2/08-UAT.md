---
status: complete
phase: GB-08-cartridge-seam-mbc5-and-mbc2
source: 08-01-SUMMARY.md, 08-02-SUMMARY.md, 08-03-SUMMARY.md, 08-04-SUMMARY.md, 08-05-SUMMARY.md, 08-06-SUMMARY.md, 08-07-SUMMARY.md, 08-08-SUMMARY.md, 08-09-SUMMARY.md, 08-10-SUMMARY.md
started: 2026-10-21T00:15:06.342565+00:00
updated: 2026-10-21T00:15:06.342565+00:00
---

## Automated Evidence

Fresh producer a338f54: core 1,144/1,144, rebuilt player 98/98 and separate installed-package 5/5, all zero skips; frozen DMG rows unchanged and core258/player55 identities covered. Package clean scans and renamed CGB/MBC/symlink controls pass. Immutable Phase8 closure contract reads65 files and rejects157 controls; player contract rejects5. All10 SUMMARY schemas pass,34 deliverables automate; historical bodies/receipts remain unchanged. See08-PACKAGE-REFRESH-EVIDENCE.md and08-PACKAGE-REFRESH-GATES.md for producers, commands, hashes, scope and limitations. This closure establishes no new hosted/hardware/perceptual qualification and accepts no audit debt.

## Current Test

[testing complete]

## Tests

### 1. Cartridge mapper seam preserves the historical DMG behavior against its old-core oracle
expected: "Cartridge mapper seam preserves the historical DMG behavior against its old-core oracle"
result: pass
source: automated
summary_file: 08-01-SUMMARY.md
coverage_id: D1
evidence: ["Historical differential .planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/differential/run-differential.sh receipts in .planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/08-01-SUMMARY.md and docs/mbc2-mbc5-evidence.md at 96d5eec977bee99a0629499b89c737415e24184c; python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test", "ctest --test-dir build -R ^(cartridge_|battery_|loader_|mbc1_continuation|dmg_baseline) --output-on-failure"]

### 2. Reusable differential harness supports explicit changed-type exclusions
expected: "Reusable differential harness supports explicit changed-type exclusions"
result: pass
source: automated
summary_file: 08-01-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 3. MBC2 mapper: bit-8 decode, echoed 512-cell nibble RAM, 512-byte canonical battery image
expected: "MBC2 mapper: bit-8 decode, echoed 512-cell nibble RAM, 512-byte canonical battery image"
result: pass
source: automated
summary_file: 08-02-SUMMARY.md
coverage_id: D1
evidence: ["tests/test_mbc2.c#mbc2_register_decode", "tests/test_mbc2.c#mbc2_ram_echo", "tests/test_mbc2.c#mbc2_battery_idempotent", "tests/test_mbc2.c#mbc2_two_instance_roundtrip"]

### 4. MBC5 mapper: 9-bit ROM banking, RAM enable/banking to 128 KiB, battery, no-RAM window
expected: "MBC5 mapper: 9-bit ROM banking, RAM enable/banking to 128 KiB, battery, no-RAM window"
result: pass
source: automated
summary_file: 08-03-SUMMARY.md
coverage_id: D1
evidence: ["tests/test_mbc5.c#mbc5_rom_banking", "tests/test_mbc5.c#mbc5_ram_enable", "tests/test_mbc5.c#mbc5_ram_banking", "tests/test_mbc5.c#mbc5_battery"]

### 5. Type-aware 8 MiB ceiling that leaves every other type's loader result unchanged
expected: "Type-aware 8 MiB ceiling that leaves every other type's loader result unchanged"
result: pass
source: automated
summary_file: 08-03-SUMMARY.md
coverage_id: D2
evidence: ["tests/test_mbc5.c#mbc5_rom_bound", "run-differential.sh --exclude-types 05,06,19,1A,1B,1C,1D,1E"]

### 6. gbb_rumble_state / GBB_NO_RUMBLE with exact reset, load and saturation semantics
expected: "gbb_rumble_state / GBB_NO_RUMBLE with exact reset, load and saturation semantics"
result: pass
source: automated
summary_file: 08-03-SUMMARY.md
coverage_id: D3
evidence: ["tests/test_mbc5.c#mbc5_rumble_reset_load", "tests/test_mbc5_internal.c#mbc5_rumble_saturation", "installed_consumer_c / installed_consumer_cpp"]

### 7. MBC2/MBC5 battery cartridges run in the player without touching the save directory
expected: "MBC2/MBC5 battery cartridges run in the player without touching the save directory"
result: pass
source: automated
summary_file: 08-04-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-phase8-player-contract.py --self-test"]

### 8. Status string, stderr warning and limitations text name the unsaved-progress gap
expected: "Status string, stderr warning and limitations text name the unsaved-progress gap"
result: pass
source: automated
summary_file: 08-04-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-phase8-player-contract.py --self-test"]

### 9. 15 digest-pinned Mooneye MBC2/MBC5 derivative ROMs with redistribution notices
expected: "15 digest-pinned Mooneye MBC2/MBC5 derivative ROMs with redistribution notices"
result: pass
source: automated
summary_file: 08-05-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"]

### 10. Bounded multi-suite runner selects admitted manifest digests and records callback results
expected: "Bounded multi-suite runner selects admitted manifest digests and records callback results"
result: pass
source: automated
summary_file: 08-05-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"]

### 11. Fixture reproduction recipe and provenance retain builder pins and measured 7/7 MBC2, 8/8 MBC5 historical receipt
expected: "Fixture reproduction recipe and provenance retain builder pins and measured 7/7 MBC2, 8/8 MBC5 historical receipt"
result: pass
source: automated
summary_file: 08-05-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 12. Digest, inventory and runner-PC agreement verifier
expected: "Digest, inventory and runner-PC agreement verifier"
result: pass
source: automated
summary_file: 08-06-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"]

### 13. 15 per-case receipts and fail-closed manifest/type/PC controls
expected: "15 per-case receipts and fail-closed manifest/type/PC controls"
result: pass
source: automated
summary_file: 08-06-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"]

### 14. Sibling fixture rights, eligibility and notices document the named software profile
expected: "Sibling fixture rights, eligibility and notices document the named software profile"
result: pass
source: automated
summary_file: 08-06-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 15. Name and digest redistribution guard rejects planted fixtures and wrong fixture lists
expected: "Name and digest redistribution guard rejects planted fixtures and wrong fixture lists"
result: pass
source: automated
summary_file: 08-07-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R ^mooneye_mbc_ --output-on-failure"]

### 16. Install and extracted preview/player packaging exclude admitted Mooneye MBC fixtures
expected: "Install and extracted preview/player packaging exclude admitted Mooneye MBC fixtures"
result: pass
source: automated
summary_file: 08-07-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R ^(mooneye_mbc_|preview_package_smoke) --output-on-failure"]

### 17. Historical exact-head Linux rebuild and CI receipts remain attributed to their original producer
expected: "Historical exact-head Linux rebuild and CI receipts remain attributed to their original producer"
result: pass
source: automated
summary_file: 08-07-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 18. Original licensed RGBDS MBC5 guest has pinned bytes and a reproduction recipe
expected: "Original licensed RGBDS MBC5 guest has pinned bytes and a reproduction recipe"
result: pass
source: automated
summary_file: 08-08-SUMMARY.md
coverage_id: D1
evidence: ["ctest --test-dir build -R ^mbc5_banking_ --output-on-failure"]

### 19. Guest exercises banking through real CPU and bus, including harness-supplied bank 1FF marker
expected: "Guest exercises banking through real CPU and bus, including harness-supplied bank 1FF marker"
result: pass
source: automated
summary_file: 08-08-SUMMARY.md
coverage_id: D2
evidence: ["ctest --test-dir build -R ^mbc5_(banking_|bank_1ff) --output-on-failure"]

### 20. Ninth-bit mutant fails the discriminator and passes its below-100 control
expected: "Ninth-bit mutant fails the discriminator and passes its below-100 control"
result: pass
source: automated
summary_file: 08-08-SUMMARY.md
coverage_id: D3
evidence: ["ctest --test-dir build -R ^mbc5_ninth_bit_mutant_ --output-on-failure"]

### 21. Historical hosted reproduction step and fixture provenance remain explicitly bounded
expected: "Historical hosted reproduction step and fixture provenance remain explicitly bounded"
result: pass
source: automated
summary_file: 08-08-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 22. Historical public cartridge matrix, allocation bounds, battery and rumble API match Phase8 scope
expected: "Historical public cartridge matrix, allocation bounds, battery and rumble API match Phase8 scope"
result: pass
source: automated
summary_file: 08-09-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 23. Historical evidence ledger distinguishes oracle classes, ninth-bit proof and game/hardware exclusions
expected: "Historical evidence ledger distinguishes oracle classes, ninth-bit proof and game/hardware exclusions"
result: pass
source: automated
summary_file: 08-09-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 24. Historical README and preview text state player persistence and size limits
expected: "Historical README and preview text state player persistence and size limits"
result: pass
source: automated
summary_file: 08-09-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 25. Historical support entry states profile, denominators, player persistence gap and source-archive limits
expected: "Historical support entry states profile, denominators, player persistence gap and source-archive limits"
result: pass
source: automated
summary_file: 08-09-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 26. Historical package capability text states the cartridge scope and persistence limit
expected: "Historical package capability text states the cartridge scope and persistence limit"
result: pass
source: automated
summary_file: 08-09-SUMMARY.md
coverage_id: D5
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 27. Phase8 decisions are adopted, concrete lessons retained and research index links preserved
expected: "Phase8 decisions are adopted, concrete lessons retained and research index links preserved"
result: pass
source: automated
summary_file: 08-09-SUMMARY.md
coverage_id: D6
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 28. Deferred MBC1 backfill, cartridge split, region decode, verifier, haptics and packed save directions are recorded
expected: "Deferred MBC1 backfill, cartridge split, region decode, verifier, haptics and packed save directions are recorded"
result: pass
source: automated
summary_file: 08-09-SUMMARY.md
coverage_id: D7
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 29. Phase-wide gates (additions-only inventory, frozen paths, no baseline: commits, no 0x03u literal, JOYP and ninth-bit anchors once, baseline status=pass)
expected: "Phase-wide gates (additions-only inventory, frozen paths, no baseline: commits, no 0x03u literal, JOYP and ninth-bit anchors once, baseline status=pass)"
result: pass
source: automated
summary_file: 08-10-SUMMARY.md
coverage_id: D1
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 30. Exact-head CI at the evidence head: eight required jobs and four fixture-repro jobs success
expected: "Exact-head CI at the evidence head: eight required jobs and four fixture-repro jobs success"
result: pass
source: automated
summary_file: 08-10-SUMMARY.md
coverage_id: D2
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 31. Historical PR #64 readiness and open/unmerged receipt retained with its exact producer
expected: "Historical PR #64 readiness and open/unmerged receipt retained with its exact producer"
result: pass
source: automated
summary_file: 08-10-SUMMARY.md
coverage_id: D3
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 32. Historical phase pause and verification route persisted in STATE and continuation with auto flags false
expected: "Historical phase pause and verification route persisted in STATE and continuation with auto flags false"
result: pass
source: automated
summary_file: 08-10-SUMMARY.md
coverage_id: D4
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 33. Historical privacy scan records no personal paths and only the permitted upstream licence address
expected: "Historical privacy scan records no personal paths and only the permitted upstream licence address"
result: pass
source: automated
summary_file: 08-10-SUMMARY.md
coverage_id: D5
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

### 34. Historical boundary triage records no open issues and PR64 disposition
expected: "Historical boundary triage records no open issues and PR64 disposition"
result: pass
source: automated
summary_file: 08-10-SUMMARY.md
coverage_id: D6
evidence: ["python3 -I tests/scripts/verify-phase8-closure-contract.py --self-test"]

## Summary

total: 34
passed: 34
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
