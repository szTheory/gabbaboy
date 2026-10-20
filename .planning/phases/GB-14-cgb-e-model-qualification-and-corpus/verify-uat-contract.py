#!/usr/bin/env python3
"""Check Phase 14's automated UAT closure, without asking the owner to repeat it.

This phase-boundary check stays local: recurring SUMMARY schema, behavioral,
mutation, consumer and package checks already run in CI. It does not manufacture
fresh behavioral evidence from report text; 14-UAT.md names the actual runs.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path('.planning/phases/GB-14-cgb-e-model-qualification-and-corpus')
spec = importlib.util.spec_from_file_location(
    'coverage_rules', ROOT / 'tests/scripts/verify-summary-coverage.py')
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)


def check(root):
    directory = root / PHASE
    text = (directory / '14-UAT.md').read_text(encoding='utf-8')
    frontmatter = '\n'.join(rules.frontmatter_lines(text))
    assert re.search(r'^status: complete$', frontmatter, re.M), 'session incomplete'
    assert re.search(r'^phase: GB-14-cgb-e-model-qualification-and-corpus$', frontmatter, re.M), 'wrong phase'
    assert text.split('## Current Test\n', 1)[1].split('## Tests\n', 1)[0].strip() == '[testing complete]', 'pending checkpoint'
    expected = {}
    summaries = sorted(directory.glob('*-SUMMARY.md'))
    assert len(summaries) == 13, 'missing plan summary'
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
    headings = re.findall(r'^#{1,6} .+$', tests, re.M)
    numbers = [re.match(r'^### (\d+)\. ', heading) for heading in headings]
    assert all(numbers) and [int(match[1]) for match in numbers] == list(range(1, 50)), 'unparsed or misnumbered test heading'
    prelude, *blocks = re.split(r'^### \d+\. ', tests, flags=re.M)
    assert not prelude.strip(), 'unparsed test prelude'
    seen = set()
    for block in blocks:
        allowed = {'expected', 'result', 'source', 'summary_file', 'coverage_id', 'evidence'}
        for line in block.splitlines()[1:]:
            assert not line.strip() or line.partition(':')[0] in allowed, 'unparsed test content'
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
    assert seen == set(expected) and len(seen) == 49, 'incomplete coverage'
    summary = text.split('## Summary\n', 1)[1].split('## Gaps\n', 1)[0]
    for name, value in [('total', 49), ('passed', 49), ('issues', 0), ('pending', 0), ('skipped', 0), ('blocked', 0)]:
        assert re.search(r'^' + name + ': ' + str(value) + r'$', summary, re.M), 'incorrect totals'
    assert text.split('## Gaps\n', 1)[1].strip() == '[none]', 'unresolved gap'
    return len(seen)


# The handoff is a point-in-time record: read it as merged with Phase 14 (PR #71),
# not from the live tree, which later phases legitimately advance.
HANDOFF_COMMIT = 'c771b1b9c143d7589f8bb40c163c2e9f89ca1168'
PHASE_HEAD = '8c09f9697aabc96424280aa14544ba68ff3f2fd4'


def commit_window(content):
    def value(pattern):
        match = re.search(pattern, content, re.M)
        assert match, 'missing bounded commit field'
        return match[1]
    before = value(r'^plan_head_before: ([0-9a-f]{40})$')
    after = value(r'^plan_head_after: ([0-9a-f]{40})$')
    claimed = int(value(r'^commits: (\d+)$') if re.search(r'^commits:', content, re.M)
                  else value(r'^  commits: (\d+)$'))
    # Squash merges leave plan commits only on the phase branch, so bound the window
    # by the merged PR #71 head rather than the current HEAD.
    for left, right in ((before, after), (after, PHASE_HEAD)):
        result = subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', left, right],
                                capture_output=True, timeout=10)
        assert result.returncode == 0, 'unreachable commit window'
    result = subprocess.run(['git', '-C', str(ROOT), 'rev-list', '--count', before + '..' + after],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0 and int(result.stdout) == claimed, 'commit claim mismatch'
    return claimed




def boundary_text(root, path):
    return subprocess.run(['git', '-C', str(root), 'show', f'{HANDOFF_COMMIT}:{path}'],
                          check=True, capture_output=True, text=True).stdout


def handoff_values(state, continuation, project, config):
    # Bound the live state and overview: earlier phase receipts remain historical.
    live = state.split('### Historical Phase 13 handoff', 1)[0]
    live += state.split('## Session Continuity', 1)[-1]
    overview = project.split('## Current State', 1)[1].split('\n## ', 1)[0]
    for text in (live, continuation, overview):
        normalized = text.replace('**', '').replace(' is complete', ' complete')
        assert 'Phase 14 automated UAT complete' in normalized or (
            'Phase 14 — CGB-E Model Qualification and Corpus, automated UAT complete' in normalized
        ), 'incorrect completed stage'
        assert 'remains unstarted' in normalized and 'Phase 15' in normalized, 'lost phase pause'
        commands = re.findall(r'/gsd-[a-z-]+ \d+', text)
        assert commands and all(c == '/gsd-discuss-phase 15' for c in commands), 'stale continuation route'
        assert not re.search(r'execution remains unstarted|planning is complete|paused before automated UAT',
                             text, re.I), 'contradictory completed stage'
    for key in ('auto_advance', '_auto_chain_active'):
        assert config['workflow'][key] is False, 'automatic phase advancement enabled'



def projection_values(data):
    assert data['next']['command'] == '/gsd-discuss-phase 15', 'stale machine-readable route'
    phases = {entry['number']: entry['status'] for entry in data['phases']}
    assert phases.get('14') == 'complete' and phases.get('15') == 'pending', 'incorrect machine phase pause'


def check_handoff(root):
    projection_values(json.loads(boundary_text(root, '.planning/state.json')))
    handoff_values(boundary_text(root, '.planning/STATE.md'),
                   boundary_text(root, f'{PHASE}/continue.md'),
                   boundary_text(root, '.planning/PROJECT.md'),
                   json.loads(boundary_text(root, '.planning/config.json')))


def handoff_self_test(root):
    state = boundary_text(root, '.planning/STATE.md')
    continuation = boundary_text(root, f'{PHASE}/continue.md')
    project = boundary_text(root, '.planning/PROJECT.md')
    config = json.loads(boundary_text(root, '.planning/config.json'))
    handoff_values(state, continuation, project, config)
    controls = [
        (state.replace('/gsd-discuss-phase 15', '/gsd-verify-work 14'), continuation, project, config),
        (state, continuation.replace('/gsd-discuss-phase 15', '/gsd-execute-phase 15'), project, config),
        (state, continuation, project.replace('/gsd-discuss-phase 15', '/gsd-execute-phase 14'), config),
        (state, continuation.replace('automated UAT complete', 'planning complete'), project, config),
        (state, continuation, project.replace('automated UAT is complete', 'planning is complete'), config),
        (state, continuation.replace('remains unstarted', 'already started'), project, config),
    ]
    for key in ('auto_advance', '_auto_chain_active'):
        altered = json.loads(json.dumps(config))
        altered['workflow'][key] = True
        controls.append((state, continuation, project, altered))
    for args in controls:
        try:
            handoff_values(*args)
        except AssertionError:
            continue
        raise AssertionError('accepted stale handoff or automatic phase advance')
    projection = json.loads(boundary_text(root, '.planning/state.json'))
    projection_values(projection)
    for field in ('route', 'phase-pause'):
        altered = json.loads(json.dumps(projection))
        if field == 'route':
            altered['next']['command'] = '/gsd-verify-work 14'
        else:
            next(entry for entry in altered['phases'] if entry['number'] == '15')['status'] = 'complete'
        try:
            projection_values(altered)
        except AssertionError:
            continue
        raise AssertionError('accepted stale machine-readable state')
    print(f'uat-handoff self-test pass controls={len(controls) + 2}')


def commit_self_test(root):
    summaries = sorted((root / PHASE).glob('*-SUMMARY.md'))
    assert len(summaries) == 13
    for summary in summaries:
        commit_window(summary.read_text())
    content = summaries[0].read_text()
    for changed in (re.sub(r'^commits: 12$', 'commits: 999', content, count=1, flags=re.M),
                    re.sub(r'^plan_head_after: .+$', 'plan_head_after: ' + '0' * 40, content,
                           count=1, flags=re.M)):
        assert changed != content, 'inactive commit control'
        try:
            commit_window(changed)
        except AssertionError:
            continue
        raise AssertionError('accepted incorrect commit claim')
    print('uat-commits pass windows=13 controls=2 legacy-warnings=4')


def self_test(root):
    assert check(root) == 49
    mutations = {
        'missing-row': lambda t: re.sub(r'^### 1\..*?(?=^### 2\.)', '', t, count=1, flags=re.M | re.S),
        'manual-source': lambda t: t.replace('source: automated', 'source: human', 1),
        'pending-result': lambda t: t.replace('result: pass', 'result: [pending]', 1),
        'wrong-coverage': lambda t: t.replace('coverage_id: D1', 'coverage_id: missing', 1),
        'missing-evidence': lambda t: re.sub(r'^evidence: .+$', 'evidence: []', t, count=1, flags=re.M),
        'changed-criterion': lambda t: re.sub(r'^expected: .+$', 'expected: "weaker"', t, count=1, flags=re.M),
        'false-complete': lambda t: t.replace('status: complete', 'status: testing', 1),
        'stale-count': lambda t: t.replace('total: 49', 'total: 48', 1),
        'missing-source': lambda t: t.replace('14-01-SUMMARY.md, ', '', 1),
        'duplicate-row': lambda t: t.replace('## Summary\n', re.search(r'^### 1\..*?(?=^### 2\.)', t, re.M | re.S)[0] + '## Summary\n', 1),
        'wrong-phase': lambda t: t.replace('phase: GB-14-cgb-e-model-qualification-and-corpus', 'phase: GB-15-cgb-e-model-qualification-and-corpus', 1),
        'unnumbered-human-checkpoint': lambda t: t.replace('## Summary\n', '### Manual checkpoint\nresult: pending\nsource: human\n\n## Summary\n', 1),
        'extra-section': lambda t: t.replace('## Summary\n', '## Manual checks\n\n## Summary\n', 1),
        'unparsed-field': lambda t: t.replace('result: pass', 'manual_checkpoint: pending\nresult: pass', 1),
        'unparsed-prelude': lambda t: t.replace('## Tests\n', '## Tests\n\nManual checkpoint: pending\n', 1),
        'misnumbered-row': lambda t: t.replace('### 2. ', '### 99. ', 1),
        'open-gap': lambda t: t.replace('## Gaps\n\n[none]', '## Gaps\n\n- status: failed'),
    }
    for label, mutate in mutations.items():
        with tempfile.TemporaryDirectory(prefix='gbb-uat-closure-') as name:
            scratch = Path(name)
            shutil.copytree(root / PHASE, scratch / PHASE)
            path = scratch / PHASE / '14-UAT.md'
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
        handoff_self_test(ROOT)
        commit_self_test(ROOT)
    else:
        check_handoff(ROOT)
        for summary in sorted((ROOT / PHASE).glob('*-SUMMARY.md')):
            commit_window(summary.read_text())
        print(f'uat-closure pass automated={check(ROOT)} human=0 gaps=0 windows=13')
