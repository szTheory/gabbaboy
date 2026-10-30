## [0.3.0](https://github.com/szTheory/gabbaboy/compare/v0.2.1...v0.3.0) (2026-10-29)

GabbaBoy v0.3.0 adds the selected CGB-CPU-E software model beside DMG-CPU-B.

- Save states load only in the exact GabbaBoy release that wrote them. Battery saves remain the cross-version persistence path.
- Host mode is POSIX-only; Windows refuses `--save-dir`.
- No CGB game-level evidence exists. The CGB test-ROM corpus is software-model evidence, not game acceptance. Physical CGB-E remains UNKNOWN/POLICY.
- The macOS player archive is unsigned and not notarized.
- Support scope and known limits: [support ledger](docs/support/v0.3.0.md).
- Instruction count: +9.6% versus v0.2.0 (receipt: tests/baseline/perf-attribution-v1.json; measured at f80bdf54c6c7).
- The Ir attribution figure was measured at f80bdf54c6c7 on main before the release commit; the release-binding Ir check is the perf-gate receipt verified at the tagged source.
