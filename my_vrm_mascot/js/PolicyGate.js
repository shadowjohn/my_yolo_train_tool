/**
 * PolicyGate — 安全策略保護網關
 *
 * 核心功能：
 *   - 提供工具執行前的風險控制與安全檢查
 *   - 支援 requiredArgs, allowedArgs 校驗
 *   - 支援 allowedTargetPrefixes 前綴規則校驗
 *   - 提供 risk 分級與 requireConfirm 確認標籤
 */
export class PolicyGate {
  #mascot = null;
  #policies = new Map();

  /**
   * @param {import('./VrmMascot.js').VrmMascot} mascot
   */
  constructor(mascot) {
    this.#mascot = mascot;

    // 註冊預設工具政策
    this.registerPolicy('download_report', {
      risk: 'low',
      requireConfirm: false,
      allowedArgs: ['featureId'],
      requiredArgs: ['featureId'],
      allowedTargetPrefixes: ['PIPE-', 'CCTV-']
    });

    this.registerPolicy('query_pipe', {
      risk: 'low',
      requireConfirm: false,
      allowedArgs: ['x', 'y'],
      requiredArgs: ['x', 'y'],
      allowedTargetPrefixes: []
    });

    this.registerPolicy('query_cctv', {
      risk: 'low',
      requireConfirm: false,
      allowedArgs: ['x', 'y'],
      requiredArgs: ['x', 'y'],
      allowedTargetPrefixes: []
    });
  }

  /**
   * 註冊工具之安全政策
   * @param {string} toolName
   * @param {object} policy
   */
  registerPolicy(toolName, policy) {
    const cleanName = String(toolName || '').trim().toLowerCase();
    this.#policies.set(cleanName, {
      risk: policy.risk || 'low',
      requireConfirm: !!policy.requireConfirm,
      allowedArgs: policy.allowedArgs || [],
      requiredArgs: policy.requiredArgs || [],
      allowedTargetPrefixes: policy.allowedTargetPrefixes || []
    });
  }

  /**
   * 取得工具安全政策
   * @param {string} toolName
   * @returns {object|null}
   */
  getPolicy(toolName) {
    const cleanName = String(toolName || '').trim().toLowerCase();
    return this.#policies.get(cleanName) || null;
  }

  /**
   * 依序執行政策安全檢查
   *
   * 檢查順序：
   *   tool exists ➔ args schema ➔ required args ➔ allowed args ➔ target prefix ➔ risk / confirmation
   *
   * @param {string} toolName
   * @param {object} args
   * @returns {object} { ok: boolean, reason?: string, error?: string }
   */
  check(toolName, args) {
    const cleanName = String(toolName || '').trim().toLowerCase();

    // 1. Tool Exists (工具是否存在於 Registry)
    if (!this.#mascot.toolRegistry || !this.#mascot.toolRegistry.has(cleanName)) {
      return {
        ok: false,
        reason: 'unregistered',
        error: `安全策略攔截：工具 ${toolName} 未註冊。`
      };
    }

    const policy = this.getPolicy(cleanName);
    if (!policy) {
      return {
        ok: false,
        reason: 'no_policy',
        error: `安全策略攔截：工具 ${toolName} 沒有定義安全政策。`
      };
    }

    // 2. Args Schema (這部分與 ToolRegistry 的內建 Required 檢查互補)
    // 3. Required Args (防止缺少必要參數)
    if (policy.requiredArgs && policy.requiredArgs.length > 0) {
      for (const reqKey of policy.requiredArgs) {
        if (!args || args[reqKey] === undefined || args[reqKey] === null || args[reqKey] === '') {
          return {
            ok: false,
            reason: 'missing_required_arg',
            error: `安全策略攔截：工具 ${toolName} 缺少必要參數 ${reqKey}。`
          };
        }
      }
    }

    // 4. Allowed Args (防止多塞奇怪參數)
    if (args) {
      for (const key of Object.keys(args)) {
        if (!policy.allowedArgs.includes(key)) {
          return {
            ok: false,
            reason: 'disallowed_arg',
            error: `安全策略攔截：工具 ${toolName} 包含未允許的參數 ${key}。`
          };
        }
      }
    }

    // 5. Target Prefix (防止工具被拿去操作不該操作的 ID)
    if (policy.allowedTargetPrefixes && policy.allowedTargetPrefixes.length > 0) {
      // 搜尋參數中所有字串屬性值，以進行前綴檢查
      const targetValues = [];
      if (args) {
        for (const [key, val] of Object.entries(args)) {
          if (typeof val === 'string') {
            targetValues.push(val);
          }
        }
      }

      for (const val of targetValues) {
        const isAllowed = policy.allowedTargetPrefixes.some(prefix => val.startsWith(prefix));
        if (!isAllowed) {
          return {
            ok: false,
            reason: 'disallowed_target_prefix',
            error: `安全策略攔截：標的識別碼 "${val}" 不符合允許的前綴規則 (${policy.allowedTargetPrefixes.join(', ')})。`
          };
        }
      }
    }

    // 6. Risk & Confirmation (確認與風險級別)
    if (policy.requireConfirm) {
      return {
        ok: false,
        reason: 'require_confirmation',
        error: `安全策略攔截：執行工具 ${toolName} 需要使用者確認。`
      };
    }

    return { ok: true };
  }
}
