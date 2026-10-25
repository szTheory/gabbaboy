# Deferred items

- **Build warning:** `cmake --build --preset phase1` emitted macOS linker warnings that `libgabbaboy_core.a` appeared more than once for `test_age` and `test_cgb_speed_*`. The build completed successfully; this predates and is outside Plan 13-11's documentation and claim-checker scope. Reassess in the owning build-target plan if the warning persists.
  status: resolved
  resolution: Plan 15.1-10 (SCAN-LINK, commits e37de34 and c473349) removed the cause: `gabbaboy_accept` re-published the normal core, so those link lines named it twice. `verify-core-linkage.py --self-test` (CTests `core_linkage_links` and `core_linkage_controls`) now rejects duplicate-core links. Re-checked 2026-10-24 at f7f14c0: a fresh `cmake --build` with 145 link steps printed no duplicate-library warning. As a control, the same linker given `libgabbaboy_core.a` twice prints `ld: warning: ignoring duplicate libraries`.
