# Phase 24: Resolve remaining v0.4 evidence and verification gaps - Pattern Map

**Mapped:** 2026-11-17
**Files analyzed:** 12 tracked source, test-data, and CMake files across the six D-212 blocker groups
**Analogs found:** 12 / 12; each group has a useful implementation seam, though several lack an exact precedent for the new boundary

## Scope and authority

D-212 is planning-only in the sole existing Phase 24 plan. This map grants no implementation, test, build, CI, ROM execution, push, review, or merge authority. Preserve the frozen PR #154 candidate and allow the existing D-211 run to conclude without cancellation or rerun. Do not replay Acid2 or any excluded gbmicrotest case. Keep D-209's closed-with-gaps disposition and accepted gaps authoritative; FIXT-01 stays Pending, and no requirement or status changes are in scope. Do not weaken full-commit, fixture-pin, or ancestry validation.

The current root roadmap remains the active Phase 24 route. Use the archived v0.4 roadmap and requirements only for historical v0.4 criteria, owners, and dispositions. Do not restore an active root requirements tracker or reopen v0.4. The project has no .codex/skills or .agents/skills directory with local SKILL.md files.

## File Classification

| Existing D-212 surface | Role | Data flow | Closest analog | Match quality |
|------------------------|------|-----------|----------------|---------------|
| tests/scripts/verify-dense-input.py | test harness | batch | Same harness; commit admission in verify-fixture-admission.py | partial: isolated source and baseline exist, but the mutant subject lacks its own Git history |
| tests/scripts/verify-fixture-admission.py | utility / validator | request-response | Same production CLI and its commit/ancestry checks | exact for fail-closed pin validation |
| tests/scripts/verify-diagnostic-evidence.py | test / evidence checker | batch transform | Its immutable Git snapshot reader | exact for exact-revision input; source selection is stale for D-209 |
| tests/scripts/verify-planning-hygiene.py | utility / planning checker | batch transform | Its read_rev and committed-fixture self-tests | partial: immutable reads and archive fallback exist, but not the active Phase 24 plus archived v0.4 combination |
| tests/scripts/verify-state-forks.py | test / inventory checker | batch transform | Its manifest census and row expansion | partial: active-manifest census exists; the two current diagnostic exclusions do not |
| tests/data/state-forks.json | test configuration | transform | Same manifest inventory and existing excluded row | partial: existing exclusion is a different path and reason |
| tests/CMakeLists.txt | test configuration | batch | Existing state-fork fixture setup and dependent controls | exact for the execution dependency chain |
| tests/scripts/verify-no-phase-paths.py | utility / linter | batch scan | Its tracked-file scan, exception checks, and controls | partial: current exception is file-count based, not exact-line based |
| tests/data/v04-closeout.json | test/evidence data | transform | Existing JSON evidence values consumed by the path scanner | no logic analog; this is the historical fixture to scope narrowly |
| tests/scripts/verify-workflow-policy-coverage.py | test / workflow-policy checker | batch | Its immutable tagged-source comparison | exact for preserving the release trust root |
| tests/cmake/ci-lanes.cmake | test configuration | batch | workflow_policy_coverage_controls registration | exact for preserving the existing CTest identity |
| tests/cmake/hygiene.cmake | test configuration | batch | plan_cap and planning_hygiene_controls registration | exact for timeout, output floor, and order of cheap checks |

The archived input records, confirmed tracked, are .planning/milestones/v0.4-ROADMAP.md and .planning/milestones/v0.4-REQUIREMENTS.md. They are sources for historical facts, not files to change in this planning-only scope. All 12 paths in the table passed the tracked-source gate with git ls-files.

## Pattern Assignments

### 1. Dense-input isolated Git fixture context

**Affected surfaces:** tests/scripts/verify-dense-input.py and tests/scripts/verify-fixture-admission.py.
**Classification:** test harness / batch; production admission utility / request-response.

**Analog:** The current dense-input harness already copies only tracked source into a disposable tree and keeps a pinned baseline object store separate. It does not initialize a subject repository, which is the D-212 gap. Preserve that isolation while adding the candidate HEAD and active admission-pin objects to the temporary subject's Git context; do not solve it by putting candidate history into the separate baseline store. Assert the expected full HEAD and pin ancestry before CMake configure. Keep production admission behavior fail-closed.

**Tracked-source copy and separate baseline pattern** (verify-dense-input.py:97-129):

~~~python
def copy_tracked_source(destination: Path) -> None:
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True,
                            stdout=subprocess.PIPE).stdout.split(b"\0")
    ...
    if source.is_symlink():
        ...
        shutil.copyfile(resolved, target)
    else:
        shutil.copy2(source, target)

def create_baseline_object_store(destination: Path) -> None:
    initialized = run(["git", "init", "--bare", str(destination)], cwd=ROOT)
    ...
    fetched = run(["git", "--git-dir", str(destination), "fetch", "--no-tags",
                   str(ROOT), BASELINE_COMMIT], cwd=ROOT)
    ...
    verified = run(["git", "--git-dir", str(destination), "cat-file", "-e",
                    f"{BASELINE_COMMIT}^{{commit}}"], cwd=ROOT)
~~~

**Admission guard to retain** (verify-fixture-admission.py:146-153, 771-787):

~~~python
def check_commit(root: Path, revision: object, token: str) -> str:
    if not isinstance(revision, str) or not HEX40.fullmatch(revision):
        raise Reject(token, "expected one full lowercase commit id")
    git(root, "cat-file", "-e", f"{revision}^{{commit}}")
    return revision

pin = check_commit(root, pin_text, "admission-pin-invalid")
current_head = git(root, "rev-parse", "--verify", "HEAD^{commit}")...
ancestry = subprocess.run(["git", "merge-base", "--is-ancestor", pin, current_head], ...)
if ancestry.returncode != 0:
    raise Reject("admission-pin-not-in-history", pin)
~~~

The existing harness uses expected rejection reasons for missing or wrong baseline objects (verify-dense-input.py:132-140, 211-234). Reuse that causal-control style for missing candidate objects and wrong ancestry. Preserve its source-archive qualification assertion at lines 244-257, which checks that a gitless source copy stays unqualified with revision "unknown". The dense-input self-test builds a runner and executes the admitted Libbet case (lines 167-173, 244-272); it is not a local planning check.

### 2. Archived v0.4 planning evidence with the active recovery route

**Affected surfaces:** tests/scripts/verify-diagnostic-evidence.py and tests/scripts/verify-planning-hygiene.py. Read-only historical sources: .planning/milestones/v0.4-REQUIREMENTS.md and .planning/milestones/v0.4-ROADMAP.md.
**Classification:** evidence/planning checkers / batch transform; archived records / immutable inputs.

**Analog:** Reuse the exact-revision Git tree and snapshot readers, but select archived v0.4 requirement facts while retaining the active Phase 24 route from the root roadmap. The current diagnostic checker hard-codes the removed root requirements path in REQUIRED and BOUNDARY_PATHS (verify-diagnostic-evidence.py:68-79), and its old D-206 validation asserts the former Pending statuses (lines 519-529, 929-943). Preserve its immutable snapshot machinery, not those obsolete source/status assumptions.

**Safe immutable snapshot pattern** (verify-diagnostic-evidence.py:257-276):

~~~python
def load_snapshot(root: pathlib.Path, revision: str,
                  paths: tuple[str, ...] = REQUIRED) -> dict[str, bytes]:
    entries = tree_entries(root, revision)
    result = {}
    for path in paths:
        if not safe_path(path):
            raise Reject(f"source-path-unsafe:{path}")
        item = entries.get(path)
        if item is None:
            raise Reject(f"source-record-missing:{path}")
        _oid, size, mode = item
        if mode == "120000":
            raise Reject(f"source-symlink-refused:{path}")
        ...
        content = git(root, "show", f"{revision}:{path}", ...)
        ...
~~~

**Planning reader boundary** (verify-planning-hygiene.py:225-279, 282-301): read_rev requires a full commit and uses git show/ls-tree for its data. Its current archive fallback only activates after a completed milestone with no active phase paths and no root requirements file (lines 240-261). That fallback is not the D-209 shape: Phase 24 remains active. Do not reuse its all-or-nothing archive switch. Select the archived requirement/roadmap only for historical v0.4 facts, while preserving the root roadmap's Phase 24 section as the active route.

The archived requirement record says FIXT-01 remains Pending and RIGHTS-01, DIAG-01, and DIAG-02 are complete only for the accepted diagnostic scope (.planning/milestones/v0.4-REQUIREMENTS.md:67-71). Keep those dispositions and the original owner/criterion text; do not synthesize or restore a root requirements tracker. Use negative controls for wrong/missing archive paths, altered owner/status/criteria, and archive selection that drops the active Phase 24 route.

### 3. State-fork inventory and non-executable diagnostic exclusions

**Affected surfaces:** tests/scripts/verify-state-forks.py, tests/data/state-forks.json, and the existing CTest graph in tests/CMakeLists.txt.
**Classification:** inventory checker / batch transform; test configuration / batch execution chain.

**Analog:** manifest_cases already enumerates immutable manifests and requires exact equality with the configured list before expanding ROM rows (verify-state-forks.py:133-145). It then expands only fixture_manifests into cases (lines 170-212). The current excluded inventory contains a different optional tests/acid2 manifest and validates that specific exception (verify-state-forks.py:284-289; tests/data/state-forks.json:720-724). Use that fail-closed census pattern, but give the current fixtures/acid2 and fixtures/gbmicrotest manifests explicit exclusion entries with exact identity and non-execution reasons; do not put them in fixture_manifests or row expansion. Research records the current manifest SHA-256 values as 7f198d5964a8547d1a122d5d64d395547ba6f365264cdb00abf190a5880c5da6 for fixtures/acid2/manifest.json and d3aedaa5d9f583bea2951a9a58a3190ff2314fafbfa53b7e63e98ed6349cb7c for fixtures/gbmicrotest/manifest.json (24-RESEARCH.md:134). Keep the accepted case count and census tied to the active union plus explicitly validated exclusions.

**Census and expansion boundary** (verify-state-forks.py:133-145, 170-190):

~~~python
listed_manifests = {item["path"] for item in spec.get("fixture_manifests", [])}
...
actual_manifests = {line for line in tree.stdout.splitlines()
                    if line.endswith("/manifest.json")}
if actual_manifests != listed_manifests:
    raise ForkError("fixture manifest union differs from immutable tree: ...")
...
for item in spec.get("fixture_manifests", []):
    ...
    for row in rows:
        ...
        case = make_case(path, row, rom_path)
        add_case(case, cases, ids)
~~~

Existing state-fork CTests are execution-bearing: matrix shards set up gbb_state_fork_matrix_shards, the summary sets up gbb_state_fork_matrix_complete, and census/mutant controls require that fixture (tests/CMakeLists.txt:5393-5427). The skipped dependent checks after setup failure are consequences of this dependency chain. Do not run this chain locally under the planning-only authorization, and do not replay Acid2, div_inc_timing_a, or any excluded gbmicrotest case.

### 4. Historical path scanning for the closeout fixture

**Affected surfaces:** tests/scripts/verify-no-phase-paths.py, tests/data/v04-closeout.json, and tests/CMakeLists.txt.
**Classification:** linter / batch scan; historical test data / transform; CTest registration / batch.

**Analog:** The checker walks git-tracked text outside .planning, enforces must-scan files, rejects unlisted live-phase paths, and validates allowlist hit counts and reasons (verify-no-phase-paths.py:38-65, 95-153). Its current exception is count-based for an entire file. The exact historical value appears twice in v04-closeout.json, at lines 488 and 662. Prefer changing only those exact data values if the schema permits; otherwise extend the checker with exact line/content pins. Do not allowlist the whole file by count, since that would admit unrelated live readers.

**Tracked walk and stale/over-limit exception checks** (verify-no-phase-paths.py:95-128, 131-153):

~~~python
def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], ...)
    ...

for name in tracked_files(root):
    if name == ".planning" or name.startswith(".planning/"):
        continue
    ...
    for match in SPELLINGS.finditer(text):
        ...
        hits.setdefault(name, []).append((line, match.lastgroup or "?"))
...
if len(found) > pins[name]:
    raise LintError("REJECT over-max: ...")
...
need(observed == maximum, "REJECT stale-allowlist: ...")
~~~

The self-test has a useful exact-path positive and a second-occurrence negative for immutable boundary path pins (lines 242-255), plus negatives for actual reader spellings and broad scope roots (lines 230-240, 282-289). CTest already separates no_phase_paths_controls from the real no_phase_paths tree scan (tests/CMakeLists.txt:3001-3020); retain both identities and their control/output floors.

### 5. v0.4.0 checker trust and the exact D-209 notice overlay

**Affected surfaces:** tests/scripts/verify-workflow-policy-coverage.py, tests/scripts/verify-fixture-admission.py, and tests/cmake/ci-lanes.cmake.
**Classification:** workflow-policy checker / batch; fixture admission utility / request-response; CTest configuration / batch.

**Analog:** The workflow-policy checker obtains fixture-checker bytes from the fixed v0.4.0 source commit and rejects any byte difference (verify-workflow-policy-coverage.py:2117-2122, 2432-2444). Keep that tag as the independently verified trust root. The current D-209 notice overlay has a useful exact-byte precedent in verify-fixture-admission.py:937-956: it permits one named notice change at the specified path and rejects unrelated or duplicate changes. Its self-test covers an accepted exact status update and rejects a path change, altered value, unrelated edit, and duplicate anchor (lines 1368-1384).

**Tagged byte comparison** (verify-workflow-policy-coverage.py:2436-2444):

~~~python
trusted_fixture = root / "tests/scripts/verify-fixture-admission.py"
fixture_source = git_text(root, recovery_source,
                          "tests/scripts/verify-fixture-admission.py")
if trusted_fixture.read_bytes() != fixture_source:
    reject("release recovery fixture checker differs from the tagged trusted snapshot")
~~~

**One-path, one-anchor overlay pattern** (verify-fixture-admission.py:947-956):

~~~python
if current_index == pinned_index:
    return True
if (index_path != "THIRD_PARTY_NOTICES.md"
        or pinned_index.count(NOTICE_ACID2_STATUS_BEFORE) != 1):
    return False
return current_index == pinned_index.replace(
    NOTICE_ACID2_STATUS_BEFORE, NOTICE_ACID2_STATUS_AFTER, 1)
~~~

The existing workflow-policy production check is intentionally a full byte comparison; the admission checker has separate notice semantics. Treat those as distinct layers. Plan an exact, independently checked overlay over the unchanged tag bytes, with a valid positive and causal mutations; do not refresh the tagged digest, remove the comparison, or duplicate/weaken production rights logic. If the overlay cannot be separated while preserving the trust root, the D-212 plan requires stopping for owner resolution. Preserve the existing workflow_policy_coverage_controls identity (tests/cmake/ci-lanes.cmake:144-148).

### 6. Planning-hygiene self-test runtime

**Affected surfaces:** tests/scripts/verify-planning-hygiene.py and tests/cmake/hygiene.cmake.
**Classification:** planning checker / batch; CTest configuration / batch.

**Analog:** The self-test counts controls through one helper and checks expected specific error codes, with both passing and rejected plan fixtures (verify-planning-hygiene.py:1957-1985). Its gap-assessment controls create a temporary Git repository and commit disposable fixtures (lines 2487-2513, 2995-3013). That is the closest runtime shape for the archive-reader controls, and also the first place to inspect for redundant Git processes or repeated snapshot work if the same self-test remains slow.

**Existing control-count contract** (verify-planning-hygiene.py:1957-1967):

~~~python
def expect(label: str, errors: list[str], code: str | None) -> None:
    if code is None:
        if errors:
            raise SystemExit("... should pass ...")
    elif code not in codes(errors):
        raise SystemExit("... did not report ...")
    controls += 1
~~~

tests/cmake/hygiene.cmake:73-85 registers plan_cap and planning_hygiene_controls with a 30-second timeout; plan_cap is declared first and should be run as the cheap preflight when execution is later authorized. The self-test requires at least 125 controls. D-212 records one macOS timeout under parallel load and a Linux failure that occurred earlier at the missing archived requirements. Diagnose failure order and measured stage cost before considering any timeout change. Keep the existing CTest name, 125-control floor, and control coverage; do not raise the 30-second timeout by assumption.

## Shared Patterns

### Immutable identities and separate trust domains

Use full commit IDs and Git object reads for point-in-time facts. Resolve active fixture-pin commits and ancestry in the subject repository; keep the legacy baseline object store independent. Read historical v0.4 facts from the archived v0.4 records while retaining the active Phase 24 root route. Keep the v0.4.0 tag as the checker trust root and make any notice overlay a separate exact delta.

### Fail-closed validation with causal controls

The repository's Python scripts use standard-library imports, explicit path/revision validation, and narrow error types such as Reject, ForkError, and LintError. Self-tests pair valid cases with mutations that assert the intended error code, rather than accepting any failure. Preserve that structure and add no dependency or CTest identity.

### Keep excluded inputs outside execution rows

The state-fork census expands only active manifest rows, and its CTest fixture graph gates census/mutant controls on matrix setup. Model the new diagnostic manifests as exact, reasoned exclusions that never enter row expansion. Existing dense-input acceptance and state-fork matrix checks are execution-bearing; D-212 permits no such local invocation during planning.

## No Analog Found

Existing primitives are close but no current code implements these exact combinations:

| D-212 seam | Missing exact precedent |
|------------|------------------------|
| Archived planning readers | The planning-hygiene archive fallback requires a completed milestone and no active phase route; there is no precedent for archived v0.4 facts alongside the active Phase 24 root roadmap. |
| Tag plus D-209 overlay | The workflow-policy checker compares the whole current checker to tag bytes; the narrow notice overlay exists in admission policy but is not yet an independently separated overlay on that checker trust comparison. |
| Diagnostic state-fork exclusions | The current state-fork exclusion is for tests/acid2/manifest.json; it does not encode the exact fixtures/acid2 and fixtures/gbmicrotest manifest identities and non-execution reasons. |
| Historical path exception | The current allowlist pins file-wide counts, not exact immutable line/content for the two v04-closeout.json values. |

These are design gaps for the sole D-212 plan, not permission to broaden the source/trust/fixture boundaries.

## Metadata

**Analog search scope:** tests/scripts, tests/data, tests/cmake, the relevant tests/CMakeLists.txt registrations, and the archived v0.4 requirement/roadmap inputs.
**Tracked-source gate:** Every named code/test analog was verified by git ls-files; no ignored runtime or capability mirror path is cited.
**Pattern extraction date:** 2026-11-17
