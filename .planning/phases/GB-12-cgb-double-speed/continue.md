# Phase GB-12 Continuation

Completed workflow stage: **Phase GB-12 — CGB Double Speed, plan 12-10 execution**. Phase 12 remains in progress; see [12-10-SUMMARY.md](12-10-SUMMARY.md). Earlier plan evidence remains in [12-09-SUMMARY.md](12-09-SUMMARY.md) and [12-08-SUMMARY.md](12-08-SUMMARY.md).

Task commits: tracer and TIMA/KEY1/STOP probes `a9456fa`, DIV/serial/NR52/DMA probes with independent bounds `b326599`, digest RED assertions `a800bef`, and clean-core digest pins with mutant controls `6fcd930`. The final original `speed.gb` has SHA-256 `3c6e88de1e28d47566f7486dd13813c8fb1baf48ee336509e3902bd9ff8e2f3f`; its PCM and RGB555 pins are recorded at clean-core revision `b326599`. The M17 APU and M1 PPU mutants fail their corresponding digests; mask-zero controls pass.

The committed-core spsw-div window remains `[0x20004, 0x20007]` T at source revision `2e78a48`, with `GBB_SPEED_SWITCH_STALL_T` pinned at `0x20004` T. The AGE measurement reached its verdict at 22,702,928 half-dots under a 46,000,000-half-dot budget. The full configured CTest inventory passed **831/831**. All evidence is pinned software-corpus evidence; no physical-hardware claim was added.

Next plan: **GB-12 plan 12-11 — hostile pre-switch entry points (selector byte) with rule-derived outcomes**. Next phase after Phase 12: **Phase 13 — CGB HDMA** (not started). Next command: **`/gsd-execute-phase 12`** (resumes at 12-11). Auto-advance and auto-chain remain false. Stop after Phase 12 and wait for the owner before entering another phase.
