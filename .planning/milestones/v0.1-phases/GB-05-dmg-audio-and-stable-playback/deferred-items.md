# Deferred Items

- An unchanged `tests/test_dma.c:702` compile warning (`-Wunsequenced`) appeared
  while rebuilding the all-target Phase 1 preset. It is outside Plan 05-04's
  changed files and remains unfixed; this plan's focused audio tests pass.
  status: resolved
  resolution: 9436db0 split the unsequenced `routine[rn++] = ... rn ...` store into
  `routine[rn] = ...; ++rn;`. A clean `cmake --build --preset phase1 --clean-first`
  at c21631a emits no warnings (re-checked at v0.1 milestone close, 2026-10-10).
