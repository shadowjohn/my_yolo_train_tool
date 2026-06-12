/**
 * ExpressionController — VRM 表情與眨眼系統
 *
 * 支援 three-vrm 0.6.7 的 blendShapeProxy API
 * 功能：自動眨眼（隨機間隔）、表情設定（joy/angry/sorrow/fun）
 */

export class ExpressionController {
  /** @type {import('three-vrm').VRM|null} */
  #vrm = null;
  #blinkTimerId = null;
  #blinkPhase = 'open'; // 'open' | 'closing' | 'opening'
  #blinkWeight = 0;
  #minInterval = 2000;
  #maxInterval = 6000;

  // Expression fade
  #currentExpr = null;
  #currentWeight = 0;
  #targetWeight = 0;
  #fadeDuration = 0.3; // seconds
  #prevExpr = null;

  /**
   * 綁定 VRM 模型
   * @param {object} vrm - three-vrm VRM instance
   */
  setVrm(vrm) {
    this.#vrm = vrm;
    this.#blinkPhase = 'open';
    this.#blinkWeight = 0;
  }

  /**
   * 開啟自動眨眼
   * @param {number} [minMs=2000] - 最短間隔 (ms)
   * @param {number} [maxMs=6000] - 最長間隔 (ms)
   */
  startAutoBlink(minMs = 2000, maxMs = 6000) {
    this.#minInterval = minMs;
    this.#maxInterval = maxMs;
    this.stopAutoBlink();
    this.#scheduleBlink();
  }

  /** 停止自動眨眼 */
  stopAutoBlink() {
    if (this.#blinkTimerId !== null) {
      clearTimeout(this.#blinkTimerId);
      this.#blinkTimerId = null;
    }
  }

  /**
   * 設定表情（主要 API）
   * @param {string|null} name - 表情名稱 ('joy'|'angry'|'sorrow'|'fun'|null)
   * @param {number} [weight=1.0] - 目標權重 0~1
   * @param {number} [fadeSec=0.3] - 淡入時間
   */
  set(name, weight = 1.0, fadeSec = 0.3) {
    if (this.#currentExpr && this.#currentExpr !== name) {
      this.#prevExpr = this.#currentExpr;
    }
    this.#currentExpr = name;
    this.#targetWeight = name ? weight : 0;
    this.#fadeDuration = fadeSec;
  }

  /** @deprecated 用 set() 代替 */
  setExpression(name, weight, fadeSec) { return this.set(name, weight, fadeSec); }

  /** 取得當前表情名 */
  get currentExpression() {
    return this.#currentExpr;
  }

  /** 取得眨眼狀態（debug 用） */
  get blinkWeight() {
    return this.#blinkWeight;
  }

  /**
   * 每幀更新（由 VrmMascot.update 呼叫）
   * @param {number} dt - deltaTime in seconds
   */
  update(dt) {
    if (!this.#vrm) return;
    this.#updateBlink(dt);
    this.#updateExpression(dt);
  }

  // ── Private ──────────────────────────────

  #scheduleBlink() {
    const delay = this.#minInterval + Math.random() * (this.#maxInterval - this.#minInterval);
    this.#blinkTimerId = setTimeout(() => {
      this.#triggerBlink();
      this.#scheduleBlink();
    }, delay);
  }

  #triggerBlink() {
    if (this.#blinkPhase !== 'open') return; // 上次還沒結束
    this.#blinkPhase = 'closing';
    this.#blinkWeight = 0;
  }

  #updateBlink(dt) {
    if (this.#blinkPhase === 'open') return;

    const speed = dt / 0.07; // 70ms per phase

    if (this.#blinkPhase === 'closing') {
      this.#blinkWeight = Math.min(1, this.#blinkWeight + speed);
      if (this.#blinkWeight >= 1) {
        this.#blinkPhase = 'opening';
      }
    } else if (this.#blinkPhase === 'opening') {
      this.#blinkWeight = Math.max(0, this.#blinkWeight - speed);
      if (this.#blinkWeight <= 0) {
        this.#blinkPhase = 'open';
        this.#blinkWeight = 0;
      }
    }

    // 套用到 VRM blendShapeProxy
    const proxy = this.#vrm.blendShapeProxy;
    if (proxy) {
      proxy.setValue('blink', this.#blinkWeight);
    }
  }

  #updateExpression(dt) {
    const proxy = this.#vrm.blendShapeProxy;
    if (!proxy) return;

    // 淡出前一個表情
    if (this.#prevExpr) {
      proxy.setValue(this.#prevExpr, 0);
      this.#prevExpr = null;
    }

    if (!this.#currentExpr) {
      this.#currentWeight = 0;
      return;
    }

    // 漸變到目標權重
    const fadeSpeed = dt / Math.max(0.01, this.#fadeDuration);
    if (this.#currentWeight < this.#targetWeight) {
      this.#currentWeight = Math.min(this.#targetWeight, this.#currentWeight + fadeSpeed);
    } else if (this.#currentWeight > this.#targetWeight) {
      this.#currentWeight = Math.max(this.#targetWeight, this.#currentWeight - fadeSpeed);
    }

    proxy.setValue(this.#currentExpr, this.#currentWeight);
  }

  /** 清理資源 */
  dispose() {
    this.stopAutoBlink();
    this.#vrm = null;
  }
}
