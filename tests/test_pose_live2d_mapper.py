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
