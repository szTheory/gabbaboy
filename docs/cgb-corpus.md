# CGB software-model corpus inventory

<!-- cgb-corpus-inventory-begin -->
The executable roster is [cgb-corpus-inventory.json](../tests/external/cgb-corpus-inventory.json)
(schema `gabbaboy-cgb-corpus-inventory-v1`). The validator
`tests/scripts/verify-cgb-corpus-inventory.py` checks pinned source membership,
existing fixture manifests and bytes, the frozen case roster, and the MagenTests
admission statement. Its selection-only mode permits outputs that have been
scratch-built but have not passed per-output admission.

| Pinned source family | Source candidates | Output records | Required model cases |
|---|---:|---:|---:|
| Mooneye CGB header candidates | 83 | 9 selected outputs | 9 |
| SameSuite APU and existing DMA | 74 (70 APU + 4 DMA) | 74 | 74 |
| AGE existing plus mode-3 | 19 (13 existing + 6 new) | 19 | 19 |
| MagenTests | 5 source paths | 7 admitted outputs | 5 CGB cases |
| **Total** | **181** | **109** | **107** |

The counts describe different objects. All 109 selected output records are
admitted with pinned manifest bytes and provenance; three admitted Magen MBC
outputs remain outside the CGB case set, and one Magen PPU output supplies
separate native and compatibility-mode cases. All nine selected Mooneye CGB
outputs are admitted, reproducible and bound to individual tests. The 107
required case identities remain fixed and now all have terminal execution
receipts. The six AGE mode-3 image cases have exact expected-failure software
model results against independent source images; their author pass targets
remain separate from those observed results.

The Mooneye roster contains 59 source headers with CGB in a pass list, 26 with
CGB in a fail list, and two in both. Its nine required identities include the
unsuffixed `acceptance/instr/daa.s`, `acceptance/timer/div_write.s`, and
`acceptance/timer/tim00.s`, plus four previously admitted cases,
`acceptance/timer/tim00_div_trigger.s`, and
`misc/ppu/vblank_stat_intr-C.s`. All nine pass author assertions in their pinned
headers. Their local CGB-CPU-E compatibility-mode receipts contain six guest
passes and three exact expected failures (`boot_hwio-C`, `unused_hwio-C`, and
`vblank_stat_intr-C`). The software evaluator reports each as `xfail` only for
its pinned callback, result PC, and failure registers; none is counted as a
guest pass. Source applicability comes from the pinned header; a CGB pass
statement does not create a CGB-E-only hardware claim.

All 70 APU assembly sources at the pinned SameSuite commit remain selected,
including revision-suffixed names. Its [pinned APU README](https://github.com/LIJI32/SameSuite/blob/f15645fb049a47ea235f6d2c9a033e72d8087901/apu/README.md)
says `CPU-CGB-E – passes all tests`; the source roster preserves that
applicability quote for each APU identity. Each ROM's encoded result remains
author evidence, while SameBoy comparisons remain differential evidence. The
four existing DMA outputs are included separately.

Under the bounded CGB-CPU-E native, normal-speed software model, the 70
terminal receipts comprise eight observed guest passes and 62 exact expected
failures across 4,784 result assertions. Every source author expectation
remains `pass`; the 62 evaluator xfails are not guest passes.

AGE has 19 admitted outputs: 13 existing row-oracle cases and six mode-3
source/reference image pairs. Four new targets are normal-speed
native/compatibility cases and two are separate double-speed siblings. Each
image pair records its own source, PNG, rights, build provenance, and output
digest. Each image case was executed at its pinned model, mode, speed, ROM, and
reference identity, and all six produced nonzero exact RGB555 mismatch
signatures. These are expected failures for the current software model; the
pinned upstream author expectation remains pass for every case.

MagenTests contributes five CGB-CPU-E model/mode cases from already admitted
outputs. The HBlank VRAM DMA output is the seventh admitted ROM in its manifest
and remains one selected native CGB case. The three MBC outputs stay outside
this CGB corpus.

Source identity, generated output, admission, required case, execution, and
assertion rows are separate fields. Each case keeps its author expectation
separate from the current evaluator disposition. An absent or unadmitted byte
is never represented as an executed expected failure. The `--complete`
validator mode requires admitted hashed outputs, unique exact CTest bindings,
terminal case results, and nonempty assertion rows.

Optional local acid2 and Mealybug records remain `not-run:rights-gate-G1`.
Mealybug CGB-C/D images also remain `unsupported-model` because they have no
CGB-E expectation. Both constraints apply simultaneously. Their bytes are
absent, no outreach is authorized, and neither record enters the denominator.

These records qualify repository software-model observations and source
provenance. They do not qualify physical CGB-E hardware, analog audio/color,
or general game compatibility. The inventory is not a fixture manifest and
does not admit pending bytes.

## Private execution receipt

`tests/scripts/verify-cgb-corpus-report.py` consumes bounded existing runner/CTest
observations and writes a private, versioned receipt; it does not add a C-core
JSON interface. Its DAA tracer binds the checkout revision, covered source and
fixture digests, runner bytes, CMake configuration, Mooneye manifest and ROM,
model profile, compatibility mode, speed, boot policy, callback PCs and tick
budget. The receipt's public paths are repository-relative. A failed or partial
run replaces any earlier receipt with an `incomplete` record. The one-case
tracer is a contract check, not a claim that the full 107-case receipt has
completed; suite and assertion denominators remain separate, and matched
expected failures never count as observed guest passes.
<!-- cgb-corpus-inventory-end -->
