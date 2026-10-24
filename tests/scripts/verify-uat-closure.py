#!/usr/bin/env python3
"""Write or check a phase's automated UAT closure (D-069), for any phase.

--write builds {N}-UAT.md from the phase SUMMARY coverage blocks: every
deliverable becomes an automated pass that keeps its exact criterion and cited
evidence. It refuses when any deliverable still needs a human, and lists those,
so only real checkpoints reach the owner. The default mode checks an existing
closure; --self-test also proves that weakened copies are rejected.

Only the closure record is checked. Live routes and commit ancestry change after
the phase (later handoffs, squash merges), so verify-work reconciles them at the
boundary and the UAT prose records the result; asserting them here would turn
this check red for reasons that are not regressions.
"""

import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import subprocess
import tempfile

# Contract rules raise ClosureError rather than using assertion statements, because python -O strips
# assertions and would turn every check into a silent pass. Refuse optimized interpreters outright
# before importing or checking anything.
if not __debug__ or sys.flags.optimize:
    raise SystemExit('verify-uat-closure must not run with python -O')

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'coverage_rules', ROOT / 'tests/scripts/verify-summary-coverage.py')
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)



class ClosureError(Exception):
    """A UAT closure contract rule was violated."""


def need(condition, message):
    if not condition:
        raise ClosureError(message)


FIELDS = ('expected', 'result', 'source', 'summary_file', 'coverage_id', 'evidence')


def phase_number(directory):
    match = re.match(r'^[A-Z]+-(\d+(?:\.\d+)?)-', directory.name)
    need(match, f'unrecognized phase directory {directory.name}')
    return match[1]


def deliverables(directory, problems=None):
    """Return the summaries and (summary, id) -> entry for every coverage entry.

    Schema errors fail the check, or are collected into problems when given.
    """
    summaries = sorted(directory.glob('*-SUMMARY.md'))
    need(summaries, 'no plan summaries')
    expected = {}
    for summary in summaries:
        content = summary.read_text(encoding='utf-8')
        _, errors = rules.check_text(content)
        if problems is None:
            need(not errors, f'{summary.name}: {errors}')
        else:
            problems.extend(f'{summary.name}: schema {error}' for error in errors or [])
        for entry in rules.coverage_entries(content):
            # The schema checker truncates quoted refs, so read the full scalars here.
            # The schema also accepts a quoted id (15.1-18 quotes two), so match either form.
            block = re.search(r'^  - id: (["\']?)' + re.escape(entry['id']) +
                              r'\1\n(.*?)(?=^  - id: |^\S|\Z)', content, re.M | re.S)
            need(block, 'missing coverage block')
            refs = re.findall(r'^\s+ref: (.+)$', block[2], re.M)
            entry['uat_refs'] = [v[1:-1] if v[:1] in ('"', "'") and v[-1:] == v[:1] else v
                                 for v in refs]
            key = (summary.name, entry['id'])
            need(key not in expected, f'duplicate coverage id {key}')
            expected[key] = entry
    need(expected, 'no coverage entries')
    return summaries, expected


def human_needed(entry):
    if entry['human_judgment'] is not False:
        return 'human_judgment'
    if not entry['uat_refs']:
        return 'no_verification'
    if any(item.get('status') != 'pass' for item in entry.get('verification', [])):
        return 'verification_not_passing'
    return None


def write(directory, evidence):
    problems = []
    summaries, expected = deliverables(directory, problems)
    problems += [f'{summary}: {cid} needs a human checkpoint ({reason})'
                 for (summary, cid), entry in expected.items() if (reason := human_needed(entry))]
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        raise SystemExit('refusing to write an automated closure; resolve the items above')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    total = len(expected)
    out = ['---', 'status: complete', f'phase: {directory.name}',
           'source: ' + ', '.join(s.name for s in summaries), f'started: {now}', f'updated: {now}',
           '---', '', '## Automated Evidence', '', evidence.strip(), '',
           '## Current Test', '', '[testing complete]', '', '## Tests', '']
    for number, ((summary, cid), entry) in enumerate(expected.items(), 1):
        out += [f"### {number}. {entry['description']}", f"expected: {json.dumps(entry['description'])}",
                'result: pass', 'source: automated', f'summary_file: {summary}',
                f'coverage_id: {cid}', f"evidence: {json.dumps(entry['uat_refs'])}", '']
    out += ['## Summary', '', f'total: {total}', f'passed: {total}', 'issues: 0', 'pending: 0',
            'skipped: 0', 'blocked: 0', '', '## Gaps', '', '[none]', '']
    path = directory / f'{phase_number(directory)}-UAT.md'
    path.write_text('\n'.join(out), encoding='utf-8')
    return path, total


def check(directory):
    summaries, expected = deliverables(directory)
    total = len(expected)
    text = (directory / f'{phase_number(directory)}-UAT.md').read_text(encoding='utf-8')
    frontmatter = '\n'.join(rules.frontmatter_lines(text))
    need(re.search(r'^status: complete$', frontmatter, re.M), 'session incomplete')
    need(re.search(r'^phase: ' + re.escape(directory.name) + '$', frontmatter, re.M), 'wrong phase')
    sources = re.search(r'^source: (.+)$', frontmatter, re.M)
    need(sources and sources[1].split(', ') == [s.name for s in summaries], 'missing source summary')
    need(text.split('## Current Test\n', 1)[1].split('## Tests\n', 1)[0].strip() == '[testing complete]', 'pending checkpoint')
    tests = text.split('## Tests\n', 1)[1].split('## Summary\n', 1)[0]
    headings = re.findall(r'^#{1,6} .+$', tests, re.M)
    numbers = [re.match(r'^### (\d+)\. ', heading) for heading in headings]
    need(all(numbers) and [int(m[1]) for m in numbers] == list(range(1, total + 1)), 'unparsed or misnumbered test heading')
    prelude, *blocks = re.split(r'^### \d+\. ', tests, flags=re.M)
    need(not prelude.strip(), 'unparsed test prelude')
    seen = set()
    for block in blocks:
        for line in block.splitlines()[1:]:
            need(not line.strip() or line.partition(':')[0] in FIELDS, 'unparsed test content')

        def field(name):
            matches = re.findall(r'^' + name + r': (.+)$', block, re.M)
            need(len(matches) == 1, f'missing or duplicate {name}')
            return matches[0]
        key = (field('summary_file'), field('coverage_id'))
        need(key in expected and key not in seen, 'missing, unknown or duplicate coverage')
        seen.add(key)
        entry = expected[key]
        need(human_needed(entry) is None, 'deliverable needs a human checkpoint')
        need(field('result') == 'pass' and field('source') == 'automated', 'not an automated pass')
        need(json.loads(field('expected')) == entry['description'], 'changed acceptance criterion')
        need(json.loads(field('evidence')) == entry['uat_refs'], 'weaker evidence')
    need(seen == set(expected), 'incomplete coverage')
    summary = text.split('## Summary\n', 1)[1].split('## Gaps\n', 1)[0]
    for name, value in [('total', total), ('passed', total), ('issues', 0), ('pending', 0),
                        ('skipped', 0), ('blocked', 0)]:
        need(re.search(r'^' + name + ': ' + str(value) + r'$', summary, re.M), 'incorrect totals')
    need(text.split('## Gaps\n', 1)[1].strip() == '[none]', 'unresolved gap')
    return total


def self_test(directory):
    total = check(directory)
    first = sorted(directory.glob('*-SUMMARY.md'))[0].name
    uat_mutations = {
        'missing-row': lambda t: re.sub(r'^### 1\..*?(?=^### 2\.)', '', t, count=1, flags=re.M | re.S),
        'manual-source': lambda t: t.replace('source: automated', 'source: human', 1),
        'pending-result': lambda t: t.replace('result: pass', 'result: [pending]', 1),
        'wrong-coverage': lambda t: re.sub(r'^coverage_id: .+$', 'coverage_id: missing', t, count=1, flags=re.M),
        'missing-evidence': lambda t: re.sub(r'^evidence: .+$', 'evidence: []', t, count=1, flags=re.M),
        'changed-criterion': lambda t: re.sub(r'^expected: .+$', 'expected: "weaker"', t, count=1, flags=re.M),
        'false-complete': lambda t: t.replace('status: complete', 'status: testing', 1),
        'stale-count': lambda t: t.replace(f'total: {total}', f'total: {total - 1}', 1),
        'missing-source': lambda t: t.replace(first + ', ', '', 1),
        'duplicate-row': lambda t: t.replace('## Summary\n', re.search(r'^### 1\..*?(?=^### 2\.)', t, re.M | re.S)[0] + '## Summary\n', 1),
        'wrong-phase': lambda t: t.replace(f'phase: {directory.name}', 'phase: GB-0-other', 1),
        'unnumbered-human-checkpoint': lambda t: t.replace('## Summary\n', '### Manual checkpoint\nresult: pending\nsource: human\n\n## Summary\n', 1),
        'extra-section': lambda t: t.replace('## Summary\n', '## Manual checks\n\n## Summary\n', 1),
        'unparsed-field': lambda t: t.replace('result: pass', 'manual_checkpoint: pending\nresult: pass', 1),
        'unparsed-prelude': lambda t: t.replace('## Tests\n', '## Tests\n\nManual checkpoint: pending\n', 1),
        'misnumbered-row': lambda t: t.replace('### 2. ', '### 99. ', 1),
        'open-gap': lambda t: t.replace('## Gaps\n\n[none]', '## Gaps\n\n- status: failed'),
    }
    # A SUMMARY that later routes a deliverable to a human must reopen the closure.
    summary_mutations = {
        'summary-human-judgment': lambda t: t.replace('human_judgment: false', 'human_judgment: true', 1),
    }
    uat_name = f'{phase_number(directory)}-UAT.md'
    controls = [(uat_name, k, m) for k, m in uat_mutations.items()] + \
               [(first, k, m) for k, m in summary_mutations.items()]
    for filename, label, mutate in controls:
        with tempfile.TemporaryDirectory(prefix='gbb-uat-closure-') as name:
            scratch = Path(name) / directory.name
            shutil.copytree(directory, scratch)
            path = scratch / filename
            original = path.read_text(encoding='utf-8')
            changed = mutate(original)
            need(changed != original, f'{label}: inactive mutation')
            path.write_text(changed, encoding='utf-8')
            try:
                check(scratch)
            except ClosureError:
                continue
            raise ClosureError(f'{label}: accepted weakened closure')
    # Regenerating from the same SUMMARYs must reproduce an accepted closure.
    with tempfile.TemporaryDirectory(prefix='gbb-uat-closure-') as name:
        scratch = Path(name) / directory.name
        shutil.copytree(directory, scratch)
        write(scratch, 'self-test')
        need(check(scratch) == total, 'regenerated closure rejected')
    # A quoted coverage id is still the same deliverable, so the closure must be written and accepted.
    with tempfile.TemporaryDirectory(prefix='gbb-uat-closure-') as name:
        scratch = Path(name) / directory.name
        shutil.copytree(directory, scratch)
        path = scratch / first
        original = path.read_text(encoding='utf-8')
        quoted = re.sub(r'^(  - id: )([^"\'\s]\S*)$', r'\1"\2"', original, count=1, flags=re.M)
        need(quoted != original, 'quoted-id: inactive mutation')
        path.write_text(quoted, encoding='utf-8')
        write(scratch, 'self-test')
        need(check(scratch) == total, 'quoted coverage id rejected')
    # The checker itself must refuse an optimized interpreter, through the real CLI.
    refused = subprocess.run([sys.executable, '-O', str(Path(__file__).resolve()), str(directory)],
                             capture_output=True, text=True, check=False)
    need(refused.returncode != 0 and 'must not run with python -O' in refused.stderr,
         'optimized interpreter was not refused')
    print(f'uat-closure self-test pass automated={total} controls={len(controls) + 3}')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('phase_dir', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', metavar='EVIDENCE_FILE', type=Path,
                      help='write {N}-UAT.md with this Automated Evidence prose')
    mode.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    directory = args.phase_dir.resolve()
    if args.write:
        path, total = write(directory, args.write.read_text(encoding='utf-8'))
        print(f'uat-closure wrote {path.name} automated={total} human=0')
    elif args.self_test:
        self_test(directory)
    else:
        print(f'uat-closure pass automated={check(directory)} human=0 gaps=0')


if __name__ == '__main__':
    try:
        main()
    except ClosureError as error:
        print(f'uat-closure rejected: {error}', file=sys.stderr)
        sys.exit(1)
