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

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / '.planning/milestones/v0.2-MILESTONE-AUDIT.md'
INTEGRATION = ROOT / '.planning/milestones/v0.2-INTEGRATION-AUDIT.md'


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
    # Phase keys come from the tracked directories, so an inserted decimal
    # phase (15.1) is audited like any other instead of being silently skipped.
    keys = sorted({m[1] for f in tracked
                   if (m := re.match(r'^\.planning/phases/GB-(\d+(?:\.\d+)?)-[^/]+/[^/]+$', f))},
                  key=lambda k: tuple(int(x) for x in k.split('.')))
    phases = {}
    schema_missing = []
    for key in keys:
        n = str(int(key.split('.')[0])) + ('.' + key.split('.')[1] if '.' in key else '')
        dirs = sorted({str(Path(f).parent) for f in tracked
                       if re.match(rf'^\.planning/phases/GB-{re.escape(key)}-[^/]+/[^/]+$', f)})
        assert len(dirs) == 1
        directory = Path(dirs[0])
        files = [Path(f) for f in tracked if Path(f).parent == directory]
        ver = read_at(next(f for f in files if f.name.endswith('-VERIFICATION.md')))
        val = front(read_at(next(f for f in files if f.name.endswith('-VALIDATION.md'))))
        completed = {}
        summaries = sorted(f for f in files if f.name.endswith('-SUMMARY.md'))
        for summary in summaries:
            metadata = front(read_at(summary))
            if not re.search(r'^requirements-completed:', metadata, re.M):
                # Recorded as schema debt; the claim is not inferred from other keys.
                schema_missing.append(summary.stem.removesuffix('-SUMMARY'))
                continue
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
        n = str(int(phase))
        p = phases[n]
        # Cell padding is presentation only; 09805f3 rewrote Phase 13's row unpadded.
        ver_rows = [r for r in p['verification'].splitlines() if re.match(r'^\|\s*' + rid + r'\s*\|', r)]
        verified = p['status'] == 'passed' and any(re.search(r'\bSATISFIED\b', r) for r in ver_rows)
        claimed = p['completed'].get(rid, [])
        checked = bool(re.search(r'^- \[x\] \*\*' + rid + r'\*\*:', req, re.M))
        status = ('unsatisfied' if p['status'] == 'gaps_found' or not ver_rows
                  else 'satisfied' if verified and claimed and checked and central == 'Complete'
                  else 'partial' if verified or claimed else 'unsatisfied')
        hardening = phases.get('15.1', {}).get('completed', {}).get(rid, [])
        requirements.append(dict(id=rid, phase=n, verification='SATISFIED' if verified else 'missing',
                                 summaries=claimed, hardening=len(hardening), checked=checked,
                                 central=central, status=status))
    return dict(revision=revision, phases=phases, requirements=requirements,
                schema_missing=schema_missing)


def requirement_row(r):
    return (f"| {r['id']} | {r['phase']} | {r['verification']} | "
            f"{', '.join(r['summaries']) or '—'} | {r['hardening'] or '—'} | "
            f"{'[x]' if r['checked'] else '[ ]'} {r['central']} | {r['status']} |")


def phase_row(n, p):
    return f"| {n} | {p['summaries']} | {p['status']} {p['score']} | {p['nyquist']} |"


def integration_scores():
    text = INTEGRATION.read_text()
    match = re.search(r'^Scores: connections (\d+/\d+); flows (\d+/\d+); source ([0-9a-f]{40})$', text, re.M)
    assert match, 'integration report scores line'
    return match[1], match[2], match[3]


def check(text, data):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)
    fm = front(text)
    phases = data['phases']
    partial = [n for n, p in phases.items() if p['nyquist'] != 'COMPLIANT']
    req_gaps = {r['id'] for r in data['requirements'] if r['status'] != 'satisfied'}
    expected_status = 'gaps_found' if req_gaps or partial else 'tech_debt'
    require(scalar(fm, 'status') == expected_status, 'audit status does not follow gaps')
    count = sum(r['status'] == 'satisfied' for r in data['requirements'])
    require(f'  requirements: {count}/28\n' in fm, 'requirements score')
    passed = sum(p['status'] == 'passed' for p in phases.values())
    require(f'  phases: {passed}/{len(phases)}\n' in fm, 'phase score')
    connections, flows, source = integration_scores()
    require(source == data['revision'], 'integration report audits a different source')
    require(f'  integration: {connections}\n' in fm and f'  flows: {flows}\n' in fm, 'integration/flow scores')
    require(f"summary_count: {sum(p['summaries'] for p in phases.values())}\n" in fm, 'summary count')
    for r in data['requirements']:
        require(text.count(requirement_row(r)) == 1, f"three-source row {r['id']}")
    for n, p in phases.items():
        require(text.count(phase_row(n, p)) == 1, f'phase row {n}')
    require(set(re.findall(r'^    - id: ([A-Z]+-\d+)$', fm, re.M)) == req_gaps, 'structured requirement gaps')
    listed = re.search(r'^  partial_phases: \[(.*)\]$', fm, re.M)
    require(listed is not None and [x.strip().strip('"') for x in listed[1].split(',') if x.strip()] == partial,
            'Nyquist partial phases')
    require(f"  overall: {'partial' if partial else 'compliant'}\n" in fm, 'Nyquist overall')
    for name in data['schema_missing']:
        require(name in text, f'SUMMARY schema debt {name} not disclosed')
    expected_next = ('/gsd-validate-phase ' + partial[0] if partial and not req_gaps
                     else '/gsd-complete-milestone v0.2' if not req_gaps else None)
    require(expected_next is not None and scalar(fm, 'next_command') == expected_next, 'next route')
    require('[v0.2-INTEGRATION-AUDIT.md](v0.2-INTEGRATION-AUDIT.md)' in text, 'integration evidence link')
    require('25 actual passes and 82 matched expected failures' in text, 'bounded evidence claims')
    return errors


def self_test(text, data):
    fm = front(text)
    status = scalar(fm, 'status')
    # Each mutation flips the recorded value, so the controls stay non-trivial
    # whether the report is gaps_found or clean.
    partial = re.search(r'^  partial_phases: \[(.*)\]$', fm, re.M)[1]
    overall = re.search(r'^  overall: (\w+)$', fm, re.M)[1]
    mutations = [text.replace(f'status: {status}', f'status: {other}', 1)
                 for other in ('passed', 'gaps_found', 'tech_debt') if other != status]
    mutations += [text.replace('  requirements: 28/28', '  requirements: 25/28', 1),
                 text.replace('  phases: 10/10', '  phases: 9/9', 1),
                 re.sub(r'  integration: \d+/\d+', '  integration: 1/15', text, count=1),
                 re.sub(r'  partial_phases: \[.*\]', '  partial_phases: [' + ('' if partial else '7') + ']',
                        text, count=1),
                 text.replace(f'  overall: {overall}',
                              '  overall: ' + ('compliant' if overall == 'partial' else 'partial'), 1),
                 text.replace('\nnext_command: ', '\nnext_command: /gsd-complete-milestone v0.2 #', 1),
                 re.sub(r'summary_count: \d+', 'summary_count: 134', text, count=1),
                 text.replace('  requirements: []', '  requirements:\n    - id: CGB-99', 1)]
    for name in data['schema_missing']:
        mutations.append(text.replace(name, 'X' * len(name)))
    for rid in ('CGB-05', 'CGB-07', 'SHIP-11'):
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
    # a validation change in either direction must change the verdict.
    for change in ('unsatisfied', 'orphaned', 'nyquist-regress', 'nyquist-fixed'):
        altered = copy.deepcopy(data)
        if change == 'nyquist-regress':
            altered['phases']['7']['nyquist'] = 'PARTIAL'
        elif change == 'nyquist-fixed':
            # Flip the last phase's recorded Nyquist state in whichever direction applies.
            last = altered['phases'][list(altered['phases'])[-1]]
            if all(p['nyquist'] == 'COMPLIANT' for p in altered['phases'].values()):
                last['nyquist'] = 'NOT-VALIDATED'
            else:
                for p in altered['phases'].values():
                    p['nyquist'] = 'COMPLIANT'
        else:
            altered['requirements'][0]['status'] = 'unsatisfied'
            if change == 'orphaned':
                altered['requirements'][0]['verification'] = 'missing'
        assert check(text, altered), 'gap hidden by clean report'
    return len(mutations) + 7


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--facts', action='store_true')
    parser.add_argument('--rows', action='store_true', help='print the rows the report must contain')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    data = facts()
    if args.facts:
        print(json.dumps(data, indent=2))
        return
    if args.rows:
        print('\n'.join(requirement_row(r) for r in data['requirements']))
        print('\n'.join(phase_row(n, p) for n, p in data['phases'].items()))
        print('schema_missing:', ', '.join(data['schema_missing']))
        return
    text = REPORT.read_text()
    errors = check(text, data)
    assert not errors, '; '.join(errors)
    phases = data['phases']
    satisfied = sum(r['status'] == 'satisfied' for r in data['requirements'])
    print(f"PASS: audit reconciles 28 requirements, {sum(p['summaries'] for p in phases.values())} summaries "
          f"and {len(phases)} phase reports; {satisfied} satisfied, {28 - satisfied} not satisfied")
    if args.self_test:
        print(f'PASS: {self_test(text, data)} negative controls rejected')


if __name__ == '__main__':
    main()
