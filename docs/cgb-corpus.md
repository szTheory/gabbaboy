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
required case identities remain fixed. A fresh exact-membership CTest receipt
establishes runtime completion; the static inventory does not rewrite an
unobserved source-row result to make a summary pass. The six AGE mode-3 image cases have exact expected-failure software
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

<!-- cgb-corpus-evidence-begin -->
For the bounded CGB-CPU-E native, normal-speed software model, all 70 source
author expectations remain `pass`. Evaluator outcomes are independently
recorded and a matched xfail is never a guest pass. Read current completed-case,
observed-pass, matched-xfail, assertion, and image-pixel totals from the current
complete receipt (`cgb-corpus-receipt.json`); do not copy those changing observations into
this static contract. The pinned source, fixture, and result ancestry remain
navigable through the inventory, APU disposition records, report schema, and
build stamp. A fresh receipt is created by `--begin-run`, one full CTest stream,
and `--from-ctest`; it is not a fixture-inventory completion flag. SameBoy
agreement is differential evidence; author-encoded targets
remain the expected result. This is software-model evidence only. It does not
qualify physical CGB-E, analog audio/color, or general game compatibility. See
[`cgb-corpus-inventory.json`](../tests/external/cgb-corpus-inventory.json),
[`cgb-apu-dispositions.json`](../tests/external/cgb-apu-dispositions.json), and
`tests/scripts/verify-cgb-corpus-report.py`.
<!-- cgb-corpus-evidence-end -->

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
is never represented as an executed expected failure. `--selection-only`
validates pinned selection and allows outputs to remain pending admission.
`--bindings` validates that every frozen case points to an admitted, hashed
output and a unique registered CTest test. The command
`python3 -I tests/scripts/verify-cgb-corpus-inventory.py --complete` currently
exits 1 with `complete-case-not-terminal:magentests:bg_oam_priority`, because
the static inventory does not claim an observed result for that row. This
rejection is an intentional negative control; `--complete` keeps its terminal
observation requirement. Runtime completeness comes from `--begin-run`, one
full `ctest --test-dir build -T Test --no-compress-output` stream, and
`--from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json`, plus
the independent required-test inventory check on that run's nonce JUnit file.
The exact CTest and every consumer use the same run nonce. This proves the
fresh exact-107-case execution (plus the aggregate SameSuite APU test) without
changing the static inventory fact.

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
JSON interface. CMake stamps the compiled source/config/toolchain and corpus
inputs. The native lane calls `--begin-run --build-dir build` before one full
`ctest --test-dir build -T Test --no-compress-output` stream. CTest otherwise
limits passing-test output to 1 KiB, so the lane sets
`--test-output-size-passed 16777216`; the receipt parser enforces the same
16 MiB per-test bound. This option is supported since CMake 3.4
([CTest reference](https://cmake.org/cmake/help/v3.25/manual/ctest.1.html)).
Measured APU-suite output was 617,531 bytes for 70 guest records and 4,784
assertion rows, below that bound. The lane then uses
`--from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json` to
consume the local Test.xml and matching nonce-specific JUnit output. The receipt
rejects stale, dirty, missing or changed input identities and missing selected
test names; it does not rerun the guests. Receipt paths are repository-relative,
and a failed or partial run replaces any earlier receipt with an `incomplete`
record.

The native workflow retains only the receipt, build stamp, run metadata, and a
small artifact manifest. A pre-upload check validates their JSON schemas,
relative paths, and contents. Raw Test.xml and JUnit remain local to the job:
both include host names and absolute build commands, so neither is published.
The receipt preserves their hashes for provenance without copying their raw
host-specific contents into the artifact.

The receipt keeps attempted, completed, actual guest-pass, matched-xfail and
assertion counts separate. Every required suite and source-behavior cohort has
passing evidence. The six AGE image comparisons retain their individual
software-model outcomes and pixel signatures in the receipt. The DAA one-case
tracer remains a separate contract test; matched expected failures never count
as observed guest passes.

The recurring native workflow retains the build stamp and privacy-checked JSON
receipt evidence; its parser and required-test inventory check still consume
the same local full-stream Test.xml and nonce-named JUnit report. Sanitizer CI
continues to verify the full required CTest inventory.
The pinned fixture workflow rebuilds all nine Mooneye CGB ROMs and all AGE and
SameSuite corpus outputs, including the six AGE reference PNG digests. These
workflow declarations are offline contract checks; they do not imply that a
hosted workflow ran on this revision. Local configure/build and corpus timings
and the measured reproduction elapsed times are recorded in the plan summary.

## Latest local complete receipt

The fresh nonce-bound producer run from source revision
`36be4dc093566b242d61c4d6afc0d024f2ff2059` completed CTest `108/108`: 107
required model cases plus the aggregate SameSuite APU stream. Across the
required cases, all 107 were attempted and completed: 25 actual guest passes,
82 actual guest failures matched to expected-failure dispositions, zero
excluded, and zero not run. The 4,959 assertion rows contain 2,845 passes and
2,114 failures. The 82 matched xfails remain guest failures. This receipt says
nothing about physical hardware or CGB game compatibility.

| Suite | Required cases | Guest passes | Matched xfails | Assertion rows | Assertion passes | Assertion failures |
|---|---:|---:|---:|---:|---:|---:|
| AGE | 19 | 2 | 17 | 148 | 43 | 105 |
| MagenTests | 5 | 5 | 0 | 5 | 5 | 0 |
| Mooneye CGB | 9 | 6 | 3 | 9 | 6 | 3 |
| SameSuite APU and DMA | 74 | 12 | 62 | 4,797 | 2,791 | 2,006 |
| **Total required cases** | **107** | **25** | **82** | **4,959** | **2,845** | **2,114** |

The AGE image subset compared 138,240 pixels and recorded 18,208 mismatches.
The complete private receipt has run id
`bccb54cf2e23f758299550a47e54828d65b1e7c28f2862ad2305fa880c943f59` and
SHA-256 `78e8a98f72be7431029dd8a7f05c31d7b3c198253b6506480e8570e76742c3b0`.
These counts are local software-model evidence; the receipt does not imply a
hosted workflow ran.
<!-- cgb-corpus-inventory-end -->
