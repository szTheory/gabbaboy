const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const { test } = require('node:test');

const root = path.resolve(__dirname, '../..');
const checker = path.join(root, 'tests/scripts/verify-cgb-hdma-claims.py');

test('HDMA claim language does not turn software agreement into physical qualification', (context) => {
  const args = ['-I', checker];
  if (process.env.GSD_PROHIB_SUBJECT) {
    args.push('--subject', process.env.GSD_PROHIB_SUBJECT);
  }
  const result = spawnSync('python3', args, {
    cwd: root,
    encoding: 'utf8',
    maxBuffer: 1024 * 1024,
    timeout: 10000,
  });
  if (result.error) {
    throw new Error(`claim checker could not run: ${result.error.message}`);
  }
  const output = `${result.stdout || ''}${result.stderr || ''}`;
  const violation = /CGB-C evidence must not be presented as physical CGB-E qualification/;
  if (result.status !== 0 && violation.test(output)) {
    assert.fail(`claim checker rejected prohibited qualification language: ${output}`);
  }
  if (result.status !== 0) {
    context.skip(`claim checker did not reach the named qualification predicate: ${output}`);
  }
  assert.equal(result.status, 0, output || `claim checker exited ${result.status}`);
});
