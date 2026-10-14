#!/usr/bin/env python3
"""Check Phase 12's automated UAT closure, without asking the owner to repeat it.

This phase-boundary check stays local: recurring SUMMARY schema, behavioral,
mutation, consumer and package checks already run in CI. It does not manufacture
fresh behavioral evidence from report text; 12-UAT.md names the actual runs.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path('.planning/phases/GB-12-cgb-double-speed')
spec = importlib.util.spec_from_file_location(
    'coverage_rules', ROOT / 'tests/scripts/verify-summary-coverage.py')
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)


def check(root):
    directory = root / PHASE
    text = (directory / '12-UAT.md').read_text(encoding='utf-8')
    frontmatter = '\n'.join(rules.frontmatter_lines(text))
    assert re.search(r'^status: complete$', frontmatter, re.M), 'session incomplete'
    assert re.search(r'^phase: GB-12-cgb-double-speed$', frontmatter, re.M), 'wrong phase'
    assert text.split('## Current Test\n', 1)[1].split('## Tests\n', 1)[0].strip() == '[testing complete]', 'pending checkpoint'
    expected = {}
    summaries = sorted(directory.glob('*-SUMMARY.md'))
    assert len(summaries) == 19, 'missing plan summary'
    for summary in summaries:
        content = summary.read_text(encoding='utf-8')
        _, errors = rules.check_text(content)
        assert not errors, f'{summary.name}: {errors}'
        assert summary.name in frontmatter, 'missing source summary'
        for entry in rules.coverage_entries(content):
            assert entry['human_judgment'] is False, 'automatable deliverable routed to human'
            # The installed classifier preserves escaped interior quotes. The
            # older CI schema checker only needs nonempty refs and truncates
            # those values, so compare the full original scalar here.
            block = re.search(r'^  - id: ' + re.escape(entry['id']) +
                              r'\n(.*?)(?=^  - id: |^\S|\Z)', content, re.M | re.S)
            assert block, 'missing coverage block'
            refs = re.findall(r'^\s+ref: (.+)$', block[1], re.M)
            entry['uat_refs'] = [v[1:-1] if v[:1] in ('"', "'") and v[-1:] == v[:1] else v for v in refs]
            expected[(summary.name, entry['id'])] = entry
    tests = text.split('## Tests\n', 1)[1].split('## Summary\n', 1)[0]
    blocks = re.split(r'^### \d+\. ', tests, flags=re.M)[1:]
    seen = set()
    for block in blocks:
        def field(name):
            matches = re.findall(r'^' + name + r': (.+)$', block, re.M)
            assert len(matches) == 1, f'missing or duplicate {name}'
            return matches[0]
        key = (field('summary_file'), field('coverage_id'))
        assert key in expected and key not in seen, 'missing, unknown or duplicate coverage'
        seen.add(key)
        entry = expected[key]
        assert field('result') == 'pass' and field('source') == 'automated', 'not an automated pass'
        assert json.loads(field('expected')) == entry['description'], 'changed acceptance criterion'
        assert json.loads(field('evidence')) == entry['uat_refs'], 'weaker evidence'
    assert seen == set(expected) and len(seen) == 73, 'incomplete coverage'
    summary = text.split('## Summary\n', 1)[1].split('## Gaps\n', 1)[0]
    for name, value in [('total', 73), ('passed', 73), ('issues', 0), ('pending', 0), ('skipped', 0), ('blocked', 0)]:
        assert re.search(r'^' + name + ': ' + str(value) + r'$', summary, re.M), 'incorrect totals'
    assert text.split('## Gaps\n', 1)[1].strip() == '[none]', 'unresolved gap'
    return len(seen)


def self_test(root):
    assert check(root) == 73
    mutations = {
        'missing-row': lambda t: re.sub(r'^### 1\..*?(?=^### 2\.)', '', t, count=1, flags=re.M | re.S),
        'manual-source': lambda t: t.replace('source: automated', 'source: human', 1),
        'pending-result': lambda t: t.replace('result: pass', 'result: [pending]', 1),
        'wrong-coverage': lambda t: t.replace('coverage_id: D1', 'coverage_id: missing', 1),
        'missing-evidence': lambda t: re.sub(r'^evidence: .+$', 'evidence: []', t, count=1, flags=re.M),
        'changed-criterion': lambda t: re.sub(r'^expected: .+$', 'expected: "weaker"', t, count=1, flags=re.M),
        'false-complete': lambda t: t.replace('status: complete', 'status: testing', 1),
        'stale-count': lambda t: t.replace('total: 73', 'total: 72', 1),
        'open-gap': lambda t: t.replace('## Gaps\n\n[none]', '## Gaps\n\n- status: failed'),
    }
    for label, mutate in mutations.items():
        with tempfile.TemporaryDirectory(prefix='gbb-uat-closure-') as name:
            scratch = Path(name)
            shutil.copytree(root / PHASE, scratch / PHASE)
            path = scratch / PHASE / '12-UAT.md'
            original = path.read_text(encoding='utf-8')
            changed = mutate(original)
            assert changed != original, f'{label}: inactive mutation'
            path.write_text(changed, encoding='utf-8')
            try:
                check(scratch)
            except AssertionError:
                continue
            raise AssertionError(f'{label}: accepted weakened closure')
    print(f'uat-closure self-test pass controls={len(mutations)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test(ROOT)
    else:
        print(f'uat-closure pass automated={check(ROOT)} human=0 gaps=0')
