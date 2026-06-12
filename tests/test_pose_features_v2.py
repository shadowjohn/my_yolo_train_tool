import unittest
import math
from pose_motion_core import (
    COCO17_KEYPOINTS,
    compute_pose_features,
    smooth_features,
    joint_angle_deg,
)
from pose_live2d_mapper import (
    DEFAULT_MAPPING,
    build_live2d_params,
    apply_ema_smoothing,
)


class PoseFeaturesV2Tests(unittest.TestCase):
    def test_joint_angle_deg(self):
        # Straight line: angle should be 180 degrees
        p1 = {"x": 0.0, "y": 0.0}
        p2 = {"x": 0.0, "y": 1.0}
        p3 = {"x": 0.0, "y": 2.0}
        self.assertAlmostEqual(joint_angle_deg(p1, p2, p3), 180.0, places=2)

        # Right angle (90 degrees)
        p1 = {"x": 1.0, "y": 0.0}
        p2 = {"x": 0.0, "y": 0.0}
        p3 = {"x": 0.0, "y": 1.0}
        self.assertAlmostEqual(joint_angle_deg(p1, p2, p3), 90.0, places=2)

    def test_compute_pose_features_v2_all_keys_exist(self):
        kpts = [{"name": name, "x": 0.0, "y": 0.0, "confidence": 1.0} for name in COCO17_KEYPOINTS]
        features = compute_pose_features(kpts, roi={"left": 0, "top": 0, "width": 100, "height": 100})
        
        expected_keys = [
            "shoulder_angle_deg", "hip_angle_deg", "torso_angle_deg",
            "body_center_x", "body_center_y", "left_arm_angle_deg",
            "right_arm_angle_deg", "left_leg_angle_deg", "right_leg_angle_deg",
            "head_angle_x_deg", "head_angle_y_deg", "head_angle_z_deg",
            "left_elbow_angle_deg", "right_elbow_angle_deg",
            "left_shoulder_raise", "right_shoulder_raise"
        ]
        for key in expected_keys:
            self.assertIn(key, features)

    def test_head_rotations(self):
        kpts = [{"name": name, "x": 0.0, "y": 0.0, "confidence": 1.0} for name in COCO17_KEYPOINTS]
        # Nose is directly above shoulder center: head_angle_x should be 0
        # Left shoulder at (40, 50), Right shoulder at (60, 50). Center is (50, 50).
        # Nose at (50, 40)
        # Shoulder width is 20
        kpts[COCO17_KEYPOINTS.index("left_shoulder")].update({"x": 40.0, "y": 50.0})
        kpts[COCO17_KEYPOINTS.index("right_shoulder")].update({"x": 60.0, "y": 50.0})
        kpts[COCO17_KEYPOINTS.index("nose")].update({"x": 50.0, "y": 38.0}) # distance = 12 (0.6 of shoulder width)
        
        features = compute_pose_features(kpts, roi={"left": 0, "top": 0, "width": 100, "height": 100})
        self.assertAlmostEqual(features["head_angle_x_deg"], 0.0, places=2)
        # Ratio = 12 / 20 = 0.6. Pitch angle = (0.6 - 0.6)*90 = 0.0
        self.assertAlmostEqual(features["head_angle_y_deg"], 0.0, places=2)

        # Nose shifts right to (55, 38). head_angle_x_deg should be positive
        kpts[COCO17_KEYPOINTS.index("nose")].update({"x": 55.0, "y": 38.0})
        features = compute_pose_features(kpts, roi={"left": 0, "top": 0, "width": 100, "height": 100})
        self.assertGreater(features["head_angle_x_deg"], 0.0)

    def test_smooth_features_ema(self):
        frames = [
            {"val": 10.0},
            {"val": 20.0},
            {"val": 30.0},
        ]
        # EMA alpha = 0.5
        # f0: 10.0
        # f1: 0.5 * 20.0 + 0.5 * 10.0 = 15.0
        # f2: 0.5 * 30.0 + 0.5 * 15.0 = 22.5
        smoothed = smooth_features(frames, alpha=0.5)
        self.assertEqual(len(smoothed), 3)
        self.assertAlmostEqual(smoothed[0]["val"], 10.0, places=2)
        self.assertAlmostEqual(smoothed[1]["val"], 15.0, places=2)
        self.assertAlmostEqual(smoothed[2]["val"], 22.5, places=2)

    def test_live2d_mapper_with_ema(self):
        pose_record = {
            "version": 1,
            "source": {"fps_target": 30},
            "frames": [
                {"time_ms": 0, "features": {"head_angle_x_deg": 10.0}},
                {"time_ms": 33, "features": {"head_angle_x_deg": 20.0}},
            ]
        }
        # Under PARAM_ANGLE_X, source = head_angle_x_deg, scale = 1.0, offset = 0.0
        # Without smoothing: values are 10.0 and 20.0
        # With ema_alpha = 0.5: values are 10.0 and 15.0
        params = build_live2d_params(pose_record, ema_alpha=0.5)
        param_x = next(p for p in params["parameters"] if p["id"] == "PARAM_ANGLE_X")
        self.assertAlmostEqual(param_x["keys"][0]["value"], 10.0, places=2)
        self.assertAlmostEqual(param_x["keys"][1]["value"], 15.0, places=2)


if __name__ == "__main__":
    unittest.main()
