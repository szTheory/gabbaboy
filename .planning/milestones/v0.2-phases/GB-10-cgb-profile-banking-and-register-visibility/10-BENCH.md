# Phase 10 banking-indirection benchmark (D-22, advisory)

Receipts: `10-BENCH.json` (keys `headline`, `attribution`, `headline_repeat_1`, `headline_repeat_2`).
Harness: `tests/scripts/measure-release-baseline.sh --ab BASE HEAD` (strictly interleaved pairs, order
alternating each pair). CTest checks only the digest and receipt shape (`cgb_bench_ab_*`); timing is never asserted.

## Setup (identical for every run)

- Workload `original-wram-tracer-1m-half-dots-v1`, fixture `fixtures/tracer/tracer.gb`, model DMG-CPU-B, `--no-trace`.
- Output digest `correctness_digest_fnv1a64=4c7a57ff3d50d228` verified on every warm-up and sample of both builds.
- 3 warm-ups, 30 interleaved pairs; metric is `elapsed_ns` reported by `measure_core`.
- Builds: `-DCMAKE_BUILD_TYPE=Release` (`-O3 -DNDEBUG`), Apple clang 21.0.0, `measure_core` target only, one build per revision.
- Hardware class: Darwin arm64, Apple M5 Pro (macOS arm64 class of the frozen baseline).
- Revisions: frozen Phase 7 baseline `5a55f19ba2e0ec596005af4dbbc55d476b326333`; Phase 9 head `d7e2e0a`;
  Phase 10 head `c7c616a` (the revision of the 10-17 harness commit; core sources are unchanged by this plan).
- No hosted CI timings were collected; any hosted number would be non-comparable and is not used.

## Results (head time as percent of base time; 100 = no change)

| Comparison | Median | Min-of-n | SD | 95% margin (1.96 sd/sqrt n) | Label | Review trigger |
|---|---|---|---|---|---|---|
| Phase 10 vs frozen baseline 5a55f19 (headline) | 107.28 | 101.52 | 10.94 | 3.91 | slower than base by more than 3% | fired |
| headline repeat 1 | 105.59 | 105.44 | 9.04 | 3.24 | slower than base by more than 3% | fired |
| headline repeat 2 | 105.98 | 107.37 | 10.84 | 3.88 | slower than base by more than 3% | fired |
| Phase 10 vs Phase 9 head d7e2e0a (attribution) | 100.67 | 103.52 | 10.53 | 3.77 | within noise (under 3%) | not fired |

## Reading

- review trigger fired: three independent headline runs put the median at 105.6 to 107.3 percent of the Phase 7 baseline
  with the lower margin bound above 100 percent in each. The DMG hot path pays roughly 6 to 7 percent for the per-access
  bank indirection. The first run's min-of-n (101.5) is the lowest estimate; the other two are above the trigger on both statistics.
- Attribution run: Phase 10 versus Phase 9 is within noise (median 100.67, but min-of-n 103.52), so the cost cannot be
  cleanly split between Phase 9 and Phase 10 from these data. The measurement is not conclusive about which phase introduced it.
- Interference: the host was shared and loaded (load average about 10 to 11 during the runs), so per-pair SD is around 9 to 11
  percent, large compared with the 3 percent noise threshold. Treat all numbers as advisory.
- Per DECISIONS D-016 the owner decides whether this warrants performance work. This plan does not optimise (owner veto item 5).
  `tests/baseline/dmg-cpu-b-v1.txt` is unchanged and gains no `bench.banking.*` lines.
