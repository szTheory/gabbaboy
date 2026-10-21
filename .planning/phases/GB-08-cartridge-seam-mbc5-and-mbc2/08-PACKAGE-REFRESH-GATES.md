---
phase: "8"
artifact: package-refresh-gates
refreshed: "2026-10-21T00:09:37Z"
status: supplemental_pass
scope: preview-package-fixture-exclusion
---

# Phase 8 Package Refresh Gates

This supplement refreshes the Phase 8 package-fixture exclusion evidence for the later change in commit `1ba2346` (`cmake/PreviewPackageSmoke.cmake`). That change extends the extracted preview-package scan from the Mooneye MBC manifest to both Mooneye MBC and CGB manifests, and adds a renamed CGB ROM negative control. All ten Phase 8 plans have execution summaries. This report does not re-audit the mapper implementation or re-run the full Phase 8 gate set.

## Scope and gate routing

The installed runtime identified as `@opengsd/gsd-core` 1.18.0. Project hooks are enabled for Nyquist validation, security enforcement, UI review, and code review; both automatic-advance settings are false.

The Phase 8 evaluation-scope resolver returned `degraded` with reason `no-reachable-task-commits`: its historical range contains 415 files and five unreachable commits (`0082ae2`, `08fb22c`, `2b154fc`, `69f1a90`, `b126ec7`), with no missing files. That range is not used here as a claim of a fresh 415-file review. The direct source review is limited to the package-smoke change in `cmake/PreviewPackageSmoke.cmake` and its scanner/test connections. The companion `.planning/context/LESSONS.md` change in `1ba2346` is outside this source-gate supplement.

## Refreshed evidence

### Nyquist validation

The historical [08-VALIDATION.md](08-VALIDATION.md) remains `validated` and Nyquist-compliant with 27 mapped checks. Its V-25 row describes the then-current MBC package scan; it does not include the later CGB-manifest extension. The following current checks supplement that row:

| Check | Result | Evidence |
|---|---|---|
| `preview_package_smoke` | PASS | Reinstalled and extracted the package; the clean MBC+CGB scan passed, and the CMake script printed `Extracted package renamed CGB fixture rejected by digest` for its renamed-payload negative control. Relocation, runner, and external C/C++ consumer smokes also completed. |
| `mooneye_mbc_not_installed_link_selftest` | PASS | The scanner rejected a forbidden MBC ROM reached through an innocuous symlink name. |
| `cgb_mooneye_not_installed_selftest` | PASS | The scanner rejected a renamed CGB fixture planted as `share/payload.bin`. |
| `mooneye_mbc_not_installed` and `cgb_mooneye_not_installed` | PASS | The install-tree scans passed; CTest also ran the `libbet_install_tree` setup fixture. |
| Direct combined MBC+CGB scan of the extracted package | PASS | `mooneye-mbc absent from scanned tree files=17`; the exact fixture-directory allowlist matched. |

The CTest runs were:

```text
ctest --test-dir build --output-on-failure -R '^(preview_package_smoke|mooneye_mbc_not_installed_link_selftest|cgb_mooneye_not_installed_selftest)$'  # 3/3 passed
ctest --test-dir build --output-on-failure -R '^(cgb_mooneye_not_installed|mooneye_mbc_not_installed)$'                  # 3/3 passed including install fixture
ctest --test-dir build-player --output-on-failure -R '^player_session_classification_drift$'                             # 1/1 passed
```

`preview_package_smoke` was also run verbosely and passed, showing the renamed-CGB rejection message and the final relocated-package consumer-smoke message. No full CTest run was repeated by this scoped reviewer; the parent workflow records its separate fresh regression in 08-PACKAGE-REFRESH-EVIDENCE.md.

### Security enforcement

The historical [08-SECURITY.md](08-SECURITY.md) records 41 plan-authored threats, `threats_open: 0`, and ASVS level 1. Under the secure-phase workflow, a plan-authored register with zero blocking open threats at level 1 short-circuits the deeper auditor pass. This is the existing receipt, not a new verification of all 41 mitigations. For the changed package boundary, the refreshed install-tree and extracted-package clean scans plus planted CGB/MBC negative controls passed as listed above. No new package-exclusion finding was observed in the scoped change.

### UI review

The UI-review hook is enabled, but this refresh changes package-test CMake only; no player UI source or copy changed, and Phase 8 has no `08-UI-SPEC.md`. No UI review was run and this supplement makes no refreshed phase-wide UI claim.

### Code review and dispositions

The historical [08-REVIEW.md](08-REVIEW.md) is a standard review of 27 files at its recorded 2026-10-11 head, with 0 critical, 2 warnings, and 3 info findings. [08-REVIEW-DISPOSITION.md](08-REVIEW-DISPOSITION.md) records all five dispositions with `open: 0`:

- WR-01 (scanner skipped symlink targets) is fixed in the current scanner, which resolves file-link targets before digest checks. `mooneye_mbc_not_installed_link_selftest` passed.
- WR-02 (player battery classification duplicated core type data) was deferred to Phase 9. Its current drift test passed; inspection confirms it iterates every cartridge type byte `0..255` and RAM code `0..5`, comparing player classification and load acceptance against the core.
- IN-01 is fixed: the scanner lowercases manifest digests before comparison. IN-02 and IN-03 remain skipped as documented in the disposition.

The `1ba2346` CMake delta was reviewed in context at `cmake/PreviewPackageSmoke.cmake:67-92`. The combined manifest scan checks the clean extracted package; the planted CGB payload must produce the expected digest-rejection diagnostic, and it is removed before the script proceeds to consumers. No new bug or security finding was identified in this scoped review. The GSD scope resolver's degraded 415-file union was not treated as a completed broad review.

## Limits

These checks validate the current preview-package installation and relocation behavior on the existing local build products. They do not establish fresh results for the historical 27 Nyquist rows, all 41 threat mitigations, the complete Phase 8 source set, or other platforms. No source files or old phase receipts were changed.
