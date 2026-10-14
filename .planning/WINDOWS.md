---
schema_version: 1
open_count: 15
waived_count: 0
fixed_count: 0
total_count: 15
last_updated: 2026-10-14T01:52:45.826Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | deviation | tests/test_cpu.c |  | Updated opcode matrix expectations for explicit HALT/STOP outcomes and IE register reads. | open |  | 2026-10-06T19:26:33.657Z |  |
| 2 | 02 | deviation | fixtures/mooneye/manifest.json |  | Raised DAA's finite execution budget from 200000 to 2000000 half-dots after pinned source workload analysis showed 4096 cases require at least 1343488 half-dots before setup and completion protocol. | open |  | 2026-10-06T20:51:58.126Z |  |
| 3 | 05 | deviation | src/player/audio.c |  | Ring-full producer stalls are counted with lock-free 64-bit backpressure events. | open |  | 2026-10-08T13:03:33.944Z |  |
| 4 | 05 | deviation | tests/test_apu.c |  | Corrected the wave guest program DAC register address and trigger setup after its PCM assertion stayed silent. | open |  | 2026-10-08T13:44:31.478Z |  |
| 5 | 05 | deviation | tests/test_apu.c |  | Moved the generated channel-mask program past ROM header checksum offset 0x14D so checksum generation cannot alter instructions. | open |  | 2026-10-08T13:44:31.569Z |  |
| 6 | 05 | deviation | tests/test_apu.c |  | Extended the reset-test run budget so the guest completes the wave-RAM readback instead of observing only cleared work RAM. | open |  | 2026-10-08T13:47:03.408Z |  |
| 7 | 05 | deviation | src/player/input.c |  | The Task 1 input implementation was staged in its RED test commit after the failing assertion was captured; behavior and classifier evidence still verified before the GREEN commit. | open |  | 2026-10-08T15:55:21.063Z |  |
| 8 | 05 | deviation | tests/player/test_input.c |  | The reconnect queue-full fixture now loads the demo ROM so its retry case has a live guest timeline. | open |  | 2026-10-08T15:55:37.132Z |  |
| 9 | 05 | deviation | src/player/audio.h |  | Added the existing internal adapter header to the task scope so new audio transition functions have declarations shared by main and tests. | open |  | 2026-10-08T16:00:39.497Z |  |
| 10 | 05 | deviation | .github/workflows/preview.yml |  | Corrected stale preview capability claims and package metadata to describe the implemented scoped DMG audio contract. | open |  | 2026-10-08T16:24:49.415Z |  |
| 11 | 12 | deviation | tests/scripts/test-reproduce-age.sh |  | The byte-difference negative control mutates the scratch rebuilt ROM because mutating the committed fixture is rejected first by self-check. | open |  | 2026-10-13T17:06:18.785Z |  |
| 12 | 12 | deviation | cmake/P12Mutants.cmake |  | Adjusted the M3 mutant because divider_phase remains zero and its initial normal-speed phase replacement was equivalent in double speed. | open |  | 2026-10-13T18:02:22.258Z |  |
| 13 | 12 | deviation | cmake/P12Mutants.cmake |  | Made the generated M12 RTC fault use an explicit double_speed local while keeping production RTC code outside that trust domain. | open |  | 2026-10-13T18:02:22.362Z |  |
| 14 | 12 | deviation | tests/expected-tests.txt |  | The planned broad AGE selector includes the pre-existing div timeout negative control (14 tests total; 13 ROM disposition tests). | open |  | 2026-10-14T01:20:16.619Z |  |
| 15 | 12 | deviation | cmake/P12Mutants.cmake |  | M28 mutant scope corrected to double-speed destinations after the AGE sweep measured mode-0 discrimination. | open |  | 2026-10-14T01:52:45.826Z |  |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "02",
    "file": "tests/test_cpu.c",
    "line": null,
    "description": "Updated opcode matrix expectations for explicit HALT/STOP outcomes and IE register reads.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-06T19:26:33.657Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "02",
    "file": "fixtures/mooneye/manifest.json",
    "line": null,
    "description": "Raised DAA's finite execution budget from 200000 to 2000000 half-dots after pinned source workload analysis showed 4096 cases require at least 1343488 half-dots before setup and completion protocol.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-06T20:51:58.126Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 3,
    "kind": "deviation",
    "phase": "05",
    "file": "src/player/audio.c",
    "line": null,
    "description": "Ring-full producer stalls are counted with lock-free 64-bit backpressure events.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T13:03:33.944Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 4,
    "kind": "deviation",
    "phase": "05",
    "file": "tests/test_apu.c",
    "line": null,
    "description": "Corrected the wave guest program DAC register address and trigger setup after its PCM assertion stayed silent.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T13:44:31.478Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 5,
    "kind": "deviation",
    "phase": "05",
    "file": "tests/test_apu.c",
    "line": null,
    "description": "Moved the generated channel-mask program past ROM header checksum offset 0x14D so checksum generation cannot alter instructions.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T13:44:31.569Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 6,
    "kind": "deviation",
    "phase": "05",
    "file": "tests/test_apu.c",
    "line": null,
    "description": "Extended the reset-test run budget so the guest completes the wave-RAM readback instead of observing only cleared work RAM.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T13:47:03.408Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 7,
    "kind": "deviation",
    "phase": "05",
    "file": "src/player/input.c",
    "line": null,
    "description": "The Task 1 input implementation was staged in its RED test commit after the failing assertion was captured; behavior and classifier evidence still verified before the GREEN commit.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T15:55:21.063Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 8,
    "kind": "deviation",
    "phase": "05",
    "file": "tests/player/test_input.c",
    "line": null,
    "description": "The reconnect queue-full fixture now loads the demo ROM so its retry case has a live guest timeline.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T15:55:37.132Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 9,
    "kind": "deviation",
    "phase": "05",
    "file": "src/player/audio.h",
    "line": null,
    "description": "Added the existing internal adapter header to the task scope so new audio transition functions have declarations shared by main and tests.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T16:00:39.497Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 10,
    "kind": "deviation",
    "phase": "05",
    "file": ".github/workflows/preview.yml",
    "line": null,
    "description": "Corrected stale preview capability claims and package metadata to describe the implemented scoped DMG audio contract.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-08T16:24:49.415Z",
    "resolved_at": null,
    "milestone": "v0.1"
  },
  {
    "id": 11,
    "kind": "deviation",
    "phase": "12",
    "file": "tests/scripts/test-reproduce-age.sh",
    "line": null,
    "description": "The byte-difference negative control mutates the scratch rebuilt ROM because mutating the committed fixture is rejected first by self-check.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-13T17:06:18.785Z",
    "resolved_at": null,
    "milestone": "v0.2"
  },
  {
    "id": 12,
    "kind": "deviation",
    "phase": "12",
    "file": "cmake/P12Mutants.cmake",
    "line": null,
    "description": "Adjusted the M3 mutant because divider_phase remains zero and its initial normal-speed phase replacement was equivalent in double speed.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-13T18:02:22.258Z",
    "resolved_at": null,
    "milestone": "v0.2"
  },
  {
    "id": 13,
    "kind": "deviation",
    "phase": "12",
    "file": "cmake/P12Mutants.cmake",
    "line": null,
    "description": "Made the generated M12 RTC fault use an explicit double_speed local while keeping production RTC code outside that trust domain.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-13T18:02:22.362Z",
    "resolved_at": null,
    "milestone": "v0.2"
  },
  {
    "id": 14,
    "kind": "deviation",
    "phase": "12",
    "file": "tests/expected-tests.txt",
    "line": null,
    "description": "The planned broad AGE selector includes the pre-existing div timeout negative control (14 tests total; 13 ROM disposition tests).",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-14T01:20:16.619Z",
    "resolved_at": null,
    "milestone": "v0.2"
  },
  {
    "id": 15,
    "kind": "deviation",
    "phase": "12",
    "file": "cmake/P12Mutants.cmake",
    "line": null,
    "description": "M28 mutant scope corrected to double-speed destinations after the AGE sweep measured mode-0 discrimination.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-14T01:52:45.826Z",
    "resolved_at": null,
    "milestone": "v0.2"
  }
]
````
