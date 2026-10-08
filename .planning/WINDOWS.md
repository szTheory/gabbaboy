---
schema_version: 1
open_count: 3
waived_count: 0
fixed_count: 0
total_count: 3
last_updated: 2026-10-08T13:03:33.944Z
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
  }
]
````
