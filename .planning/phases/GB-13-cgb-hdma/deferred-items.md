# Deferred items

- **Build warning:** `cmake --build --preset phase1` emitted macOS linker warnings that `libgabbaboy_core.a` appeared more than once for `test_age` and `test_cgb_speed_*`. The build completed successfully; this predates and is outside Plan 13-11's documentation and claim-checker scope. Reassess in the owning build-target plan if the warning persists.
