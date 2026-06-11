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
