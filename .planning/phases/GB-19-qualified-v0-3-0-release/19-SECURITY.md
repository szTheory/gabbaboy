---
phase: "19"
slug: qualified-v0-3-0-release
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-30"
---

# Phase 19 — Security

The fresh independent D-134 ASVS L1 recheck at `d2c0dc95ecc7c5eb34a85bdc541f5ac3918190dc` verifies all41 authored threats closed, including the existing AR-19-01 acceptance. It reclosed T-19-22 after independently reproducing the baseline malformed-schema acceptance and confirming exact-type refusals with recomputed inventory hashes and valid actual evidence. The original audit, subsequent reopening and authorized correction remain recorded below. No blocking or non-blocking threat remains open; final local/hosted/goal qualification and PR B merge remain separate gates.

The second focused audit at `0fec185016ae4d3578b641ffc694aafdd1d8795c` verified that CI integration fixes preserve the registered mitigations: production tag and publication guards are unchanged; the tag-guard fixture uses a relative log path with an explicit temporary working directory; and the two lifecycle control suites run serially with unchanged 60-second limits, minimum counts and semantic assertions. The independent auditor executed all three tag-guard scenarios successfully. Subsequent local targeted CTests passed 3/3; actual final-head Windows CI and renewed preflight remain pending. This adds no risk acceptance and changes no threat status.

**E0 execution update:** the coherent preflight at frozen PR head `e0ca6463c3b6379fe65f28bb1fa0673be79ee071` fulfilled T-19-25, including the bump-only negative, all six hosted producers, exact judge comparison and transient-branch deletion. This is 27/35 threats closed, eight operational items open, four at the blocking threshold. Both E0 Windows CI instances failed the test harness by selecting a WSL launcher; T-19-26 remains open and PR #133 cannot merge. Two fix rounds are used, so a further interpreter-selection fix requires owner rescope. The production tag/publication guards remain unchanged. Any later source head requires its own qualification; E0 evidence is not relabeled.

**Owner-approved rescope audit:** D-121 permits the one bounded additional fix/review; D-122 resolves D-09 acknowledgment. The independent ASVS L1 delta audit at `8f4deeddd07ddf06f9927a1c6c571b717732b06e` found no implementation blocker: bundled Windows Bash selection rejects missing, unsupported, system-root and escaping candidates; all three real guard assertions remain; production guards and limits are unchanged. Resolver controls passed five negative/four positive cases, and an isolated selected-executable invocation exercised the guard scenarios. The executor's revision-bound targeted suite passed 5/5 with the 453 POSIX/426 Windows floors and unchanged 180-second policy timeout. Actual hosted Windows CI and renewed final-source preflight remain mandatory; E0 qualification is historical, so T-19-25 is open for the new source. Current register: 26/35 closed, nine operational items open, four blocking. No new risk acceptance.


## D-121 validation continuation

Actual b33 Windows CI located Git at `Git/ucrt64/bin/git.EXE`; the first resolver candidate mapped that equivalent layout one directory too deep. Commit `dedeb22a5528b0ec6bb3cb4845a535303f66ccd4` adds the observed architecture layout and a persistent positive fixture selecting top-level `Git/bin/bash.exe`. The independent focused audit preserved T-19-14, T-19-22 and AR-19-01: all five refusal controls, three real guard scenarios, timeout limits, negative-count floors and production guards are unchanged. Resolver controls are five negative/five positive; overall policy controls are 453 negative/nine positive. A valid uppercase `git.EXE` fixture fails on immutable `8f4deed` and selects the correct Bash on the new source. The revision-bound local CTest passed 1/1 in 56.18 seconds. Actual Windows CI and the final-source preflight remain mandatory. Superseded b33 runs were canceled, their partial/canceled results are not passes, the transient branch was deleted, the tag is absent and main remains unchanged.

## Trust Boundaries

| Boundary | Data crossing |
|----------|---------------|
| Untrusted PR subject → trusted workflow judge | Commit/tree IDs, workflow declarations and receipts |
| Serialized state → portable core | Bounded state bytes validated before application |
| Build/archive → external consumer | Installed package bytes, host smoke and platform identity |
| Rehearsal/CI → release qualification | Run/attempt, exact source, performance and corpus receipts |
| Draft release → public release | Frozen API asset IDs, names and digests |
| GitHub API → committed readback | Sanitized source-bound metadata and raw pre-publish inventory |
| Operator → Git refs | Guarded pushes, merges, immutable tag and draft lifecycle |

## Threat Register

Evidence paths below are relative to `tests/scripts/` unless otherwise qualified. Unchanged rows retain the initial audit's evidence at29f6ae2b; T-19-22 uses the b0beb4fd re-audit.

| Threat ID | Category | Component | Severity | Disposition | Mitigation / remaining evidence | Status |
|-----------|----------|-----------|----------|-------------|---------------------------------|--------|
| T-19-01 | Spoofing | Ledger citations | high | mitigate | `.github/scripts/verify-workflow-policy.py:2473,2491,2639,2657`: anchor ancestry/tree, retained release object, cited job and API tree | closed |
| T-19-02 | Repudiation | Git evidence | medium | mitigate | Policy checker fails closed at2454; rehearsal full-history trusted judge and explicit Git root | closed |
| T-19-03 | Tampering | Trusted policy | high | mitigate | CI extracts checker from BUDGET_BASE; policy pins base-copy commands | closed |
| T-19-04 | Information disclosure | Repro workflow credentials | low | mitigate | libbet-repro disables persisted credentials and belongs to READONLY_WORKFLOWS | closed |
| T-19-05 | Repudiation | Player linkage | low | mitigate | Corrected core links; verify-phase3-player.sh Debug linkage check; auditor observed66 targets, zero violations | closed |
| T-19-06 | Tampering | State application | high | mitigate | gabbaboy.c validates before shared infallible conversion; range-removal mutant control | closed |
| T-19-07 | Repudiation | Fuzz source binding | low | mitigate | verify-v02-fuzz.py includes public header and header-edit control | closed |
| T-19-08 | Repudiation | Managed claims | high | mitigate | verify-support-ledger.py exact keys, enums, derived counts and evidence registration | closed |
| T-19-09 | Tampering | Generated ledger | medium | mitigate | Exact generator bytes and hand-edit refusing control | closed |
| T-19-10 | Repudiation | Interop claims | medium | mitigate | verify-no-interop-claims.py scans optional v0.3 ledger with widened pattern and controls | closed |
| T-19-11 | Repudiation | Performance claims | medium | mitigate | verify-v02-adoption.py requires full measured head and historical-head/tag-bound wording | closed |
| T-19-12 | Tampering | Version window inputs | high | mitigate | verify-version-window.py includes and digests managed claims | closed |
| T-19-13 | Spoofing | Rehearsal source proof | high | mitigate | Exact PR head/tree and run-attempt jobs; R2-red control | closed |
| T-19-14 | Tampering | Postdated rehearsal | high | mitigate | Source proof compares merge/completion timestamps; judge refuses existing tag | closed |
| T-19-15 | Elevation of privilege | Version PR gate | high | mitigate | PR-only trigger, read permissions, trusted base checkout, data-only subject and environment body; policy pins | closed |
| T-19-16 | Tampering | Active window version | medium | mitigate | Window checks tree version; release requires active record at SOURCE_SHA | closed |
| T-19-17 | Denial of service | API replay coverage | medium | mitigate | verify-release-lifecycle.py inventories endpoint forms and rejects uncovered routes | closed |
| T-19-18 | Information disclosure | API captures | medium | mitigate | Lifecycle sanitizer; bounded bytes, digest and private-text/email refusal | closed |
| T-19-19 | Spoofing | Perf receipt handoff | high | mitigate | Release selects named artifact at run/attempt; verifier binds source/event/workflow/run/attempt/limits | closed |
| T-19-20 | Tampering | Performance policy | high | mitigate | Shared exact predicate and immutable limits checks; frozen limits unchanged | closed |
| T-19-21 | Repudiation | Consumer host smoke | medium | mitigate | Policy orders host smoke and platform-bound receipts for every writer; consumer verifier checks results | closed |
| T-19-22 | Tampering | Publication inventory/readback | high | mitigate | D134 independent recheck confirms exact-integer schema guards at published-assets69-73 and dispositions592-600; actual inventory/readback positives pass and true/1.0 mutations with recomputed hashes refuse. Complete frozen asset identity/digest maps and pre-publication guard remain intact. | closed |
| T-19-23 | Information disclosure | Readback | medium | mitigate | verify-v03-dispositions.py privacy scan and immutable lifecycle pattern parity | closed |
| T-19-24 | Repudiation | Release profiles | low | mitigate | Lifecycle derives profiles/ledger from tag; profile control | closed |
| T-19-25 | Denial of service | Final synthetic preflight | medium | mitigate | Final source preflight records six successful producers, matching trusted-judge outcome, fixed-point ledger and transient-ref deletion; later source corrections separately qualified. Actual preflight evidence retained under build/preflight/runs/8f5da5203e7cb525d4ed4f4ddb1182369ab750a7-final-20261030-8f5da520/. | closed |
| T-19-26 | Tampering | PR A merge | high | mitigate | Actual PR A branch-protection/check-run/PR snapshots show all required instances successful at reviewed head; immutable squash tree equals that head. Guarded PR133 squash cb3055c9 retained. | closed |
| T-19-27 | Tampering | PR titles/file set | medium | mitigate | Immutable PR133 squash subject and regenerated PR131 snapshots preserve required titles and bounded version bump file set; task1 input/prepush records and task3-go-no-go snapshots retained. | closed |
| T-19-28 | Repudiation | Documentation | low | mitigate | Doc links and first CHANGELOG heading contract checks with refusing controls | closed |
| T-19-29 | Tampering | Version PR merge | high | mitigate | Actual W checks and active gate bind R2 before merge; immutable tree(S)==tree(W), S parent is recorded window base, guarded PR131 merge retained in task3-go-no-go evidence. | closed |
| T-19-30 | Tampering | Main during window | high | mitigate | Actual Task1 prepush and Task3 main snapshots pin historical WINDOW_BASE9c405b01; immutable S has that parent and exactly one window-range commit. Current HEAD is never substituted for the historical boundary. | closed |
| T-19-31 | Tampering | Tag/draft lifecycle | high | mitigate | Actual Git tag stays at S and release429606490 keeps its identity. Body-only association drift stopped dispatch; owner D132/D133 authorized the single separately marked same-ID restoration before the sole successful retry. | closed |
| T-19-32 | Spoofing | Post-merge rehearsal | medium | mitigate | Existing-tag guard and merge-time source proof remain enforced. Actual selected R2 attempt completed before S merge; retained run list/no-postmerge-rehearsal assertion and successful publication preserve the premerge binding. | closed |
| T-19-33 | Repudiation | Release body | medium | mitigate | task3-go-no-go/body-final.md equals captured live PR body and its canonical digest matches W. Historical window check and adoption check pass; changed-body control refuses. | closed |
| T-19-34 | Information disclosure | Committed readback | medium | mitigate | tests/CMakeLists.txt registers actual v03_readback with immutable source, planning label and exit/regex checks; verify-v03-dispositions.py privacy parity and private-path refusal hold. Actual 22-asset readback passes. | closed |
| T-19-35 | Tampering | draft notes | high | mitigate | Lifecycle checker491-503/1093-1103 pins exact single-link transformation and body hashes; actual failing notes and association captures validate. D132/D133 tag-only request and independent unchanged repaired-body readback are retained. | closed |
| T-19-36 | Spoofing | retry workflow/product binding | high | mitigate | Disposition checker203-337 binds actual main/G dispatch/run/jobs separately from product/tag/receipts S; normal run equality remains strict at568. Actual raw projections match and false G/S substitution refuses. | closed |
| T-19-37 | Repudiation | failed/retried run history | medium | mitigate | Original failed S push41148606886 remains distinct from successful G dispatch41205021983 attempt1. Actual request/run/job/log captures and both final summaries preserve the sequence. | closed |
| T-19-38 | Information disclosure | new capture/readback | medium | mitigate | Lifecycle checker521-548/680-695 enforces additive fixture privacy, bounds and pinned provenance; both actual fixtures validate and private path/token/email negatives refuse. Public-body exception is narrowly scoped. | closed |
| T-19-39 | Denial of service | repeated/concurrent recovery | high | mitigate | Existing release serialization remains; separate exclusive permanent markers preserve original body PATCH, single association restoration and sole dispatch. Actual captures show no concurrent release work and one successful retry; no limits changed. | closed |
| T-19-40 | Elevation of privilege | alternate ref or weakened judge | high | mitigate | Main-only workflow guards and disposition checker203-253 restrict exact seven-path G/S correction and protected blobs. Independent immutable comparison proves reviewed/squash tree equality, unchanged product/workflow/policy and successful actual-G remaining-stage checks before retry. | closed |
| T-19-SC | Tampering | Package installations | high | accept | Existing plan-time acceptance recorded as AR-19-01 | closed |


## Implementation Findings and Round 1 Closure

CR-01 / T-19-22: the publisher excludes `SHA256SUMS` and `release-receipt.json` from their payload lists, uploads both, then snapshots every API asset. Readback incorrectly requires both payload lists to cover the complete inventory. Independent reproduction: payload-only fixture passes; replacing its inventory with the production full shape and rehashing raw bytes rejects `readback-digest-mismatch`. Correct coverage must distinguish payloads and separately bind final metadata IDs/digests, preserving complete inventory comparison.

CR-02 / T-19-22: the final gate precedes nightly. `publish-draft` performs its asset comparison after `gh release edit --draft=false`. Independent replay with unmodified production scripts: final-gate=0; nightly-gate=0; remove qualified `gabbaboy-core-linux-x64.tar.gz`; publish-draft=1 with `REJECT published-assets`, but draft=false and a publish decision already recorded. Require fresh complete frozen-inventory comparison immediately before publication, with a control proving a changed asset leaves draft=true and zero publication decisions. Retain post-publication comparison. This finding concerns an already present change, distinct from the residual race between separate API requests.

Both historical findings above are fixed at b0beb4fd. The independent auditor ran all48 readback controls against the full production-shaped inventory, the shared asset verifier self-test, and the focused lifecycle control against immutable b0beb4fd inputs with the real validation/final/nightly prelude. Unchanged assets publish once; a post-gate removal leaves draft=true and zero publication decisions; the omitted-guard mutant publishes once and then refuses. The complete post-tag replay reports3 positives,84 controls and23 endpoints. The four CTest-wired controls passed4/4 at the same source SHA. Evidence: `build/preflight/runs/b0beb4fd8d1c2290d89b707860bf23c899e12fac/review/round1-evidence.md` and adjacent logs (ignored local evidence).

The code review additionally found WR-01: changed-path closure accepted internal `..` components. Canonical repository-path validation and a traversal negative control now refuse it. Integration also exposed IR-01: the judge helper's CLI contradicted its documentation; the documented `--key STDERR --exit N` grammar now has positive and refusing CLI controls. Neither is a new authored threat ID.

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-19-01 | T-19-SC | The existing acceptance in all seven authored plans states no package installation: stdlib Python, CMake and gh; existing pinned actions only. The auditor verified that premise at the reviewed commit. This entry records that existing disposition and grants no new risk acceptance. | Plan-time disposition in19-01..19-07; independently rechecked by gsd-security-auditor | 2026-10-30 |

## Audit Trail and Limits

| Date | Source | Closed | Open | Blocking open | Audit |
|------|--------|--------|------|---------------|-------|
| 2026-10-30 |29f6ae2b818fdc4dac8b73b3107b5a9722e10578|24|11|6|Independent initial audit; T-19-SC log absent |
| 2026-10-30 |Same source; acceptance logged here|25|10|5|Orchestrator records existing AR-19-01; two independently confirmed T-19-22 gaps remain |
| 2026-10-30 |b0beb4fd8d1c2290d89b707860bf23c899e12fac|26|9|4|Independent gsd-security-auditor focused re-audit closes both T-19-22 implementation gaps; existing AR-19-01 verified |
| 2026-10-30 |0fec185016ae4d3578b641ffc694aafdd1d8795c|26|9|4|Independent focused round 2 audit preserves T-19-14/T-19-22 and AR-19-01; tag scenarios executed; executor targeted controls subsequently pass 3/3; Windows CI pending |
| 2026-10-30 |e0ca6463c3b6379fe65f28bb1fa0673be79ee071|27|8|4|Orchestrator records completed E0 preflight and actual Windows WSL-launcher failure; T-19-26 remains blocking; owner rescope pending |
| 2026-10-30 |8f4deeddd07ddf06f9927a1c6c571b717732b06e|26|9|4|Independent approved-rescope audit preserves mitigations; targeted suite 5/5; actual Windows and renewed preflight pending; D-121/D-122 approved |
| 2026-10-30 |dedeb22a5528b0ec6bb3cb4845a535303f66ccd4|26|9|4|Focused D-121 continuation covers observed ucrt64 layout; old-resolver refusal/new-selection proof and actual guard cases pass locally; Windows/preflight pending |

No missing subject-ancestry dependency was established: ancestry/object checks use full-history trusted-judge; subject derivation reads CMake/manifest; fuzz exact-tree/blob validation follows fetching the subject commit. The local differential uses full-history worktrees and does not exercise a shallow subject checkout; this is a coverage limitation, not a verified defect. The five completed summaries have no explicit Threat Flags sections; that is not proof of an exhaustive attack-surface inventory.

Audit-time linkage, managed claims, interop scan, CHANGELOG heading and doc link checks passed. Reproductions were isolated. The subsequent E0 rehearsal used a transient remote branch, deleted after its terminal run. T-19-25 was closed for E0 only and is reopened for the resolver source; actual Windows CI and the guarded merge remain unperformed. Publication operations and REL-01 remain pending. No security or phase-completion sign-off is claimed.


## Final operational audit evidence

The independent `gsd-security-auditor` verified the current source and all eight authored registers, actual release429606490 publication at2026-10-31T13:47:13Z, successful sole retry41205021983 attempt1, workflow G/product S distinction, original pre-publish artifact and downloaded raw receipt/inventory bytes. Every capture-manifest hash and actual job projection matched. Immutable Git comparisons verified S/W, corrective reviewed/squash trees, exact correction paths and unchanged critical blobs. Historical window/body checks passed; in-memory negatives refused false workflow identity, inventory changes and private text. Existing no-interop and documentation checks with controls passed.

Operational evidence resides in ignored build/phase19-window task1-live/task2-live/task3-go-no-go, posttag-recovery/tag-drift-replan, retry-dispatch-D133 and release-S/published-41205021983 captures; committed readback is19-release-readback.json. D131 diagnosis approval, D132 separately marked conditional restoration, D133 two-call UTF-8 fix/full actual-entrypoint replay/review and the original one retry remain separate authorizations. The actual no-write preflight TypeError is preserved as a failure, not a live mutation or successful preflight. No second retry or extra corrective main merge occurred.

The auditor wrote no project files, project Git metadata or remote state. An existing interop validator internally created and removed its isolated temporary fixture repository; the auditor reported that procedural detail. No new risk acceptance was granted. At that audit snapshot all41 threats were closed; the subsequent schema finding below reopens T-19-22. Neither snapshot stands in for final PR B qualification or its guarded merge.

## Security Audit 2026-10-31

| Metric | Count |
|---|---|
| Threats found | 41 |
| Closed | 41 |
| Open | 0 |


## Post-review T-19-22 reopening

After the independent L1 audit, code review and a current-source reproduction established that the final publication-inventory validator accepts JSON true or1.0 as schema version1. This contradicts its strict-schema contract, although the actual published inventory has the correct integer schema and all retained release bytes remain reconciled. T-19-22 is reopened for this bounded schema-correctness gap; no existing acceptance covers it. The original41/41 audit remains historical evidence of what was checked, not approval to ignore this finding. Final phase closure and PR B merge are held. An isolated repair and negative controls will support the required owner scope decision; no further release mutation is proposed.

## Security Audit 2026-10-31

| Metric | Count |
|---|---|
| Threats found | 41 |
| Closed | 40 |
| Open | 1 |


## D-134 independent schema recheck

At d2c0dc95, all seven affected implementation/test paths match the approved900eabfd prototype. The auditor independently verified valid integer and malformed boolean/float/string/null/array cases across the five validators, including direct schema-2 ledger handling and controlled CoverageError for non-object policy registries. The readback schema negatives recomputed raw-inventory hashes, so a hash mismatch could not masquerade as the desired type refusal. Actual v0.3.0 readback passed with22 assets.

T-19-22 is reclosed. T-19-08/09/17/18/23/34/35/36/38/40 remain closed: exact schema guards are at support-ledger337/585, lifecycle538/1446/3559/3629, dispositions592-600, published-assets69-73 and policy-coverage500-505. Existing privacy/bounds/provenance/source/G-S/attacher, stable-ID ordering/coverage and immutable policy-blob checks remain. The changed coverage return has one updated caller at lifecycle3860. The other audited mitigations and existing AR-19-01 remain unchanged; no new acceptance is granted.

The committed eight-target affected selection passed without skips in build/prb-schema-focused.log. Existing floors/markers are strengthened to51/120/99/72 without timeout changes. The recovery test verifies the immutable helper bytes before invoking its existing self-test. The independent auditor changed no file, project Git metadata or API state. Final full local/player/consumer, goal verification, exact-head protected CI and guarded PR B squash remain downstream gates; no new owner decision or release action is needed.

## Security Audit 2026-10-31

| Metric | Count |
|---|---|
| Threats found | 41 |
| Closed | 41 |
| Open | 0 |


## D-135 independent Windows wiring recheck

At e46023c53bdff9e7ac44fcfb33a9e237ceec0430, the fresh independent ASVS1 recheck confirms all41 mitigations preserved and threats_open0. The implementation diff is exactly .gitattributes and tests/CMakeLists.txt, byte-identical to the approved fa768f81 patch. No validator, workflow, policy, product or fixture source changed.

CMake5637-5648 derives the configurable phase-root readback as a repository-relative Git path while preserving the immutable revision, expected exit/output, label and timeout. Disposition reader148-184 still uses bounded immutable git-show reads; missing/wrong-root/drive paths refuse and traversal/external paths reject. The exact helper LF rule does not match the existing unpinned APU EOL negative. Helper bytes remain identical to its27635-byte Git blob, SHA25693a81e523eb1fd1d42e2c5172b28400475b6fc89c5bb7f1ec92abadb8fbf93ce. Lifecycle1428-1438 retains the raw byte comparison before executing the helper self-test; no normalization or relaxation was added to that check.

Independent actual readback passes22 assets. Recomputed-hash schema mutations, false workflow-G substitution, private-text, missing/traversal/drive-path and tampered-helper negatives refuse. Existing G/S dispatch/source/allowlist/protected-blob, exact transformation/hash/body, capture/privacy and policy authority checks remain unchanged. Current-head qualification contains23 passing affected tests with no skips; command-log hashes match. Forced-autocrlf baseline/fixed replay proves the checkout difference without claiming new native Windows qualification. Existing AR-19-01 remains the only acceptance. The auditor wrote no file, project Git metadata or API state. Fresh actual new-head native/protected CI and the guarded PR B boundary remain downstream gates.
