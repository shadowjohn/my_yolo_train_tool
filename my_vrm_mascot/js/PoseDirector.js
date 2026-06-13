/**
 * PoseDirector — Agent 狀態到 VRM 表現層的語意姿勢映射。
 *
 * 這層只理解「running / done / blocked」這類語意狀態，
 * 不知道 ToolRegistry、PolicyGate 或骨架細節，避免 Agent Runtime 與 Renderer 耦合。
 */

const DEFAULT_DIRECTIVES = {
  thinking: {
    pose: 'think',
    motion: 'think',
    expression: 'sorrow',
    expressionWeight: 0.3,
    fadeSec: 0.25,
    lookAt: { target: 'mouse' },
  },
  pending: {
    pose: 'think',
    motion: 'think',
    expression: 'sorrow',
    expressionWeight: 0.3,
    fadeSec: 0.25,
    lookAt: { target: 'mouse' },
  },
  running: {
    pose: 'presenting',
    motion: 'presenting',
    expression: 'fun',
    expressionWeight: 0.45,
    fadeSec: 0.2,
    lookAt: { target: 'point', data: { x: -0.45, y: 0.05 } },
  },
  done: {
    pose: 'wave',
    motion: 'wave',
    expression: 'joy',
    expressionWeight: 0.75,
    fadeSec: 0.2,
    lookAt: { target: 'mouse' },
  },
  blocked: {
    pose: 'warning',
    motion: 'warning',
    expression: 'angry',
    expressionWeight: 0.65,
    fadeSec: 0.2,
    lookAt: { target: 'mouse' },
  },
  warning: {
    pose: 'warning',
    motion: 'warning',
    expression: 'angry',
    expressionWeight: 0.65,
    fadeSec: 0.2,
    lookAt: { target: 'mouse' },
  },
  failed: {
    pose: 'shake_head',
    motion: 'shake_head',
    expression: 'sorrow',
    expressionWeight: 0.65,
    fadeSec: 0.2,
    lookAt: { target: 'mouse' },
  },
};

function cloneDirective(directive, meta = {}) {
  if (!directive) return null;
  return {
    ...directive,
    lookAt: directive.lookAt
      ? {
          ...directive.lookAt,
          data: directive.lookAt.data ? { ...directive.lookAt.data } : undefined,
        }
      : undefined,
    meta: { ...meta },
  };
}

function normalizeStateName(state) {
  const value = String(state || '').toLowerCase();
  if (value === 'timeout' || value === 'error') return 'failed';
  if (value === 'blocked') return 'blocked';
  if (value === 'warning') return 'warning';
  return value;
}

/**
 * 依語意狀態取得姿勢指令。
 * @param {string} state
 * @param {object} [meta]
 * @returns {object|null}
 */
export function resolvePoseDirectiveForState(state, meta = {}) {
  return cloneDirective(DEFAULT_DIRECTIVES[normalizeStateName(state)], meta);
}

/**
 * 依 trace step + patch 推導姿勢指令。
 * @param {string} step
 * @param {object} [patch]
 * @param {object} [intentObj]
 * @returns {object|null}
 */
export function resolvePoseDirectiveForTrace(step, patch = {}, intentObj = {}) {
  const status = normalizeStateName(patch.status);
  if (!status) return null;

  if (step === 'policy_check' && status === 'blocked') {
    return resolvePoseDirectiveForState('blocked', {
      step,
      status,
      reason: patch.reason,
      action: intentObj.action,
      tool: intentObj.tool,
    });
  }

  if (step !== 'execute_tool') {
    return null;
  }

  if (status === 'pending') {
    return resolvePoseDirectiveForState('pending', {
      step,
      status,
      action: intentObj.action,
      tool: intentObj.tool,
    });
  }

  if (status === 'running') {
    return resolvePoseDirectiveForState('running', {
      step,
      status,
      action: intentObj.action,
      tool: intentObj.tool,
    });
  }

  if (status === 'done') {
    return resolvePoseDirectiveForState('done', {
      step,
      status,
      action: intentObj.action,
      tool: intentObj.tool,
    });
  }

  if (status === 'failed') {
    return resolvePoseDirectiveForState('failed', {
      step,
      status,
      reason: patch.reason,
      action: intentObj.action,
      tool: intentObj.tool,
    });
  }

  return null;
}

export class PoseDirector {
  #motion = null;
  #expression = null;
  #lookAt = null;
  #lastPose = 'none';

  constructor(controllers = {}) {
    this.setControllers(controllers);
  }

  setControllers(controllers = {}) {
    this.#motion = controllers.motion || null;
    this.#expression = controllers.expression || null;
    this.#lookAt = controllers.lookAt || null;
  }

  get lastPose() {
    return this.#lastPose;
  }

  poseForState(state, meta = {}) {
    return this.applyDirective(resolvePoseDirectiveForState(state, meta));
  }

  poseForIntentResult(status, intentObj = {}) {
    return this.poseForState(status, {
      action: intentObj.action,
      tool: intentObj.tool,
      reason: intentObj.reason,
    });
  }

  applyDirective(directive) {
    if (!directive) return null;

    if (directive.motion && this.#motion?.play) {
      this.#motion.play(directive.motion);
    }

    if (directive.expression && this.#expression?.set) {
      this.#expression.set(
        directive.expression,
        directive.expressionWeight ?? 1,
        directive.fadeSec ?? 0.25
      );
    }

    if (directive.lookAt && this.#lookAt?.setTarget) {
      this.#lookAt.setTarget(directive.lookAt.target || 'mouse', directive.lookAt.data);
    }

    this.#lastPose = directive.pose || directive.motion || 'none';
    return directive;
  }
}
