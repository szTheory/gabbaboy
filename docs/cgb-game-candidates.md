# CGB game candidate evidence contract

The candidate contract fixes exactly two identities and their order: Potion Panic (GB Compo
2025), followed by µCity 1.3's `preferred-ucity.gbc` only after a final Potion Panic no-go. The
checker validates evidence accounting. It does not grant rights, establish compatibility, or admit
candidate bytes to product packages.

## Immutable inputs and commands

Every project check resolves one full `--source-revision` commit and reads the candidate checker,
Phase 20 admission checker, CMake test registration and this document from that commit. Executable
contract files in the working checkout must match their immutable blobs. Record paths are fixed at
`tests/data/cgb-candidates/potion-panic.json` and
`tests/data/cgb-candidates/ucity-1.3.json`; a third top-level JSON record, missing record or
renamed identity fails the closed attempt-set check.

Run both synthetic checks with:

```sh
python3 -I tests/scripts/verify-cgb-candidates.py --self-test --repo-root . \
  --source-revision "$(git rev-parse HEAD)"
python3 -I tests/scripts/verify-cgb-candidates.py --self-test-controls --repo-root . \
  --source-revision "$(git rev-parse HEAD)"
```

Inspect one stage or both fixed records with `--check-record PATH` or `--check-all`. An admitted
replay also requires the exact CMake-built runner and its current test-build qualification receipt:

```sh
python3 -I tests/scripts/verify-cgb-candidates.py --check-all --require-final \
  --runner build/phase1/gabbaboy-runner \
  --current-build-qualification build/phase21-evidence/current-runner-qualification.json \
  --repo-root . --source-revision "$(git rev-parse HEAD)"
```

The receipt is created by the normal CMake test build after linking `gabbaboy-runner`. It binds
the selected full source revision, source qualification state, all 24 runner build inputs (including
`cmake/StateVersion.cmake` and `src/core/gbb_accept_input.h`), the
qualification writer, the canonical target path and the measured executable digest. The checker
validates those values against immutable Git blobs and the current files before replay, then checks
the same executable digest afterward. CMake creates this receipt only with `BUILD_TESTING=ON`;
`BUILD_TESTING=OFF` builds have no Python dependency or qualification writer.

A partial record names its current `stage` and every field beyond its cutoff as `not_observed`,
with the earlier blocking stage and a concrete reason. `--require-final` rejects partial records
and unresolved defects. Candidate records may be staged during an attempt, but project case/input
and receipt identities remain tied to immutable project source commits.

## Admission and native progress

An admitted record names the exact Phase 20 fixture manifest, its digest, and the adjacent
`admission.commit` pin. The candidate checker binds source, build recipe, tools, build inputs, ROM
bytes and cartridge header to those manifest identities, then invokes
`verify-fixture-admission.py --check-manifest` for that exact manifest. Phase 20 remains the sole
admission authority; title, license text, or a digest alone cannot authorize game use.

An admitted ROM must have a valid CGB header flag (`0x80` or `0xC0`) and the recorded execution
must report profile `cgb-cpu-e` with actual mode `native-cgb`. A header flag by itself does not
establish native-mode execution. Progress evidence binds the case, input script and source-anchored
predicate to immutable project/game revisions, records a positive `predicate-reached` result, and
requires distinct `no-input`, `wrong-input` and `impossible-predicate` controls with their raw
`predicate-not-reached` reasons. The positive and each negative control have distinct observation
digests. A bounded half-dot budget and ordered checkpoints bind RGB555 frame and PCM digests.

The historical receipt document repeats the ROM, case, input, predicate, recipe, project/game
source, runner, binary, mode, positive/control and observation identities. Those historical source
IDs and executable hashes remain immutable and are validated against the historical receipt.
Current replay uses the separate CMake qualification receipt above, so a newer current artifact
can replay older admitted evidence without rewriting its provenance.

Admitted observations use one strict `aggregate` object and named RGB555 checkpoints. The aggregate
binds `end_half_dots`, `frame_rolling555`, `pcm_sha256`, `pcm_samples`, `pcm_audible`, and each
channel's peak-to-peak range and change count. The rolling RGB555 digest and PCM digest/sample count
cover the runner's full emitted stream; audibility and per-channel statistics cover the runner's
PCM window from `play_start` through the one-second tail after the hit. Checkpoints retain only
their name, completion time and RGB555 digest because the runner does not emit per-checkpoint PCM.
The checker validates bounds and PCM audibility coherence, then requires every fresh aggregate
value to equal the immutable admitted observation. RGB555 and PCM values establish repeatability,
not rendering accuracy or perceptual quality. The synthetic replay controls run valid changed
rolling and PCM digests, sample counts, and silent/audible channel statistics through the replay
entry point and require an observation mismatch. They also reject missing or extra aggregate
fields and coordinated observation edits that no longer match the receipt digest. These controls
use only the private synthetic subject; neither named game record is changed or executed.

An executed build records its mechanism, acquired source and tool identities, source-qualified
launcher-policy digest, explicit environment allowlist, privilege-escalation status, exact mounts,
network/credential status and sanitized probe log identities. Only source and toolchain are
read-only mounts, with one writable output mount. Credentials and privilege escalation are
forbidden. Harmless baseline outside-root and local-network probes must be allowed, while the
restricted environment denies both. An admission failure stops before the candidate runner is
called. If the isolation environment cannot meet a network/probe condition, a build no-go records
`executed: false`, `result: not-run`, the concrete isolation failure and every later fact as
`not_observed` at the build cutoff. Credential inheritance, privilege escalation or extra writable
mounts are security defects and cannot be converted into a no-go. No-go and not-needed records
never invoke the candidate runner.

## Cutoffs, no-go and fallback

A final no-go identifies an evidence-backed rights, source, build, identity, mode or predicate
cause. Each later fact is `not_observed`; no digest, cartridge header, execution mode, predicate
result or output is invented beyond the cutoff. A reproduced harness, emulator or security defect
is `blocked-defect`, which cannot close the candidate pair.

The fallback record is eligible only after the primary no-go is committed and referenced by
immutable commit and record digest. If the primary is admitted, the fallback is `not-needed` and
contains no invented µCity ROM identity. Reversed order, another candidate ID, missing attempts,
and fallback after an admitted primary all fail final closure.

All positive and negative self-test records, the synthetic CGB ROM, its temporary admission
manifest and the synthetic runner are created in a private disposable Git clone. They never become
candidate outcomes and do not authorize, attempt or decide Potion Panic or µCity.
