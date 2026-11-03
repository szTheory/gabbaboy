---
phase: GB-22-composition-and-microtest-evidence
reviewed_source: 93004a65143a4bc3199e1f028b003e2d3dd11ef6
review_level: ASVS 1
source_review: clean
status: source-review-clean
verdict: SECURED
blocking_findings: 0
threats_open: 0
exception_review: D-143 (1 of 1; ordinary review/gap counts unchanged)
---

# Phase 22 Security Review

## Current D-143 C1 Review

- **Reviewed source:** `93004a65143a4bc3199e1f028b003e2d3dd11ef6`
- **Review level:** ASVS 1
- **Verdict:** SECURED; zero blocking findings
- **Scope:** The C1 OSC payload-disclosure edge of T-22-38 in `tests/scripts/verify-diagnostic-evidence.py`.

The independent security auditor confirmed that the C1 OSC payload and delimiters are removed after UTF-8 decoding and before generic control cleanup, while ordinary surrounding text survives. Existing ESC CSI/OSC handling, native/Windows/home-root replacement, whitespace cleanup, and the 700-character limit remain. The augmented byte control is called from the existing `phase22_evidence_controls` self-test.

The reviewed source's direct control passes. Disabling only the C1 matcher produces `diagnostic-sanitization-control-failed`, and restoring it passes. The amended regression also fails against the exact pre-C1 sanitizer at `f59ebd166a354537343dd9e87b870698cc686b2b`. The ignored records `build/phase22/c1-fail-first.json` and `build/phase22/c1-direct-and-mutation.json` retain the local results. AST comparison found changes only in `sanitized_diagnostic` and `diagnostic_sanitization_control`; registrations, expected-test policy, presets, CI workflow and the existing 60-second CTest limit are unchanged. Output draining, caps, termination, reader joins, child timeouts and retained causal controls remain intact.

The earlier ASVS result at `f59ebd166a354537343dd9e87b870698cc686b2b` did not cover the C1 form and is not used as evidence for this closure. This is the single D-143 exception review; the two ordinary review-fix rounds and one gap round remain used. Phase 22's final local full suite, exact-head required CI, Windows coverage, fixture/package artifacts, protection checks, and merge-tree comparison passed for PR #142 before its merge. T-22-32 is closed for the Phase 22 source-to-remote qualification. The later PR #143 Windows scheduling fix is operational cleanup and is recorded separately in `22-EVIDENCE.md`.

## Historical Security Review — 06d2cbc1

The independent source audit reviewed exact source `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04`. No unresolved source-level correctness or security findings remain. This audit occurred before the Phase 22 PR was opened; the final operational status of T-22-32 is recorded in `build/phase22/remote-evidence.json`.

## Threat Dispositions

| Threat / finding | Disposition | Evidence |
|---|---|---|
| T-22-30 — payload admission boundary | Mitigated. Added paths are rejected by path and content signatures, including `.rar`, `.zst`, `.dat`, extensionless archive/image/ROM payloads, UTF-8/UTF-16 SVG roots, long comments, namespace prefixes, and DOCTYPE subsets. Each added blob is bounded and inspected individually. | Exact-source `verify-diagnostic-evidence.py --self-test-controls`; immutable `--check`; added-path scan. |
| CR-01 — mutable Phase 20 dependency | Mitigated. The Phase 20 checker and policy are read from the selected immutable commit and compared with worktree bytes before checker execution; separate mutations of each dependency are refused. | `verify-diagnostic-admission.py --self-test-controls` passed 12 controls. |
| CR-07 — planning inventory command substitution | Mitigated. The exception is limited to the named evidence contract and exact isolated invocation. It resolves the invoked absolute interpreter and requires it to match `sys.executable`; it pins the checker, source revision, source root and configured build directory, with no extra arguments. | `verify-planning-labels.py --self-test` passed 17 controls, including executable injection, `--write-evidence`, Python `-c`, and an absolute Python stub. The configured inventory check passed with 1,732 tests and 47 planning-labelled tests. |
| T-22-33 — requirement and closure accounting | Mitigated. DIAG-01/02 and RIGHTS-01 retain their original Pending definitions and dispositions; closure is derived from automated summary coverage. | Plan 22-02 D2 has `human_judgment: false`; immutable boundary and shared closure controls. |
| T-22-34 — unintended phase transition | Mitigated. The boundary requires both automatic-advance flags false, Phase 23 unstarted, and the owner route `/gsd-discuss-phase 23`. | Immutable boundary check and its route/auto-flag mutation controls. |
| T-22-35 — public information disclosure | Mitigated. Public artifacts use repository-relative paths and public source/check identities; no home path, personal media, or credentials were added. | Scoped public-artifact review. |
| T-22-SC — package/dependency installation | Mitigated. No package install or new dependency was introduced. | Scoped source review and existing toolchain controls. |
| T-22-32 — source-to-remote qualification | Exact-head checks are required. The final local source must match the PR head, with successful required CI, fixture reproduction, preview package jobs/artifacts, review dispositions, and merge-tree equivalence. | `.github/scripts/verify-pr-evidence.sh`; final sanitized identity record in `build/phase22/remote-evidence.json`. |

## Exact Source Evidence

- `verify-diagnostic-evidence.py --check` passed at the reviewed source with 513 metadata cases, seven unresolved real-fixture gates, zero admissions, and zero executions.
- `verify-diagnostic-admission.py --self-test-controls` passed all 12 mutation controls; `--require-approved` returned exit 2 with the complete seven-gate `scope-resolution-required` list.
- The planning-label CTest check and its 17-control self-test passed. The explicitly configured inventory is used, including in alternate CMake build directories; the planning contract reads CTest's JSON listing and does not execute a built artifact.
- `verify-no-phase-paths.py --self-test` passed 19 controls; its current tree check scanned 594 tracked files.
- The candidate-record regression controls reject a primary no-go reference whose commit is not an ancestor of the selected source and reject a mismatched digest. The referenced Potion Panic JSON blob at PR #140's squash merge and the current checked-in record both have Git blob `f3583f2933e48479b275e68beb275cfd1f356c01` and SHA-256 `9a23c0c13dba57f7806b19501756f09616c6cbbebe1e4bcef04eb099bf8ca352`.
- No upstream ROM/reference payload was fetched, retained, built, run, or admitted. No real diagnostic result or license prohibition is claimed.

## Remote Qualification

Source review is clean. T-22-32 is the exact-head operational gate; this source audit makes no claim that it passed. Its final disposition is determined by the required same-head CI and artifacts, review state, exact-head equality, and merge-tree equivalence recorded in `build/phase22/remote-evidence.json`. Any inaccessible, stale, skipped, failed, or mismatched result leaves Phase 22 unclosed.
