# Phase 16 deferred items

## 16-01

- `tests/scripts/verify-closeout-scan.py --self-test` fails 2 of 8 tests (`test_clean_review_is_nonblocking_but_pending_canonical_uat_blocks`, `test_archived_review_is_checked_at_its_exact_archive_source`). The failures reproduce on the pre-move tree at `131d7ae`, so they predate this plan and depend on how the installed OpenGSD runtime scans the fixture. No CTest runs the script. Out of scope for TUNE-01; decide in a later plan whether to repair or retire it.
