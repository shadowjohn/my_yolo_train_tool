# YouTube Pose Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse completed YouTube Pose records when the same project, YouTube URL, pose model, confidence, FPS, and duration limit are requested again.

**Architecture:** Keep cache discovery file-based inside the selected project's `pose_record/record_*` folders. Store a compact cache key in `source_video_info.json`, and also support older records by deriving the same key from `pose_record.json` plus saved metadata. On cache hit, set `pose_last_output_file`, regenerate missing Live2D files if needed, and skip download/YOLO processing.

**Tech Stack:** Python stdlib, tkinter callbacks, existing `source_video_info.json`, existing `pose_record.json`, existing unittest callback harness.

---

### Task 1: Cache Key and Lookup

**Files:**
- Modify: `my_yolo_train_tool.py`
- Test: `tests/test_my_yolo_train_tool_callbacks.py`

- [x] **Step 1: Write failing tests** for `build_youtube_pose_cache_key()` and `find_youtube_pose_cache_record()`.
- [x] **Step 2: Run targeted tests** and verify they fail because the functions do not exist.
- [x] **Step 3: Implement helpers** that match only complete records with `pose_record.json`, `source.mp4`, and matching key fields.
- [x] **Step 4: Run targeted tests** and verify they pass.

### Task 2: Button Flow Integration

**Files:**
- Modify: `my_yolo_train_tool.py`
- Test: `tests/test_my_yolo_train_tool_callbacks.py`

- [x] **Step 1: Write failing test** proving `start_youtube_pose_recording()` uses a complete cache hit without creating a new record folder or starting a thread.
- [x] **Step 2: Run targeted test** and verify it fails.
- [x] **Step 3: Implement cache-hit branch** after authorization confirmation and before `create_pose_record_folder()`.
- [x] **Step 4: Run targeted tests** and verify they pass.

### Task 3: Metadata and Verification

**Files:**
- Modify: `my_yolo_train_tool.py`
- Modify: `history.md`

- [x] **Step 1: Add cache key fields** to new `source_video_info.json` writes.
- [x] **Step 2: Update `history.md`** with the cache behavior and invalidation rules.
- [x] **Step 3: Run full tests** using `binary\Ultralytics\python.exe -m unittest discover -s tests`.
- [x] **Step 4: Run `git diff --check`** and review the scoped diff.
