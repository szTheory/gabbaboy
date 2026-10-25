---
phase: "7"
slug: "dmg-game-acceptance-and-regression-baseline"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-10"
---

# Phase 7 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Upstream release → repository | Third-party Libbet ROM, licence and closure admitted once | ROM bytes, notices; integrity-pinned by SHA-256 |
| Case / script files → runner | Text case and input-script files parsed by `gabbaboy-runner` | Untrusted text; bounded parse before any guest state |
| Runner → filesystem | Failure PPMs and stall reports written to `--failure-dir` | Derived artefacts only; fixed names from validated ids |
| CLI → player script smoke | `--smoke-package` / `--input-script` diagnostic in the packaged player | Script + ROM; no network, saves, or environment activation |
| Toolchain downloads → opt-in reproduction | RGBDS archive and Pillow wheels in `reproduce-libbet.sh` | Hash-pinned archives; dispatch-only, read-only token |
| Frozen ledger → later phases | `tests/baseline/dmg-cpu-b-v1.txt` and CHANGES protocol | Digests; no update mode, reverse-apply change records |
| CI evidence → completion claims | Exact-head required checks and JUnit inventories | Run ids, job conclusions |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-07-01 | Repudiation | rights.embedded_assets | high | mitigate | `tests/scripts/verify-libbet-admission.py` closure digest + record checks; 5 negative tests + `--self-test` | closed |
| T-07-02 | Tampering | fixtures/libbet/libbet.gb | high | mitigate | Size/digest/header checks; `.gitattributes -text`; required CI never fetches upstream | closed |
| T-07-03 | Tampering | admission download | medium | mitigate | One-time empty-scratch download accepted only on exact digest (`fixtures/libbet/SOURCES.md`) — process evidence | closed |
| T-07-04 | Tampering | verifier JSON parse | low | mitigate | Duplicate-key rejection, fixed paths, `python3 -I` | closed |
| T-07-05 | Tampering / Info disclosure | `src/runner/cases.c` paths | high | mitigate | Rejects absolute, `.`/`..`, empty segments, backslash, colon; `acceptance_negative_path_traversal` | closed |
| T-07-06 | DoS | input_script time arithmetic | medium | mitigate | Overflow checks, 600 s and event caps; `acceptance_parse_script_bounds` | closed |
| T-07-07 | DoS | script parser | medium | mitigate | 64 KiB / line caps, NUL and non-ASCII rejection, free-on-failure; `acceptance_parse_script_errors` | closed |
| T-07-08 | Tampering | partial execution | medium | mitigate | Case, script digest, script parse, ROM size/digest all validated before `gbb_load_rom` | closed |
| T-07-09 | DoS | heap ROM loader | medium | mitigate | 8 MiB cap with capacity+1 read; Mooneye buffers on heap | closed |
| T-07-10 | Tampering | audio mix change | medium | mitigate | Core and test changed together (ed4cb9d); D-027, GB-AUDIO-001 | closed |
| T-07-11 | Elevation of privilege | scratch Libbet clone | medium | mitigate | 07-17 probe read the clone only — process evidence (07-17-SUMMARY) | closed |
| T-07-12 | Repudiation | audio investigation outcome | low | mitigate | D-027, GB-AUDIO-001 | closed |
| T-07-13 | Elevation of privilege | libbet-repro token | high | mitigate | `workflow_dispatch` only, `contents: read`, no secrets, no upload | closed |
| T-07-14 | Tampering | RGBDS archive and Pillow | high | mitigate | Provenance check before download, archive SHA before extract, `pip --require-hashes --no-deps` | closed |
| T-07-15 | Tampering | vendored ROM | medium | mitigate | Reproduction writes only to `mktemp -d`, compares with `cmp`; not in `ci.yml` | closed |
| T-07-16 | Tampering | PPM output path | medium | mitigate | Names from validated `[a-z0-9-]` id + fixed suffix; probed directory; `acceptance_failure_dir_unwritable` | closed |
| T-07-17 | Tampering | cross-OS digests | high | mitigate | Explicit P6 header + LE int16 hashing; independent Python vector `acceptance_digest_vectors` | closed |
| T-07-18 | Tampering | `--observe` | medium | mitigate | Case opened read-only; `acceptance_observe_only_flag` | closed |
| T-07-19 | Repudiation | regression vs oracle labelling | medium | mitigate | Configure-time check of `reference_digest`; `class=regression` output | closed |
| T-07-20 | Tampering | core mutant | medium | mitigate | Configure fails unless anchor unique; mutant library test-only, not installed | closed |
| T-07-21 | DoS | stall report | medium | mitigate | 4096-record / 64-write rings, 65536-byte cap, truncation marker | closed |
| T-07-22 | Repudiation | cross-OS evidence | medium | mitigate | Exact-head byte-identical observation lines (07-11-SUMMARY) — process evidence | closed |
| T-07-23 | DoS | `--input-script` | medium | mitigate | Bounded read, parse-first, 8 MiB ROM cap in `script_smoke` | closed |
| T-07-24 | Elevation of privilege | diagnostic activation | medium | mitigate | `verify_script_smoke_surface.cmake` + selftest, exact-argc dispatch | closed |
| T-07-25 | Tampering | SDL timestamp conversion | low | mitigate | Overflow-guarded conversion in `src/player/input.c` | closed |
| T-07-26 | Repudiation | PR-only player gate | medium | mitigate | `required-native` with `if: always()` + `check-player-result.sh` self-test | closed |
| T-07-27 | Tampering | silent re-bless | high | mitigate | No update mode; print-candidate to temp only; frozen body digest; `dmg_baseline_changes_unrecorded` | closed |
| T-07-28 | Tampering | CRLF and ordering | medium | mitigate | `eol=lf`, CR stripping, unsorted/duplicate/malformed self-tests | closed |
| T-07-29 | Repudiation | skipped frozen tests | high | mitigate | JUnit `junit-missing/skipped/failed` checks in three native jobs and player job | closed |
| T-07-30 | Info disclosure | benchmark metadata | low | mitigate | Ledger records hardware class only; privacy scan clean at audit | closed |
| T-07-31 | Info disclosure | docs, PR body, ledgers | medium | mitigate | Privacy scan of 98 changed files: 0 matches | closed |
| T-07-32 | Repudiation | completion claim | high | mitigate | Exact-head run ids recorded (07-16-SUMMARY); PR unmerged until verified | closed |
| T-07-33 | Repudiation | overclaiming scope | medium | mitigate | Limits stated in `docs/game-acceptance.md`, `docs/support/unreleased.md` | closed |
| T-07-34 | Tampering | case-file rejection regression | medium | mitigate | Seven negatives with exit 2, reason regex, `GBB_FORBID_REGEX`; boundary matrix | closed |
| T-07-35 | Repudiation | suite denominator | high | mitigate | Undeclared/missing exclusion tests; no `SKIP_RETURN_CODE` | closed |
| T-07-36 | Repudiation | expected-failure masking | medium | mitigate | `acceptance_unexpected_pass` | closed |
| T-07-37 | Repudiation | PCM threshold erosion | medium | mitigate | Calibration rule and values beside thresholds; 07-11 table | closed |
| T-07-38 | Tampering | blessing a mixed state | high | mitigate | `frozen_revision` ancestor of HEAD; no `src/` diff since; baseline commit touches no `src/` | closed |
| T-07-39 | Info disclosure | install-tree ROM | medium | mitigate | `libbet_not_installed` + planted-payload selftest | closed |
| T-07-40 | DoS | stepper and driver loops | medium | mitigate | Iteration guard, STOPPED reporting, no host clock | closed |
| T-07-41 | Tampering | Mooneye path regression | medium | mitigate | `fixtures/mooneye/` unchanged; six `mooneye_*` tests inventoried | closed |
| T-07-42 | Repudiation | gate that cannot fail | high | mitigate | N1/N2 raw + xfail, drop-start, core mutant controls | closed |
| T-07-43 | Info disclosure | player package | medium | mitigate | `--scan-dir` on extracted package | closed |
| T-07-44 | Repudiation | comparator category never fires | medium | mitigate | 20 `dmg_baseline_*` self-tests inventoried | closed |
| T-07-45 | Info disclosure | telemetry / network creep | medium | mitigate | Surface check forbids socket/connect/curl/http(s) | closed |
| T-07-46 | Repudiation | closure vs pinned source | high | mitigate | `--derive-closure` before `make`; required CI checks closure constant | closed |
| T-07-47 | Tampering | joypad path change | medium | mitigate | D-028 (no fix needed); unique anchor enforced at configure | closed |
| T-07-48 | Repudiation | investigation outcome | low | mitigate | D-028, GB-GAME-002 | closed |
| T-07-SC | Tampering | npm/pip/cargo installs | high | mitigate | Only opt-in `reproduce-libbet.sh` installs, behind fail-closed provenance gate; required CI installs nothing | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

Audit notes (non-blocking):
- T-07-03, T-07-11, T-07-22 and T-07-30 rest on one-time process evidence, not a code control.
- T-07-14: the GitHub release-asset digest cross-check is skipped when the API returns no digest (it returned none); the pinned SHA-256 is still enforced before extraction.
- T-07-28: CRLF is tolerated by stripping, not rejected; no CRLF-specific negative test exists.

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-10 | 49 | 49 | 0 | gsd-security-auditor (ASVS L1, block_on high) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-10
