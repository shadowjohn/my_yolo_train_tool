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

    def test_features_tolerate_missing_keypoint_coordinates(self):
        kpts = [{"name": name, "x": 0.0, "y": 0.0, "confidence": 1.0} for name in COCO17_KEYPOINTS]
        kpts[COCO17_KEYPOINTS.index("left_shoulder")]["x"] = None
        kpts[COCO17_KEYPOINTS.index("left_shoulder")]["y"] = None
        features = compute_pose_features(kpts, roi={"left": 0, "top": 0, "width": 100, "height": 100})
        self.assertIsNone(features["shoulder_angle_deg"])
        self.assertIsNone(features["left_arm_angle_deg"])
        self.assertIsNone(features["torso_angle_deg"])

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
