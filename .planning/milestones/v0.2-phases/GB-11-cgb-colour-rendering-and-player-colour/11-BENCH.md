# Phase 11 colour-path benchmark (D-33, D-04, D-22, advisory)

Receipts: `11-BENCH.json` (keys `headline`, `headline_repeat_1`, `headline_repeat_2`, `cgb_colour`).
Harness: `tests/scripts/measure-release-baseline.sh --ab BASE HEAD` (strictly interleaved pairs, order
alternating each pair). CTest checks only the digest and receipt shape (`cgb_bench_ab_*`); no timing is
asserted anywhere, and no hosted timing was collected.

## Setup

DMG A/B (headline and two repeats):

- Workload `original-wram-tracer-1m-half-dots-v1`, fixture `fixtures/tracer/tracer.gb`, model DMG-CPU-B, `--no-trace`.
- Output digest `correctness_digest_fnv1a64=4c7a57ff3d50d228` verified by the harness on every warm-up and every
  sample of both builds (a mismatch aborts the run).
- 3 warm-ups, 30 interleaved pairs per run; the metric is `elapsed_ns` reported by `measure_core`.
- Builds: `-DCMAKE_BUILD_TYPE=Release` (`-O3 -DNDEBUG`), Apple clang 21.0.0, `measure_core` target only, one build
  per revision, each in its own scratch build directory.
- Hardware class: Darwin arm64, Apple M5 Pro. The host was shared (load average about 5 during the runs).
- Revisions: base is the Phase 10 head `3012e8f` (the Phase 10 squash on main), built from a detached
  `git worktree` outside the repository tree with the head `tests/measure_core.c` overlaid so both binaries accept
  the same arguments (the DMG form is byte-identical); head is `271faa1`, the plan 11-14 commit that carries the
  `--profile cgb` form. The head core is the Phase 11 colour core.

CGB colour workload (separate, not an A/B):

- Fixture `fixtures/cgb-colour/colour-attr.gb`, model CGB-CPU-E, `measure_core --no-trace --profile cgb`, budget
  1 000 000 half-dots (about 7 frames), head build only, 3 warm-ups, 30 samples, same build flags and hardware class.
  `measure_core` prints the legacy workload label `original-wram-tracer-1m-half-dots-v1` for every ROM; the
  workload here is the fixture named above.
- Output digest `correctness_digest_fnv1a64=3c5797f6525df9c7` (work RAM and HRAM) on every warm-up and sample.
- There is no like-for-like base: the Phase 10 head stops this workload after 131 544 half-dots on the first
  colour register (stop reason unsupported-bus, the colour registers being DEFERRED there), with the same digest.

## Results

DMG: head time as percent of base time (100 = no change).

| Comparison | Median | Min-of-n | SD | 95% margin (1.96 sd/sqrt n) | Label | D-22 trigger |
|---|---|---|---|---|---|---|
| Phase 11 head vs Phase 10 head 3012e8f (headline) | 99.22 | 99.17 | 4.13 | 1.48 | within noise (under 3%) | not fired |
| headline repeat 1 | 98.49 | 96.94 | 4.52 | 1.62 | within noise (under 3%) | not fired |
| headline repeat 2 | 100.23 | 97.13 | 5.37 | 1.92 | within noise (under 3%) | not fired |

CGB colour workload, absolute time per run of 1 000 000 half-dots, head build.

| Statistic | Value |
|---|---|
| Median | 8.19 ms |
| Min-of-n | 7.69 ms |
| SD | 0.40 ms |
| 95% margin of the mean | 0.14 ms |

## Reading and D-04 decision

- The D-22 trigger is a median ratio above 105 with the lower bound (median minus margin) above 100. All three
  headline runs put the median between 98.5 and 100.2 percent, so it did not fire in any of them. The colour core
  costs the DMG profile nothing measurable against the Phase 10 head.
- D-04: no hoist: the per-dot branch stays (D-04). Because the trigger did not fire, no core change was made for
  performance, so no second A/B receipt is owed; the DMG identity checks and the player suite were run at the
  plan head (see the plan SUMMARY).
- The CGB colour workload is a recorded cost only. It runs at roughly 122 M half-dots per second on this host
  class, comparable to the DMG tracer; it has no base to compare with and no threshold.
- Interference: per-pair SD of 4 to 5 percent comes from a shared host. Treat every number as advisory; the
  conclusion rests on the margin bounds, not a single median.
