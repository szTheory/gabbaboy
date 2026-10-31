# API Coverage — bounded GitHub release lifecycle

This phase integrates the existing GabbaBoy release lifecycle, not a general GitHub client. The capability surface is the23 post-tag endpoint/CLI forms inventoried by POST_TAG_ENDPOINTS in tests/scripts/verify-release-lifecycle.py, plus the three explicit operator recovery actions bounded by D-27 and the owner-approved D-130..D-133 recovery decisions. Every form is integrated; there are no silent opt-outs or new services. Existing declared replay routes and named workflow-policy rules remain authoritative. Fixture data proves deterministic logic and response shapes; actual authenticated runs prove permissions.

| capability | decision | reason |
|---|---|---|
| GET actions/runs/{id}/attempts/{attempt}/jobs?per_page=100 | INTEGRATE | Existing attempt_jobs replay; rehearsal merge-time binding and actual retry attempt jobs. |
| GET actions/runs/{id}/artifacts?per_page=100 | INTEGRATE | Existing check_release policy; actual independent pre-publish inventory artifact. |
| GET actions/runs/{id} | INTEGRATE | Existing ci_run replay; actual source CI and retry run identity. |
| GET exact-source main push CI runs | INTEGRATE | actions/workflows/ci.yml/runs?head_sha={sha}&event=push&branch=main&per_page=100; existing check_release policy binds S fuzz/perf evidence. |
| GET successful rehearsal branch runs | INTEGRATE | actions/workflows/release-rehearsal.yml/runs?branch=rehearsal/{tag}&status=success&per_page=100; existing workflow_runs replay retains premerge R2 at W. |
| GET actions/workflows/{workflow}/runs?per_page=100 | INTEGRATE | Existing check_release_gate_wiring policy; recovery and competing-run identity checks. |
| GET branches/main/protection | INTEGRATE | Existing check_release_gate_wiring policy; protected merge qualification. |
| GET commits/{tag-or-sha} | INTEGRATE | Existing commit replay; tagS identity remains unchanged. |
| GET commits/{sha}/check-runs?per_page=100 | INTEGRATE | Existing check_runs replay; every required exact-head context instance. |
| GET commits/{sha}/pulls | INTEGRATE | Existing pull_requests replay; merged version PR and server-recorded merge time. |
| GET contents/CMakeLists.txt?ref={sha} | INTEGRATE | Existing check_release policy; immutable source version. |
| GET pulls/{number} | INTEGRATE | Existing pull_request replay; reviewed merged source PR evidence. |
| GET releases/{id} | INTEGRATE | Existing release replay; actual failing/repaired/same published draft identity. |
| GET releases/{id}/assets?per_page=100 | INTEGRATE | Existing release_assets replay; complete IDs/names/digests and empty first-failure assets. |
| GET releases?per_page=100 | INTEGRATE | Existing release replay; exact real candidate list shape captured additively in19-08. |
| gh pr checks | INTEGRATE | Existing check_release policy; protected source PR requirements. |
| gh release download | INTEGRATE | Existing release_assets replay; actual downloaded-byte checks. |
| gh release edit | INTEGRATE | Existing release replay; only qualified pipeline publication, intercepted offline. |
| gh release upload | INTEGRATE | Existing release replay; bounded existing asset lifecycle and retry reuse. |
| gh run download | INTEGRATE | Existing check_release policy; genuine candidate, rehearsal and inventory artifacts. |
| gh run download --name perf-gate-{run}-{attempt} | INTEGRATE | Existing perf_gate_artifact_name policy; exact-source performance receipt. |
| gh run list | INTEGRATE | Existing workflow_runs replay; nightly selection plus actual competing-run observation. |
| gh run view | INTEGRATE | Existing workflow_runs replay; actual conclusion/head/event and nightly results. |
| PATCH releases/429606490 with body only (historical) | INTEGRATE | Historical one-shot repair changed draft association; retain request/response, unchanged Git tag and body digests as a refusing regression. Repetition remains forbidden. |
| PATCH releases/429606490 with tag_name only | INTEGRATE | D-132/D-133: one marked same-ID restoration after UTF-8 replay, review and preflight; captures bind body/target/flags/assets. Marker, ambiguity, identity, count and conflict negatives refuse. |
| POST actions/workflows/release-please.yml/dispatches | INTEGRATE | Main ref and explicit retry inputs;19-08 controls forbid duplicate/foreign requests, actual API run/job and candidate logs bind mainG to productS. |

For actual readback, paginated APIs retain all pages and validate their total/unique identities; bounded historical fixture samples never substitute for full live inventories. Auth tokens, headers and private machine data are excluded from committed captures.

Plan19-08 extends the existing checker and preserves every frozen baseline/ID/policy pin. The association restoration adds one explicitly bounded payload form on the existing release-ID endpoint; it adds no product job, package dependency, service account, permission or general-purpose API abstraction. The actual successful sole retry and committed readback close the recovery; no further live release action is included. Generic GitHub issue/project/organization administration is outside this release capability boundary; the already authorized boundary triage remains in19-07.
