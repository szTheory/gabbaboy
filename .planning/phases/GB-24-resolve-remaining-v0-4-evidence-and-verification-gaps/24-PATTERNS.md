# Phase 24: Resolve Remaining v0.4 Evidence and Verification Gaps - Pattern Map

**Mapped:** 2026-11-16  
**Files analyzed:** 3 candidate files  
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-EVIDENCE.md` | evidence report | batch / commit-pinned reconciliation | `.planning/phases/GB-22-composition-and-microtest-evidence/22-VERIFICATION.md` and `22-EVIDENCE.md` | role + data-flow match |
| `tests/scripts/verify-planning-hygiene.py` | CLI utility / contract checker | request-response CLI over immutable snapshots | same file's `v04-reconciliation` check and self-test | exact role + data-flow match |
| `tests/cmake/hygiene.cmake` | CTest configuration | request-response test wrapper | existing `plan_cap` and `planning_hygiene_controls` declarations | exact role + data-flow match; retain identities |

`24-EVIDENCE.md` is the recommended name in `24-RESEARCH.md` (Assumption A1), not a locked filename. If the plan selects another canonical Phase 24 evidence name, retain the same additive, commit-pinned record shape.

## Pattern Assignments

### `.planning/phases/GB-24-resolve-remaining-v0-4-evidence-and-verification-gaps/24-EVIDENCE.md` (evidence report, batch / commit-pinned reconciliation)

**Analogs:**

- `.planning/phases/GB-22-composition-and-microtest-evidence/22-EVIDENCE.md`
- `.planning/phases/GB-22-composition-and-microtest-evidence/22-VERIFICATION.md`
- `.planning/phases/GB-23.1-close-v0-4-requirement-and-verification-gaps/23.1-VERIFICATION.md`

All three report paths above are git-tracked. Phase 22's evidence record is the closest format match for a durable evidence artifact; its verification report is the closest semantic match for distinguishing historical outcome, immutable source, and current freshness. Phase 23.1 is the recent example of reporting focused checks while preserving the open milestone and Pending owners.

**Immutable identity and scope pattern** (`22-EVIDENCE.md`, lines 3-9):

```markdown
**Scope:** Owner-approved D-141 synthetic-plus-metadata closeout plus the single D-143 C1 OSC correction/review cycle in existing Plan 22-12. DIAG-01, DIAG-02, and RIGHTS-01 retain their original definitions and remain Pending. All seven real-fixture gates remain unresolved; no license prohibition is inferred.

## Immutable Source and Metadata

The source-bound metadata assessment preserves historical source revision `559b5f7296f957a1a1fea278056a908f9a3d9339`. Local immutable checks at reviewed source `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04` report 513 named metadata cases...
```

Use separate full commit fields for the assessment input and historical comparison baseline. State what each revision contains and what the check establishes. The record's containing commit can be referenced later by SUMMARY/verification evidence; do not make the record self-referential by requiring its own future commit ID.

**Historical status versus freshness pattern** (`22-VERIFICATION.md`, lines 6-12, 50-57, 95-99):

```yaml
source_head: d18db4c56d2a79e6138df37a9d16e3d346a86e13
implementation_head: ca2f0be6b38e7dd22e0eb3296b9a21cceed1a765
implementation_tree: e768b7ec26d7c07542d6aa29aef53ae8fc826c5e
evidence_head: d18db4c56d2a79e6138df37a9d16e3d346a86e13
report_kind: boundary_reconstruction
current_freshness: not_evaluated
```

The body explains that the report reconstructs facts from pinned evidence and that a historical pass does not refresh another phase's report. Apply this distinction to every row: original acceptance text and owner, tracker status, milestone-audit disposition, historical report result, current freshness, and exact unsatisfied gate are separate facts. Cover all eight original v0.4 requirements, including the four Complete tracker rows whose audit freshness is Partial/Stale; keep FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 Pending under their original owners. Do not copy Phase 22's statuses or counts as Phase 24 facts.

**Focused-check reporting pattern** (`23.1-VERIFICATION.md`, lines 42-49):

```markdown
The existing plan_cap CTest is wired to the immutable full source revision; the authorized plan_cap and planning_hygiene_controls CTests passed 2/2. The hygiene self-test retains the plan-cap negative controls.
```

When the evidence records Phase 24 results, bind the command/result to the checked full commit, call it point-in-time evidence, and explicitly say it does not refresh Phase 20/21 verification or satisfy the D-103 final-head suite gate. No rights conclusion or fixture/source action belongs in this record. Keep upstream page-access failures labeled as access failures.

---

### `tests/scripts/verify-planning-hygiene.py` (CLI utility / contract checker)

**Analog:** `tests/scripts/verify-planning-hygiene.py`, existing `v04-reconciliation` stage and self-test. This file is git-tracked and already owns planning report contracts; extend its established checker seam rather than create a second snapshot loader or new dependency.

**Imports pattern** (lines 55-69):

```python
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import posixpath
import re
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Callable
from pathlib import Path
```

**Immutable commit snapshot pattern** (lines 256-294):

```python
def commit_snapshot(repo: Path, rev: str) -> tuple[dict[str, bytes] | None, str | None]:
    """Read the planning tree from a commit in one Git operation; cache only immutable object ids."""
    cache_key = (str(repo.resolve()), rev)
    if cache_key in COMMIT_SNAPSHOT_CACHE:
        return COMMIT_SNAPSHOT_CACHE[cache_key], None
    if not FULL_COMMIT.fullmatch(rev):
        return None, "v04-reconciliation-rev: --rev must be a full 40-hex commit id"
    found = git_run(repo, "cat-file", "-t", rev)
    if found.returncode != 0 or found.stdout.strip() != b"commit":
        return None, f"v04-reconciliation-rev: {rev} is not a commit in {repo}"
    archive = git_run(repo, "archive", "--format=tar", rev, "--", ".planning")
    # Decode only committed planning files; errors fail closed.
```

Use `commit_file(repo, rev, path)` (lines 291-294) for exact files; it does not fall back to checkout contents. The existing command validates both `--rev` and `--baseline-rev` as full commits before dispatching to a stage (`check_v04_reconciliation`, lines 1103-1117).

**Exact status/owner and protected-baseline pattern** (`check_v04_report`, lines 903-950):

```python
dispositions = frontmatter_objects(report, "requirement_dispositions") or []
actual_dispositions = {
    item.get("id", ""): (item.get("status", ""), item.get("original_owner", ""))
    for item in dispositions
}
expected_dispositions = {
    key: ("Pending", owner) for key, owner in V04_PENDING_OWNERS.items()
}
if actual_dispositions != expected_dispositions:
    errors.append("v04-report-requirements: four original requirements must remain Pending with their original owners")
```

The existing checker also compares protected files against a pinned baseline before accepting the report (lines 944-950). For Phase 24, add exact expected owner/status/audit sets for the evidence-map contract and causal controls for false completion, owner reassignment, and milestone closure. Preserve the protected-input comparison for the original tracker and historical reports. Keep source observations, evaluator outcomes, freshness, and authority gates in distinct fields.

**Positive and causal-negative CLI control pattern** (`self_test_v04_reconciliation`, lines 1627-1637 and 1855-1886):

```python
def cli_check(stage: str, rev: str, expected_code: str | None = None,
              check_baseline: str | None = None) -> None:
    nonlocal controls
    output, error = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
        result = main(["--check", "v04-reconciliation", "--stage", stage, "--rev", rev,
                       "--baseline-rev", check_baseline or baseline_rev, "--repo", str(repo)])
    if expected_code is None:
        expected_line = f"v04-reconciliation pass stage={stage}"
        if result != 0 or output.getvalue().strip() != expected_line:
            raise SystemExit("planning-hygiene self-test FAIL: report CLI positive")
    elif result != 1 or expected_code not in error.getvalue():
        raise SystemExit(f"planning-hygiene self-test FAIL: report CLI negative wanted {expected_code}")
    controls += 1
```

Retain one canonical passing report and semantic mutations whose required refusal identifies the broken claim. Test the production CLI against committed fixtures in a disposable repository, not live working-tree files. Keep the Phase 22-specific `v04-reconciliation` meaning intact; implement the Phase 24 contract as an additive Phase 24 check/path instead of changing the existing report stage's subject.

---

### `tests/cmake/hygiene.cmake` (CTest configuration)

**Analog:** Existing planning-hygiene registrations in `tests/cmake/hygiene.cmake`, included by `tests/cmake/areas.cmake` lines 8-10. Both files are git-tracked.

**Wrapper and registration pattern** (`hygiene.cmake`, lines 28-43, 71-85):

```cmake
function(gbb_add_hygiene_test name code regex timeout script)
  set(command "${Python3_EXECUTABLE}" -I "${script}" ${ARGN})
  list(JOIN command "$<SEMICOLON>" joined)
  add_test(NAME ${name}
    COMMAND ${CMAKE_COMMAND}
      "-DGBB_CMD=${joined}"
      -DGBB_EXPECT_CODE=${code}
      "-DGBB_EXPECT_REGEX=${regex}"
      "-DGBB_WORKDIR=${PROJECT_SOURCE_DIR}"
      ${GBB_HYGIENE_EXTRA_ARGS}
      -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
  set_tests_properties(${name} PROPERTIES TIMEOUT ${timeout} LABELS planning)
endfunction()

gbb_add_hygiene_test(plan_cap 0 "plan-cap pass phases=[0-9]+ plans=[0-9]+" 30
  "${GBB_PLANNING_HYGIENE_CHECKER}" --check plan-cap
  --rev "${GBB_HYGIENE_SOURCE_REV}" --repo "${PROJECT_SOURCE_DIR}")

gbb_add_hygiene_test(planning_hygiene_controls 0 "planning-hygiene self-test pass controls=[0-9]+" 30
  "${GBB_PLANNING_HYGIENE_CHECKER}" --self-test
  --rev "${GBB_HYGIENE_SOURCE_REV}" --repo "${PROJECT_SOURCE_DIR}")
```

Keep the two authorized CTest identities exactly `plan_cap` and `planning_hygiene_controls`, and retain their current 30-second timeout and planning label. No new CTest identity or broad suite is in scope. The wrapper checks an exact exit code and output regex, and can enforce a parsed minimum control count; use it only if the existing self-test output contract changes. Avoid adding redundant live checks that increase the existing self-test runtime.

## Shared Patterns

### Immutable report boundaries

**Sources:** `tests/scripts/verify-planning-hygiene.py` lines 256-294, 880-950, 1103-1117; `22-VERIFICATION.md` lines 50-57, 95-99.  
**Apply to:** Phase 24 evidence validation and all comparisons with original requirement or historical report state.

Read the full target commit and baseline commit from Git objects. Never use a branch, tag, dirty checkout, or runtime `HEAD` as the report's source of facts. Keep record-source commit and comparison baseline distinct, and reject any historical Phase 20/21 report byte change.

### Exact refusal class and controls

**Sources:** `tests/scripts/verify-planning-hygiene.py` lines 880-922 and 1627-1637, 1855-1886.  
**Apply to:** Phase 24 report checker and its self-test.

Pair the canonical valid report with causal mutants for a completed requirement, changed original owner, changed historical/stale disposition, or closed milestone. Require the specific error family, not merely a nonzero exit. Keep the change small enough for the existing 30-second `planning_hygiene_controls` ceiling.

### CTest identity and output contract

**Source:** `tests/cmake/hygiene.cmake` lines 28-43, 71-85; `tests/cmake/areas.cmake` lines 8-10.  
**Apply to:** Only the existing `plan_cap` and `planning_hygiene_controls` checks.

CTest is invoked through `tests/expect_exit.cmake`; the CMake fragment binds the checker to the full configure-time source revision and asserts exit code/output. Preserve both names and the timeout. Do not add release inventory entries or any other CTest.

## Phase 24 Fences

- Produce one additive point-in-time evidence map. Keep all eight original requirement definitions, owners, tracker statuses, audit freshness, historical report results, and remaining gates distinct.
- Preserve FIXT-01, RIGHTS-01, DIAG-01, and DIAG-02 as Pending under their original owners; a Phase 24 checker pass cannot satisfy them.
- Keep Phase 20/21 reports and source identities unchanged. Phase 24 checks do not refresh their full verification criteria or satisfy the D-103 exact-final-head suite gate.
- Record allowed source-page identity/access outcomes as observations only. No rights determination, fixture/source payload acquisition, build/run/admission, or third candidate search.
- Keep the milestone audit `gaps_found`; no requirement acceptance, release change, lifecycle retry, milestone completion, or archival.
- Run only `plan_cap` and `planning_hygiene_controls` as the plan's focused CTests; this mapping pass ran no tests.

## No Analog Found

None for the three candidate files. The evidence/report and immutable checker patterns are already present.

## Metadata

**Analog search scope:** `.planning/phases/GB-22-composition-and-microtest-evidence/`, `.planning/phases/GB-23.1-close-v0-4-requirement-and-verification-gaps/`, `tests/scripts/`, and `tests/cmake/`.  
**Tracked-source check:** Every analog named above was confirmed by `git ls-files`; no ignored runtime mirrors are referenced.  
**Pattern extraction date:** 2026-11-16
