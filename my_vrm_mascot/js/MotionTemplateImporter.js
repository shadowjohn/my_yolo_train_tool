export const UPPER_BODY_BONES = Object.freeze([
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

export const DEFAULT_EXPORT_PRECISION = 2;

const UPPER_BODY_BONE_SET = new Set(UPPER_BODY_BONES);

export function clampSampleTime(value, duration = 0) {
  const numeric = Number(value);
  const max = Number.isFinite(Number(duration)) && Number(duration) > 0 ? Number(duration) : 0;
  if (!Number.isFinite(numeric) || numeric <= 0) return 0;
  if (numeric >= max) return max;
  return numeric;
}

export function roundDegrees(value, precision = DEFAULT_EXPORT_PRECISION) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 0;
  const factor = 10 ** precision;
  const rounded = Math.round((numeric + Number.EPSILON) * factor) / factor;
  return Object.is(rounded, -0) ? 0 : rounded;
}

export function normalizeRotation(rotation = {}, precision = DEFAULT_EXPORT_PRECISION) {
  return {
    x: roundDegrees(rotation.x, precision),
    y: roundDegrees(rotation.y, precision),
    z: roundDegrees(rotation.z, precision),
  };
}

export function normalizeRotationMap(rotations = {}, precision = DEFAULT_EXPORT_PRECISION) {
  const result = {};

  for (const bone of UPPER_BODY_BONES) {
    if (!Object.prototype.hasOwnProperty.call(rotations, bone)) continue;
    result[bone] = normalizeRotation(rotations[bone], precision);
  }

  return result;
}

export function buildNaturalPosePreset({
  basePreset = {},
  rotations = {},
  source = {},
  warnings = [],
  precision = DEFAULT_EXPORT_PRECISION,
} = {}) {
  const basePose = basePreset.basePose || {};
  const baseRotation = basePose.rotation || {};
  const basePosition = basePose.position || {};
  const importedRotations = normalizeRotationMap(rotations, precision);
  const mergedRotation = {};

  for (const bone of Object.keys(baseRotation).sort()) {
    if (UPPER_BODY_BONE_SET.has(bone) && importedRotations[bone]) {
      continue;
    }
    mergedRotation[bone] = normalizeRotation(baseRotation[bone], precision);
  }

  for (const bone of UPPER_BODY_BONES) {
    if (!importedRotations[bone]) continue;
    mergedRotation[bone] = importedRotations[bone];
  }

  return sortObjectDeep({
    model: basePreset.model || 'AliciaSolid',
    source: normalizeSource(source, warnings),
    basePose: {
      rotation: mergedRotation,
      position: clonePosition(basePosition, precision),
    },
  });
}

export function stableStringifyPreset(preset) {
  return JSON.stringify(sortObjectDeep(preset), null, 2);
}

function normalizeSource(source = {}, warnings = []) {
  const normalizedWarnings = Array.from(new Set(
    (Array.isArray(warnings) ? warnings : [])
      .map((item) => String(item || '').trim())
      .filter(Boolean),
  )).sort();

  return sortObjectDeep({
    type: String(source.type || 'vrma'),
    fileName: String(source.fileName || ''),
    sampleTime: roundDegrees(source.sampleTime || 0, 4),
    boneScope: 'upper_body',
    warnings: normalizedWarnings,
  });
}

function clonePosition(position = {}, precision = DEFAULT_EXPORT_PRECISION) {
  const result = {};

  for (const bone of Object.keys(position).sort()) {
    const value = position[bone] || {};
    result[bone] = {
      x: roundDegrees(value.x, precision + 3),
      y: roundDegrees(value.y, precision + 3),
      z: roundDegrees(value.z, precision + 3),
    };
  }

  return result;
}

function sortObjectDeep(value) {
  if (Array.isArray(value)) {
    return value.map((item) => sortObjectDeep(item));
  }

  if (!value || typeof value !== 'object') {
    return value;
  }

  return Object.keys(value)
    .sort()
    .reduce((acc, key) => {
      acc[key] = sortObjectDeep(value[key]);
      return acc;
    }, {});
}
