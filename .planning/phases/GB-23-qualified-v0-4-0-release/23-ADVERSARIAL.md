# Phase 23 Adversarial Review

**Reviewed implementation:** 33a1e7faf0c4126a4840e3c1c55ee9d1589d2593
**Role:** adversarial
**Reviewer:** recovery-adversarial-20261110
**Independence:** independent source review; no implementation edits or commits.

## Result

ACCEPT for the reviewed implementation. No correctness or security finding remains open. ADV-01 through ADV-34 retain their historical identities, dispositions, fix commits and verification references in the evidence object below. ADV-35 records the previously reported D-169 worker-cleanup defect, independently rechecked as fixed at this source.

This recovery review covers the D-168 through D-173 changes from previously reviewed implementation 950c78b0bac936992403511a3cfa41f7cb1069c6, including D-172 from 10fee4515c9db0e8b259e089ef2ec41f0453b811 and a fresh D-173 delta review from b50f0c10e0794591a212edbfd083f10084805532. I inspected the immutable revision and verified the checkout's implementation matched it. Full local qualification, live required checks, and hosted/release qualification remain separate gates; this report does not establish them.

## D-168 bounded execution and preserved controls

The candidate harness invokes the actual cloned checker parser and main function in a fresh runpy namespace for each request, inside a reused isolated Python process. Its parent waits at the unchanged 30-second per-call limit, then terminates or kills and reaps the worker. Separate LimitedOutput objects count UTF-8 bytes for stdout and stderr, each capped at 1 MiB. The parent still checks the CLI return code and required diagnostic (tests/scripts/verify-cgb-candidates.py:1809-2038). The early in-process prototype at 8a6e1536d29a2bfa8d53236d4e2eba2766bb1342 checked elapsed time only after returning and had unbounded StringIO capture; it was superseded by the bounded subprocess implementation at 3c0489d722728c23f2369a0dced49c996b9ac9dc.

I directly attacked the exact current implementation with disposable scripts:

- Simultaneous stdout and stderr of exactly 1 MiB each are accepted, proving the streams do not share a combined 1 MiB limit. A one-byte excess on either stream rejects with candidate-subprocess-output-limit. A subsequent valid request succeeds.
- A request that sleeps for 31 seconds rejects with candidate-subprocess-timeout at the actual configured 30-second boundary; the captured worker process has exited. A new worker then accepts a valid request.
- Two invocations of the actual candidate CLI --help succeed. A disposable script that increments a module global prints 1 on both calls, establishing that reuse does not retain case module globals.

The disclosure control copies adoption inputs once into a private workspace but still launches the actual adoption CLI separately for every existing ledger case, with its 45-second subprocess timeout. Each invocation overwrites the disposable ledger. The altered-history, omitted-disclosure, handwritten-edit and relocated-disclosure controls retain their exact expected rejection checks and valid counterparts (tests/scripts/verify-support-ledger.py:4213-4448). The delta removes no semantic assertion.

At the preceding D-168 source, the parent-only archive cache retained at most 16 MiB. D-172 below divides that same combined budget between parent and worker. Worktree byte checks remain in the product validator, and the self-test requires cache reuse. Reusing already-read private-baseline rules does not cache mutated archive/product entries.

Its actual CLI parser/main also runs in a fresh namespace in an isolated reused worker. Direct invocation of its built-in worker controls rejects stdout overflow and a slow call for the intended diagnostics, then accepts real CLI --help after overflow and worker restart. Independent probes accept 1 MiB on each stream simultaneously and reject stderr at 1 MiB plus one byte. The worker is explicitly stopped on normal self-test completion. These probes inspect the production worker functions without running a second full archive/control suite.

Both consumer controls retain PROCESSORS=4. COST is 600 in ordinary configurations and 1800 only with sanitizers, matching the existing threefold sanitizer timeout scaling. Existing test inventory and per-test ceilings remain unchanged. The source-bound coverage self-test retains stale-COST negatives for both consumers, ordinary and sanitizer metadata validation, all 200 docs controls at two slots, and unrelated four-slot reservations.

## D-169 cleanup and exception exits

**ADV-35 — BLOCKER at the prior source; fixed.** The prior worker retained the synthetic temporary directory as its current directory until atexit. On Windows that can prevent removal. The correction at 3af81d66d1503f6ae4766d6a411f7604e5d4bd1d wraps the directory body in a finally that stops the worker before TemporaryDirectory exits (tests/scripts/verify-cgb-candidates.py:1926-1943).

I invoked the actual cleanup controls. Temporarily replacing the stop routine with a no-op causes the live-worker guard to reject with candidate-subprocess-stop-failed. Restoring the routine terminates the captured process. The exception control raises inside the context and verifies that the process is stopped and the directory absent. Both controls pass. The stop routine retains terminate, bounded wait, kill fallback and final still-live rejection; normal and exception cleanup share that path.

## D-170 complete dependency window and stale-value attacks

I traced ci.yml producer dependencies: changes has a five-minute cap, the longest dependent producer is native-windows at 70 minutes, and required-native depends on those results with a five-minute cap. The player-gate/package path is shorter. The four readers allow the approved 80-minute producer path:

- All three preview waiters use literal --deadline-seconds 4800 and 90-minute job caps.
- release.yml:candidate-fuzz uses 160 attempts at 30-second intervals, a 4800-second deadline and a 142-minute cap.
- Its declared bound is 4800 + 60 + 30 + 2700 + 900 = 8490 seconds, within 8520 seconds. The loop retains its elapsed-time deadline and per-request timeout. Failure to find completed exact-source evidence remains blocking.

The four matching ledger rows preserve their cited run, SHA, p50 and sample count, with changed-body disclosures. The sanitizer inventory alone changes from 55 to 65 minutes under D-168. Other producer caps remain as approved. Preview comments still describe the earlier D-165 window; executable values, ledger and source-bound controls consistently enforce D-170, so those historical comments do not change gate behavior.

The immutable-source coverage self-test passes 598 controls. I inspected its new mutations: it rejects the immediately previous release 150-attempt/4500-second/137-minute values, previous preview 4500-second/85-minute values, older release 90-attempt/3000-second/112-minute values, older preview 3900-second/75-minute values, and stale ledger rows. Cause-specific release/ledger assertions remain active. Accepted inputs come from git blobs at the requested revision, including the complete workflow inventory and CMake version.

Defenses behind ADV-31 through ADV-34 remain: exact parsed unconditional shell argv, pinned checkout immediately before the waiter, pinned host runners, no job containers/services, and workflow/job/step environment/default checks. The self-test retains comment-only deadline, dead-branch, Python-function shadow, GITHUB_ENV/BASH_ENV writer, changed-runner and container/service negatives. The revised production policy snapshot changes only the four approved release self-test mutation anchors; reviewed-snapshot and other baseline AST/source guards remain.

Configured caps do not guarantee hosted queue availability or package completion near the deadline. Expiry fails closed, the limitation explicitly retained by D-170.

## D-171 fixture trigger attacks

The fixture-repro delta is only branches: [main] under push. pull_request and workflow_dispatch remain unconditional; all seven job bodies are byte-unchanged. The source-bound checker requires the exact parsed trigger mapping. Four paired mutations reject unrestricted pushes, missing PR coverage, missing manual recovery and a wrong push branch with the intended trigger diagnostic. The exact accepted workflow passes. This removes duplicate PR-branch push work while retaining PR, main and manual evidence.

## D-172 exact-source cache extension review

I inspected b50f0c10e0794591a212edbfd083f10084805532 against 10fee4515c9db0e8b259e089ef2ec41f0453b811. The sole source delta extends the existing self-test immutable-blob cache into the reused CLI worker; the other changed files record the adopted scope. No workflow, CTest registration, timeout or existing archive/product/receipt control changes.

The parent and worker each retain at most 8 MiB of blob values, preserving the combined 16 MiB limit; an entry above 1 MiB is never retained. Keys contain the checker source digest, canonical repository root, full lowercase 40-character commit identity and requested path. Symbolic revisions bypass caching, and a failed blob lookup propagates before insertion (tests/scripts/verify-v02-source-archive.py:711-751). The worker reloads the archive script and helper modules for each CLI invocation. Only the helper blob function receives the shared immutable-value cache; archive parsing, policy reads, current-worktree reads, source comparisons and product validation execute again. The parent validates worker-reported cache bounds, and final self-test completion requires actual worker cache hits.

Independent focused probes at exact b50f0c10 passed the actual built-in cache controls: exact-identity reuse; root/revision/path isolation; changed checker-source isolation; symbolic-ref nonretention; exact 8 MiB aggregate capacity; excess-capacity nonretention; and oversized-entry nonretention. Replacing the cache installer with a no-op makes the actual control reject with its intended immutable-reuse diagnostic, establishing that it exercises the cache. An additional probe forces an initial blob-read exception and verifies that neither entries nor retained bytes change; a subsequent successful read is cached and reused. Another probe installs the production wrapper in two separate fresh helper namespaces and verifies shared immutable-value reuse across them.

I also reran the actual worker timeout/output controls on the changed source: overflow and timeout reject for their expected causes, while real CLI help works after overflow and restart. Fresh CLI/parser/main execution and independent stream limits remain in the source. The original 17 positive and 94 negative cases remain, with new cache controls added rather than replacing archive/product/receipt controls. The original 90-second CTest ceiling remains unchanged. No new correctness or security finding was established; this review does not claim that the affected CTest or full qualification passed at b50f0c10.

## D-173 exact-source lifecycle scheduling review

I inspected the sole source delta at 33a1e7faf0c4126a4840e3c1c55ee9d1589d2593 against b50f0c10e0794591a212edbfd083f10084805532. It moves the unchanged serial positive_baselines sequence into one slot of the existing ThreadPoolExecutor, then adds its result to the positive count before aggregating the unchanged negative futures (tests/scripts/verify-release-lifecycle.py:3739-3773). It does not alter the three baseline functions, case builders, real production script calls, expected diagnostics or result aggregation. The template setup remains the fourth positive, with the existing 101 control outcomes retained. PARALLEL remains between two and eight; the baseline consumes an existing slot rather than increasing that ceiling. CTest remains RUN_SERIAL with a 60-second timeout, and inventory/registration are unchanged.

I traced the new concurrent boundary. build_stages completes before submitting any work, freezing attached/manifested/finalized snapshots. Each baseline creates its own Scenario. Scenario allocation uses the existing locked counter, copies snapshot state into a distinct root, and owns its stub state, home, runner directories and workspaces (Scenario:2045-2068). Subject workspaces clone the shared judge rather than modifying it; trusted scripts are copied into the private workspace. Baseline source/draft/final checks read the shared immutable evidence and use their private transport state. The newly overlapped baseline path does not call snapshot or mutate the shared capture/template. Negative cases were already mutually concurrent, and their scenario-local mutations remain isolated from the new baseline task.

Independent cheap scheduling probes invoked the actual current controls function with disposable setup and synthetic task callbacks, avoiding a duplicate production suite. A baseline waiting for a control-side event succeeds only when overlapping the existing pool, and positive/control results aggregate correctly. Separate baseline-failure and negative-control-failure probes propagate their distinct exceptions. In all cases, the executor completes every submitted task before returning or raising; no failure path can produce a successful report by omitting the baseline or a later control. The successful path explicitly obtains the baseline and every control future result.

No new correctness or security defect was established. The earlier focused 60-second timeout and matching-environment diagnostic remain historical evidence for the scheduling decision, not current qualification. The parent owns the affected CTest and final focused/full/hosted results; this reviewer did not run an expensive duplicate lifecycle suite.

## Historical review continuity

Historical finding records below remain unchanged. The public Markdown parser, release-note/version-window matcher, notice and self-test path-confinement code, recovery adoption pin, review-evidence validator, source/package trust judge and legal fixture boundaries have no implementation delta from the reviewed baseline. I traced the changed harnesses into those unchanged production checks.

Earlier source-specific runs and limitations remain historical evidence in each finding's verification_ref; they are not rerun claims for this review. No real game/diagnostic fixture was fetched, built, run or admitted during review; no hosted workflow was started, release published or platform/signing claim promoted.

## Prior recovery independent verification

At exact implementation 10fee4515c9db0e8b259e089ef2ec41f0453b811:

- python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev 10fee4515c9db0e8b259e089ef2ec41f0453b811 passed with 598 controls.
- python3 -I .github/scripts/verify-workflow-policy.py --check --root . passed.
- Candidate worker probes passed separate stream boundaries, both overflow causes, actual 30-second timeout and termination, restart, actual parser execution, fresh namespaces, causal disabled-stop rejection and exception cleanup.
- Source-archive worker probes passed parser/help reuse, both stream boundaries, overflow rejection, forced timeout and restart.

The parent owns full local qualification and hosted evidence. At 10fee4515 the parent reported v02_source_archive_controls reaching its unchanged 90-second ceiling; that failure is retained as historical evidence. Subsequent D-172 and D-173 source reviews appear above; the parent runs the affected tests and final qualification. This reviewer started no additional full suite. No new correctness/security finding requires an owner rescope; the parent must establish current local and hosted results.

<!-- gbb-review-evidence:start -->
```json
{
  "schema_version": 1,
  "report_id": "gbb-phase23-adversarial-33a1e7fa-20261110-recovery",
  "role": "adversarial",
  "reviewer_id": "recovery-adversarial-20261110",
  "independent": true,
  "reviewed_sha": "33a1e7faf0c4126a4840e3c1c55ee9d1589d2593",
  "findings": [
    {
      "id": "ADV-01",
      "category": "correctness",
      "severity": "high",
      "required_property": "Only visible Markdown prose may satisfy required release-note disclosures.",
      "disposition": "fixed",
      "rationale": "The exact-source renderer-built release-note baseline passes. The current controls reject disclosures hidden in inline and block code, comments, and container code; removing a required visible clause fails with its specific diagnostic.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-version-window.py --self-test-version-v04: positives=63 controls=66."
    },
    {
      "id": "ADV-02",
      "category": "correctness",
      "severity": "high",
      "required_property": "Release notes must not claim a requirement is complete while its required status remains Pending.",
      "disposition": "fixed",
      "rationale": "The exact-source release-note controls reject both a promoted Pending row and contradictory completion prose; the valid Pending baseline passes before each mutation.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-support-ledger.py --self-test-disclosure: positives=4 controls=20."
    },
    {
      "id": "ADV-03",
      "category": "correctness",
      "severity": "high",
      "required_property": "Metadata-only diagnostic inventories must not be presented as executed or passing diagnostics.",
      "disposition": "fixed",
      "rationale": "The exact-source release-note controls reject the claim that all 513 named diagnostic microtests executed and passed, while accepting the metadata-only baseline with seven unresolved gates and zero real fixtures executed or admitted.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; the named metadata-as-diagnostic mutant checks its specific diagnostic."
    },
    {
      "id": "ADV-04",
      "category": "correctness",
      "severity": "high",
      "required_property": "A rights-scope no-go must not be represented as a legal license prohibition without evidence.",
      "disposition": "fixed",
      "rationale": "The exact-source notes controls reject an unsupported claim that both candidates' licenses prohibit repository and public-CI use; the source/rights-scope baseline remains accepted.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; rights-scope-presented-as-license-prohibition mutant."
    },
    {
      "id": "ADV-05",
      "category": "correctness",
      "severity": "high",
      "required_property": "Inline code, image destinations, and hidden markup cannot satisfy visible-prose or ledger-link requirements.",
      "disposition": "fixed",
      "rationale": "Visible prose and a real ledger link pass. Code-only disclosure evidence, image-ledger destinations, and hidden titles/alt text fail the required visibility or ledger checks.",
      "fix_sha": "9e09eef8b379ca8d329cb13bf354058661296daa",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 pass their paired visibility controls."
    },
    {
      "id": "ADV-06",
      "category": "correctness",
      "severity": "high",
      "required_property": "A required support-ledger link must target the ledger itself, not contain its path in unrelated URL text or a title.",
      "disposition": "fixed",
      "rationale": "Relative and canonical ledger links are accepted; external-query, title-only, image, and malformed destinations reject for ledger mismatch or malformed-link reasons.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 passed."
    },
    {
      "id": "ADV-07",
      "category": "correctness",
      "severity": "high",
      "required_property": "Text hidden by closed or unterminated HTML comments cannot satisfy release-note or changelog requirements.",
      "disposition": "fixed",
      "rationale": "Closed- and open-comment mutants cannot satisfy candidate or required-clause checks; a hidden changelog ledger link fails the version-output check. Visible counterparts pass.",
      "fix_sha": "9a193975fb32ae69bd09be2cf847e3271d078733",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; verify-version-window.py --self-test: positives=11 controls=64."
    },
    {
      "id": "ADV-08",
      "category": "correctness",
      "severity": "high",
      "required_property": "Fenced and indented code inside list and blockquote containers cannot satisfy disclosure or changelog visibility requirements.",
      "disposition": "fixed",
      "rationale": "The current controls cover same-line and nested list/blockquote fences plus indented code. Hidden disclosures and links reject; visible disclosures and genuine code masking remain accepted.",
      "fix_sha": "46f5ce4a515daa65bb9850a28a1ee4be9b9b8c5a",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04 and verify-version-window.py --self-test-version-v04 passed."
    },
    {
      "id": "ADV-09",
      "category": "correctness",
      "severity": "high",
      "required_property": "Incomplete raw-HTML block openers cannot hide required changelog links or release-note disclosures.",
      "disposition": "fixed",
      "rationale": "Script, pre, style, doctype, and XML processing-instruction openers fail at the required paths while comments, code, and escaped examples remain valid when visible evidence is present. The legacy-matcher controls establish causality.",
      "fix_sha": "a63f1dc67654613e105ac1071b7445f21adea0bc",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-version-window.py --self-test-version-v04: positives=63 controls=66; verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72."
    },
    {
      "id": "ADV-10",
      "category": "correctness",
      "severity": "high",
      "required_property": "Markdown visibility and claim matching must follow the paired D-144 parser cases for labels, continuations, comments, fences, and autolinks.",
      "disposition": "fixed",
      "rationale": "The source-bound controls reject whitespace-only image labels, invalid tab-expanded continuations, mismatched reference-label comment payloads, false comment-created fences, and a title-only hardware disclosure around an autolink. Valid collapsed labels, matching comments, correct continuations, genuine fences, and valid titles remain accepted.",
      "fix_sha": "3d27596b341877d9a19cb82409e178f9eae0d1e9",
      "verification_ref": "D-144 source-bound docs controls at 4c9c54f8b5a33e758624c997f107d1ffdd7c94a0 passed 473 checks/255 rejected controls; reviewed-source diff leaves the parser unchanged; current release-note controls pass 2/72."
    },
    {
      "id": "ADV-11",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unicode Cf characters cannot split a visible unsupported CGB-game claim.",
      "disposition": "fixed",
      "rationale": "The claim-only matcher removes Cf characters, rejecting U+200B, U+2060, and U+200C claims while leaving unrelated disclosures and safe prose unchanged.",
      "fix_sha": "742bf1bb5dd3a6e71ab93dbdb420bca2ec94d16a",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; exact-source docs shards 0/200 and 199/200 pass; matcher unchanged by D-155."
    },
    {
      "id": "ADV-12",
      "category": "correctness",
      "severity": "high",
      "required_property": "Unicode 18.0 Default_Ignorable_Code_Point characters, including non-Cf characters, cannot split a visible unsupported CGB-game claim.",
      "disposition": "fixed",
      "rationale": "The matcher includes the frozen Unicode 18.0 default-ignorable ranges; current paired controls cover U+034F and representative non-Cf ranges with safe-text counterparts.",
      "fix_sha": "a6bc0a824bce55de57422e2b6b73b94ed0f841d1",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; docs matcher is unchanged by D-155."
    },
    {
      "id": "ADV-13",
      "category": "correctness",
      "severity": "high",
      "required_property": "Valid CommonMark references to invisible characters cannot split an unsupported CGB-game claim after rendering.",
      "disposition": "fixed",
      "rationale": "Hexadecimal, decimal, and named references to invisible/default-ignorable characters are decoded for the claim matcher; code spans remain masked and visible safe-reference prose remains accepted.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; parser/matcher code unchanged by D-155."
    },
    {
      "id": "ADV-14",
      "category": "correctness",
      "severity": "high",
      "required_property": "All valid CommonMark character references in visible prose are normalized before unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "The claim matcher decodes valid visible references to spaces and CGB letters as well as invisible separators. Safe visible references and masked code spans retain their intended behavior.",
      "fix_sha": "fc0ba4ff9626e06e04d8800800561b51414166bf",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; exact-source claim/profile controls pass 22 positives/21 controls."
    },
    {
      "id": "ADV-15",
      "category": "correctness",
      "severity": "high",
      "required_property": "CommonMark hard line breaks and encoded spaces are joined for unsupported-game matching in docs, release notes, and notices after code masking.",
      "disposition": "fixed",
      "rationale": "LF, CR, CRLF, encoded-space, soft-break, safe-prose, and code controls remain paired; the notices caller supplies uncollapsed visible prose to the shared matcher.",
      "fix_sha": "e26757fafc818a92ddf7ca45f1a409658a5a5bdd",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): release-note controls pass 2/72; docs shard 0/200 passes notice-path child controls; notice caller and matcher are unchanged except D-155 path checks."
    },
    {
      "id": "ADV-16",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible CGB claim text split by CommonMark emphasis or inline-link labels cannot evade unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "Strong, intraword-star, underscore-emphasis, and inline-link-label claims are rejected. Intraword underscores, escaped punctuation, code, and destination/title-only claims remain accepted.",
      "fix_sha": "e017078b72e78b38fb596faced3af3e35c2ca0ce",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): verify-v02-adoption.py --self-test-release-notes-v04: positives=2 controls=72; matcher code unchanged by D-155."
    },
    {
      "id": "ADV-17",
      "category": "correctness",
      "severity": "high",
      "required_property": "Visible shortcut, full, and collapsed reference-link labels participate in unsupported-game matching while destinations and titles do not.",
      "disposition": "fixed",
      "rationale": "The matcher resolves each valid reference-label form and excludes its destination/title; unresolved and escaped labels, code, and destination-only claims remain accepted counterparts. Notice uses the same claim matcher.",
      "fix_sha": "b798781105b8f6f803e85aa2ad766d2b2fdbec22",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): release-note controls pass 2/72; docs shards 0/200 and 199/200 pass; parser/matcher diff is empty for D-155."
    },
    {
      "id": "ADV-18",
      "category": "security",
      "severity": "high",
      "required_property": "Delimiter matching must not rescan all prior unmatched runs for each closer in bounded public Markdown input.",
      "disposition": "fixed",
      "rationale": "The matcher uses fixed per-marker candidate buckets and exhausts candidates rather than scanning all prior delimiter runs; dense unmatched-marker controls assert claim detection without timing thresholds.",
      "fix_sha": "6876fab06bf746fdaab67beaa4d52a6b1c70ac06",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): release-note controls pass 2/72; source inspection confirms the candidate-stack implementation is unchanged by D-155."
    },
    {
      "id": "ADV-19",
      "category": "correctness",
      "severity": "high",
      "required_property": "CommonMark emphasis flanking treats Unicode punctuation and symbol categories P and S as punctuation for unsupported-game matching.",
      "disposition": "fixed",
      "rationale": "The exact-source matcher uses Unicode P/S categories. The paired Unicode-symbol claim and safe-prose controls are retained; current release-note controls pass.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): release-note controls pass 2/72; historical exact-source D-153 probes rejected both claims on four production paths and accepted paired safe/code controls; matcher is unchanged by D-155."
    },
    {
      "id": "ADV-20",
      "category": "security",
      "severity": "high",
      "required_property": "Impossible nested or over-999-character reference-label candidates are rejected before copying or normalization.",
      "disposition": "fixed",
      "rationale": "A bracket stack and prefix count check nested/overlong spans before slicing or normalization; only valid labels at or below CommonMark's 999-character limit are normalized. Dense-bracket controls retain safe prose counterparts.",
      "fix_sha": "4c9c54f8b5a33e758624c997f107d1ffdd7c94a0",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): release-note controls pass 2/72; historical exact-source D-154 probes reject the 512-level attack on four production paths and accept safe counterparts; source is unchanged by D-155."
    },
    {
      "id": "ADV-21",
      "category": "security",
      "severity": "high",
      "required_property": "Notice inputs and self-test copy destinations must resolve inside their respective roots, including when paths traverse or follow symlinks.",
      "disposition": "fixed",
      "rationale": "The old inline notice path could read outside the checkout and be reused as a copy destination. The reviewed code rejects traversal components, resolves source symlinks and enforces repository containment, and re-resolves copy destinations after parent creation. Current minimal-tree probes accept baseline/in-root paths, reject traversal and external symlink inputs as notice-path-outside-root, and reject a target symlink as self-test-copy-path-outside-root with zero external writes. The exact-source docs shard runs its matching traversal, symlink, and copy controls.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): docs shard 0/200 passed; direct check_notices baseline=112 and safe in-root=113, traversal/symlink rejected; direct copy_inputs normal copy passed and destination symlink rejected with external_files=0."
    },
    {
      "id": "ADV-22",
      "category": "other",
      "severity": "medium",
      "required_property": "The focused Plan 23-04 CTest selector must include every registered numbered docs shard, including 100–199.",
      "disposition": "fixed",
      "rationale": "The former two-digit selector omitted the high-numbered shards. The corrected `[0-9]+` selector matched all 199 numbered tests in an isolated CTest run, including 100 and 199; shard 199/200 itself passed. CMake registration, expected inventory, and timeout allowlist contain each numbered shard once.",
      "fix_sha": "9166ab60d25c6d246761b4aa33a0ceb35dd83f5c",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): exact Plan regex through ctest -N -R selected 200 total entries; CMake range/inventory/budget inspection matched shards 1–199 exactly; production docs shard 199/200 passed."
    },
    {
      "id": "ADV-23",
      "category": "other",
      "severity": "medium",
      "required_property": "Every new 90-second docs-shard budget row must resolve against both the plan-pinned and PR-base checker, while D-069 remains the governing timeout policy.",
      "disposition": "fixed",
      "rationale": "At the preceding source the 168 shard rows cited D-154, which did not resolve at the immutable plan base. The exact reviewed source remaps those rows to D-068. D-068 exists and was unused in both checker bases; D-069 still governs the timeout. The immutable budget checker passes against both the plan-pinned base and exact PR base.",
      "fix_sha": "7c6f01ad5ecf3b6736bf694324acc1671d9e20cc",
      "verification_ref": "python3.14 -I tests/scripts/verify-test-budget.py --build-dir build --base f2b05c9fb3ba314cfe46959b64073ce9441724ca --repo . (pass); same command with --base 1ab65414d60828fa9505babeaeea9de0571f016c (pass); tests/scripts/verify-test-budget.py --self-test (54 controls pass)."
    },
    {
      "id": "ADV-24",
      "category": "other",
      "severity": "medium",
      "required_property": "The post-tag recovery control must pin the exact D-155 adoption-checker bytes and preserve comparisons against both the immutable pin and the reviewed revision.",
      "disposition": "fixed",
      "rationale": "The lifecycle checker pin now names 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c. The adoption checker at that pin and at the reviewed source has identical SHA-256 bytes, and the recovery self-test passed with both immutable checks retained.",
      "fix_sha": "bd5ab993a3f09307e6a5ef31185f554740a0787b",
      "verification_ref": "At b677 (historical evidence; D-163 changes only docs CTest scheduling and its coverage checker, leaving this finding’s behavior controls unchanged): python3.14 -I tests/scripts/verify-release-lifecycle.py --rev 7c6f01ad5ecf3b6736bf694324acc1671d9e20cc --self-test-post-tag-recovery (controls=99 positives=12); verify-v02-adoption.py blob SHA-256 at 9166ab60d25c6d246761b4aa33a0ceb35dd83f5c and b677 both 4d0ac0c724e10c7cbca3f22d57c35dd90e98dddde396f47eda23f7289ab29e93."
    },
    {
      "id": "ADV-25",
      "category": "other",
      "severity": "medium",
      "required_property": "The workflow-policy coverage verifier must pin the exact D-157 policy source while retaining baseline AST checks for functions outside the approved change set.",
      "disposition": "fixed",
      "rationale": "At 01370352 the D-157 policy source changed but the coverage checker still pinned the earlier snapshot, so its self-test rejected the candidate source. The follow-up commit pins the exact 01370352 policy blob and lists only the reviewed changed functions for the historical AST exception. The exact-source self-test and configured-inventory check now pass.",
      "fix_sha": "ecdde9d5f63500dd0ad32d9e101f47e29ded0eb2",
      "verification_ref": "At exact source bc282cc229c887d7034e533175249861db846154: workflow-policy coverage self-test passes 526 controls, including one former-four-slot and one wrong-label negative for each of 200 docs controls; configured --check passes 540 controls/6 groups; focused coverage CTest pair passes 2/2."
    },
    {
      "id": "ADV-26",
      "category": "correctness",
      "severity": "high",
      "required_property": "The Windows planning-label exception must compare all repository and output path arguments using the same case-insensitive host normalization, and its case-variant positive control must pass.",
      "disposition": "fixed",
      "rationale": "The reviewed correction normalizes both renderer --repo/--output values and the review-evidence --repo value before comparison. Wrong-repository renderer and review-command negatives reject. The exact-source POSIX self-test passes all 33 controls, including simulated Windows case variants for renderer output, renderer repository, and review repository paths.",
      "fix_sha": "b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae",
      "verification_ref": "At preceding exact source b75ecb97d8ab11cda5dcb3cc94a87363e60f0cae: verify-planning-labels.py --self-test (33 controls pass, including POSIX simulated-Windows path cases). This source does not change that checker."
    },
    {
      "id": "ADV-27",
      "category": "correctness",
      "severity": "high",
      "required_property": "The exact configured CTest coverage checker must accept the actual v02_support_ledger_controls registration while enforcing its 120-second timeout and four-slot reservation.",
      "disposition": "fixed",
      "rationale": "The coverage checker now accepts and validates the exact support-ledger test properties, including LABELS=[planning,v02] and ENVIRONMENT=[GBB_TEST_BUILD_DIR=<configured build>], while retaining timeout=120 and PROCESSORS=4 checks. Exact configured-inventory validation passes at this source; the targeted CTest selection passes all three tests.",
      "fix_sha": "d0fb68361f3ffd82e1205e16609f644d4f733df2",
      "verification_ref": "At exact source bc, configured coverage check passes 540 controls/6 groups and focused coverage CTest pair passes 2/2; the 526-control self-test retains the Windows environment-path positive and wrong-directory negative. All docs reservations are two slots; non-doc reservations remain four."
    },
    {
      "id": "ADV-28",
      "category": "other",
      "severity": "medium",
      "required_property": "The workflow-policy coverage self-test must causally reject a wrong native or sanitizer-scaled timeout for v02_support_ledger_controls.",
      "disposition": "fixed",
      "rationale": "The checker self-test now changes the support-ledger native timeout to 119 seconds and the sanitizer-scaled timeout to 120 instead of 360; both mutations are rejected. It also reduces PROCESSORS to 3 for each of the four D-157 controls and the D-158 support-ledger control, and those mutations reject. Accepted native/scaled fixtures retain the exact labels and environment.",
      "fix_sha": "d0fb68361f3ffd82e1205e16609f644d4f733df2",
      "verification_ref": "At exact source bc, the 526-control self-test rejects native/scaled support-ledger timeout mutants, three-slot non-doc mutants, former-four-slot docs mutants, all docs wrong-label mutants, and the Windows wrong-directory mutant; configured check and focused coverage CTest pair pass."
    },
    {
      "id": "ADV-29",
      "category": "correctness",
      "severity": "high",
      "required_property": "The source-bound workflow-policy coverage self-test must create one synthetic CTest entry per policy or reserved test and execute a three-slot negative for every reserved control.",
      "disposition": "fixed",
      "rationale": "At fdccc15a, adding workflow_policy_group_ci and workflow_policy_group_rehearsal to PHASE23_RESERVED_TESTS made _self_test append each twice: once from GROUPS and once from the generic reserved-test loop. The initial validation rejected before any reservation mutation and the coverage CTest pair failed 1/2. At 4343d95d, the fixture generator subtracts POLICY_TEST_NAMES from only the generic synthesis loop. Both policy tests remain in PHASE23_RESERVED_TESTS and in the per-reservation mutation loop, so all ten D-161 three-slot negatives still execute.",
      "fix_sha": "4343d95dde8597253994efff2e030ae25089d288",
      "verification_ref": "At exact source bc, the 526-control self-test and 2/2 coverage CTest pair pass. The expanded inventory includes 200 unique docs controls and exercises one former-four-slot and one wrong-label mutation per entry without duplicate fixtures."
    },
    {
      "id": "ADV-30",
      "category": "correctness",
      "severity": "medium",
      "required_property": "The native macOS timeout self-test must read workflow YAML, timeout ledger, and project version from its immutable --rev instead of mutable checkout files.",
      "disposition": "fixed",
      "rationale": "At d3811b8e the positive pair check and mismatch fixture copied live .github/workflows, .github/ci-timeouts.json, and CMakeLists.txt after resolving --rev, allowing dirty configuration to mask a committed mismatch. At 48d8e501 the fixture lists workflow paths from the candidate tree and reads every workflow, the timeout ledger, and CMakeLists.txt with git show at the resolved candidate commit before running the positive and stale-ledger negative.",
      "fix_sha": "48d8e501872b9a19138a4653830a40b983199adc",
      "verification_ref": "At exact source 48d8e501872b9a19138a4653830a40b983199adc: python3 -I tests/scripts/verify-workflow-policy-coverage.py --self-test --root . --rev 48d8e501872b9a19138a4653830a40b983199adc passed with 528 controls; python3 -I .github/scripts/verify-workflow-policy.py --check --root . passed."
    },
    {
      "id": "ADV-31",
      "category": "correctness",
      "severity": "high",
      "required_property": "The preview waiter deadline check must bind the parsed command event and cannot count deadline text that appears only in a shell comment.",
      "disposition": "fixed",
      "rationale": "At 6774831810824740a10b6644f7452eb33091a1f1, a regex-style source check accepted a stale deadline when the expected 4500 text appeared only in a comment. The corrected shell-event parser requires the exact literal argv; the causal comment-only control rejects on all three preview lanes.",
      "fix_sha": "07bdf08d17d253abe8d1f2ac63c6bfdf16bf40b1",
      "verification_ref": "At 950c78b0bac936992403511a3cfa41f7cb1069c6, verify-workflow-policy-coverage.py --self-test passed 573 controls, including a comment-only stale deadline mutant for each preview waiter."
    },
    {
      "id": "ADV-32",
      "category": "correctness",
      "severity": "high",
      "required_property": "The exact-head waiter must execute unconditionally as one parsed shell event, and a shell function must not shadow the expected Python command.",
      "disposition": "fixed",
      "rationale": "Re-review of 07bdf08 found dead-branch and in-command Python-function-shadow bypasses. The source-bound validator now requires one unconditional shell event with exact literal argv; both causal mutants reject for each of the three waiter jobs.",
      "fix_sha": "e5a2f71dbf2ed27912d0ba810d434e95b9fc8c4c",
      "verification_ref": "At 950c78b0bac936992403511a3cfa41f7cb1069c6, the 573-control exact-source coverage self-test rejects dead-branch and shadowed-Python waiter mutations on all three preview jobs."
    },
    {
      "id": "ADV-33",
      "category": "security",
      "severity": "high",
      "required_property": "No untrusted step may run between the exact pinned checkout and waiter and set BASH_ENV through GITHUB_ENV to alter the waiter shell.",
      "disposition": "fixed",
      "rationale": "At e5a2f71d, an injected prior step could write a Python wrapper and set BASH_ENV through GITHUB_ENV. The profile now requires the waiter at index 1 immediately after the exact pinned checkout, and its causal prior-step writer is rejected for each lane.",
      "fix_sha": "170b7eb2ba24ea166376ddf2088ce3d731fddc37",
      "verification_ref": "At 950c78b0bac936992403511a3cfa41f7cb1069c6, the 573-control exact-source coverage self-test rejects a prior-step GITHUB_ENV/BASH_ENV writer for all three preview jobs."
    },
    {
      "id": "ADV-34",
      "category": "security",
      "severity": "high",
      "required_property": "The exact-head waiter must run on the pinned host runner and reject job-level containers or services that could alter its shell environment or interpreter.",
      "disposition": "fixed",
      "rationale": "At 170b7eb2, a Linux job container with BASH_ENV could install a python3 wrapper while preserving the checked step and argv. The corrected profile pins the Linux lane to ubuntu-22.04 and rejects container/services keys on every waiter job; all causal mutants reject.",
      "fix_sha": "950c78b0bac936992403511a3cfa41f7cb1069c6",
      "verification_ref": "At 950c78b0bac936992403511a3cfa41f7cb1069c6, exact-source coverage self-test passed 573 controls, with a changed-runner negative and container/services negatives for each lane; adversarial and security re-reviews accepted."
    },
    {
      "id": "ADV-35",
      "category": "correctness",
      "severity": "high",
      "required_property": "The reusable candidate-checker worker must stop before its synthetic temporary directory is removed, including exception exits.",
      "disposition": "fixed",
      "rationale": "At 3c0489d722728c23f2369a0dced49c996b9ac9dc the worker retained the synthetic temporary directory as its current directory until atexit, risking Windows cleanup failure. The D-169 context manager stops it in a finally block inside TemporaryDirectory. At the exact reviewed source, the causal disabled-stop control rejects a still-live worker, real cleanup terminates it, and the exception control confirms both worker termination and temporary-directory removal.",
      "fix_sha": "3af81d66d1503f6ae4766d6a411f7604e5d4bd1d",
      "verification_ref": "Exact 10fee4515 source: tests/scripts/verify-cgb-candidates.py:1926-1972; independently invoked _checker_worker_cleanup_controls() returned 2; direct probes also passed separate 1 MiB stdout/stderr boundaries, both overflows, actual 30-second timeout with worker terminated, restart and fresh namespace reuse."
    }
  ]
}
```
<!-- gbb-review-evidence:end -->
