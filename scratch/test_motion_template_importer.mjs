import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const SPEC_PATH = 'docs/superpowers/specs/2026-06-13-m6-7-motion-template-importer-design.md';
const LAB_PATH = 'my_vrm_mascot/motion_template_lab.html';
const MODULE_PATH = 'my_vrm_mascot/js/MotionTemplateImporter.js';
const INDEX_PATH = 'my_vrm_mascot/index.html';

function read(path) {
  return readFileSync(path, 'utf8');
}

async function importImporterModule() {
  return import(`${pathToFileURL(MODULE_PATH).href}?t=${Date.now()}`);
}

function testSpecRequiresDeterministicExport() {
  const spec = read(SPEC_PATH);

  assert.match(spec, /deterministic/i);
  assert.match(spec, /same VRMA sample|同一份 VRMA|Exporting the same VRMA sample/i);
  assert.match(spec, /JSON differences are not allowed|JSON 差異/i);
}

function testLabHtmlContractExists() {
  assert.equal(existsSync(LAB_PATH), true, `${LAB_PATH} should exist`);

  const html = read(LAB_PATH);
  assert.match(html, /Motion Template Lab/);
  assert.match(html, /VRMA-first Pose Importer/);
  assert.match(html, /載入 VRMA/);
  assert.match(html, /取第一幀/);
  assert.match(html, /取指定時間/);
  assert.match(html, /複製 JSON/);
  assert.match(html, /下載 JSON/);
  assert.match(html, /匯出 NaturalPosePreset/);
  assert.match(html, /Upper Body/);
  assert.match(html, /motion-template-json/);
}

function testLabReferencesVrmaCapabilityOnlyInLab() {
  const html = read(LAB_PATH);
  const index = read(INDEX_PATH);

  assert.match(html, /@pixiv\/three-vrm-animation/);
  assert.match(html, /VRMAnimationLoaderPlugin/);
  assert.match(html, /createVRMAnimationClip/);
  assert.doesNotMatch(index, /motion_template_lab|three-vrm-animation|VRMAnimationLoaderPlugin/);
}

function testLabDoesNotImportAgentRuntime() {
  const html = read(LAB_PATH);

  assert.doesNotMatch(html, /ActionQueue/);
  assert.doesNotMatch(html, /ActingBridge/);
  assert.doesNotMatch(html, /ActingPolicy/);
  assert.doesNotMatch(html, /PoseDirector/);
  assert.doesNotMatch(html, /contextDigest/);
  assert.doesNotMatch(html, /performIntent/);
}

async function testUpperBodyWhitelistIsExplicitAndStable() {
  const mod = await importImporterModule();

  assert.deepEqual(mod.UPPER_BODY_BONES, [
    'spine',
    'chest',
    'leftShoulder',
    'rightShoulder',
    'leftUpperArm',
    'rightUpperArm',
    'leftLowerArm',
    'rightLowerArm',
    'leftHand',
    'rightHand',
  ]);

  assert.equal(mod.UPPER_BODY_BONES.includes('head'), false);
  assert.equal(mod.UPPER_BODY_BONES.includes('hips'), false);
  assert.equal(mod.UPPER_BODY_BONES.includes('leftUpperLeg'), false);
}

async function testBuildNaturalPosePresetMergesUpperBodyOnly() {
  const {
    buildNaturalPosePreset,
  } = await importImporterModule();

  const basePreset = {
    model: 'AliciaSolid',
    basePose: {
      rotation: {
        leftUpperLeg: { x: 1, y: 0, z: 2 },
        rightUpperLeg: { x: -1, y: 0, z: -2 },
        leftUpperArm: { x: 9, y: -3, z: 54 },
      },
      position: {
        hips: { x: -0.014, y: 0, z: 0.004 },
      },
    },
  };

  const preset = buildNaturalPosePreset({
    basePreset,
    rotations: {
      leftUpperArm: { x: 12.345, y: -2.222, z: 43.333 },
      rightUpperArm: { x: 10, y: 2, z: -43 },
      head: { x: 99, y: 99, z: 99 },
      hips: { x: 88, y: 88, z: 88 },
    },
    source: {
      type: 'vrma',
      fileName: 'stand.vrma',
      sampleTime: 0,
    },
    warnings: [],
  });

  assert.deepEqual(preset.basePose.rotation.leftUpperArm, { x: 12.35, y: -2.22, z: 43.33 });
  assert.deepEqual(preset.basePose.rotation.rightUpperArm, { x: 10, y: 2, z: -43 });
  assert.deepEqual(preset.basePose.rotation.leftUpperLeg, { x: 1, y: 0, z: 2 });
  assert.deepEqual(preset.basePose.rotation.rightUpperLeg, { x: -1, y: 0, z: -2 });
  assert.equal(preset.basePose.rotation.head, undefined);
  assert.deepEqual(preset.basePose.position.hips, { x: -0.014, y: 0, z: 0.004 });
}

async function testStableExportIsDeterministic() {
  const {
    buildNaturalPosePreset,
    stableStringifyPreset,
  } = await importImporterModule();

  const basePreset = {
    model: 'AliciaSolid',
    basePose: {
      rotation: {
        chest: { x: -2, y: -2, z: -1 },
        leftUpperArm: { x: 9, y: -3, z: 54 },
        rightUpperArm: { x: 9, y: 3, z: -54 },
      },
      position: {
        hips: { x: -0.014, y: 0, z: 0.004 },
      },
    },
  };

  const rotationsA = {
    rightUpperArm: { z: -42.7777, x: 7.1111, y: 3.2222 },
    leftUpperArm: { y: -3.2222, z: 42.7777, x: 7.1111 },
    chest: { z: -0.5555, y: -1.2222, x: -2.7777 },
  };

  const rotationsB = {
    chest: { x: -2.7777, y: -1.2222, z: -0.5555 },
    leftUpperArm: { x: 7.1111, y: -3.2222, z: 42.7777 },
    rightUpperArm: { x: 7.1111, y: 3.2222, z: -42.7777 },
  };

  const source = {
    type: 'vrma',
    fileName: 'girl_stand.vrma',
    sampleTime: 0.25,
  };

  const first = stableStringifyPreset(buildNaturalPosePreset({
    basePreset,
    rotations: rotationsA,
    source,
    warnings: ['missing leftHand'],
  }));

  const second = stableStringifyPreset(buildNaturalPosePreset({
    basePreset,
    rotations: rotationsB,
    source,
    warnings: ['missing leftHand'],
  }));

  assert.equal(first, second);
  assert.match(first, /"sampleTime": 0.25/);
  assert.doesNotMatch(first, /generatedAt|Date|exportSessionId|Math\.random/);
}

async function testClampSampleTime() {
  const { clampSampleTime } = await importImporterModule();

  assert.equal(clampSampleTime(-1, 2), 0);
  assert.equal(clampSampleTime(3, 2), 2);
  assert.equal(clampSampleTime(1.23456, 2), 1.23456);
  assert.equal(clampSampleTime(Number.NaN, 2), 0);
}

async function run() {
  const tests = [
    testSpecRequiresDeterministicExport,
    testLabHtmlContractExists,
    testLabReferencesVrmaCapabilityOnlyInLab,
    testLabDoesNotImportAgentRuntime,
    testUpperBodyWhitelistIsExplicitAndStable,
    testBuildNaturalPosePresetMergesUpperBodyOnly,
    testStableExportIsDeterministic,
    testClampSampleTime,
  ];

  for (const test of tests) {
    await test();
    console.log(`PASS ${test.name}`);
  }
}

run().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
