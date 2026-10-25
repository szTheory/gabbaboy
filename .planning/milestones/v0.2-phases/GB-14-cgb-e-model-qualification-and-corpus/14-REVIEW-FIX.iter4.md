---
phase: 14
iteration: 4
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 14 sanitizer child deadline

## Fixed Issues

### CR-08: AGE child deadline ignores sanitizer slowdown

The old ASan job `116778422483` in Actions run `38840242246` failed the AGE assertion-identity adapter when the `stat-mode-ds-cgbBCE` child exceeded its fixed 15-second deadline. This was separate from the five configured-build-directory failures. CTest's sanitizer timeout scaling did not reach the Python child call.

CMake now passes a 15-second normal or 45-second sanitizer child deadline, matching the existing threefold sanitizer policy. The adapter accepts only integer deadlines from 1 through 45 seconds and passes the selected deadline to every bounded guest call. The outer sanitizer CTest deadline remains 180 seconds; guest execution budgets and expected observations are unchanged.

The registered inherited-contract unit test covers all 13 child calls with the selected deadline, rejects zero, excessive, boolean and fractional values, and propagates a timeout as a failure. Its new regression failed before the API accepted the configured deadline, then passed after the fix. The live AGE identity and inherited-contract CTests passed 2/2, and the CMake source selects the 45-second child limit while the existing threefold policy scales the 60-second outer limit to 180 seconds. This macOS host rejects the Linux-only sanitizer preset, so no local sanitizer configuration or execution is claimed. Actual hosted sanitizer execution remains pending for the final revision.
