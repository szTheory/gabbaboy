const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const { test } = require('node:test');

const root = path.resolve(__dirname, '../..');
const checker = path.join(root, '.planning/phases/GB-13-cgb-hdma/verify-hdma-closure.py');
const python = String.raw`import json, pathlib, runpy, sys
root = pathlib.Path(sys.argv[1])
checks = runpy.run_path(sys.argv[2])
state = (root / '.planning/STATE.md').read_text()
continuation = (root / '.planning/phases/GB-13-cgb-hdma/continue.md').read_text()
config = json.loads((root / '.planning/config.json').read_text())
checks['handoff_values'](state, continuation, config)
print('actual phase13 handoff contract passed')`;

test('phase 13 continuity documents route execution to automated verification and stop before phase 14', () => {
  const result = spawnSync('python3', ['-I', '-c', python, root, checker], {
    cwd: root,
    encoding: 'utf8',
    maxBuffer: 1024 * 1024,
    timeout: 10000,
  });
  if (result.error) {
    throw new Error(`handoff contract could not run: ${result.error.message}`);
  }
  const output = `${result.stdout || ''}${result.stderr || ''}`;
  assert.equal(result.status, 0, output || `handoff contract exited ${result.status}`);
});


test('phase 13 completed goal verification retains the UAT route and phase pause', () => {
  const progression = String.raw`import runpy, sys
checks = runpy.run_path(sys.argv[1])
state = "Current stage: Phase 13 execution and goal verification complete.\nNext command: /gsd-verify-work 13\nPhase 14 — CGB-E Model Qualification and Corpus remains unstarted.\n"
config = {"workflow": {"auto_advance": False, "_auto_chain_active": False}}
checks['handoff_values'](state, state, config)
try:
    checks['handoff_values'](state.replace('execution and goal verification complete', 'planning'), state, config)
except checks['ContractError']:
    pass
else:
    raise AssertionError('accepted an incorrect completed stage')`;
  const result = spawnSync('python3', ['-I', '-c', progression, checker], {
    cwd: root, encoding: 'utf8', maxBuffer: 1024 * 1024, timeout: 10000,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, `${result.stdout || ''}${result.stderr || ''}`);
});

test('completed automated UAT routes to phase 14 discussion without repeating verification', () => {
  const progression = String.raw`import runpy, sys
checks = runpy.run_path(sys.argv[1])
state = "Completed stage: Phase 13 automated UAT complete.\nNext command: /gsd-discuss-phase 14\nPhase 14 — CGB-E Model Qualification and Corpus remains unstarted.\n"
config = {"workflow": {"auto_advance": False, "_auto_chain_active": False}}
checks['handoff_values'](state, state, config)
for other_state, other_continuation in (
    (state.replace('/gsd-discuss-phase 14', '/gsd-verify-work 13'), state),
    (state, state.replace('automated UAT complete', 'planning')),
    (state, state.replace('/gsd-discuss-phase 14', '/gsd-execute-phase 14')),
):
    try:
        checks['handoff_values'](other_state, other_continuation, config)
    except checks['ContractError']:
        pass
    else:
        raise AssertionError('accepted stale route or conflicting completed stage')`;
  const result = spawnSync('python3', ['-I', '-c', progression, checker], {
    cwd: root, encoding: 'utf8', maxBuffer: 1024 * 1024, timeout: 10000,
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, `${result.stdout || ''}${result.stderr || ''}`);
});
