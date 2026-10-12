---
phase: 09
review: 09-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Player variant message names only MBC1 multicart wiring"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "No-host-clock proof can pass vacuously"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "--clock-unix accepts leading whitespace and '+'"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Battery block accepts any latch-edge byte"
  - id: IN-03
    severity: info
    disposition: skipped
    title: "Player hard-codes the live DH offset in the RTC block"
open: 0
total: 5
---
# Phase 09: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | fc85d8c: `GBB_UNSUPPORTED_CARTRIDGE_VARIANT` now reads "cartridge variant (MBC1 multicart wiring or MBC30)"; no test pinned the old text; player gate green |
| WR-02 | warning | fixed | 8896725: the comment stripper honours whichever of `/*` and `//` comes first, and an empty symbol listing fails with `no-host-clock-symbols-empty`. New `no_host_clock_comment_selftest` passes on the old script (`pass files=1`) and fails on the new one; live `no_host_clock` still reports `files=2 symbols=11 tool=nm` |
| IN-01 | info | fixed | 19deb6b: only an optional `-` followed by digits is accepted; `clock_flag_scope` gains leading-space, plus-sign and bare-minus rejections |
| IN-02 | info | fixed | 2863aae: the public header now states that the latch-edge byte is the last byte written to the latch register, so any value is valid. Rejecting values would refuse states the core itself produces |
| IN-03 | info | skipped | Readability only. Adding a public offset constant would grow the API; the v1 block layout is pinned by `rtc_block_*` tests and the player continuation fixture, which would fail on any layout drift |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
