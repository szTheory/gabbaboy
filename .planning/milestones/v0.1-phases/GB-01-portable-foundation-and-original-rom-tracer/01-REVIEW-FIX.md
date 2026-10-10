---
phase: GB-01-portable-foundation-and-original-rom-tracer
fixed_at: 2026-10-03T17:30:00Z
review_path: .planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-REVIEW.md
iteration: 4
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 1: Code Review Fix Report

**Latest fix:** 2026-10-03T17:30:00Z  
**Source review:** `.planning/phases/GB-01-portable-foundation-and-original-rom-tracer/01-REVIEW.md`  
**Latest iteration:** 4

**Latest iteration summary:**
- Findings in scope: 1
- Fixed: 1
- Skipped: 0

## Fixed Issues

### CR-01: ROM-only sizes above 32 KiB are accepted but mapped incorrectly

**Files modified:** `src/core/gabbaboy.c`, `include/gabbaboy/gabbaboy.h`, `tests/test_loader.c`, `tests/CMakeLists.txt`, `tests/expected-tests.txt`  
**Commit:** `0d2579e`  
**Applied fix:** ROM-only cartridge headers with ROM-size codes above 0 now return `GBB_UNSUPPORTED_ROM_SIZE`. The API contract documents support for exact-size 32 KiB ROM-only images. Added a valid-checksum 64 KiB image regression; it verifies rejection preserves the already-loaded image and usable machine state.

### CR-02: Artifact path checks do not validate archive link targets

**Files modified:** `.github/workflows/fixture-repro.yml`, `.github/scripts/verify-pr-evidence.sh`, `.github/scripts/safe_extract_package.py`  
**Commits:** `7ba40dc`, `809ee1a`  
**Applied fix:** The fixture workflow checks the downloaded RGBDS v1.0.1 Linux archive against its SHA-256 before extracting or running its tools. The evidence verifier uses a Python standard-library extractor that validates all member paths and types before writing, rejects links and special files, absolute/parent/out-of-prefix paths, duplicates, and file-parent conflicts, and writes only regular files and directories beneath `installed-prefix` using no-follow file creation. The evidence verifier runs an adversarial self-test before processing artifacts.

### WR-01: RGBDS release archive is version-named but not digest-pinned

**File modified:** `.github/workflows/fixture-repro.yml`  
**Commit:** `7ba40dc`  
**Applied fix:** The fixture workflow checks the downloaded RGBDS v1.0.1 Linux archive against SHA-256 `80a5cad8dae27e24e46a93041352c47cadbc165103983f41c2b3082c42f6dad9` before extracting or running its tools.

## Iteration 1 Verification

Commands below ran in the isolated worktree for iteration 1, which was removed after its commits were integrated.

- CR-01: Configured with CMake/Ninja, built `test_loader`, and ran `ctest -R '^loader_unsupported_declared_size$'`; the regression passed. CMake configure also accepted the updated fail-closed test inventory.
- CR-02: `python3 -m py_compile .github/scripts/safe_extract_package.py`, `python3 .github/scripts/safe_extract_package.py --self-test`, `sh -n .github/scripts/verify-pr-evidence.sh`, and `git diff --check` passed. The adversarial self-test rejected symlink, hardlink, FIFO, traversal, absolute, out-of-prefix, duplicate, and file-parent-conflict archives.
- WR-01: Ruby YAML parsing of `.github/workflows/fixture-repro.yml` and `git diff --check` passed. The digest check is placed after download and before extraction; the external RGBDS archive was not downloaded or executed during that focused step.
- Logic changes were marked **fixed: requires human verification** for the orchestrator's phase-wide verification and hosted CI; the focused checks were not a substitute for those gates.

## Iteration 2: WR-02

**File modified:** `.github/scripts/safe_extract_package.py`  
**Commits:** `da58af3`, `000f3a7`  
**Applied fix:** Added documented limits of 64 MiB compressed archive size, 4,096 tar members, 512 MiB aggregate declared/expanded data, and 576 MiB total decompressed tar-stream bytes. Member headers are scanned incrementally and rejected on count, negative size, single-member size, or aggregate size violations before extraction. Streaming copies enforce the aggregate limit, reject bytes beyond the declared member size, and reject truncation when copied length differs from the header. Tar parsing uses a bounded gzip reader in streaming mode; hidden PAX/GNU extension headers are limited to 64 KiB each, 8 MiB total, and 8,192 headers before tarfile reads their payloads. A second bounded pass extracts only after full path/type validation. Added synthetic tests for member-count, aggregate-size, and decompressed-reader rejection without large fixtures.

**Verification:** In isolated worktrees, syntax compilation, the extractor `--self-test`, and `git diff --check` passed. The self-test reported `PASS safe package extraction adversarial validation (member count, aggregate size, and decompressed stream bounds)`. A focused tiny gzip/tar extraction smoke printed `PASS bounded streaming extraction smoke` and confirmed exact extracted bytes. No full test suite was run.

## Iteration 3: WR-03

**File modified:** `.github/scripts/safe_extract_package.py`  
**Commit:** `a34b990`  
**Applied fix:** Added a documented 64-component archive path limit. `checked_name` counts separators and rejects paths over the limit before splitting components or constructing `PurePosixPath`. The adversarial self-test now rejects a path deeper than the limit and identifies path depth in its pass message. Existing archive byte, member, and extraction limits are unchanged.

**Verification:** In the isolated worktree, `python3 .github/scripts/safe_extract_package.py --self-test` passed with `PASS safe package extraction adversarial validation (member count, path depth, aggregate size, and decompressed stream bounds)`. `git diff --check` passed. `python3 -c 'from pathlib import Path; compile(Path(".github/scripts/safe_extract_package.py").read_text(), ".github/scripts/safe_extract_package.py", "exec")'` passed. `python3 -m py_compile` was attempted but could not write Python's cache beneath the home cache directory due sandbox permissions; it produced no source change. No full test suite was run.

---

_Latest fix: 2026-10-03T17:20:00Z_  
_Fixer: the agent (gsd-code-fixer)_  
_Latest iteration: 3_

## Iteration 4: WR-04

**File modified:** `.github/scripts/verify-pr-evidence.sh`  
**Commit:** `784b7ca`  
**Applied fix:** Replaced the predictable PID-based evidence staging path and `mkdir -p` with atomic `mktemp -d "${TMPDIR:-/tmp}/gabbaboy-pr-evidence.XXXXXX"`. The existing `umask 077`, cleanup function, and exit/signal traps remain in place.

**Verification:** In the isolated worktree, `sh -n .github/scripts/verify-pr-evidence.sh` and `git diff --check` passed. A focused temporary-directory check created two distinct staging directories using the same template under `umask 077`, confirmed both existed with mode 700, and removed them. No full test suite was run.

---

_Latest fix: 2026-10-03T17:30:00Z_  
_Fixer: the agent (gsd-code-fixer)_  
_Latest iteration: 4_
