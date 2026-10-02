# Cross-project lesson exchange

Created 2026-10-02. This ledger is intentionally small. Detailed imported evidence is in `research/PRECEDENT.md`; hardware and upstream evidence are in the corresponding research topics.

## Rule for incoming lessons

A lesson from another emulator is a hypothesis until its mechanism applies to GabbaBoy and evidence supports the adaptation. Record the source project and revision/date, whether it was implemented or merely planned, how the target differs, the smallest local reproduction, and the resulting decision. Preserve corrections by superseding old entries instead of silently erasing the reasoning.

## Rule for outgoing lessons

At meaningful phase/milestone boundaries, produce a short pasteable transfer when requested. Exclude absolute personal paths, identities, private ROM names/hashes, credentials, and conversation transcripts. Do not imply another console shares the same timing behavior simply because the bug category sounds similar.

## Transfer template

```text
Lesson ID / date / originating project revision:
Symptom and reproduction:
Root cause / invariant:
Fix and evidence:
Applies when:
Does not establish:
Suggested check in the receiving project:
Source paths or public URLs:
Status: observed / reproduced / adopted / superseded
```

## Imported safeguards to validate locally

| ID | Lesson | GabbaBoy action | Status |
|---|---|---|---|
| XFER-001 | A promising homebrew fixture may be private, unlicensed for redistribution, or for a different console | Admit GB fixtures only after license/system/protocol review; add an original persistence fixture | Imported; implementation pending |
| XFER-002 | A save test can pass without reading previously persisted bytes | Reload in a fresh instance/process and assert behavior that depends on old save contents; include wrong-save control | Imported; implementation pending |
| XFER-003 | Green orchestration is weaker than evidence tied to a source revision and packaged bytes | Assert mandatory gate execution, tested revision, install/consumer smoke, and artifact digest | Imported; implementation pending |
| XFER-004 | Timing and save correctness require hidden in-flight state, not only visible registers | Exercise split-run equivalence and save/load continuation at intermediate device events | Proposed adaptation; implementation pending |
| XFER-005 | Upstream automation behavior changes; copied CI folklore can be stale | Recheck official GitHub token/event rules during workflow implementation and verify target-repo behavior | Source-checked recommendation; repository verification pending |

There are no GabbaBoy implementation-derived lessons yet. Add them with evidence as phases ship.
