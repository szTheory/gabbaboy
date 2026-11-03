# Phase 22: Composition and Microtest Evidence — Pattern Map

**Mapped:** 2026-11-03
**Files classified:** 3 existing Task 1 source files
**Analogs found:** 3 / 3

This map is for the D-143 addition to existing plan 22-12. Its only new source delta is the C1 OSC sanitizer correction and its regression inside `tests/scripts/verify-diagnostic-evidence.py`. The other two files remain part of the pre-existing D-142 Task 1 scope; they are listed here because they are in that task's `<files>` field, not because D-143 expands their scope.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality / Scope |
|---|---|---|---|---|
| `tests/scripts/verify-cgb-progress.py` | utility / checker | request-response; bounded subprocess output is parsed into progress evidence | `tests/scripts/verify-diagnostic-evidence.py` | role-match; existing D-142 Task 1 only, not part of the C1 delta |
| `tests/scripts/verify-diagnostic-evidence.py` | utility / checker | transform for the affected path: diagnostic bytes or text → sanitized bounded text | its existing `sanitized_diagnostic` and `diagnostic_sanitization_control` | exact; sole C1 source target |
| `tests/scripts/verify-planning-labels.py` | utility / checker | request-response; configured CTest inventory → pass/reject result | its existing path normalization and self-test | exact; existing D-142 Task 1 only, not part of the C1 delta |

## Pattern Assignments

### `tests/scripts/verify-diagnostic-evidence.py` (utility, bounded diagnostic transform)

**Analog:** the existing implementation and synthetic control in the same tracked file. The implementation uses Python standard-library modules only (imports, lines 5–18); no new dependency or module is needed.

**Current sanitizer order** (lines 85–109):

```python
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ANSI_ESCAPE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
DIAGNOSTIC_CONTROLS = re.compile(r"[\x00-\x1f\x7f-\x9f]+")

def sanitized_diagnostic(value: bytes | str,
                         roots: tuple[tuple[str | pathlib.Path, str], ...]) -> str:
    """Return at most 700 characters without escape sequences or local roots."""
    text = value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)
    text = ANSI_ESCAPE.sub("", text)
    replacements: dict[str, str] = {}
    for root, token in roots:
        native = os.fspath(root)
        if not native:
            continue
        for spelling in {native, native.replace("\\", "/"), native.replace("/", "\\")}:
            if spelling:
                replacements[spelling] = token
    for spelling, token in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(spelling, token)
    return " ".join(DIAGNOSTIC_CONTROLS.sub(" ", text).split())[:700]
```

The correction belongs between the existing ESC-sequence removal and generic C0/C1 cleanup: consume the complete 8-bit OSC span (`U+009D` through `U+009C`) while its delimiters are still present. Preserve root substitutions, generic control cleanup, whitespace compaction, and the 700-character cap. Do not broaden the sanitizer or alter unrelated diagnostic call sites.

**Existing synthetic regression control** (lines 1024–1037):

```python
def diagnostic_sanitization_control(root: pathlib.Path) -> None:
    windows_root = r"C:\Users\runneradmin\AppData\Local\Temp\gbb-diagnostic-probe"
    raw = (f"\x1b[31mconfigure failed at {root}/project\x1b[0m\t"
           f"{windows_root}\\project\n"
           "\x1b]0;synthetic-secret-title\x1b\\\x1b]0;synthetic-bel-title\x07" + "x" * 900)
    detail = sanitized_diagnostic(
        raw, ((root, "<temp>"), (windows_root, "<windows-temp>"),
              (pathlib.Path.home(), "<home>")),
    )
    if (len(detail) > 700 or "\x1b" in detail or "\n" in detail or "\t" in detail
            or str(root) in detail or windows_root in detail
            or "synthetic-secret-title" in detail or "synthetic-bel-title" in detail
            or "<temp>" not in detail or "<windows-temp>" not in detail):
        raise Reject("diagnostic-sanitization-control-failed")
```

Extend this existing control with one synthetic byte input that has an ordinary prefix, `\u009d0;synthetic-c1-title\u009c`, and an ordinary suffix. Assert that the payload is absent while the prefix and suffix survive, and retain the current checks for ESC controls, local roots, whitespace/control cleanup, and the 700-character bound. Feed UTF-8 bytes, matching the captured `out + err` input used by the production error path. Keep the current ESC CSI and ESC OSC examples.

The existing self-test calls `diagnostic_sanitization_control` before its other bounded-process controls (lines 1160–1163); `self_test(..., controls=True)` is selected by the existing CLI (lines 1072, 1377). Keep the C1 case inside this path.

**Existing CTest contract** (tracked `tests/CMakeLists.txt`, lines 3711–3719):

```cmake
add_test(NAME phase22_evidence_controls
  COMMAND "${Python3_EXECUTABLE}" -I "${GBB_PHASE22_EVIDENCE_CHECKER}" --self-test-controls
    --repo-root "${PROJECT_SOURCE_DIR}" --source-revision "${GBB_PHASE22_EVIDENCE_SOURCE_REV}")
set_tests_properties(phase22_evidence_controls PROPERTIES TIMEOUT 60 LABELS planning
  PASS_REGULAR_EXPRESSION "diagnostic evidence controls pass positives=1 rejected_controls=passed boundary=immutable")
```

The C1 regression stays under this test identity and preserves its command, label, pass expression, inventory membership, and 60-second timeout. No new CTest registration is needed.

### Existing D-142 Task 1 files outside the C1 delta

`tests/scripts/verify-cgb-progress.py` already has a standard-library checker, synthetic controls, and bounded diagnostic sanitization; it is a nearby utility pattern for its pre-existing D-142 repair. `tests/scripts/verify-planning-labels.py` has a local path-normalization helper and self-test for its pre-existing D-142 repair. D-143 does not assign either file new C1 behavior; do not spread this one correction into those files or expand it into test-inventory/CI changes.

## Shared Patterns

### Bounded diagnostic text

**Source:** `tests/scripts/verify-diagnostic-evidence.py:94-109`
**Apply to:** the existing `sanitized_diagnostic` path only.

Decode bytes with replacement, remove complete escape/control spans before stripping individual controls, redact local roots in all path spellings, compact whitespace, and retain the current 700-character ceiling.

### Synthetic negative control

**Source:** `tests/scripts/verify-diagnostic-evidence.py:1024-1037,1160-1163`
**Apply to:** the existing `diagnostic_sanitization_control` called by `--self-test-controls`.

Use synthetic input only. Assert the C1 payload is absent and surrounding ordinary text remains. Retain existing sanitizer assertions and the current `phase22_evidence_controls` CTest contract.

## Metadata

**Analog search scope:** `tests/scripts/`, the `phase22_evidence_controls` registration in `tests/CMakeLists.txt`, and the D-143 sections of `22-RESEARCH.md` / `22-12-PLAN.md`.
**Tracked-source check:** all analog paths named above are tracked by Git.
**Pattern extraction date:** 2026-11-03
