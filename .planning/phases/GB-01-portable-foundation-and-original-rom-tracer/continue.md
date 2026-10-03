# Continue: Phase 1 execution

**Completed stage:** Phase GB-01-03 execution — relocatable installed package and C/C++ consumer verification. Plans 01–03 of 5 are complete; Phase 1 remains active.

Plan 03 is committed as `a48f254` and `98a15c4`, with summary commit `0be34c9`. All 21 ordinary CTest cases pass. After install and relocation, the runner and both C/C++ external consumers pass 3/3 tests from the relocated prefix; the runner uses the installed fixture from an unrelated working directory. Local evidence is macOS arm64 only. The fixture remains narrow DMG-CPU-B evidence, not general CPU or gameplay support. Native Linux/Windows runs, the CMake 3.25.3 floor, required CI, and hosted artifacts are not yet proven.

The plans incorporate the accepted small-dependency-tree preference: the core stays standard-library-only; RGBDS is isolated to fixture regeneration CI. The package exports only the public C interface and makes no stable ABI promise. Hosted remote/PR/artifact evidence remains pending because no origin is configured. Plan 05 retains a checkpoint to provide the canonical repository endpoint or report that hosting is unavailable.

**Next stage:** Phase 1 Plan 04 — native CI matrix, sanitizers, and CMake 3.25.3 floor verification.

**Next command:** `$gsd-execute-phase 1`

Follow the repository pause rule: complete and verify Phase 1, then stop before Phase 2.
