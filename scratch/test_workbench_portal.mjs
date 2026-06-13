import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';

const PORTAL_PATH = 'my_vrm_mascot/portal.html';
const RUN_SERVER_PATH = 'my_vrm_mascot/run_server.bat';
const RUN_SERVER_DEBUG_PATH = 'my_vrm_mascot/run_server_debug.bat';
const STOP_SERVER_PATH = 'my_vrm_mascot/stop_server.bat';
const OPEN_PORTAL_PATH = 'my_vrm_mascot/open_portal.bat';

function read(path) {
  return readFileSync(path, 'utf8');
}

function testPortalExistsAndIsChineseFirstWorkbench() {
  assert.equal(existsSync(PORTAL_PATH), true, `${PORTAL_PATH} should exist`);

  const html = read(PORTAL_PATH);
  assert.match(html, /My VRM Mascot Workbench/);
  assert.match(html, /本地開發入口/);
  assert.match(html, /展示區/);
  assert.match(html, /Motion Mining/);
  assert.match(html, /Pose \/ Motion Tools/);
  assert.match(html, /Runtime Demo/);
  assert.match(html, /使用方法/);
  assert.match(html, /Server/);
}

function testPortalLinksKnownMascotSurfaces() {
  const html = read(PORTAL_PATH);

  for (const href of [
    'index.html',
    'motion_template_lab.html',
    'm6_acting_bridge_demo.html',
    'README.md',
    'examples/m6_7_vrma_samples/README.md',
    'examples/m6_7_motion_mining/mining_log.json',
    'examples/m6_7_motion_mining/mining_report.json',
  ]) {
    assert.match(html, new RegExp(`href="${href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"`));
  }
}

function testPortalDocumentsLocalServerAndApacheBoundary() {
  const html = read(PORTAL_PATH);

  assert.match(html, /run_server\.bat/);
  assert.match(html, /open_portal\.bat/);
  assert.match(html, /stop_server\.bat/);
  assert.match(html, /python \.\\server\.py/);
  assert.match(html, /http:\/\/127\.0\.0\.1:8765\/portal\.html/);
  assert.match(html, /Apache2/);
  assert.match(html, /3wa/);
  assert.match(html, /靜態展示可直接搬移/);
  assert.match(html, /寫入.*PHP API|寫入.*Python API/);
}

function testServerScriptsExistAndUseLocalPort() {
  for (const path of [RUN_SERVER_PATH, RUN_SERVER_DEBUG_PATH, STOP_SERVER_PATH, OPEN_PORTAL_PATH]) {
    assert.equal(existsSync(path), true, `${path} should exist`);
  }

  const runServer = read(RUN_SERVER_PATH);
  assert.match(runServer, /cd \/d "%~dp0"/);
  assert.match(runServer, /python server\.py/);
  assert.match(runServer, /127\.0\.0\.1:8765/);

  const runServerDebug = read(RUN_SERVER_DEBUG_PATH);
  assert.match(runServerDebug, /set FLASK_DEBUG=1/);
  assert.match(runServerDebug, /python server\.py/);

  const stopServer = read(STOP_SERVER_PATH);
  assert.match(stopServer, /set PORT=8765/);
  assert.match(stopServer, /netstat -ano/);
  assert.match(stopServer, /findstr "LISTENING"/);
  assert.match(stopServer, /taskkill \/PID %%a \/F/);

  const openPortal = read(OPEN_PORTAL_PATH);
  assert.match(openPortal, /start "" "http:\/\/127\.0\.0\.1:8765\/portal\.html"/);
}

function run() {
  const tests = [
    testPortalExistsAndIsChineseFirstWorkbench,
    testPortalLinksKnownMascotSurfaces,
    testPortalDocumentsLocalServerAndApacheBoundary,
    testServerScriptsExistAndUseLocalPort,
  ];

  for (const test of tests) {
    test();
    console.log(`PASS ${test.name}`);
  }
}

run();
