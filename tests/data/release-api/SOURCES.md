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

## v0.3.0 draft tag-association restoration (additive fixture)

- `v030-draft-association-restoration.json` sha256: db51ac4f33395dac233520f78d8a2b91c680594ceafd3f5df296adf1f7689f05
- bytes: 6774 (bound: 262144)
- format: UTF-8 JSON, sorted keys, two-space indent, LF line endings
- API version: `X-GitHub-Api-Version: 2022-11-28`

This is a bounded projection of actual GitHub API observations for the existing
unpublished release ID `429606490`; it is not a response-shape mock. The fixture
stores the nine release fields read by the restoration guard (`id`, `tag_name`,
`target_commitish`, `name`, `body`, `draft`, `prerelease`, `published_at`, and
`assets`). It replaces body text with its UTF-8 SHA-256 and the empty asset array
with its count. No raw release body, request body, user object, response envelope,
local file name, credential or personal identifier is copied into this fixture.

The first observation comes from the retained body-only metadata update. Its
request had only the `body` member (1813 bytes; SHA-256
`d9c7505dcc68b1e4d05b21a6870140f026dfcdecf13c44389e38c7cd2eb84967`). The
pre-PATCH release response SHA-256 was
`67dd8e89c156b026b078e53a2b424698787737184db484abb85ab3385025d93d`. The actual
PATCH returned HTTP 200 with response SHA-256
`4697bcc10c59a576d4f3bd959579ccd132fad323363ada6b848ac6e346867d84`; its tag
changed from `v0.3.0` to `untagged-bff38b7645da850c79be` as the repaired body
was installed. The recorded operator stopped with
`release is not the same unpublished empty v0.3.0 draft` before dispatch.

The D132 read-only follow-up made eleven GETs and no PATCH, then stopped with a
`TypeError` at the UTF-8 adoption boundary. Its sanitized release-response
digest is the same actual drift state above; its run-record SHA-256 is
`ed1df67d702b1ce6128efa920b25870a2899cda4cf9ef347cced48ef0b7c9934`.

The D133 restoration request was exactly `{"tag_name":"v0.3.0"}` with final LF
(22 bytes; SHA-256
`9369228a1035720e68125af98e7758717f315c6b1124d073cb5e2abc814af72e`). The
same-ID PATCH returned HTTP 200 with response SHA-256
`9d3f3be4a52be94c4e47848f11e67fc3a831441f1a075ea7e74b5b4fe0d8b71b`. The
independent GET returned the same release-response digest; the Git tag remained
at S, the asset endpoint remained empty, the release list had one `v0.3.0` row
for the same release ID, and the actual CLI detail view reported a draft, not a
prerelease. The pre-restoration release-list capture SHA-256 was
`34203f9d011f8a4c3ef66fe30ba318aef77250114918faf93eecc60b6022f7c5`; the
post-restoration release-list capture SHA-256 was
`aa51f9a29c6ec539ca46f0b6370e0cee5cbdbe650db7ad9229c8d764741a1a6d`. Of the
nine guarded release fields, `tag_name` was the only field that changed; the other eight, including the repaired body digest
`ab81ea7e6164964957a13676060f8741095635127a5afa19d8e8f90f4c2a6784`, were
identical before and after. The operator recorded
`restored-readback-verified-no-dispatch`, adoption pass, and dispatch `none`.
The fixture records only this restoration readback; it contains no retry result,
publication result, or phase-completion claim.

The API exposes `body` as a JSON string while the production adoption checker
accepts UTF-8 bytes. The captured D132 `TypeError` is retained as the regression
case. The fixed operator's private full-main replay used the actual G/S Git
objects and production checker with `gh` intercepted and a temporary marker;
its report SHA-256 is
`a9b99aec1b633fae4fd6d53d4eecfd9904937b0ab60649186ba92bd378e07bb1`. That
private replay's simulated PATCH is not used as fixture data or counted as a
live observation. The actual D133 operator result separately records successful
adoption before and after restoration against the same body bytes.

The fixture is an explicit allowlist projection generated from the retained
`body-patch-G/`, `association-preflight-D132/`, and
`association-restoration-D133/` captures. Each included response digest is the
digest of its retained raw response bytes; other response members are omitted.
The sanitized capture can prove the recorded one-field requests, HTTP statuses,
same-ID state transition, nine-field comparison, empty assets, and refusal/no-
dispatch boundaries. It cannot prove successful publication or completion of
the separately handled retry.

## Provenance

Captured 2026-10-29 by the repository's Phase 19 release-lifecycle work from the repository's own public history with
read-only GitHub API GETs. The data describes the published, immutable v0.2.1 release, its merged pull request and
release rehearsal attempt. The replay uses these objects as shape templates and retargets their identities (tag, ids
and SHAs) to fixture releases and runs; no captured value is trusted as evidence about a live release.
