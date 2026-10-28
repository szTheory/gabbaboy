# Captured GitHub API responses

`captured.json` holds read-only, sanitized, bounded GitHub REST responses for the public repository
`szTheory/gabbaboy`. The release lifecycle replay (`tests/scripts/verify-release-lifecycle.py`) serves response
shapes derived from it so that the production attach, manifest, final-gate and publish-decision code runs against the
real object schemas (run, job, artifact, check run, pull request, release and release asset) and not against shapes
invented to satisfy a verifier. It proves deterministic logic. It does not prove live GitHub permissions.

- captured.json sha256: 8f0f8f8b231f5b34df29b256cd9f64e417927325ed68d2f81d901524032ddcf5
- bytes: 108510 (bound: 262144)
- format: UTF-8 JSON, sorted keys, two-space indent, LF line endings (`.gitattributes` pins `eol=lf` so the digest is stable on Windows)

## Endpoints

Each was read once with `gh api` (HTTP GET, no mutation, no authentication material stored). Identity captured:
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
| commit | `repos/szTheory/gabbaboy/commits/v0.2.1` |

Release asset downloads are not stored: the bytes are replaced by fixture bytes, and only the asset row shape
(`url`, `browser_download_url`, `digest`, `size`) is captured.

## API version

`X-GitHub-Api-Version: 2022-11-28` (the default REST version for `gh api` at capture time, 2026-10-28), recorded as
`api_version` in the file and checked by `--check-capture`.

## Sanitization

Applied by `verify-release-lifecycle.py --sanitize-capture RAW_DIR captured.json` (function `sanitize`; every rule
has a negative control in `--self-test`). The raw responses are not stored.

- every email-shaped string becomes `redacted@example.invalid`; git author and committer names become `Sanitized Author`
- user objects other than the repository owner, the `github` organization and `[bot]` accounts are replaced by a
  fixed placeholder with the same members
- release and pull-request `body` text, commit `patch`, `signature` and `payload`, and runner names and ids are
  replaced by a fixed marker or zero; messages and titles are cut at 200 characters
- arrays are cut to the bounds recorded in `sanitizer.truncated` of the file (assets 2, workflow runs 2, jobs 2,
  artifacts 2, commit files 1, job steps 2, check runs: the three required contexts plus one other); `total_count`
  fields keep their real values
- no member is added, renamed or removed otherwise: in particular a check run keeps `url`, `html_url`, `check_suite`,
  `app`, `head_sha`, `status` and `conclusion` and carries no `repository` member, because GitHub returns none
- the checker rejects the file if it contains a local path marker, a credential marker, an email other than the
  redacted one, CRLF, more than 262144 bytes, a digest that differs from the line above, or a missing required member

The repository owner login `szTheory` is kept because it is the repository identity (`szTheory/gabbaboy`), which the
production verifiers pin and derive from the check-run `url` and `html_url` prefixes.

## Provenance

Captured 2026-10-28 by the repository's Phase 17 release-lifecycle work from the repository's own public history,
using the maintainer's authenticated `gh` session for rate limits only. The data describes a published, immutable
release and its merged pull request; the replay uses it as a shape template and retargets the identity (tag, ids and
SHAs) to a fixture release, so no value in the captured file is trusted as evidence about a live release.
