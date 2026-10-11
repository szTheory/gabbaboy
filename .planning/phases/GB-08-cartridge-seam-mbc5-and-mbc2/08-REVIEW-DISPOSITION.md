---
phase: 08
review: 08-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Installed-tree scan silently skips symlinks"
  - id: WR-02
    severity: warning
    disposition: deferred
    title: "Player battery classification duplicates the core type table with no drift guard"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "Scan digest comparison is case-sensitive"
  - id: IN-02
    severity: info
    disposition: skipped
    title: "Unused table columns and duplicated status block"
  - id: IN-03
    severity: info
    disposition: skipped
    title: "Banking guest's ninth-bit write-order checks are inert on the 64 KiB image"
open: 0
total: 5
---
# Phase 08: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 1620c99: file links are followed and their targets scanned; new `mooneye_mbc_not_installed_link_selftest` fails on the old script's bypass; player package scan still clean (files=14) |
| WR-02 | warning | deferred | Phase 9 (CART-06) replaces the $06/$1B/$1E unsupported list when MBC2/MBC5 persistence lands; add the every-type-byte classification test there. Today's list matches every battery type the core admits |
| IN-01 | info | fixed | 1620c99: manifest digests lowercased before comparison |
| IN-02 | info | skipped | Readability only; no behaviour change, and the core table columns are frozen by the Phase 8 seam decisions |
| IN-03 | info | skipped | Already stated in docs/mbc2-mbc5-evidence.md: the ninth-bit proof is `mbc5_bank_1ff` on the inflated image (D-062), not the 64 KiB write-order checks |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
