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

The counts describe different objects. The 109 output records include three
admitted Magen MBC outputs outside the CGB case set; one Magen PPU output
supplies separate native and compatibility-mode cases. At this inventory
revision, 33 outputs are admitted and 76 selected outputs remain pending
per-output admission. All nine selected Mooneye CGB outputs are admitted,
reproducible and bound to individual tests. The 107 required case identities
remain fixed; nine Mooneye cases have terminal execution and assertion records,
while other selected cases remain pending.

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

AGE retains its 13 existing outputs and selects six mode-3 source/reference
image pairs. Four are normal-speed native/compatibility targets and two are
separate double-speed siblings. Each new ROM requires its own source, PNG,
build provenance, output digest, and executable predicate before admission.

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
<!-- cgb-corpus-inventory-end -->
