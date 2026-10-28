#!/usr/bin/env python3
"""Check historical Phase 8 documentation and handoff at its immutable boundary.

This validates recorded receipts, not the current state of GitHub or later public
support. Live routes and HEAD ancestry deliberately have no role in this check.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

# The boundary is a durable annotated tag on the Phase 8 verification commit (D-12). It is resolved once to a
# commit id and never falls back to a literal SHA, so an unreadable tag fails closed. A tag is mutable, so the commit
# it must peel to is also pinned here (WR-02): a retargeted tag fails with its own message before any clause is read,
# and the clauses themselves are read from the resolved commit, never from the working tree or later history.
DEFAULT_BOUNDARY = 'historical/phase-08-boundary'
EXPECTED_BOUNDARY = '96d5eec977bee99a0629499b89c737415e24184c'
PHASE = '.planning/phases/GB-08-cartridge-seam-mbc5-and-mbc2/'
# Each fragment represents a required claim or an explicit limit in the original
# boundary. Normalize whitespace so wrapping alone does not weaken the contract.
CONTRACT = {
 'docs/cartridge-and-saves.md': [
  '| `$05` | MBC2', '| `$06` | MBC2', '| `$19` | MBC5', '| `$1E` | MBC5',
  'at most 8 MiB of ROM plus 128 KiB of cartridge RAM',
  'every other type, including a type byte the loader does not recognize, keeps the earlier 2 MiB ceiling',
  'Bank 0 is selectable', 'by address bit 8', 'exactly 512 bytes',
  'Packed 256-byte MBC2 saves', 'normalises each byte',
  'gbb_rumble_state(instance, &on, &changes)', 'saturates at `UINT64_MAX`',
  'The player and the headless runner do not drive any haptics',
  'Player battery persistence applies only to MBC1 type `$03`',
  "The player's own read bound stays 2 MiB", 'mbc2-mbc5-evidence.md'],
 'docs/native-integration.md': ['supported lengths up to 8 MiB for MBC5 types',
  'up to 2 MiB for', '128 KiB of RAM', 'gbb_rumble_state', 'GBB_NO_RUMBLE'],
 'README.md': ['core supports ROM-only, MBC1, MBC2 and MBC5 cartridges',
  'MBC2 and MBC5 battery cartridges run there without saving progress',
  'no general game compatibility or physical-hardware accuracy claim'],
 'docs/preview.md': ["player's own 2 MiB file-read bound", 'Battery persistence applies only to MBC1 type `$03`',
  'battery cartridges run without saving', 'the player produces no haptics'],
 'docs/mbc2-mbc5-evidence.md': ['CART-01', 'CART-02', 'CART-03',
  'cells=86016 differences=0', 'cells=85344 differences=0', 'cells=83328 differences=0',
  '4c7a57ff3d50d228', 'not game compatibility', 'not hardware qualification',
  'MBC2A caveat', 'author-attested hardware results',
  'original software fixture plus a synthetic oracle, not hardware evidence',
  '38151282870', 'mbc2=7/7 mbc5=8/8', 'bank at or above 256',
  'mbc5_ninth_bit_mutant_bank_1ff', 'mbc5_ninth_bit_mutant_control_below_100',
  'They are not installed and not packaged', 'automatically generated source archives'],
 'docs/support/unreleased.md': ['Cartridge breadth (Phase 8)', 'mbc2 (7 of 7)', 'mbc5 (8 of 8)',
  '31510e12eea6286d36eea060a6adde755e1067aa', 'not game compatibility',
  'without saving progress', 'about 17 MiB', 'mbc2-mbc5-evidence.md'],
 '.github/workflows/preview.yml': ['standard MBC1, MBC2 and MBC5', 'player battery persistence: MBC1 type \\$03 only'],
 '.planning/research/INDEX.md': ['mbc2-mbc5-evidence.md', '08-RESEARCH.md'],
 '.planning/context/FUTURE-MILESTONES.md': ['13 further ROMs', 'multicart_rom_8Mb',
  'cartridge.c', 'Six build sites', 'read8', 'A/B evidence', 'Generalised suite verifier',
  'Host haptics', 'Packed 256-byte MBC2'],
 'fixtures/mooneye-mbc/SOURCES.md': ['31510e12eea6286d36eea060a6adde755e1067aa', 'LICENSE', 'WLA'],
 'fixtures/mooneye-mbc/ELIGIBILITY.md': ['DMG-CPU-B', 'MBC2A'],
 'THIRD_PARTY_NOTICES.md': ['mooneye-mbc'],
 PHASE+'08-01-SUMMARY.md': ['cells=86016 lines=213114', 'old_sha256=d171c90db94218aa0378d457578657bd9e8bbdf94745f1a83f91f717307800b6', 'new_sha256=d171c90db94218aa0378d457578657bd9e8bbdf94745f1a83f91f717307800b6', 'differences=0', '--exclude-types'],
 PHASE+'differential/run-differential.sh': ['--exclude-types'],
 PHASE+'08-07-SUMMARY.md': ['38151282870', 'rom_64Mb', 'mutant'],
 PHASE+'08-08-SUMMARY.md': ['RGBDS 1.0.1', 'mbc5_bank_1ff', 'fixture-repro'],
 PHASE+'08-10-SUMMARY.md': ['a3f27f71c10838e372f27d8c2fcf0070123b0919',
  '38155767928', '38155768038', 'cea55b28e32f320b14e47d921545e410ab4c5711',
  '38157465103', '38157465090', 'native-windows-x64 success',
  'linux-asan-ubsan success', 'required-native success', 'privacy check clean',
  'zero `/(Users|home)/<name>/` matches', 'isDraft=false state=OPEN',
  'no open issues', 'Not merged'],
 '.planning/STATE.md': ['Phase 8 execution complete', '/gsd-verify-work 8', 'awaiting verification'],
 '.planning/.continue-here.md': ['Phase 8 execution complete', 'open, not merged',
  '**Next command:** `/gsd-verify-work 8`', 'nothing advances automatically'],
}

FROZEN = ('cmake/VerifyMooneye.cmake', 'tests/scripts/reproduce-mooneye.sh') + tuple(
    'fixtures/mooneye/'+name for name in (
        'ELIGIBILITY.md', 'FONT-LICENSE.txt', 'LICENSE.txt', 'SOURCES.md',
        'candidate-digests.json', 'daa.gb', 'font-source.c', 'headless-report.patch',
        'manifest.json', 'pre-admission-baseline.json', 'tim00.gb', 'tim00_div_trigger.gb')) + tuple(
    'tests/baseline/'+name for name in ('CHANGES.md', 'dmg-cpu-b-v1.txt',
        'selftest/CHANGES.md', 'selftest/junit.xml', 'selftest/ledger.txt', 'selftest/observed.txt'))
OLD = '5673bed'

def resolve_boundary(rev: str, repo: str | None = None) -> str | None:
    """Return the commit id for rev, or None when rev is empty, option-shaped or not a readable commit."""
    if not rev or rev.startswith('-'):
        return None
    command = ['git'] + (['-C', repo] if repo else []) + ['rev-parse', '--verify', '--quiet', f'{rev}^{{commit}}']
    result = subprocess.run(command, capture_output=True, text=True)
    sha = result.stdout.strip()
    if result.returncode or not re.fullmatch(r'[0-9a-f]{40}', sha):
        return None
    return sha

def boundary_identity_error(rev: str, sha: str, expected: str = EXPECTED_BOUNDARY) -> str | None:
    """The named tag must peel to the pinned commit. Any other revision is an explicit override (the wrong-boundary
    controls use one), judged by its clauses alone."""
    if rev == DEFAULT_BOUNDARY and sha != expected:
        return f'boundary tag {rev} was retargeted: it resolves to {sha}, not {expected}'
    return None

def normalized(text: str) -> str:
    return ' '.join(text.split())

def verify(files: dict[str, str]) -> list[str]:
    errors = []
    for path, required in CONTRACT.items():
        source = normalized(files[path])
        for fragment in required:
            if normalized(fragment) not in source:
                errors.append(f'{path}: missing historical clause {fragment!r}')
    try:
        config = json.loads(files['.planning/config.json'])
    except ValueError:
        config = {}
        errors.append('missing historical clause: config.json is absent or unparsable at the boundary')
    for name in ('auto_advance', '_auto_chain_active'):
        if config.get('workflow', {}).get(name) is not False:
            errors.append(f'historical {name} must be false')
    for number in range(49, 63):
        rows = [row for row in files['.planning/context/DECISIONS.md'].splitlines()
                if row.startswith(f'| D-{number:03d} |')]
        if len(rows) != 1 or '**Adopted**' not in rows[0]:
            errors.append(f'missing adopted D-{number:03d}')
    for number in range(1, 7):
        if f'GB-CART-{number:03d}' not in files['.planning/context/LESSONS.md']:
            errors.append(f'missing lesson GB-CART-{number:03d}')
    old_inventory = set(files['old:tests/expected-tests.txt'].splitlines())
    new_inventory = set(files['tests/expected-tests.txt'].splitlines())
    if not old_inventory <= new_inventory or not new_inventory - old_inventory:
        errors.append('historical expected inventory must add cases and remove none')
    for path in FROZEN:
        if files['old:'+path] != files[path]:
            errors.append(f'historical frozen path changed: {path}')
    core = files['src/core/gabbaboy.c']
    for anchor in ('joypad_select & 0x20u) ==', '& 1u) << 8'):
        if core.count(anchor) != 1:
            errors.append(f'historical anchor count is not one: {anchor}')
    if 'cartridge_type == 0x03u' in core:
        errors.append('historical scattered battery-type literal returned')
    # These original public docs must not contain local-user paths or personal
    # emails. Upstream licence notices are deliberately outside this scan.
    for path in CONTRACT:
        if path.startswith(('docs/', 'README', '.github/')):
            if re.search(r'/(?:Users|home)/[A-Za-z0-9_.-]+/|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', files[path]):
                errors.append(f'private identifier in historical public artifact: {path}')
    return errors

def boundary_identity_self_test(boundary: str) -> int:
    """Retarget a disposable annotated and a disposable lightweight tag and require the pinned-commit rejection; the
    repository's own tag is never touched. Returns the number of controls that held."""
    controls = 0
    if boundary_identity_error(DEFAULT_BOUNDARY, boundary) is not None and boundary == EXPECTED_BOUNDARY:
        raise SystemExit('phase8-closure-contract FAIL boundary identity rejected the pinned commit')
    if boundary_identity_error(DEFAULT_BOUNDARY, '0' * 40) is None:
        raise SystemExit('phase8-closure-contract FAIL boundary identity accepted another commit for the tag')
    if boundary_identity_error('v0.2.0', '0' * 40) is not None:
        raise SystemExit('phase8-closure-contract FAIL boundary identity rejected an explicit override')
    controls += 3
    with tempfile.TemporaryDirectory(prefix='gbb-phase8-tag-') as tmp:
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'SYSTEMROOT', 'TMPDIR', 'TEMP', 'TMP')}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_AUTHOR_NAME='fixture',
                   GIT_AUTHOR_EMAIL='fixture@example.invalid', GIT_COMMITTER_NAME='fixture',
                   GIT_COMMITTER_EMAIL='fixture@example.invalid')

        def git(*args: str) -> str:
            return subprocess.run(['git', '-C', tmp, *args], capture_output=True, text=True, check=True, env=env).stdout.strip()

        git('init', '-q')
        git('commit', '-q', '--allow-empty', '-m', 'boundary')
        pinned = git('rev-parse', 'HEAD')
        git('commit', '-q', '--allow-empty', '-m', 'other')
        other = git('rev-parse', 'HEAD')
        git('tag', '-a', '-m', 'boundary', DEFAULT_BOUNDARY, pinned)
        resolved = resolve_boundary(DEFAULT_BOUNDARY, tmp)
        if resolved != pinned or boundary_identity_error(DEFAULT_BOUNDARY, resolved, pinned) is not None:
            raise SystemExit('phase8-closure-contract FAIL a disposable annotated tag at the pinned commit was rejected')
        git('tag', '-f', '-a', '-m', 'retargeted', DEFAULT_BOUNDARY, other)
        # The command line the CTest runs, from inside the disposable repository: the retargeted tag stops it with its own
        # message, before any clause is judged.
        run = subprocess.run([sys.executable, '-I', os.path.abspath(__file__)], cwd=tmp, capture_output=True, text=True, env=env)
        if run.returncode != 1 or 'retargeted' not in run.stderr or 'missing historical clause' in run.stderr:
            raise SystemExit(f'phase8-closure-contract FAIL the command did not stop on a retargeted tag: {run.returncode} {run.stderr[:200]}')
        controls += 1
        for label in ('annotated', 'lightweight'):
            resolved = resolve_boundary(DEFAULT_BOUNDARY, tmp)
            error = boundary_identity_error(DEFAULT_BOUNDARY, resolved or '', pinned)
            if resolved != other or not error or 'retargeted' not in error:
                raise SystemExit(f'phase8-closure-contract FAIL a retargeted {label} tag was not rejected')
            git('tag', '-f', DEFAULT_BOUNDARY, other)
            controls += 1
        git('tag', '-d', DEFAULT_BOUNDARY)
        if resolve_boundary(DEFAULT_BOUNDARY, tmp) is not None:
            raise SystemExit('phase8-closure-contract FAIL a deleted tag still resolved')
        controls += 2
    return controls

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--boundary', default=DEFAULT_BOUNDARY,
                        help='revision of the Phase 8 verification commit (default: %(default)s)')
    args = parser.parse_args()
    boundary = resolve_boundary(args.boundary)
    if boundary is None:
        print(f'phase8-closure-contract FAIL: boundary unreadable: {args.boundary}', file=sys.stderr)
        return 1
    retargeted = boundary_identity_error(args.boundary, boundary)
    if retargeted:
        print(f'phase8-closure-contract FAIL: {retargeted}', file=sys.stderr)
        return 1
    paths = list(CONTRACT) + ['.planning/config.json', '.planning/context/DECISIONS.md',
                              '.planning/context/LESSONS.md', 'src/core/gabbaboy.c', 'tests/expected-tests.txt'] + list(FROZEN) + ['old:'+p for p in (*FROZEN, 'tests/expected-tests.txt')]
    files = {}
    for path in paths:
        ref = f'{OLD}:{path[4:]}' if path.startswith('old:') else f'{boundary}:{path}'
        result = subprocess.run(['git', 'show', ref], capture_output=True)
        if result.returncode and path.startswith('old:'):
            print(f'phase8-closure-contract FAIL cannot read {path}: {result.stderr.strip()}', file=sys.stderr)
            return 1
        # A path absent at a readable but wrong boundary reads as empty, so the failure is a clause miss
        # (missing historical clause), distinct from an unreadable revision, which exited above.
        files[path] = '' if result.returncode else (
            result.stdout.hex() if path.endswith('.gb') else result.stdout.decode('utf-8'))
    errors = verify(files)
    if errors:
        print('\n'.join('phase8-closure-contract FAIL '+e for e in errors), file=sys.stderr)
        return 1
    controls = 0
    if args.self_test:
        # An unreadable boundary is its own failure class: empty, option-shaped and missing revisions all fail closed.
        for bad in ('', '--help', 'refs/tags/does-not-exist-phase8'):
            if resolve_boundary(bad) is not None:
                print(f'phase8-closure-contract FAIL ineffective unreadable-boundary control {bad!r}', file=sys.stderr)
                return 1
            controls += 1
        controls += boundary_identity_self_test(boundary)
        # Every clause must independently matter: remove one at a time without
        # fetching or mutating HEAD, the working tree or a remote service.
        for path, fragments in CONTRACT.items():
            for fragment in fragments:
                mutant = dict(files)
                text = normalized(files[path])
                mutant[path] = text.replace(normalized(fragment), '<removed>')
                if mutant[path] == text or not verify(mutant):
                    print(f'phase8-closure-contract FAIL ineffective control {path}: {fragment}', file=sys.stderr)
                    return 1
                controls += 1
        for path in FROZEN:
            mutant = dict(files); mutant[path] += '\nchanged'
            if not verify(mutant):
                return 1
            controls += 1
        mutant = dict(files)
        mutant['tests/expected-tests.txt'] = ''
        if not verify(mutant):
            return 1
        controls += 1
        for flag in ('auto_advance', '_auto_chain_active'):
            mutant = dict(files)
            config = json.loads(files['.planning/config.json']); config['workflow'][flag] = True
            mutant['.planning/config.json'] = json.dumps(config)
            if not verify(mutant):
                return 1
            controls += 1
        for number in range(49, 63):
            mutant = dict(files)
            path = '.planning/context/DECISIONS.md'
            mutant[path] = '\n'.join(row for row in files[path].splitlines()
                                      if not row.startswith(f'| D-{number:03d} |'))
            if not verify(mutant):
                return 1
            controls += 1
        for number in range(1, 7):
            mutant = dict(files); path = '.planning/context/LESSONS.md'
            mutant[path] = files[path].replace(f'GB-CART-{number:03d}', 'removed-lesson')
            if not verify(mutant):
                return 1
            controls += 1
        for anchor in ('joypad_select & 0x20u) ==', '& 1u) << 8'):
            for replacement in ('', anchor + anchor):
                mutant = dict(files); path = 'src/core/gabbaboy.c'
                mutant[path] = files[path].replace(anchor, replacement)
                if not verify(mutant):
                    return 1
                controls += 1
        for path, addition in [('docs/preview.md', '/home/private-user/'),
                               ('README.md', 'private-user@example.invalid')]:
            mutant = dict(files); mutant[path] += '\n'+addition
            if not verify(mutant):
                return 1
            controls += 1
    print(f'phase8-closure-contract PASS boundary={boundary} files={len(files)} rejected_controls={controls}; historical receipts only, no live CI/route qualification')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
