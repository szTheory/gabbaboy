#!/usr/bin/env python3
"""Check the pending phase's scope against its immutable closeout input."""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent

def check(scope, state, config, manager):
    assert scope['phase'] == '15.1' and scope['decision'] == 'resolve-first'
    assert scope['next_command'] == '/gsd-plan-phase 15.1'
    sha = scope['source_head']
    assert re.fullmatch(r'[0-9a-f]{40}', sha)
    audit = subprocess.check_output(['git', 'show', sha + ':.planning/v0.2-MILESTONE-AUDIT.md'], cwd=ROOT, text=True)
    expected = [json.loads(m) for m in re.findall(r'^      - (".*")$', audit.split('---')[1], re.M)]
    debt = [x for x in scope['items'] if re.fullmatch(r'P\d+-\d+', x['id'])]
    assert len(expected) == len(debt) == scope['audit_debt_count'] == 21
    assert [x['description'] for x in debt] == expected
    assert len({x['id'] for x in scope['items']}) == len(scope['items']) == 24
    assert {x['id'] for x in scope['items']} >= {'SCAN-UAT', 'SCAN-LINK', 'SUMMARY-SCHEMA'}
    assert all(x['status'] == 'open' and (ROOT / x['source']).is_file() for x in scope['items'])
    assert state['next']['command'] == '/gsd-plan-phase 15.1'
    assert next(x for x in state['phases'] if x['number'] == '15.1')['status'] == 'pending'
    assert all(config['workflow'][x] is False for x in ('auto_advance', '_auto_chain_active'))
    assert manager['phase_count'] == 10 and manager['completed_count'] == 9 and manager['all_complete'] is False
    last = next(x for x in manager['phases'] if x['number'] == '15.1')
    assert last['plan_count'] == 0 and last['summary_count'] == 0 and last['phase_complete'] is False

scope = json.loads((PHASE / '15.1-SCOPE.json').read_text())
state = json.loads((ROOT / '.planning/state.json').read_text())
config = json.loads((ROOT / '.planning/config.json').read_text())
manager = json.loads(subprocess.check_output(['node', str(Path.home() / '.codex/gsd-core/bin/gsd-tools.cjs'), 'query', 'init.manager'], cwd=ROOT, text=True))
check(scope, state, config, manager)
for file, section in [('STATE.md', '## Current Position'), ('PROJECT.md', '## Current State')]:
    text = (ROOT / '.planning' / file).read_text().split(section, 1)[1]
    text = text.split('### Historical', 1)[0].split('**Phase 15 is complete;', 1)[0]
    assert '/gsd-plan-phase 15.1' in text
for file in [ROOT / '.planning/.continue-here.md', PHASE / 'continue.md']:
    assert '/gsd-plan-phase 15.1' in file.read_text()
fm = (ROOT / '.planning/STATE.md').read_text().split('---')[1]
assert 'current_phase: "15.1"' in fm and 'completed_phases: 9' in fm and 'total_phases: 10' in fm
roadmap = (ROOT / '.planning/ROADMAP.md').read_text()
assert '### Phase 15.1: Release Hardening and Milestone Debt Closure (INSERTED)' in roadmap
assert (ROOT / '.planning/REQUIREMENTS.md').is_file()
assert not (ROOT / '.planning/milestones/v0.2-ROADMAP.md').exists()
assert not list(PHASE.glob('*-PLAN.md'))
print('PASS: 21 original debts + 3 scan/schema issues; 9/10 phases complete; pending phase and four handoffs agree')
if '--self-test' in sys.argv:
    mutants = []
    def mutant(which, fn):
        args = copy.deepcopy([scope, state, config, manager]); fn(args[which]); mutants.append(args)
    mutant(0, lambda x: x['items'].pop(0))
    mutant(0, lambda x: x['items'][0].update(description='weakened finding'))
    mutant(0, lambda x: x['items'][1].update(id=x['items'][0]['id']))
    mutant(0, lambda x: x['items'][0].update(status='fixed'))
    mutant(1, lambda x: x['next'].update(command='/gsd-complete-milestone v0.2'))
    mutant(2, lambda x: x['workflow'].update(auto_advance=True))
    mutant(2, lambda x: x['workflow'].update(_auto_chain_active=True))
    mutant(3, lambda x: x.update(completed_count=10, all_complete=True))
    for args in mutants:
        try:
            check(*args)
        except AssertionError:
            continue
        raise AssertionError('weakened scope accepted')
    print('PASS: 8 negative controls rejected')
