# Planning closeout scan

Run the repository compatibility scan from the checkout root:

```sh
python3 tests/scripts/verify-closeout-scan.py --check --output build/closeout-scan.json
python3 tests/scripts/verify-closeout-scan.py --self-test
```

The first command invokes the installed `@opengsd/gsd-core` `audit-open --json` command without changing planning artifacts. Its JSON report preserves the exact runtime stdout and stderr, parsed source payload, installed package identity and version, project Git revision, and SHA-256 revision of the installed CLI entry point. It adds one classified record per runtime finding and keeps duplicate findings as separate records.

The installed audit currently treats filenames containing `-UAT` as UAT documents, so a clean file such as `14-UAT-REVIEW.md` can appear under the raw `uat_gaps` list. The wrapper retains that finding as source evidence and marks it non-blocking only when the exact `N-UAT-REVIEW.md` filename has a `status: clean` verdict, exactly one each of `critical`, `warning`, `info`, and `total` under `findings`, all four counts are zero, the total matches their sum, and the raw runtime item also reports `status: clean` with zero open scenarios. This classification does not edit, acknowledge, or rename the review.

The observed repository scan with OpenGSD 1.18.0 retained the clean Phase 14 review in the raw UAT list and classified it as `clean-review`. The overall result remained blocked by one separate Phase 13 deferred linker-warning record. This is the expected closeout behavior: the SCAN-UAT false positive is separated while real open debt stays visible.

An exact canonical `N-UAT.md` reported as incomplete stays blocking. Dirty or malformed reviews, unknown UAT-related filenames, scan errors, missing project revision, and every other open audit category also stay visible and blocking. The output's `raw_limitation` records when the installed runtime produced the clean-review false positive; the wrapper does not patch or upgrade that runtime.

Exit status `0` means the scan completed with no classified blocking records. Status `1` means the scan completed and retained one or more blocking findings. Status `2` means the runtime identity, audit result, or output write failed; when `--output` is writable, the error record retains available raw diagnostics.
