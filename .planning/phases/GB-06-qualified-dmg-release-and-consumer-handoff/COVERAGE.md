# API Coverage — GitHub repository, Actions, and Releases

> Full coverage by default for the GitHub capabilities required by this phase. Opt-outs are explicit and reasoned. This matrix covers the repository integration surface needed to qualify and publish this release; it does not claim to enumerate unrelated GitHub product APIs.

This reviewed matrix decides 23 capabilities: 17 are integrated and 6 are
intentional opt-outs. The concrete callers are the trusted
[`release-please.yml`](../../../.github/workflows/release-please.yml) and
[`release.yml`](../../../.github/workflows/release.yml) workflows. A manual
retry resumes only an already qualified candidate and cannot replace protected
version-PR checks.

| capability | decision | reason |
|---|---|---|
| Read repository identity, default branch, and current repository settings | INTEGRATE | Establish the trusted repository and resolve current release configuration. |
| Read branch protection and ruleset requirements | INTEGRATE | Release eligibility must use live required contexts, not a stale planning snapshot. |
| Read pull requests, changed files, head SHA, base SHA, and merge eligibility | INTEGRATE | Validate the release-please PR and its exact candidate revision. |
| Create/update the version pull request through release-please | INTEGRATE | Required version and tag workflow. |
| Merge the reviewed version PR when protected checks pass | INTEGRATE | The final gated merge creates the release source revision; branch protection remains authoritative. |
| Read required check contexts and check-run conclusions for the exact PR head | INTEGRATE | Missing, stale, skipped, cancelled, timed-out, or failed evidence must block promotion. |
| Read workflow-run status and relevant Actions evidence | INTEGRATE | Diagnose whether required exact-head evidence completed successfully. |
| Read and verify the version tag and target commit SHA | INTEGRATE | Bind the trusted version tag to the final merged source revision. |
| Create one unpublished draft and force its matching tag | INTEGRATE | Keep release assets private while making the exact tag available for candidate builds. |
| Read draft release identity and unpublished status | INTEGRATE | Reuse the same draft and block work if it is missing, duplicated, or published early. |
| Route candidate jobs from release-please action outputs | INTEGRATE | Use release_created, tag_name, and sha in the same workflow despite suppressed tag events. |
| Resume candidate work against the existing qualified draft | INTEGRATE | Retry only after rechecking draft/tag/SHA and saved exact-head PR evidence. |
| Upload and enumerate release assets and read their metadata/digests | INTEGRATE | Bind the draft to the tested asset bytes and sidecars. |
| Download release assets for relocated package/player smoke | INTEGRATE | Smoke the bytes that will be published rather than rebuilding after qualification. |
| Publish the qualified draft and read back the final release/assets | INTEGRATE | Confirm durable publication preserves the approved bytes and evidence. |
| Generate and verify artifact attestations when enabled | INTEGRATE | Use provenance where available and verifiable; report capability/access failures without claiming an attestation. |
| Read open issues and pull requests for the phase-boundary triage | INTEGRATE | Record relevant release/adopter reports and access limitations at the handoff. |
| Create or edit issues, labels, discussions, comments, or project-board items | OPT-OUT | Phase 6 only inspects open issue/PR state; it does not authorize or require external user communication or project-board changes. |
| Bypass protection or modify branch rulesets | OPT-OUT | Release automation must prove eligibility and preserve existing repository policy. |
| Dispatch arbitrary workflows or use manual dispatch as release evidence | OPT-OUT | Manual dispatch cannot replace required checks on the exact version-PR head or trusted tag path. |
| Delete releases/assets or mutate a published release | OPT-OUT | Published release identity and bytes are a durable contract; repair requires a separately reviewed repository policy. |
| Provision App credentials or change Actions approval settings | OPT-OUT | Credential provisioning and approval policy are owner-operated; the plan records the operational gate and uses least privilege when provisioned. |
| Upload packages to GitHub Packages or another package registry | OPT-OUT | Distribution is the single durable GitHub Release with platform assets; package-registry publication is deferred. |

## Draft lifecycle and release authorization

The release-please action owns creation of the version pull request. Only after
that PR is reviewed and merged under the repository's current protection rules
does the trusted main workflow consume the action's `release_created`,
`tag_name`, and `sha` outputs. For a created version, release-please creates
one unpublished draft (`draft=true`) and the matching version tag immediately.
The workflow confirms the tag resolves to that exact source SHA and confirms a
single draft with non-empty notes before attaching any candidate bytes.

| Stage | Required API state | Gate |
|---|---|---|
| Version PR review | Current repository rules; exact PR head and all required check conclusions | Missing, stale, skipped, failed, cancelled, or timed-out checks block merge/publication. Manual dispatch is not evidence for this stage. |
| Candidate start | `release_created=true`, the action's `tag_name` and `sha`, the tag resolving to that SHA, and exactly one matching draft with `draft=true` | A pushed tag event is not relied on; `GITHUB_TOKEN` can suppress downstream workflow runs. |
| Candidate and retry | The same draft ID, tag, source SHA, prior exact-head proof, and byte-identical existing attachments | Retry cannot create another draft, retag, rebuild qualified bytes, or continue against a published release. |
| Publish | Exact expected asset names and identities; every downloaded asset passes digest and consumer/package smoke; release is still `draft=true` immediately before publication | One explicit draft-to-published transition. Any failed or missing gate leaves the release unpublished. |
| After publish | Read back the release and asset identities/digests | Reconcile the published bytes without rebuilding or mutating the release. |

Attestations are attempted and verified only when the repository's current
permissions and GitHub capability allow it. An unavailable or unverifiable
attestation is recorded as unavailable; it is never represented as a pass.
