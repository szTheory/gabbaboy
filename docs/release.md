# Release, downloads, and recovery

GabbaBoy v0.2 is a limited, bootless software preview with a DMG-CPU-B and a
selected CGB-CPU-E software model. Find the current candidate or published
release under the repository's GitHub Releases page; it is the only record of
what has been published, and this page makes no publication claim for v0.2.0.
The release notes identify the version and list assets. The package
matrix is Linux x64, macOS arm64, and Windows x64 core archives; the optional
SDL3 player archive is macOS arm64 only. These are tested runner/configuration
combinations, not minimum OS versions, all-architecture promises, or general
platform support floors. The C core itself has no SDL runtime dependency.

## Source archives and product packages

GitHub generated source archives retain the admitted licensed fixtures and
their notices, because they are a snapshot of the whole repository tree. Those
third-party and author-test ROMs are repository test fixtures: they are listed
with their rights and digests in
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md). The installed and downloaded
product packages remain fixture-free: they carry only the original
project-authored tracer, visible demo and MBC1 continuation fixtures, and a
policy scan fails a package that contains any other fixture ROM. A source
archive therefore answers "what may I rebuild and test", and a product package
answers "what do I run"; neither is a substitute for the other.

## Verify and unpack

Download the asset for your runner and its matching `.sha256` file where
provided. Check it before extraction (for example,
`sha256sum --check gabbaboy-core-macos-arm64.tar.gz.sha256`; use the platform's
SHA-256 utility on macOS/Windows). The release's candidate/platform manifest,
build receipts, and `support-ledger.json` (named `support-ledger-v0.1.0.json` on v0.1.0) provide additional provenance;
compare each asset name and digest with the downloaded bytes.

Native proof comes in two kinds that are kept apart. The installed-prefix check
installs the build, relocates the prefix and runs C and C++ consumers against
it, which shows that the package layout works. The downloaded-asset check runs
the same consumers against the release archive's own bytes after download,
which shows that the distributed file works. A passing installed-prefix check
does not stand in for the downloaded-asset check.

The tagged release evidence is bound to the exact tag and source revision:
`support-ledger.json` binds the applicable ledger blob and the fresh corpus
receipt, and `release-performance-receipt.json` records the paired v0.1.0
comparison for that source. The bounded fuzz campaign receipt
`v02-fuzz-receipt.json` is a release requirement that is attached only after an
actual campaign passes on the exact source; no fuzz campaign result is claimed
by this document. The support
sidecar is generated after the tag. It records the exact source SHA and the
Git blob digest of the applicable tagged ledger, plus fixture and corpus
identity. A release binds the newest `docs/support/vX.Y.Z.md` at or below its
own version: ledgers are added when the support scope changes, so a fixes-only
patch release (for example v0.1.1 or v0.1.2) binds the unchanged
[`docs/support/v0.1.0.md`](support/v0.1.0.md) and records both versions.
The source ledger intentionally does not contain its future commit SHA, so its
own source can be reviewed before tagging without a self-reference.

## Support-ledger generator and managed inputs

`python3 -I tests/scripts/verify-support-ledger.py --write-current --receipt
build/cgb-corpus-receipt.json` renders the versioned support ledger for the
tree's own version. The historical performance disclosure below is part of that
generator output, not prose added afterwards: its facts live in
[`tests/data/release-disclosure.json`](../tests/data/release-disclosure.json)
and are rendered into every generated ledger. The input is validated before it
is used. Every field is classified, and the candidate and baseline source
identities must be the commits of the `v0.2.0` and `v0.1.0` tags, and the
fixture digest must be the candidate-source blob's digest, all read from Git
objects. A current advisory interpretation is rendered only for ledgers after
the last tagged one (v0.2.1); it states that paired wall-clock timing is
advisory and that the instruction-count ratio and realtime floor remain
blocking. It never rewrites the historical metric.

To preview without touching a tracked file, add `--output PATH`; the default
target is refused when that version already has its tag, because a tagged
ledger's bytes are historical. A generated ledger is accepted only if
rendering its own structured data reproduces its exact bytes, so a hand edit
(including a hand-inserted disclosure) is rejected.

```sh
python3 -I tests/scripts/verify-support-ledger.py --check-disclosure
python3 -I tests/scripts/verify-support-ledger.py --self-test-disclosure
```

The first command requires the tracked v0.2.0 and v0.2.1 ledgers to be exact
generator output, the v0.2.1 ledger to equal its tag blob, and the adoption
verifier to accept the result. The second runs omission, altered-value,
unbound-source, handwritten-bypass and tagged-rewrite controls. Both run as the
`release_disclosure_generator` and `release_disclosure_controls` tests.

## Version-PR content window

A version PR is generated content. release-please rewrites `CHANGELOG.md`, the
version files and the PR body, and the support ledger is rendered from the
managed generator inputs above. A short review freeze therefore protects exact
content, never elapsed time: no clock, expiry or run counter appears in the
record or in any proof of it.

The freeze begins only after the managed outputs are generated and the checks
and rehearsal are green on one exact head. It ends immediately when main, the
source tree, the release notes, a generator input or the regenerated PR body
changes. Only the window record itself may differ between the reviewed head and
the revision being merged. The window is reopened only by regenerating the
managed outputs, recomputing the digests and rerunning the exact-head required
checks and rehearsal. Required checks are never disabled, and release-note paths
are never excluded wholesale, to make a window easier to hold.

The record is [`tests/data/version-window.json`](../tests/data/version-window.json).
In normal development it is the inactive example: every window field is null and
the record cannot assert a frozen identity or release readiness. An active record
carries the release version, the frozen head and main base, the SHA-256 of each
managed generator input (the disclosure input, the ledger generator and the
release-please configuration), the SHA-256 of each regenerated file (the ledger,
`CHANGELOG.md` and the manifest) and of the PR body, and the exact-head review and
rehearsal run identities.

```sh
# draft the digests of a freshly regenerated head, then fill in the run identities
python3 -I tests/scripts/verify-version-window.py --rev HEAD_SHA --base MAIN_SHA \
  --body pr-body.md --pull-request N --ci-run-id ID --rehearsal-run-id ID --digest
# judge the committed record at the revision about to merge
python3 -I tests/scripts/verify-version-window.py --rev REV_SHA --base MAIN_SHA \
  --check tests/data/version-window.json --body pr-body.md
```

The PR body is compared after normalizing line endings and trailing newlines
(`gh`, the API and the web editor differ in both); every other byte of it is
reviewed content.

`--rev` and `--base` are full 40-hex commits. The record, the generator inputs and
the regenerated files are read from Git objects at `--rev`, so the working tree
is never a fallback. The checker proves content bindings only; the recorded run
identities name hosted evidence that the required checks on the exact head, not
this script, authenticate. The `release_window_contract` and
`release_window_controls` tests cover the tracked record and the body-overwrite,
stale-head, stale-input, changed-path, regeneration-mismatch and revalidation
cases.

### Production regeneration route and operator sequence

The `version-window` job in `.github/workflows/release-please.yml` runs after the
`release` job, on every push to main, so it judges the version PR that
release-please has just regenerated. With no open version PR, or with the
inactive record (the normal state), it passes and the existing release policy is
unchanged. With an active record it runs the checker from the trusted main
commit against the version-PR head, which is checked out as data and never
executed, and the job fails while the freeze is broken. It cannot be skipped by
a failed release job, a paths filter on the trigger, a masked failure
(`|| true`, `continue-on-error`) or a path exclusion in
`release-please-config.json`; `.github/scripts/verify-workflow-policy.py`
enforces each of these. A regenerated body, a moved main or any changed source,
release note or generator input therefore invalidates the old reviewed digests
rather than preserving stale hand edits. Phase 17 does not open, regenerate or
merge a live version PR and ships only the inactive record.

For a future version PR, in order:

1. Let release-please regenerate the PR, then render the ledger with
   `--write-current` from the managed inputs; commit no hand-edited generated
   file.
2. Run the required checks on that exact head and push the matching
   `rehearsal/vX.Y.Z` branch for the rehearsal.
3. When both are green on the same head, run `--digest` for that head, main and
   the PR body, fill in the run identities, and commit only the resulting
   `tests/data/version-window.json` as the next commit. Run `--check` on that
   commit before asking for merge.
4. Any later change reopens the work: regenerate, repeat steps 1 to 3 on the new
   exact head, and merge only a commit whose `--check` passes with the current
   main.

The six release-bound timeout citations tracked as RM-027 are separate and
remain an entry blocker for Phase 19; nothing here closes them, and the window
gate has per-step timeouts because a new job has no completed run to cite in
`.github/ci-timeouts.json`.

## Evidence lifecycle and its local replay

The attach, platform-manifest, final-gate and publication steps of
`.github/workflows/release.yml` are the modes of
`.github/scripts/release-evidence-lifecycle.sh` (`attach-evidence`,
`validate-evidence`, `build-manifest`, `validate-draft`, `final-gate`,
`nightly-gate`, `publish-draft`). The workflow runs each from the trusted checkout, and the
workflow policy judges every call as the body that runs, so the extracted code
cannot be unused, misplaced or run from the tagged tree.

`tests/scripts/verify-release-lifecycle.py` replays that lifecycle before a tag
exists. It runs the production script and gates from a non-git workspace for the
attacher and from a tag checkout for the judge jobs, with `GH_REPO` explicit,
against a `gh` stand-in that serves response shapes taken from the sanitized
captures in `tests/data/release-api/` (see its `SOURCES.md` for endpoints,
sanitization and digest) and refuses any endpoint, repository, flag, mutation or
reshaped response it was not told about. The publish command is intercepted and
recorded as a decision; nothing reaches the network or a real tag, release or
asset. The replay proves deterministic logic. It does not prove live GitHub
permissions, hosted runner behavior, or the real corpus, fuzz, performance and
archive owner validators (the delivery self-test runs those).

On a retry the evidence a failed attempt already attached is downloaded and
judged first by `verify-release-gates.sh --check-attached-evidence` (tag and
source identity, the sidecar's binding to the attached corpus receipt, each
digest GitHub reports, and the allowed inventory). Only then do the identical
attached bytes replace the regenerated run-specific copies; nothing is uploaded,
replaced or deleted, and a refusal leaves the regenerated evidence untouched.
The platform-manifest step accepts the final receipts of an earlier attempt, so a
retry that stopped after the final upload can reach the publish job, whose
recovery decision then compares them byte for byte.

## Owner approval of a deterministic Ir exception and the nightly replay gate

Two gates live in `tests/scripts/verify-release-gates.py` (stdlib only, refuses
`python -O`, every refusal is `REJECT code: reason` with exit 1).

**Ir exception approval.** Ordinary advisory paired timing never needs an
approval and no approval can excuse a wrong correctness digest, a failed safety
check or a realtime miss: `verify-perf-gate.py` still judges all of those. The
only approvable event is a deliberate widening of `ir_ratio_limit`. The
evaluator writes the exact measurement the owner approves
(`--evaluate ... --emit-exception-measurement FILE`, which still refuses the
unapproved widening), `verify-release-gates.py --digest --measurement FILE`
prints its full canonical digest, and the owner comments on the recorded review
issue with the exact wording the gate derives from the decision (the full
digest, the approved limit, the accepted cause and its reference, and the
per-ROM ratio bands). `--review-approval --comment-json FILE --decision FILE
--measurement FILE --rev SHA [--output FILE --exception-receipt FILE]` requires
`author_association` `OWNER`, the stored issue URL and number, a comment newer
than the issue, empty owner fields, a measurement taken at `--rev`, and that
exact wording (a wrong, prefix-only or absent digest, a changed cause, limit or
band all refuse). Only after every check does it copy the verified comment's
identity, link and time into new files; the input is never edited and a refusal
writes nothing. `tests/scripts/run-perf-gate.sh --gate` is the production path:
with the two exception environment variables named in its header set (the saved
owner comment and the decision file) it asks the gate for the receipt and hands
only that receipt to the ratchet.

**Nightly replay gate.** Before the one publication transition the
`nightly-gate` lifecycle mode runs `--nightly-gate --runs-json FILE --run-json
FILE --head SHA --output FILE [--rev SHA --branch NAME]` on saved `gh run list`
and `gh run view` JSON. The head is the rehearsed head proved to have the
tagged tree. The newest eligible `nightly-asan` run at that head must be
completed with success and its `asan-full-replay` job must have succeeded (a
skipped job does not count). A newer red or in-progress run at the head, a
newer run at another head, no run at the head, a different tree than the tagged
source and out-of-order timestamps all refuse, and the source-bound receipt is
written exclusively and on success alone. `verify-state-contract.py --boundary
--rev SHA` reads a phase boundary (plans, summaries, requirements, route flags,
receipt timestamps and the Phase 16 receipts) from that one commit and never
from the live tree or later ancestry.

The six `release_bound` rows of `.github/ci-timeouts.json` remain a named Phase
19 entry blocker (RM-027): they must be replaced by verified tree-equality
citations before `VERSION` exceeds 0.2.1, and the boundary check refuses a
seventh row or a version that moved past 0.2.1 with any row left.

## Performance measurement and qualification

The v0.2.0 DMG paired performance comparison is historical evidence: it reported
the candidate as **+14.86% slower than v0.1.0 with a ±1.62% margin**. Keep that
result separate from any fresh measurement; it is not a current approval or a
substitute for rerunning the benchmark on the candidate source.

The archived v0.2.0 performance receipt compares candidate source
`ab301aa69b1f085050fd66bf7b1378863a0821f2` with baseline source
`e30d168f7fc61de8db0a3801e7b1736362912cb7`. It measures workload
`original-wram-tracer-1m-half-dots-v1` on DMG-CPU-B using
`fixtures/tracer/tracer.gb` (SHA-256
`ded6a499118b57539710892d58b4d7ced2269f08d447eed1451201d8ad65ec8d`), a
1,000,000 half-dot budget, and correctness digest `4c7a57ff3d50d228`. The
Linux x86_64 run used 30 paired samples after 3 warmups and recorded
**+14.86% slower** with an approximate 95% mean margin of ±1.62%; its
historical disposition was `accepted-with-disclosed-regression`. This
source-bound result describes that historical comparison only. It is not a
current approval, fresh result, or equivalent-speed claim.

The hosted instruction-count gate (cachegrind Ir against a v0.2.0 build made in
the same job) is a regression tripwire, not a performance claim; its blind spots
and rejection codes are in the limitation note in
[`tests/baseline/perf-gate-v1.txt`](../tests/baseline/perf-gate-v1.txt).

Start a fresh measurement from the checkout being evaluated:

```sh
bash tests/scripts/measure-release-baseline.sh --qualify-v02 \
  --output /tmp/v02-performance-measurement.json
```

The receipt records baseline and candidate revisions, build and compiler
identities, hardware class, the frozen workload and output digest, warmups,
paired samples, and uncertainty. The existing regression trigger is unchanged:
the median must exceed 105% of baseline and remain above 100% after subtracting
the approximate 95% mean margin. If it does not fire, the producer exits zero
and writes an untriggered receipt. If it fires, the producer writes a schema-v2
`pending-investigation` measurement and exits nonzero. A supplied
`--review-regression` note is retained only as a compatibility argument for
existing callers; its prose is untrusted and cannot qualify a triggered result.

Only a separately recorded decision from an actual independent reviewer can
turn that exact pending measurement into a qualifying receipt. Keep the review
record outside the source checkout. It must identify the decision and reviewer,
link the review record, state its timestamp and rationale, and bind the full
canonical measurement receipt digest, source pair, workload, measured summary,
and uncertainty. After the independent reviewer has recorded a decision, apply
that file and verify the resulting receipt:

```sh
python3 -I tests/scripts/verify-v02-performance.py --apply-decision \
  --measurement /tmp/v02-performance-measurement.json \
  --decision /secure/review/performance-decision.json \
  --output /tmp/v02-performance-qualified.json
python3 -I tests/scripts/verify-v02-performance.py --verify \
  /tmp/v02-performance-qualified.json
```

The qualified receipt retains the original pending measurement and checks that
the decision still matches its receipt digest and evidence. The verifier checks
the supplied review record's shape and bindings; it cannot authenticate the
reviewer's identity or prove that an external link represents a real
independent review. Do not create a review record on a reviewer's behalf or use
a self-test fixture as approval.

The release rehearsal carries that decision through the hosted workflow without
creating one. A rehearsal run whose paired measurement is `pending-investigation`
still uploads the measurement as an artifact (`if: always()`, seven days). After
the independent reviewer has recorded a decision outside the checkout, dispatch
`release-rehearsal.yml` on the same `rehearsal/vX.Y.Z` branch with the inputs
`measurement_run_id` (the run that produced the pending measurement) and
`performance_decision` (the decision as a JSON string). The step downloads that
artifact, requires that run to be a `release-rehearsal` run on a commit with the
same tree as this run, applies the decision as shown above, verifies
the result and uploads the qualified receipt. With neither input the step is
the plain paired measurement.

The release workflow may reuse the performance receipt of a rehearsal run instead
of measuring again, but only under a judge it takes from the trusted workflow
revision. It considers the newest successful run of `release-rehearsal.yml` on
`rehearsal/vX.Y.Z` and requires a push or manual dispatch of this repository (no
fork), a completed successful conclusion, and a head that is the tagged commit or
has exactly the tagged tree, proved from git objects. It then requires the one
artifact that exact run and attempt uploaded. If the newest run is stale or any
check fails, the release measures afresh and never falls back to an older run or
trusts a branch or artifact name alone.

`release.yml` reuses that qualified receipt for the paired gate only when
`python3 -I tests/scripts/verify-v02-performance.py --verify-reuse PATH --tag-tree TREE`
accepts it, which requires a fully verified `passed` receipt whose measured
candidate tree equals the tag's tree (`reuse-tree-mismatch` otherwise). A
missing, expired, pending or unequal-tree receipt means the release measures
fresh, exactly as before. The paired wall-clock gate and its trigger thresholds
are unchanged.

The attach and evidence gate applies the same rule. `verify-v02-delivery.py
--check-evidence` accepts a performance receipt whose candidate SHA differs
from the tag source (a rehearsal head is never an ancestor of a squash-merged
tag) only when the receipt's `candidate.tree_sha` and the tree of the commit it
names both equal the tag source's tree, and the performance owner's
`--verify-reuse PATH --tag-tree TREE` then accepts it as a fully verified
`passed` receipt. A different tree, a pending or unqualified receipt, a
tampered decision or digest, or a missing receipt is rejected
(`performance-binding` or `owner-performance`). A fresh measurement taken
inside the release would re-trigger the review with a digest no earlier
decision binds, so the supported route is: measure in the rehearsal, record the
independent decision, qualify through the rehearsal, then tag a source with the
same tree.

An `evidence-reuse.json` record beside the evidence remains accepted for the
ancestor route (a justified producer SHA that is an ancestor of the tag source
with every covered input unchanged). No workflow produces it; it is kept for a
hand-reviewed ancestor case and takes precedence over tree equality when
present.

Schema-v1 receipts can be inspected only with
`python3 -I tests/scripts/verify-v02-performance.py --verify-historical PATH`.
That mode identifies legacy evidence as historical and pins it to the original
v0.2.0 source; it cannot satisfy current qualification. The regular `--verify`
mode accepts current schema-v2 receipts only.

Extract an archive into a new directory. Keep the core's `include`, `lib`, and
CMake package metadata together; configure consumers with
`-DCMAKE_PREFIX_PATH=<that-prefix>` and link `GabbaBoy::core`. The installed C
example in [`native-integration.md`](native-integration.md) shows instance
ownership, half-dot bounded execution, timestamped input, caller-owned frame
and audio buffers, and host-managed battery import/export. It is designed to
build and run outside the source and build trees. For source builds, follow the
top-level [build instructions](../README.md); SDL is only needed for the
optional player.

## Trust and macOS launch state

The macOS player is a command-line `.tar.gz` package, not a disk-image installer
or signed app bundle. The release is unsigned and not notarized unless its
release record explicitly reports successful verification of the exact final
bytes. A successful compile or smoke test does not establish Apple signing or
notarization. macOS security policy may warn or refuse execution of a
downloaded unsigned binary. Do not disable Gatekeeper globally. If policy
blocks the binary, use a locally built trusted binary or request a properly
signed release; the project does not claim a universal bypass procedure.

The package smoke uses SDL dummy audio/video and an offscreen software renderer.
It exercises the documented software path, including guest input, frame/audio
delivery, and save continuation; it does not establish physical-device,
perceptual, or hardware equivalence.

## Saves, upgrades, rollback, and recovery

The C core owns emulated cartridge RAM only. The embedding host owns save-file
location, format, validation, backup, and atomic replacement. The example
documents these responsibilities and transfers exactly the byte count
reported by `gbb_battery_size`; the core does not read or write files.

The SDL player stores identity-bound battery saves in its per-user preferences
directory. Before an upgrade, quit the player cleanly and back up that
application's save directory. Keep the backup until the new version opens the
same ROM and confirms progress. If rolling back, quit first and restore the
matching backup; do not run two writers against one save. The player's save
envelope is versioned and tied to the exact ROM bytes. A malformed or
wrong-identity save is preserved under a recovery name when safe preservation
succeeds; the player starts with fresh RAM and shows a warning instead of
silently importing it. Recovery files are not automatically loaded. See
[`cartridge-and-saves.md`](cartridge-and-saves.md) for the envelope and
recovery limits.

If a final save fails, the player pauses quit, reset, or ROM replacement and
offers retry, continue without saving, or cancel. Continuing without saving
may lose recent progress. Cancel keeps the session available for another save
attempt. See [`preview.md`](preview.md) for controls and player behavior.

## Support and troubleshooting

The versioned [support ledger](support/v0.2.1.md) records the bootless
DMG-CPU-B and CGB-CPU-E software models, the cartridge and save matrix, the
CGB test-ROM corpus rows, exclusions, and known issues; the earlier
[v0.1.0 ledger](support/v0.1.0.md) remains the record for that release. The
CGB corpus is a bounded set of test ROMs; its counts are software-model
results, not a game compatibility percentage. No CGB game-level evidence
exists. Physical CGB-E remains UNKNOWN/POLICY, and there are no physical DMG
observations and no broad game-library claim. Do not infer a minimum OS from a
runner label or one successful build.

- **Package not found by CMake:** point `CMAKE_PREFIX_PATH` at the extracted
  install prefix and keep its directory layout intact.
- **ROM rejected:** check the exact supported cartridge scope in
  [`cartridge-and-saves.md`](cartridge-and-saves.md); the file picker filter is
  not a compatibility promise.
- **No player audio:** check the player status/help. If no output device opens,
  the player discards and counts PCM while guest execution continues. Dummy
  audio is only a test backend.
- **Save warning or lock conflict:** close other GabbaBoy processes. Copy any
  recovery file before inspecting it; malformed records are not auto-loaded.
  Do not replace a save while another process is using it.
- **Unsigned player blocked:** use a local trusted build or await a signed
  release. Do not disable system security globally.
- **Unexpected behavior:** retain the version, platform, asset name and
  checksum, and report the issue through the repository's normal issue
  process. Never attach commercial ROMs, save files containing private data,
  or secrets.

Before a version PR is merged, push a `rehearsal/vX.Y.Z` branch, where `X.Y.Z`
is the tree's own version (CMake `project` VERSION, which must equal the
release-please manifest), to run `.github/workflows/release-rehearsal.yml`. The
workflow derives its runner-local tag from the branch name and refuses any other
ref or a ref for another version. It executes the corpus, support
sidecar, fuzz, paired performance, relocated-consumer and source-archive
producers on that commit with a read-only token and a runner-local tag, and it
never creates a tag, release or upload. It does not exercise the draft-bound
download, attach, final gate or publish steps. The fuzz producer takes the
qualified commit from an explicit source-commit variable because `GITHUB_SHA` is
runner-owned and cannot be overridden by a step.

Privilege is split so tagged code never holds release write authority for the
v0.2 evidence. The corpus and performance producers run tagged build, test and
measurement code with `contents: read`, no GitHub token in their environment and
no persisted checkout credential, and retain their receipts as run artifacts.
The two paired-performance producers additionally hold `actions: read`, with the
token in one `gh` step that fetches a pending measurement and runs no tagged
code; the step that applies a decision has no token.
The fuzz job executes no tagged code: it reads the completed exact-source
`ci.yml` push campaign through the trusted validator, and fails with a named
limitation when no such completed campaign exists. A separate attacher holds the
only write token for that evidence, runs no checked-out code, and attaches the
retained bytes without replacing an asset. The manifest and publisher jobs run
the release gate and delivery validators from a trusted checkout of the workflow
revision, with the tagged tree as data. The Linux, macOS and Windows candidate
jobs, the manifest job and the publisher still hold write authority while they
build, download or judge the tagged tree; that residual is named in
`.github/scripts/verify-workflow-policy.py`, which is enforced as an exact set
and is not a claim of closure. The policy judge, which reads workflows as data
and proves each required command is reachable and fatal (comments, `echo`, dead
branches, `|| true` and `continue-on-error` do not count), runs from the
default branch in the rehearsal `judge` job and as part of
`bash .github/scripts/verify-release-gates.sh --self-test`. Shared unprivileged
setup is `.github/scripts/produce-release-evidence.sh`.

The version PR is the final review point for `CHANGELOG.md`; release-please may
update it there. Its rendered release notes are checked with
`python3 -I tests/scripts/verify-v02-adoption.py --release-notes PATH`, which
requires the exact version, the sentence "No CGB game-level evidence exists.",
the unsigned/not-notarized statement and a link to the exact-version ledger. The merged, tagged changelog and that tag's release notes are
the public notes. The candidate is kept as one unpublished draft while exact
tag bytes are built, attached, downloaded, and smoked. Publication is a single
gated transition after all required checks and downloaded-byte tests pass.
Retries can reuse only that same draft, tag, source SHA, and previously
qualified byte-identical assets.
