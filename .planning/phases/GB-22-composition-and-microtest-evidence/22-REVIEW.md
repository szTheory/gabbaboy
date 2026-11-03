---
phase: GB-22-composition-and-microtest-evidence
reviewed: 2026-11-03T16:57:11Z
depth: standard
reviewed_source: 93004a65143a4bc3199e1f028b003e2d3dd11ef6
review_base: f59ebd166a354537343dd9e87b870698cc686b2b
review_round: 2 of 2
exception_review: D-143 (1 of 1; ordinary review-round count unchanged)
files_reviewed: 1
files_reviewed_list:
  - tests/scripts/verify-diagnostic-evidence.py
findings:
  critical: 0
  warning: 0
  info: 0
  necessity: 0
  total: 0
status: clean
prior_source_review:
  reviewed_source: f59ebd166a354537343dd9e87b870698cc686b2b
  review_round: 2 of 2
  files_reviewed: 3
  findings:
    critical: 0
    warning: 1
    info: 0
    total: 1
  status: blocked
historical_review:
  reviewed: 2026-11-03T13:00:48Z
  reviewed_source: 06d2cbc1e0ceaa100cc0ecc28826e39794a73f04
  status: clean
  findings: 0
---

# Phase GB-22: Code Review Report

## Historical Review (06d2cbc1)

**Reviewed:** 2026-11-03T13:00:48Z

**Depth:** deep

**Files Reviewed:** 12

**Source identity:** `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04`

**Review base:** `7f57dcc3542fb274f74257f48c6cd9d1c7e49741`

**Status:** clean

## Summary

Reviewed the Phase 22 source delta through `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04`, including the CTest inventory wiring and the planning-label exception. The build-directory regression and inventory-only command bypasses found during review are fixed and covered by causal controls. All reviewed files meet quality standards. No unresolved findings remain.

The evidence contract remains metadata-only: 513 named cases, seven unresolved real-fixture gates, zero admissions, and zero executions. No upstream payload was fetched or run, and no real diagnostic result was produced.

## Verification Evidence

- `verify-diagnostic-evidence.py --check --repo-root . --source-revision 06d2cbc1e0ceaa100cc0ecc28826e39794a73f04 --build-dir build` passed with 513 cases, seven unresolved gates, admitted=0, and executed=0.
- `verify-planning-labels.py --self-test` passed 17 positive and negative controls, including missing classification, a build-executable injection, extra evidence-write flags, Python `-c` pass-output substitution, and an absolute Python stub.
- In a clean detached checkout configured only in `build-cmake-3.25.3`, the configured CTest contract, immutable evidence controls, live planning-label check, and planning-label controls all passed. This confirms the checker uses the active CMake binary directory even when `<repo>/build` is absent.
- `verify-diagnostic-evidence.py --self-test-controls` passed in the clean configured checkout, including immutable boundary, source-archive, and payload-rejection controls.
- `verify-cgb-candidates.py --self-test-controls` passed with 71 negative controls in an isolated temporary Git configuration. `verify-diagnostic-admission.py --self-test-controls` passed 12 controls.
- `verify-cgb-progress.py --self-test --repo-root .` passed its observation, identity, timing, digest, PCM, dump, source-history, and Git-hook controls under an isolated temporary Git configuration.
- `verify-no-phase-paths.py --self-test` passed 19 controls and `--check` scanned 594 files. `run-acid2-local.py --self-test` passed six checks.

## Finding Dispositions

- **CR-01, immutable Phase 20 checker/policy binding:** Closed; exact-head admission controls reject worktree mutations to the checker and policy.
- **T-22-30, renamed ROM/archive/payload guard:** Closed; immutable evidence controls cover renamed and extensionless payloads.
- **CR-02, SVG root and encoding coverage:** Closed for the reviewed UTF-8, namespaced, internal-subset doctype, and UTF-16 variants.
- **CR-03, checker self-classification as SVG:** Closed; the immutable evidence check passes.
- **CR-04, no-Git source-archive configure:** Closed; the source-archive control passes.
- **WR-01, bounded subprocess output:** Closed in the reviewed source.
- **WR-02, aggregate added-file buffering:** Closed; added blobs are inspected one at a time.
- **CR-05, temporary Git hook/signing execution:** Closed; the exact-head controls use isolated Git configuration and pass.
- **CR-06, evidence CTest using the wrong build directory:** Closed at `24c4e191`; the contract passes from a clean alternate binary directory.
- **WR-03, inventory-only command accepted extra flags:** Closed at `9d39195a`; an output-flag mutation is rejected.
- **CR-07, inventory-only command could replace the checker invocation:** Closed at `06d2cbc1`; the verifier binds to the current absolute Python executable and rejects both `python -c` and a Python stub.

## Narrative Findings (AI reviewer)

All reviewed files meet quality standards. No unresolved findings.

---

_Reviewed: 2026-11-03T13:00:48Z_

_Reviewer: the agent (gsd-code-reviewer)_

_Depth: deep_

## D-142 Review-Fix Round Ledger

The prior Phase 22 review history uses one review-fix round of the two-round cap. The round resolved the inventory command-shape and interpreter findings before the clean review of source `06d2cbc1e0ceaa100cc0ecc28826e39794a73f04`; the dispositions point to commits `24c4e191`, `9d39195a`, and `06d2cbc1`. The full-suite gap round is separately used and remains the single permitted gap round, as recorded in `22-11-SUMMARY.md` and commits `26082639` through `06d2cbc1`.

The D-142 review used the second and final review-fix round. At source `4e532d76a671a33daa91576e283e84a8bd442b71`, both reviewers found that the new sanitizers left OSC payloads when terminated by ESC-backslash. Commit `f59ebd166a354537343dd9e87b870698cc686b2b` corrects the 7-bit OSC BEL and ESC-backslash handling, and direct controls reject both synthetic title payloads.

**Review status at the last reviewed source `f59ebd166a354537343dd9e87b870698cc686b2b`: BLOCKED.** The corrected-source code review found a remaining T-22-38 edge: an 8-bit C1 OSC sequence (`U+009D … U+009C`) has its control bytes removed but leaves the printable payload (`0;synthetic-c1-title`) in the diagnostic. This contradicts the plan's requirement to remove control/escape sequences. The independent ASVS review at this source returned SECURED for T-22-36/37/38, but its review did not cover the C1 form; the later code-review finding keeps the combined updated-source review open. No other source finding was reported. Under D-142's original allowance, no further code change or re-review was authorized; the owner subsequently approved the narrow D-143 exception below.

## D-143 Owner-Approved Exception

On 2026-11-03, the owner authorized exactly one additional fix-and-independent-review cycle, limited to the C1 OSC payload leak. Amend the existing 22-12 plan in place. The prior two review-fix rounds and the single gap round remain used; no new plan, gap round, broader source repair, or review-cap reset is authorized. If the C1 correction or its fresh independent review surfaces another blocking correctness/security issue, stop Phase 22 for owner scope resolution. If the C1 review is clean, continue the already approved final local and exact-head PR qualification. No final full-suite or fresh remote qualification has started at the source named above.

## D-143 Exception Review (one exception review)

**Reviewed:** 2026-11-03T16:57:11Z

**Depth:** standard, focused exact-source review

**Source identity:** `93004a65143a4bc3199e1f028b003e2d3dd11ef6`

**Review base:** `f59ebd166a354537343dd9e87b870698cc686b2b`

**Files reviewed:** `tests/scripts/verify-diagnostic-evidence.py`

**Ordinary review-fix ledger:** 2 of 2 used; unchanged. This is the single D-143 exception review and does not reset the ordinary-round or gap-round counters.

**Status:** clean; no findings.

### Review Evidence

- The checker decodes byte diagnostics as UTF-8 with replacement before applying the C1 OSC expression. The expression removes the complete `U+009D … U+009C` span non-greedily across line breaks before roots are replaced and remaining controls are normalized.
- The synthetic diagnostic is UTF-8 bytes. Its sentinels before and after the OSC remain required, while the title payload and both C1 delimiters must be absent. The control also retains coverage for existing 7-bit CSI/OSC handling, Unix/Windows/home-root redaction, and the 700-character output cap.
- The fail-first mutation replaces only `C1_OSC_ESCAPE` with a never-match expression and requires the sanitization assertion to reject the surviving printable C1 payload; the original expression is restored in `finally`.
- `tests/CMakeLists.txt` is byte-for-byte unchanged between the review base and source. The existing `phase22_evidence_controls` CTest still invokes `--self-test-controls` with its 60-second timeout and planning label; no CTest wiring or limit changed in this delta.

### Narrative Findings (AI reviewer)

All reviewed changes meet the scoped requirements. No issues found.
