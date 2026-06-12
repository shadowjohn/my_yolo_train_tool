# My YOLO Train Tool — 開發歷程與專案脈絡

## 專案定位

**my_yolo_train_tool** 是一個 Windows 桌面工具，讓使用者可以：
1. 框選螢幕區域截圖 → 收集訓練素材
2. 透過 Web UI 標註圖片（分類 + bounding box）
3. 在 Web UI 提交訓練任務，背景跑 YOLO 訓練
4. 即時桌面辨識（用透明 Overlay 畫框顯示 YOLO 結果）

打包成單一 `.exe`（PyInstaller）方便散佈，非開發者也能使用。

---

## 技術架構

### 主程式 `my_yolo_train_tool.py`

| 層次 | 技術 | 說明 |
|------|------|------|
| GUI | tkinter | 主視窗、專案管理、截圖熱鍵、信心度滑桿 |
| Web UI | FastAPI + uvicorn (port 9487) | `www/index.html` 前端 + `/api` 後端 |
| AI 推論 | ultralytics YOLO | 桌面即時辨識，透明 canvas Overlay 畫框 |
| AI 訓練 | ultralytics YOLO（背景執行） | 支援多種模型、epoch、batch、早停 |
| 截圖 | mss | 高效全螢幕 / 區域截圖 |
| 全域熱鍵 | keyboard | CTRL+F2 觸發截圖 |
| 單例鎖 | portalocker | 防止程式重複執行 |
| 打包 | PyInstaller 6.9.0 | --onefile，www 靜態資源一併打包 |

### 全域狀態 `GDATA`

所有 UI 元件、截圖範圍座標、錄製狀態等都掛在 `GDATA` dict，以 global 傳遞。

### FastAPI `/api` 路由清單（`?mode=XXX`）

| mode | 功能 |
|------|------|
| `project_list` | 列出所有專案 |
| `project_add_action` | 新增專案 |
| `project_edit_action` | 重命名專案 |
| `choice_project` | 切換專案（同步更新 tkinter UI） |
| `getKindList` | 取得類別列表與照片數量 |
| `addKind` / `delKind` / `editKind` | 類別 CRUD |
| `getPhotoList` | 未分類照片列表 |
| `delPhoto` | 刪除照片 |
| `setPhotoToKind` | 移動照片到類別資料夾 |
| `getDoMarkKindList` | 各類別已標/未標數量 |
| `getMY_DATASETSPhotos` | 取得類別內圖片與對應 YOLO txt 標註 |
| `resetPhotoKind` | 退回未分類 |
| `saveTxt` | 儲存 YOLO bounding box txt |
| `train_add` | 新增訓練任務（寫 job.txt + status.txt） |
| `train_lists` | 列出所有訓練任務 |
| `train_get_task_status` | 查詢任務狀態 + log + progress + results.csv |
| `train_retrain` | 重設任務重跑 |

### 目錄結構（資料目錄）

```
data/
  projects/
    {project_name}/
      *.jpg                    # 未分類截圖
      rect.txt                 # 截圖框選座標
      dataset/                 # (保留目錄)
      my_dataset/
        {kind_name}/
          *.jpg                # 已分類照片
          *.txt                # YOLO 標註 (0 x y w h)
      train_project/
        task_{timestamp}/
          job.txt              # 訓練參數
          status.txt           # 0=待訓練, 1=訓練中, 2=完成, -1=失敗
          status_log.txt       # 結束訊息
          status_progress.txt  # 進度 %
          train.txt            # YOLO 訓練 log
          runs/train/output/   # 訓練結果 (results.csv, 圖片)
```

---

## OverlayWindow（透明辨識框）

- tkinter `Toplevel` 設 `-transparentcolor black` 實現透明
- PIL `ImageDraw` 批次畫所有 bounding box 後轉 `PhotoImage` 一次貼圖（效能最佳）
- 截圖前先 `hideAll()` 隱藏框線避免被截到，截完再 `showAll()`

---

## 環境設定

### 開發環境（requirements.txt）
```
c:\python312_64\Scripts\pip3.exe install -r requirements.txt
```
主要套件：opencv-python 4.10、ultralytics 8.3.49、torch+torchvision、FastAPI+uvicorn、tensorflow 2.16.2

### 訓練環境（build_conda_env.bat）
- 另建 conda 環境 `binary/Ultralytics` (Python 3.10)
- CUDA 11.8 + pytorch-cuda
- 從 conda 頻道安裝 pytorch，避免 pip 版本衝突

### 打包（build.bat）
```bat
c:\python312_64\scripts\pyinstaller -F --onefile --icon="pic\icon.ico" ...
--add-data=www:www my_yolo_train_tool.py
```
主動 exclude：tensorflow, pandas, scipy, IPython 等大型套件以縮小 exe 體積。

---

## Git 開發歷程（重要節點）

| commit | 說明 |
|--------|------|
| `eb8a06a` | 初始，修正 readme |
| `5e38900` | 加入 Ultralytics |
| `9cc0dcc` | 可選模型檔、可調信心度 |
| `8d61ad6` | 加入 ONNX 版本 |
| `4fd0ddc` | 簽入需要的檔案 |
| `8e9a0ea` | Web 可以編輯專案 |
| `94239c6` | 圖框設定功能 OK |
| `54f7307` | 開始訓練的功能 |
| `56c8ece` | 加入背景執行 YOLO 轉檔 |
| `8a24465` | 可重新訓練，更新 file_put_contents |
| `906f266` | 可以進行轉檔了 |
| `160497b` | 加入 jQuery UI |
| `e71690b` | 細節畫面 |
| `1e2773e` | 改用 conda 環境（訓練隔離） |
| `627a4fd` | 研究 tensorflow 版本相依問題 |
| `73fea4b` | 增加模型參照 Epoch 早停機制、早停耐心次數 |
| `0636d32` | 修正早停機制 |
| `f091a0b` | 停用 rect（目前 HEAD） |

---

## 目前未解決 / 待續事項

- 2026-06-12：修正桌面「新增專案檔」callback 例外。
  - 根因：`new_project()` 建立資料夾後尚未設定 `GDATA["project_folder"]`，就呼叫 `method_count_wait_process_files()` 統計 jpg，第一次建立專案會觸發 `KeyError: 'project_folder'`。
  - 修正：`new_project()` 改走既有 `reload_projects(project_name)` 流程；`reload_projects()` 只在有選定專案時設定 `project_folder` 並統計待處理檔案；`method_count_wait_process_files()` 對尚未選專案狀態回報 0。
  - 同步修正：`win_do_move()` 在 `root.x/root.y` 已被清成 `None` 時忽略殘留拖曳事件，避免 `TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'`。
  - 測試：新增 `tests/test_my_yolo_train_tool_callbacks.py`；使用 `binary\Ultralytics\python.exe -m unittest discover -s tests` 通過 19 個測試。系統 Python 缺 `PIL`、`cv2`，完整測試需使用 Ultralytics 環境。
- 2026-06-12：改善 YouTube Pose 長時間處理時的進度回報。
  - 觀察：YouTube URL 輸入後其實有在跑，`source_video_info.json` 會先到 `status: downloaded`，接著進入 YOLO pose 影格推論；短片仍可能因 NMS 較慢讓 UI 看起來像卡住。
  - 修正：YouTube 下載完成後顯示「開始分析影格」，影格分析第 1 張與每 5 張更新一次 GUI 狀態列，並同步 `print(..., flush=True)` 到 terminal。
  - 注意：RTX 5060 Ti 目前會出現 PyTorch CUDA capability sm_120 警告，且可能看到 `NMS time limit exceeded`；這代表推論/後處理可能偏慢，不一定是失敗。
  - 測試：擴充 `tests/test_my_yolo_train_tool_callbacks.py` 模擬 YouTube worker 進度；使用 `binary\Ultralytics\python.exe -m unittest discover -s tests` 通過 20 個測試。
- 2026-06-12：完成 Live2D 三畫面舞步對照播放器第一版。
  - YouTube Pose 新紀錄會保存下載後短片為 `pose_record/source.mp4`，並在 `pose_record.json` 的 `source.source_video_file` 與 `source_video_info.json` 寫入保存狀態；`open_live2d_dancer()` 會自動帶入 `video_url`。
  - `www/live2d_dancer.html` 改為左側原影片、中間 COCO17 火柴人 canvas、右側 Live2D 的同步對照舞台；播放、暫停、上一格、下一格、時間軸共用同一個 `currentTimeMs`。
  - `/data` 檔案回應新增 `Range: bytes=...` 支援，影片拖曳與逐格才可正常 seek；播放到尾端會停在最後一格，不再 modulo loop 造成影片與時間軸不同步。
  - Live2D registry 預設先嘗試 `fullbody` Cubism 4 `model3.json` loader；目前未放入未確認授權的網路模型，也未安裝 Cubism4 runtime，所以會 fallback 到 Shizuku 並顯示「腿部不保證對齊」能力提示。
  - Pose 到 Live2D mapping 新增 `PARAM_LEG_L`、`PARAM_LEG_R`，讓未來全身模型可以吃腿部角度曲線。
  - 測試：新增/擴充 `tests/test_fastapi_data_route.py`、`tests/test_live2d_dancer_page.py`、`tests/test_pose_live2d_mapper.py`、`tests/test_my_yolo_train_tool_callbacks.py`；使用 `binary\Ultralytics\python.exe -m unittest discover -s tests` 通過 28 個測試。
  - Browser QA：以臨時 9491 server 驗證 `pose_url + motion_url + video_url` 三欄載入、時間軸跳到 1.20s、上一格/下一格、播放 0.5 秒、片尾停止、無 `video_url` 舊紀錄 fallback；截圖保存在 `output/playwright/live2d_compare_qa.png`。
- 2026-06-12：Live2D 三畫面預設角色改為概念圖的示範全身角色。
  - 新增 `www/live2d/assets/mock_fullbody_schoolgirl.png`，由已確認的三欄概念圖裁出黑髮制服全身角色，作為本機 `mock_fullbody` 預設顯示。
  - `www/live2d_dancer.html` 預設 `model=mock_fullbody`，右欄顯示「示範全身角色」並套用同一個 pose 時間軸的身體傾斜、上下位移與手腳參數；Cubism4 `fullbody` loader 與 Shizuku fallback 仍保留。
  - 注意：這不是正式 Cubism 模型，只是先把概念圖角色帶回三畫面對照流程；等取得可驗證授權的 `.model3.json` 全身 Live2D 模型後，可直接接到既有 `fullbody` registry。
  - 測試：擴充 `tests/test_live2d_dancer_page.py` 檢查 `mock_fullbody` 預設、設計圖角色 asset、Cubism4 與 Shizuku fallback 保留；使用 `binary\Ultralytics\python.exe -m unittest discover -s tests` 通過 30 個測試。
- 2026-06-12：修正 Live2D 角色方向判斷。
  - 釐清：切圖/PNG mock 不能視為 Live2D 模型，不能拿來冒充 Cubism 參數控制。
  - 本機目前只有 Cubism 2 Shizuku/default `.moc` 與舊 `live2d.min.js`，沒有真正可載入的 Cubism 4/5 `model3.json` runtime 與全身模型。
  - 後續模型候選決策：優先使用官方 Live2D Sample Data / `Live2D/CubismWebSamples` 內的 Hiyori 作第一個 Cubism3+ 測試模型；Mao/Haru 可作第二輪；Eikanya/Live2d-model 屬第三方遊戲拆包合集，授權與用途風險較高，不納入預設或散佈。
- 2026-06-12：改用可驗證來源的官方 Cubism 4 sample model3。
  - 新增官方 sample 模型 `ren`、`mark`、`hiyori` 到 `www/live2d/models/`，並保留官方 license；預設 `fullbody` 指向 Ren，Ren 失敗時先 fallback 到 Mark-kun，再 fallback 到 Shizuku。
  - 新增本機 Cubism4 runtime：`live2dcubismcore.min.js`、`pixi.min.js`、`pixi-live2d-display-cubism4.min.js`；`live2d-runtime-shim.js` 負責把 classic script 的 `PIXI` / `Live2DCubismCore` 掛到 `window`，避免 runtime 判斷失敗。
  - Browser QA：以 9493 server 開啟 `model=mark`，右欄顯示 `Mark-kun / Cubism model3`，Shizuku canvas 與切圖 placeholder 隱藏；按播放後時間軸前進到 1.61s、影片 `currentTime` 到 1.774s，三欄仍同步。
  - 注意：Browser 內建截圖在 WebGL canvas 頁面會 timeout，改用系統層截圖存到 `%TEMP%\live2d_mark_model3_verify.png` 做畫面證據。
- 2026-06-12：新增 YouTube Pose 本機快取。
  - 同一專案內再次處理同一 YouTube 影片時，若 URL、pose model 檔名、pose confidence、FPS、最大處理秒數相同，且 `pose_record.json`、`source.mp4` 都完整存在，會直接重用既有紀錄，不再下載影片、不再跑 YOLO pose。
  - 新產生的 `source_video_info.json` 會寫入 `cache_key`、`pose_model`、`pose_confidence`、`fps_target`、`max_duration_seconds`；舊紀錄沒有 `cache_key` 時，會從 `source_video_info.json` 與 `pose_record.json` 推回可比對欄位，缺少舊版 confidence 時使用目前設定做 legacy 匹配。
  - 快取命中後會補轉缺少的 `live2d_params.json` / `motion3.json`，設定 `pose_last_output_file`，主畫面狀態顯示「YouTube Pose 使用快取」。
  - 乾跑確認 `data/projects/舞曲` 內既有 shorts 紀錄可被 lookup 命中。
- 2026-06-12：YouTube Pose 快取命中時改為先詢問。
  - 命中同設定快取後跳出「YouTube Pose 快取」三態確認；「是」使用既有快取，「否」重新轉換並建立新的 `record_*`，「取消」不處理。
  - 不刪除舊紀錄，避免已開啟的 Live2D/VRM 對照頁或其他本機流程失去來源檔案。
- 2026-06-12：優化 3D VRM 舞步展示頁面，實作全本地化、修復骨骼偏角與影片同步。
  - **本地化 (Offline-ready)**：將 `three.min.js`、`OrbitControls.js`、`GLTFLoader.js` 與 `three-vrm.min.js` 套件以及 `AliciaSolid.vrm`、`AvatarSample_B.vrm` 角色模型下載至本地，實作 100% 離線載入。
  - **脊椎彎腰修正 (Spine Offset)**：針對 `torso_angle_deg` 在直立狀態下為 `-90.0` 度的特性，在 3D VRM 骨骼動畫（`pose_vrm_mapper.py` 與 `vrm_dancer.html`）中加入 `+90.0` 度偏移，使角色直立於 0 度位置，修復角色攔腰折斷/平躺 90 度的問題。
  - **手臂映象與正負號修正 (Arm Rotation)**：因應 VRM 骨骼左右映象對稱設計（左臂正角度為向下，右臂正角度為向上，且右臂 T-pose 為 180 度），修正旋轉公式：左臂為 `armL`，右臂為 `armR - 180`，完美對齊火柴人與原影片。
  - **對照影片自動帶入 (video_url passing)**：修正 Python 後端 `open_live2d_dancer()` 路由邏輯，自動讀取 `pose_record.json` 中保存的 `source_video_file` 並傳遞 `video_url` 參數給網頁，無縫啟用三欄同步對照。
  - **時間軸平滑拖曳 (Smooth Scrubbing)**：採用 `seeking` 狀態鎖與 `seeked` 事件追趕佇列機制（Queue），解決高頻拖曳滑桿導致瀏覽器影片尋跡阻塞（lag/卡住）的問題。
  - **測試**：透過 `binary\Ultralytics\python.exe -m unittest discover -s tests` 順利通過全部 46 項單元測試。
- tensorflow 版本相依問題（目前有簽入但 requirements.txt 的 torch/torchvision 版本仍有註解掉的選項）
- `rect` 相關功能被停用（f091a0b），原因待確認
- `_legacy_run_flask_unused()` — 舊 Flask 版本已封存，正式用 FastAPI
- 錄影功能 `start_recording` / `stop_recording` 已全部 comment out，保留程式碼但未啟用
- `example_pt/` 目錄下有大量以 timestamp 命名的訓練結果目錄，尚未整理

---

## 作者資訊

- 作者：羽山 (https://3wa.tw)
- 版本：0.01
- 開發日期紀錄起始：2026-05-09
