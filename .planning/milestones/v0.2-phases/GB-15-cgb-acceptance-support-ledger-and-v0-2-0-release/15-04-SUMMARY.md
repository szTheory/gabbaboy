---
phase: 15-cgb-acceptance-support-ledger-and-v0-2-0-release
plan: "04"
subsystem: testing
tags:
  - cgb
  - adoption
  - notices
  - release-notes
  - claims
requires:
  - phase: "Phase 15 Plan 02"
    provides:
      - "The v0.2.0 support ledger and tagged sidecar contract the guides link to"
  - phase: "Phase 15 Plan 03"
    provides:
      - "Relocated C/C++ client and save guidance the integration docs describe"
provides:
  - "A semantic prose, public-symbol, notice and release-note contract for v0.2.0 adoption claims"
  - "Adopter model, mode, audio, preview and release guidance limited to shipped behavior"
  - "Notices reconciled with every admitted fixture directory by recomputed digests"
affects:
  - "Phase 15 source archive, workflow and delivery plans that register and consume this checker"
actuals:
  tokens: 15038
  tasks: 2
  commits: 2
plan_head_before: 954ca111c7e6de1a8d27038c7b6b462206847e2c
plan_head_after: 338edc1bfc04b83ea75c304555645c02ac618f80
tech-stack:
  added: []
  patterns:
    - "Prose parsing strips HTML comments and fenced code so a comment-only phrase never satisfies a claim"
    - "Public gbb_/GBB_ names resolve against the installed header; internal names need a verified source-file allowance"
    - "Notice digests are recomputed from committed fixture bytes in both directions (missing and unknown directories)"
key-files:
  created: []
  modified:
    - tests/scripts/verify-v02-adoption.py
    - docs/cgb-profile.md
    - docs/audio-and-playback.md
    - docs/preview.md
    - docs/release.md
    - THIRD_PARTY_NOTICES.md
    - README.md
key-decisions:
  - "Reuse the production CGB claim parser (verify-cgb-corpus-claims.py) for claim markers and qualification grammar rather than a second grammar, with a negation guard so 'no ... is claimed' prose is not misread as a claim."
  - "Name only shipped behavior: fuzz evidence is documented as a release requirement with no campaign result claimed, and publication is left to the GitHub Releases page."
  - "Reconcile notices with a manifest/LICENSE digest table covering all admitted fixture directories, including SameSuite X11 rights, instead of per-row prose digests."
requirements-completed:
  - SHIP-10
  - CGB-11
  - SHIP-09
coverage:
  - id: D1
    description: "Model, mode, raw RGB555, digital PCM, dummy SDL and physical/perceptual limit guidance in the CGB profile, audio and preview guides is checked as prose, including claim markers parsed by the production CGB claim parser."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --check docs"
        status: pass
  - id: D2
    description: "Every gbb_ or GBB_ name in the public surfaces resolves in the public header or a verified internal-source allowance; an undeclared or removed symbol is rejected."
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"
        status: pass
  - id: D3
    description: "Removed API, RTC, save and model phrases, comment-only limits and false hardware, game, signing, publication, platform and fuzz claims each fail the real command line with a named reason."
    requirement: CGB-11
    human_judgment: false
    verification:
      - kind: unit
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"
        status: pass
  - id: D4
    description: "The release guide separates source archives, fixture-free product packages, tested runner labels, installed versus downloaded native proof, exact-tag sidecars and the unsigned/not-notarized macOS state."
    requirement: SHIP-09
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --check docs"
        status: pass
  - id: D5
    description: "THIRD_PARTY_NOTICES lists every admitted fixture directory with manifest and notice digests recomputed from committed bytes, carries the source-archive distinction and rejects stale, missing, unknown and Rebound-attribution entries."
    requirement: SHIP-09
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"
        status: pass
  - id: D6
    description: "The --release-notes PATH mode requires the exact version, the absence sentence, the unsigned/not-notarized statement and an exact-version ledger link, and rejects wrong-version, missing, comment-only and contrary notes."
    requirement: SHIP-10
    human_judgment: false
    verification:
      - kind: integration
        ref: "python3 -I tests/scripts/verify-v02-adoption.py --self-test docs"
        status: pass
duration: "about 35 min"
completed: "2026-10-20"
status: complete
---

# Phase 15 Plan 04: Adoption, Limitation and Notice Claims Summary

**A stdlib checker turns the v0.2.0 adoption, notice and release-note claims into prose, symbol, digest and release-note contracts with 39 real-CLI negative controls, and the guides now state only shipped behavior and its limits.**

## Performance

- **Duration:** about 35 minutes (start time was not recorded)
- **Completed:** 2026-10-20
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Expanded `tests/scripts/verify-v02-adoption.py` `--check docs` to 370 checks: required claim phrases over README, native integration, cartridge/save, game acceptance, the v0.2.0 ledger and the CGB profile, audio, preview and release guides; claim markers parsed by the production CGB claim parser; and public-symbol resolution (106 distinct names) against `include/gabbaboy/gabbaboy.h`. HTML comments and fenced code are removed before phrase checks, so a comment-only occurrence is rejected.
- Added an adopter summary to `docs/cgb-profile.md` (models, header-selected mode, bootless start, raw RGB555 with no colour correction, digital PCM, `$FF` in compatibility mode) with the explicit limits: no CGB game-level evidence, physical CGB-E UNKNOWN/POLICY, no mode-3 timing claim, no physical or perceptual qualification. Audio, preview and README now carry matching limits and link the v0.2.0 ledger.
- Rewrote the relevant parts of `docs/release.md`: GitHub generated source archives retain the admitted licensed fixtures and notices while installed and downloaded product packages stay fixture-free; the installed-prefix check and downloaded-asset check are separate proofs; `support-ledger.json`, `release-performance-receipt.json` and `v02-fuzz-receipt.json` are described as exact-tag evidence with no fuzz result claimed; macOS output stays unsigned and not notarized; the page makes no publication claim for v0.2.0.
- Reconciled `THIRD_PARTY_NOTICES.md` with all 19 admitted fixture directories. Twelve directories were previously unlisted (CGB guests, MBC continuation/banking guests, the v0.1.2 save-envelope vectors, DMG and CGB Mooneye ROMs and SameSuite under X11). A digest table is recomputed from committed manifest and LICENSE bytes; the existing inline digests are also verified against bytes. No Rebound attribution was added.
- Added `--release-notes PATH` for the later version PR. It is exercised here only against a generated valid fixture and seven contrary or missing-note mutations; the real final notes do not exist yet and release-please history was not pre-written.

## Task Commits

1. **Task 1 (tracer): model, audio and preview adoption claims** - `7efeb2a` (`feat`)
2. **Task 2: notices, release guide and release-note mode** - `338edc1` (`feat`)

## Verification Evidence

- `python3 -I tests/scripts/verify-v02-adoption.py --check docs` passed: 370 checks, positive success.
- `python3 -I tests/scripts/verify-v02-adoption.py --self-test docs` passed: 39 negative controls, 39 rejected, each for its expected reason, plus positive re-runs after restoring bytes.
- `--check game` (14 checks) and `--self-test game` (2 of 2 controls) still pass.
- Related existing checks after the doc edits: `verify-cgb-corpus-claims.py` (static and `--self-test`, 15 controls), `verify-cgb-hdma-claims.py` (8 surfaces), `verify-support-ledger.py --self-test`, `verify-libbet-admission.py --check-notices` and `--self-test`, and CTest `cgb_tables*` and the 21 `libbet` tests all passed.
- A real `--release-notes` run accepted a valid note and rejected a note without the absence sentence with `release-notes-absence-missing`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Production claim regex misread negated prose**
- **Found during:** Task 1
- **Issue:** `UNQUALIFIED_CLAIM` from the production parser matched "no general game compatibility is claimed" in the native integration guide.
- **Fix:** Added a negation guard (`no`/`not`/`never` immediately before the match) in the adoption checker; the production script is unchanged.
- **Files modified:** `tests/scripts/verify-v02-adoption.py`
- **Commit:** `7efeb2a`

**2. [Rule 3 - Blocking] Ledger exceeds the shared document bound**
- **Found during:** Task 1
- **Issue:** `docs/support/v0.2.0.md` embeds the historical receipt and is about 3 MB, above the 1 MiB document bound.
- **Fix:** A per-document bound of 8 MiB for the ledger only; other surfaces keep 1 MiB.
- **Commit:** `7efeb2a`

**3. [Rule 1 - Bug] Self-test control hit an earlier check**
- **Found during:** Task 1
- **Issue:** The undeclared-symbol control replaced a symbol that was also a required phrase, so it failed for a different reason; the control harness reported that honestly.
- **Fix:** Mutated `gbb_run_ex` instead so the intended symbol-resolution rejection is reached.
- **Commit:** `7efeb2a`

**4. [Rule 2 - Missing critical] README and preview still pointed at the v0.1.0 ledger**
- **Found during:** Task 1
- **Issue:** README (not in the plan's file list) and the preview guide linked only the v0.1.0 ledger, so the v0.2.0 scope was unreachable from the adopter entry points.
- **Fix:** Linked the v0.2.0 ledger and kept v0.1.0 as the earlier record.
- **Files modified:** `README.md`, `docs/preview.md`
- **Commit:** `7efeb2a`

**Total deviations:** 4 auto-fixed (2 Rule 1, 1 Rule 2, 1 Rule 3). Impact: scope unchanged; one extra file (README.md) edited.

## TDD Gate Compliance

The checker expansion was written first and run before the documents were edited. The first run exited 1 with `support-ledger-link-missing:README.md`, and a per-phrase diagnostic listed 21 missing release, profile, audio and preview claims. Task 2 repeated this: `source-archive-distinction-missing:docs/release.md` and then `...:THIRD_PARTY_NOTICES.md` before the guide and notice edits. Each failure loaded the real documents and rejected an intended missing claim, with no parser or setup error. Separate RED and GREEN commits were not made; each task was committed once after its GREEN run.

## Known Limits and Pending Evidence

- The checker is not yet registered in CTest or CI; Plan 15-09 names `v02_adoption_docs` and `v02_adoption_docs_controls` for that registration. It has been run directly only.
- No v0.2.0 release, tag or publication exists. The documents make no publication claim.
- Plan 15-06's fuzz campaign is parked and failed at `tests/fuzz_core.c:789`; no document claims a campaign pass, and `v02-fuzz-receipt.json` is described only as a release requirement.
- Physical CGB-E remains UNKNOWN/POLICY and no CGB game-level evidence exists. The paired v0.1.0 DMG measurement (23.96% slowdown, about 3.55% approximate 95% margin) is disclosed in the performance receipt and was not restated in prose here. macOS artifacts remain unsigned and not notarized.
- Source-archive contents were not extracted or inspected here; that archive-content proof belongs to Plan 15-07.

## Known Stubs

None.

## Threat Flags

None. T-15-07 and T-15-08 are mitigated by the production-entry controls above; no network surface, install or dependency was added (T-15-SC unchanged).

## Next Phase Readiness

Plan 15-04 is complete. Plan 15-07 (source archive and product packaging) is ready, and Plan 15-09 should register the two adoption CTest names. Phase 15 is not complete; stop at Phase 15 and do not advance to another phase.

## Self-Check: PASSED

- Commits `7efeb2a` and `338edc1` are on the branch.
- All six planned deliverables plus README.md exist and were committed.
- Both task verification commands pass on the committed bytes.
