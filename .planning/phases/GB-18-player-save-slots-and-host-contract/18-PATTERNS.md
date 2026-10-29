# Phase 18: Player Save Slots and Host Contract - Pattern Map

**Mapped:** 2026-10-28
**Files analyzed:** 41 new or modified files (grouped into 30 rows below)
**Analogs found:** 28 of 30 rows have a usable analog; `host_exit.h` has none and `host_signal.c` is partial (see "No Analog Found" for the specific gaps inside rows that otherwise match)
**Tracked-source gate:** every path below was checked with `git ls-files --error-unmatch` and is git-tracked. No `.gsd/capabilities/` mirror paths appear.
**Line numbers** are from the working tree at the time of mapping. CONTEXT/RESEARCH already found one drift (`src/runner/main.c` tracer route is line 455, not 451), so plans should anchor edits by text, not by number.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/host/host_basename.c/.h` | utility (pure validator) | transform | `src/player/catch_up_policy.c/.h` | role-match |
| `src/host/host_save_io.c/.h` | service (POSIX file I/O, dir-fd) | file-I/O | `src/player/session.c` (`read_save_file`, `write_all`, `sync_save_directory`, `atomic_save`) | exact (path-based; port to `*at`) |
| `src/host/host_cadence.c/.h` | utility (pure state machine) | event-driven (poll) | `src/player/session.c` `player_save_cadence_observe` | exact |
| `src/host/host_exit.h` | config (X-macro table) | transform | none (closest: core `cart_type_table`) | no analog |
| `src/host/host_signal.c/.h` | adapter (signal flag + pacing) | event-driven | `src/player/main.c:2015-2041` (clock + EINTR nanosleep only) | partial |
| `src/host/host_save_format.c/.h` | model (static lookup table) | transform | `src/core/gabbaboy.c:265-284` `cart_type_table` | role-match |
| `src/host/host_run.c/.h` | controller (frame loop, batch/paced) | streaming / batch | `src/runner/main.c:408-431` `run_original_tracer` + `tests/test_continuation_guests.c` `run_to_idle` | role-match |
| `src/runner/main.c` (modify) | controller (CLI dispatch) | request-response | itself (`main` at line 454) | exact |
| `CMakeLists.txt` (modify) | config | n/a | itself (`gabbaboy_accept_bare` lines 43-58, dirty list 85-88, install 139-159) | exact |
| `src/player/slots.c/.h` | service (SDL-free slot engine) | file-I/O + request-response | `src/player/catch_up_policy.c/.h` (module shape, message table) + `src/player/session.c` (I/O) | role-match |
| `src/player/input.c/.h` (modify: rebase helper) | utility | event-driven | `player_input_reset` / `player_input_reconcile` in the same file | exact |
| `src/player/main.c` (modify: keys, status, help) | controller (event handler) | event-driven | itself: `handle_key` 1357-1438, `reset_session` 955-976, `set_status` 788-791 | exact |
| `src/player/limitations.h` + `tests/player/test_limitations.c` (modify) | config + test | n/a | themselves (full-literal `strcmp`) | exact |
| `include/gabbaboy/gabbaboy.h` + `src/core/gabbaboy.c` (modify: `gbb_get_input_clock`) | API function | request-response | `gbb_info` / `gbb_get_info` / `info_store` | exact |
| `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp` (modify) | test (installed consumer) | request-response | `gbb_get_info` use at `c/main.c:313-320` | exact |
| `tests/test_input_clock.c` (new) | test | request-response | `tests/test_cgb_profile.c` `info_struct_size_for` | exact |
| `tests/test_host_save_io.c`, `tests/test_host_basename.c` (new) | test | file-I/O / transform | `tests/test_battery.c`, `tests/player/test_session.c` (hostile files) | role-match |
| `tests/test_host_cadence.c` (new) | test (pure) | transform | `tests/test_catch_up_policy.c` + `session_save_cadence` in `tests/player/test_session.c:644` | exact |
| `tests/test_slots.c` (new, portable) | test | file-I/O | `tests/player/test_session.c` (`session_symlink`/`session_special`) + `tests/test_battery.c` | role-match |
| `tests/player/test_slots.c` (new, macOS) | test | event-driven | `tests/player/test_reset_transition.c` (embedded `main.c`, `push_key` + `pump_events`) | exact |
| `tests/test_save_format_completeness.c` (new) | test | batch enumeration | `tests/test_loader_matrix.c` `loader_type_byte_sweep` + `tests/test_battery.c` `make_rom` | role-match |
| `tests/scripts/test_host_signals.py` (new) | test harness | event-driven (real signals) | `tests/scripts/verify-v02-consumers.py` `run_command` / `terminate_process` | role-match |
| `tests/scripts/verify-save-formats.py`, `tests/scripts/verify-host-contract.py` (new) | checker | batch | `tests/scripts/verify-v03-dispositions.py` | exact |
| `docs/host-contract.json` (new) | config (data) | n/a | `fixtures/mbc1-continuation/manifest.json` (2-space JSON) | partial |
| `cmake/CheckHostApiSymbols.cmake`, `cmake/CheckRunnerSourcesQualified.cmake` (new) | checker | batch | `cmake/CheckCoreNoHostClock.cmake` | exact |
| `cmake/CheckCoreNoHostClock.cmake` (modify) | checker | batch | itself (lines 32-50) | exact |
| `cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`, `tests/expected-tests.txt`, `tests/player/expected-tests.txt` (modify) | config (inventory) | n/a | themselves | exact |
| `tests/CMakeLists.txt`, `tests/player/CMakeLists.txt` (modify) | config | n/a | themselves (`no_host_clock*` block 2364-2415; mutant factory 5389-5415; player branch chain 51-484) | exact |
| `cmake/VerifyInstalledHostMode.cmake` (new) + `installed_host_smoke` test | test (installed package) | request-response, two processes | `cmake/VerifyInstalledPackage.cmake` | role-match |
| `docs/native-integration.md`, `docs/cartridge-and-saves.md`, `README.md`, `docs/support/unreleased.md`, `.planning/research/v0.3/PLAYSTEAD-CONTRACT.md` (modify) | docs | n/a | `native_guide_rtc_contract` (`tests/CMakeLists.txt:2438-2460`) + `cmake/VerifyDocContract.cmake` | role-match |
| Fixture ROM generator (Python module or inline in the harness) | test helper | transform | `tests/test_battery.c` `make_rom` / `fix_checksum` and `tests/test_state_fork.c` `finish_generated_rom` | role-match |

## Pattern Assignments

### Group A. `gabbaboy_host` library (HOST-01/02/03)

#### `src/host/host_save_io.c/.h` (service, file-I/O)

**Analog:** `src/player/session.c`. Same role and flow, but the analog is path-based (`open(path)`, `mkstemp`, `rename`). Port each call to its `*at(dirfd, ...)` form per D-09 and keep the structure, the EINTR loops and the fault-stage idea.

**Feature macros** (copy this exact block at the top of every POSIX file; the only in-repo precedent is `tests/measure_core.c:1-13`, because `session.c` is Apple-only and never needs it):
```c
#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include "gabbaboy/gabbaboy.h"
...
#ifdef _WIN32
#include <windows.h>
#else
#include <sys/resource.h>
#endif
```
For `src/host`, wrap the whole POSIX body in `#ifndef _WIN32` with stubs that return a refusal, so MSVC compiles (D-04).

**Bounded read with identity re-check** (`session.c:460-509`; adapt: `openat(dirfd, name, O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_NOCTTY|O_CLOEXEC)`, require `st_size == want`, read up to `want+1`, distinguish ENOENT (fresh image) from every other errno (refusal)):
```c
static bool read_save_file(const char *path, uint8_t *bytes, size_t capacity,
                           size_t *out_size, bool *out_missing,
                           bool *out_recoverable, struct stat *out_info) {
    *out_missing = false;
    *out_recoverable = false;
    *out_size = 0u;
    const int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
    if (fd < 0) {
        if (errno == ENOENT) {
            *out_missing = true;
            return true;
        }
        return false;
    }
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode) || info.st_size < 0) {
        (void)close(fd);
        return false;
    }
    ...
    size_t total = 0u;
    while (total < capacity) {
        const ssize_t count = read(fd, bytes + total, capacity - total);
        if (count > 0) { total += (size_t)count; continue; }
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) { (void)close(fd); return false; }
        break;
    }
    struct stat after;
    const bool stable = fstat(fd, &after) == 0 &&
                        after.st_dev == info.st_dev &&
                        after.st_ino == info.st_ino &&
                        after.st_size == info.st_size &&
                        total == (size_t)info.st_size;
    const int close_result = close(fd);
    if (!stable || close_result != 0) return false;
```
Do not copy the `info.st_size > capacity` allocation logic literally: D-08/D-22 forbid sizing an allocation from `st_size`. Allocate `want` (or `gbb_state_size(live)+1`) from the core, then compare `st_size` to it.

**EINTR/short-write-safe write loop** (`session.c:787-814`, keep the shape; drop the `GBB_PLAYER_SESSION_TESTING` branches or re-home them behind the host's own test-only seam):
```c
static bool write_all(int fd, const uint8_t *bytes, size_t size) {
    size_t written = 0u;
    while (written < size) {
        size_t remaining = size - written;
        const ssize_t count = write(fd, bytes + written, remaining);
        if (count > 0) { written += (size_t)count; continue; }
        if (count < 0 && errno == EINTR) continue;
        return false;
    }
    return true;
}
```

**Directory fsync tolerance** (`session.c:816-840`; adapt: the dirfd is already open, so call `fsync(dirfd)` directly instead of re-opening by path):
```c
    const int result = fsync(fd);
    const int saved_errno = errno;
    (void)close(fd);
    if (result == 0 || saved_errno == EINVAL || saved_errno == ENOTSUP ||
        saved_errno == EOPNOTSUPP)
        return true;
    return false;
```

**Target check** (`session.c:842-850`; adapt: `fstatat(dirfd, name, &info, AT_SYMLINK_NOFOLLOW)`):
```c
static bool save_target_is_replaceable(const char *path) {
    struct stat info;
    if (lstat(path, &info) == 0) {
        if (S_ISREG(info.st_mode) && !S_ISLNK(info.st_mode)) return true;
        errno = EINVAL;
        return false;
    }
    return errno == ENOENT;
}
```

**Atomic sequence with staged failure reporting** (`session.c:852-917`). Keep: target check before AND after the temp write, checked `close`, unlink the temp on any pre-rename failure, one stderr line naming the failed stage and `strerror`. Change: `mkstemp` -> `openat(dirfd, tmp, O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC, 0600)` with the EEXIST/`seq` retry (<=16), `fsync` -> `F_FULLFSYNC`-then-`fsync` (RESEARCH Pattern 1 snippet), `rename` -> `renameat`, and a directory-fsync failure after the rename reports failure and leaves the image dirty (D-09 step 7).
```c
    const int fd = fail_temp_create ? -1 : mkstemp(temporary);
    ...
    bool ok = fchmod(fd, S_IRUSR | S_IWUSR) == 0;
    if (ok && !write_all(fd, bytes, size)) { ok = false; failed_at = "write"; failure_errno = errno; }
    if (ok && (fail_file_sync || fsync(fd) != 0)) { ... failed_at = "file sync"; ... }
    if (close(fd) != 0 && ok) { ok = false; failed_at = "close"; failure_errno = errno; }
    if (ok && !save_target_is_replaceable(path)) { ok = false; failed_at = "target validation"; ... }
    if (ok && (fail_rename || rename(temporary, path) != 0)) { ... failed_at = "rename"; ... }
    if (ok && !sync_save_directory(path)) { ok = false; failed_at = "directory sync"; ... }
    if (!ok) (void)unlink(temporary);
    if (!ok)
        fprintf(stderr, "Battery save %s failed: %s\n", failed_at, strerror(failure_errno));
    return ok;
```
Note the fix to carry over: the analog does NOT forbid retrying `fsync` after EIO; D-09 does ("discard that temp and rewrite from memory next time"). Do not retry on the same fd.

**Fault-injection seam shape** (`session.c:35-57` and the `consume_test_fault` call sites): a file-static stage enum, a one-shot `consume_test_fault(stage)`, the whole thing under a test-only macro so shipped binaries expose no symbol. D-09 says "seams exist in test builds only". Mirror this with a `GBB_HOST_TESTING` macro and the test-only setter; `tests/test_host_save_io.c` compiles the library source with that macro, as `gabbaboy-player-session-test` does for `session.c` (`tests/player/CMakeLists.txt:293-304`).
```c
#ifdef GBB_PLAYER_SESSION_TESTING
static player_session_test_fault_stage test_fault_stage;
static bool consume_test_fault(player_session_test_fault_stage stage) {
    if (test_fault_stage != stage) return false;
    test_fault_stage = PLAYER_SESSION_TEST_FAULT_NONE;
    return true;
}
#endif
```

---

#### `src/host/host_cadence.c/.h` (utility, pure state machine)

**Analog:** `src/player/session.c:1081-1113` (`player_save_cadence_reset/observe`) with its header `session.h:34-39` and test `tests/player/test_session.c:644` (`session_save_cadence`). Same job (generation changed, quiet window, max age), same shape (a small struct, a reset, an observe that returns a decision, no clock inside). Differences: host time is counted in frames (D-03), the quiet/max-age are 16/300 frames, there is a 3,600-frame export-and-compare, and a "first write for an absent `.sav`" rule.
```c
bool player_save_cadence_observe(player_save_cadence *cadence,
                                 uint64_t generation,
                                 uint64_t saved_generation,
                                 uint64_t host_time_ns) {
    if (cadence == NULL) return false;
    if (generation == saved_generation) {
        player_save_cadence_reset(cadence, generation);
        return false;
    }
    if (!cadence->dirty) {
        cadence->dirty = true;
        cadence->observed_generation = generation;
        cadence->first_dirty_ns = host_time_ns;
        cadence->last_change_ns = host_time_ns;
    } else if (generation != cadence->observed_generation) {
        cadence->observed_generation = generation;
        cadence->last_change_ns = host_time_ns;
    }
    const bool quiet_elapsed = host_time_ns >= cadence->last_change_ns &&
        host_time_ns - cadence->last_change_ns >= UINT64_C(2000000000);
    const bool maximum_age_elapsed = host_time_ns >= cadence->first_dirty_ns &&
        host_time_ns - cadence->first_dirty_ns >= UINT64_C(10000000000);
    return quiet_elapsed || maximum_age_elapsed;
}
```
Return an action enum `{NONE, FLUSH, EXPORT_COMPARE}` instead of `bool`, take `frame` as the clock, and compare generation with `!=` (a `>` mutant must fail, D-11 and RESEARCH Pattern 5). Keep the unsigned `host_time >= last_change` guards. Debug frame cost is 3-4 ms, so 3,600 frames is 11-14 s: cadence must be tested as a pure function, never by waiting.

**Test pattern:** `tests/test_catch_up_policy.c` (below, under `tests/test_host_cadence.c`).

---

#### `src/host/host_basename.c/.h` (utility, transform)

**Analog:** `src/player/catch_up_policy.h/.c`: SDL-free, POSIX-free, "the caller supplies every input so the table is testable on every OS", a status enum plus a formatter that "always NUL-terminates and never overruns".
```c
/* Pure host policy ... No SDL, CommonCrypto, POSIX or clock call lives here:
 * the caller supplies both Unix timestamps, so the table is testable on every
 * operating system. */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
```
`host_stem(const char *rom_path, char *out, size_t cap)` returns `{OK, REFUSE}` and writes nothing on refusal. No in-repo UTF-8 validator exists: write the ~30-line strict DFA (RESEARCH Pattern 3), so see "No Analog Found". Each refusal class needs its own stderr reason token (GB-GSD-029).

---

#### `src/host/host_save_format.c/.h` (model, static lookup)

**Analog:** the core's `cart_type_table` (`src/core/gabbaboy.c:265-284`) for table form, and `cart_row_for_type` right below it for the lookup shape. The host table is separate, public-API-only and must NOT include `gabbaboy_test.h`.
```c
static const cart_type_row cart_type_table[] = {
    /* type kind          window batt timer rumble maxrom ram rule           ram32 ceiling */
    { 0x03u, CART_MBC1,     1u, 1u, 0u, 0u, 0x06u, CART_RAM_8K_OR_32K, 0x04u, GBB_LEGACY_MAX_ROM_SIZE },
    { 0x06u, CART_MBC2,     1u, 1u, 0u, 0u, 0x03u, CART_RAM_MBC2,      0u,    GBB_LEGACY_MAX_ROM_SIZE },
    { 0x0Fu, CART_MBC3,     1u, 1u, 1u, 0u, 0x07u, CART_RAM_NONE,      0u,    GBB_MBC3_MAX_ROM_SIZE },
    ...
static const cart_type_row *cart_row_for_type(uint8_t type) {
    for (size_t i = 0; i < sizeof(cart_type_table) / sizeof(cart_type_table[0]); ++i)
        if (cart_type_table[i].type == type) return &cart_type_table[i];
    return NULL;
}
```
Key lookup is (type, RAM code, ROM-code constraint) per D-19; derive the runtime answer from the public API (`gbb_probe_rom` flags + `gbb_battery_size`), and use the C table only to print the id. The completeness test (below) proves the two agree.

---

#### `src/host/host_signal.c/.h` (adapter, event-driven)

**Partial analog only:** `src/player/main.c:2015-2041` shows the in-repo `clock_gettime(CLOCK_MONOTONIC)` + EINTR-looped `nanosleep` idiom (for pacing). There is **no `sigaction` code anywhere in tracked source** (the only `signal.h` use is `raise(SIGSTOP)` under the session test macro). Take sigaction details from RESEARCH Pattern 4 / D-13.
```c
struct timespec started;
if (clock_gettime(CLOCK_MONOTONIC, &started) != 0) { ... }
...
const struct timespec pause = {0, 10000000};
while (nanosleep(&pause, NULL) != 0 && errno == EINTR) { }
```
Carry-over caution: the analog **loops on EINTR**, which is exactly wrong for the paced sleep. The host sleep must return on EINTR (so a SIGTERM wakes it), re-check `g_host_stop`, and only then recompute the remaining deadline. macOS has no `clock_nanosleep` (D-03), so use a relative `nanosleep` against a `CLOCK_MONOTONIC` deadline.

---

#### `src/host/host_run.c/.h` (controller, frame loop)

**Analog 1:** `src/runner/main.c:408-431` `run_original_tracer`: the runner's own load-run-report pattern.
```c
static int run_original_tracer(const char *path) {
    FILE *file=fopen(path,"rb");if(!file){fprintf(stderr,"invalid-fixture: cannot open ROM\n");return 2;}
    if(fseek(file,0,SEEK_END)!=0){fclose(file);return 2;}long length=ftell(file);
    if(length<0||length>8*1024*1024||fseek(file,0,SEEK_SET)!=0){fclose(file);fprintf(stderr,"invalid-fixture: size out of bounds\n");return 2;}
    size_t size=(size_t)length;uint8_t *rom=malloc(size);
    if(!rom||fread(rom,1,size,file)!=size){free(rom);fclose(file);return 2;}fclose(file);
    gbb_instance *machine=NULL;gbb_profile profile=GBB_RUNNER_PROFILE_DMG;
    if(gbb_create(profile,&machine)!=GBB_OK||gbb_load_rom(machine,rom,size)!=GBB_OK){free(rom);gbb_destroy(machine);fprintf(stderr,"invalid-fixture: unsupported or malformed ROM\n");return 2;}
```
Host mode already owns an 8 MiB cap here (`8*1024*1024`) but as a magic number; define a named host constant (`GBB_MAX_ROM_SIZE` is core-private, RESEARCH F7). Host code uses the public enum `GBB_PROFILE_DMG_CPU_B` / `GBB_PROFILE_CGB_CPU_E`, not `GBB_RUNNER_PROFILE_*` (that macro lives in `gabbaboy_test.h`).

**Analog 2:** `tests/test_continuation_guests.c:55-71` `run_to_idle`: treat `GBB_STOP_HALTED_IDLE` as a normal outcome and any non-`BUDGET` reason otherwise as a stop.
```c
const gbb_run_result r = gbb_run(m, SLICE, NULL, 0u);
if (r.reason == GBB_STOP_HALTED_IDLE) { ... return 0; }
if (r.reason != GBB_STOP_BUDGET) { fprintf(stderr, "unexpected stop reason %d\n", (int)r.reason); return 1; }
```
For host mode the normal set is `{BUDGET, HALTED_IDLE, STOPPED}` (RESEARCH F10); everything else is a core stop: final flush then exit 1.

**Frame constant:** `src/player/main.c:24` `#define PLAYER_FRAME_HALF_DOTS UINT64_C(140448)`. Define the host equivalent in `src/host/` rather than including `player/main.c`.

---

#### `src/host/host_exit.h` (X-macro exit table)

**No analog** (no X-macro exists in `src/` or `include/`). Use the RESEARCH "Exit table as X-macro" example and have `verify-host-contract.py` parse it against `docs/host-contract.json`. See "No Analog Found".

---

### Group B. Runner integration

#### `src/runner/main.c` (modify: host dispatch)

**Analog:** the same file. Dispatch point and anchor text (`main.c:454-455`):
```c
int main(int argc,char **argv) {
    if(argc==2&&strncmp(argv[1],"--",2)!=0)return run_original_tracer(argv[1]);
    const char *manifest=NULL,*selected=NULL,*acceptance=NULL;int receipt=0,suite=0;
    gbb_acceptance_options options;memset(&options,0,sizeof(options));
```
Insert the host-invocation test **before** the `argc==2` line. Existing error convention to follow for host-mode usage errors (exit 2, one stable token, nothing else on stdout):
```c
else {fprintf(stderr,"invalid-arguments: use --help for usage\n");return 2;}
...
if(!found||options.has_drop_button){fprintf(stderr,"invalid-arguments: reason=invalid-mutate\n");return 2;}
```
Host-mode grammar errors should print `invalid-arguments: reason=<token>` in this style so `tests/expect_exit.cmake` regexes can pin each reason. The runner's file is dense one-line style; keep the host code out of it (it only dispatches), as RESEARCH F8 recommends.

`print_usage` (`main.c:433-444`) is checked by `tests/verify_runner_help.cmake`, which asserts a list of required substrings but not equality, so adding a host-mode usage line is safe. D-16 forbids a new help-equality check.

**Linking/dirty list:** the runner SOURCES list is a single file (`CMakeLists.txt:69`), so the D-04 "SOURCES subset of dirty list" check currently has one source; new runner-side sources (`src/host/*.c`) must be appended to the `git diff --quiet HEAD --` list at `CMakeLists.txt:85-88`.

---

#### `CMakeLists.txt` (modify: `gabbaboy_host` target, dirty list, install)

**Analog for the library target:** `gabbaboy_accept_bare` (`CMakeLists.txt:43-58`). It is the in-repo model of "compile helpers once, name no core, let the executable supply the core"; `verify-core-linkage.py` requires an acceptance-linked executable to name exactly one core archive exactly once.
```cmake
add_library(gabbaboy_accept_bare STATIC
  src/accept/sha256.c ...)
target_include_directories(gabbaboy_accept_bare PUBLIC
  "${CMAKE_CURRENT_SOURCE_DIR}/src/accept" "${CMAKE_CURRENT_SOURCE_DIR}/include")
target_compile_features(gabbaboy_accept_bare PUBLIC c_std_17)
set_target_properties(gabbaboy_accept_bare PROPERTIES C_EXTENSIONS OFF)
```
Mirror: `add_library(gabbaboy_host STATIC src/host/*.c)`, include dirs `src/host` + `include` only, `c_std_17`, `C_EXTENSIONS OFF`, **no** `GabbaBoy::core` link (the runner and `test_slots` link the core themselves). The root `CMakeLists.txt` is outside `tests/`, so the directory-scoped `include_directories("${PROJECT_SOURCE_DIR}/src/core")` at `tests/CMakeLists.txt:20` does not apply to `gabbaboy_host`: a stray `#include "gabbaboy_test.h"` would fail to compile there, which is a free guard. Tests must therefore **link** `gabbaboy_host`, not compile `src/host/*.c` directly into a `tests/` target, or that guard disappears.

**Dirty-list excerpt to extend** (`CMakeLists.txt:85-88`):
```cmake
execute_process(COMMAND git diff --quiet HEAD -- CMakeLists.txt include/gabbaboy/gabbaboy.h src/core/gabbaboy.c src/core/gabbaboy_test.h src/runner/main.c
    src/runner/acceptance.h src/runner/cases.c src/runner/acceptance.c
    src/accept/gbb_accept.h src/accept/sha256.c src/accept/input_script.c src/accept/stepper.c src/accept/predicate.c src/accept/digest.c
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}" RESULT_VARIABLE GABBABOY_SOURCE_DIRTY ERROR_QUIET)
```

**Windows link precedent:** `CMakeLists.txt:174-176` (`if(WIN32) target_link_libraries(measure_core PRIVATE Psapi)`).

**Install precedent for `share/gabbaboy/host-contract.json`** (`CMakeLists.txt:144-159`):
```cmake
install(FILES
  fixtures/mbc1-continuation/continuation.gb
  ...
  DESTINATION "${CMAKE_INSTALL_DATADIR}/gabbaboy/fixtures/mbc1-continuation")
```
Add `install(FILES docs/host-contract.json DESTINATION "${CMAKE_INSTALL_DATADIR}/gabbaboy")`.

---

### Group C. Input-clock getter (PLAY-01, plan 18-02)

#### `include/gabbaboy/gabbaboy.h` + `src/core/gabbaboy.c` (`gbb_get_input_clock`)

**Analog:** `gbb_info` / `gbb_get_info` / `info_store`.

Header shape (`gabbaboy.h:360-396`): a struct whose first field is `uint32_t struct_size`, a `GBB_..._SIZE_V1` macro, and a doc comment stating handshake and "Outputs are left unchanged on any error":
```c
typedef struct { uint32_t struct_size; /* IN: caller sets sizeof(...); OUT: bytes written */ ... } gbb_info;
#define GBB_INFO_SIZE_V1 28u   /* the core static-asserts this equals sizeof(gbb_info) */
...
gbb_error gbb_get_info(const gbb_instance *instance, gbb_info *out_info);
```
Core implementation (`gabbaboy.c:5439-5453`, plus the field-by-field store at 5385-5400, plus the static assert at line 474):
```c
/* MODEL: BOTH GATE-00 basis=host-api */
gbb_error gbb_get_info(const gbb_instance *instance, gbb_info *out_info) {
    if (instance == NULL || out_info == NULL || out_info->struct_size < GBB_INFO_SIZE_V1)
        return GBB_INVALID_ARGUMENT;
    gbb_info info = {0};
    ...
    info_store(out_info, &info);
    return GBB_OK;
}
static void info_store(gbb_info *out, const gbb_info *src) {
    /* Field by field, never a struct copy: the caller's struct may be larger than V1 and its
     * extra bytes stay untouched. */
    out->profile = src->profile;
    ...
    out->struct_size = GBB_INFO_SIZE_V1;
}
_Static_assert(sizeof(gbb_info) == GBB_INFO_SIZE_V1, "gbb_info layout");
```
Data source for the new getter: `instance->time_half_dots`, `instance->input_event_count`, and the last queued event `instance->input_events[count-1].at_half_dots` (the same fields `gbb_queue_events` reads at `gabbaboy.c:3969-3994`):
```c
uint64_t previous = instance->time_half_dots;
if (instance->input_event_count != 0)
    previous = instance->input_events[instance->input_event_count - 1].at_half_dots;
```
`last_queued_half_dots == now_half_dots` when the queue is empty. Required hygiene for any new top-level core function (RESEARCH Pattern 7): a `/* MODEL: BOTH GATE-00 basis=host-api */` tag directly above it (rule R1 of `tests/scripts/verify-model-gates.py`; GATE-00 is the shared id so no `docs/model-gates.md` row is needed), a `_Static_assert` for `GBB_INPUT_CLOCK_SIZE_V1 24`, and no new `GBB_HORIZON_GUARD` unless you add an arithmetic bound.

**Core test analog:** `tests/test_cgb_profile.c:134-143` and `276-306`: sentinel-filled struct, "too small" sizes `{0, 1, 27}` return `GBB_INVALID_ARGUMENT` and leave bytes untouched, exact size writes `struct_size == V1`, a larger struct keeps its trailing bytes.
```c
static void fill_info(gbb_info *info, uint32_t size) {
    memset(info, SENTINEL, sizeof(*info));
    info->struct_size = size;
}
static int info_untouched(const gbb_info *info, uint32_t size) { ... memcmp(info, &want, sizeof(want)) == 0; }
...
    static const uint32_t too_small[] = {0u, 1u, 27u};
    for (...) { fill_info(&info, too_small[i]); REQUIRE(CALL(&info) == GBB_INVALID_ARGUMENT); REQUIRE(info_untouched(&info, too_small[i])); }
    big_info big; memset(&big, SENTINEL, sizeof(big)); big.info.struct_size = (uint32_t)sizeof(big);
    REQUIRE(CALL(&big.info) == GBB_OK);
    for (size_t i = 0u; i < sizeof(big.extra); ++i) REQUIRE(big.extra[i] == SENTINEL);
```
Add the semantic cases (empty queue gives `last == now`, N queued events give `queued_count == N` and `last == final event`, NULL instance, after `gbb_load_state` of a later-time and an earlier-time state). Register it the way `battery_*` is (`tests/CMakeLists.txt:374-380`: one executable, `foreach(case ...)`, `add_test(NAME ... COMMAND test_x case)`), and add the names to `tests/expected-tests.txt`.

#### `tests/consumers/c/main.c` and `tests/consumers/cpp/main.cpp`

**Analog:** the existing `gbb_get_info` use (`c/main.c:313-320`) and the function-pointer reference pattern for state calls (`c/main.c:39-41`):
```c
static gbb_error (*const save_state_api)(const gbb_instance *, uint8_t *, size_t) = gbb_save_state;
...
    memset(&info, 0xA7, sizeof(info));
    info.struct_size = sizeof(gbb_info);
    if (gbb_get_info(machine, &info) != GBB_OK || info.mode != GBB_MODE_CGB ||
        info.profile != 2u || info.struct_size != GBB_INFO_SIZE_V1 ||
```
The Phase 11 symbol-presence check fails with `consumer-symbol-missing` unless the new symbol and macro appear in **both** consumer sources. Registration to copy (`tests/CMakeLists.txt:3438-3457`): a comma-separated symbol list passed to `tests/cgb_consumer_symbol_coverage.cmake`, plus a self-test that deletes one symbol from a copy and expects exit 1. Add `gbb_get_input_clock,gbb_input_clock,GBB_INPUT_CLOCK_SIZE_V1` as a new list/test pair (a new name, not an edit of the Phase 11 list).

---

### Group D. Slot engine and player integration

#### `src/player/slots.c/.h` (service, file-I/O + request-response)

**Analog for module shape and message table:** `src/player/catch_up_policy.h/.c`: pure, no SDL, caller supplies inputs, enum status + `*_format_status` that writes into `out/capacity` safely. The slot error-to-message map (D-25) should be a pure function in the same style, tested by iterating every enum value:
```c
void player_catch_up_format_status(enum player_catch_up_status status, int64_t delta,
                                   bool carry_became_set, bool halted,
                                   char *out, size_t capacity) {
    if (out == NULL || capacity == 0u) return;
    out[0] = '\0';
    switch (status) {
    case PLAYER_CATCH_UP_STATUS_NO_TIMESTAMP:
        snprintf(out, capacity, "Game clock not advanced: the save has no time stamp.");
        return;
```
**Registration analog for "SDL-free player file compiled into both the player library and a portable test":** `catch_up_policy.c` is listed in `gabbaboy-player-adapter` (`CMakeLists.txt:105-111`) and compiled straight into a portable test (`tests/CMakeLists.txt:188-194`):
```cmake
add_executable(test_catch_up_policy test_catch_up_policy.c
  "${PROJECT_SOURCE_DIR}/src/player/catch_up_policy.c")
target_include_directories(test_catch_up_policy PRIVATE "${PROJECT_SOURCE_DIR}/src/player")
target_compile_features(test_catch_up_policy PRIVATE c_std_17)
set_target_properties(test_catch_up_policy PROPERTIES C_EXTENSIONS OFF)
add_test(NAME catch_up_policy_table COMMAND test_catch_up_policy catch_up_policy_table)
```
Do the same for `slots.c`, linking `GabbaBoy::core` and `gabbaboy_host`. The player-adapter library target (`CMakeLists.txt:105`) gets `src/player/slots.c` added to its sources and `gabbaboy_host` to its link line.

**Slot file names** (D-22) follow `battery_file_path` (`session.c:416-422`): hex-encode `rom_sha256` the same way, then append `-<dmg|cgb>-slot<N>.gbbs` etc. Nothing user-controlled.
```c
    char digest[65];
    static const char hex[] = "0123456789abcdef";
    for (size_t i = 0u; i < sizeof(identity->rom_sha256); ++i) {
        digest[i * 2u] = hex[identity->rom_sha256[i] >> 4];
        digest[i * 2u + 1u] = hex[identity->rom_sha256[i] & 0x0Fu];
    }
    digest[64] = '\0';
```
The slot engine must take the 32-byte digest (or the hex string) as an argument; `session.c` hashes with CommonCrypto (`session.c:5`), which is macOS-only, and `gbb_accept_sha256_*` lives in `gbb_accept.h` which D-04 bans from slot code.

**Pref directory and test isolation:** `battery_file_path` (`session.c:387-451`) shows the pattern: `SDL_GetPrefPath("GabbaBoy","GabbaBoy")` in production, `test_pref_path` override under `GBB_PLAYER_SESSION_TESTING`. The slot engine receives the already-open `dirfd`; the player side opens it from `SDL_GetPrefPath` (or `player_session_test_set_pref_path`).

**Read and refusal semantics:** same bounded-read pattern as host_save_io above (`read_save_file`, `session.c:460-509`); cap at `gbb_state_size(live)+1`.

**Hostile-file test patterns** (for `tests/test_slots.c`): `tests/player/test_session.c:840-926` builds each hostile target in a temp dir and asserts "refused AND the target is untouched", using `symlink`, `mkfifo`, `lstat`:
```c
    REQUIRE(unlink(path) == 0);
    REQUIRE(mkfifo(path, 0600) == 0);
    REQUIRE(!player_session_load_battery(machine, &identity, error, sizeof(error)));
    REQUIRE(!identity.persistence_enabled);
    REQUIRE(battery_matches(machine, initial, sizeof(initial)));
    struct stat info;
    REQUIRE(lstat(path, &info) == 0 && S_ISFIFO(info.st_mode));
    REQUIRE(count_recovery_files(root) == 0u);
```
Copy the helpers `path_join` and `remove_tree` (`test_session.c:193-215`, duplicated in `test_continuation.c:35-65`; the repo copies rather than shares them). Use `mkdtemp` (`tests/player/test_reset_transition.c:103,128`). Note `test_session.c` includes `<CommonCrypto/CommonDigest.h>`: the portable `tests/test_slots.c` cannot, so hash files with `gbb_accept_sha256_hex` (`src/accept/gbb_accept.h:38`, linked through `gabbaboy_accept`) for the "SHA-256 of slot/undo/preload/`.gbb` unchanged" assertion.

**Order-mutant test:** copy the `gbb_state_refusal_mutant` factory (`tests/CMakeLists.txt:5389-5415`): write a mutated copy of the source with an anchor that must occur exactly once, build it into its own executable, expect exit 1 + a failure regex, and register a `_control` test that must exit 0. Use it for "undo written before `gbb_load_state`" and "no rebase".
```cmake
function(gbb_state_refusal_mutant name anchor replacement)
  set(text "${gbb_state_internal_core_text}")
  string(FIND "${text}" "${anchor}" first)
  string(FIND "${text}" "${anchor}" last REVERSE)
  if(first EQUAL -1 OR NOT first EQUAL last)
    message(FATAL_ERROR "State refusal mutant ${name}: anchor must occur exactly once (first=${first}, last=${last})")
  endif()
  ...
  add_test(NAME state_refusal_mutant_${name}
    COMMAND ${CMAKE_COMMAND} "-DGBB_CMD=$<TARGET_FILE:${target}>;state_refusal"
      -DGBB_EXPECT_CODE=1 "-DGBB_EXPECT_REGEX=FAIL state_refusal"
      -P "${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake")
  add_test(NAME state_refusal_mutant_${name}_control ... -DGBB_EXPECT_CODE=0 ...)
```
The player directory has its own factory for mutating player sources, `gbb_player_mutate_source` (`tests/player/CMakeLists.txt:10-23`), same exactly-once rule.

---

#### `src/player/input.c/.h` (modify: re-anchor helper)

**Analog:** the same file. A post-load re-anchor is `player_input_reset` plus a cursor/pending seed, so build it from the same primitives and keep the existing guards:
```c
void player_input_reset(player_input_state *state, uint64_t host_now_ns) {
    if (state == NULL) return;
    memset(state, 0, sizeof(*state));
    state->host_anchor_ns = host_now_ns;
}
void player_input_reconcile(player_input_state *state, uint64_t guest_cursor_half_dots) {
    if (state == NULL || guest_cursor_half_dots < state->guest_cursor_half_dots)
        return;   /* NOTE: refuses to move the cursor backwards */
```
**Hazard:** `player_input_reconcile` returns early when the new cursor is *smaller* than the stored one. Loading an earlier-time state therefore cannot use it; the re-anchor must set `guest_cursor_half_dots` and `guest_anchor_half_dots` directly (D-24: "set the cursor and anchor to `now`"). That is the case the required "earlier-time state" test (D-26 item 7) and its "no rebase" mutant guard.

Scheduling code the re-anchor must stay consistent with (`input.c:110-119`, `121-132`):
```c
static bool schedule_time(const player_input_state *state, uint64_t host_timestamp_ns, uint64_t *out_guest_half_dots) {
    if (!map_host_time(state, host_timestamp_ns, out_guest_half_dots)) return false;
    if (state->pending_count > 0) {
        const uint64_t last = state->pending[state->pending_count - 1].at_half_dots;
        if (*out_guest_half_dots < last) *out_guest_half_dots = last;
    }
    return true;
}
```
`pending[]` is mirrored in the player (`input.h:28`, capacity `PLAYER_INPUT_QUEUE_CAPACITY 64u` at `input.h:12`), so seed `pending_count` from `queued_count`; the core's own capacity constant is private (`GBB_INPUT_EVENT_CAPACITY`, `gabbaboy.c:128`).

---

#### `src/player/main.c` (modify: keys, status line, help)

**Analog:** the same file.

Key handler insertion point and the existing bare-key branches that need a `!command` guard (`main.c:1384-1424`):
```c
    if (pressed && !key->repeat) {
        const bool command = (key->mod & SDL_KMOD_GUI) != 0;
        if (command && key->key == SDLK_Q) { request_quit(app); return; }
        if (!app->dialog_pending && command && key->key == SDLK_O) { request_open_rom(app); return; }
        ...
        if (!app->dialog_pending && key->scancode == SDL_SCANCODE_R) {
            begin_transition(app, PLAYER_TRANSITION_RESET, NULL);
            return;
        }
        if (!app->dialog_pending && key->scancode == SDL_SCANCODE_S) {
            if (!app->save_identity.battery_backed)
                set_status(app, "This ROM has no battery-backed RAM");
            else
                (void)attempt_battery_save(app, true);
            return;
        }
    }
    const gbb_error result = player_input_key(...);
```
Note `handle_key` early-returns while `app->pending_transition != PLAYER_TRANSITION_NONE` (lines 1358-1383): the "ignored while a transition is pending" rule is already satisfied by placing slot branches after that block. `dialog_pending` is checked per branch; copy that idiom. The ⌘Z keydown must be consumed (`return`) before it reaches `player_input_key`, which maps `SDL_SCANCODE_Z` to button A (`input.c:102`); the later Z key-up still reaches `player_input_key` and must be harmless (release of an unpressed button).

Status/title plumbing (`main.c:766-791`): the title is rebuilt on every `set_status`; `app->save_status_active ? app->save_status : status`. D-25's `<save_status> · <slot message>` combination belongs in a small formatter next to `format_window_title`.
```c
static void set_status(player *app, const char *status) {
    (void)snprintf(app->status, sizeof(app->status), "%s", status);
    update_window_title(app);
}
```
`status[192]` and `save_status[192]` are fixed buffers (`main.c:81-82`); size the combined line accordingly.

Post-load recovery sequence to mirror (`reset_session`, `main.c:955-976`): clear audio, re-anchor input, force a redraw, reset the displayed generation and the save cadence:
```c
    const bool audio_cleared = player_audio_clear(app->audio);
    app->user_paused = false;                         /* slots must NOT do this: pause is kept across a load (D-21) */
    player_input_reset(&app->input, SDL_GetTicksNS());
    if (!app->window_focused || app->dialog_pending)
        player_input_pause(&app->input);
    app->displayed_generation = 0;
    app->needs_redraw = true;
    ...
    player_save_cadence_reset(&app->save_cadence, generation);
```
Also reset the `.gbb` save cadence after a load (the battery contents changed): this is a gap not stated in D-23, worth a plan-level check.

Help dialog (`show_help`, `main.c:793-832`): the message is an `snprintf` into `char message[4096]` ending with `GBB_PLAYER_LIMITATIONS_TEXT`. Add the slot lines near `"Reset current ROM: R\nSave battery RAM now ...: S\n"`. D-25 requires the exact sentence `Saving replaces the slot. Loading also replaces the game's battery save; ⌘Z undoes the last load.` Check the 4096-byte budget after adding it.

---

#### `tests/player/test_slots.c` (macOS key-decoder and event-pump test) and registration

**Analog:** `tests/player/test_reset_transition.c`. It embeds `main.c` so static functions are reachable, drives keys through the real event queue, and isolates saves via `player_session_test_set_pref_path`:
```c
#define main gabbaboy_player_embedded_main
#include "../../src/player/main.c"
#undef main
...
    player app = {0};
    app.save_lock_fd = -1;
    app.running = true;
    app.window_focused = true;
    app.skip_final_save = true;
    ...
    if (!push_key(&app, SDL_EVENT_KEY_DOWN, SDL_SCANCODE_SPACE, SDL_GetTicksNS()) || !pump_events(&app) ||
        !app.user_paused || ...
...
    root = mkdtemp(root_template);   /* "/tmp/gabbaboy-reset-transition-XXXXXX" */
    player_session_test_set_pref_path(root);
```
`push_key` (`main.c:1601-1611`) sets only `scancode` and `down`, not `event.key.mod` or `event.key.key`. A GUI-modified key test (⌘S, ⌘R, ⌘Z) needs `mod = SDL_KMOD_GUI` and `key = SDLK_S` etc. set on the event, so either extend `push_key` with a modifiers argument or add a sibling helper in `main.c`. `handle_key` reads `key->mod` and `key->key` for ⌘Q/⌘O but `key->scancode` for R/S, so the decoder must say which field it reads for each key.

Player-suite CMake registration (`tests/player/CMakeLists.txt:371-391`):
```cmake
  elseif(test_name STREQUAL "player_reset_transition")
    add_executable(test_player_reset_transition
      test_reset_transition.c
      "${PROJECT_SOURCE_DIR}/src/player/audio.c" ... "${PROJECT_SOURCE_DIR}/src/player/script_smoke.c")
    target_link_libraries(test_player_reset_transition PRIVATE gabbaboy-player-session-test gabbaboy_accept)
    target_compile_definitions(test_player_reset_transition PRIVATE
      GBB_PLAYER_AUDIO_TESTING GBB_PLAYER_SESSION_TESTING
      GABBABOY_PLAYER_DEMO_ROM="..." GABBABOY_PLAYER_INVALID_ROM="...")
    add_test(NAME player_reset_transition COMMAND test_player_reset_transition)
    set_tests_properties(player_reset_transition PROPERTIES ENVIRONMENT "SDL_AUDIO_DRIVER=dummy")
```
Add a branch for each new name, list the names in `tests/player/expected-tests.txt` (a **different** file from `tests/expected-tests.txt`), and remember the chain ends in `message(FATAL_ERROR "Unknown optional player test in inventory: ...")` (line 482), so a name added to the inventory without a branch fails configure.

`player_slot_key_action(...)` (pure decoder, D-21) belongs in a small SDL-types-only file or in `slots.h` and should be unit-tested without a window; the embedded-`main.c` test then covers wiring only.

---

#### `src/player/limitations.h` and `tests/player/test_limitations.c`

**Analog:** themselves. `GBB_PLAYER_LIMITATIONS_TEXT` is one long string literal (`limitations.h:4-5`) and the test duplicates the full literal and compares with `strcmp` (`test_limitations.c:6-12`). Any edit changes both files in one commit. The same string is read by `tests/scripts/verify-phase8-player-contract.py:129-210`, `tests/player/claims_agree.cmake` (phrases across `README.md`, `limitations.h` and `.github/workflows/preview.yml`), and the CGB claim checkers. D-27 forbids release-workflow edits, so only add wording that does not require a new `claims_agree` phrase (RESEARCH Pitfall 5), and grep every consumer of the string before editing. Avoid "no double speed" phrasing (`check_no_stale_speed_claims.cmake` scans these files).

---

### Group E. Tests, checkers and harness

#### `tests/test_host_cadence.c`, `tests/test_host_basename.c` (pure unit tests)

**Analog:** `tests/test_catch_up_policy.c`. Shape to copy: one `REQUIRE` macro that prints `file:line: expr` and returns 1, a `check(...)` helper that asserts a whole decision struct, a table of boundary values including extremes, and a `main` that dispatches on `argv[1]`:
```c
#define REQUIRE(x) do { if (!(x)) { \
    fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #x); return 1; \
} } while (0)

static int check(int64_t saved, bool saved_ok, int64_t now, bool now_ok,
                 enum player_catch_up_action action, enum player_catch_up_status status,
                 int64_t delta) {
    const struct player_catch_up_decision d = player_catch_up_policy(saved, saved_ok, now, now_ok);
    REQUIRE(d.action == action);
    ...
```
Use boundary pairs for 15/16/17 quiet frames, 299/300/301 age, 3,599/3,600/3,601 drift, generation `!=` vs `>` (including a wrap/decrease). Register with the `add_executable(... src/host/host_cadence.c)` + `add_test` block copied from lines 188-194 shown above.

#### `tests/test_host_save_io.c`

**Analogs:** `tests/test_battery.c` (public-API ROM/battery fixtures: `fix_checksum`, `make_rom`, `fill_pattern`) and `tests/player/test_session.c` (temp dir, hostile files, fault stages). Header-valid ROM generator to reuse verbatim (`test_battery.c:11-28`):
```c
static void fix_checksum(uint8_t *rom) {
    uint8_t checksum = 0u;
    for (size_t i = 0x134u; i <= 0x14Cu; ++i)
        checksum = (uint8_t)(checksum - rom[i] - 1u);
    rom[0x14Du] = checksum;
}
static uint8_t *make_rom(uint8_t rom_code, uint8_t type, uint8_t ram_code, size_t *out_size) {
    *out_size = (size_t)32768u << rom_code;
    uint8_t *rom = calloc(*out_size, 1u);
    if (rom == NULL) return NULL;
    rom[0x147u] = type;
    rom[0x148u] = rom_code;
    rom[0x149u] = ram_code;
    fix_checksum(rom);
    return rom;
}
```
Per-test dispatch style (`test_battery.c:240-251`): `main(argc, argv)` returns 2 for an unknown case; each case name becomes a CTest name via `foreach(case ...) add_test(NAME battery_${case} COMMAND test_battery battery_${case})` (`tests/CMakeLists.txt:378-380`).

For the hostile-file sweep (D-30: sizes 0, N-1, N, N+1, 8 MiB+1; FIFO, directory, device, symlink), `tests/player/test_session.c` already has `write_sized_file` (line 49), `write_oversized_file`, `write_truncated_file`, and the symlink/FIFO assertions. Add a separate expectation per negative with its own reason token (GB-GSD-029), not one shared `exit 2` check.

#### `tests/test_save_format_completeness.c` (in-process completeness enumeration, D-20)

**Analog:** `tests/test_loader_matrix.c:299-332` `loader_type_byte_sweep`: iterate all 256 type bytes, derive expected acceptance from an oracle table, load each and compare, then check the accepted set both ways (every accepted type seen, nothing unexpected):
```c
    int seen[256] = {0};
    for (unsigned type = 0u; type < 256u; ++type) {
        ...
        if (got == GBB_OK) seen[type] = 1;
    }
    for (unsigned type = 0u; type < 256u; ++type) {
        int in_set = 0;
        for (size_t i = 0u; i < sizeof(accepted); ++i) in_set |= accepted[i] == type;
        if (seen[type] != in_set) { fprintf(stderr, "accepted-set mismatch at type %02X ...", ...); return 1; }
    }
```
Extend to type x RAM code `00..06` x ROM code, using `gbb_probe_rom` (`GBB_INFO_HAS_BATTERY`, `GBB_INFO_HAS_RTC`, `ram_size_bytes`) then `gbb_load_rom` + `gbb_battery_size`. Build ROMs with the `make_rom` above. Assert `$10/$05` is **not** admitted (`GBB_UNSUPPORTED_CARTRIDGE_VARIANT`, MBC30). Link only `GabbaBoy::core` and `gabbaboy_host` (for the table).

#### `tests/scripts/verify-save-formats.py` and `tests/scripts/verify-host-contract.py` (checkers with seeded controls)

**Analog:** `tests/scripts/verify-v03-dispositions.py` (and the same family: `verify-closeout-dispositions.py`). It already contains every convention these checkers need.

Module shape: docstring that states inputs and modes; `from __future__ import annotations`; a refusal to run under `python -O`; an exact-set requirement table; a `Reject(code, message)` exception; a `Source` class that reads from the working tree or `git show REV:<path>`:
```python
if not __debug__:
    raise SystemExit("verify-v03-dispositions refuses to run under python -O (its asserts and checks must stay on)")
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")

class Reject(Exception):
    def __init__(self, code: str, message: str) -> None: ...

class Source:
    """Reads a path from the working tree, or from one commit with `git show REV:<path>` (never both)."""
    def read(self, path: str, code: str = "receipt-missing") -> bytes:
        relative = self.relative(path)
        if self.rev is not None:
            done = subprocess.run(["git", "-C", str(self.repo), "show", f"{self.rev}:{relative}"], capture_output=True, check=False)
            if done.returncode != 0:
                reject(code, f"{relative} is not present at {self.rev}")
```
The strict `TAG` regex is the freeze-baseline selector the RESEARCH recommends (local tags include a stray `v0.2`). For "latest tag" use `git tag --list` filtered by `TAG` and a numeric sort; there is no existing helper that does this (the closest is the `TAG` constant above).

Self-test shape: a throwaway git repo built in a temp dir with a fixed identity, `git(repo, ...)` helper with `-c user.name=fixture ... commit.gpgsign=false core.hooksPath=/dev/null`, a `run_cli` that re-invokes the script with `python -I`, and `expect_pass` / `expect_reject` that count controls and require `REJECT <code>:` on stderr, so a control fails for its own named reason:
```python
def git(repo, *args):
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                           "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                          capture_output=True, text=True, check=True)
...
def run_cli(repo, *args):
    return subprocess.run([sys.executable, "-I", str(SCRIPT), "--repo", str(repo), *args], capture_output=True, text=True, timeout=120, check=False)

        def expect_reject(label, result, code):
            nonlocal controls
            if result.returncode == 0 or "v03-dispositions pass" in result.stdout:
                raise SystemExit(f"self-test accepted {label}")
            if f"REJECT {code}:" not in result.stderr:
                raise SystemExit(f"self-test {label}: expected REJECT {code}, got: {result.stderr.strip()[:240]}")
            controls += 1
```
Final line and `main()`:
```python
    print(f"v03-dispositions self-test pass controls={controls}")
...
    except Reject as error:
        print(f"REJECT {error.code}: {error.message}", file=sys.stderr)
        return 1
```
Seeded controls required by D-20 (each its own `REJECT` code): `$10/$03`=32,816; changed id; deleted row; MBC30 `$10/$05` admitted; release-versioned or uppercase id; `bytes != ram+rtc`; one id two sizes; 1-byte-short file shim; cgb-profile id shim; freeze mismatch; non-canonical JSON; `$1A` file shim.

CTest registration analog (`tests/CMakeLists.txt:1556-1571`): one `--check` test and one `--self-test` test, each through `expect_exit.cmake` with `-DGBB_EXPECT_REGEX` on the exact success line and `GBB_EXPECT_MIN_KEY/VALUE` for a nonzero count:
```cmake
add_test(NAME v03_dispositions_controls
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${Python3_EXECUTABLE};-I;${PROJECT_SOURCE_DIR}/tests/scripts/verify-v03-dispositions.py;--self-test"
    -DGBB_EXPECT_CODE=0
    "-DGBB_EXPECT_REGEX=v03-dispositions self-test pass controls=[0-9]+"
    -DGBB_EXPECT_MIN_KEY=controls -DGBB_EXPECT_MIN_VALUE=10
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
set_tests_properties(v03_dispositions_controls PROPERTIES TIMEOUT 60 LABELS "planning")
```
**Python `-I` gotcha:** with `-I` the script directory is not on `sys.path`, so a helper module beside the script cannot be imported by name (`tests/scripts/test_verified_player_output_dir.py:19` does `import verified_player_output_dir`, but it is registered **without** `-I`, `tests/player/CMakeLists.txt:477-480`). If the ROM generator is shared between `verify-save-formats.py` and `test_host_signals.py`, load it with `importlib.util.spec_from_file_location` (precedent: `tests/scripts/test-cgb-corpus-report.py:26-28`, `test_hdma_remote_evidence.py:28`) or keep it inside one script and have the other call it as a subprocess.

#### `tests/scripts/test_host_signals.py` (real-signal harness, D-17)

**Analog:** `tests/scripts/verify-v02-consumers.py:55-142` (bounded subprocess handling), the only tracked code that starts a process in its own session and signals it.
```python
        process = subprocess.Popen(
            command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
            start_new_session=(os.name != "nt"),
        )
        ...
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            terminate_process(process)
            process.communicate()
...
def terminate_process(process, *, force=False):
    if process.poll() is not None:
        return
    try:
        if os.name == "nt": ...
        else:
            os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        pass
```
Differences for the host harness: signal the **child pid directly** (`p.send_signal(...)`) not the process group; read the `gbb-host: ready` line from stderr with a watchdog instead of `communicate()`; reset the harness's own SIGINT/SIGHUP to `SIG_DFL` before `Popen` (and add the inherited-`SIG_IGN` row); keep POSIX-only (`os.name != "nt"` must skip with a clear message, or the test is excluded from the Windows inventory). Each negative-control decoy runner (no flush on SIGTERM, partial-frame flush, exit 0 after failed flush, in-place write) can be a small C shim or a mutant runner built with the `gbb_player_mutate_source`-style anchor discipline; keep decoys build-tree-only and out of installed targets (D-17: no crash backdoor in shipped binaries).

Registration conventions in this repo: `Python3_EXECUTABLE -I script`, an explicit `TIMEOUT`, and (per RESEARCH F15/Pattern 8) `PROCESSORS` or a `RESOURCE_LOCK` because CI runs ctest 4-wide. Both properties have precedent: `tests/CMakeLists.txt:5277-5279` reserves slots for a worker pool (`set_tests_properties(state_horizon_mutants PROPERTIES PROCESSORS 4)` with the comment "reserve that many slots so a parallel ctest does not oversubscribe the runner"), and `tests/acceptance/CMakeLists.txt:407,415` serialises build-tree-touching tests with `RESOURCE_LOCK gbb_build_tree`.

#### `cmake/CheckHostApiSymbols.cmake`, `cmake/CheckRunnerSourcesQualified.cmake`, and the `CheckCoreNoHostClock.cmake` extension

**Analog:** `cmake/CheckCoreNoHostClock.cmake`. It is an `nm`/`llvm-nm`/`dumpbin` undefined-symbol reader with a source layer and an object layer, `-D` inputs, a `GBB_SYMBOLS_FILE` injection for selftests, `message(STATUS "no-host-clock-...: ...")` failure tokens, and one success line. Reuse `gbb_read_undefined_symbols` and `gbb_parse_nm` (lines 144-221) verbatim for `CheckHostApiSymbols.cmake` (copy the functions; the repo duplicates rather than `include`s across checkers). Change: instead of a deny-list, compare each undefined `gbb_*` name to the set of `gbb_*` function names declared in `include/gabbaboy/gabbaboy.h`; any `gbb_*` symbol not declared there (a `gbb_test_*` seam) fails.

D-18 extension points in `CheckCoreNoHostClock.cmake` (lines 32-50), add the signal names to **both** lists, then add one more seeded selftest:
```cmake
set(gbb_allowed_includes "<stddef.h>" "<stdint.h>" "<stdlib.h>" "<string.h>"
  "\"gabbaboy/gabbaboy.h\"" "\"gabbaboy_test.h\"" "\"gbb_accept_input.h\"")
set(gbb_denied_calls
  time clock clock_gettime gettimeofday timespec_get localtime gmtime mktime difftime
  nanosleep usleep sleep getenv QueryPerformanceCounter QueryPerformanceFrequency
  GetLocalTime mach_absolute_time __rdtsc)
...
set(gbb_denied_symbols
  time _time32 _time64 clock clock_gettime gettimeofday timespec_get localtime localtime_r
  localtime_s gmtime gmtime_r mktime difftime nanosleep usleep sleep getenv
  QueryPerformanceCounter GetSystemTimeAsFileTime GetTickCount GetTickCount64 GetLocalTime
  mach_absolute_time __rdtsc)
```
append `signal sigaction raise kill sigprocmask pthread_sigmask alarm setitimer`. The four-header allowlist already rejects `<signal.h>`. Because the source layer uses a `(^|[^A-Za-z0-9_])name[ \t]*\(` match, `raise` and `kill` are generic English-ish identifiers: RESEARCH F12 confirms no current core match, but re-run `no_host_clock` after the edit to prove no false positive (e.g. a core function named `...kill(`).

Negative-control registration pattern to copy (`tests/CMakeLists.txt:2371-2415`): write a scratch `bad.c` under `${PROJECT_BINARY_DIR}`, invoke the script through `expect_exit.cmake` with `GBB_EXPECT_CODE=1` and a regex on the exact failure token:
```cmake
file(WRITE "${PROJECT_BINARY_DIR}/no-host-clock-selftest/bad.c"
  "#include <time.h>\nint host_seconds(void) { return (int)time(NULL); }\n")
add_test(NAME no_host_clock_selftest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=${CMAKE_COMMAND};-DGBB_SOURCE_DIRS=${PROJECT_BINARY_DIR}/no-host-clock-selftest;-DGBB_SYMBOLS_FILE=;-P;${GBB_NO_HOST_CLOCK_SCRIPT}"
    -DGBB_EXPECT_CODE=1
    -DGBB_EXPECT_REGEX=no-host-clock-include
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
```
D-18 asks for the seeded signal control to be "compiled with the project's real strict-C17 flags", so it must be an actual object (an `add_library(OBJECT)`/`add_library(STATIC)` of the seeded source whose undefined symbols feed the object layer), not just the `GBB_SYMBOLS_FILE` text injection used by `no_host_clock_symbol_selftest`.

---

### Group F. Docs, installed smoke and inventories

#### `docs/host-contract.json`

**Partial analog:** `fixtures/mbc1-continuation/manifest.json`: hand-written, 2-space indent, trailing newline, `"key": value` objects. The canonical-form rule (D-16) is `json.dumps(json.loads(text), indent=2, ensure_ascii=True) + "\n" == text` with key order preserved. Note other checkers in this repo use `sort_keys=True` (`verify-cgb-corpus-artifacts.py:99`, `verify-closeout-scan.py:342`); this one must NOT sort, because the contract is hand-ordered and the checker compares against the raw bytes.

#### `cmake/VerifyInstalledHostMode.cmake` and `installed_host_smoke`

**Analog:** `cmake/VerifyInstalledPackage.cmake`. Same inputs (`GBB_INSTALL_PREFIX`, `GBB_EXECUTABLE_SUFFIX`, `GBB_RUNNER_WORKDIR`), same "required installed files" loop, and the same relocation proof (run from an unrelated working directory via `cmake -E chdir`):
```cmake
  execute_process(
    COMMAND "${CMAKE_COMMAND}" -E chdir "${runner_workdir}"
      "${runner}" "${fixture_dir}/tracer.gb"
    RESULT_VARIABLE runner_result OUTPUT_VARIABLE runner_output ERROR_VARIABLE runner_error)
  if(NOT runner_result EQUAL 0 OR NOT runner_output MATCHES "outcome=pass" OR ...)
    message(FATAL_ERROR "Installed runner failed from unrelated working directory (${runner_result}): ${runner_output}${runner_error}")
```
Test registration (`tests/CMakeLists.txt:1870-1878`), gated on `GBB_TEST_INSTALL_PREFIX`:
```cmake
if(GBB_TEST_INSTALL_PREFIX AND EXISTS "${GBB_TEST_INSTALL_PREFIX}")
  ...
  add_test(NAME installed_runner_smoke
    COMMAND ${CMAKE_COMMAND}
      -DGBB_INSTALL_PREFIX=${GBB_TEST_INSTALL_PREFIX_ABSOLUTE}
      -DGBB_EXECUTABLE_SUFFIX=${CMAKE_EXECUTABLE_SUFFIX}
      -DGBB_RUNNER_WORKDIR=${PROJECT_BINARY_DIR}/installed-runner-cwd
      -P ${PROJECT_SOURCE_DIR}/cmake/VerifyInstalledPackage.cmake)
```
**Inventory trap:** name the test `installed_host_smoke` so it is covered by the existing `sed '/^installed_/d'` in `verify-test-inventory.sh:164` for `--core-only` runs, **and** add it to the `list(REMOVE_ITEM expected_tests installed_runner_smoke installed_consumer_c ...)` in `cmake/ExpectedTests.cmake:12-15` (otherwise configure fails when no install prefix is set). It is also POSIX-only (host mode on Windows is a refusal), so the Windows exclusion applies in both inventories too. The smoke needs a generated ROM or the already installed `fixtures/mbc1-continuation/continuation.gb` (CMakeLists install lines 154-159); RESEARCH Pattern 10 recommends an SRAM counter fixture whose persisted byte depends on the previous run's byte, with a wrong-preloaded-save control.

#### Inventories (`cmake/ExpectedTests.cmake`, `.github/scripts/verify-test-inventory.sh`, `tests/expected-tests.txt`, `tests/player/expected-tests.txt`)

**Analog:** themselves; GB-CGB-007 requires the same name list in **two** places. `cmake/ExpectedTests.cmake:16-26`:
```cmake
  if(WIN32)
    # The A/B benchmark harness is a bash script (Plan 10-17).
    list(REMOVE_ITEM expected_tests cgb_bench_ab_selftest ... core_linkage_links core_linkage_controls
      release_lifecycle_replay release_lifecycle_controls
      perf_advisory_pipeline perf_advisory_controls)
  endif()
```
`verify-test-inventory.sh` carries the same names three times: the `sed -e '/^name$/d'` block (lines 11-30), the seed list in `_self_test_platform_filter_cases` (lines 39-59) and the "must be removed" loop (lines 68-86). Add each new POSIX-only name (host file-producing tests, signal harness, slot file tests that link the dir-fd writer, `installed_host_smoke`) to all four places, then run `bash .github/scripts/verify-test-inventory.sh --self-test`. A new test that only exists under `if(NOT WIN32)` follows the pattern at `tests/CMakeLists.txt:1520-1536` (`core_linkage_*`).

Per GB-CART-003, plans that edit `tests/expected-tests.txt` / `tests/CMakeLists.txt` must run serially. Plan 18-01 and 18-02 are marked parallel in D-31 but both append to these two files; RESEARCH Pitfall 1 recommends serialising them.

`tests/CMakeLists.txt:2898-2903` already handles partial Windows inventories for `test_budget` (`--partial-inventory`); new POSIX-only tests do not need a separate budget edit, but run `test_budget` after adding timeouts.

#### Docs (`docs/native-integration.md`, `docs/cartridge-and-saves.md`, `README.md`, `docs/support/unreleased.md`, `PLAYSTEAD-CONTRACT.md`)

**Analog:** the existing RTC guide contract. A phrase list plus a scope paragraph, checked by `cmake/VerifyDocContract.cmake` (`tests/CMakeLists.txt:2438-2460`):
```cmake
set(GBB_DOC_CONTRACT_SCRIPT "${PROJECT_SOURCE_DIR}/cmake/VerifyDocContract.cmake")
set(GBB_NATIVE_GUIDE_RTC_PHRASES
  "`gbb_rtc_catch_up` applies host wall-clock time"
  ...
add_test(NAME native_guide_rtc_contract
  COMMAND ${CMAKE_COMMAND}
    -DGBB_DOC=${PROJECT_SOURCE_DIR}/docs/native-integration.md
    "-DGBB_DECLARATIONS=${PROJECT_SOURCE_DIR}/include/gabbaboy/gabbaboy.h;${PROJECT_SOURCE_DIR}/examples/relocated-c/CMakeLists.txt"
    "-DGBB_REQUIRED=${GBB_NATIVE_GUIDE_RTC_PHRASES}"
    "-DGBB_SCOPE_START=`gbb_rtc_catch_up` applies host wall-clock time"
    -P ${GBB_DOC_CONTRACT_SCRIPT})
set_tests_properties(native_guide_rtc_contract PROPERTIES
  PASS_REGULAR_EXPRESSION "doc-contract pass identifiers=[1-9][0-9]* phrases=12[^0-9]")
```
Controls to mirror: `doc_contract_missing_selftest` (phrase removed copy) at lines 2476-2483. Constraint: every `gbb_*`/`GBB_*` token in `native-integration.md` must be declared in `gabbaboy.h` (`doc-contract-undeclared`), so the Host process contract section cannot name `GBB_MAX_ROM_SIZE` or `GBB_INPUT_EVENT_CAPACITY` (core-private); write "8 MiB". `gbb_get_input_clock` is usable only after the header declares it (18-02 first). The doc tables for exit codes and save formats should be checked against `docs/host-contract.json` by `verify-host-contract.py` rather than hand-synced.

The `docs/support/unreleased.md` entries follow its stated rule (lines 3-6): "Add future pending evidence here only with its source, model, execution mode, rights, result disposition, and intended versioned-ledger destination". Destination for Phase 18: v0.3.0.

`PLAYSTEAD-CONTRACT.md` correction (line 107): replace "Non-RTC SRAM is byte-identical to mGBA and can be documented as such." with the MBC2 exception (256 vs 512 B), per D-19.

---

## Shared Patterns

### Public-API-only boundary
**Source:** `src/accept/gbb_accept.h` and `src/core/gabbaboy_test.h` are what the runner includes today (`src/runner/main.c:1-4`); host and slot code must include only `gabbaboy/gabbaboy.h` and libc/POSIX.
**Apply to:** every `src/host/*` and `src/player/slots.*` file.
```c
#include "gabbaboy/gabbaboy.h"
#include "gbb_accept.h"                 /* NOT for host/slot code */
#include "acceptance.h"                 /* NOT for host/slot code */
#include "../core/gabbaboy_test.h"      /* NOT for host/slot code */
```
Enforced by the new `CheckHostApiSymbols.cmake` (undefined `gbb_*` symbols vs the public header, plus an include scan, RESEARCH Pitfall 10).

### POSIX feature macros under `C_EXTENSIONS OFF`
**Source:** `tests/measure_core.c:1-13` (see the host_save_io section). **Apply to:** every POSIX `.c` in `src/host`, `src/player/slots.c`, and any new POSIX-using test `.c`. Not in `.h` files.

### Exact-exit-code negative controls
**Source:** `tests/expect_exit.cmake` (header lines 1-18 and the check at 39-48). **Apply to:** every CLI negative and every checker `--self-test`. Exit code must equal `GBB_EXPECT_CODE` exactly (a signal or "Child aborted" never equals a decimal), and the combined output must match `GBB_EXPECT_REGEX`; add `GBB_FORBID_REGEX` to prove a different reason did not fire; `GBB_EXPECT_MIN_KEY/VALUE` requires exactly one `KEY=<digits>` token and a minimum (use it for `bytes=` from `--print-save-format`).
```cmake
add_test(NAME cgb_mooneye_unknown_manifest
  COMMAND ${CMAKE_COMMAND}
    "-DGBB_CMD=$<TARGET_FILE:gabbaboy-runner>;--manifest;...;--suite"
    -DGBB_EXPECT_CODE=2
    -DGBB_EXPECT_REGEX=invalid-manifest
    -P ${PROJECT_SOURCE_DIR}/tests/expect_exit.cmake)
```
`GBB_EXPECT_FILE`, `GBB_EXPECT_FILE_SIZE` and `GBB_EXPECT_FILE_FRESH` exist for "the `.sav` is exactly N bytes" checks on the batch run.

### Error handling in adapters
**Source:** `src/player/session.c:869-872, 913-915`: one stderr line naming the failed stage and `strerror(errno)`, never silent, and the caller gets a `bool`/code. Runner convention: `fprintf(stderr, "invalid-arguments: reason=<token>\n"); return 2;`. **Apply to:** all host/slot failure paths. Host-mode stderr lines are prefixed `gbb-host:` (D-14) and are diagnostics, not contract.

### Test registration and timeouts
**Source:** `tests/CMakeLists.txt:1864` `set(GBB_DEFAULT_TEST_TIMEOUT_SECONDS 60)`; `cmake/ScaleSanitizerTimeouts.cmake:4-17` (x3 only for tests that set a `TIMEOUT`); the player directory re-applies the sweep (`tests/player/CMakeLists.txt:495-508`). **Apply to:** all new tests. D-27: base 60 s, no allowlist rows. Do not set a custom `TIMEOUT` unless needed: a test that sets none gets 60 s, and sanitizer scaling only multiplies a TIMEOUT that exists on the test at the time `gbb_scale_sanitizer_test_timeouts()` runs (end of each CMake directory).

### Core purity
**Source:** `src/core/gabbaboy.c` has no signal, clock or env calls (RESEARCH F12). **Apply to:** the single core change (`gbb_get_input_clock`): no new includes, no host calls; `no_host_clock` and `core_linkage_*` must stay green.

### Model-gate tagging
**Source:** `/* MODEL: BOTH GATE-00 basis=host-api */` directly above `gbb_queue_events` (`gabbaboy.c:3968`), `gbb_get_info` (5438), `info_store` (5385). **Apply to:** `gbb_get_input_clock` and any new static helper in `gabbaboy.c`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/host/host_exit.h` (X-macro table) | config | transform | No X-macro table exists in `src/` or `include/`. Use RESEARCH "Exit table as X-macro" and have `verify-host-contract.py` parse it against `docs/host-contract.json`. |
| `src/host/host_signal.c` (`sigaction`, `volatile sig_atomic_t`, SA_RESETHAND) | adapter | event-driven | The only signal code in tracked source is `raise(SIGSTOP)` under `GBB_PLAYER_SESSION_TESTING` (`session.c:54-56`) and `kill(child, SIGKILL)` in the player smoke. Follow D-13 and RESEARCH Pattern 4, probed on macOS and gcc:13. |
| Strict UTF-8 validator (inside `host_basename.c`) | utility | transform | No UTF-8 validation in the codebase beyond the player's `utf8_prefix` (`src/player/main.c:748-755`, title truncation: it only backs up over continuation bytes and does not reject overlongs, surrogates or truncated sequences). Write the ~30-line DFA described in RESEARCH Pattern 3. |
| Dir-fd `*at` calls, `O_EXCL` temp names, `F_FULLFSYNC` | service | file-I/O | The analog `session.c` uses path-based `open`/`mkstemp`/`rename`. The `*at` forms and `F_FULLFSYNC` have no tracked precedent; take them from RESEARCH Pattern 1 and D-09. |
| Real-signal Python harness with `kill -SIGKILL` storm, `RLIMIT_CORE=0`, inherited `SIG_IGN` | test harness | event-driven | `verify-v02-consumers.py` is the nearest process-control code but signals a process group and has no storm/replay logic. Use RESEARCH Pattern 8. |
| Latest-`v*`-tag freeze comparison (`git show <tag>:docs/host-contract.json`) | checker | batch | `Source.read` in `verify-v03-dispositions.py` covers `git show REV:path`, but no tracked script selects "latest strict-semver tag". Reuse its `TAG` regex and add the numeric sort (RESEARCH Pattern 9). |

## Hazards the planner should carry into plans

These came out of reading the analogs and are not in CONTEXT:

1. **`player_input_reconcile` cannot move the cursor backwards** (`input.c:57-60`): an earlier-time state load needs a direct cursor/anchor set, not a reconcile call.
2. **Paced-sleep EINTR is the opposite of the player's idiom**: `main.c:2041` loops on EINTR; the host sleep must return on EINTR (D-03).
3. **`push_key` does not set `mod` or `key`** (`main.c:1601-1611`): the ⌘ key-decoder tests need a modifier-aware helper or they cannot exercise `command`-guarded branches.
4. **`reset_session` sets `user_paused = false`** (`main.c:961`): do not copy that line into the slot-load path (D-21: pause is kept across a load). Also reset `save_cadence` after a load.
5. **`tests/CMakeLists.txt` has a directory-wide `include_directories(src/core)`**: link `gabbaboy_host` as a library from tests; compiling host sources directly into a test target would silently allow `gabbaboy_test.h`.
6. **Python `-I` disables sibling-module imports**: share the ROM generator with `importlib.util.spec_from_file_location` or keep one script.
7. **`installed_host_smoke` needs three bookkeeping edits**: `ExpectedTests.cmake:12-15` removal list, Windows lists (POSIX-only), and the `installed_` prefix already handled by `verify-test-inventory.sh:164`.
8. **Player-suite vs main-suite inventories are different files** (`tests/player/expected-tests.txt` vs `tests/expected-tests.txt`) and the player branch chain `FATAL_ERROR`s on an unknown name (`tests/player/CMakeLists.txt:482`).
9. **`session.c` hashes with CommonCrypto** (macOS-only): the portable slot engine cannot call it; it receives the digest as an argument, and portable tests hash with `gbb_accept_sha256_hex`.
10. **`GBB_BUILD_QUALIFIED` dirty list** lives in the root `CMakeLists.txt:85-88`; the new checker asserts the runner/host sources are a subset, so add each new file in the same commit that creates it.

## Metadata

**Analog search scope:** `src/` (core, runner, player, accept), `include/gabbaboy/`, `cmake/`, `tests/` (C tests, `tests/player/`, `tests/scripts/`, `tests/consumers/`), `.github/scripts/`, `fixtures/`, `docs/`, root `CMakeLists.txt`.
**Files scanned:** ~60 opened or grepped (runner `main.c`, player `session.c`/`main.c`/`input.c`/`catch_up_policy.*`, core header and `gabbaboy.c` sections, `CheckCoreNoHostClock.cmake`, `ExpectedTests.cmake`, `expect_exit.cmake`, `VerifyInstalledPackage.cmake`, `VerifyDocContract.cmake`, `verify-test-inventory.sh`, `verify-v03-dispositions.py`, `verify-v02-consumers.py`, `verify-core-linkage.py`, `verify-model-gates.py`, test sources listed above, both `tests/CMakeLists.txt`).
**Pattern extraction date:** 2026-10-28
