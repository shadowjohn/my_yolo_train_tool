/**
 * MotionController — 程序式動作系統
 *
 * 管理 idle / wave / dance_short / think 等動作。
 * 所有動作都是程序式產生（不依賴外部動畫檔），
 * Phase 2 再加入 Mixamo FBX / VRMA 支援。
 *
 * 注意：頭部由 LookAtController 控制，MotionController 不碰 head bone。
 */

/** 取得 VRM bone name 對應 (0.6.7 相容) */
function getBoneNames() {
  if (typeof THREE !== 'undefined' && THREE.VRMHumanoidBoneName) {
    return THREE.VRMHumanoidBoneName;
  }
  // fallback
  return {
    Spine: 'spine', Chest: 'chest', Hips: 'hips',
    LeftUpperArm: 'leftUpperArm', LeftLowerArm: 'leftLowerArm',
    RightUpperArm: 'rightUpperArm', RightLowerArm: 'rightLowerArm',
    LeftUpperLeg: 'leftUpperLeg', LeftLowerLeg: 'leftLowerLeg',
    RightUpperLeg: 'rightUpperLeg', RightLowerLeg: 'rightLowerLeg',
    LeftShoulder: 'leftShoulder', RightShoulder: 'rightShoulder',
  };
}

const DEG = Math.PI / 180;

/** 平滑插值 */
function lerp(a, b, t) {
  return a + (b - a) * Math.min(1, Math.max(0, t));
}

/** ease-in-out */
function easeInOut(t) {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}


export class MotionController {
  #vrm = null;
  #currentAction = 'idle';
  #elapsed = 0;       // 當前動作經過時間 (s)
  #bones = {};
  #hipsBaseY = 0;     // hips 初始 Y 位置
  #customAnimData = null;
  #customOptions = {};
  #tempQ1 = null;
  #tempQ2 = null;

  /**
   * 綁定 VRM 模型
   * @param {object} vrm
   */
  setVrm(vrm) {
    this.#vrm = vrm;
    this.#cacheBones();
    this.#currentAction = 'idle';
    this.#elapsed = 0;
  }

  /** 快取骨骼節點 */
  #cacheBones() {
    const h = this.#vrm.humanoid;
    const bn = getBoneNames();
    this.#bones = {
      spine:          h.getBoneNode(bn.Spine),
      chest:          h.getBoneNode(bn.Chest),
      hips:           h.getBoneNode(bn.Hips),
      leftUpperArm:   h.getBoneNode(bn.LeftUpperArm),
      leftLowerArm:   h.getBoneNode(bn.LeftLowerArm),
      rightUpperArm:  h.getBoneNode(bn.RightUpperArm),
      rightLowerArm:  h.getBoneNode(bn.RightLowerArm),
      leftUpperLeg:   h.getBoneNode(bn.LeftUpperLeg),
      rightUpperLeg:  h.getBoneNode(bn.RightUpperLeg),
      leftShoulder:   h.getBoneNode(bn.LeftShoulder),
      rightShoulder:  h.getBoneNode(bn.RightShoulder),
    };
    // 記錄 hips 初始 Y
    if (this.#bones.hips) {
      this.#hipsBaseY = this.#bones.hips.position.y;
    }
  }

  /**
   * 播放動作
   * @param {string} name - 動作名 (idle|wave|dance_short|think|happy)
   */
  play(name) {
    if (this.#currentAction !== name) {
      this.#resetBones();
    }
    this.#currentAction = name;
    this.#elapsed = 0;
    this.#customAnimData = null;
    this.#customOptions = {};
  }

  /**
   * 播放自訂 JSON 動畫
   * @param {object} animData - JSON 動畫資料
   * @param {object} [options]
   * @param {boolean} [options.loop=false]
   * @param {function} [options.onComplete]
   */
  playCustom(animData, options = {}) {
    this.#resetBones();
    this.#currentAction = 'custom';
    this.#elapsed = 0;
    this.#customAnimData = animData;
    this.#customOptions = options;
  }

  /** 回到 idle */
  stop() {
    this.play('idle');
  }

  /** @returns {string} 當前動作名 */
  get currentAction() {
    return this.#currentAction;
  }

  /**
   * 每幀更新
   * @param {number} dt - deltaTime (s)
   */
  update(dt) {
    if (!this.#vrm) return;
    this.#elapsed += dt;

    switch (this.#currentAction) {
      case 'idle':        this.#doIdle(); break;
      case 'wave':        this.#doWave(); break;
      case 'dance_short': this.#doDance(); break;
      case 'think':       this.#doThink(); break;
      case 'happy':       this.#doHappy(); break;
      case 'custom':      this.#doCustom(); break;
      default:            this.#doIdle(); break;
    }
  }

  // ── Idle：呼吸微動 ───────────────────────

  #doIdle() {
    const t = this.#elapsed;

    // 脊椎微微前傾呼吸
    if (this.#bones.spine) {
      this.#bones.spine.rotation.x = Math.sin(t * 1.4) * 0.008;
      this.#bones.spine.rotation.z = Math.sin(t * 0.7) * 0.003;
    }

    // 臀部微幅上下（呼吸感）
    if (this.#bones.hips) {
      this.#bones.hips.position.y = this.#hipsBaseY + Math.sin(t * 1.4) * 0.002;
    }

    // 手臂自然微垂
    if (this.#bones.leftUpperArm) {
      this.#bones.leftUpperArm.rotation.z = Math.sin(t * 0.9) * 0.01;
    }
    if (this.#bones.rightUpperArm) {
      this.#bones.rightUpperArm.rotation.z = Math.sin(t * 0.9 + 0.5) * 0.01;
    }
  }

  // ── Wave：右手揮手 ──────────────────────

  #doWave() {
    const t = this.#elapsed;
    const totalDuration = 2.8; // 秒

    // 同時做呼吸
    this.#doIdleSubtle();

    if (t >= totalDuration) {
      this.#currentAction = 'idle';
      this.#elapsed = 0;
      this.#resetBones();
      return;
    }

    const riseEnd = 0.35;
    const waveStart = riseEnd;
    const waveEnd = 2.2;
    const fallEnd = totalDuration;

    // 右上臂
    if (this.#bones.rightUpperArm) {
      let zAngle;
      if (t < riseEnd) {
        // 舉手
        zAngle = easeInOut(t / riseEnd) * (-70 * DEG);
      } else if (t < waveEnd) {
        // 揮動
        zAngle = -70 * DEG + Math.sin((t - waveStart) * 7) * (12 * DEG);
      } else {
        // 放下
        const p = easeInOut((t - waveEnd) / (fallEnd - waveEnd));
        zAngle = (-70 * DEG) * (1 - p);
      }
      this.#bones.rightUpperArm.rotation.z = zAngle;
      this.#bones.rightUpperArm.rotation.x = t < waveEnd ? 15 * DEG : 15 * DEG * (1 - easeInOut((t - waveEnd) / (fallEnd - waveEnd)));
    }

    // 右下臂（肘彎曲）
    if (this.#bones.rightLowerArm) {
      let yAngle;
      if (t < riseEnd) {
        yAngle = easeInOut(t / riseEnd) * (50 * DEG);
      } else if (t < waveEnd) {
        yAngle = 50 * DEG + Math.sin((t - waveStart) * 7 + 0.8) * (10 * DEG);
      } else {
        const p = easeInOut((t - waveEnd) / (fallEnd - waveEnd));
        yAngle = (50 * DEG) * (1 - p);
      }
      this.#bones.rightLowerArm.rotation.y = yAngle;
    }
  }

  // ── Dance Short：左右搖擺 ──────────────

  #doDance() {
    const t = this.#elapsed;
    const totalDuration = 4.0;

    if (t >= totalDuration) {
      this.#currentAction = 'idle';
      this.#elapsed = 0;
      this.#resetBones();
      return;
    }

    const beat = t * 2.5; // ~150 BPM feel

    // 身體左右搖
    if (this.#bones.spine) {
      this.#bones.spine.rotation.z = Math.sin(beat * Math.PI) * (8 * DEG);
      this.#bones.spine.rotation.x = Math.sin(beat * Math.PI * 2) * 0.015 + 0.01;
    }

    // 臀部上下彈跳
    if (this.#bones.hips) {
      this.#bones.hips.position.y = this.#hipsBaseY + Math.abs(Math.sin(beat * Math.PI)) * 0.015;
    }

    // 雙手交替舉起
    if (this.#bones.leftUpperArm) {
      this.#bones.leftUpperArm.rotation.z = Math.sin(beat * Math.PI) * (25 * DEG) + 5 * DEG;
    }
    if (this.#bones.rightUpperArm) {
      this.#bones.rightUpperArm.rotation.z = Math.sin(beat * Math.PI + Math.PI) * (25 * DEG) - 5 * DEG;
    }

    // 肘部配合
    if (this.#bones.leftLowerArm) {
      this.#bones.leftLowerArm.rotation.y = Math.sin(beat * Math.PI * 2) * (15 * DEG);
    }
    if (this.#bones.rightLowerArm) {
      this.#bones.rightLowerArm.rotation.y = Math.sin(beat * Math.PI * 2 + Math.PI) * (-15 * DEG);
    }
  }

  // ── Think：歪頭沉思 ────────────────────

  #doThink() {
    const t = this.#elapsed;
    const totalDuration = 3.0;

    this.#doIdleSubtle();

    if (t >= totalDuration) {
      this.#currentAction = 'idle';
      this.#elapsed = 0;
      this.#resetBones();
      return;
    }

    const fadeIn = Math.min(1, t / 0.4);
    const fadeOut = t > 2.4 ? 1 - (t - 2.4) / 0.6 : 1;
    const intensity = easeInOut(fadeIn) * Math.max(0, fadeOut);

    // 右手抬到下巴
    if (this.#bones.rightUpperArm) {
      this.#bones.rightUpperArm.rotation.z = -40 * DEG * intensity;
      this.#bones.rightUpperArm.rotation.x = 30 * DEG * intensity;
    }
    if (this.#bones.rightLowerArm) {
      this.#bones.rightLowerArm.rotation.y = 90 * DEG * intensity;
    }
  }

  // ── Happy：開心跳躍 ────────────────────

  #doHappy() {
    const t = this.#elapsed;
    const totalDuration = 2.0;

    if (t >= totalDuration) {
      this.#currentAction = 'idle';
      this.#elapsed = 0;
      this.#resetBones();
      return;
    }

    // 雙手舉高
    const riseEnd = 0.3;
    const holdEnd = 1.5;
    let armIntensity;
    if (t < riseEnd) {
      armIntensity = easeInOut(t / riseEnd);
    } else if (t < holdEnd) {
      armIntensity = 1;
    } else {
      armIntensity = 1 - easeInOut((t - holdEnd) / (totalDuration - holdEnd));
    }

    if (this.#bones.leftUpperArm) {
      this.#bones.leftUpperArm.rotation.z = 60 * DEG * armIntensity;
      this.#bones.leftUpperArm.rotation.x = 10 * DEG * armIntensity;
    }
    if (this.#bones.rightUpperArm) {
      this.#bones.rightUpperArm.rotation.z = -60 * DEG * armIntensity;
      this.#bones.rightUpperArm.rotation.x = 10 * DEG * armIntensity;
    }

    // 小跳躍
    if (this.#bones.hips && t < holdEnd) {
      const jumpPhase = Math.sin((t - riseEnd) * 6);
      this.#bones.hips.position.y = this.#hipsBaseY + Math.max(0, jumpPhase) * 0.03 * armIntensity;
    }

    // 身體微微後仰
    if (this.#bones.spine) {
      this.#bones.spine.rotation.x = -5 * DEG * armIntensity;
    }
  }

  // ── Utilities ──────────────────────────

  /** 低強度呼吸（供其他動作疊加） */
  #doIdleSubtle() {
    const t = this.#elapsed;
    if (this.#bones.spine) {
      this.#bones.spine.rotation.x = (this.#bones.spine.rotation.x || 0) + Math.sin(t * 1.4) * 0.004;
    }
    if (this.#bones.hips) {
      this.#bones.hips.position.y = this.#hipsBaseY + Math.sin(t * 1.4) * 0.001;
    }
  }

  /** 重設所有骨骼到初始姿勢 */
  #resetBones() {
    for (const [key, bone] of Object.entries(this.#bones)) {
      if (!bone) continue;
      bone.rotation.set(0, 0, 0);
      if (key === 'hips') {
        bone.position.y = this.#hipsBaseY;
      }
    }
  }

  #lazyInitTempQ() {
    if (!this.#tempQ1 && typeof THREE !== 'undefined') {
      this.#tempQ1 = new THREE.Quaternion();
      this.#tempQ2 = new THREE.Quaternion();
    }
  }

  /** 播放自訂 JSON 動作軌跡（插值邏輯） */
  #doCustom() {
    if (!this.#customAnimData) return;
    const durationMs = this.#customAnimData.duration_ms || 1000;
    const loop = this.#customOptions.loop ?? false;
    let timeMs = this.#elapsed * 1000;

    if (timeMs >= durationMs) {
      if (loop) {
        timeMs = timeMs % durationMs;
      } else {
        // 結束動作
        this.#currentAction = 'idle';
        this.#elapsed = 0;
        this.#resetBones();
        const cb = this.#customOptions.onComplete;
        this.#customAnimData = null;
        this.#customOptions = {};
        cb?.();
        return;
      }
    }

    this.#lazyInitTempQ();

    // 1. 骨骼旋轉插值 (Slerp)
    const bonesData = this.#customAnimData.bones || {};
    for (const [boneName, keys] of Object.entries(bonesData)) {
      const boneNode = this.#bones[boneName];
      if (!boneNode || !keys || keys.length === 0) continue;

      let kA = keys[0];
      let kB = keys[0];

      if (timeMs <= keys[0].time_ms) {
        kA = keys[0];
        kB = keys[0];
      } else if (timeMs >= keys[keys.length - 1].time_ms) {
        kA = keys[keys.length - 1];
        kB = keys[keys.length - 1];
      } else {
        // 線性搜尋
        for (let i = 0; i < keys.length - 1; i++) {
          if (timeMs >= keys[i].time_ms && timeMs <= keys[i + 1].time_ms) {
            kA = keys[i];
            kB = keys[i + 1];
            break;
          }
        }
      }

      const denom = kB.time_ms - kA.time_ms;
      const alpha = denom > 0 ? (timeMs - kA.time_ms) / denom : 0;

      if (this.#tempQ1 && this.#tempQ2) {
        this.#tempQ1.set(kA.rot[0], kA.rot[1], kA.rot[2], kA.rot[3]);
        this.#tempQ2.set(kB.rot[0], kB.rot[1], kB.rot[2], kB.rot[3]);
        boneNode.quaternion.slerpQuaternions(this.#tempQ1, this.#tempQ2, alpha);
      }
    }

    // 2. Hips 平移插值 (Lerp)
    const hipsPosData = this.#customAnimData.hips_position || [];
    if (this.#bones.hips && hipsPosData.length > 0) {
      let kA = hipsPosData[0];
      let kB = hipsPosData[0];

      if (timeMs <= hipsPosData[0].time_ms) {
        kA = hipsPosData[0];
        kB = hipsPosData[0];
      } else if (timeMs >= hipsPosData[hipsPosData.length - 1].time_ms) {
        kA = hipsPosData[hipsPosData.length - 1];
        kB = hipsPosData[hipsPosData.length - 1];
      } else {
        for (let i = 0; i < hipsPosData.length - 1; i++) {
          if (timeMs >= hipsPosData[i].time_ms && timeMs <= hipsPosData[i + 1].time_ms) {
            kA = hipsPosData[i];
            kB = hipsPosData[i + 1];
            break;
          }
        }
      }

      const denom = kB.time_ms - kA.time_ms;
      const alpha = denom > 0 ? (timeMs - kA.time_ms) / denom : 0;

      const px = lerp(kA.pos[0], kB.pos[0], alpha);
      const py = lerp(kA.pos[1], kB.pos[1], alpha);
      const pz = lerp(kA.pos[2], kB.pos[2], alpha);

      this.#bones.hips.position.x = px;
      this.#bones.hips.position.y = this.#hipsBaseY + py;
      this.#bones.hips.position.z = pz;
    }
  }

  /** 清理 */
  dispose() {
    this.#vrm = null;
    this.#bones = {};
    this.#customAnimData = null;
    this.#customOptions = {};
  }
}
