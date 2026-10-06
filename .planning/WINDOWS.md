---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-10-06T19:26:33.657Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | deviation | tests/test_cpu.c |  | Updated opcode matrix expectations for explicit HALT/STOP outcomes and IE register reads. | open |  | 2026-10-06T19:26:33.657Z |  |

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
  }
]
````
