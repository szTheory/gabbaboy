# API Coverage — GitHub repository, Actions, and Releases

> Full coverage by default for the GitHub capabilities required by this phase. Opt-outs are explicit and reasoned. This matrix covers the repository integration surface needed to qualify and publish this release; it does not claim to enumerate unrelated GitHub product APIs.

| capability | decision | reason |
|---|---|---|
| Read repository identity, default branch, and current repository settings | INTEGRATE | Establish the trusted repository and resolve current release configuration. |
| Read branch protection and ruleset requirements | INTEGRATE | Release eligibility must use live required contexts, not a stale planning snapshot. |
| Read pull requests, changed files, head SHA, base SHA, and merge eligibility | INTEGRATE | Validate the release-please PR and its exact candidate revision. |
| Create/update the version pull request through release-please | INTEGRATE | Required version and tag workflow. |
| Read required check contexts and check-run conclusions for the exact PR head | INTEGRATE | Missing, stale, skipped, cancelled, timed-out, or failed evidence must block promotion. |
| Read workflow-run status and relevant Actions evidence | INTEGRATE | Diagnose whether required exact-head evidence completed successfully. |
| Create a draft GitHub Release for the trusted version tag | INTEGRATE | Hold the candidate while exact bytes and metadata are qualified. |
| Upload and enumerate release assets and read their metadata/digests | INTEGRATE | Bind the draft to the tested asset bytes and sidecars. |
| Download release assets for relocated package/player smoke | INTEGRATE | Smoke the bytes that will be published rather than rebuilding after qualification. |
| Publish the qualified draft and read back the final release/assets | INTEGRATE | Confirm durable publication preserves the approved bytes and evidence. |
| Generate and verify artifact attestations when enabled | INTEGRATE | Use provenance where available and verifiable; report capability/access failures without claiming an attestation. |
| Read open issues and pull requests for the phase-boundary triage | INTEGRATE | Record relevant release/adopter reports and access limitations at the handoff. |
| Create or edit issues, labels, discussions, comments, or project-board items | OPT-OUT | Phase 6 only inspects open issue/PR state; it does not authorize or require external user communication or project-board changes. |
| Merge pull requests, bypass protection, or modify branch rulesets | OPT-OUT | Release automation must prove eligibility and preserve existing owner/repository protection; it does not administer or bypass repository policy. |
| Dispatch arbitrary workflows or use manual dispatch as release evidence | OPT-OUT | Manual dispatch cannot replace required checks on the exact version-PR head or trusted tag path. |
| Delete releases/assets or mutate a published release | OPT-OUT | Published release identity and bytes are a durable contract; repair requires a separately reviewed repository policy. |
| Provision App credentials or change Actions approval settings | OPT-OUT | Credential provisioning and approval policy are owner-operated; the plan records the operational gate and uses least privilege when provisioned. |
| Upload packages to GitHub Packages or another package registry | OPT-OUT | Distribution is the single durable GitHub Release with platform assets; package-registry publication is deferred. |
