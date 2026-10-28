---
phase: GB-17-native-save-state-core
reviewed: 2026-10-28T00:00:00Z
depth: standard
reviewed_head: e8ea47a
files_reviewed: 62
files_reviewed_list:
  - .github/ci-timeouts.json
  - .github/scripts/release-evidence-lifecycle.sh
  - .github/scripts/verify-release-gates.sh
  - .github/scripts/verify-release-source-proof.py
  - .github/scripts/verify-test-inventory.sh
  - .github/scripts/verify-workflow-policy.py
  - .github/workflows/ci.yml
  - .github/workflows/nightly-asan.yml
  - .github/workflows/release-please.yml
  - .github/workflows/release-rehearsal.yml
  - .github/workflows/release.yml
  - CMakeLists.txt
  - cmake/ExpectedTests.cmake
  - cmake/P12Mutants.cmake
  - cmake/StateVersion.cmake
  - docs/cartridge-and-saves.md
  - docs/release.md
  - docs/state-format.md
  - include/gabbaboy/gabbaboy.h
  - src/core/gabbaboy.c
  - tests/CMakeLists.txt
  - tests/cmake/ci-lanes.cmake
  - tests/cmake/hygiene.cmake
  - tests/cmake/perf.cmake
  - tests/consumers/c/main.c
  - tests/consumers/cpp/main.cpp
  - tests/fuzz_core.c
  - tests/scripts/measure-release-baseline.sh
  - tests/scripts/run-perf-gate.sh
  - tests/scripts/state_boundary.py
  - tests/scripts/test-state-fork-mutant-controls.py
  - tests/scripts/test_hdma_remote_evidence.py
  - tests/scripts/verify-dense-input.py
  - tests/scripts/verify-hdma-lane.py
  - tests/scripts/verify-no-phase-paths.py
  - tests/scripts/verify-perf-gate.py
  - tests/scripts/verify-phase8-closure-contract.py
  - tests/scripts/verify-phase8-player-contract.py
  - tests/scripts/verify-planning-hygiene.py
  - tests/scripts/verify-release-gates.py
  - tests/scripts/verify-release-lifecycle.py
  - tests/scripts/verify-state-contract.py
  - tests/scripts/verify-state-forks.py
  - tests/scripts/verify-state-horizon.py
  - tests/scripts/verify-state-mutants.py
  - tests/scripts/verify-state-pins.py
  - tests/scripts/verify-support-ledger.py
  - tests/scripts/verify-test-budget.py
  - tests/scripts/verify-v02-delivery.py
  - tests/scripts/verify-v02-fuzz.py
  - tests/scripts/verify-v02-performance.py
  - tests/scripts/verify-version-window.py
  - tests/test_cgb_hdma_internal.c
  - tests/test_cgb_profile.c
  - tests/test_cgb_speed_internal.c
  - tests/test_events.c
  - tests/test_state_alloc.c
  - tests/test_state_api.c
  - tests/test_state_codec.c
  - tests/test_state_fork.c
  - tests/test_state_horizon.c
  - tests/test_state_internal.c
findings:
  critical: 5
  warning: 13
  info: 8
  total: 26
status: issues_found
---

# Phase 17: Code Review Report

Three independent `gsd-code-reviewer` passes at standard depth, one per slice, at branch head `e8ea47a` (final source head `6199487`). Finding IDs carry their slice letter: CR-A01 is critical finding 1 of slice A. Each reviewer checked its findings against the source. Slice A reproduced CR-A01..03, WR-A01 and WR-A02 with proof-of-concept builds. Slice B rebuilt the intended purity mutants. Slice C applied its policy-gap edits to scratch copies. The orchestrator independently confirmed CR-B01 (the three generated `state_alloc_mutant_*.c` files are byte-identical) and CR-C01 (`review_approval` never binds the issue URL's owner/repo to this repository).

| Slice | Critical | Warning | Info |
|---|---|---|---|
| A: core state codec and C API | 3 | 5 | 3 |
| B: state checkers and CTest wiring | 1 | 3 | 3 |
| C: release, performance and CI tooling | 1 | 5 | 2 |

## Slice A: Core state codec and C API

**Depth:** standard, with executable proofs. I built the core in the reviewer's scratch directory and ran
proofs of concept for every Critical and the first two Warnings. Nothing in the repository was modified.

### Summary

The codec framing is sound: little-endian explicit encoding, exact-length and CRC ordering, header
identity, overlap checks and the 2^62 horizon guards all behave as documented. I found no endianness,
truncation or short-input read defects in the header path.

The defects are in the semantic validator, which is the code that decides what the machine will accept.
It is wrong in both directions:

- **Too strict (CR-A01, CR-A02):** it refuses states the emulator itself produces during normal play. A user
  hitting "save" gets `GBB_STATE_INVALID_CONTENT`. CR-A01 reproduced on the in-repo fixture `libbet.gb`
  (13 of 2500 sampled instants). CR-A02 reproduced with a 14-instruction CGB program.
- **Too lax (CR-A03, WR-A01, WR-A02):** it accepts hostile or unreachable values. CR-A03 is an
  out-of-bounds write (UBSan-confirmed) reachable from a CRC-repaired state file.

The test suites pass because they only mutate fields one at a time and only save at a handful of
hand-picked instants. Nothing checks "every state the emulator can reach is saveable", and nothing
exercises a relation between two fields (WR-A03, WR-A04).

### Critical Issues

#### CR-A01: Valid mid-frame state is un-saveable because `ppu_objects_stalled` keeps stale bits

**File:** `src/core/gabbaboy.c:4597-4598` (relation), `3247-3250` (`ppu_begin_object_scan`), `2858-2860` (LCD-off path), `3515` (only reset point)

**Issue:** The relation `(ppu_stalled >> selected_count) != 0 -> reject` assumes stalled bits are always
`< ppu_selected_object_count`. The emulator breaks that. `ppu_begin_object_scan()` sets
`ppu_selected_object_count = 0` at every line wrap, and the LCD-off write sets it to 0, but neither
clears `ppu_objects_stalled`. The bits are only cleared in `ppu_begin_transfer()` at dot 80. So:

- During mode 2 of the line after any line that stalled on an object, the live state violates the relation.
- If the LCD is switched off right after such a line, the state stays invalid for as long as the LCD stays
  off.

`gbb_state_size()` and `gbb_save_state()` run `state_validate()` on the live machine and return
`GBB_STATE_INVALID_CONTENT`. A real CGB-compat run of `fixtures/libbet/libbet.gb` was refused at
`ly=72 dot=8 mode=2 stalled=0x2 selcount=0` (13 of 2500 samples).

Reproduction, a DMG ROM with one sprite at OAM `Y=16, X=8` and LCDC=0x93:

```
REFUSED t=7536 ly=8 dot=4  mode=2 stalled=0x1 selcount=0 err=27
REFUSED t=7584 ly=8 dot=28 mode=2 stalled=0x1 selcount=0 err=27
REFUSED t=7632 ly=8 dot=52 mode=2 stalled=0x1 selcount=0 err=27
```

After `write8(FF40, 0x13)` (LCD off) mid-line, `gbb_state_size` returns 27 on every later call, even
after 6400 more half-dots.

`docs/state-format.md:366` ("stalled-object bits cannot exceed the selected count") documents the false
invariant.

**Fix:** Pick one. Either choice changes the golden pins, so regenerate them and record the disposition.

```c
/* option A, no behaviour change: bound by the physical limit, not the transient count */
if (ppu_enqueued > GBB_FRAME_WIDTH + ppu_fine_scroll || ppu_transfer > 12u ||
    ppu_stall > 11u || (ppu_stalled >> GBB_LINE_OBJECT_LIMIT) != 0u) return 0;

/* option B: clear the stale bits where the count is cleared */
static void ppu_begin_object_scan(gbb_instance *m) {
    m->ppu_selected_object_count = 0;
    m->ppu_scan_index = 0;
    m->ppu_objects_stalled = 0;      /* also add to the LCD-off/LCD-on branches */
}
```

Add a regression that saves at every 16 half-dots across several frames of a sprite ROM, and of
`libbet.gb` on both profiles. Then update the doc sentence at `docs/state-format.md:366`.

---

#### CR-A02: Any CGB game that writes a palette high byte with bit 7 set makes the machine un-saveable

**File:** `src/core/gabbaboy.c:4266-4267` (validator), `1995-1999` (`cram_data_write`), `docs/state-format.md:355`

**Issue:** The validator requires every odd-index `bg_cram` / `obj_cram` byte to have bit 7 clear. The core
stores whatever the guest writes (`cram[idx] = value`) and masks bit 15 only when rendering
(`cram_colour(...) & 0x7FFF`, line 3385). Filling palette RAM with `0xFF` (white) is an extremely common
CGB init pattern.

Reproduction, CGB native, LCD off, `BCPS=0x80`, then 64 writes of `0xFF` to `BCPD`:

```
before run: state_size=0
after guest fills BG palette RAM with 0xFF: state_size=27 (27=INVALID_CONTENT)
```

The machine can never be saved again until the palette is rewritten.

**Fix:** The consumer already masks, so accept the byte. Either delete the `(raw & 0x80)` rule for CRAM and
fix the doc line, or mask at write time. The latter changes the CRAM read-back, which the mooneye-cgb and
AGE oracle tests may pin, so check them first. Add a guest-driven test that writes `0xFF` bytes and then
saves and reloads.

```c
/* remove */
if ((STATE_PATH("bg_cram") || STATE_PATH("obj_cram")) && (index & 1u) != 0u)
    return (raw & 0x80u) == 0u;
```

---

#### CR-A03: Accepted state with `dma_active=1, dma_index>=160` causes an out-of-bounds write in the OAM DMA tick

**File:** `src/core/gabbaboy.c:4319` and `4542` (only `dma_index <= 160` is checked), `3764-3769` (`dma_advance_half_dot`)

**Issue:** `dma_index` is validated as `<= GBB_OAM_BYTES` (160), which is legal only when DMA is inactive.
No relation ties it to `dma_active`. `dma_advance_half_dot()` runs `m->oam[m->dma_index] = value` whenever
`dma_active` is set, and only stops on `dma_index == 160`. A CRC-repaired state with `dma_active=1` and
`dma_index=160` is accepted. Reproduction against a DMG instance, mutating the saved body and re-computing
the CRC:

```
dma_active=1,index=160 load -> 0
gabbaboy.c:3766:5: runtime error: index 160 out of bounds for type 'uint8_t[160]'
```

The write lands in the adjacent `frame_working[0..]`. `dma_index` then increments through 255 and wraps,
so it corrupts `frame_working[0..95]` with guest-visible bytes. The result is intra-object UB reachable
from untrusted input, and a violation of the AGENTS.md rule to guard state boundaries. CRC is explicitly
not a MAC, so an attacker recomputes it.

**Fix:** Add the relation, and harden the tick so it can never index out of range.

```c
/* state_validate_relations */
if (dma_active != 0u && dma_index >= GBB_OAM_BYTES) return 0;   /* read dma_active via STATE_RELATION_READ */

/* dma_advance_half_dot */
if (!m->dma_active) return;
if (m->dma_index >= GBB_OAM_BYTES) { m->dma_active = 0; return; }
```

Add a refuse-and-unchanged test for `{dma_active=1, dma_index=160}` and `{dma_active=1, dma_index=255}`.
`tests/test_state_codec.c:482` only tries `dma_index = 161` on its own.

### Warnings

#### WR-A01: `ly` is unvalidated, although `docs/state-format.md:362` says it is 0..153

**File:** `src/core/gabbaboy.c:874` (descriptor, plain U8), `4237-4392` (no `"ly"` rule), `docs/state-format.md:362`

**Issue:** There is no `STATE_PATH("ly")` rule and no relation. The documented domain is `0..153`
(`GBB_LINES_PER_FRAME = 154`). The load of `ly=200` was accepted. `ppu_advance_dot` only wraps on
`ly == 154`, so an accepted `ly>=154` runs vblank for up to 100 extra lines until the uint8 wraps at 256.
It also skips the `ppu_window_line = 0` and frame-completion handling for that wrap. This is not
memory-unsafe: the transfer path is gated by `ly >= 144`. But it admits states the machine cannot produce,
which defeats the documented contract and the canonical-resave closure.

**Fix:**

```c
if (STATE_PATH("ly")) return raw < GBB_LINES_PER_FRAME;
```

Also consider relating `ly >= GBB_FRAME_HEIGHT` to `ppu_mode == 1` and to `ppu_transfer_complete`, and add
a test.

---

#### WR-A02: Active HDMA with `destination_cursor == 0` is accepted, contradicting "active destination spans stay within VRAM"

**File:** `src/core/gabbaboy.c:4616` (`hdma_destination > 0x9FF0u` only), `docs/state-format.md:369`

**Issue:** The field rule allows `0` as the "reset" cursor, and the active-block check has only an upper
bound. `hdma_admit_block` (line 2408) requires `>= 0x8000`, so an active block with a zero cursor is
unreachable. Proof: CGB native, `hdma.mode=2, active=1, blocks=1, source=0xC000, dest=0` loaded OK, and the
next `gbb_run` returned `GBB_STOP_UNSUPPORTED_BUS`. The write itself is guarded at line 2446, so this is
not memory-unsafe. It is accepted-unreachable state that surfaces as a spurious bus fault.

**Fix:**

```c
(hdma_active != 0u && (hdma_destination < 0x8000u || hdma_destination > 0x9FF0u || ...))
```

---

#### WR-A03: The "refused load leaves the target unchanged" helper cannot see heap state, so cartridge RAM mutation is untested

**File:** `tests/test_state_codec.c:215-242` (`test_load_rejects_mutations`), `:244-249`, `:251-268`

**Issue:** `unchanged` is `memcmp(backup, target, sizeof(*target))`, which is the instance struct only.
`cartridge_ram` is a separate heap allocation, and it is the one field the load path writes through a
pointer. The semantic-bounds cases for `cartridge_ram[0]` (MBC2 `0x0F`) and for MBC3/MBC5 mappers therefore
pass even if `state_apply` ever wrote RAM before validation finished. The fuzz target and `test_state_alloc.c`
compare RAM, but only for their own fixed scenarios.

**Fix:** Snapshot and compare `instance->cartridge_ram` (and `rom`) bytes in `test_load_rejects_mutations`
and `test_load_rejects_header_unchanged`. Reuse the `snapshot_capture` pattern from `test_state_alloc.c`.
Add a negative control that makes `state_apply` run before `state_validate_relations`.

---

#### WR-A04: Nothing checks that reachable machine states are saveable, and the state fuzzer is scenario-based rather than byte-level

**File:** `tests/fuzz_core.c` (`gbb_fuzz_state_one_input`, 8 fixed scenarios), `tests/test_state_codec.c`, `tests/test_state_fork.c`

**Issue:** CR-A01 and CR-A02 are failures of `gbb_state_size` on live, emulator-produced state. All the
suites save at hand-chosen instants of ROMs that do not combine sprites, line wraps, LCD toggling and
palette writes. CR-A03 passes the fuzzer because the fuzzer mutates only about 10 chosen fields and never
mutates an arbitrary body offset. Its accepted cases then run only 32 half-dots with no sanitizer
requirement on a wild mutation.

**Fix:** Add two properties:

1. For every ROM in `fixtures/` and both profiles, run in 1-4 KiB chunks and assert `gbb_state_size == GBB_OK`
   at every boundary, then load-and-resave the result. This is about 25 ms per call, which is acceptable.
2. Make the fuzz target pick a random body offset and a random value, re-CRC, and require that if the load is
   accepted the machine survives a few frames under ASan/UBSan and a canonical resave.

---

#### WR-A05: `state_apply` re-implements the decoder instead of calling the validated store path

**File:** `src/core/gabbaboy.c:4694-4740` versus `4127-4171` (`state_store_host_value`, otherwise unused)

**Issue:** Two independent raw-to-host decoders exist. `state_store_host_value` range-checks BOOL, COUNT and
EVENT_KIND. The one that runs in production, `state_apply`, does not (`(int)raw`, `(size_t)raw`, raw cast to
the enum). Safety therefore rests entirely on every field having an exact upstream rule. CR-A03 and WR-A01
show that this is not guaranteed. The two copies can also drift: the tests exercise the unused one, while
production uses the other.

**Fix:** Make `state_apply` call `state_store_host_value`, assert on a `0` return (it cannot happen after
validation), and delete the duplicated switch.

### Info

#### IN-A01: Test-only helpers compile into the production core and trip `-Wall -Wextra`

**File:** `src/core/gabbaboy.c:645` (`STATE_FIELD_TREATMENT`), `1023`, `1045`, `3986`, `4030`, `4127`, `4758`

**Issue:** `cc -Wall -Wextra` reports `-Wunused-const-variable` / `-Wunused-function` for
`STATE_FIELD_TREATMENT`, `state_descriptor_max_total_size`, `state_audio_hpf_history_valid`,
`state_encode_i64`, `state_crc32`, `state_store_host_value` and `state_record_field`. They are referenced
only by tests that `#include` the `.c` file.

**Fix:** Guard them with a `GBB_TEST_STATE_SEAMS` macro that the tests define, or mark them `GBB_UNUSED`
deliberately.

---

#### IN-A02: Save/size error for an invalid *live* state is undocumented

**File:** `include/gabbaboy.h` (state API comment), `docs/state-format.md:388-399` (error table), `docs/cartridge-and-saves.md`

**Issue:** `gbb_state_size` / `gbb_save_state` return `GBB_STATE_INVALID_CONTENT` when the live machine fails
validation (`gabbaboy.c:4841`, `4854`). The error table and the header comment list only
`INVALID_ARGUMENT`, `NO_ROM` and `BUFFER_TOO_SMALL`. Given CR-A01 and CR-A02 this is a user-visible outcome
that hosts need to handle.

**Fix:** Add a row ("live machine violates a state invariant -> `GBB_STATE_INVALID_CONTENT`") to the table
and to the header comment, and say whether a host may retry later.

---

#### IN-A03: The parity-sweep negative control was narrowed, and several flag fields have no canonical-value rule

**File:** `tests/test_cgb_profile.c:~477-495`; `src/core/gabbaboy.c` descriptors 72 (`ppu_window_line_drawn`), 34 (`cpu_stall_half_dots`)

**Issue:**

- `probe_parity` used to prove that the whole 100k-case matrix loop detects a skewed validator
  (`parity_sweep(1, ...)` had to report at least one mismatch). The replacement checks one hand-made
  header. The sweep loop itself is no longer shown to be able to fail.
- `ppu_window_line_drawn` is a uint8 truth flag accepted as any of 0..255, and `cpu_stall_half_dots` is
  accepted when the kind is `NONE`. Both load and resave byte-for-byte, so non-canonical states survive
  indefinitely.

**Fix:** Restore a sweep-level negative control (inject a skewed probe through a function pointer). Constrain
`ppu_window_line_drawn` to `<= 1` and require `cpu_stall_half_dots == 0` when `cpu_stall_kind == NONE`.

---

## Slice B: State checkers and CTest wiring

**Depth:** standard. Diff base `5ca03b394f2a3e0640f69d94e5eda5622753b36c` (merge-base with origin/main).
Nothing in the repository was modified. I ran read-only checks and wrote scratch builds under the session scratchpad only.

### Summary

The checkers are mostly careful. Revisions are 40-hex validated and read with `git show`. Kill criteria in the fork,
horizon, codec and refusal mutant runners require an exact exit code plus intended diagnostic text, and a compile failure,
a timeout or a sanitizer report is refused rather than counted as a kill. `state_boundary.py` reads only git objects, and
its 31 controls are real (each uses a disposable repository).

One negative control does not test what it names: the three `state_purity_mutant_*` CTests build the same mutant, and it
is not any of the three their names claim (CR-B01). Three further findings are weaker controls or wiring gaps (WR-B01 to
WR-B03). I dropped two candidate findings I could not substantiate: the `.CRT$`/`.ARM.attributes` case mismatch in
`is_known_readonly_section` only fails closed, and the `source_digest` `find(...) + 2` arithmetic only matters for
malformed C.

### Critical Issues

#### CR-B01: All three `state_purity_mutant_*` controls build the same CRC-omission mutant, not the allocation, hash or tail-write mutants they name

**File:** `tests/CMakeLists.txt:5472-5490` (the macro is `gbb_state_alloc_mutant`, defined at `:5442`)

**Issue:** `GBB_STATE_SAVE_SUCCESS_ANCHOR` is set to a bracket string that contains a `;`:

```
state_put_u32(header + 60u, crc);
    return GBB_OK;
```

The three calls pass it unquoted: `gbb_state_alloc_mutant(allocation_in_save ${GBB_STATE_SAVE_SUCCESS_ANCHOR} [=[...]=])`.
CMake splits the unquoted expansion on `;`. The function therefore receives `anchor = "state_put_u32(header + 60u, crc)"`
and `replacement = "\n    return GBB_OK"`. The real replacement text is the fourth argument and is silently ignored,
because the function declares only three parameters. The anchor still occurs exactly once, so the `FATAL_ERROR` guard does
not fire.

I verified this on the generated files. `git show HEAD:src/core/gabbaboy.c | diff - build/tests/state_alloc_mutant_{allocation_in_save,hash_in_save,save_overwrites_tail}.c`
gives the identical hunk for all three:

```
4880c4880,4881
<     state_put_u32(header + 60u, crc);
---
>
>     return GBB_OK;
```

That removes the CRC write. There is no `malloc`, no `state_sha256` call and no `out_bytes[total_size]` write in any of them.
Running `build/tests/test_state_alloc_mutant_*` `state_purity` prints `state_purity failure: operation=load_success
result_or_snapshot` for all three, because a save without a CRC no longer loads. The CTest only requires exit code 1 and
the regex `state_purity failure`, so it passes. The `_control` variants pass too, so nothing looks wrong.

The result is that "save allocates", "save hashes the ROM" and "save writes past the buffer" have no effective negative
control in `state_purity`. AGENTS.md requires every deliverable to have an automated check with a negative control.

I rebuilt the intended mutants in scratch, using the same test source and the same mutant text the CMake file intended.
They are killable, and the probe reports the intended diagnostic:

- `operation=save_success heap_calls=2 request_bytes=1 largest=1 hashes=0`
- `operation=save_success heap_calls=0 ... hashes=1`
- `state_purity failure: save tail modified`

So the probe is fine and only the wiring is broken.

**Fix:**
```cmake
gbb_state_alloc_mutant(allocation_in_save "${GBB_STATE_SAVE_SUCCESS_ANCHOR}" [=[...]=])
gbb_state_alloc_mutant(hash_in_save       "${GBB_STATE_SAVE_SUCCESS_ANCHOR}" [=[...]=])
gbb_state_alloc_mutant(save_overwrites_tail "${GBB_STATE_SAVE_SUCCESS_ANCHOR}" [=[...]=])

function(gbb_state_alloc_mutant name anchor replacement failing_regex)
  if(NOT ARGC EQUAL 4)
    message(FATAL_ERROR "State allocation mutant ${name}: expected 4 arguments, got ${ARGC}")
  endif()
  ...
  "-DGBB_EXPECT_REGEX=${failing_regex}"   # "heap_calls=[1-9]", "hashes=[1-9]", "save tail modified"
```
Use `heap_calls=[1-9]`, `hashes=[1-9]` and `save tail modified` as the three regexes, so a mutant that dies for another
reason (such as the missing CRC) cannot satisfy the control.

### Warnings

#### WR-B01: `state_boundary_controls` spawns about 1,050 git processes, which is above the GB-CI-012 limit on Windows

**File:** `tests/CMakeLists.txt:5548-5555` (TIMEOUT 60); the work is in `tests/scripts/state_boundary.py:161-286`

**Issue:** `boundary_self_test` calls `run_boundary` 32 times (31 controls plus the real run). Each call runs about 30 to 45
separate `git` subprocesses: one `git show` per plan and summary, one `merge-base` per summary, `ls-tree`, `rev-parse` per
historic receipt, and so on. Each fixture `commit()` adds `add -A`, `commit` and `rev-parse`.

I counted the spawns by wrapping `subprocess.run` around the real self-test: **1048 spawns, 12.4 s** on an idle Apple-silicon
host. GB-CI-012 records that 1,398 spawns went from 30.1 s on macOS to 115.7 s on hosted Windows, a factor of about 3.8.
The same factor puts this test at roughly 47 s against its 60 s TIMEOUT on `native-windows-x64`, which is 78% and above the
75% line the lesson sets. This test is not skipped on Windows (`ExpectedTests.cmake` only drops the lifecycle pair).
Fixture checkout, antivirus and `git add -A` on the Windows runner make it worse.

**Fix:** Read each rev's facts through one `git cat-file --batch` process (as `e5064c3` did for the support ledger), or
resolve `git ls-tree -r <rev>` once and fetch all needed blobs in one batch. That drops `run_boundary` to a handful of
spawns. Replace the per-summary `merge-base --is-ancestor` loop with a single `git rev-list <rev>` set lookup. Keep the
TIMEOUT.

#### WR-B02: Seven horizon mutants pass the "intended discrepancy was reported" check without that check being able to fail

**File:** `tests/scripts/verify-state-horizon.py:360-376` (and the `MUTANTS` table at `:60-228`)

**Issue:** `check_semantic_rejection` requires `mutant.expected_failure in output` after confirming every
`mutant.witnesses` string is present. For `cpu-stall`, `hdma-tick`, `irq`, `halt`, `instruction`,
`speed-switch-reservation` and `hdma-block-reservation`, the witness string is
`"# horizon witness: horizon discrepancy: X"` and the expected failure is `"horizon discrepancy: X"`, a substring of the
witness. `tests/test_state_horizon.c:98-103` (`branch_no_progress`) prints that witness line unconditionally, before the
code under test runs:

```c
printf("# horizon witness: %s\n", reason);
const gbb_run_result result = gbb_run(machine, budget, NULL, 0u);
```

So the "intended discrepancy" check is satisfied on every run of those seven cases. A mutant counts as killed whenever the
case exits 1 and prints `not ok 1 - <case>` after the witness, whichever assertion fails or why. The negative controls in
`self_test_helpers` only exercise `MUTANTS[0]` (`stop-wait`), whose witness differs from its expected failure, so the
tautology is not covered. The same is true of `execute(..., self_test=True)`, which builds only the first mutant.

**Fix:** Make the discrepancy text something that only the failure path prints. For example, have `fail_case` emit
`# horizon failure: <reason>` and have the checker require that prefix (`"# horizon failure: " + mutant.expected_failure`).
Alternatively change the witness text to `# horizon witness: <name>` and keep `horizon discrepancy: ...` as failure-only.
Add a self-test control that feeds `check_semantic_rejection` a witness-only transcript for a branch mutant with a
different failing assertion and expects a rejection.

#### WR-B03: The new `perf_advisory_*` CTests have no parsed minimum, and a Windows run reports "pass controls=1" for a fully skipped test

**File:** `tests/cmake/perf.cmake:59-70, 118-121`; `tests/scripts/verify-v02-performance.py:1256-1273`

**Issue:** `gbb_add_perf_receipt_test` passes only `GBB_EXPECT_REGEX="advisory ... self-test pass controls=[0-9]+"`. It sets
no `GBB_EXPECT_MIN_KEY`, unlike every other control test in this file and the "controls are a parsed minimum" convention
stated in the comment above it. `controls=0` or any number satisfies the regex.

Both underlying unittest cases carry `@unittest.skipIf(os.name == "nt", ...)` (`verify-v02-performance.py:879` and `:907`).
On Windows, `self_test(test_name, label)` runs that single skipped test. `testsRun` is 1 and `wasSuccessful()` is true for
a skip. `controls = max(1, testsRun - 1)` is forced to 1, `positive_successes` is 1, and the script prints
`advisory pipeline self-test pass controls=1` and exits 0. CTest therefore records a pass for an advisory pipeline that
never ran. The explicit skip is documented in GB-CI-011, but the `max(1, ...)` clamp turns it into a positive claim.

**Fix:** Count `result.testsRun - len(result.skipped) - len(result.errors)` as executed, and when a named test was skipped
print `... self-test skipped` and return a dedicated code. Register the CTests with `SKIP_RETURN_CODE`, or do not register
them under `WIN32`, as the lifecycle pair is. Drop the `max(1, ...)` clamp. Add `GBB_EXPECT_MIN_KEY=controls` with a minimum
of 1 (or the real count) to `gbb_add_perf_receipt_test`.

### Info

#### IN-B01: The installed-tracer step never re-checks the library or proof-executable hashes it records

**File:** `tests/scripts/verify-state-contract.py:1113-1129`, receipt written at `:1316-1330`

**Issue:** `run_precodec` writes `library_sha256` and `proof_executable_sha256` into `state-precodec-proof.json`.
`run_tracer` only compares `source_commit`, the three source hashes and `negative_controls`. It never hashes the library or
the `test_state_api` it is about to install and run. The error text says the receipt "does not bind the installed tracer
revision", but a library rebuilt after the receipt was written (for example from a header or `src/core/*.h` edit) is
accepted. Fixture ordering (`FIXTURES_REQUIRED gbb_state_precodec_receipt`) hides this under CTest. A manual `--tracer`
run against a rebuilt tree does not.

**Fix:** In `run_tracer`, after `resolve_cmake_artifact`, compare `sha256_file(library)` with `receipt["library_sha256"]`
and `sha256_file(api)` with `receipt["proof_executable_sha256"]`.

#### IN-B02: `state_fuzz_controls` does not compare the public header against the revision, though the probes build from it

**File:** `tests/scripts/verify-v02-fuzz.py:45-63` (`SOURCE_FILES`), used by `state_fuzz_controls` (~`:560`)

**Issue:** `source_manifest(revision, compare_worktree=True)` covers `src/core/gabbaboy.c`, `tests/fuzz_core.c`,
`tests/test_state_codec.c`, CMake files and the workflow, but not `include/gabbaboy/gabbaboy.h`. `struct gbb_instance` is
parsed from that header elsewhere (`verify-state-contract.py:162`). `test_state_fuzz` and the observer mutant link the
working-tree header. With HEAD equal to the configured revision, an uncommitted header edit passes the "inputs equal the
immutable revision" gate. The sibling checkers `state_purity` and `state_field_census` do check the header.

**Fix:** Add `include/gabbaboy/gabbaboy.h` (and `src/core/gabbaboy_test.h` if the probes include it) to `SOURCE_FILES`.

#### IN-B03: The `v02_fuzz_controls` self-test prints hand-maintained constants as its control counts

**File:** `tests/scripts/verify-v02-fuzz.py:2198-2200`; wiring `tests/CMakeLists.txt:1506-1508`

**Issue:** The line `positive_controls=7 negative_controls={22 + 14 + 5 + 3 + 3 + 3} rejected_mutations={10 + 14 + 3 + 3}`
is arithmetic on literals, not counts taken from the executed suite. The CTest regex only demands `[1-9][0-9]*` and sets no
minimum. Deleting a unit test, or one that quietly skips, changes nothing in the evidence line. AGENTS.md says counters
must not serve as evidence, and this one cannot move with the suite. The pattern predates this phase, but this phase
extended it with `+ 3 + 3`.

**Fix:** Derive the numbers from `result.testsRun`, `result.skipped` and per-test tags (or drop the figures). Then either
pin a parsed minimum in the CMake registration, as the other control tests do, or print only `self-test=pass`.

---

_Reviewed: 2026-10-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

## Slice C: Release, performance and CI tooling

**Reviewed:** 2026-10-28
**Depth:** standard
**Status:** issues_found

### Summary

Scope was the release, performance and CI tooling in the diff `5ca03b3..HEAD`. I read the lifecycle script, the source-proof selection, the release-gates gate (both modes), the perf-gate driver, the planning-hygiene, test-budget and Phase 8 changes, the version-window checker and all five workflow diffs. For every claimed policy rule I ran mutations against a scratch copy of the repository (nothing in the repository was modified) and recorded which dangerous edits `verify-workflow-policy.py --check` still accepts.

No untrusted-PR-content-with-write-token path was found. There is no `pull_request_target` or `workflow_run` trigger. The privileged jobs (`attach-evidence`, `publish-qualified-release`, `report-red`, `version-window`) check out only `${{ github.sha }}`, the trusted revision, or hold read-only tokens. Event fields reach shell only through `env:`. The nightly gate, rehearsal-run selection and source-proof code are sound as written (details below).

Phase 16 closures, checked against current source:

| Finding | Verdict |
|---|---|
| Phase 16 WR-01 (unauthenticated rehearsal artifact) | Closed. `select_performance_run` and `select_performance_artifact` bind workflow path, event, success, branch, repository, fork status, head tree from git objects, and run id plus attempt plus artifact origin. A refusal falls back to measuring. |
| Phase 16 WR-02 (mutable Phase 8 tag) | Closed. `EXPECTED_BOUNDARY` is pinned, the tag peels to `96d5eec`, and the retarget controls are real. |
| Phase 16 WR-03 (SHA256SUMS duplicates) | Closed. The strict regex parse and duplicate rejection are in place. |
| Phase 16 WR-04 (new allowlist rows) | Half closed. See WR-C04 below. |
| Phase 16 WR-05 (plan-cap names and phase count) | Closed for the conventional names. |
| Phase 16 IN-01 (retry order) | Reordered, but the new check is weaker than the docs say. See IN-C01 below. |
| Phase 16 IN-02 (wildcard app id) | Closed. |
| Phase 16 IN-03 (`report-red` timeout) | Closed, but it left a release-head blocker. See WR-C03 below. |
| Phase 16 IN-04 (per-repeat lines, HDMA anchors) | Closed. |

One finding is a control that 17-SECURITY.md records as `closed` (T-17-27) and is worse than the stated residual. The rest are policy-checker blind spots, a release-process trap, and a half-closed Phase 16 finding.

### Critical Issues

#### CR-C01: The OWNER approval of an Ir exception can be forged from committed files, and the "fails closed on hosted runs" claim is not enforced

**File:** `tests/scripts/verify-release-gates.py:67,252-299` (`ISSUE_URL`, `review_approval`); `tests/scripts/run-perf-gate.sh:166-179`; `.github/scripts/verify-workflow-policy.py:2441-2467` (`check_release_gate_wiring`)

**Issue:** 17-SECURITY.md (T-17-27, residual 1) accepts that the comment JSON is only as authentic as the file, and says it "fails closed on hosted runs, because no workflow sets `GBB_IR_EXCEPTION_*`". Two facts make this worse than stated.

1. The gate never binds the review issue or the commenter to this project. `ISSUE_URL` accepts any `https://api.github.com/repos/<any-owner>/<any-repo>/issues/N`. The only identity checks are `author_association == "OWNER"` and a login-shaped string. The owner of any repository is `OWNER` in their own repository, so a self-made repository, issue and comment satisfy every check. The shipped positive self-test already approves under `example-owner/example-repo` (`REVIEW_ISSUE_API`, line 500), so the accepted behaviour is exercised and proven. Even a future trusted fetcher would not help, because the URL it would fetch comes from the decision file, which the PR author controls.
2. Nothing in the policy forbids a workflow from setting `GBB_IR_EXCEPTION_COMMENT_JSON` and `GBB_IR_EXCEPTION_DECISION`. I added both to the `run-perf-gate.sh --gate` step in `ci.yml` and in `release-rehearsal.yml`, and `verify-workflow-policy.py --check` accepted both. `check_release_gate_wiring` only counts fragments inside `run-perf-gate.sh`.

Scenario: a PR widens `ir_ratio_limit` in `tests/baseline/perf-gate-v1.txt` and commits three JSON files. They are a forged `OWNER` comment on an attacker-owned repository, a decision file, and the digest of the measurement the evaluator emits. The PR also sets the two env names on the CI perf-gate step. The gate verifies the forgery, writes a receipt, and the ratchet accepts the widened limit. The Ir regression budget is the only deterministic performance control the project has left now that paired timing is advisory.

**Fix:**
```python
EXPECTED_REVIEW_REPOSITORY = ("szTheory", "gabbaboy")
...
need((located.group(1), located.group(2)) == EXPECTED_REVIEW_REPOSITORY, "review-wrong-repository",
     "the review issue is not in the project repository")
need(comment["user"]["login"] == located.group(1), "review-not-owner",
     "the approving login is not the repository owner")
```
The self-test fixture should use the real owner and repository names, or take the expected repository as a parameter. In the policy, add a rule that no workflow `env:`, `run:` or `with:` mentions `GBB_IR_EXCEPTION_`, with a mutant that sets it. Until a trusted fetcher exists (a read-only step that calls `gh api repos/szTheory/gabbaboy/issues/comments/<id>` from the trusted revision), the residual should read "forgeable by any PR author", not "fails closed".

### Warnings

#### WR-C01: The release-please entrypoint and the non-release workflows are barely constrained by the policy checker

**File:** `.github/scripts/verify-workflow-policy.py:1515-1531` (`READONLY_WORKFLOWS` checks credentials only), `:2047-2060` (release-please is only checked for calling `release.yml`), `:2467-2486` (`check_all`)

**Issue:** Each of these dangerous edits was applied to a scratch copy and `--check` returned PASS:

- `release-please.yml`: add `secrets: inherit` to the `release` caller job.
- `release-please.yml`: add `packages: write` and `id-token: write` to the caller job's permissions.
- `release-please.yml`: change the top-level `permissions:` to `contents: write`.
- `release-please.yml`: add a new job with `contents: write` that runs `gh release delete`.
- `release-please.yml`: add `pull_request_target:` to `on:` (the checks use `GITHUB_REF == refs/heads/main`, which is true under `pull_request_target`).
- `release-rehearsal.yml`: widen the push filter to `branches: ['**']`, or add a `pull_request_target:` trigger.
- `fixture-repro.yml` and `libbet-repro.yml`: change `permissions: contents: read` to `contents: write`. `fixture-repro` runs PR code on `pull_request`.
- A `${{ github.head_ref }}` interpolation in a `run:` of `ci.yml` (`_check_run_expressions` is not called for `ci`, `preview` or `fixture-repro`).
- A brand-new `.github/workflows/evil.yml` with `pull_request_target`, `contents: write` and a checkout of the PR head SHA. The policy never enumerates the workflow directory; only the timeout-ledger glob does, and it passed too.

`release-please.yml` is the one workflow that holds `contents: write`, `issues: write` and `pull-requests: write` on every push to main, and it has the least coverage. The Phase 17 additions (`version-window`, `report-red`, nightly gate) are well mutated. The pre-existing surface around them is not.

**Fix:** Add a closed-world check. Enumerate `.github/workflows/*.yml` and require the set to equal `WORKFLOWS`. For every workflow assert an exact trigger set, exact top-level `permissions`, no `secrets:` key, and a pinned job list for `release-please.yml`. Add `_check_run_expressions` to `check_ci`, `check_readonly_workflows` and the preview and fixture checks. Add a mutant for each.

#### WR-C02: The policy judges the lifecycle script by region and the pin base by substring, so a one-line edit disables either gate

**File:** `.github/scripts/verify-workflow-policy.py:1966-1980` (`lifecycle_regions`), `:1658-1700` (`_check_state_pin_native_jobs`)

**Issue:** Two confirmed accepted mutations:

1. `release-evidence-lifecycle.sh` is judged only between `# BEGIN` and `# END` markers plus the exact dispatch lines. Everything outside the regions is unconstrained. Each of these passed `--check`:
   - `python3() { return 0; }` after the top-level `set`;
   - `bash() { return 0; }`;
   - `trap 'exit 0' ERR`;
   - an extra first arm `nightly-gate) exit 0 ;;` before `case "${1:-}" in`'s real arm. Bash takes the first match, so the nightly gate is silently never run while the policy still sees its dispatch line.
2. `_check_state_pin_native_jobs` tests that tokens appear in `state_pin_base`'s `run:`. Inserting `base=$(git rev-parse HEAD)` between `git cat-file -e "${base}^{commit}"` and `echo "base=$base"` keeps every token and passes. `state_portable_pins` then compares HEAD to itself and is vacuous (T-17-14, T-17-16).

**Fix:** Compare the script outside the regions to a pinned skeleton. Require exact text for the `case` block, the top-level `set` line, and nothing else between functions. Reject any line outside the regions that matches `^\w+\(\) \{` other than the seven `lifecycle_*` functions, or any `trap`. For the pin base, compare the `run:` body byte for byte to a constant, as `WINDOW_CALL` does.

#### WR-C03: The shipped tree fails the rehearsal judge's `--release-head`, so no release can pass the nightly gate until a follow-up commit lands

**File:** `.github/ci-timeouts.json:178-185` (`"provisional": true`), `.github/workflows/release-rehearsal.yml:360`, `.github/scripts/verify-workflow-policy.py:2252`

**Issue:** I ran the exact judge command on HEAD: `python3 -I .github/scripts/verify-workflow-policy.py --check --release-head` exits 1 with `REJECT timeout-ledger-provisional: nightly-asan.yml:report-red: a provisional row cannot stand at the release head; re-cite it from a main run`. The rehearsal `judge` job runs this command, so a rehearsal of this tree ends red. The release path then breaks in two places. `select_performance_run` requires a successful rehearsal run (so receipt reuse silently degrades to a fresh measurement). The `nightly-gate` needs the same run to find its head, so publication fails at the last step. The ordinary `--check` does not catch this, so CI is green.

17-SECURITY.md residual 3 and RM-027 list only the `candidate-performance` re-cite and the six `release_bound` rows. They do not mention this one. Re-citing needs a nightly dry run on `main`, which cannot exist until after merge, so the fix is a mandatory extra commit.

**Fix:** Add this row to the RM-027 entry-blocker list and to the post-merge steps in `docs/release.md`: "dispatch `nightly-asan.yml --ref main -f report_red_dry_run=true`, then commit the re-cited non-provisional row". Better, add a CTest that runs `--check --release-head` and is expected to fail only for rows listed in a named pending set, so the blocker is visible in CI rather than at release time.

#### WR-C04: Phase 16 WR-04 is only half closed; the budget checker and allowlist still come from the PR head

**File:** `.github/workflows/ci.yml:144`, `tests/scripts/verify-test-budget.py:149-200`

**Issue:** The new rows are now bounded (`NEW_ROW_CEILING_MAX`, `new-row-ref-reused`), which closes the arithmetic gap. The step still runs `python3 -I tests/scripts/verify-test-budget.py ... --base "$BUDGET_BASE"` from the checked-out PR tree. A change that edits the checker (or the allowlist and a `TIMEOUT` together) is judged by its own edited rules. The `changes` job runs its classifier from the base commit for exactly this reason. 16-REVIEW suggested the same here (`git show "$BUDGET_BASE:tests/scripts/verify-test-budget.py"`). T-17-25 is recorded closed without this half.

**Fix:**
```yaml
run: |
  git show "$BUDGET_BASE:tests/scripts/verify-test-budget.py" > "$RUNNER_TEMP/verify-test-budget.py"
  python3 -I "$RUNNER_TEMP/verify-test-budget.py" --build-dir build --base "$BUDGET_BASE" --repo "$GITHUB_WORKSPACE"
```
Keep the head copy's `--self-test` as a separate step. Fall back to the head copy only when the base lacks the file (first seeding).

#### WR-C05: The state-pin base step fails on every force-push and rebase, unlike the budget base step

**File:** `.github/workflows/ci.yml:98-119` (and the same step in `native-macos`, `native-windows`)

**Issue:** For a `push` event the step uses `github.event.before`, falling back to `git merge-base HEAD origin/main` only when `before` is all zeros. After a force-push or rebase, `before` is non-zero but no longer reachable, so `git cat-file -e "${base}^{commit}"` fails and the step exits 1 on all three native lanes. The adjacent `budget_base` step handles exactly this case (`|| ! git cat-file -e` falls back to the merge base, with the comment "a rebased or force-pushed branch has a parent that no fetched ref reaches any more"), and the policy then pins the stricter text. The result is a red `push`-event `required-native` for the same head alongside a green `pull_request` run. Whether branch protection tolerates that depends on settings the repository does not record, but a red required context on every rebase is at best noise that trains people to ignore the check.

**Fix:** Mirror `budget_base`: take the merge-base fallback when `before` is zero or unresolvable, then validate the result. Update `_check_state_pin_native_jobs` (which pins the exact token list) at the same time, together with a mutant for the unreachable-parent case.

### Info

#### IN-C01: The retry tamper check cannot detect a post-attachment swap and is described as if it could

**File:** `.github/scripts/verify-release-gates.sh:382-440` (`check_attached_evidence`), `docs/release.md` (retry paragraph)

**Issue:** Each attached asset is compared with `digest` from the live asset list. That digest is GitHub's hash of whatever is currently attached, so replacing an asset through the API or UI produces a new, self-consistent digest and the comparison passes. What the check really adds is identity binding (tag, version, source SHA, sidecar-to-corpus hash, fuzz source, performance candidate sha) and detection of download corruption. That is useful, but T-17-22 ("independent tamper check") and the doc overstate it. The fuzz and performance receipts get only a source and `passed` check at this stage, with the real validation deferred to `--check-v02-evidence`. 16-REVIEW IN-C01 suggested recording the attached digests earlier in the run; that is not done.

**Fix:** Reword the threat as "identity and consistency check" and keep `--check-v02-evidence` as the content gate. If swap detection is wanted, persist the attached digests from the first attempt in a signed-by-workflow place (a run artifact or the source receipt) and compare on retry.

#### IN-C02: `libbet-repro.yml` and `fixture-repro.yml` are outside the "persist-credentials: false" rule set for some jobs

**File:** `.github/workflows/libbet-repro.yml:16-17`

**Issue:** The checkout has no `with: persist-credentials: false`, and `libbet-repro` is not in `READONLY_WORKFLOWS`, so the credentials rule never sees it. The token is `contents: read` and the workflow is dispatch-only, so impact is low. It is part of the same coverage gap as WR-C01.

**Fix:** Add `persist-credentials: false` and include `libbet-repro.yml` in `READONLY_WORKFLOWS`.

---

_Reviewed: 2026-10-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
