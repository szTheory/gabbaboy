#!/usr/bin/env python3
"""Local metadata reconciliation check; reuses existing behavioral evidence."""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
TARGETS = {'CGB-05': (11, '11-15'), 'CGB-09': (11, '11-15'), 'CGB-07': (13, '13-12')}


def front(text):
    return text.split('---', 2)[1]


def claims(text):
    match = re.search(r'^requirements-completed:[ \t]*(\[[^\n]*\]|\n(?:[ \t]+- [^\n]+\n)+)', front(text), re.M)
    assert match, 'missing completion field'
    return re.findall(r'[A-Z]+-\d+', match[1])


def facts():
    req = (ROOT / '.planning/REQUIREMENTS.md').read_text()
    result = []
    for rid, phase, central in re.findall(r'^\| ([A-Z]+-\d+) \| Phase (\d+) \| (\w+) \|$', req, re.M):
        directory, = (ROOT / '.planning/phases').glob(f'GB-{int(phase):02d}-*')
        verification = (directory / f'{int(phase):02d}-VERIFICATION.md').read_text()
        owners = [p.stem.removesuffix('-SUMMARY') for p in directory.glob('*-SUMMARY.md') if rid in claims(p.read_text())]
        result.append(dict(id=rid, phase=int(phase), central=central, owners=owners,
                           checked=bool(re.search(r'^- \[x\] \*\*'+rid+r'\*\*:', req, re.M)),
                           passed=bool(re.search(r'^status: passed$', front(verification), re.M)),
                           satisfied=any('SATISFIED' in row for row in verification.splitlines() if re.match(r'^\| '+rid+r' \|', row))))
    return result


def check(rows):
    assert len(rows) == 28 and len({r['id'] for r in rows}) == 28
    for r in rows:
        assert r['central'] == 'Complete' and r['checked'] and r['passed'] and r['satisfied'] and r['owners'], r['id']
        if r['id'] in TARGETS:
            phase, owner = TARGETS[r['id']]
            assert r['phase'] == phase and owner in r['owners'], r['id']


def check_legacy_uat(text):
    assert re.search(r'^status: complete$', front(text), re.M)
    sections = re.findall(r'^### (\d+)\. .*?\n(.*?)(?=^### |^## Summary)', text, re.M | re.S)
    assert [int(n) for n, _ in sections] == list(range(1, 12))
    for _, body in sections:
        for field in ('result: pass', 'source: automated', 'coverage_id:', 'evidence:'):
            assert field in body
    for name, number in {'total':11, 'passed':11, 'issues':0, 'pending':0, 'skipped':0, 'blocked':0}.items():
        assert re.search(r'^'+name+': '+str(number)+r'$', text, re.M)


def rejected(fn):
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError('negative control accepted')


if __name__ == '__main__':
    runtime = Path(sys.argv[1]).resolve()
    identity = json.loads(subprocess.check_output(['node', str(runtime), 'runtime-identity', '--raw'], text=True))
    assert identity['packageName'] == '@opengsd/gsd-core'
    rows = facts()
    check(rows)
    for rid in TARGETS:
        for field, value in [('owners', []), ('satisfied', False), ('checked', False)]:
            mutant = copy.deepcopy(rows)
            next(r for r in mutant if r['id'] == rid)[field] = value
            rejected(lambda: check(mutant))
    directory, = (ROOT / '.planning/phases').glob('GB-11-*')
    uat = (directory / '11-UAT.md').read_text()
    check_legacy_uat(uat)
    rejected(lambda: check_legacy_uat(uat.replace('result: pass', 'result: pending', 1)))
    total = 0
    for summary in sorted(directory.glob('*-SUMMARY.md')):
        data = json.loads(subprocess.check_output(['node', str(runtime), 'uat', 'classify-coverage', '--summary', str(summary)], text=True))
        assert data['mode'] == 'coverage' and data['all_auto_covered'] and not data['present'] and not data['errors']
        total += data['total']
    assert total == 91
    config = json.loads((ROOT / '.planning/config.json').read_text())['workflow']
    assert config['auto_advance'] is False and config['_auto_chain_active'] is False
    print('reconciliation pass requirements=28/28 targets=3/3 legacy-uat=11/11 coverage=91/91 rejected=10 auto-flags=false')
