#!/usr/bin/env bash
# The release evidence lifecycle: attach, platform manifest, final gates and the one publication transition (RM-028, D-20).
#
# Each mode below is the body of one release.yml step, moved here verbatim so that the production workflow and the local
# replay (tests/scripts/verify-release-lifecycle.py) execute the same commands. The workflow calls
#
#     bash trusted/.github/scripts/release-evidence-lifecycle.sh MODE
#
# from the trusted workflow revision (`trusted/`), never from the tagged checkout. Everything a mode needs arrives in the
# environment the workflow step already provided (GH_REPO, RELEASE_TAG, SOURCE_SHA, RELEASE_ID, RETRY, RUNNER_TEMP, ...) and
# in the working directory layout the earlier steps built (trusted/, build/). The `gh` executable on PATH is the only
# transport; the gates, validators and `trusted/` tree are the production files.
#
# Mode            Workflow job                    Purpose
# attach-evidence attach-v02-evidence             attach corpus, sidecar, fuzz and performance evidence; retry reuse
# validate-evidence candidate-platform-manifest   judge the attached evidence families against the tag source
# build-manifest  candidate-platform-manifest     validate the candidate asset set and attach the platform manifest
# validate-draft  publish-qualified-release       validate every downloaded byte, write SHA256SUMS and the release receipt
# final-gate      publish-qualified-release       recheck the final inventory and receipts
# nightly-gate    publish-qualified-release       the exact-tree nightly ASan replay gate, immediately before publication
# publish-draft   publish-qualified-release       the one draft-to-published transition, then published-asset readback
#
# policy: .github/scripts/verify-workflow-policy.py reads each region between its BEGIN and END marker as the body of the
# step that calls the mode, so the workflow rules keep judging the exact commands that run.
set -euo pipefail

lifecycle_attach_evidence() {
# BEGIN attach-evidence
set -euo pipefail
[[ "$GH_REPO" == szTheory/gabbaboy && "$GITHUB_REF" == refs/heads/main ]] || { echo "Evidence attachment runs only from trusted main workflow runs." >&2; exit 1; }
[[ "$RELEASE_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ && "$SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "Malformed release tag or source SHA." >&2; exit 1; }
[[ "$(gh api "repos/$GH_REPO/commits/$RELEASE_TAG" --jq .sha)" == "$SOURCE_SHA" ]] || { echo "Release tag does not resolve to the source SHA." >&2; exit 1; }
release_json=$(gh api "repos/$GH_REPO/releases?per_page=100")
[[ $(jq --arg tag "$RELEASE_TAG" '[.[] | select(.tag_name == $tag and .draft == true)] | length' <<<"$release_json") == 1 ]] || { echo "Expected exactly one unpublished draft." >&2; exit 1; }
release_id=$(jq --arg tag "$RELEASE_TAG" -r '.[] | select(.tag_name == $tag) | .id' <<<"$release_json")
if [[ -n "$INPUT_RELEASE_ID" ]]; then [[ "$release_id" == "$INPUT_RELEASE_ID" ]] || { echo "Retry release ID differs." >&2; exit 1; }; fi
assets=$(gh api "repos/$GH_REPO/releases/$release_id/assets?per_page=100")
present() { jq --arg name "$1" '[.[] | select(.name == $name)] | length' <<<"$assets"; }
corpus=$(present cgb-corpus-receipt.json); sidecar=$(present support-ledger.json)
[[ "$corpus" -le 1 && "$sidecar" -le 1 && "$corpus" == "$sidecar" ]] || { echo "Corpus receipt and support sidecar are duplicated or only partially attached." >&2; exit 1; }
fuzz=$(present v02-fuzz-receipt.json); performance=$(present v02-performance-receipt.json)
[[ "$fuzz" -le 1 && "$performance" -le 1 ]] || { echo "Draft has duplicate campaign or performance receipts." >&2; exit 1; }
# A retry rebuilds the corpus receipt and sidecar with per-run identity (nonce, run id, timestamps), so their bytes
# can never equal the ones a failed earlier attempt already attached, and the campaign and performance receipts
# follow the newest CI and rehearsal runs. On a retry the attached bytes are the qualified bytes: they replace the
# regenerated copies here (never the other way round, and nothing is uploaded or replaced by this block). They are
# still judged against the tag source by --check-v02-evidence in the platform manifest and final gates.
# The attached bytes are fetched first and judged on their own, BEFORE any regenerated copy is replaced: identity,
# bindings, digests and the allowed inventory are read from the attachments and the live release, never from the copies
# a producer just made, and a refusal leaves the regenerated evidence untouched. Only then are they reused.
if [[ "${RETRY:-}" == true ]]; then
  for pair in "build/evidence-corpus support-ledger.json" "build/evidence-corpus cgb-corpus-receipt.json" "build/evidence-fuzz v02-fuzz-receipt.json" "build/evidence-performance v02-performance-receipt.json"; do
    read -r dir name <<<"$pair"
    if [[ "$(present "$name")" == 1 ]]; then
      mkdir -p "$RUNNER_TEMP/attached-$name"
      gh release download "$RELEASE_TAG" --repo "$GH_REPO" --pattern "$name" --dir "$RUNNER_TEMP/attached-$name"
      test -s "$RUNNER_TEMP/attached-$name/$name"
    fi
  done
  gh api "repos/$GH_REPO/releases/$release_id/assets?per_page=100" > "$RUNNER_TEMP/attached-assets.json"
  bash trusted/.github/scripts/verify-release-gates.sh --check-attached-evidence "$RELEASE_TAG" "$SOURCE_SHA" "$RUNNER_TEMP/attached-assets.json" "$RUNNER_TEMP"
  for pair in "build/evidence-corpus support-ledger.json" "build/evidence-corpus cgb-corpus-receipt.json" "build/evidence-fuzz v02-fuzz-receipt.json" "build/evidence-performance v02-performance-receipt.json"; do
    read -r dir name <<<"$pair"
    if [[ "$(present "$name")" == 1 ]]; then
      cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"
    fi
  done
fi
# Recovery is decided from independently read live state BEFORE any evidence write: an attachment whose bytes
# differ from the retained producer bytes, a concurrent release writer or a stale attempt stops here.
python3 -I trusted/.github/scripts/verify-published-release-assets.py --inventory "$RUNNER_TEMP/expected-inventory.json" build/evidence-corpus/support-ledger.json build/evidence-corpus/cgb-corpus-receipt.json build/evidence-fuzz/v02-fuzz-receipt.json build/evidence-performance/v02-performance-receipt.json
bash trusted/.github/scripts/verify-release-gates.sh --check-recovery "$release_id" "$RELEASE_TAG" "$SOURCE_SHA" "$RUNNER_TEMP/expected-inventory.json" "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" subset > "$RUNNER_TEMP/recovery-decision.txt"
decision=$(cat "$RUNNER_TEMP/recovery-decision.txt")
[[ "$decision" == draft-reuse || "$decision" == draft-upload-missing:* ]] || { echo "Unexpected recovery decision: $decision" >&2; exit 1; }
missing=",${decision#draft-upload-missing:},"
attach() {
  # $1 artifact directory, $2 asset name; the receipt that marks a pair complete is attached last.
  count=$(gh api "repos/$GH_REPO/releases/$release_id/assets?per_page=100" | jq --arg name "$2" '[.[] | select(.name == $name)] | length')
  [[ "$count" == 0 ]] || { echo "Evidence asset appeared during attachment: $2" >&2; exit 1; }
  gh release upload "$RELEASE_TAG" "$1/$2" --repo "$GH_REPO"
}
readback() {
  mkdir -p "build/readback-$2"
  gh release download "$RELEASE_TAG" --repo "$GH_REPO" --pattern "$2" --dir "build/readback-$2"
  test -s "build/readback-$2/$2"
  [[ "$3" == reused ]] || cmp -s "$1/$2" "build/readback-$2/$2" || { echo "Attached $2 differs from the retained producer bytes." >&2; exit 1; }
}
for pair in "build/evidence-corpus support-ledger.json $sidecar" "build/evidence-corpus cgb-corpus-receipt.json $corpus" "build/evidence-fuzz v02-fuzz-receipt.json $fuzz" "build/evidence-performance v02-performance-receipt.json $performance"; do
  read -r dir name _ <<<"$pair"
  test -s "$dir/$name"
  if [[ "$missing" == *",$name,"* ]]; then attach "$dir" "$name"; state=fresh; else state=reused; fi
  readback "$dir" "$name" "$state"
done
# END attach-evidence
}

lifecycle_validate_evidence() {
# BEGIN validate-evidence
set -euo pipefail
[[ "$GH_REPO" == szTheory/gabbaboy && "$GITHUB_REF" == refs/heads/main ]] || exit 1
[[ "$(git rev-parse HEAD)" == "$SOURCE_SHA" && "$(git rev-parse "$RELEASE_TAG^{commit}")" == "$SOURCE_SHA" ]] || exit 1
release_json=$(gh api "repos/$GH_REPO/releases?per_page=100")
[[ $(jq --arg tag "$RELEASE_TAG" '[.[] | select(.tag_name == $tag and .draft == true)] | length' <<<"$release_json") == 1 ]] || exit 1
release_id=$(jq --arg tag "$RELEASE_TAG" -r '.[] | select(.tag_name == $tag) | .id' <<<"$release_json")
if [[ -n "$RELEASE_ID" ]]; then [[ "$release_id" == "$RELEASE_ID" ]] || exit 1; fi
mkdir -p build/evidence-validation
gh release download "$RELEASE_TAG" --repo "$GH_REPO" \
  --pattern cgb-corpus-receipt.json --pattern support-ledger.json --pattern v02-performance-receipt.json \
  --pattern v02-fuzz-receipt.json --pattern source-archive-receipt.json --pattern v02-consumer-receipt.json \
  --dir build/evidence-validation
python3 -I trusted/.github/scripts/download-release-artifact.py "https://github.com/$GH_REPO/archive/refs/tags/$RELEASE_TAG.tar.gz" "$RUNNER_TEMP/source-archive.tar.gz" --max-bytes 1073741824 --total-timeout 600
bash trusted/.github/scripts/verify-release-gates.sh --check-v02-evidence \
  build/evidence-validation "$RELEASE_TAG" "$SOURCE_SHA" "$RUNNER_TEMP/source-archive.tar.gz"
# END validate-evidence
}

lifecycle_build_manifest() {
# BEGIN build-manifest
set -euo pipefail
[[ "$GH_REPO" == szTheory/gabbaboy && "$GITHUB_REF" == refs/heads/main ]] || exit 1
release_json=$(gh api "repos/$GH_REPO/releases?per_page=100")
[[ $(jq --arg tag "$RELEASE_TAG" '[.[] | select(.tag_name == $tag and .draft == true)] | length' <<<"$release_json") == 1 ]] || exit 1
release_id=$(jq --arg tag "$RELEASE_TAG" -r '.[] | select(.tag_name == $tag) | .id' <<<"$release_json")
if [[ -n "$RELEASE_ID" ]]; then [[ "$release_id" == "$RELEASE_ID" ]] || exit 1; fi
[[ $(gh api "repos/$GH_REPO/commits/$RELEASE_TAG" --jq .sha) == "$SOURCE_SHA" ]] || exit 1
assets=$(gh api "repos/$GH_REPO/releases/$release_id/assets?per_page=100")
python3 - "$assets" <<'PY'
import json, sys
rows = json.loads(sys.argv[1])
names = [row["name"] for row in rows]
expected = {
    "candidate-receipt.json", "gabbaboy-core-linux-x64.tar.gz", "gabbaboy-notices.txt",
    "source-receipt.json", "build-receipt.json", "gabbaboy-core-macos-arm64.tar.gz",
    "gabbaboy-core-macos-arm64.tar.gz.sha256", "gabbaboy-build-receipt-macos-arm64.json",
    "gabbaboy-preview-macos-arm64.tar.gz", "gabbaboy-preview-macos-arm64-build-receipt.json",
    "gabbaboy-core-windows-x64.tar.gz", "gabbaboy-core-windows-x64.tar.gz.sha256",
    "gabbaboy-build-receipt-windows-x64.json", "support-ledger.json",
    "cgb-corpus-receipt.json", "v02-performance-receipt.json", "v02-fuzz-receipt.json",
    "source-archive-receipt.json", "v02-consumer-receipt.json",
}
if len(names) != len(set(names)):
    raise SystemExit("release draft contains duplicate asset names")
actual = set(names)
# A retry may find the manifest and, after an earlier attempt got as far as the final upload, the final receipts. They are
# never required here and never accepted without the manifest; the publish job's recovery decision compares their bytes with
# the regenerated ones and refuses any difference, so accepting them cannot replace or hide anything.
manifest = {"candidate-platform-manifest.json"}
finals = {"SHA256SUMS", "release-receipt.json"}
extra = actual - expected
if expected - actual or not extra <= manifest | finals or (extra & finals and not extra & manifest):
    raise SystemExit(f"candidate asset set mismatch; missing={sorted(expected-actual)} unknown={sorted(actual-expected)}")
PY
mkdir -p build/downloaded
gh release download "$RELEASE_TAG" --repo "$GH_REPO" --pattern 'gabbaboy-core-*' --pattern 'gabbaboy-preview-*' --pattern 'gabbaboy-build-receipt-*' --pattern candidate-receipt.json --pattern gabbaboy-notices.txt --pattern source-receipt.json --pattern build-receipt.json --pattern support-ledger.json --pattern cgb-corpus-receipt.json --pattern v02-performance-receipt.json --pattern v02-fuzz-receipt.json --pattern source-archive-receipt.json --pattern v02-consumer-receipt.json --dir build/downloaded
git show "${GITHUB_SHA}:.github/scripts/verify-release-gates.sh" > build/verify-release-gates.sh
bash build/verify-release-gates.sh --check-digest-sidecar \
  build/downloaded/gabbaboy-core-macos-arm64.tar.gz.sha256 \
  build/downloaded/gabbaboy-core-macos-arm64.tar.gz
bash build/verify-release-gates.sh --check-digest-sidecar \
  build/downloaded/gabbaboy-core-windows-x64.tar.gz.sha256 \
  build/downloaded/gabbaboy-core-windows-x64.tar.gz
python3 - "$SOURCE_SHA" <<'PY'
import hashlib, json, pathlib, sys
source_sha = sys.argv[1]
root = pathlib.Path("build/downloaded")
assets = []
for path in sorted(root.iterdir()):
    if not path.is_file(): raise SystemExit(f"unexpected non-file release asset: {path.name}")
    assets.append({"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
required = {"candidate-receipt.json", "gabbaboy-core-linux-x64.tar.gz", "gabbaboy-notices.txt",
            "source-receipt.json", "build-receipt.json", "gabbaboy-core-macos-arm64.tar.gz",
            "gabbaboy-core-macos-arm64.tar.gz.sha256", "gabbaboy-build-receipt-macos-arm64.json",
            "gabbaboy-preview-macos-arm64.tar.gz", "gabbaboy-preview-macos-arm64-build-receipt.json",
            "gabbaboy-core-windows-x64.tar.gz", "gabbaboy-core-windows-x64.tar.gz.sha256",
            "gabbaboy-build-receipt-windows-x64.json", "support-ledger.json",
            "cgb-corpus-receipt.json", "v02-performance-receipt.json", "v02-fuzz-receipt.json",
            "source-archive-receipt.json", "v02-consumer-receipt.json"}
if {item["name"] for item in assets} != required:
    raise SystemExit("downloaded release asset set differs from the qualified exact set")
evidence_names = ("support-ledger.json", "cgb-corpus-receipt.json", "v02-performance-receipt.json",
                  "v02-fuzz-receipt.json", "source-archive-receipt.json", "v02-consumer-receipt.json")
for evidence_name in evidence_names:
    if not any(item["name"] == evidence_name for item in assets):
        raise SystemExit(f"generated source evidence missing from manifest: {evidence_name}")
evidence = {}
for platform in ("macos-arm64", "windows-x64"):
    receipt = json.loads((root / f"gabbaboy-build-receipt-{platform}.json").read_text())
    if receipt.get("source_sha") != source_sha or receipt.get("platform") != platform:
        raise SystemExit(f"build receipt identity mismatch for {platform}")
    evidence[platform] = receipt
linux = json.loads((root / "build-receipt.json").read_text())
if linux.get("source_sha") != source_sha or linux.get("asset_name") != "gabbaboy-core-linux-x64.tar.gz":
    raise SystemExit("Linux build receipt identity mismatch")
evidence["linux-x64"] = linux.get("build")
preview = json.loads((root / "gabbaboy-preview-macos-arm64-build-receipt.json").read_text())
if preview.get("source_revision") != source_sha or preview.get("result") != "passed":
    raise SystemExit("player build receipt identity or result mismatch")
data = {"schema_version": 1, "source_sha": source_sha, "assets": assets, "builds": evidence,
        "support_sidecar": "support-ledger.json",
        "corpus_receipt": "cgb-corpus-receipt.json",
        "performance_receipt": "v02-performance-receipt.json",
        "fuzz_receipt": "v02-fuzz-receipt.json",
        "source_archive_receipt": "source-archive-receipt.json",
        "consumer_receipt": "v02-consumer-receipt.json",
        "player_build_receipt": "gabbaboy-preview-macos-arm64-build-receipt.json",
        "downloaded_smoke": "Linux/macOS/Windows core consumers and macOS player passed",
        "hardware_qualified": False, "signed": False, "notarized": False}
pathlib.Path("build/candidate-platform-manifest.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY
current=$(gh api "repos/$GH_REPO/releases/$release_id")
[[ $(jq -r .draft <<<"$current") == true && $(jq -r .tag_name <<<"$current") == "$RELEASE_TAG" ]] || exit 1
count=$(gh api "repos/$GH_REPO/releases/$release_id/assets?per_page=100" --jq '[.[] | select(.name == "candidate-platform-manifest.json")] | length')
[[ "$count" -le 1 ]] || exit 1
if [[ "$count" == 1 ]]; then
  mkdir -p build/existing
  gh release download "$RELEASE_TAG" --repo "$GH_REPO" --pattern candidate-platform-manifest.json --dir build/existing
  cmp -s build/candidate-platform-manifest.json build/existing/candidate-platform-manifest.json || { echo "The attached platform manifest differs from the regenerated one and is never replaced." >&2; exit 1; }
else
  gh release upload "$RELEASE_TAG" build/candidate-platform-manifest.json --repo "$GH_REPO"
fi
# END build-manifest
}

lifecycle_validate_draft() {
# BEGIN validate-draft
set -euo pipefail
bash trusted/.github/scripts/verify-release-gates.sh --check-draft "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"
mkdir -p build/release-final
gh release download "$RELEASE_TAG" --repo "$GH_REPO" --dir build/release-final
api_assets=$(gh api "repos/$GH_REPO/releases/$RELEASE_ID/assets?per_page=100")
printf '%s\n' "$api_assets" > build/release-final/api-assets.json
bash trusted/.github/scripts/verify-release-gates.sh --check-merged-source "$SOURCE_SHA" "$RELEASE_TAG" "$RELEASE_ID" \
  build/release-final/source-receipt.json "$RUNNER_TEMP/verify-release-source-proof.py"
perf_run_id=$(jq -er '.run_id' build/evidence-fuzz/perf-gate/perf-gate-receipt.json)
perf_run_attempt=$(jq -er '.run_attempt' build/evidence-fuzz/perf-gate/perf-gate-receipt.json)
python3 -I trusted/tests/scripts/verify-perf-gate.py --verify-receipt \
  build/evidence-fuzz/perf-gate/perf-gate-receipt.json --source-sha "$SOURCE_SHA" \
  --run-json build/evidence-fuzz/perf-gate-run.json --run-id "$perf_run_id" --attempt "$perf_run_attempt" --repo trusted
# shellcheck disable=SC2016
python3 - "$api_assets" build/release-final "$RELEASE_TAG" "$SOURCE_SHA" "$RELEASE_ID" \
  build/evidence-fuzz/perf-gate/perf-gate-receipt.json <<'PY'
import hashlib, json, pathlib, sys
rows = json.loads(sys.argv[1])
root = pathlib.Path(sys.argv[2])
tag, source, release_id, perf_gate_path = sys.argv[3:]
perf_gate = json.loads(pathlib.Path(perf_gate_path).read_text())
names = [row["name"] for row in rows]
if len(names) != len(set(names)):
    raise SystemExit("duplicate draft asset names")
# A retry may find final metadata from an earlier attempt. The receipts are derived from the qualified
# inventory only, so an unchanged draft reproduces byte-identical receipts and recovery can compare them.
final_names = {"SHA256SUMS", "release-receipt.json"}
names = [name for name in names if name not in final_names]
rows = [row for row in rows if row["name"] not in final_names]
files = sorted(p for p in root.iterdir() if p.is_file() and p.name != "api-assets.json" and p.name not in final_names)
if {p.name for p in files} != set(names):
    raise SystemExit("downloaded files do not exactly match GitHub's draft asset inventory")
sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files)
(root / "SHA256SUMS").write_text(sums)
manifest = json.loads((root / "candidate-platform-manifest.json").read_text())
proof = json.loads((root / "candidate-receipt.json").read_text()).get("prior_pr_proof", {})
release = {
    "schema_version": 1,
    "version": tag[1:],
    "tag": tag,
    "source_sha": source,
    "release_id": release_id,
    "draft": True,
    "signed": False,
    "notarized": False,
    "hardware_qualified": False,
    "sha256sums_sha256": hashlib.sha256((root / "SHA256SUMS").read_bytes()).hexdigest(),
    "prior_pr_proof": proof,
    "downloaded_smoke": "Linux, macOS, and Windows core consumers plus macOS player passed on exact draft bytes",
    "assets": [{"name": row["name"], "id": row["id"], "sha256": hashlib.sha256((root / row["name"]).read_bytes()).hexdigest()}
               for row in rows],
    "support_sidecar": "support-ledger.json",
    "support_sidecar_sha256": hashlib.sha256((root / "support-ledger.json").read_bytes()).hexdigest(),
    "evidence_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                        for name in ("cgb-corpus-receipt.json", "v02-performance-receipt.json", "v02-fuzz-receipt.json",
                                     "source-archive-receipt.json", "v02-consumer-receipt.json")},
    "perf_gate": perf_gate,
    "candidate_manifest_sha256": hashlib.sha256((root / "candidate-platform-manifest.json").read_bytes()).hexdigest(),
    "builds": manifest.get("builds", {}),
    "limits": [f"{tag} deterministic software profiles DMG-CPU-B and CGB-CPU-E as scoped by docs/support/{tag}.md",
               "no physical DMG observation", "no Developer ID signature or notarization"],
}
(root / "release-receipt.json").write_text(json.dumps(release, indent=2, sort_keys=True) + "\n")
PY
# Recovery is decided from independently read live state, with the trusted inventory of the bytes about to
# be attached, BEFORE any final-metadata write. Changed bytes, a concurrent writer or a stale attempt stop here.
python3 -I trusted/.github/scripts/verify-published-release-assets.py --inventory "$RUNNER_TEMP/expected-inventory.json" build/release-final
bash trusted/.github/scripts/verify-release-gates.sh --check-recovery "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA" "$RUNNER_TEMP/expected-inventory.json" "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" full > "$RUNNER_TEMP/recovery-decision.txt"
decision=$(cat "$RUNNER_TEMP/recovery-decision.txt")
if [[ "$decision" == draft-reuse ]]; then
  echo "Final metadata already attached with identical bytes; nothing to upload."
elif [[ "$decision" == draft-upload-missing:* ]]; then
  IFS=, read -r -a missing <<<"${decision#draft-upload-missing:}"
  for name in "${missing[@]}"; do
    [[ "$name" == SHA256SUMS || "$name" == release-receipt.json ]] || { echo "Recovery asked to upload a non-final asset: $name" >&2; exit 1; }
    gh release upload "$RELEASE_TAG" "build/release-final/$name" --repo "$GH_REPO"
  done
else
  echo "Unexpected recovery decision: $decision" >&2
  exit 1
fi
# END validate-draft
}

lifecycle_final_gate() {
# BEGIN final-gate
bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"
assets=$(gh api "repos/$GH_REPO/releases/$RELEASE_ID/assets?per_page=100")
python3 - "$assets" "$RELEASE_TAG" "$SOURCE_SHA" "$RELEASE_ID" "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" <<'PY'
import json, pathlib, sys
rows = json.loads(sys.argv[1])
tag, source, release_id, run_id, run_attempt = sys.argv[2:]
assets = sorted(({"name": row["name"], "id": row["id"], "digest": row["digest"]} for row in rows),
                key=lambda row: row["name"])
inventory = {"schema_version": 1, "kind": "pre-publish-inventory", "tag": tag,
             "source_sha": source, "release_id": int(release_id), "run_id": int(run_id),
             "run_attempt": int(run_attempt), "assets": assets}
path = pathlib.Path("build/release-final/pre-publish-inventory.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(inventory, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
PY
# END final-gate
}

lifecycle_nightly_gate() {
# BEGIN nightly-gate
set -euo pipefail
[[ "$GH_REPO" == szTheory/gabbaboy && "$GITHUB_REF" == refs/heads/main ]] || exit 1
[[ "$RELEASE_TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ && "$SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "Malformed release tag or source SHA." >&2; exit 1; }
# The full ASan stall replay is dispatched on the rehearsal branch at the rehearsed head, whose tree is the tagged tree (the
# squash commit differs from that head, the tree does not). The head is the one the trusted selection proves for the newest
# successful rehearsal run of this tag, from git objects. verify-release-gates.py --nightly-gate then requires the newest
# nightly-asan run at that head to be completed with success and its asan-full-replay job to have succeeded; a newer run at
# another head supersedes it, and a source with another tree refuses. The judge is the trusted workflow revision. A
# refusal stops the job before the one publication transition.
gh api "repos/$GH_REPO/actions/workflows/release-rehearsal.yml/runs?branch=rehearsal/$RELEASE_TAG&status=success&per_page=100" > "$RUNNER_TEMP/nightly-rehearsal-runs.json"
gh api "repos/$GH_REPO/commits/$SOURCE_SHA/pulls" > "$RUNNER_TEMP/nightly-source-pulls.json"
source_pr=$(jq -ec --arg sha "$SOURCE_SHA" '[.[] | select(.merged_at != null and .base.ref == "main" and .merge_commit_sha == $sha)] | if length == 1 then .[0] else error("source commit does not map to exactly one merged main PR") end' "$RUNNER_TEMP/nightly-source-pulls.json")
pr_head=$(jq -r '.head.sha' <<<"$source_pr")
merged_at=$(jq -r '.merged_at' <<<"$source_pr")
selected_rehearsal=$(jq -ec '[.workflow_runs[]] | if length == 0 then error("no successful rehearsal run exists") else max_by(.id) end' "$RUNNER_TEMP/nightly-rehearsal-runs.json")
run_id=$(jq -r '.id' <<<"$selected_rehearsal")
attempt=$(jq -r '.run_attempt' <<<"$selected_rehearsal")
[[ "$run_id" =~ ^[0-9]+$ && "$attempt" =~ ^[0-9]+$ ]] || { echo "No successful rehearsal run of this tag exists." >&2; exit 1; }
gh api "repos/$GH_REPO/actions/runs/$run_id/attempts/$attempt/jobs?per_page=100" > "$RUNNER_TEMP/nightly-rehearsal-jobs.json"
python3 -I trusted/.github/scripts/verify-release-source-proof.py --bind-rehearsal-run "$RUNNER_TEMP/nightly-rehearsal-runs.json" --tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --repo "$GH_REPO" --selected-run "$RUNNER_TEMP/nightly-rehearsal-run.json" --pr-head "$pr_head" --merged-at "$merged_at" --attempt-jobs "$RUNNER_TEMP/nightly-rehearsal-jobs.json"
head=$(jq -r .head_sha "$RUNNER_TEMP/nightly-rehearsal-run.json")
gh run list --repo "$GH_REPO" --workflow nightly-asan.yml --branch "rehearsal/$RELEASE_TAG" --limit 50 --json databaseId,attempt,headSha,headBranch,event,status,conclusion,createdAt,workflowName > "$RUNNER_TEMP/nightly-runs.json"
run_id=$(jq -r --arg head "$head" '(([.[] | select(.headSha == $head)] | sort_by([.createdAt, .databaseId]) | last) // (sort_by([.createdAt, .databaseId]) | last) // {}) | .databaseId // empty' "$RUNNER_TEMP/nightly-runs.json")
[[ -n "$run_id" ]] || { echo "No nightly-asan run exists for the rehearsal branch." >&2; exit 1; }
gh run view "$run_id" --repo "$GH_REPO" --json databaseId,attempt,headSha,headBranch,event,status,conclusion,createdAt,updatedAt,workflowName,jobs > "$RUNNER_TEMP/nightly-run.json"
python3 -I trusted/tests/scripts/verify-release-gates.py --nightly-gate --runs-json "$RUNNER_TEMP/nightly-runs.json" --run-json "$RUNNER_TEMP/nightly-run.json" --head "$head" --rev "$SOURCE_SHA" --branch "rehearsal/$RELEASE_TAG" --output "$RUNNER_TEMP/nightly-gate-receipt.json"
cat "$RUNNER_TEMP/nightly-gate-receipt.json"
# END nightly-gate
}

lifecycle_publish_draft() {
# BEGIN publish-draft
set -euo pipefail
before=$(gh api "repos/$GH_REPO/releases/$RELEASE_ID")
[[ $(jq -r .draft <<<"$before") == true && $(jq -r .tag_name <<<"$before") == "$RELEASE_TAG" ]] || {
  echo "Draft changed before the one-way publish transition." >&2; exit 1;
}
[[ "$(gh api "repos/$GH_REPO/commits/$RELEASE_TAG" --jq .sha)" == "$SOURCE_SHA" ]] || exit 1
gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag
after=$(gh api "repos/$GH_REPO/releases/$RELEASE_ID")
[[ $(jq -r .draft <<<"$after") == false && $(jq -r .tag_name <<<"$after") == "$RELEASE_TAG" ]] || {
  echo "Published release readback did not preserve tag/draft transition." >&2; exit 1;
}
assets=$(gh api "repos/$GH_REPO/releases/$RELEASE_ID/assets?per_page=100")
python3 -I trusted/.github/scripts/verify-published-release-assets.py "$assets" build/release-final/api-assets.json
echo "Published the exact qualified release $RELEASE_TAG ($SOURCE_SHA) with unsigned status recorded."
# END publish-draft
}

case "${1:-}" in
  attach-evidence) lifecycle_attach_evidence ;;
  validate-evidence) lifecycle_validate_evidence ;;
  build-manifest) lifecycle_build_manifest ;;
  validate-draft) lifecycle_validate_draft ;;
  final-gate) lifecycle_final_gate ;;
  nightly-gate) lifecycle_nightly_gate ;;
  publish-draft) lifecycle_publish_draft ;;
  *) printf 'usage: release-evidence-lifecycle.sh attach-evidence|validate-evidence|build-manifest|validate-draft|final-gate|nightly-gate|publish-draft\n' >&2; exit 2 ;;
esac
