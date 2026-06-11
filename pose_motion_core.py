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
    if not a or not b or a.get("x") is None or a.get("y") is None or b.get("x") is None or b.get("y") is None:
        return None
    return {"x": (float(a["x"]) + float(b["x"])) / 2.0, "y": (float(a["y"]) + float(b["y"])) / 2.0}


def has_xy(point):
    return bool(point) and point.get("x") is not None and point.get("y") is not None


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
        "shoulder_angle_deg": angle_deg(ls["x"], ls["y"], rs["x"], rs["y"]) if has_xy(ls) and has_xy(rs) else None,
        "hip_angle_deg": angle_deg(lh["x"], lh["y"], rh["x"], rh["y"]) if has_xy(lh) and has_xy(rh) else None,
        "torso_angle_deg": angle_deg(hip_center["x"], hip_center["y"], shoulder_center["x"], shoulder_center["y"]) if hip_center and shoulder_center else None,
        "body_center_x": None if not body_center else body_center["x"] / float(roi["width"]),
        "body_center_y": None if not body_center else body_center["y"] / float(roi["height"]),
        "left_arm_angle_deg": angle_deg(ls["x"], ls["y"], lw["x"], lw["y"]) if has_xy(ls) and has_xy(lw) else None,
        "right_arm_angle_deg": angle_deg(rs["x"], rs["y"], rw["x"], rw["y"]) if has_xy(rs) and has_xy(rw) else None,
        "left_leg_angle_deg": angle_deg(lh["x"], lh["y"], la["x"], la["y"]) if has_xy(lh) and has_xy(la) else None,
        "right_leg_angle_deg": angle_deg(rh["x"], rh["y"], ra["x"], ra["y"]) if has_xy(rh) and has_xy(ra) else None,
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
