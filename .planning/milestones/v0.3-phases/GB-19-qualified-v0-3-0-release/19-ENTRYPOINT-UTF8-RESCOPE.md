# Phase 19: bounded operator UTF-8 entrypoint repair

Status: **OWNER-APPROVED**

## Decision in plain language

D132's marker fix passed independent review, but the required read-only live
preflight found a separate text/bytes mismatch. It completed eleven successful
GETs and stopped before any PATCH or restoration marker. The draft is still
unpublished and empty, the actual Git tag is unchanged, and the original retry
is unused.

The previous tests exercised the internal state machine rather than both actual
`main()` adoption-check calls. Those calls pass JSON text to an unchanged
production checker that requires UTF-8 bytes. Both the preflight call and the
post-PATCH call need the same explicit conversion. D132's remaining-finding stop
is preserved; no fix or further live attempt has been made under that scope.

**Recommendation:** authorize one consolidated correction/recheck limited to
those two UTF-8 conversions and full entrypoint replay coverage. Only after a
clear independent result and fresh successful read-only preflight may the
already approved D132 tag-only restoration and original unused retry continue.
This does not add a PATCH, retry, main merge, plan or gap allowance.

## Exact repair

In the ignored private `restore-v030-tag-association.py`, encode the validated
release body with `.encode("utf-8")` at the two calls to
`BASE.adoption_check`: before mutation using `snapshot`, and after readback
using `final`. The response validator already requires those values to be
strings and binds their UTF-8 hashes to the exact repaired body. The conversion
does not change notes, requests, state, filenames, limits or publication logic.

Concrete un-applied patch:
`build/phase19-window/posttag-recovery/tag-drift-replan/utf8-entrypoint-fix.proposed.patch`.

| Identity | SHA-256 |
|---|---|
| Current frozen operator (unchanged, blocked) | `4d746c14ac9e8bf14d0ae17b570aa5df94e33789697cd8d71751318388d9e784` |
| Exact two-call candidate before test-only additions | `0c7d9c38703155b7ca45c1333a67171a0b6160f31abd97e750c0ead7a05a26b3` |
| Proposed patch | `e4ea73bfaefc58a1a8fca90bb949fadced8d74bf43661a3fba52bd11cc226fb0` |
| Unchanged tag-only request | `9369228a1035720e68125af98e7758717f315c6b1124d073cb5e2abc814af72e` |

## Diagnosis and offline proof

The real preflight is retained in ignored `association-preflight-D132/`.
Every API GET returned HTTP200. The evidence writer recorded `hold-no-retry`
with `TypeError`; there are no PATCH records and no restoration marker. Its
snapshots show the same release429606490, drift association, exact repaired
body, target S, draft/non-prerelease/unpublished state, empty assets, main G,
actual Git tag S and no competing release work.

Independent read-only review confirmed the helper's `notes: bytes` contract and
its `handle.write(notes)` operation, both wrong-type call sites, and the absence
of a live attempt. Encoding the retained actual body passes the unchanged
source-S adoption checker.

The full diagnostic replay is
`build/phase19-window/posttag-recovery/tag-drift-replan/probe-main-entrypoints.py`;
the retained passing report is
`entrypoint-replay/20261031T125019Z/report.json` beneath that directory. The frozen
operator file was not changed: the two-call candidate executed only in memory.
All `gh` subprocesses were intercepted, and simulated attempt markers were
redirected to temporary ignored evidence. There were no GitHub requests.

The replay executes the actual `main()` functions, real G/S Git reads/source
extraction, unchanged production adoption checker, real HTTP response parser
and evidence writer. Its API JSON comes from the eleven actual retained GETs.
Only the expected PATCH response/state transition is modeled. It establishes:

- The frozen baseline reproduces the preflight TypeError before any PATCH.
- The two-call candidate completes the read-only entrypoint.
- Its apply entrypoint completes exactly one simulated tag-only PATCH, complete
  readback and the actual post-adoption call, without dispatch.
- A changed preflight body refuses before mutation; changed post-PATCH body
  refuses after the simulated request and cannot become a success.
- The real operator, original body-attempt marker and absent restoration marker
  remain unchanged after the replay.

This proves the candidate's integration through the real local boundaries. It
does not prove a future live GitHub result or grant authority to attempt one.

## Bounded authority requested

Permit exactly one further consolidated private operator correction and fresh
independent recheck for this two-call mismatch. Preserve all D132 marker,
copy-path, approval, identity, source, partial-response, ambiguity, competitor,
workflow-ref and exact-request guards. Add/retain the full actual-entrypoint
replay as executable coverage of the final frozen operator, including the
failing baseline and refusing twins. A unit-only state-machine pass is
insufficient. Record final code/test identities before the actual preflight.

Then, only if every condition passes, resume the **same unused** D132 actions:
one tag-only association PATCH to the existing release ID, followed by the
original single workflow retry on main G after strict actual readback. Preserve
both permanent attempt markers, all earlier failures/reviews, immutable S and G,
the strict seven-path readback contract and every product/policy/permission/
dependency/performance/time limit. No new main merge or publisher change is
authorized. A further finding or live failure holds again; no round is reset.

Carry this integration failure and its regression evidence into existing PR B
with the earlier incident records. No completed recovery/release/REL-01 or
Phase19 claim exists. The eventual execution handoff remains
`/gsd-verify-work 19`; do not run it or advance the milestone automatically.

## D133 owner approval

The owner answered “yes i approve” on2026-10-31. Exactly the two UTF-8 call
conversions, full actual-entrypoint replay and fresh independent recheck are
authorized. Only after those gates and a fresh read-only preflight pass may
the same unused D132 restoration and original retry proceed. No action count
or prior review round is reset; all other constraints and stops remain.

## Actual D133 gate and recovery outcome so far

The exact0c7d9c38 operator passed the full actual-entrypoint replay and fresh
independent review. Fresh read-only preflight passed. The one same-ID tag-only
association restoration returnedHTTP200 and passed complete response/readback,
adoption and actual CLI draft lookup with unchanged notes/source/state. The
original single retry was then dispatched once: actualrun41205021983 attempt1,
workflow_dispatch/main/G. It is in progress; no publication/readback/phase
completion is claimed. Preserve all earlier failures and permanent markers;
further live failure holds again.
