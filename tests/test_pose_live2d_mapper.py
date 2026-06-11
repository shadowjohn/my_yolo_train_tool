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
        self.assertEqual(params["source_pose_record"], "pose_record.json")
        self.assertEqual(params["duration_ms"], 33)
        body = next(p for p in params["parameters"] if p["id"] == "ParamBodyAngleX")
        self.assertEqual(body["keys"][0]["time_ms"], 0)
        self.assertLessEqual(max(k["value"] for k in body["keys"]), 30)

    def test_build_motion3_has_curves(self):
        params = build_live2d_params(self.sample_pose_record())
        motion = build_motion3(params)
        self.assertEqual(motion["Version"], 3)
        self.assertGreater(motion["Meta"]["CurveCount"], 0)
        self.assertTrue(any(c["Target"] == "Parameter" for c in motion["Curves"]))
        self.assertEqual(motion["Meta"]["CurveCount"], 4)
        self.assertEqual(motion["Meta"]["TotalSegmentCount"], 4)
        self.assertEqual(motion["Meta"]["TotalPointCount"], 8)
        self.assertEqual(motion["Curves"][0]["Segments"], [0.0, 0.0, 0, 0.033, 10.0])

    def test_build_motion3_skips_empty_parameter_curves(self):
        motion = build_motion3({
            "version": 1,
            "fps": 30,
            "duration_ms": 0,
            "parameters": [
                {"id": "ParamBodyAngleX", "keys": []},
            ],
        })
        self.assertEqual(motion["Meta"]["CurveCount"], 0)
        self.assertEqual(motion["Meta"]["TotalSegmentCount"], 0)
        self.assertEqual(motion["Meta"]["TotalPointCount"], 0)
        self.assertEqual(motion["Curves"], [])

    def test_build_motion3_skips_single_key_parameter_curves(self):
        motion = build_motion3({
            "version": 1,
            "fps": 30,
            "duration_ms": 0,
            "parameters": [
                {"id": "ParamBodyAngleX", "keys": [{"time_ms": 0, "value": 1.0}]},
            ],
        })
        self.assertEqual(motion["Meta"]["CurveCount"], 0)
        self.assertEqual(motion["Curves"], [])

    def test_build_live2d_params_supports_custom_source_name(self):
        params = build_live2d_params(
            self.sample_pose_record(),
            mapping=[{"id": "ParamBodyAngleX", "source": "missing", "scale": 1.0, "offset": 2.0, "clamp": [-5, 5]}],
            source_pose_record="record_1/pose_record.json",
        )
        self.assertEqual(params["source_pose_record"], "record_1/pose_record.json")
        self.assertEqual(params["parameters"][0]["keys"][0]["value"], 2.0)


if __name__ == "__main__":
    unittest.main()
