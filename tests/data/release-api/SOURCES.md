# Captured GitHub API responses

`captured.json` holds read-only, sanitized, bounded GitHub REST responses for the public repository
`szTheory/gabbaboy`. The release lifecycle replay (`tests/scripts/verify-release-lifecycle.py`) serves response
shapes derived from it so that the production attach, manifest, final-gate and publish-decision code runs against the
real object schemas (run, job, artifact, check run, pull request, release and release asset) and not against shapes
invented to satisfy a verifier. It proves deterministic logic. It does not prove live GitHub permissions.

- captured.json sha256: f07daba99707dacadfc0a5823c83c3e5779dbbac452807c54cac8edef50351ec
- bytes: 168019 (bound: 262144)
- format: UTF-8 JSON, sorted keys, two-space indent, LF line endings (`.gitattributes` pins `eol=lf` so the digest is stable on Windows)

## Endpoints

Each was read once with `gh api` (HTTP GET, no mutation, no authentication material stored). `POST_TAG_ENDPOINTS` in `verify-release-lifecycle.py` inventories each post-tag `gh api`, `gh run`, `gh release` and `gh pr` form as a replay route with required capture paths or a named workflow-policy pin. Identity captured:
release `v0.2.1` (id 423802899, already published at capture time), source commit
`b93137f00d07b11dc74e40330e0ddf6029c0677d`, merged pull request #75 with head `c6dc575b6a84cf51a56688948fce9241ba323400`,
and release-please workflow run 40259198302.

| Capture key | Endpoint |
|---|---|
| release | `repos/szTheory/gabbaboy/releases/423802899` |
| release_assets | `repos/szTheory/gabbaboy/releases/423802899/assets?per_page=100` |
| workflow_runs | `repos/szTheory/gabbaboy/actions/workflows/release-please.yml/runs?per_page=5` |
| workflow_run | `repos/szTheory/gabbaboy/actions/runs/40259198302` |
| jobs | `repos/szTheory/gabbaboy/actions/runs/40259198302/jobs?per_page=100` |
| artifacts | `repos/szTheory/gabbaboy/actions/runs/40259198302/artifacts?per_page=100` |
| check_runs | `repos/szTheory/gabbaboy/commits/c6dc575b6a84cf51a56688948fce9241ba323400/check-runs?per_page=100` |
| pull_request | `repos/szTheory/gabbaboy/pulls/75` |
| pull_requests | `repos/szTheory/gabbaboy/commits/b93137f00d07b11dc74e40330e0ddf6029c0677d/pulls` |
| attempt_jobs | `repos/szTheory/gabbaboy/actions/runs/40257161612/attempts/1/jobs?per_page=100` |
| ci_run | `repos/szTheory/gabbaboy/actions/runs/40259198255` (v0.2.1 source CI push run) |
| commit | `repos/szTheory/gabbaboy/commits/v0.2.1` |

Release asset downloads are not stored: the bytes are replaced by fixture bytes, and only the asset row shape
(`url`, `browser_download_url`, `digest`, `size`) is captured.

## API version

`X-GitHub-Api-Version: 2022-11-28` (the default REST version for `gh api` at capture time, 2026-10-29), recorded as
`api_version` in the file and checked by `--check-capture`.

## Sanitization

Applied by `verify-release-lifecycle.py --sanitize-capture RAW_DIR captured.json` (function `sanitize`; every rule
has a negative control in `--self-test`). The raw responses are not stored.

- every email-shaped string becomes `redacted@example.invalid`; git author and committer names become `Sanitized Author`
- user objects other than the repository owner, the `github` organization and `[bot]` accounts are replaced by a
  fixed placeholder with the same members
- release and pull-request `body` text, commit `patch`, `signature` and `payload`, and runner names and ids are
  replaced by a fixed marker or zero; messages and titles are cut at 200 characters
- arrays are cut to the bounds recorded in `sanitizer.truncated` of the file (assets 2, workflow runs 2, jobs 8,
  artifacts 2, commit files 1, job steps 2, check runs: the three required contexts plus one other); `total_count`
  fields keep their real values
- no member is added, renamed or removed otherwise: in particular a check run keeps `url`, `html_url`, `check_suite`,
  `app`, `head_sha`, `status` and `conclusion` and carries no `repository` member, because GitHub returns none
- the checker rejects the file if it contains a local path marker, a credential marker, an email other than the
  redacted one, CRLF, more than 262144 bytes, a digest that differs from the line above, or a missing required member

The repository owner login `szTheory` is kept because it is the repository identity (`szTheory/gabbaboy`), which the
production verifiers pin and derive from the check-run `url` and `html_url` prefixes.

## v0.3.0 first post-tag failure (additive fixture)

- `v030-notes-failure.json` sha256: 4c1bd56c9fdf07103f72e71560287cf8c01d9c5b1519eaab35545a0e499ee148
- bytes: 53859 (bound: 262144)
- format: UTF-8 JSON, sorted keys, two-space indent, LF line endings
- API version: `X-GitHub-Api-Version: 2022-11-28`

The failure snapshot is the retained first-run evidence: draft detail GET
`repos/szTheory/gabbaboy/releases/429606490`, empty asset-list GET
`repos/szTheory/gabbaboy/releases/429606490/assets?per_page=100`, workflow-run GET
`repos/szTheory/gabbaboy/actions/runs/41148606886`, and candidate-job GET
`repos/szTheory/gabbaboy/actions/jobs/124379552103`. The run failed at the actual
`Require final release notes to satisfy the v0.2 adoption contract` step with
`release-notes-absence-missing`; the draft was unpublished and had no assets. These
are digests of the retained sanitized-input files, not claimed wire-body digests.
The exact UTF-8 notes body is preserved separately in the fixture because the
existing sanitizer intentionally replaces API `body` members.

The candidate-identity list response was not present in the first-run snapshot. A
new bounded read-only GET to
`repos/szTheory/gabbaboy/releases?per_page=100` was captured at
`2026-10-31T00:48:23Z`, after the failure, with five entries. The fixture preserves
that response shape after the same sanitizer and records the raw response SHA-256;
the capture time is distinct from the failure snapshot and is not used to rewrite
its historical state.

Sanitization reuses `verify-release-lifecycle.py`'s existing `sanitize` function:
API bodies are omitted, email-shaped strings are redacted, non-owner user objects
are replaced with same-shape placeholders, runner identifiers are removed, and
bounded API arrays are truncated with the actual counts recorded. The separately
retained failed notes include the SHA-256 of their exact UTF-8 bytes and the digest
of the saved release-detail capture from which the body was taken. The frozen
reviewed body has SHA-256
`71003d07287066ef740a10c62238ef25d9ef054a7e84064caf46b7467fe39202` and contains
the exact tag-pinned support-ledger URL once; the recovery checker derives its
repair only from the original tagged section and the one specified link change.

The source section at tag `v0.3.0` / S has SHA-256
`187fb676dc1717e6582aa16f27a26f3932c29f29b5049aa3d59ecebdb934a4be`. Replacing
only `[support ledger](docs/support/v0.3.0.md)` with
`[support ledger](https://github.com/szTheory/gabbaboy/blob/v0.3.0/docs/support/v0.3.0.md)`
produces SHA-256
`ab81ea7e6164964957a13676060f8741095635127a5afa19d8e8f90f4c2a6784`.

## Provenance

Captured 2026-10-29 by the repository's Phase 19 release-lifecycle work from the repository's own public history with
read-only GitHub API GETs. The data describes the published, immutable v0.2.1 release, its merged pull request and
release rehearsal attempt. The replay uses these objects as shape templates and retargets their identities (tag, ids
and SHAs) to fixture releases and runs; no captured value is trusted as evidence about a live release.
