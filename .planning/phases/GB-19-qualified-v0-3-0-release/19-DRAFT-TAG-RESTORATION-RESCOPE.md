# Phase 19: one bounded same-draft tag-association restoration

Status: **OWNER-APPROVED**

## Proposed outcome

Restore the existing unpublished draft's association with the already existing
`v0.3.0` Git tag, then conditionally resume the original, still-unused single
workflow retry. Keep the same draft ID and immutable product source. This does
not move or recreate a Git tag, replace a release, or change the publisher.

The owner approved D131 diagnosis and offline remedy design only. This document
is the resulting execution proposal; D131 does not authorize its live actions.

## What went wrong and what the investigation established

The original single raw API PATCH sent exactly `body`. GitHub returned HTTP200,
installed the exact repaired notes, and changed draft `tag_name` from `v0.3.0`
to `untagged-bff38b7645da850c79be`. The refusing readback guard stopped before a
retry. The actual Git tag is unchanged; the same draft remains unpublished and
empty. The first body PATCH and its permanent attempt marker remain historical.

The official [GitHub CLI2.101.0 implementation](https://raw.githubusercontent.com/cli/cli/v2.101.0/pkg/cmd/release/edit/edit.go)
explicitly supplies the fetched release's tag name when `release edit` omits a
replacement flag, because the API can remove it. Raw `gh api --input` transmits
the provided JSON and does not add that field. The body-only assumption in the
earlier operator plan was therefore insufficient for this draft update.

The existing protected publisher already uses `gh release edit`, with a
separate actual Git-tag/source check. An isolated TLS loopback test of the
installed2.101.0 binary recorded its exact current publisher request as
`{"draft":false,"tag_name":"v0.3.0"}`. A deliberately omitted-tag publisher
request failed the modeled identity check. No runtime publisher, workflow,
permission, source pin or readback allowlist change is demonstrated necessary.
This proves the tested binary's transport, not the version of a future hosted
runner or a future GitHub response. The runner-image manifest linked from the
ordinary G job could not be fetched; that access failure is not a version proof.

## Exact additional manual mutation

Address existing release ID `429606490` directly:

```text
PATCH repos/szTheory/gabbaboy/releases/429606490
```

Request bytes, UTF-8 with one final LF:

```json
{"tag_name":"v0.3.0"}
```

Request SHA-256:
`9369228a1035720e68125af98e7758717f315c6b1124d073cb5e2abc814af72e`.

No body, name, target, draft, prerelease, asset or publication field is sent.
The notes are already correct and must remain byte-identical. An existing
fully restored and otherwise matching state is a no-write result, not another
PATCH. Any third state stops.

## Guards and evidence

Before that one request, the operator must check current main G, local clean G
and its reviewed tree/parent/seven-path/critical-blob bindings, actual Git tag S,
the exact captured drift state on the same release ID, unchanged repaired-body
bytes/name/target/draft/prerelease/publication state, both empty asset views,
unique release association, no active release workflow and no open component
PR. Missing fields, non-boolean flags, duplicate JSON keys and incomplete API
pages refuse. No GitHub compare-and-swap guarantee is claimed.

Keep the original body-PATCH attempt marker unchanged. Reserve a distinct,
durable exclusive marker before the one association request. Save the exact
request, actual HTTP response and independent GET bodies without credentials.
Require complete HTTP200 output and complete independent readback: tag
association restored, notes/body and all other guarded release fields unchanged,
actual tag still S, main still G, draft still unpublished/non-prerelease/empty.
Ambiguous or non-success output, unexpected state or a prior attempt marker
holds execution with no repeat, compensation, rollback or dispatch.

Only after that successful readback and every existing source/replay/publication
precondition passes, dispatch the original existing workflow once on main G
with `retry=true`, `tag_name=v0.3.0`, `source_sha=S`, and `release_id=429606490`.
Preserve the first failed run separately. Actual workflow/job heads are G;
products, tag, downloaded receipts and inventory remain S. Do not infer retry
from an attempt number. The existing pipeline owns attachments and its one
guarded publication transition. Any further live failure stops for the owner;
this is not a renewed retry or failure allowance.

## Explicit scope decision

If approved, amend the body-only/second-failure stop only for the exact manual
association restoration above and conditional resumption of the unused original
retry. Permit the bounded private operator implementation and independent
offline recheck required to make that action reviewable, preserving all earlier
reviews/failures. No new main merge, plan, gap, automatic rerun, product change,
dependency, permission, policy authority, timeout or performance change is
authorized. G remains `d61a25ea54364e0e26ef89bb7467c72089361d49`, directly on S
`a3f3390451f9a893aa47475f15a722ada86daaa6`; the existing strict seven-path
readback contract and critical-blob equality remain intact.

Carry sanitized incident captures, the corrected operator procedure and the
captured-drift/explicit-association positive and negative regression evidence
into the already planned PR B, extending existing checker/tests where needed.
This explicitly defers those operator-only closure records to PR B rather than
requiring another corrective main PR. Do not weaken the original body-only
failure capture or any dispatch/identity assertion. PR B still requires full
local qualification, phase review/security/validation/goal gates, exact-head
hosted checks and a guarded merge before the phase execution handoff.

19-07 and REL-01 remain pending. There is no successful release readback or
completed19-07/19-08 SUMMARY yet. After qualified publication and PR B, stop at
`/gsd-verify-work 19`; do not run it or advance a milestone automatically.

## Offline qualification record

The reviewed prototype/request/transport evidence lives in ignored
`build/phase19-window/posttag-recovery/tag-drift-replan/`. It uses captured actual
inputs and isolated/in-memory response models. Models do not prove a future
live API result; strict actual readback remains mandatory.

The current operator is frozen at SHA-256
`30441ac1c5154b12d7af8f3abe46d7a193d06ab7b48e80bc097b61944e4970ce`.
Its current offline suite passes, but final independent review is **BLOCKED**:
the marker's path is derived from the helper's own location. A same-depth copy
in a sibling evidence directory resolves the same project and approval document
while using a different marker, permitting a second attempt after an ambiguous
first one. The independent offline copy probe reproduced that bypass. No live
restoration request has been sent, and the new marker remains absent.

The first consolidated operator correction closed ambiguous-attempt no-op,
concurrent release-workflow, incomplete-PR and malformed-release-list gaps. The
second corrected documented Actions workflow paths with `@ref` suffixes. Those
findings and all prior phase reviews remain historical; no counter is reset.
The remaining marker issue forces this explicit scope decision under the
project's bounded review rule.

## Final bounded operator correction requested

Authorize exactly one further consolidated private operator correction and
independent recheck for the remaining marker finding, followed **only if clear**
by the exact manual association restoration and original unused retry defined
above. This is the requested new authority; D131 did not grant it. A remaining
or unrelated finding after that recheck holds execution again.

The concrete un-applied patch is retained as
`build/phase19-window/posttag-recovery/tag-drift-replan/canonical-marker-fix.proposed.patch`.
It changes the preparation/model/request/marker directory from `__file__`'s
parent to the fixed project-root evidence directory and rejects execution of a
copied operator before qualification or network calls. The endpoint, one-field
request, existing state guards, original body-PATCH marker, workflow/product
identities, permissions, source and every limit remain unchanged.

Required negative controls must copy the operator/request/model to a same-depth
sibling: both copies must resolve the same canonical marker, and copied execution
must refuse before any request. A prior marker must stop every copy, including
after an ambiguous attempt that did not change remote state. Keep the normal
canonical-path positive, old-marker integrity check, all existing negatives and
the real CLI loopback transport evidence. Do not claim qualification from a
test count or syntax-only pass.

After the final corrected hash is independently clear, run a fresh **read-only**
preflight against current APIs before the one approved restoration. Save the
approved hash, request digest, review result and actual readback; only then may
the conditional original retry proceed. There is no new main merge or publisher
change. The latest actual-G push CI and fixture runs have also passed; its
scheduled main nightly is separate from release/rehearsal authority.

Until the owner approves this scope and its conditions pass, all live actions
remain stopped. Approval does not waive a finding, loosen a gate, renew a retry,
accept unknown behavior, or authorize another phase.

## D132 owner approval

The owner answered “Okay, yes, I approve” on2026-10-31. This approves exactly
the final canonical-marker correction and independent recheck, followed only
if clear by the one same-ID tag-only association restoration and conditional
original unused retry. Every guard, stop, unchanged-source constraint and PR B
closure obligation above remains binding. No prior round is reset.

## Subsequent D132 execution hold

The canonical-marker correction and independent recheck passed at4d746c14,
but the required read-only live preflight stopped with TypeError before any
PATCH/marker. Its main pre/post adoption calls pass str to a bytes helper.
D132's remaining-finding stop is active. The exact un-applied UTF-8 proposal,
full main-entrypoint replay and requested bounded scope are in
[19-ENTRYPOINT-UTF8-RESCOPE.md](19-ENTRYPOINT-UTF8-RESCOPE.md). No new action
is authorized by this document while that scope is pending.

## Actual D133 gate and recovery outcome so far

The exact0c7d9c38 operator passed the full actual-entrypoint replay and fresh
independent review. Fresh read-only preflight passed. The one same-ID tag-only
association restoration returnedHTTP200 and passed complete response/readback,
adoption and actual CLI draft lookup with unchanged notes/source/state. The
original single retry was then dispatched once: actualrun41205021983 attempt1,
workflow_dispatch/main/G. It is in progress; no publication/readback/phase
completion is claimed. Preserve all earlier failures and permanent markers;
further live failure holds again.
