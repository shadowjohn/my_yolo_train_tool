/**
 * LookAtController — 滑鼠注視系統
 *
 * 將滑鼠螢幕座標轉換為頭部 bone 旋轉，帶 EMA 平滑。
 * 與 MotionController 共存：LookAt 只控制頭部，Motion 控制其他骨骼。
 */

export class LookAtController {
  #vrm = null;
  #headBone = null;
  #neckBone = null;
  #enabled = true;

  // 目標（滑鼠正規化座標 -1~1）
  #targetX = 0;
  #targetY = 0;

  // 平滑後的值
  #smoothX = 0;
  #smoothY = 0;

  // 參數
  #alpha = 0.10;    // EMA 係數（越小越滑）
  #maxYaw = 30;     // 最大左右轉角（度）
  #maxPitch = 20;   // 最大上下仰角（度）
  #neckRatio = 0.3; // 脖子分攤比例

  /**
   * 綁定 VRM 模型
   * @param {object} vrm - three-vrm VRM instance
   */
  setVrm(vrm) {
    this.#vrm = vrm;
    // getBoneNode 使用 VRM 0.6.7 的 lowercase bone names
    this.#headBone = vrm.humanoid?.getBoneNode('head') ?? null;
    this.#neckBone = vrm.humanoid?.getBoneNode('neck') ?? null;
  }

  /** 開啟/關閉注視 */
  setEnabled(flag) {
    this.#enabled = flag;
    if (!flag) {
      this.#targetX = 0;
      this.#targetY = 0;
    }
  }

  /** @returns {boolean} */
  get enabled() {
    return this.#enabled;
  }

  /**
   * 設定注視模式
   * @param {'mouse'|'point'|'none'} type
   * @param {{x?:number, y?:number}} [data]
   */
  setTarget(type, data) {
    switch (type) {
      case 'none':
        this.#enabled = false;
        break;
      case 'mouse':
        this.#enabled = true;
        break;
      case 'point':
        this.#enabled = true;
        if (data) {
          this.#targetX = data.x ?? 0;
          this.#targetY = data.y ?? 0;
        }
        break;
    }
  }

  /**
   * 處理滑鼠移動（由外部 mousemove 事件呼叫）
   * @param {number} nx - 正規化 X (-1 ~ 1，左到右)
   * @param {number} ny - 正規化 Y (-1 ~ 1，下到上)
   */
  onMouseMove(nx, ny) {
    if (!this.#enabled) return;
    this.#targetX = Math.max(-1, Math.min(1, nx));
    this.#targetY = Math.max(-1, Math.min(1, ny));
  }

  /**
   * Debug 資訊
   * @returns {{yaw: number, pitch: number}}
   */
  get debugValues() {
    return {
      yaw: +(this.#smoothX * this.#maxYaw).toFixed(1),
      pitch: +(this.#smoothY * this.#maxPitch).toFixed(1),
    };
  }

  /**
   * 每幀更新
   * @param {number} dt - deltaTime in seconds
   */
  update(dt) {
    if (!this.#enabled || !this.#headBone) return;

    // EMA 平滑
    this.#smoothX += (this.#targetX - this.#smoothX) * this.#alpha;
    this.#smoothY += (this.#targetY - this.#smoothY) * this.#alpha;

    const yawRad = (this.#smoothX * this.#maxYaw) * Math.PI / 180;
    const pitchRad = (this.#smoothY * this.#maxPitch) * Math.PI / 180;

    // 分攤到脖子和頭部
    if (this.#neckBone) {
      this.#neckBone.rotation.y = yawRad * this.#neckRatio;
      this.#neckBone.rotation.x = pitchRad * this.#neckRatio;
    }

    // 頭部拿剩餘的旋轉
    const headRatio = 1 - this.#neckRatio;
    this.#headBone.rotation.y = yawRad * headRatio;
    this.#headBone.rotation.x = pitchRad * headRatio;
  }

  /** 清理 */
  dispose() {
    this.#vrm = null;
    this.#headBone = null;
    this.#neckBone = null;
  }
}
