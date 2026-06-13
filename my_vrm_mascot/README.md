# VRM Mascot — 可互動 3D 吉祥物

Phase 1 MVP：載入 VRM 模型，實現 idle / blink / mouse look / wave / dance 等互動。

## 快速開始

```bash
# 在 my_yolo_train_tool 目錄下
python -m http.server 8765 --directory my_vrm_mascot

# 開啟瀏覽器
# http://localhost:8765
```

> **注意**：ES Module 需要 HTTP server，不支援 `file://` 協定。

## 目錄結構

```
my_vrm_mascot/
  index.html                  # MVP 展示頁
  js/
    VrmMascot.js              # 主控制器（Three.js + VRM）
    MotionController.js       # 動作控制器（natural pose / idle / semantic motions / clip playback）
    MotionClips.js            # 短動作 clip 定義（wave/victory/warning_nod/shake_head/dance_short/punch_short）
    ExpressionController.js   # 眨眼 + 表情控制
    MascotStateMachine.js     # 狀態機（dispatch / do / say / emote）
    LookAtController.js       # 滑鼠注視（EMA 平滑）
  css/
    mascot.css                # 深色主題 + glassmorphism
  vendor/                     # Three.js r149 + three-vrm 0.6.7（離線化）
  models/                     # VRM 模型
  motions/                    # Phase 2 用：VRMA / FBX 動畫檔
```

## API

### 基本用法

```javascript
const mascot = new VrmMascot(document.getElementById('container'));
await mascot.load('models/mascot.vrm');
```

### 狀態機 — dispatch（主要 API，與 LLM intent 對齊）

```javascript
// 支援直接傳入物件格式 (與 LLM 輸出意圖對接)
mascot.dispatch({ type: 'do',    name: 'wave' });
mascot.dispatch({ type: 'say',   text: '部署完成了！', emotion: 'joy', motion: 'wave' });
mascot.dispatch({ type: 'emote', name: 'happy', duration: 2000 });
mascot.dispatch({ type: 'lookAt', target: 'mouse' });
mascot.dispatch({ type: 'reset' });

// 也支援方法參數呼叫：
mascot.dispatch('talking', { text: '你好', emotion: 'joy', motion: 'wave' });
```

### 代理意圖對接 — Agent Bridge (Phase 4)

為方便對接 LLM 代理（如 OpenAI、Gemini、Claude），可以利用 `performIntent` API 發送抽象的高階意圖，系統會自動轉譯為預置動作序列：

```javascript
// 執行成功意圖 (使用預設文字、表情與動作)
mascot.performIntent('success');

// 執行思考意圖 (覆蓋文字)
mascot.performIntent({
  intent: 'thinking',
  text: '讓我想想，怎麼寫程式才最優美...'
});

// 意圖參數完全覆蓋 (Override)
mascot.performIntent({
  intent: 'success',
  text: '我們成功搞定 Agent Bridge 了！',
  emotion: 'fun',
  motion: 'dance_short'
});

// 未知意圖防錯自動 Fallback (自動降級為 explain 並輸出控制台 Warning 警告)
mascot.performIntent({
  intent: 'unknown_action_name',
  text: '這是一個未定義的意圖，但安全防護會將其降級並照常說明。'
});
```

### 行為佇列 — ActionQueue (Phase 3)

讓角色可以排程連續行為，例如：`看向滑鼠` -> `招手說話` -> `開心跳躍`：

```javascript
mascot.enqueue([
  { type: 'lookAt', target: 'mouse' },
  { type: 'wait', duration: 500 },
  { 
    type: 'say', 
    text: '羽山哥，動畫與排程佇列載入成功！', 
    emotion: 'joy', 
    motion: 'wave',
    timeout: 6000 // Timeout Guard 防護 (毫秒)
  },
  { type: 'do', name: 'happy', timeout: 3000 }
]);

// 中斷並清空佇列
mascot.clearQueue(); 
```

### 便捷 API

```javascript
mascot.state.do('wave');
mascot.state.say('你好');
mascot.state.emote('happy');
mascot.state.lookAt('mouse');
mascot.state.reset();
```

### 子系統直接存取

```javascript
mascot.motion.play('dance_short');   // MotionController
mascot.motion.playClip('victory');    // Short Motion Clips
mascot.motion.playCustom(animData, { loop: true }); // 播放自訂 JSON 動畫
mascot.expression.set('joy', 0.8);  // ExpressionController
mascot.lookAt.setTarget('none');     // LookAtController
mascot.resetCamera();                // 重置 3D 視角
```

### 語意姿勢綁定 — PoseDirector (Phase M1)

Agent Runtime 不直接碰骨架，改透過語意姿勢 API 交給 VRM 表現層：

```javascript
mascot.poseForState('running');              // presenting
mascot.poseForIntentResult('done', intent);  // wave
```

`updateIntentTrace()` 會自動把 tool trace 狀態轉成姿勢：
`pending -> think`、`running -> presenting`、`done -> wave`、`blocked -> warning`、`failed/timeout -> shake_head`。

MotionController 會在 VRM 載入後立即套用 Natural Pose；所有內建程序式動作都建立在這個自然站姿上，再疊加呼吸、展示、警告或揮手動作，避免回到模型 bind/rest pose 的 T-Pose。

M2 Idle Micro Motion 只強化待機層：idle 會疊加胸口/脊椎/重心分層呼吸、肩膀放鬆、前臂與手腕微擺；LookAt `none` 時會加小幅頭部 drift，目標注視時不啟用這個漂移。

M3 Short Motion Clips 把短動作集中在 `MotionClips.js`：`wave`、`victory`、`warning_nod`、`shake_head`、`dance_short`、`punch_short` 都是短、可預期、可恢復的 clip。`MotionController.play(name)` 會自動路由 clip name，`playClip(name)` 可直接播放；clip 結束後會回到 idle 並重套 Natural Pose，避免殘留骨骼偏移。

Base pose preset 會依模型載入：

- `models/mascot.vrm` -> `motions/poses/alicia_solid.json`
- 未知或上傳模型 -> `motions/poses/default.json`
- Character Inspector 的本機設定只在有 localStorage preset 時覆蓋模型預設。

## 可用動作

| 名稱 | 說明 | 持續時間 |
|------|------|---------|
| `idle` | 呼吸微動（預設） | 持續 |
| `wave` | 右手短揮手 clip | 1.2s |
| `victory` | 短勝利 YA clip | 1.0s |
| `warning_nod` | 警示點頭 clip | 0.9s |
| `shake_head` | 否定式上身搖動 clip | 0.8s |
| `dance_short` | 短舞彩蛋 clip | 1.6s |
| `punch_short` | 輕吐槽短拳 clip | 0.7s |
| `think` | 托下巴沉思（已修正方向） | 3.0s |
| `happy` | 雙手舉高跳躍（已修正方向） | 2.0s |
| `presenting` | 伸手介紹面板 | 3.2s |
| `warning` | 警示姿勢 | 2.4s |
| `custom_animation` / `custom` | 播放自訂 JSON 動作 | 視動畫檔而定 |

## 可用表情

| 名稱 | VRM Preset |
|------|-----------|
| `happy` / `joy` | joy |
| `sad` / `sorrow` | sorrow |
| `angry` | angry |
| `fun` | fun |

## 升級策略

VRM 版本相關 API 集中在 `VrmMascot.js` 的 `_vrm*` helper：

| Helper | 0.6.7 | 3.x (Phase 2) |
|--------|-------|---------------|
| `_vrmFromGltf()` | `VRM.from(gltf)` | `VRMLoaderPlugin` |
| `_getBlendShapeProxy()` | `blendShapeProxy` | `expressionManager` |
| `_getBoneNode()` | `getBoneNode()` | `getNormalizedBoneNode()` |
| `_vrmUpdate()` | `vrm.update(dt)` | `vrm.update(dt)` |
| `_vrmDispose()` | `VRMUtils.deepDispose()` | `VRMUtils.deepDispose()` |

升級時只改這 5 個 method，其餘模組不動。

## 與 my_yolo_train_tool 的關係

| 專案 | 責任 | 技術 |
|------|------|------|
| `my_yolo_train_tool` | 影片→骨架→motion draft | YOLO / Python |
| `my_vrm_mascot` | 可互動吉祥物 runtime | Three.js / ES Module |

兩者完全獨立運作。未來動作管線：
```
影片 → YOLO Pose → pose_record.json → pose_vrm_mapper → 手修 → .vrma → my_vrm_mascot
```

## 作者

羽山 (https://3wa.tw)
