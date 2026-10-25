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
total: 13
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

## Scoped re-review 2026-10-12 (host-guide contract check, `09-REVIEW.md`)

The full-phase review above is at commit 486c7bd. The current `09-REVIEW.md` reviews only `cmake/VerifyDocContract.cmake` and its CTest wiring.

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| R2 WR-01 | warning | fixed | Declaring files are comment-stripped (C `/*` and `//` in .h/.c files, whichever comes first; `#` elsewhere). `doc_contract_comment_only_selftest` fails on the old script and passes on the new one |
| R2 WR-02 | warning | fixed | Empty or whitespace-only phrases fail with `doc-contract-empty-phrase`; `doc_contract_empty_phrase_selftest` fails on the old script |
| R2 WR-03 | warning | fixed | HTML comments are removed from the guide, and `GBB_SCOPE_START` confines phrases to the RTC paragraph (it ends at the next blank line). `doc_contract_scope_selftest` fails on the old script; deleting "once per open" from the real paragraph fails the live check |
| R2 WR-04 | warning | skipped | Struct fields such as `reason` and `consumed_half_dots` are not `gbb_`-prefixed and are outside this RTC contract; the installed C and C++ consumers and `examples/relocated-c` compile against them, so a rename fails the build |
| R2 WR-05 | warning | fixed | Four new controls (comment-only, word boundary, empty phrase, scope), each shown to fail on the previous script. Multiple declaring files are exercised by the live test (`GBB_ROM_PATH` comes from the example CMakeLists) |
| R2 IN-01 | info | fixed | Phrases are whitespace-collapsed the same way as the guide, and UTF-8 no-break spaces collapse too |
| R2 IN-02 | info | fixed | Identifier extraction requires a non-identifier character before `gbb_`/`GBB_`; `doc_contract_word_boundary_selftest` forbids `gbb_ghost_tail` from `libgbb_ghost_tail` |
| R2 IN-03 | info | fixed | The pass pattern is `phrases=12[^0-9]` |
