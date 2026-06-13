import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const SPEC_PATH = 'docs/superpowers/specs/2026-06-13-m6-7-motion-template-importer-design.md';
const LAB_PATH = 'my_vrm_mascot/motion_template_lab.html';
const MODULE_PATH = 'my_vrm_mascot/js/MotionTemplateImporter.js';
const INDEX_PATH = 'my_vrm_mascot/index.html';
const EXAMPLE_DIR = 'my_vrm_mascot/examples/m6_7_vrma_samples';
const REQUIRED_EXAMPLE_VRMA = [
  'Angry.vrma',
  'Clapping.vrma',
  'Goodbye.vrma',
  'Jump.vrma',
  'LookAround.vrma',
  'Relax.vrma',
  'Sad.vrma',
  'Sleepy.vrma',
  'Surprised.vrma',
  'Thinking.vrma',
];
const MINING_LOG_PATH = 'my_vrm_mascot/examples/m6_7_motion_mining/mining_log.json';
const MINING_REPORT_PATH = 'my_vrm_mascot/examples/m6_7_motion_mining/mining_report.json';

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
  assert.match(html, /Alicia Motion Mine/);
  assert.match(html, /先找好姿勢，再分類/);
  assert.match(html, /載入 VRMA/);
  assert.match(html, /取第一幀/);
  assert.match(html, /取目前時間/);
  assert.match(html, /複製 JSON/);
  assert.match(html, /下載 JSON/);
  assert.match(html, /匯出 NaturalPosePreset/);
  assert.match(html, /Upper Body/);
  assert.match(html, /鎖定下半身/);
  assert.match(html, /motion-template-json/);
}

function testExampleVrmaSamplesExist() {
  for (const fileName of REQUIRED_EXAMPLE_VRMA) {
    const path = `${EXAMPLE_DIR}/${fileName}`;
    assert.equal(existsSync(path), true, `${path} should exist`);

    const header = readFileSync(path).subarray(0, 4).toString('ascii');
    assert.equal(header, 'glTF', `${path} should be a binary glTF/VRMA file`);
  }
}

function testLabIncludesExampleAndPlaybackControls() {
  const html = read(LAB_PATH);

  assert.match(html, /範例動作/);
  assert.match(html, /載入範例/);
  for (const fileName of REQUIRED_EXAMPLE_VRMA) {
    assert.match(html, new RegExp(fileName.replace('.', '\\.')));
  }
  assert.match(html, /播放/);
  assert.match(html, /暫停/);
  assert.match(html, /停止/);
  assert.match(html, /examples\/m6_7_vrma_samples\//);
  assert.match(html, /function\s+playMotion\s*\(/);
  assert.match(html, /function\s+pauseMotion\s*\(/);
  assert.match(html, /function\s+stopPlayback\s*\(/);
  assert.match(html, /function\s+applyLowerBodyPreviewLock\s*\(/);
  assert.match(html, /isPlaying\s*&&\s*mixer/);
  assert.match(html, /mixer\.update\(dt\)/);
  assert.match(html, /applyLowerBodyPreviewLock\(\)/);
  assert.match(html, /startTime\s*>=\s*duration\s*-\s*0\.034/);
}

function testMotionMiningLogHasSprintReviewedSamples() {
  assert.equal(existsSync(MINING_LOG_PATH), true, `${MINING_LOG_PATH} should exist`);

  const log = JSON.parse(read(MINING_LOG_PATH));
  assert.ok(log.length >= 50, 'mining log should keep the first sprint above 50 samples');
  assert.equal(new Set(log.map((entry) => entry.source)).size, 10);

  for (const source of REQUIRED_EXAMPLE_VRMA) {
    assert.ok(log.filter((entry) => entry.source === source).length >= 5, `${source} should have at least 5 mined samples`);
  }

  for (const entry of log) {
    assert.match(entry.id, /^(present|point|think|warning|success|reject|candidate_future)_\d{3}$/);
    assert.equal(REQUIRED_EXAMPLE_VRMA.includes(entry.source), true);
    assert.equal(typeof entry.sampleTime, 'number');
    assert.ok(entry.sampleTime >= 0);
    assert.match(entry.createdAt, /^2026-06-(13|14)T\d{2}:\d{2}:\d{2}\+08:00$/);
    assert.equal(Array.isArray(entry.tags), true);
    assert.equal(entry.tags.length > 0, true);
    assert.equal(typeof entry.sourceScore, 'number');
    assert.equal(typeof entry.agentScore, 'number');
    assert.ok(entry.sourceScore >= 1 && entry.sourceScore <= 5);
    assert.ok(entry.agentScore >= 1 && entry.agentScore <= 5);

    if (entry.category === 'reject') {
      assert.equal(typeof entry.rejectReason, 'string');
      assert.equal(entry.exportedPoseFile, undefined);
    } else if (entry.category === 'candidate_future') {
      assert.equal(typeof entry.reason, 'string');
      assert.equal(entry.exportedPoseFile, `${entry.id}.json`);
    } else {
      assert.equal(entry.exportedPoseFile, `${entry.id}.json`);
    }
  }
}

function testMotionMiningReportMatchesLog() {
  assert.equal(existsSync(MINING_REPORT_PATH), true, `${MINING_REPORT_PATH} should exist`);

  const log = JSON.parse(read(MINING_LOG_PATH));
  const report = JSON.parse(read(MINING_REPORT_PATH));
  const categoryCounts = {};
  const sourceCounts = {};
  const reasonCounts = {};

  for (const entry of log) {
    categoryCounts[entry.category] = (categoryCounts[entry.category] || 0) + 1;
    sourceCounts[entry.source] = (sourceCounts[entry.source] || 0) + 1;
    const reason = entry.reason || entry.rejectReason;
    if (reason) {
      reasonCounts[reason] = (reasonCounts[reason] || 0) + 1;
    }
  }

  assert.equal(report.sprint, 'Motion Mining Sprint 001');
  assert.equal(report.generatedFrom, 'mining_log.json');
  assert.equal(report.totalEntries, log.length);
  assert.equal(report.sourceCount, REQUIRED_EXAMPLE_VRMA.length);
  assert.deepEqual(report.categoryCounts, categoryCounts);
  assert.deepEqual(report.sourceCounts, sourceCounts);
  assert.deepEqual(report.reasonCounts, reasonCounts);
  assert.equal(report.rankings.categoryByCount[0].category, 'think');
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

async function testLowerBodyPreviewLockIsExplicitAndSeparateFromExportScope() {
  const mod = await importImporterModule();

  assert.deepEqual(mod.LOWER_BODY_PREVIEW_LOCK_BONES, [
    'hips',
    'leftUpperLeg',
    'rightUpperLeg',
    'leftLowerLeg',
    'rightLowerLeg',
    'leftFoot',
    'rightFoot',
    'leftToes',
    'rightToes',
  ]);

  for (const bone of mod.LOWER_BODY_PREVIEW_LOCK_BONES) {
    assert.equal(mod.UPPER_BODY_BONES.includes(bone), false, `${bone} must not be exported as upper body`);
  }
}

async function testMotionMiningSchemaBuildsCandidateAndRejectEntries() {
  const mod = await importImporterModule();

  assert.deepEqual(mod.MOTION_MINING_CATEGORIES, [
    'present',
    'point',
    'think',
    'warning',
    'success',
    'candidate_future',
    'reject',
  ]);
  assert.deepEqual(mod.MOTION_MINING_REJECT_REASONS, [
    'too_large_motion',
    'hands_cover_face',
    'off_balance',
    'too_dance_like',
    'bad_silhouette',
    'arm_cross_body',
    'not_agentic',
    'costume_clip',
    'unclear_intent',
    'requires_lower_body',
    'requires_hips',
    'requires_weight_shift',
    'requires_locomotion',
  ]);

  const candidate = mod.buildMotionMiningEntry({
    source: 'Relax.vrma',
    sampleTime: 0.46234,
    category: 'present',
    score: 5,
    sourceScore: 4,
    agentScore: 5,
    note: '雙手自然打開，適合介紹',
    tags: 'upper_body, agent_friendly',
    sequence: 1,
    createdAt: '2026-06-13T12:00:00+08:00',
  });

  assert.deepEqual(candidate, {
    id: 'present_001',
    source: 'Relax.vrma',
    sampleTime: 0.4623,
    category: 'present',
    score: 5,
    sourceScore: 4,
    agentScore: 5,
    note: '雙手自然打開，適合介紹',
    tags: ['upper_body', 'agent_friendly'],
    exportedPoseFile: 'present_001.json',
    createdAt: '2026-06-13T12:00:00+08:00',
  });

  const reject = mod.buildMotionMiningEntry({
    source: 'Clapping.vrma',
    sampleTime: 1.2,
    category: 'reject',
    score: 2,
    sourceScore: 3,
    agentScore: 1,
    rejectReason: 'hands_cover_face',
    note: '手遮住臉，但手腕角度可參考',
    tags: 'negative_sample',
    sequence: 3,
    createdAt: '2026-06-13T12:10:00+08:00',
  });

  assert.deepEqual(reject, {
    id: 'reject_003',
    source: 'Clapping.vrma',
    sampleTime: 1.2,
    category: 'reject',
    score: 2,
    sourceScore: 3,
    agentScore: 1,
    rejectReason: 'hands_cover_face',
    note: '手遮住臉，但手腕角度可參考',
    tags: ['negative_sample'],
    createdAt: '2026-06-13T12:10:00+08:00',
  });

  const future = mod.buildMotionMiningEntry({
    source: 'Jump.vrma',
    sampleTime: 1.419,
    category: 'candidate_future',
    score: 4,
    sourceScore: 5,
    agentScore: 2,
    reason: 'requires_weight_shift',
    note: '原始重心很好，但 Agent Pose 鎖下半身後失衡。',
    tags: 'future_candidate, locomotion',
    sequence: 2,
    createdAt: '2026-06-13T12:20:00+08:00',
  });

  assert.deepEqual(future, {
    id: 'candidate_future_002',
    source: 'Jump.vrma',
    sampleTime: 1.419,
    category: 'candidate_future',
    score: 4,
    sourceScore: 5,
    agentScore: 2,
    reason: 'requires_weight_shift',
    note: '原始重心很好，但 Agent Pose 鎖下半身後失衡。',
    tags: ['future_candidate', 'locomotion'],
    exportedPoseFile: 'candidate_future_002.json',
    createdAt: '2026-06-13T12:20:00+08:00',
  });
}

function testLabIncludesMotionMiningWorkbenchControls() {
  const html = read(LAB_PATH);

  assert.match(html, /Preview Mode/);
  assert.match(html, /id="previewModeOriginal"/);
  assert.match(html, /id="previewModeAgent"/);
  assert.match(html, /id="previewModeLabel"/);
  assert.match(html, /function\s+applyPreviewMode\s*\(/);
  assert.match(html, /function\s+refreshCurrentFrame\s*\(/);
  assert.match(html, /Alicia Motion Mine/);
  assert.match(html, /id="minerAdvancedTools"/);
  assert.match(html, /id="miningCategory"/);
  assert.match(html, /id="miningScore"/);
  assert.match(html, /id="miningSourceScore"/);
  assert.match(html, /id="miningAgentScore"/);
  assert.match(html, /id="miningFutureReason"/);
  assert.match(html, /id="miningRejectReason"/);
  assert.match(html, /id="miningNote"/);
  assert.match(html, /id="miningTags"/);
  assert.match(html, /id="btnAddMiningCandidate"/);
  assert.match(html, /id="btnExportMiningLog"/);
  assert.match(html, /id="miningCandidateList"/);
  assert.match(html, /function\s+addMiningCandidate\s*\(/);
  assert.match(html, /function\s+downloadMiningLog\s*\(/);
  assert.match(html, /mining_log\.json/);
  assert.doesNotMatch(html, /innerHTML/);
}

function testLabIncludesQuickReviewModeControls() {
  const html = read(LAB_PATH);

  assert.match(html, /Quick Review Mode/);
  assert.match(html, /快速標註/);
  assert.match(html, /id="quickReviewPanel"/);
  assert.match(html, /id="quickReviewPresent"/);
  assert.match(html, /id="quickReviewPoint"/);
  assert.match(html, /id="quickReviewThink"/);
  assert.match(html, /id="quickReviewWarning"/);
  assert.match(html, /id="quickReviewSuccess"/);
  assert.match(html, /id="quickReviewFuture"/);
  assert.match(html, /id="quickReviewReject"/);
  assert.match(html, /data-quick-key="Q"/);
  assert.match(html, /data-quick-key="W"/);
  assert.match(html, /data-quick-key="E"/);
  assert.match(html, /data-quick-key="R"/);
  assert.match(html, /data-quick-key="T"/);
  assert.match(html, /data-quick-key="C"/);
  assert.match(html, /data-quick-key="X"/);
  assert.match(html, /id="advancedMiningDetails"/);
  assert.match(html, /function\s+addQuickReviewCandidate\s*\(/);
  assert.match(html, /function\s+getQuickReviewPreset\s*\(/);
  assert.match(html, /function\s+handleQuickReviewKeydown\s*\(/);
  assert.match(html, /function\s+isQuickReviewEditableTarget\s*\(/);
  assert.match(html, /event\.repeat/);
  assert.match(html, /event\.ctrlKey/);
  assert.match(html, /event\.metaKey/);
  assert.match(html, /event\.altKey/);
  assert.match(html, /category:\s*'candidate_future'[\s\S]*reason:\s*'requires_weight_shift'/);
  assert.match(html, /category:\s*'reject'[\s\S]*rejectReason:\s*'unclear_intent'/);
}

function testLabGuardsAccidentalDuplicateMiningEntries() {
  const html = read(LAB_PATH);

  assert.match(html, /id="btnUndoMiningCandidate"/);
  assert.match(html, /function\s+findDuplicateMiningEntry\s*\(/);
  assert.match(html, /function\s+addMiningEntry\s*\(/);
  assert.match(html, /function\s+undoLastMiningCandidate\s*\(/);
  assert.match(html, /findDuplicateMiningEntry\(entry\)/);
  assert.match(html, /已略過重複候選/);
  assert.match(html, /miningEntries\.pop\(\)/);
  assert.match(html, /已撤銷/);
  assert.match(html, /btnUndoMiningCandidate\.addEventListener/);
}

function testLabIncludesReviewQueueControls() {
  const html = read(LAB_PATH);

  assert.match(html, /id="reviewQueuePanel"/);
  assert.match(html, /審核清單/);
  assert.match(html, /id="btnGenerateReviewQueue"/);
  assert.match(html, /id="reviewQueueFilter"/);
  assert.match(html, /id="btnReviewPrevious"/);
  assert.match(html, /id="btnReviewNext"/);
  assert.match(html, /id="reviewQueueList"/);
  assert.match(html, /function\s+buildReviewQueueItems\s*\(/);
  assert.match(html, /function\s+selectReviewQueueItem\s*\(/);
  assert.match(html, /function\s+classifySelectedReviewItem\s*\(/);
}

function testReviewQueueUsesChineseFirstLabels() {
  const html = read(LAB_PATH);

  assert.match(html, /待分類/);
  assert.match(html, /已分類/);
  assert.match(html, /全部/);
  assert.match(html, /產生清單/);
  assert.match(html, /上一筆/);
  assert.match(html, /下一筆/);
  assert.doesNotMatch(html, />\s*Generate Queue\s*</);
  assert.doesNotMatch(html, />\s*Pending\s*</);
  assert.doesNotMatch(html, />\s*Classified\s*</);
}

function testReviewQueueSchemaAndBehaviorContracts() {
  const html = read(LAB_PATH);

  assert.match(html, /const\s+MINING_CATEGORIES\s*=/);
  assert.match(html, /status:\s*'pending'/);
  assert.match(html, /status:\s*'classified'/);
  assert.match(html, /duration\s*-\s*0\.001/);
  assert.match(html, /selectedReviewQueueId/);
  assert.match(html, /updatedAt/);
  assert.match(html, /reviewActionHistory/);
  assert.match(html, /entry\.status\s*===\s*'classified'/);
}

function testLabUsesAliciaMotionMineManagerUi() {
  const html = read(LAB_PATH);

  assert.match(html, /Alicia Motion Mine/);
  assert.match(html, /先找好姿勢，再分類/);
  assert.match(html, /礦區/);
  assert.match(html, /候選片段/);
  assert.match(html, /id="mineList"/);
  assert.match(html, /id="pinnedCandidateList"/);
  assert.match(html, /id="btnPinMoment"/);
  assert.match(html, /id="minerCurrentSample"/);
  assert.match(html, /id="minerProgressText"/);
  assert.match(html, /id="minerProgressBar"/);
  assert.match(html, /id="sourceVrmaCount"/);
  assert.match(html, /id="pinnedCandidateCount"/);
  assert.match(html, /id="classifiedCandidateCount"/);
  assert.match(html, /id="minerAdvancedTools"/);
  assert.match(html, /進階工具/);
  assert.match(html, /只顯示必要資訊/);
  assert.doesNotMatch(html, />\s*Motion Mining Workbench\s*</);
}

function testLabIncludesRuleBasedMiningSuggestion() {
  const html = read(LAB_PATH);

  assert.match(html, /id="miningSuggestionPanel"/);
  assert.match(html, /自動推薦/);
  assert.match(html, /id="suggestedCategoryLabel"/);
  assert.match(html, /id="suggestionConfidence"/);
  assert.match(html, /id="suggestionReason"/);
  assert.match(html, /function\s+suggestMiningCategory\s*\(/);
  assert.match(html, /function\s+extractPoseFeatures\s*\(/);
  assert.match(html, /handNearFace/);
  assert.match(html, /headDown/);
  assert.match(html, /armExtended/);
  assert.match(html, /setRecommendedCategory/);
  assert.ok(
    html.indexOf("source.includes('angry')") < html.indexOf("source.includes('thinking')"),
    'Angry source heuristic should recommend warning before generic thinking posture rules',
  );
}

function testLabUsesPinThenClassifyMiningFlow() {
  const html = read(LAB_PATH);

  assert.doesNotMatch(html, /const\s+MINER_AUTO_ADVANCE/);
  assert.doesNotMatch(html, /generateReviewQueue\(\{\s*silent:\s*true\s*\}\)/);
  assert.doesNotMatch(html, /await\s+advanceToNextPendingReviewItem\(''\)/);
  assert.match(html, /function\s+renderMineList\s*\(/);
  assert.match(html, /function\s+pinCurrentMoment\s*\(/);
  assert.match(html, /function\s+renderPinnedCandidates\s*\(/);
  assert.match(html, /function\s+selectPinnedCandidate\s*\(/);
  assert.match(html, /釘選這一刻/);
  assert.match(html, /建議取樣點/);
  assert.match(html, /event\.key\s*===\s*' '/);
  assert.match(html, /event\.key\s*===\s*'ArrowRight'/);
  assert.match(html, /event\.key\.toUpperCase\(\)\s*===\s*'P'/);
  assert.match(html, /event\.key\.toUpperCase\(\)\s*===\s*'Z'/);
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
  const { clampSampleTime, SAMPLE_TIME_EPSILON } = await importImporterModule();

  assert.equal(clampSampleTime(-1, 2), 0);
  assert.equal(clampSampleTime(3, 2), 2 - SAMPLE_TIME_EPSILON);
  assert.equal(clampSampleTime(1.23456, 2), 1.23456);
  assert.equal(clampSampleTime(Number.NaN, 2), 0);
}

async function testClampSampleTimeAvoidsDurationLoopBoundary() {
  const { clampSampleTime, SAMPLE_TIME_EPSILON } = await importImporterModule();

  const duration = 2;
  const safeLastFrame = duration - SAMPLE_TIME_EPSILON;

  assert.equal(clampSampleTime(duration, duration), safeLastFrame);
  assert.equal(clampSampleTime(duration + 1, duration), safeLastFrame);
  assert.equal(clampSampleTime(safeLastFrame, duration), safeLastFrame);
}

async function run() {
  const tests = [
    testSpecRequiresDeterministicExport,
    testLabHtmlContractExists,
    testExampleVrmaSamplesExist,
    testLabIncludesExampleAndPlaybackControls,
    testLabReferencesVrmaCapabilityOnlyInLab,
    testLabDoesNotImportAgentRuntime,
    testUpperBodyWhitelistIsExplicitAndStable,
    testLowerBodyPreviewLockIsExplicitAndSeparateFromExportScope,
    testMotionMiningSchemaBuildsCandidateAndRejectEntries,
    testLabIncludesMotionMiningWorkbenchControls,
    testLabIncludesQuickReviewModeControls,
    testLabGuardsAccidentalDuplicateMiningEntries,
    testLabIncludesReviewQueueControls,
    testReviewQueueUsesChineseFirstLabels,
    testReviewQueueSchemaAndBehaviorContracts,
    testLabUsesAliciaMotionMineManagerUi,
    testLabIncludesRuleBasedMiningSuggestion,
    testLabUsesPinThenClassifyMiningFlow,
    testMotionMiningLogHasSprintReviewedSamples,
    testMotionMiningReportMatchesLog,
    testBuildNaturalPosePresetMergesUpperBodyOnly,
    testStableExportIsDeterministic,
    testClampSampleTime,
    testClampSampleTimeAvoidsDurationLoopBoundary,
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
