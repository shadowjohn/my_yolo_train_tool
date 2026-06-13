import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  PoseDirector,
  resolvePoseDirectiveForTrace,
} from '../my_vrm_mascot/js/PoseDirector.js';
import {
  getPosePresetUrlForModel,
  MotionController,
} from '../my_vrm_mascot/js/MotionController.js';
import { LookAtController } from '../my_vrm_mascot/js/LookAtController.js';

function createFakeControllers() {
  const calls = [];
  return {
    calls,
    motion: {
      play(name) {
        calls.push({ type: 'motion', name });
      },
    },
    expression: {
      set(name, weight, fadeSec) {
        calls.push({ type: 'expression', name, weight, fadeSec });
      },
    },
    lookAt: {
      setTarget(target, data) {
        calls.push({ type: 'lookAt', target, data });
      },
    },
  };
}

function createRotation() {
  return {
    x: 0,
    y: 0,
    z: 0,
    set(x, y, z) {
      this.x = x;
      this.y = y;
      this.z = z;
    },
  };
}

function createBone() {
  return {
    rotation: createRotation(),
    position: { x: 0, y: 1, z: 0 },
  };
}

function createFakeVrm() {
  const names = [
    'spine',
    'chest',
    'hips',
    'leftUpperArm',
    'leftLowerArm',
    'rightUpperArm',
    'rightLowerArm',
    'leftHand',
    'rightHand',
    'leftUpperLeg',
    'rightUpperLeg',
    'leftShoulder',
    'rightShoulder',
    'head',
    'neck',
  ];
  const bones = Object.fromEntries(names.map(name => [name, createBone()]));
  bones.hips.position.y = 1.2;

  return {
    bones,
    vrm: {
      humanoid: {
        getBoneNode(name) {
          return bones[name] || null;
        },
      },
    },
  };
}

function radians(deg) {
  return deg * Math.PI / 180;
}

function testRunningTraceResolvesPresentingPose() {
  const directive = resolvePoseDirectiveForTrace('execute_tool', { status: 'running' });

  assert.equal(directive.pose, 'presenting');
  assert.equal(directive.motion, 'presenting');
  assert.equal(directive.expression, 'fun');
  assert.equal(directive.lookAt.target, 'point');
}

function testDoneTraceResolvesWavePose() {
  const directive = resolvePoseDirectiveForTrace('execute_tool', { status: 'done' });

  assert.equal(directive.pose, 'wave');
  assert.equal(directive.motion, 'wave');
  assert.equal(directive.expression, 'joy');
}

function testPolicyBlockedTraceResolvesWarningPose() {
  const directive = resolvePoseDirectiveForTrace('policy_check', {
    status: 'blocked',
    reason: 'target_prefix_not_allowed',
  });

  assert.equal(directive.pose, 'warning');
  assert.equal(directive.motion, 'warning');
  assert.equal(directive.expression, 'angry');
}

function testTimeoutFailureResolvesShakeHeadPose() {
  const directive = resolvePoseDirectiveForTrace('execute_tool', {
    status: 'failed',
    reason: 'timeout',
  });

  assert.equal(directive.pose, 'shake_head');
  assert.equal(directive.motion, 'shake_head');
  assert.equal(directive.expression, 'sorrow');
}

function testPoseDirectorAppliesSemanticDirectiveToControllers() {
  const { calls, motion, expression, lookAt } = createFakeControllers();
  const director = new PoseDirector({ motion, expression, lookAt });

  const applied = director.poseForIntentResult('running');

  assert.equal(applied.pose, 'presenting');
  assert.deepEqual(calls, [
    { type: 'motion', name: 'presenting' },
    { type: 'expression', name: 'fun', weight: 0.45, fadeSec: 0.2 },
    { type: 'lookAt', target: 'point', data: { x: -0.45, y: 0.05 } },
  ]);
}

function testSetVrmAppliesNaturalPoseImmediately() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);

  assert.ok(Math.abs(bones.leftUpperArm.rotation.z) > radians(12), 'left arm should not remain in T-pose');
  assert.ok(Math.abs(bones.rightUpperArm.rotation.z) > radians(12), 'right arm should not remain in T-pose');
  assert.ok(Math.abs(bones.leftLowerArm.rotation.y) > radians(3), 'left elbow should have a natural bend');
  assert.ok(Math.abs(bones.rightLowerArm.rotation.y) > radians(3), 'right elbow should have a natural bend');
  assert.ok(Math.abs(bones.hips.position.x) > 0.001, 'hips should have a slight weight shift');
}

function testResetToNaturalPoseDoesNotZeroBones() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  for (const bone of Object.values(bones)) {
    bone.rotation.set(0, 0, 0);
  }
  bones.hips.position.x = 0;

  motion.resetToNaturalPose(0);

  assert.ok(Math.abs(bones.leftUpperArm.rotation.z) > radians(12));
  assert.ok(Math.abs(bones.rightUpperArm.rotation.z) > radians(12));
  assert.ok(Math.abs(bones.hips.position.x) > 0.001);
}

function testIdleBuildsOnNaturalPose() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  motion.update(0.5);

  assert.ok(Math.abs(bones.leftUpperArm.rotation.z) > radians(12));
  assert.ok(Math.abs(bones.rightUpperArm.rotation.z) > radians(12));
  assert.ok(Math.abs(bones.hips.position.x) > 0.001);
  assert.notEqual(bones.hips.position.y, 1.2);
}

function testIdleMicroMotionAddsBoundedLifeSignals() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  motion.loadPosePreset(JSON.parse(readFileSync('my_vrm_mascot/motions/poses/alicia_solid.json', 'utf8')));
  const natural = {
    hipsX: bones.hips.position.x,
    hipsY: bones.hips.position.y,
    spineX: bones.spine.rotation.x,
    chestX: bones.chest.rotation.x,
    leftShoulderZ: bones.leftShoulder.rotation.z,
    rightShoulderZ: bones.rightShoulder.rotation.z,
    leftLowerArmY: bones.leftLowerArm.rotation.y,
    rightLowerArmY: bones.rightLowerArm.rotation.y,
    leftHandZ: bones.leftHand.rotation.z,
    rightHandZ: bones.rightHand.rotation.z,
  };

  motion.update(0.75);

  assert.notEqual(bones.spine.rotation.x, natural.spineX, 'idle should add layered spine breathing');
  assert.notEqual(bones.chest.rotation.x, natural.chestX, 'idle should add layered chest breathing');
  assert.notEqual(bones.hips.position.x, natural.hipsX, 'idle should add tiny weight shift');
  assert.notEqual(bones.leftShoulder.rotation.z, natural.leftShoulderZ, 'idle should relax left shoulder');
  assert.notEqual(bones.rightShoulder.rotation.z, natural.rightShoulderZ, 'idle should relax right shoulder');
  assert.notEqual(bones.leftLowerArm.rotation.y, natural.leftLowerArmY, 'idle should add forearm micro motion');
  assert.notEqual(bones.rightLowerArm.rotation.y, natural.rightLowerArmY, 'idle should add forearm micro motion');
  assert.notEqual(bones.leftHand.rotation.z, natural.leftHandZ, 'idle should add wrist micro motion');
  assert.notEqual(bones.rightHand.rotation.z, natural.rightHandZ, 'idle should add wrist micro motion');

  assert.ok(Math.abs(bones.hips.position.x - natural.hipsX) <= 0.004);
  assert.ok(Math.abs(bones.hips.position.y - natural.hipsY) <= 0.004);
  assert.ok(Math.abs(bones.leftShoulder.rotation.z - natural.leftShoulderZ) <= radians(1.2));
  assert.ok(Math.abs(bones.rightShoulder.rotation.z - natural.rightShoulderZ) <= radians(1.2));
  assert.ok(Math.abs(bones.leftHand.rotation.z - natural.leftHandZ) <= radians(1));
  assert.ok(Math.abs(bones.rightHand.rotation.z - natural.rightHandZ) <= radians(1));
}

function testIdleMicroMotionDoesNotLeakIntoPresenting() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  motion.loadPosePreset(JSON.parse(readFileSync('my_vrm_mascot/motions/poses/alicia_solid.json', 'utf8')));
  const naturalLeftHandZ = bones.leftHand.rotation.z;
  const naturalLeftShoulderZ = bones.leftShoulder.rotation.z;

  motion.play('presenting');
  motion.update(0.75);

  assert.equal(bones.leftHand.rotation.z, naturalLeftHandZ);
  assert.equal(bones.leftShoulder.rotation.z, naturalLeftShoulderZ);
}

function testPresentingUsesRightHandOnly() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  motion.loadPosePreset(JSON.parse(readFileSync('my_vrm_mascot/motions/poses/alicia_solid.json', 'utf8')));
  const naturalLeftZ = bones.leftUpperArm.rotation.z;
  const naturalRightZ = bones.rightUpperArm.rotation.z;
  motion.play('presenting');
  motion.update(0.8);

  assert.ok(
    Math.abs(bones.leftUpperArm.rotation.z - naturalLeftZ) < radians(3),
    'presenting should keep the left arm close to the natural down pose'
  );
  assert.ok(
    Math.abs(bones.rightUpperArm.rotation.z - naturalRightZ) > radians(12),
    'presenting should use the right arm as the only active arm'
  );
  assert.ok(
    Math.abs(bones.rightUpperArm.rotation.z) > radians(30),
    'presenting should not lift the right arm close to a horizontal T-pose'
  );
}

function testLoadPosePresetUsesDegreeRotationAndHipsPosition() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  motion.loadPosePreset({
    model: 'TestModel',
    basePose: {
      rotation: {
        leftUpperArm: { x: 10, y: 0, z: 55 },
        rightUpperArm: { x: 10, y: 0, z: -55 },
      },
      position: {
        hips: { x: -0.02, y: 0.01, z: 0.03 },
      },
    },
  });

  assert.equal(bones.leftUpperArm.rotation.x, radians(10));
  assert.equal(bones.leftUpperArm.rotation.z, radians(55));
  assert.equal(bones.rightUpperArm.rotation.z, radians(-55));
  assert.equal(bones.hips.position.x, -0.02);
  assert.equal(bones.hips.position.y, 1.21);
  assert.equal(bones.hips.position.z, 0.03);
}

function testSetBasePoseRotationUpdatesPresetAndCurrentPose() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  motion.setBasePoseRotation('leftLowerArm', 'y', -22);

  const preset = motion.getPosePreset();
  assert.equal(preset.basePose.rotation.leftLowerArm.y, -22);
  assert.equal(bones.leftLowerArm.rotation.y, radians(-22));
}

function testSetBasePosePositionKeepsHipsSeparateFromRotation() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  motion.setBasePosePosition('hips', 'x', -0.031);

  const preset = motion.getPosePreset();
  assert.equal(preset.basePose.position.hips.x, -0.031);
  assert.equal(preset.basePose.rotation.hips, undefined);
  assert.equal(bones.hips.position.x, -0.031);
}

function testResetBasePoseBoneRestoresDefaultPose() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  const initialZ = bones.leftUpperArm.rotation.z;
  motion.setBasePoseRotation('leftUpperArm', 'z', 70);
  motion.resetBasePoseBone('leftUpperArm');

  assert.equal(bones.leftUpperArm.rotation.z, initialZ);
  assert.equal(motion.getPosePreset().basePose.rotation.leftUpperArm.z, 42);
}

function testMascotModelUsesAliciaPosePreset() {
  assert.equal(
    getPosePresetUrlForModel('models/mascot.vrm'),
    'motions/poses/alicia_solid.json'
  );
}

function testUnknownModelFallsBackToDefaultPosePreset() {
  assert.equal(
    getPosePresetUrlForModel('models/custom_character.vrm'),
    'motions/poses/default.json'
  );
}

function testAliciaPresetKeepsArmsAwayFromTPose() {
  const motion = new MotionController();
  const { vrm, bones } = createFakeVrm();

  motion.setVrm(vrm);
  motion.loadPosePreset({
    model: 'AliciaSolid',
    basePose: {
      rotation: {
        leftUpperArm: { x: 9, y: -3, z: 54 },
        rightUpperArm: { x: 9, y: 3, z: -54 },
        leftLowerArm: { x: 1, y: -14, z: -5 },
        rightLowerArm: { x: 1, y: 14, z: 5 },
      },
      position: {
        hips: { x: -0.014, y: 0, z: 0.004 },
      },
    },
  });

  assert.ok(bones.leftUpperArm.rotation.z > radians(45));
  assert.ok(bones.rightUpperArm.rotation.z < radians(-45));
  assert.ok(Math.abs(bones.leftLowerArm.rotation.y) > radians(8));
  assert.ok(Math.abs(bones.rightLowerArm.rotation.y) > radians(8));
  assert.ok(Math.abs(bones.hips.position.x) > 0.01);
}

function testAliciaPresetFileIsModelSpecificAndNatural() {
  const preset = JSON.parse(readFileSync('my_vrm_mascot/motions/poses/alicia_solid.json', 'utf8'));
  const rotation = preset.basePose.rotation;

  assert.equal(preset.model, 'AliciaSolid');
  assert.ok(rotation.leftUpperArm.z > 45, 'Alicia left upper arm should hang down from bind pose');
  assert.ok(rotation.rightUpperArm.z < -45, 'Alicia right upper arm should hang down from bind pose');
  assert.ok(Math.abs(rotation.leftLowerArm.y) > 8, 'Alicia left elbow should have a relaxed bend');
  assert.ok(Math.abs(rotation.rightLowerArm.y) > 8, 'Alicia right elbow should have a relaxed bend');
  assert.ok(Math.abs(preset.basePose.position.hips.x) > 0.01, 'Alicia hips should have a visible weight shift');
}

function testVrmMascotLoadsModelSpecificPosePresetWithFileLoader() {
  const source = readFileSync('my_vrm_mascot/js/VrmMascot.js', 'utf8');

  assert.match(source, /getPosePresetUrlForModel/);
  assert.match(source, /#loadPosePresetForModel\(url\)/);
  assert.match(source, /new THREE\.FileLoader\(\)/);
  assert.doesNotMatch(source, /fetch\([^)]*pose/i);
}

function testLookAtNoneAddsBoundedIdleHeadDrift() {
  const lookAt = new LookAtController();
  const { vrm, bones } = createFakeVrm();

  lookAt.setVrm(vrm);
  lookAt.setTarget('none');
  lookAt.update(0.75);

  assert.notEqual(bones.head.rotation.x, 0);
  assert.notEqual(bones.head.rotation.y, 0);
  assert.notEqual(bones.neck.rotation.x, 0);
  assert.ok(Math.abs(bones.head.rotation.x) <= radians(1.2));
  assert.ok(Math.abs(bones.head.rotation.y) <= radians(1.4));
  assert.ok(Math.abs(bones.neck.rotation.x) <= radians(0.5));
}

function testLookAtPointDoesNotUseIdleDriftMode() {
  const lookAt = new LookAtController();
  const { vrm, bones } = createFakeVrm();

  lookAt.setVrm(vrm);
  lookAt.setTarget('point', { x: 0.5, y: 0 });
  lookAt.update(0.75);

  assert.ok(bones.head.rotation.y > radians(0.5));
  assert.equal(bones.head.rotation.z, 0);
}

const tests = [
  testRunningTraceResolvesPresentingPose,
  testDoneTraceResolvesWavePose,
  testPolicyBlockedTraceResolvesWarningPose,
  testTimeoutFailureResolvesShakeHeadPose,
  testPoseDirectorAppliesSemanticDirectiveToControllers,
  testSetVrmAppliesNaturalPoseImmediately,
  testResetToNaturalPoseDoesNotZeroBones,
  testIdleBuildsOnNaturalPose,
  testIdleMicroMotionAddsBoundedLifeSignals,
  testIdleMicroMotionDoesNotLeakIntoPresenting,
  testPresentingUsesRightHandOnly,
  testLoadPosePresetUsesDegreeRotationAndHipsPosition,
  testSetBasePoseRotationUpdatesPresetAndCurrentPose,
  testSetBasePosePositionKeepsHipsSeparateFromRotation,
  testResetBasePoseBoneRestoresDefaultPose,
  testMascotModelUsesAliciaPosePreset,
  testUnknownModelFallsBackToDefaultPosePreset,
  testAliciaPresetKeepsArmsAwayFromTPose,
  testAliciaPresetFileIsModelSpecificAndNatural,
  testVrmMascotLoadsModelSpecificPosePresetWithFileLoader,
  testLookAtNoneAddsBoundedIdleHeadDrift,
  testLookAtPointDoesNotUseIdleDriftMode,
];

for (const test of tests) {
  test();
  console.log(`PASS ${test.name}`);
}
