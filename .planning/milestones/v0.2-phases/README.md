# v0.2 phase records (archive)

Phases 7 through 15.1 of milestone v0.2 were moved here from the live phases directory on 2026-10-24
(Phase 16, plan 01, TUNE-01).

- The move is a pure rename. No record's bytes changed, and the 15.1 disposition, scope and evidence
  records digest-pin several of them.
- Links inside the archived files still name their original locations in the live phases directory.
  They are history, not routes. Read each one under this directory instead.
- Tests and verifiers read these records only through `GBB_V02_PHASES_DIR` in `tests/CMakeLists.txt` or an
  explicit path argument. `tests/scripts/verify-no-phase-paths.py` rejects any other tracked reader of the live
  phases directory, and the count-pinned rows in its allowlist explain each exception.
- The v0.2 milestone audit accounting script now lives beside the audits at
  `.planning/milestones/verify-v02-milestone-audit.py`.
