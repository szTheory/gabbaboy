# GabbaBoy unreleased support-ledger entries

The chronological Phase 8–14 support notes have been reconciled into the
[versioned v0.2.0 support ledger](v0.2.0.md). This file carries no additional
release qualification. Add future pending evidence here only with its source,
model, execution mode, rights, result disposition, and intended versioned-ledger
destination; do not use it as evidence for a tagged release.

The v0.2.0 ledger records the current CGB software-model corpus receipt and the
explicit absence of CGB game-level evidence. Physical CGB-E remains
UNKNOWN/POLICY. The separate DMG Libbet acceptance and prior mapper, save, RTC,
CGB profile, colour, speed, HDMA, and digital APU scope are summarized with
their boundaries in that ledger.

GDMA and HBlank DMA remain implemented under the selected bootless CGB-CPU-E
software model, with the cancellation, timing and physical-evidence limits in
the versioned ledger and [CGB profile guide](../cgb-profile.md).

Optional Mealybug CGB-C cases are `not-run:rights-gate-G1`, informational only, and outside the CGB-E denominator. Physical CGB-E remains UNKNOWN/POLICY.

## Host mode (HOST-01..03, pending v0.3.0)

Host mode is the headless `gabbaboy-runner --rom ... --save-dir ...` process contract: an exact-size raw
`{stem}.sav` imported at start and atomically published on a bounded cadence and at SIGTERM, SIGINT or
SIGHUP, with the published exit table, the published save-format ids and `--print-save-format`. The
runner records no wall-clock time and is POSIX-only; Windows is refused.

- Source: this repository at the Phase 18 head; the fixtures are original generated ROMs.
- Model: DMG-CPU-B and CGB-CPU-E software profiles. No physical-hardware, game-compatibility or
  emulator-interoperability claim is made, and no power-loss durability is promised.
- Execution mode: the headless runner (`gabbaboy-runner`).
- Rights: original generated fixtures and the committed contract JSON; nothing third-party is stored.
- Result disposition (CTest names): `host_continuation`, `host_cadence_retry`, `host_signal_term`,
  `host_exit_table_codes`, `save_format_files`, `save_format_completeness`, `save_format_freeze`,
  `host_contract_json`, `host_contract_docs` and `installed_host_smoke`.
- Intended versioned-ledger destination v0.3.0, written at release.

## Player state slots (PLAY-01, pending v0.3.0)

The SDL player keeps nine numbered machine-state slots per game and model. A load is all-or-nothing, backs
up the in-game battery save and the replaced state, and uses `gbb_get_input_clock` to re-anchor input.

- Source: this repository at the Phase 18 head; the slot tests use original generated ROMs.
- Model: DMG-CPU-B and CGB-CPU-E software profiles; a slot is bound to the exact GabbaBoy release that
  saved it. No interoperability claim is made.
- Execution mode: the SDL player (macOS) and its SDL-free slot engine tests.
- Rights: original generated fixtures; no third-party or commercial image.
- Result disposition (CTest names): `slot_message_table`, `slot_reanchor_plan` and `input_clock_after_load`.
- Intended versioned-ledger destination v0.3.0, written at release.
