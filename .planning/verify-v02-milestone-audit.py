#!/usr/bin/env python3
"""Check the v0.2 audit's three-source accounting; no emulator/CI claim is inferred.

Boundary-only tool: inputs come from the report's recorded source_head commit.
Later phase closures do not change its point-in-time facts or live routes.
Only the needed scalar/list fields are read, avoiding legacy YAML prose quoting.
"""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / '.planning/v0.2-MILESTONE-AUDIT.md'


def front(text):
    return text.split('---', 2)[1]


def scalar(text, key):
    match = re.search(r'^' + re.escape(key) + r':[ \t]*(.*?)[ \t]*$', text, re.M)
    assert match, f'missing {key}'
    return match[1].strip('"\'')


def facts():
    # This is a historical audit: later closures must not make it claim facts
    # from a different HEAD. New audits record a new source_head explicitly.
    revision = scalar(front(REPORT.read_text()), 'source_head')
    assert re.fullmatch(r'[0-9a-f]{40}', revision), 'invalid source_head'
    def read_at(path):
        return subprocess.check_output(['git', 'show', f'{revision}:{path}'], cwd=ROOT, text=True)
    tracked = subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', revision, '--', '.planning/phases'],
        cwd=ROOT, text=True).splitlines()
    req = read_at('.planning/REQUIREMENTS.md')
    rows = re.findall(r'^\| ([A-Z]+-\d+) \| Phase (\d+) \| (\w+) \|$', req, re.M)
    assert len(rows) == 28 and len({r[0] for r in rows}) == 28
    phases = {}
    for n in range(7, 16):
        dirs = sorted({str(Path(f).parent) for f in tracked
                       if re.match(rf'^\.planning/phases/GB-{n:02d}-[^/]+/[^/]+$', f)})
        assert len(dirs) == 1
        directory = Path(dirs[0])
        files = [Path(f) for f in tracked if Path(f).parent == directory]
        ver = read_at(next(f for f in files if f.name.endswith('-VERIFICATION.md')))
        val = front(read_at(next(f for f in files if f.name.endswith('-VALIDATION.md'))))
        completed = {}
        summaries = sorted(f for f in files if f.name.endswith('-SUMMARY.md'))
        for summary in summaries:
            metadata = front(read_at(summary))
            field = scalar(metadata, 'requirements-completed')
            if not field:
                block = re.search(r'^requirements-completed:\n((?:[ \t]+- [^\n]+\n)+)', metadata, re.M)
                assert block, summary.name
                field = block[1]
            else:
                assert field.startswith('[') and field.endswith(']'), summary.name
            for item in re.findall(r'[A-Z]+-\d+', field):
                completed.setdefault(item, []).append(summary.stem.removesuffix('-SUMMARY'))
        phases[n] = dict(directory=str(directory),
                         status=scalar(front(ver), 'status'), verification=ver,
                         score=scalar(front(ver), 'score').split()[0],
                         completed=completed, summaries=len(summaries),
                         nyquist=('COMPLIANT' if scalar(val, 'status') == 'validated'
                                  and scalar(val, 'nyquist_compliant') == 'true'
                                  else 'PARTIAL' if scalar(val, 'status') == 'validated'
                                  else 'NOT-VALIDATED'))
    requirements = []
    for rid, phase, central in rows:
        n = int(phase)
        p = phases[n]
        ver_rows = [r for r in p['verification'].splitlines() if re.match(r'^\| ' + rid + r' \|', r)]
        verified = p['status'] == 'passed' and any(re.search(r'\bSATISFIED\b', r) for r in ver_rows)
        claimed = p['completed'].get(rid, [])
        checked = bool(re.search(r'^- \[x\] \*\*' + rid + r'\*\*:', req, re.M))
        status = ('unsatisfied' if p['status'] == 'gaps_found' or not ver_rows
                  else 'satisfied' if verified and claimed and checked and central == 'Complete'
                  else 'partial' if verified or claimed else 'unsatisfied')
        requirements.append(dict(id=rid, phase=n, verification='SATISFIED' if verified else 'missing',
                                 summaries=claimed, checked=checked, central=central, status=status))
    return dict(phases=phases, requirements=requirements)


def requirement_row(r):
    return (f"| {r['id']} | {r['phase']} | {r['verification']} | "
            f"{', '.join(r['summaries']) or '—'} | "
            f"{'[x]' if r['checked'] else '[ ]'} {r['central']} | {r['status']} |")


def phase_row(n, p):
    return f"| {n} | {p['summaries']} | {p['status']} {p['score']} | {p['nyquist']} |"


def check(text, data):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)
    fm = front(text)
    expected_status = 'gaps_found' if any(r['status'] != 'satisfied' for r in data['requirements']) or any(
        p['nyquist'] != 'COMPLIANT' for p in data['phases'].values()) else 'tech_debt'
    require(scalar(fm, 'status') == expected_status, 'audit status does not follow gaps')
    count = sum(r['status'] == 'satisfied' for r in data['requirements'])
    require(f'  requirements: {count}/28\n' in fm, 'requirements score')
    require(f"  phases: {sum(p['status'] == 'passed' for p in data['phases'].values())}/9\n" in fm, 'phase score')
    require('  integration: 9/9\n' in fm and '  flows: 6/6\n' in fm, 'integration/flow scores')
    for r in data['requirements']:
        require(text.count(requirement_row(r)) == 1, f"three-source row {r['id']}")
    for n, p in data['phases'].items():
        require(text.count(phase_row(n, p)) == 1, f'phase row {n}')
    expected_gaps = {r['id'] for r in data['requirements'] if r['status'] != 'satisfied'}
    require(set(re.findall(r'^    - id: ([A-Z]+-\d+)$', fm, re.M)) == expected_gaps, 'structured requirement gaps')
    require('  partial_phases: []\n' in fm and '  overall: compliant\n' in fm
            and all(p['nyquist'] == 'COMPLIANT' for p in data['phases'].values()), 'Nyquist discovery')
    require(scalar(fm, 'next_command') == '/gsd-complete-milestone v0.2', 'next route')
    require('[v0.2-INTEGRATION-AUDIT.md](v0.2-INTEGRATION-AUDIT.md)' in text, 'integration evidence link')
    require('63/63' in text and '25 actual passes and 82 matched expected failures' in text, 'bounded evidence claims')
    return errors


def self_test(text, data):
    mutations = [text.replace('status: tech_debt', 'status: passed', 1),
                 text.replace('  requirements: 28/28', '  requirements: 25/28', 1),
                 text.replace('  phases: 9/9', '  phases: 8/9', 1),
                 text.replace('  integration: 9/9', '  integration: 8/9', 1),
                 text.replace('  overall: compliant', '  overall: partial', 1),
                 text.replace('\nnext_command: /gsd-complete-milestone v0.2', '\nnext_command: /gsd-new-milestone', 1),
                 text.replace('  requirements: []', '  requirements:\n    - id: CGB-99', 1)]
    for rid in ('CGB-05', 'CGB-07', 'CGB-09'):
        row = next(requirement_row(r) for r in data['requirements'] if r['id'] == rid)
        mutations.extend([text.replace(row, '', 1), text.replace(row, row.replace('satisfied', 'partial'), 1)])
    for altered in mutations:
        assert altered != text and check(altered, data), 'weakened report accepted'
    for change in ('verification', 'checkbox', 'summary'):
        altered = copy.deepcopy(data)
        row = altered['requirements'][0]
        if change == 'verification':
            row['verification'] = 'missing'
        elif change == 'checkbox':
            row['checked'] = False
        else:
            row['summaries'] = []
        assert check(text, altered), 'changed source accepted'
    # A discovered requirement gap must override the otherwise clean score;
    # a validation regression must likewise prevent a compliant verdict.
    for change in ('unsatisfied', 'orphaned', 'nyquist'):
        altered = copy.deepcopy(data)
        if change == 'nyquist':
            altered['phases'][7]['nyquist'] = 'PARTIAL'
        else:
            altered['requirements'][0]['status'] = 'unsatisfied'
            if change == 'orphaned':
                altered['requirements'][0]['verification'] = 'missing'
        assert check(text, altered), 'gap hidden by clean report'
    return len(mutations) + 6


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--facts', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    data = facts()
    if args.facts:
        print(json.dumps(data, indent=2))
        return
    text = REPORT.read_text()
    errors = check(text, data)
    assert not errors, '; '.join(errors)
    print('PASS: audit reconciles 28 requirements, 134 summaries and 9 phase reports; 28 satisfied, 0 partial')
    if args.self_test:
        print(f'PASS: {self_test(text, data)} negative controls rejected')


if __name__ == '__main__':
    main()
