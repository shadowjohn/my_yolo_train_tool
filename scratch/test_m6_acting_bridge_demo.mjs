import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';

const DEMO_PATH = 'my_vrm_mascot/m6_acting_bridge_demo.html';

function readDemo() {
  assert.ok(existsSync(DEMO_PATH), `${DEMO_PATH} should exist`);
  return readFileSync(DEMO_PATH, 'utf8');
}

function testDemoHtmlContractExists() {
  const html = readDemo();

  assert.match(html, /Phase M6\.5/);
  assert.match(html, /Acting Bridge Demo Harness/);
  assert.match(html, /id=["']demoTraceList["']/);
  assert.match(html, /id=["']demoBridgeState["']/);
  assert.match(html, /id=["']demoLog["']/);
  assert.match(html, /id=["']demoCurrentAction["']/);
}

function testDemoButtonsExposeRequiredActions() {
  const html = readDemo();
  const requiredActions = [
    'act:success',
    'act:warning',
    'act:blocked',
    'act:failed',
    'trace:pending',
    'trace:running',
    'trace:done',
    'trace:failed',
    'trace:blocked',
    'talking:thinking',
    'talking:speaking',
    'talking:idle',
    'scenario:tool_success',
    'scenario:tool_failed',
    'scenario:speaking_while_running',
  ];

  for (const action of requiredActions) {
    assert.match(html, new RegExp(`data-demo-action=["']${action}["']`));
  }
}

function testDemoUsesBridgeFacingApisOnly() {
  const html = readDemo();

  assert.match(html, /import\s+\{\s*VrmMascot\s*,\s*createIntentTrace\s*\}\s+from\s+['"]\.\/js\/VrmMascot\.js['"]/);
  assert.match(html, /mascot\.act\(/);
  assert.match(html, /mascot\.updateIntentTrace\(/);
  assert.match(html, /mascot\.notifyTalkingState\(/);
  assert.doesNotMatch(html, /mascot\.performIntent\(/);
  assert.doesNotMatch(html, /\bfetch\s*\(/);
  assert.doesNotMatch(html, /\bXMLHttpRequest\b/);
}

function testDemoIncludesScenarioAndTraceHelpers() {
  const html = readDemo();

  assert.match(html, /function\s+applyTraceStatus\s*\(/);
  assert.match(html, /function\s+runScenario\s*\(/);
  assert.match(html, /function\s+renderTrace\s*\(/);
  assert.match(html, /function\s+appendLog\s*\(/);
  assert.match(html, /tool_success/);
  assert.match(html, /tool_failed/);
  assert.match(html, /speaking_while_running/);
}

const tests = [
  testDemoHtmlContractExists,
  testDemoButtonsExposeRequiredActions,
  testDemoUsesBridgeFacingApisOnly,
  testDemoIncludesScenarioAndTraceHelpers,
];

for (const test of tests) {
  test();
  console.log(`PASS ${test.name}`);
}
