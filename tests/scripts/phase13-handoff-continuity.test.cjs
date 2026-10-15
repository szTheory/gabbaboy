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
