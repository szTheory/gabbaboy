# Phase 15: CGB Acceptance, Support Ledger and v0.2.0 Release — Pattern Map

**Mapped:** 2026-10-16  
**Files/seams classified:** 21  
**Tracked analogs found:** 18; the source-archive contract and a campaign receipt have no exact analog.

This map follows Phase 15 CONTEXT/RESEARCH/VALIDATION. The likely game-evidence route is the explicit absence alternative: the pinned Rebound build failed with the inspected RGBDS toolchain, rights remain unresolved, and no ROM was admitted. Do not plan a runner rewrite or add game bytes unless focused gates produce new admissible evidence.

## File Classification

| New/Modified File or seam | Role | Data Flow | Closest tracked analog | Match |
|---|---|---|---|---|
| `docs/support/v0.2.0.md` (new) | documentation/config | batch | `docs/support/v0.1.0.md` | role-match |
| `docs/support/unreleased.md` (fold into v0.2.0) | documentation | transform | `docs/support/v0.1.0.md` | role-match |
| `tests/scripts/verify-support-ledger.py` (modify) | utility/validator | batch | same file, v1 path | exact |
| CGB absence and public-claim contract (new checker or validator extension; name is planner discretion) | test/utility | batch | `tests/scripts/verify-cgb-corpus-claims.py` | role-match |
| `tests/consumers/c/main.c`, `tests/consumers/cpp/main.cpp` (reuse; edit only for a demonstrated API gap) | test/consumer | request-response | same files | exact |
| `tests/CMakeLists.txt`, `tests/expected-tests.txt` (extend only for new recurring contracts) | config/test inventory | batch | same files | exact |
| `tests/scripts/measure-release-baseline.sh` (modify A/B provenance) | utility/benchmark | batch | same file, `--ab` path | exact |
| `tests/scripts/run-bounded-fuzz.sh` (modify campaign route/receipt) | utility/fuzz runner | batch | same file, `--explore` path | exact |
| `.github/workflows/ci.yml` (route actual Clang campaign to eligible Linux sanitizer job) | config/workflow | event-driven | same file, `linux-sanitizers` job | exact |
| `.github/workflows/release.yml` (extend sidecars and retain exact-tag/downloaded consumer gates) | config/workflow | event-driven, file I/O | same file | exact |
| `.github/scripts/verify-release-gates.sh` (extend required sidecars/inventory and final readback) | utility/validator | batch | same file | exact |
| `.github/scripts/verify-release-source-proof.py` (extend only if receipt schema changes) | utility/validator | request-response | same file | exact |
| `tests/scripts/verify-release-candidate.sh` (extend package/receipt checks as needed) | test/utility | file I/O | same file | exact |
| Source archive content/notice contract (new; exact path not fixed) | test/utility | file I/O | `tests/scripts/verify-release-candidate.sh` | partial |
| `README.md`, `docs/game-acceptance.md`, `docs/cgb-profile.md`, `docs/audio-and-playback.md`, `docs/preview.md` | documentation | transform | corresponding current docs; `docs/game-acceptance.md` is the closest claim-boundary example | role-match |
| `docs/native-integration.md` | documentation/example | request-response, file I/O | same file | exact |
| `docs/cartridge-and-saves.md` | documentation | transform | same file | exact |
| `docs/release.md` | documentation | transform | same file | exact |
| `THIRD_PARTY_NOTICES.md` | documentation/rights record | transform | same file | exact |
| `CHANGELOG.md` / release-please version PR | documentation/release metadata | transform | same file and `.github/workflows/release.yml` | role-match |
| Conditional only: `src/runner/acceptance.c`, `tests/acceptance/CMakeLists.txt` | test harness | request-response | same files | exact, only if game gates close |

All named analogs above were checked with `git ls-files -- <path>` and are tracked source. No ignored `.gsd/capabilities` mirror path is used.

## Pattern Assignments

### Support ledger and tag-dispatched sidecar

**Target:** new `docs/support/v0.2.0.md`; modify `tests/scripts/verify-support-ledger.py`; fold the current unreleased support claims into the versioned ledger.

**Analog:** `docs/support/v0.1.0.md` and `tests/scripts/verify-support-ledger.py`.

The v0.1 ledger separates prose from one delimited JSON block (ledger lines 37–75), and explicitly limits the claims to its model, corpus, exclusions, and hardware evidence. Preserve that readable-prose-plus-structured-data shape. The validator parses UTF-8 strictly and rejects repeated JSON keys (lines 66–95). Its current version-1 checks pin a model, fixed ordered cases, denominator, outcomes, exclusions, limitations, and manifest hashes (lines 98–145).

Current release selection deliberately picks the newest ledger not above a tag (validator lines 40–53), which supports v0.1 patch releases. Add a separate v0.2.0 selection rule that requires exactly `docs/support/v0.2.0.md`; preserve and regression-check v1 behavior. Keep inventory membership and denominators derived from tagged manifests and a fresh receipt rather than caller totals. Include distinct attempted/executed/pass/fail/matched-xfail/excluded/not-run counts by suite and model/mode, with the Phase 14 107/25/82 totals remaining historical until refreshed.

The current tagged sidecar pattern is the closest copy point (validator lines 182–220):

```python
actual_sha = git("rev-parse", f"{tag}^{{commit}}", cwd=repo_root).decode().strip()
if actual_sha != source_sha:
    fail("supplied source SHA does not resolve from the requested tag")
names = git("ls-tree", "--name-only", f"{tag}:{LEDGER_DIR}", cwd=repo_root).decode().split()
ledger = select_ledger(names, tag)
ledger_raw = git("show", f"{tag}:{ledger}", cwd=repo_root)
data = parse_ledger(ledger_raw, ledger_version(ledger))
```

Bind the v0.2 sidecar to the tag's exact ledger path/blob/hash, full source SHA, current receipt and manifest identities. Do not let v0.2.0 inherit v0.1 claims through the patch fallback.

### Explicit no-game-evidence claim

**Target:** the v0.2 ledger, release notes and relevant public claims; add the semantic check to the existing validator or a small checker whose filename the planner assigns.

**Analog:** `tests/scripts/verify-cgb-corpus-claims.py` (tracked; lines 19–28, 52–80, 119–135). It enumerates public claim surfaces, requires contract text, uses bounded marker sections, and rejects unqualified hardware/general-game claims. The v0.1 ledger validator also already guards `broad_game_claim` and current unsupported claims (lines 105–106, 132–136).

For the selected absence route, require the exact statement **“No CGB game-level evidence exists”** in the v0.2 ledger and release claims. Negative controls should remove it and inject a contrary positive claim; both must fail through the registered contract command. Keep game evidence distinct from corpus pass counts. Do not add a Rebound ROM, infer rights from its repository license, or force the Libbet/DMG progress path into CGB acceptance.

If the bounded candidate gates unexpectedly close, the nearest runner seam is `src/runner/acceptance.c` lines 187–191, which currently fails CGB frame-progress capture explicitly with `frame-unsupported-profile`; RGB555 capture exists at lines 750–760. The current negative CTest is `tests/acceptance/CMakeLists.txt` lines 417–419. Prototype only that bounded runner seam and keep the existing refusal as a failing control; this is conditional, not the default Phase 15 file plan.

### Installed C/C++ consumer proof

**Target:** reuse existing consumers; extend only a measured gap. Run them from relocated prefixes and again against downloaded candidate package bytes.

**Analogs:** `tests/consumers/c/main.c` lines 85–119, 136–142; `tests/consumers/cpp/main.cpp` lines 648–689; `tests/CMakeLists.txt` lines 1646–1674.

The C consumer already probes the CGB-only-on-DMG result, selects CGB, verifies `gbb_get_info`, rejects unsupported PGB execution and exercises RGB555 frame copy/stride refusal. The C++ main also runs CGB speed/DMA twins and RTC/API smoke. Reuse these behavioral checks; symbol presence or an in-tree build does not close SHIP-10. The CMake registrations use separate C/C++ consumer sources and build directories against the installed prefix. Release workflow lines 340–365 then downloads the draft asset, extracts it, forbids checkout/build discovery paths, and compiles/runs both consumers from the downloaded bytes. Preserve this two-stage proof.

### Controlled v0.1.0 DMG comparison

**Target:** strengthen `tests/scripts/measure-release-baseline.sh`'s existing interleaved `--ab` path and its receipt checks.

**Analog:** same script, lines 48–74 and 98–149. It pins workload `original-wram-tracer-1m-half-dots-v1`, checks each binary's workload and output digest, alternates A/B order, and records raw samples, warmups, uncertainty, and hardware class. The current receipt can default revision labels to `unknown` and build metadata can return `unknown` when a cache is absent; Phase 15 must validate source/build/binary identity from artifacts and reject unknown or unsupported labels.

Use the exact v0.1.0 commit named in CONTEXT, clean matching Release configurations, three warmups and thirty paired samples by default. Preserve the output digest on both binaries. Record uncertainty and the +5% review disposition; investigate material regressions without silently optimizing to noisy percentages. Do not substitute the historical Phase 10 slowdown or relabel candidate output as baseline evidence.

### Actual bounded Clang/libFuzzer campaign

**Target:** `tests/scripts/run-bounded-fuzz.sh`, `.github/workflows/ci.yml`, and release-side evidence validators.

**Analog:** the existing `--explore` path in `tests/scripts/run-bounded-fuzz.sh` lines 80–96. It requires an executable fuzz binary and supplies `-max_len=65536`, `-max_total_time=60`, `-timeout=2`, `-rss_limit_mb=512`, `-jobs=1`, and `-workers=1`. Keep these resource limits, the dictionary, seed identities, and deterministic hostile regressions separate. Its `--self-test`/`--fast` path can report `unsupported` while succeeding; that output is not campaign evidence. Require a matching Clang fuzzer/address/undefined-sanitizer runtime and a nonzero actual exploration receipt with source, build, binary, seed/dictionary, bounds, result and minimized artifacts. Local unavailable runtime routes to an eligible hosted Clang job; absence of a real campaign keeps SHIP-11 open.

The existing Linux sanitizer workflow currently runs the self-test (`.github/workflows/ci.yml`, `linux-sanitizers` job, lines 187–215); extend that eligible lane without adding a new CI matrix or dependency.

### Exact-tag delivery, receipts, downloaded bytes, and retry

**Targets:** `.github/workflows/release.yml`, `.github/scripts/verify-release-gates.sh`, `.github/scripts/verify-release-source-proof.py`, and `tests/scripts/verify-release-candidate.sh`.

**Analog excerpts:**

`release.yml` lines 99–127 verifies retry uses the same existing release ID, checks tag target against the source SHA, requires one unpublished draft, and checks out the exact tagged source:

```bash
api_commit=$(gh api "repos/$GH_REPO/commits/$RELEASE_TAG" --jq '.sha')
[[ "$api_commit" == "$SOURCE_SHA" ]] || exit 1
[[ "$draft" == true && -n "$body" && "$body" != null ]] || exit 1
if [[ "$RETRY" == true && "$release_id" != "$INPUT_RELEASE_ID" ]]; then
  echo "Retry release ID differs from the supplied existing draft." >&2
  exit 1
fi
```

`verify-release-source-proof.py` lines 30–59 binds the source receipt to a merged main PR and the live exact-head required checks; copy its fail-closed comparison style for the new sidecar identities. `verify-release-gates.sh` lines 218–267 validates exact asset inventory, downloaded digests, support-sidecar tag/source/blob, and candidate manifest byte hashes. Extend those existing receipt and inventory paths for the v0.2 ledger, paired DMG receipt and actual campaign receipt. Keep final asset readback separate from the earlier validation download.

`release.yml` lines 340–365 provides the downloaded Linux C/C++ consumer smoke; lines 761–780 do the analogous Windows downloaded-archive consumer path. The existing retry path (`release.yml` lines 206–240 and 267–337) downloads and revalidates a previously qualified draft and refuses a differing attachment. On an error, inspect actual tag/release state first; reuse byte-identical assets only, never overwrite published bytes or change the frozen tag/source to make a check green.

`tests/scripts/verify-release-candidate.sh` lines 14–47 bounds archive extraction, rejecting traversal, links, duplicates, and oversized packages; lines 182–198 runs relocated C/C++ consumers, and lines 297–340 mutates receipts and archive paths as negative controls. Reuse this negative-control style for package/source proof.

### Documentation, notices, and source archives

Keep adopter claims synchronized across `README.md`, `docs/game-acceptance.md`, `docs/cgb-profile.md`, `docs/audio-and-playback.md`, `docs/preview.md`, `docs/native-integration.md`, `docs/cartridge-and-saves.md`, `docs/release.md`, `THIRD_PARTY_NOTICES.md`, and the tagged `CHANGELOG.md`. `docs/native-integration.md` lines 10–43 shows the project convention: move the install prefix, configure from a separate directory, link only `GabbaBoy::core`, and explain exactly what the consumer proves. `docs/game-acceptance.md` lines 12–18 frames acceptance around a ROM-bound guest predicate and clearly distinguishes frame/PCM digests from proof of progress. `THIRD_PARTY_NOTICES.md` lines 11–20 records fixture rights, provenance, digests and repository-only distribution separately; absence route adds no uncertain Rebound material.

No exact source-archive checker exists. Add a bounded contract for the generated v0.2.0 source archive and notices, with a missing/unlicensed-file negative control. Keep it distinct from the existing product-package allow-list: source archives retain licensed fixture source/notices, binary packages remain fixture-free. `verify-release-candidate.sh` is only a partial file-I/O analog because it checks installed product archives, not GitHub-generated source archives.

## Shared Patterns

- **Bind every result to actual bytes and revision.** Read identity from the tagged tree, binary/build metadata, downloaded asset, or live PR/check records. Reject stale, duplicate, partial, unknown, and mismatched values.
- **Use exact inventories and meaningful negative controls.** The existing validators mutate schema, membership, digest, claims, and release receipts in self-tests. Register new recurring contracts in existing CTest/required-test inventory; keep one-off planning checks local.
- **Keep evidence classes separate.** A CGB corpus result is not a game result; RGB555/PCM digests are regression observations; unsupported fuzz is not a campaign; installed source builds are not downloaded-package proof.
- **Preserve delivery boundaries.** Keep v0.1 ledger behavior for patch tags. v0.2.0 requires its exact ledger. Keep source archives, binary packages, notices, and release sidecars as separately checked artifacts.
- **Avoid widening scope.** No new runtime or benchmark dependency, GSD runtime CI, duplicate matrix, broad emulator rewrite, uncertain ROM, or physical/perceptual claim is supported by these seams.

## No Analog Found

| File/seam | Why there is no exact analog | Planner direction |
|---|---|---|
| GitHub-generated source-archive/notice verifier | Existing package checks inspect product archives; source archives have a different content contract. | Add one bounded archive-content checker and a missing/unlicensed-file control. |
| Actual Clang/libFuzzer campaign receipt tied to final release source | Current bounded runner has strict limits but its `--fast`/self-test route can succeed as unsupported and does not provide the required campaign identity receipt. | Extend the existing exploration route and receipt validators; do not count unsupported output as a run. |

## Metadata

**Tracked search scope:** phase 15 context/research/validation; current support ledger and validator; acceptance runner/CTest; C/C++ consumers and CMake registrations; benchmark/fuzz scripts; CI/release workflows and receipt validators; adopter and rights documentation.  
**Selection limit:** patterns were sampled at these direct seams; no broad repository survey was performed.  
**Conditional CGB acceptance:** only if rights, reproducible build, objective, and runner feasibility gates close; otherwise document the exact absence statement and leave `src/runner/acceptance.c` unchanged.
