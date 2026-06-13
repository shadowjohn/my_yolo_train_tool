import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  CHARACTER_INSPECTOR_SECTIONS,
  CHARACTER_INSPECTOR_BONE_GROUPS,
  CHARACTER_INSPECTOR_BONE_LABELS,
  getInspectorBoneLabel,
  getInspectorBonesForGroup,
} from '../my_vrm_mascot/js/CharacterInspectorLabels.js';

const indexHtml = readFileSync(new URL('../my_vrm_mascot/index.html', import.meta.url), 'utf8');
const css = readFileSync(new URL('../my_vrm_mascot/css/mascot.css', import.meta.url), 'utf8');

function testSectionMetadataUsesChineseLabels() {
  assert.deepEqual(
    CHARACTER_INSPECTOR_SECTIONS.map(section => section.id),
    ['pose', 'expression', 'lookAt', 'motion']
  );
  assert.deepEqual(
    CHARACTER_INSPECTOR_SECTIONS.map(section => section.label),
    ['姿勢', '表情', '視線', '動作']
  );
  assert.equal(CHARACTER_INSPECTOR_SECTIONS[0].enabled, true);
  assert.equal(CHARACTER_INSPECTOR_SECTIONS[1].enabled, false);
  assert.equal(CHARACTER_INSPECTOR_SECTIONS[2].enabled, false);
  assert.equal(CHARACTER_INSPECTOR_SECTIONS[3].enabled, false);
}

function testBoneGroupsUseApprovedM17Bones() {
  assert.deepEqual(Object.keys(CHARACTER_INSPECTOR_BONE_GROUPS), ['center', 'body', 'arms', 'hands']);
  assert.deepEqual(getInspectorBonesForGroup('center'), ['hips']);
  assert.deepEqual(getInspectorBonesForGroup('body'), ['spine', 'chest']);
  assert.deepEqual(getInspectorBonesForGroup('arms'), [
    'leftUpperArm',
    'rightUpperArm',
    'leftLowerArm',
    'rightLowerArm',
  ]);
  assert.deepEqual(getInspectorBonesForGroup('hands'), ['leftHand', 'rightHand']);
  assert.deepEqual(getInspectorBonesForGroup('unknown'), [
    'hips',
    'spine',
    'chest',
    'leftUpperArm',
    'rightUpperArm',
    'leftLowerArm',
    'rightLowerArm',
    'leftHand',
    'rightHand',
  ]);
}

function testBoneLabelsKeepChineseAndHumanoidIds() {
  assert.equal(CHARACTER_INSPECTOR_BONE_LABELS.rightUpperArm, '右上臂 rightUpperArm');
  assert.equal(CHARACTER_INSPECTOR_BONE_LABELS.leftLowerArm, '左前臂 leftLowerArm');
  assert.equal(CHARACTER_INSPECTOR_BONE_LABELS.hips, '重心 hips');
  assert.equal(getInspectorBoneLabel('rightHand'), '右手 rightHand');
  assert.equal(getInspectorBoneLabel('unknownBone'), 'unknownBone');
}

function testIndexHtmlUsesCharacterInspectorCopy() {
  assert.match(indexHtml, /角色檢查器/);
  assert.match(indexHtml, /Character Inspector/);
  assert.match(indexHtml, /開發者模式/);
  assert.match(indexHtml, /複製 JSON/);
  assert.match(indexHtml, /儲存本機/);
  assert.match(indexHtml, /重設骨骼/);
  assert.match(indexHtml, /全部重設/);
  assert.doesNotMatch(indexHtml, />Reset Bone</);
  assert.doesNotMatch(indexHtml, />Reset All</);
  assert.doesNotMatch(indexHtml, />Save Local</);
  assert.doesNotMatch(indexHtml, />Pose Calibration</);
}

function testIndexHtmlKeepsInspectorContracts() {
  assert.match(indexHtml, /data-inspector-section="\$\{escapeHtml\(section\.id\)\}"/);
  assert.match(indexHtml, /\$\{section\.enabled \? '' : 'disabled'\}/);
  assert.match(indexHtml, /data-inspector-group="\$\{escapeHtml\(groupId\)\}"/);
  assert.match(indexHtml, /id="btnInspectorCopyJson"/);
  assert.match(indexHtml, /id="btnInspectorSaveLocal"/);
  assert.match(indexHtml, /id="btnInspectorResetBone"/);
  assert.match(indexHtml, /id="btnInspectorResetAll"/);
}

function testCssUsesCharacterInspectorNamespace() {
  assert.match(css, /\.character-inspector-container/);
  assert.match(css, /\.character-inspector-deck/);
  assert.match(css, /\.character-inspector-slider-list/);
  assert.doesNotMatch(css, /\.pose-calibration-container/);
}

const tests = [
  testSectionMetadataUsesChineseLabels,
  testBoneGroupsUseApprovedM17Bones,
  testBoneLabelsKeepChineseAndHumanoidIds,
  testIndexHtmlUsesCharacterInspectorCopy,
  testIndexHtmlKeepsInspectorContracts,
  testCssUsesCharacterInspectorNamespace,
];

for (const test of tests) {
  test();
  console.log(`PASS ${test.name}`);
}
