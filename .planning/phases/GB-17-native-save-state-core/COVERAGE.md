# API Coverage — inherited GitHub release evidence

Full coverage by default over the actual inherited API capability surface used by Phase17 tooling; this is not a new general GitHub client. Detector ran on Phase17 plan scope and reported detected:true. Local native state functions are not external API integration.

| capability | decision | reason |
|---|---|---|
| list/get workflow runs and attempts | INTEGRATE | Bind producing workflow/event/head/status/conclusion and newest eligible nightly |
| get workflow jobs and timings | INTEGRATE | Verify successful replay, exact job identity and real timeout evidence |
| list/get check-runs and check-suite/app identity | INTEGRATE | Real url/html_url/check_suite schemas and consistent trusted App |
| list/get/download run artifacts | INTEGRATE | Bind producer/source/equal-tree route and exact artifact bytes |
| get release/draft identity and assets | INTEGRATE | Existing production inventory, manifest, stale/partial/tamper refusal |
| download release assets and read attached-byte digests | INTEGRATE | Retry reuses identical validated attachments |
| upload draft evidence assets | INTEGRATE | Existing production path is exercised by bounded local stub; no live upload here |
| final release publish decision | INTEGRATE | Invoke actual production decision with intercepted transport; no live publish |
| retrieve issue/comment approval metadata | INTEGRATE | OWNER, exact issue/time/full measurement digest, no prefilled identity |
| nightly-red issue list/search/exact title-label dedupe | INTEGRATE | Existing production path replayed without sending a message |
| write/update nightly-red issue | INTEGRATE | Existing production behavior covered via non-writing captured/stub transport |
| create/move/delete tags or published assets | OPT-OUT | Phase17 explicitly authorizes no live publication or mutation of published tags/assets |
| general GitHub repo/PR/team/user CRUD, webhooks and unrelated endpoints | OPT-OUT | No general GitHub integration is introduced; capabilities are outside this phase's inherited evidence surface |
| live issue/comment approval authoring | OPT-OUT | Owner approvals must originate from the owner; tests only validate captured approval data |
| live draft creation/permission qualification | OPT-OUT | Bounded captured replay covers deterministic logic; live permissions/publication belong to later release work unless a concrete remaining material gap is separately authorized |

