# YOLO Pose to Live2D Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two Stage A pose input modes, shared pose JSON output, initial Live2D body/face parameter mapping, a desktop Live2D character launcher, and a Face CopyCat path that can mirror desktop ROI facial expressions.

**Architecture:** Add focused helper modules for pose geometry, face expression mapping, JSON serialization, video/URL processing, and Live2D mapping. Keep `my_yolo_train_tool.py` as the tkinter/FastAPI integration shell, with separate `pose_model` and `face_tracker` state so existing object detection remains untouched. Use project-scoped output folders under `data/projects/{project}/pose_record/record_{timestamp}/` and `data/projects/{project}/face_record/record_{timestamp}/`.

**Tech Stack:** Python 3.12, tkinter, FastAPI, OpenCV, mss, Ultralytics YOLO pose, optional `yt-dlp`, optional `mediapipe` Face Landmarker, local static HTML/JS for pose/face preview and Live2D v2 assets copied from `Z:\inc\javascript\live2d_demo`.

---

## File Structure

- Create `pose_motion_core.py`: COCO17 constants, bounded frame buffer, ROI normalization, geometry helpers, main dancer selection, JSON builders, HTML skeleton preview builder.
- Create `face_motion_core.py`: face record JSON builder, blendshape-to-Live2D mapping, face parameter JSON builder.
- Create `face_tracking_source.py`: optional MediaPipe Face Landmarker wrapper for ROI frames.
- Create `pose_video_source.py`: authorized YouTube URL/local video frame extraction into the shared pose pipeline.
- Create `pose_live2d_mapper.py`: converts `pose_record.json` into `live2d_params.json` and simple `.motion3.json`.
- Reference KennardWang/VTuber-MomoseHiyori for the Face CopyCat control set: head roll/pitch/yaw, eye openness, eyeball X/Y, eyebrows, mouth width, and mouth open. Do not copy its dlib/FAN pipeline into this project.
- Create `tests/__init__.py`: ensures local `tests` package wins over installed site-package `tests`.
- Create `tests/test_pose_motion_core.py`: unit tests for core pose helpers.
- Create `tests/test_face_motion_core.py`: unit tests for face mapping helpers.
- Create `tests/test_pose_live2d_mapper.py`: unit tests for Stage B mapper.
- Modify `requirements.txt`: add optional URL-mode dependency `yt-dlp` and optional face dependency `mediapipe`.
- Modify `my_yolo_train_tool.py`: add pose model state, tkinter buttons, screen ROI pose recording loop, URL prompt mode, Live2D launcher, and FastAPI pose endpoints.
- Create `www/pose_record.html`: list pose records and open preview JSON/HTML.
- Create `www/live2d_dancer.html`: local Live2D desktop dancer control page with body and face parameter playback.
- Copy required local Live2D assets from `Z:\inc\javascript\live2d_demo` into `www/live2d/` if the source exists.

Do not stage unrelated generated files under `dist/`, `example_pt/`, `.superpowers/`, `.claude/`, or model binaries unless explicitly requested.

## Task 1: Pose Core Utilities

**Files:**
- Create: `pose_motion_core.py`
- Create: `tests/test_pose_motion_core.py`

- [ ] **Step 1: Write failing tests for geometry, buffering, and dancer selection**

Create `tests/test_pose_motion_core.py`:

```python
import json
import unittest

from pose_motion_core import (
    COCO17_KEYPOINTS,
    FrameBuffer,
    build_pose_record,
    compute_pose_features,
    normalize_keypoints,
    normalize_roi,
    select_main_person,
)


class PoseMotionCoreTests(unittest.TestCase):
    def test_coco17_has_expected_points(self):
        self.assertEqual(len(COCO17_KEYPOINTS), 17)
        self.assertEqual(COCO17_KEYPOINTS[5], "left_shoulder")
        self.assertEqual(COCO17_KEYPOINTS[16], "right_ankle")

    def test_normalize_roi_supports_reverse_drag(self):
        roi = normalize_roi(200, 300, 100, 120)
        self.assertEqual(roi, {"left": 100, "top": 120, "width": 100, "height": 180})

    def test_frame_buffer_drops_oldest_when_full(self):
        buf = FrameBuffer(max_frames=2)
        buf.put(0, "a")
        buf.put(1, "b")
        buf.put(2, "c")
        self.assertEqual(buf.stats()["dropped_frames"], 1)
        self.assertEqual(buf.get()["frame"], "b")
        self.assertEqual(buf.get()["frame"], "c")

    def test_select_main_person_prefers_previous_center(self):
        people = [
            {"bbox": {"x1": 0, "y1": 0, "x2": 300, "y2": 500, "confidence": 0.8}, "mean_keypoint_confidence": 0.8},
            {"bbox": {"x1": 500, "y1": 0, "x2": 620, "y2": 220, "confidence": 0.95}, "mean_keypoint_confidence": 0.95},
        ]
        selected = select_main_person(people, roi_center=(320, 240), previous_center=(560, 120))
        self.assertEqual(selected, people[1])

    def test_features_include_body_angles(self):
        kpts = [{"name": name, "x": 0.0, "y": 0.0, "confidence": 1.0} for name in COCO17_KEYPOINTS]
        for name, x, y in [
            ("left_shoulder", 0, 0),
            ("right_shoulder", 10, 0),
            ("left_hip", 1, 20),
            ("right_hip", 11, 20),
            ("left_wrist", -5, 10),
            ("right_wrist", 15, 10),
            ("left_ankle", 0, 40),
            ("right_ankle", 10, 40),
        ]:
            i = COCO17_KEYPOINTS.index(name)
            kpts[i]["x"] = x
            kpts[i]["y"] = y
        features = compute_pose_features(kpts, roi={"left": 0, "top": 0, "width": 100, "height": 100})
        self.assertIn("shoulder_angle_deg", features)
        self.assertIn("torso_angle_deg", features)
        self.assertIn("body_center_x", features)

    def test_build_pose_record_is_json_serializable(self):
        frame = {
            "frame_index": 0,
            "time_ms": 0,
            "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 20, "confidence": 0.9},
            "keypoints": [{"name": name, "x": 1, "y": 2, "confidence": 0.9} for name in COCO17_KEYPOINTS],
            "normalized_keypoints": normalize_keypoints(
                [{"name": name, "x": 1, "y": 2, "confidence": 0.9} for name in COCO17_KEYPOINTS],
                {"left": 0, "top": 0, "width": 10, "height": 20},
            ),
            "features": {},
            "quality": {"mean_keypoint_confidence": 0.9, "visible_keypoints": 17, "is_interpolated": False},
        }
        record = build_pose_record(
            project_name="demo",
            source={"type": "screen_roi", "input_mode": "screen_roi"},
            roi={"left": 0, "top": 0, "width": 10, "height": 20},
            fps_target=15,
            model_name="yolo26n-pose.pt",
            frames=[frame],
        )
        encoded = json.dumps(record, ensure_ascii=False)
        self.assertIn('"coco17"', encoded)
        self.assertEqual(record["frames"][0]["time_ms"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_pose_motion_core -v
```

Expected: FAIL because `pose_motion_core.py` does not exist.

- [ ] **Step 3: Implement `pose_motion_core.py`**

Create `pose_motion_core.py` with these public names:

```python
import datetime
import json
import math
import os
import queue
import time

COCO17_KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]

COCO17_SKELETON = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
]


class FrameBuffer:
    def __init__(self, max_frames=120):
        self._queue = queue.Queue(maxsize=max_frames)
        self._max_frames = max_frames
        self._received_frames = 0
        self._dropped_frames = 0

    def put(self, timestamp, frame, **metadata):
        item = {"timestamp": timestamp, "frame": frame}
        item.update(metadata)
        try:
            self._queue.put_nowait(item)
            self._received_frames += 1
        except queue.Full:
            try:
                self._queue.get_nowait()
                self._dropped_frames += 1
            except queue.Empty:
                pass
            self._queue.put_nowait(item)
            self._received_frames += 1

    def get(self, timeout=0.0):
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def empty(self):
        return self._queue.empty()

    def clear(self):
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def stats(self):
        return {
            "max_frames": self._max_frames,
            "queued_frames": self._queue.qsize(),
            "received_frames": self._received_frames,
            "dropped_frames": self._dropped_frames,
        }


def now_iso_taipei():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).isoformat(timespec="seconds")


def normalize_roi(x1, y1, x2, y2):
    left = int(min(x1, x2))
    top = int(min(y1, y2))
    width = int(abs(x2 - x1))
    height = int(abs(y2 - y1))
    if width <= 0 or height <= 0:
        raise ValueError("ROI width and height must be greater than zero")
    return {"left": left, "top": top, "width": width, "height": height}


def angle_deg(x1, y1, x2, y2):
    return math.degrees(math.atan2(y2 - y1, x2 - x1))


def keypoint_by_name(keypoints, name):
    for item in keypoints:
        if item.get("name") == name:
            return item
    return None


def safe_midpoint(a, b):
    if not a or not b:
        return None
    return {"x": (float(a["x"]) + float(b["x"])) / 2.0, "y": (float(a["y"]) + float(b["y"])) / 2.0}


def normalize_keypoints(keypoints, roi):
    width = float(roi["width"])
    height = float(roi["height"])
    output = []
    for kp in keypoints:
        output.append({
            "name": kp["name"],
            "x": None if kp.get("x") is None else float(kp["x"]) / width,
            "y": None if kp.get("y") is None else float(kp["y"]) / height,
            "confidence": float(kp.get("confidence", 0.0)),
        })
    return output


def compute_pose_features(keypoints, roi):
    ls = keypoint_by_name(keypoints, "left_shoulder")
    rs = keypoint_by_name(keypoints, "right_shoulder")
    lh = keypoint_by_name(keypoints, "left_hip")
    rh = keypoint_by_name(keypoints, "right_hip")
    lw = keypoint_by_name(keypoints, "left_wrist")
    rw = keypoint_by_name(keypoints, "right_wrist")
    la = keypoint_by_name(keypoints, "left_ankle")
    ra = keypoint_by_name(keypoints, "right_ankle")
    shoulder_center = safe_midpoint(ls, rs)
    hip_center = safe_midpoint(lh, rh)
    body_center = safe_midpoint(shoulder_center, hip_center)
    features = {
        "shoulder_angle_deg": angle_deg(ls["x"], ls["y"], rs["x"], rs["y"]) if ls and rs else None,
        "hip_angle_deg": angle_deg(lh["x"], lh["y"], rh["x"], rh["y"]) if lh and rh else None,
        "torso_angle_deg": angle_deg(hip_center["x"], hip_center["y"], shoulder_center["x"], shoulder_center["y"]) if hip_center and shoulder_center else None,
        "body_center_x": None if not body_center else body_center["x"] / float(roi["width"]),
        "body_center_y": None if not body_center else body_center["y"] / float(roi["height"]),
        "left_arm_angle_deg": angle_deg(ls["x"], ls["y"], lw["x"], lw["y"]) if ls and lw else None,
        "right_arm_angle_deg": angle_deg(rs["x"], rs["y"], rw["x"], rw["y"]) if rs and rw else None,
        "left_leg_angle_deg": angle_deg(lh["x"], lh["y"], la["x"], la["y"]) if lh and la else None,
        "right_leg_angle_deg": angle_deg(rh["x"], rh["y"], ra["x"], ra["y"]) if rh and ra else None,
    }
    return features


def bbox_center(bbox):
    return ((float(bbox["x1"]) + float(bbox["x2"])) / 2.0, (float(bbox["y1"]) + float(bbox["y2"])) / 2.0)


def bbox_area(bbox):
    return max(0.0, float(bbox["x2"]) - float(bbox["x1"])) * max(0.0, float(bbox["y2"]) - float(bbox["y1"]))


def distance(a, b):
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def select_main_person(people, roi_center=None, previous_center=None):
    if not people:
        return None
    if previous_center:
        return min(people, key=lambda p: distance(bbox_center(p["bbox"]), previous_center))
    if roi_center:
        return min(
            people,
            key=lambda p: (
                -float(p.get("mean_keypoint_confidence", p["bbox"].get("confidence", 0.0))),
                -bbox_area(p["bbox"]),
                distance(bbox_center(p["bbox"]), roi_center),
            ),
        )
    return max(people, key=lambda p: (float(p.get("mean_keypoint_confidence", 0.0)), bbox_area(p["bbox"])))


def build_pose_record(project_name, source, roi, fps_target, model_name, frames):
    return {
        "version": 1,
        "created_at": now_iso_taipei(),
        "project_name": project_name,
        "source": dict(source, roi=roi, fps_target=fps_target, model=model_name),
        "keypoint_format": {"name": "coco17", "points": COCO17_KEYPOINTS},
        "frames": frames,
    }


def write_json_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path
```

- [ ] **Step 4: Run tests and fix issues**

Run:

```powershell
python -m unittest tests.test_pose_motion_core -v
```

Expected: PASS.

- [ ] **Step 5: Commit scoped files**

Run:

```powershell
git add -- pose_motion_core.py tests/test_pose_motion_core.py
git -c gc.auto=0 commit -m "feat: add pose motion core helpers"
```

Expected: commit only these two files.

## Task 1A: Local Test Package Marker

**Files:**
- Create: `tests/__init__.py`

- [ ] **Step 1: Write package marker**

Create `tests/__init__.py`:

```python
"""Local test package for my_yolo_train_tool."""
```

- [ ] **Step 2: Run dotted unittest command**

Run:

```powershell
python -m unittest tests.test_pose_motion_core -v
```

Expected: PASS. This prevents the installed `site-packages/tests` package from shadowing the local tests folder.

- [ ] **Step 3: Commit scoped file**

Run:

```powershell
git add -- tests/__init__.py
git -c gc.auto=0 commit -m "test: make local tests package importable"
```

Expected: commit only `tests/__init__.py`.

## Task 2: Live2D Mapper Core

**Files:**
- Create: `pose_live2d_mapper.py`
- Create: `tests/test_pose_live2d_mapper.py`

- [ ] **Step 1: Write failing mapper tests**

Create `tests/test_pose_live2d_mapper.py`:

```python
import unittest

from pose_live2d_mapper import build_live2d_params, build_motion3


class Live2DMapperTests(unittest.TestCase):
    def sample_pose_record(self):
        return {
            "version": 1,
            "source": {"fps_target": 30},
            "frames": [
                {"time_ms": 0, "features": {"torso_angle_deg": 0, "body_center_y": 0.5, "left_arm_angle_deg": 10, "right_arm_angle_deg": -10}},
                {"time_ms": 33, "features": {"torso_angle_deg": 20, "body_center_y": 0.4, "left_arm_angle_deg": 30, "right_arm_angle_deg": -30}},
            ],
        }

    def test_build_live2d_params_clamps_values(self):
        params = build_live2d_params(self.sample_pose_record())
        ids = [p["id"] for p in params["parameters"]]
        self.assertIn("ParamBodyAngleX", ids)
        body = next(p for p in params["parameters"] if p["id"] == "ParamBodyAngleX")
        self.assertEqual(body["keys"][0]["time_ms"], 0)
        self.assertLessEqual(max(k["value"] for k in body["keys"]), 30)

    def test_build_motion3_has_curves(self):
        params = build_live2d_params(self.sample_pose_record())
        motion = build_motion3(params)
        self.assertEqual(motion["Version"], 3)
        self.assertGreater(motion["Meta"]["CurveCount"], 0)
        self.assertTrue(any(c["Target"] == "Parameter" for c in motion["Curves"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_pose_live2d_mapper -v
```

Expected: FAIL because `pose_live2d_mapper.py` does not exist.

- [ ] **Step 3: Implement mapper**

Create `pose_live2d_mapper.py` with:

```python
def clamp(value, min_value, max_value):
    if value is None:
        return 0.0
    return max(min_value, min(max_value, float(value)))


DEFAULT_MAPPING = [
    {"id": "ParamBodyAngleX", "source": "torso_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "ParamBodyBounce", "source": "body_center_y", "scale": -60.0, "offset": 30.0, "clamp": [-30, 30]},
    {"id": "ParamArmL", "source": "left_arm_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "ParamArmR", "source": "right_arm_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
]


def build_live2d_params(pose_record, mapping=None):
    mapping = mapping or DEFAULT_MAPPING
    fps = int(pose_record.get("source", {}).get("fps_target", 30) or 30)
    frames = pose_record.get("frames", [])
    duration_ms = frames[-1]["time_ms"] if frames else 0
    parameters = []
    for spec in mapping:
        lo, hi = spec["clamp"]
        keys = []
        for frame in frames:
            features = frame.get("features", {})
            raw_value = features.get(spec["source"])
            value = clamp((0.0 if raw_value is None else raw_value) * spec["scale"] + spec["offset"], lo, hi)
            keys.append({"time_ms": int(frame["time_ms"]), "value": value})
        parameters.append(dict(spec, keys=keys))
    return {"version": 1, "fps": fps, "duration_ms": int(duration_ms), "parameters": parameters}


def build_motion3(live2d_params):
    curves = []
    total_segments = 0
    total_points = 0
    for param in live2d_params.get("parameters", []):
        segments = []
        first = True
        for key in param.get("keys", []):
            time_sec = round(float(key["time_ms"]) / 1000.0, 6)
            value = float(key["value"])
            if first:
                segments.extend([time_sec, value])
                first = False
            else:
                segments.extend([0, time_sec, value])
                total_segments += 1
            total_points += 1
        curves.append({"Target": "Parameter", "Id": param["id"], "Segments": segments})
    return {
        "Version": 3,
        "Meta": {
            "Duration": round(float(live2d_params.get("duration_ms", 0)) / 1000.0, 6),
            "Fps": int(live2d_params.get("fps", 30) or 30),
            "Loop": False,
            "AreBeziersRestricted": True,
            "CurveCount": len(curves),
            "TotalSegmentCount": total_segments,
            "TotalPointCount": total_points,
            "UserDataCount": 0,
            "TotalUserDataSize": 0,
        },
        "Curves": curves,
    }
```

- [ ] **Step 4: Run mapper tests**

Run:

```powershell
python -m unittest tests.test_pose_live2d_mapper -v
```

Expected: PASS.

- [ ] **Step 5: Commit scoped files**

Run:

```powershell
git add -- pose_live2d_mapper.py tests/test_pose_live2d_mapper.py
git -c gc.auto=0 commit -m "feat: add live2d pose mapper"
```

Expected: commit only these two files.

## Task 3: Video and YouTube URL Pose Source

**Files:**
- Create: `pose_video_source.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add optional dependency**

Modify `requirements.txt` to include:

```text
yt-dlp==2026.6.9
```

If that exact version is unavailable in the local environment, use the installed/latest compatible version and record it in `history.md` after verification.

- [ ] **Step 2: Implement URL/local video processing helpers**

Create `pose_video_source.py` with public functions:

```python
import json
import os
import tempfile

import cv2

from pose_motion_core import write_json_atomic


def is_probable_youtube_url(url):
    return isinstance(url, str) and ("youtube.com/" in url or "youtu.be/" in url)


def write_source_video_info(record_folder, info):
    return write_json_atomic(os.path.join(record_folder, "source_video_info.json"), info)


def download_authorized_youtube_video(url, output_dir, max_duration_seconds=300):
    try:
        import yt_dlp
    except ImportError as ex:
        raise RuntimeError("yt-dlp 未安裝，無法處理 YouTube URL。請安裝 requirements 或改用螢幕框選模式。") from ex
    opts = {
        "outtmpl": os.path.join(output_dir, "source.%(ext)s"),
        "format": "mp4[height<=720]/mp4/best[height<=720]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = int(info.get("duration") or 0)
        if duration and duration > max_duration_seconds:
            raise RuntimeError("影片長度超過上限 %s 秒，請先換短片或調整設定。" % max_duration_seconds)
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
    return filepath, info


def iter_video_frames(video_path, fps_target=15, max_duration_seconds=300):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("無法開啟影片: %s" % video_path)
    source_fps = cap.get(cv2.CAP_PROP_FPS) or fps_target
    frame_interval = max(1, int(round(float(source_fps) / float(fps_target))))
    frame_index = 0
    emitted_index = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        time_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
        if max_duration_seconds and time_ms > max_duration_seconds * 1000:
            break
        if frame_index % frame_interval == 0:
            yield emitted_index, time_ms, frame
            emitted_index += 1
        frame_index += 1
    cap.release()
```

The actual YOLO inference integration happens in Task 5 so this module stays source-focused.

- [ ] **Step 3: Run import smoke**

Run:

```powershell
python -m py_compile pose_video_source.py
```

Expected: PASS.

- [ ] **Step 4: Commit scoped files**

Run:

```powershell
git add -- pose_video_source.py requirements.txt
git -c gc.auto=0 commit -m "feat: add authorized video pose source"
```

Expected: commit only these files.

## Task 4: Pose Inference and JSON Builder Integration

**Files:**
- Modify: `my_yolo_train_tool.py`

- [ ] **Step 1: Add imports and separate pose globals**

Modify imports near the other imports:

```python
from pose_motion_core import (
    COCO17_KEYPOINTS,
    COCO17_SKELETON,
    FrameBuffer,
    build_pose_record,
    bbox_center,
    compute_pose_features,
    normalize_keypoints,
    normalize_roi,
    select_main_person,
    write_json_atomic,
)
from pose_live2d_mapper import build_live2d_params, build_motion3
from pose_video_source import (
    download_authorized_youtube_video,
    is_probable_youtube_url,
    iter_video_frames,
    write_source_video_info,
)
```

Add separate globals near `model_file`:

```python
pose_model_file = os.path.join(basedir, "example_pt", "yolo26n-pose.pt")
pose_model = None
pose_confidence = 0.35
```

- [ ] **Step 2: Add GDATA pose state**

Extend `GDATA`:

```python
"pose_recording": False,
"pose_stop_in_progress": False,
"pose_frame_buffer": None,
"pose_frames": [],
"pose_record_folder": None,
"pose_last_output_file": "",
"pose_previous_center": None,
"pose_fps_target": 15,
```

- [ ] **Step 3: Add helper functions**

Add functions before tkinter UI construction:

```python
def ensure_pose_model():
    global pose_model
    if pose_model is None:
        if not os.path.isfile(pose_model_file):
            raise RuntimeError("找不到 pose model: %s" % pose_model_file)
        pose_model = YOLO(pose_model_file)
    return pose_model


def get_current_project_folder():
    if "project_folder" in GDATA and GDATA.get("project_folder") and os.path.isdir(GDATA["project_folder"]):
        return GDATA["project_folder"]
    raise RuntimeError("請先選擇專案")


def create_pose_record_folder(project_folder):
    folder = os.path.join(project_folder, "pose_record", "record_%s" % int(time.time()))
    os.makedirs(folder, exist_ok=True)
    os.chmod(folder, 0o777)
    return folder


def yolo_pose_result_to_people(result, roi):
    people = []
    if result.keypoints is None or result.boxes is None:
        return people
    kpt_data = result.keypoints.data.cpu().numpy()
    boxes = result.boxes
    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy() if boxes.conf is not None else [0.0] * len(xyxy)
    for person_index, points in enumerate(kpt_data):
        keypoints = []
        confidences = []
        for idx, name in enumerate(COCO17_KEYPOINTS):
            row = points[idx]
            conf = float(row[2]) if len(row) > 2 else 1.0
            keypoints.append({"name": name, "x": float(row[0]), "y": float(row[1]), "confidence": conf})
            confidences.append(conf)
        box = xyxy[person_index]
        people.append({
            "bbox": {"x1": float(box[0]), "y1": float(box[1]), "x2": float(box[2]), "y2": float(box[3]), "confidence": float(confs[person_index])},
            "keypoints": keypoints,
            "mean_keypoint_confidence": sum(confidences) / max(1, len(confidences)),
        })
    return people


def build_pose_frame(frame_index, time_ms, person, roi):
    keypoints = person["keypoints"]
    return {
        "frame_index": frame_index,
        "time_ms": int(time_ms),
        "bbox": person["bbox"],
        "center": {"x": bbox_center(person["bbox"])[0], "y": bbox_center(person["bbox"])[1]},
        "scale": 1.0,
        "quality": {
            "mean_keypoint_confidence": float(person.get("mean_keypoint_confidence", 0.0)),
            "visible_keypoints": len([p for p in keypoints if p.get("confidence", 0.0) >= pose_confidence]),
            "is_interpolated": False,
        },
        "keypoints": keypoints,
        "normalized_keypoints": normalize_keypoints(keypoints, roi),
        "features": compute_pose_features(keypoints, roi),
    }
```

- [ ] **Step 4: Run syntax check**

Run:

```powershell
python -m py_compile my_yolo_train_tool.py
```

Expected: PASS.

- [ ] **Step 5: Commit scoped file**

Run:

```powershell
git add -- my_yolo_train_tool.py
git -c gc.auto=0 commit -m "feat: add pose inference helpers"
```

Expected: commit only `my_yolo_train_tool.py`.

## Task 5: Screen ROI Pose Recorder A2

**Files:**
- Modify: `my_yolo_train_tool.py`

- [ ] **Step 1: Add pose overlay drawing**

Add `create_pose_skeleton` to `OverlayWindow` or add a separate `PoseOverlayWindow`. Use `ImageDraw.line` over a transparent image and draw COCO17 skeleton segments. Use comments in Traditional Chinese only where needed:

```python
def create_pose_skeleton(self, keypoints, lines):
    self.clear_rectangles()
    # 只畫信心度足夠的線段，避免骨架抖動時畫出錯誤連線。
    ...
```

- [ ] **Step 2: Add recorder start/stop/finalize functions**

Implement:

```python
def preflight_pose_capture(roi):
    monitor = {"left": roi["left"], "top": roi["top"], "width": roi["width"], "height": roi["height"]}
    with mss.mss(with_cursor=False) as sct:
        sct.grab(monitor)
    return True


def toggle_screen_pose_recording():
    if GDATA["pose_recording"]:
        stop_screen_pose_recording()
    else:
        start_screen_pose_recording()
```

`start_screen_pose_recording()` must:

- block if `is_run_keep_screen_predict` is true;
- require selected project and ROI;
- call `ensure_pose_model()`;
- create `pose_record_folder`;
- create `FrameBuffer(max_frames=int(GDATA["pose_fps_target"] * 5))`;
- start capture and inference threads;
- set button text to `骨架錄製(停止)`.

`stop_screen_pose_recording()` must:

- set `pose_recording` false;
- set `pose_stop_in_progress` true;
- start finalize thread.

`finish_screen_pose_recording()` must:

- wait for queue drain;
- build pose record with source `{"type": "screen_roi", "input_mode": "screen_roi", "url": None}`;
- write `pose_record.json`;
- write `preview.html`;
- set `pose_last_output_file`;
- show `messagebox.showinfo("骨架錄製完成", output_path)`;
- set button text back to `骨架錄製(開始)`.

- [ ] **Step 3: Add capture and inference loops**

Use monotonic timestamps:

```python
start_monotonic = time.monotonic()
time_ms = int((time.monotonic() - start_monotonic) * 1000)
```

The inference loop must call:

```python
results = ensure_pose_model().predict(frame_bgr, conf=pose_confidence, verbose=False)
people = yolo_pose_result_to_people(results[0], roi)
person = select_main_person(people, roi_center=(roi["width"] / 2, roi["height"] / 2), previous_center=GDATA["pose_previous_center"])
```

When `person` exists, append `build_pose_frame(...)` to `GDATA["pose_frames"]` and update overlay.

- [ ] **Step 4: Add tkinter buttons**

Increase window height enough for one extra row. Add a `pose_frame` with:

- `YouTube Pose`
- `骨架錄製(開始)`
- `Live2D 人物`

Bind `骨架錄製(開始)` to `toggle_screen_pose_recording`.

- [ ] **Step 5: Run checks**

Run:

```powershell
python -m py_compile my_yolo_train_tool.py
python -m unittest tests.test_pose_motion_core -v
```

Expected: PASS.

- [ ] **Step 6: Manual smoke**

Manual smoke:

1. Start app.
2. Select project.
3. Select ROI.
4. Start `骨架錄製`.
5. Move a person/video into ROI for 3-5 seconds.
6. Stop recording.
7. Confirm message shows `pose_record.json` path.
8. Confirm JSON has frames with increasing `time_ms`.

- [ ] **Step 7: Commit scoped file**

Run:

```powershell
git add -- my_yolo_train_tool.py
git -c gc.auto=0 commit -m "feat: add screen pose recorder"
```

Expected: commit only `my_yolo_train_tool.py`.

## Task 6: YouTube URL Pose A1

**Files:**
- Modify: `my_yolo_train_tool.py`

- [ ] **Step 1: Add URL prompt function**

Add:

```python
def start_youtube_pose_recording():
    try:
        project_folder = get_current_project_folder()
        url = simpledialog.askstring("YouTube URL Pose", "請貼上已授權可處理的 YouTube URL：")
        if not url:
            return
        if not is_probable_youtube_url(url):
            messagebox.showwarning("URL 格式不正確", "請輸入 YouTube URL，或改用螢幕框選模式。")
            return
        record_folder = create_pose_record_folder(project_folder)
        threading.Thread(target=run_youtube_pose_worker, args=(url, record_folder), daemon=True).start()
    except Exception as ex:
        messagebox.showerror("YouTube Pose 啟動失敗", str(ex))
```

- [ ] **Step 2: Add worker**

`run_youtube_pose_worker(url, record_folder)` must:

- write `source_video_info.json` at start;
- download authorized local working file into a temp directory;
- iterate frames with `iter_video_frames(..., fps_target=GDATA["pose_fps_target"])`;
- run the same pose model and frame builder used by A2;
- write `pose_record.json`;
- delete temp video folder in `finally`;
- use `root.after` to show completion/error message.

- [ ] **Step 3: Wire button**

Bind `YouTube Pose` button to `start_youtube_pose_recording`.

- [ ] **Step 4: Run checks**

Run:

```powershell
python -m py_compile my_yolo_train_tool.py pose_video_source.py
```

Expected: PASS.

- [ ] **Step 5: Manual smoke**

Manual smoke with a short authorized URL or local equivalent:

1. Click `YouTube Pose`.
2. Paste URL.
3. Confirm completion message shows `pose_record.json`.
4. Confirm temp video is not retained.
5. Confirm `source_video_info.json` exists.

- [ ] **Step 6: Commit scoped file**

Run:

```powershell
git add -- my_yolo_train_tool.py
git -c gc.auto=0 commit -m "feat: add youtube url pose mode"
```

Expected: commit only `my_yolo_train_tool.py`.

## Task 7: Pose Record Web Review

**Files:**
- Modify: `my_yolo_train_tool.py`
- Modify: `www/index.html`
- Create: `www/pose_record.html`

- [ ] **Step 1: Add FastAPI modes**

Inside `create_fastapi_app()` `/api`, add:

- `pose_record_list`: project name -> list `pose_record/record_*`
- `pose_record_convert_live2d`: project name + record name -> write `live2d_params.json` and `motion3.json`

Use existing `api_json(...)` style and path containment checks.

- [ ] **Step 2: Add `www/pose_record.html`**

Create a jQuery page using `myAjax_async_json(...)` to:

- list pose records;
- show `pose_record.json` path;
- open `preview.html`;
- trigger Live2D conversion.

- [ ] **Step 3: Add navigation entry**

In `www/index.html`, add a top-button entry next to `模型訓練`:

```html
<a href="javascript:;" reqk="a功能按鈕" reqc="a骨架動作" class="btn btn-secondary mx-2">骨架動作</a>
```

In the existing document-ready binding area, add a click handler:

```js
$("#divTop a[reqc='a骨架動作']").off().bind("click", function () {
    $("#divTop a[reqk='a功能按鈕']").removeClass("btn-primary");
    $(this).addClass("btn-primary");
    var uPROJECT_NAME = encodeURIComponent(getMemory("project_name"));
    $("#divMain").html(`
        <iframe src="/www/pose_record.html?project_name=${uPROJECT_NAME}" class="iframe_class"></iframe>
    `);
});
```

- [ ] **Step 4: Run checks**

Run:

```powershell
python -m py_compile my_yolo_train_tool.py
```

Then open:

```text
http://127.0.0.1:9487/www/pose_record.html
```

Expected: page loads and API returns `status: OK` for a selected project.

- [ ] **Step 5: Commit scoped files**

Run:

```powershell
git add -- my_yolo_train_tool.py www/index.html www/pose_record.html
git -c gc.auto=0 commit -m "feat: add pose record review page"
```

Expected: commit only these files.

## Task 8: Live2D Desktop Dancer C

**Files:**
- Modify: `my_yolo_train_tool.py`
- Create: `www/live2d_dancer.html`
- Create/copy: `www/live2d/assets/*`
- Create/copy: `www/live2d/live2d_api/*`

- [ ] **Step 1: Copy local Live2D assets**

If `Z:\inc\javascript\live2d_demo` exists, copy these into `www/live2d/`:

```text
Z:\inc\javascript\live2d_demo\assets
Z:\inc\javascript\live2d_demo\live2d_api
```

Do not copy generated logs such as `php_errors.log`.

- [ ] **Step 2: Create `www/live2d_dancer.html`**

Base it on `Z:\inc\javascript\live2d_demo\demo-control.html`, but use local paths:

```html
<link rel="stylesheet" href="/www/live2d/assets/waifu.min.css">
<script src="/www/vendor/bootstrap/bootstrap.bundle.min.js"></script>
<script src="/www/live2d/assets/waifu-tips.min.js"></script>
<script src="/www/live2d/assets/live2d.min.js"></script>
```

Expose:

```js
window.ScreenAiLive2D = {
  speak: speak,
  stopSpeak: stopSpeak,
  setExpression: setExpression,
  startMotion: startMotion,
  setParam: setParam,
  clearParams: clearParams,
  getCurrentModel: getCurrentModel
};
```

Add a file input or record selector. On click/tap character, show `要跳哪支舞？` and open the selector.

- [ ] **Step 3: Apply Live2D params from JSON**

Add JS function:

```js
function playLive2DParams(params) {
  var start = performance.now();
  var active = true;
  function tick() {
    if (!active) return;
    var elapsedMs = performance.now() - start;
    params.parameters.forEach(function (param) {
      var keys = param.keys || [];
      var current = keys[0];
      for (var i = 0; i < keys.length; i++) {
        if (keys[i].time_ms <= elapsedMs) current = keys[i];
        else break;
      }
      if (current) setParam(param.id, current.value, 1);
    });
    if (elapsedMs <= params.duration_ms) requestAnimationFrame(tick);
    else clearParams();
  }
  requestAnimationFrame(tick);
}
```

- [ ] **Step 4: Add desktop launcher**

In `my_yolo_train_tool.py`, add:

```python
def open_live2d_dancer():
    webbrowser.open("http://127.0.0.1:9487/www/live2d_dancer.html")
```

Bind `Live2D 人物` button to it.

- [ ] **Step 5: Run checks**

Run:

```powershell
python -m py_compile my_yolo_train_tool.py
```

Open:

```text
http://127.0.0.1:9487/www/live2d_dancer.html
```

Expected:

- If assets exist, character appears.
- If assets do not exist, page clearly says Live2D assets are missing.
- Loading `live2d_params.json` changes at least one visible parameter or logs applied values.

- [ ] **Step 6: Commit scoped files**

Run:

```powershell
git add -- my_yolo_train_tool.py www/live2d_dancer.html www/live2d
git -c gc.auto=0 commit -m "feat: add live2d dancer launcher"
```

Expected: do not add `dist/`, `example_pt/`, `.superpowers/`, `.claude/`, or model binaries outside `www/live2d`.

## Task 9: Face CopyCat Core Mapping

**Files:**
- Create: `face_motion_core.py`
- Create: `tests/test_face_motion_core.py`

- [ ] **Step 1: Write failing tests for face record and Live2D mapping**

Create `tests/test_face_motion_core.py`:

```python
import json
import unittest

from face_motion_core import (
    build_face_frame,
    build_face_record,
    build_live2d_face_params,
    matrix_to_euler_degrees,
)


class FaceMotionCoreTests(unittest.TestCase):
    def test_build_face_frame_is_readable(self):
        frame = build_face_frame(
            frame_index=0,
            time_ms=33,
            blendshapes={"eyeBlinkLeft": 0.8, "eyeBlinkRight": 0.2, "jawOpen": 0.5},
            landmarks=[{"x": 0.5, "y": 0.4, "z": -0.01}],
            facial_transformation_matrix=[1.0, 0.0, 0.0, 0.0] * 4,
        )
        self.assertTrue(frame["face_detected"])
        self.assertEqual(frame["quality"]["blendshape_count"], 3)
        self.assertEqual(frame["quality"]["landmark_count"], 1)

    def test_live2d_face_params_invert_eye_blink(self):
        record = {
            "version": 1,
            "source": {"fps_target": 30},
            "frames": [
                build_face_frame(
                    frame_index=0,
                    time_ms=0,
                    blendshapes={
                        "eyeBlinkLeft": 1.0,
                        "eyeBlinkRight": 0.0,
                        "jawOpen": 0.25,
                        "eyeLookUpLeft": 0.4,
                        "eyeLookUpRight": 0.4,
                    },
                    landmarks=[],
                    head_pose={"yaw": 10.0, "pitch": -5.0, "roll": 2.0},
                )
            ],
        }
        params = build_live2d_face_params(record)
        by_id = {item["id"]: item for item in params["parameters"]}
        self.assertEqual(by_id["ParamEyeLOpen"]["keys"][0]["value"], 0.0)
        self.assertEqual(by_id["ParamEyeROpen"]["keys"][0]["value"], 1.0)
        self.assertEqual(by_id["ParamMouthOpenY"]["keys"][0]["value"], 0.25)
        self.assertEqual(by_id["ParamAngleX"]["keys"][0]["value"], 10.0)
        self.assertGreater(by_id["ParamEyeBallY"]["keys"][0]["value"], 0.0)

    def test_build_face_record_is_json_serializable(self):
        frame = build_face_frame(
            frame_index=0,
            time_ms=0,
            blendshapes={"mouthSmileLeft": 0.5, "mouthSmileRight": 0.5},
            landmarks=[],
        )
        record = build_face_record(
            project_name="demo",
            source={"type": "screen_roi", "input_mode": "face_roi"},
            roi={"left": 0, "top": 0, "width": 640, "height": 480},
            fps_target=15,
            backend="mediapipe_face_landmarker",
            model_name="face_landmarker.task",
            frames=[frame],
        )
        encoded = json.dumps(record, ensure_ascii=False)
        self.assertIn("face_record", record["record_type"])
        self.assertIn("mouthSmileLeft", encoded)

    def test_matrix_to_euler_degrees_identity(self):
        pose = matrix_to_euler_degrees([1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0])
        self.assertAlmostEqual(pose["yaw"], 0.0, places=4)
        self.assertAlmostEqual(pose["pitch"], 0.0, places=4)
        self.assertAlmostEqual(pose["roll"], 0.0, places=4)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_face_motion_core -v
```

Expected: FAIL because `face_motion_core.py` does not exist.

- [ ] **Step 3: Implement `face_motion_core.py`**

Create `face_motion_core.py`:

```python
import datetime
import json
import math
import os


DEFAULT_FACE_MAPPING = [
    {"id": "ParamEyeLOpen", "source": "eyeBlinkLeft", "scale": -1.0, "offset": 1.0, "clamp": [0.0, 1.0], "bucket": "blendshapes"},
    {"id": "ParamEyeROpen", "source": "eyeBlinkRight", "scale": -1.0, "offset": 1.0, "clamp": [0.0, 1.0], "bucket": "blendshapes"},
    {"id": "ParamEyeBallX", "source": {"positive": ["eyeLookOutRight", "eyeLookInLeft"], "negative": ["eyeLookOutLeft", "eyeLookInRight"]}, "scale": 1.0, "offset": 0.0, "clamp": [-1.0, 1.0], "bucket": "blendshapes"},
    {"id": "ParamEyeBallY", "source": {"positive": ["eyeLookUpLeft", "eyeLookUpRight"], "negative": ["eyeLookDownLeft", "eyeLookDownRight"]}, "scale": 1.0, "offset": 0.0, "clamp": [-1.0, 1.0], "bucket": "blendshapes"},
    {"id": "ParamMouthOpenY", "source": "jawOpen", "scale": 1.0, "offset": 0.0, "clamp": [0.0, 1.0], "bucket": "blendshapes"},
    {"id": "ParamMouthForm", "source": ["mouthSmileLeft", "mouthSmileRight"], "scale": 2.0, "offset": -1.0, "clamp": [-1.0, 1.0], "bucket": "blendshapes"},
    {"id": "ParamBrowLY", "source": ["browInnerUp", "browOuterUpLeft"], "scale": 1.0, "offset": 0.0, "clamp": [-1.0, 1.0], "bucket": "blendshapes"},
    {"id": "ParamBrowRY", "source": ["browInnerUp", "browOuterUpRight"], "scale": 1.0, "offset": 0.0, "clamp": [-1.0, 1.0], "bucket": "blendshapes"},
    {"id": "ParamAngleX", "source": "yaw", "scale": 1.0, "offset": 0.0, "clamp": [-30.0, 30.0], "bucket": "head_pose"},
    {"id": "ParamAngleY", "source": "pitch", "scale": 1.0, "offset": 0.0, "clamp": [-30.0, 30.0], "bucket": "head_pose"},
    {"id": "ParamAngleZ", "source": "roll", "scale": 1.0, "offset": 0.0, "clamp": [-30.0, 30.0], "bucket": "head_pose"},
]


def now_iso_taipei():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).isoformat(timespec="seconds")


def clamp(value, min_value, max_value):
    if value is None:
        return 0.0
    return max(min_value, min(max_value, float(value)))


def source_value(frame, spec):
    bucket = frame.get(spec.get("bucket", "blendshapes"), {})
    source = spec["source"]
    if isinstance(source, dict):
        positive = [float(bucket.get(name, 0.0)) for name in source.get("positive", [])]
        negative = [float(bucket.get(name, 0.0)) for name in source.get("negative", [])]
        positive_mean = sum(positive) / max(1, len(positive))
        negative_mean = sum(negative) / max(1, len(negative))
        return positive_mean - negative_mean
    if isinstance(source, list):
        values = [float(bucket.get(name, 0.0)) for name in source]
        return sum(values) / max(1, len(values))
    return float(bucket.get(source, 0.0))


def matrix_to_euler_degrees(matrix):
    if not matrix:
        return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
    flat = list(matrix)
    if len(flat) < 16:
        return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
    r00, r01, r02 = flat[0], flat[1], flat[2]
    r10, r11, r12 = flat[4], flat[5], flat[6]
    r20, r21, r22 = flat[8], flat[9], flat[10]
    sy = math.sqrt(r00 * r00 + r10 * r10)
    if sy >= 1e-6:
        pitch = math.degrees(math.atan2(r21, r22))
        yaw = math.degrees(math.atan2(-r20, sy))
        roll = math.degrees(math.atan2(r10, r00))
    else:
        pitch = math.degrees(math.atan2(-r12, r11))
        yaw = math.degrees(math.atan2(-r20, sy))
        roll = 0.0
    return {"yaw": yaw, "pitch": pitch, "roll": roll}


def build_face_frame(frame_index, time_ms, blendshapes=None, landmarks=None, head_pose=None, facial_transformation_matrix=None):
    blendshapes = blendshapes or {}
    landmarks = landmarks or []
    matrix = facial_transformation_matrix or []
    if head_pose is None:
        head_pose = matrix_to_euler_degrees(matrix)
    return {
        "frame_index": int(frame_index),
        "time_ms": int(time_ms),
        "face_detected": bool(blendshapes or landmarks or matrix),
        "quality": {"blendshape_count": len(blendshapes), "landmark_count": len(landmarks)},
        "blendshapes": {str(k): float(v) for k, v in blendshapes.items()},
        "head_pose": {
            "yaw": float(head_pose.get("yaw", 0.0)),
            "pitch": float(head_pose.get("pitch", 0.0)),
            "roll": float(head_pose.get("roll", 0.0)),
        },
        "facial_transformation_matrix": [float(v) for v in matrix],
        "landmarks": landmarks,
    }


def build_face_record(project_name, source, roi, fps_target, backend, model_name, frames):
    source_data = dict(source)
    source_data.update({"roi": roi, "fps_target": fps_target, "backend": backend, "model": model_name})
    return {
        "version": 1,
        "record_type": "face_record",
        "created_at": now_iso_taipei(),
        "project_name": project_name,
        "source": source_data,
        "frames": frames,
    }


def build_live2d_face_params(face_record, mapping=None):
    mapping = mapping or DEFAULT_FACE_MAPPING
    fps = int(face_record.get("source", {}).get("fps_target", 30) or 30)
    frames = face_record.get("frames", [])
    duration_ms = int(frames[-1]["time_ms"]) if frames else 0
    parameters = []
    for spec in mapping:
        lo, hi = spec["clamp"]
        keys = []
        for frame in frames:
            raw = source_value(frame, spec)
            value = clamp(raw * float(spec["scale"]) + float(spec["offset"]), lo, hi)
            keys.append({"time_ms": int(frame["time_ms"]), "value": value})
        parameters.append(dict(spec, keys=keys))
    return {
        "version": 1,
        "record_type": "live2d_face_params",
        "fps": fps,
        "duration_ms": duration_ms,
        "parameters": parameters,
    }


def write_json_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path
```

- [ ] **Step 4: Run tests and syntax check**

Run:

```powershell
python -m unittest tests.test_face_motion_core -v
python -m py_compile face_motion_core.py
```

Expected: PASS.

- [ ] **Step 5: Commit scoped files**

Run:

```powershell
git add -- face_motion_core.py tests/test_face_motion_core.py
git -c gc.auto=0 commit -m "feat: add face copycat mapping core"
```

Expected: commit only these two files.

## Task 10: MediaPipe Face Tracking Source

**Files:**
- Create: `face_tracking_source.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add optional MediaPipe dependency**

Modify `requirements.txt` to include:

```text
mediapipe==0.10.35
```

This version is available for the current Python environment. If install conflicts with the existing TensorFlow stack, keep the import optional and record the conflict in `history.md`.

- [ ] **Step 2: Implement MediaPipe wrapper**

Create `face_tracking_source.py`:

```python
import cv2

from face_motion_core import build_face_frame


def mediapipe_available():
    try:
        import mediapipe  # noqa: F401
        return True
    except ImportError:
        return False


class MediaPipeFaceTracker:
    def __init__(self, model_path, running_mode="VIDEO", num_faces=1):
        if not mediapipe_available():
            raise RuntimeError("mediapipe 未安裝，無法啟用表情 CopyCat。")
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        mode = getattr(vision.RunningMode, running_mode)
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mode,
            num_faces=num_faces,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
        )
        self._mp = mp
        self._vision = vision
        self._running_mode = running_mode
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def close(self):
        if self._landmarker:
            self._landmarker.close()
            self._landmarker = None

    def detect_frame(self, frame_bgr, frame_index, time_ms):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        if self._running_mode == "IMAGE":
            result = self._landmarker.detect(mp_image)
        else:
            result = self._landmarker.detect_for_video(mp_image, int(time_ms))
        return face_result_to_frame(result, frame_index, time_ms)


def face_result_to_frame(result, frame_index, time_ms):
    if not result or not result.face_landmarks:
        return build_face_frame(frame_index=frame_index, time_ms=time_ms, blendshapes={}, landmarks=[])

    landmarks = []
    for item in result.face_landmarks[0]:
        landmarks.append({"x": float(item.x), "y": float(item.y), "z": float(item.z)})

    blendshapes = {}
    if result.face_blendshapes:
        for category in result.face_blendshapes[0]:
            blendshapes[category.category_name] = float(category.score)

    matrix = []
    if result.facial_transformation_matrixes:
        raw_matrix = result.facial_transformation_matrixes[0]
        matrix = [float(v) for row in raw_matrix for v in row]

    return build_face_frame(
        frame_index=frame_index,
        time_ms=time_ms,
        blendshapes=blendshapes,
        landmarks=landmarks,
        facial_transformation_matrix=matrix,
    )
```

- [ ] **Step 3: Run import/syntax smoke**

Run:

```powershell
python -m py_compile face_tracking_source.py
python - <<'PY'
from face_tracking_source import mediapipe_available
print("mediapipe_available=", mediapipe_available())
PY
```

Expected: syntax PASS. `mediapipe_available` may print `False` until requirements are installed.

- [ ] **Step 4: Commit scoped files**

Run:

```powershell
git add -- face_tracking_source.py requirements.txt
git -c gc.auto=0 commit -m "feat: add mediapipe face tracking source"
```

Expected: commit only these files.

## Task 11: Face CopyCat UI and Live2D Face Playback

**Files:**
- Modify: `my_yolo_train_tool.py`
- Modify: `www/live2d_dancer.html`

- [ ] **Step 1: Add face imports and globals**

In `my_yolo_train_tool.py`, add:

```python
from face_motion_core import build_face_record, build_live2d_face_params, write_json_atomic as write_face_json_atomic
from face_tracking_source import MediaPipeFaceTracker, mediapipe_available
```

Add globals near pose state:

```python
face_model_file = os.path.join(basedir, "models", "face_landmarker.task")
face_tracker = None
face_fps_target = 15
```

Extend `GDATA`:

```python
"face_recording": False,
"face_stop_in_progress": False,
"face_frames": [],
"face_record_folder": None,
"face_last_output_file": "",
```

- [ ] **Step 2: Add face tracker helpers**

Add:

```python
def ensure_face_tracker():
    global face_tracker
    if face_tracker is None:
        if not mediapipe_available():
            raise RuntimeError("mediapipe 未安裝，請先安裝 requirements 或暫時使用骨架錄製。")
        if not os.path.isfile(face_model_file):
            raise RuntimeError("找不到 face landmarker model: %s" % face_model_file)
        face_tracker = MediaPipeFaceTracker(face_model_file, running_mode="VIDEO", num_faces=1)
    return face_tracker


def create_face_record_folder(project_folder):
    folder = os.path.join(project_folder, "face_record", "record_%s" % int(time.time()))
    os.makedirs(folder, exist_ok=True)
    os.chmod(folder, 0o777)
    return folder
```

- [ ] **Step 3: Add recording toggle**

Add:

```python
def toggle_face_copycat_recording():
    if GDATA["face_recording"]:
        stop_face_copycat_recording()
    else:
        start_face_copycat_recording()
```

`start_face_copycat_recording()` must:

- require selected project and ROI;
- call `ensure_face_tracker()`;
- create `face_record_folder`;
- clear `face_frames`;
- start a worker thread that captures ROI frames with `mss(with_cursor=False)`;
- sample at `face_fps_target`;
- call `ensure_face_tracker().detect_frame(frame_bgr, frame_index, time_ms)`;
- append frames to `GDATA["face_frames"]`;
- set the button text to `表情 CopyCat(停止)`.

`stop_face_copycat_recording()` must set `face_recording` false and finalize on a worker thread.

Finalize must write:

```python
face_record = build_face_record(
    project_name=GDATA.get("project_name", ""),
    source={"type": "screen_roi", "input_mode": "face_roi"},
    roi=roi,
    fps_target=face_fps_target,
    backend="mediapipe_face_landmarker",
    model_name=os.path.basename(face_model_file),
    frames=GDATA["face_frames"],
)
face_path = os.path.join(GDATA["face_record_folder"], "face_record.json")
write_face_json_atomic(face_path, face_record)
params = build_live2d_face_params(face_record)
write_face_json_atomic(os.path.join(GDATA["face_record_folder"], "live2d_face_params.json"), params)
```

Then report `face_record.json` path with `messagebox.showinfo`.

- [ ] **Step 4: Add tkinter button**

Add a `表情 CopyCat` button next to `骨架錄製(開始)` and bind it to `toggle_face_copycat_recording`.

- [ ] **Step 5: Add Live2D face parameter playback**

In `www/live2d_dancer.html`, add support for loading `live2d_face_params.json` with the same `setParam` API:

```js
function playLive2DFaceParams(params) {
  var start = performance.now();
  function tick() {
    var elapsedMs = performance.now() - start;
    (params.parameters || []).forEach(function (param) {
      var keys = param.keys || [];
      var current = keys[0];
      for (var i = 0; i < keys.length; i++) {
        if (keys[i].time_ms <= elapsedMs) current = keys[i];
        else break;
      }
      if (current) setParam(param.id, current.value, 1);
    });
    if (elapsedMs <= (params.duration_ms || 0)) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
```

The page can decide whether loaded JSON is body or face by checking `record_type === "live2d_face_params"`.

- [ ] **Step 6: Run checks**

Run:

```powershell
python -m py_compile my_yolo_train_tool.py face_motion_core.py face_tracking_source.py
python -m unittest tests.test_face_motion_core -v
```

Expected: PASS. Manual face smoke may report missing `face_landmarker.task`; that is acceptable if the UI message is clear.

- [ ] **Step 7: Commit scoped files**

Run:

```powershell
git add -- my_yolo_train_tool.py www/live2d_dancer.html
git -c gc.auto=0 commit -m "feat: add face copycat live2d playback"
```

Expected: commit only these files.

## Task 12: Final Verification and History

**Files:**
- Modify: `history.md`

- [ ] **Step 1: Run unit tests**

Run:

```powershell
python -m unittest tests.test_pose_motion_core tests.test_pose_live2d_mapper tests.test_face_motion_core -v
```

Expected: PASS.

- [ ] **Step 2: Run syntax checks**

Run:

```powershell
python -m py_compile my_yolo_train_tool.py pose_motion_core.py pose_video_source.py pose_live2d_mapper.py face_motion_core.py face_tracking_source.py
```

Expected: PASS.

- [ ] **Step 3: Run manual smoke checks**

Manual smoke checklist:

1. Existing screenshot hotkey `CTRL+F2` still works.
2. Existing desktop detection still starts/stops.
3. Screen ROI pose records 3-5 seconds and reports `pose_record.json`.
4. YouTube URL pose processes an authorized short clip or reports clear failure.
5. Web pose list loads.
6. Conversion writes `live2d_params.json` and `motion3.json`.
7. Live2D dancer page opens and either loads a character or reports missing assets.
8. Face CopyCat writes `face_record.json` and `live2d_face_params.json`, or clearly reports missing MediaPipe/model setup.

- [ ] **Step 4: Update `history.md`**

Add a dated section summarizing:

- two Stage A input modes;
- shared pose JSON output;
- Live2D mapper output;
- Live2D dancer launcher status;
- Face CopyCat backend choice and output status;
- known limitations.

- [ ] **Step 5: Commit final docs**

Run:

```powershell
git add -- history.md
git -c gc.auto=0 commit -m "docs: record pose live2d workflow progress"
```

Expected: commit only `history.md`.
