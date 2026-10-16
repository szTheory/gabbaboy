# Phase 14 execution closure evidence

All 13 plans, 31 tasks and 11 execution waves are summarized. Nyquist coverage is 31/31, with no manual-only row. Security closes all 27 plan-time threats. The copy-only UI review's one stale player expectation is fixed and passes the three player copy/claim checks, including a mutation. Independent code review found two Windows tooling blockers; fixes `e1deb42` and `bfd6f09` passed eight focused controls and all 13 report-contract tests, then an independent recheck closed both. The disposition ledger records two fixed, zero open and zero unparsed findings.

## Final regression gate

The configured one-shot CMake/CTest regression command was run under OpenGSD's 600-second timeout. The CTest portion used one fresh nonce-bound dashboard/JUnit stream, parallelism two, uncompressed bounded output and the explicit `build` test directory. It ran after both portability fixes, on actual producer revision `0018d4a9b8bfa0e60890be7fb3386b73601e0eb2`:

- 1,136/1,136 CTests passed; zero failures, errors or skips; 158.27 seconds.
- JUnit: local `build/phase14-final-regression.xml`, SHA-256 `8450b716d4b61dd5f31c185135745d78077fbd5d08014a5f80e031888f6182c5`.
- Receipt: local `build/cgb-corpus-receipt.json`, SHA-256 `2a733d37f42928c25a7c61cfdfd1003b01ce2251dc4342566db6104c6de98766`; nonce `bba3ef079f86ae657970b15517dbd0ad`.
- 107/107 cases complete: 25 actual passes, 82 matched expected failures; 2,845/4,959 passing assertion rows; 18,208/138,240 mismatching image pixels. These are honest software observations, not 107 hardware passes.
- Required installed inventory accepted all 1,136 executed names without skips. The frozen DMG JUnit inventory accepted all 258 required names with no changed baseline rows.
- The three-file public artifact allowlist passed its privacy check, and post-receipt semantic claims passed against that complete receipt.

The prior 11 wave receipts remain historical at their own revisions. This final gate replaces none of them and relabels no earlier evidence. Its byte identity includes the single CMake spacing line introduced during phase execution; that line is retained in the phase tree so published verification fingerprints match the inspected source. The owner's pre-existing configuration and state timestamp changes remain separate.

## Scope and handoff

Physical CGB-E, analog/perceptual output, real IR peers and general game compatibility remain UNKNOWN/POLICY or explicitly unqualified. Rights/model exclusions remain outside the executed-case denominator. Phase 15 acceptance/release work is unstarted; release PR #70 is outside this execution closure.

D-069 remains the default: every decidable deliverable has an automated contract and an intended negative control. Reuse the completed phase research and these checks; do not invent manual UAT or add duplicate CI lanes. The next command after execution closure is `/gsd-verify-work 14`, for automated SUMMARY coverage/commit-window closure before the owner chooses Phase 15. Hosted status must be read at the final exact PR head; this local report does not assert a hosted result.
