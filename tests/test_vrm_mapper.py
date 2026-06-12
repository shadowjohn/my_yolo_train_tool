import unittest
from pose_vrm_mapper import euler_to_quaternion, build_vrm_bones_animation

class VRMMapperTests(unittest.TestCase):
    def test_euler_to_quaternion_zero(self):
        q = euler_to_quaternion(0, 0, 0)
        self.assertEqual(q, [0.0, 0.0, 0.0, 1.0])

    def test_build_vrm_bones_animation(self):
        pose_record = {
            "version": 1,
            "source": {"fps_target": 30},
            "frames": [
                {
                    "time_ms": 0,
                    "features": {
                        "head_angle_x_deg": 10.0,
                        "head_angle_y_deg": -5.0,
                        "head_angle_z_deg": 0.0,
                        "torso_angle_deg": 5.0,
                        "left_arm_angle_deg": 45.0,
                        "right_arm_angle_deg": -45.0,
                        "left_elbow_angle_deg": 90.0,
                        "right_elbow_angle_deg": 180.0,
                        "left_leg_angle_deg": 90.0,
                        "right_leg_angle_deg": 90.0,
                        "body_center_x": 0.5,
                        "body_center_y": 0.5
                    }
                }
            ]
        }
        anim = build_vrm_bones_animation(pose_record)
        self.assertEqual(anim["version"], 1)
        self.assertEqual(anim["fps"], 30)
        self.assertEqual(anim["duration_ms"], 0)
        self.assertIn("head", anim["bones"])
        self.assertIn("leftUpperArm", anim["bones"])
        self.assertEqual(len(anim["bones"]["head"]), 1)
        self.assertEqual(anim["bones"]["head"][0]["time_ms"], 0)
        self.assertEqual(len(anim["hips_position"]), 1)
        # Hips position for center x=0.5, y=0.5 should be [0.0, 0.0, 0.0]
        self.assertEqual(anim["hips_position"][0]["pos"], [0.0, 0.0, 0.0])

if __name__ == "__main__":
    unittest.main()
