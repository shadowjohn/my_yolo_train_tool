import unittest
from pathlib import Path


PAGE = Path(__file__).resolve().parents[1] / "www" / "vrm_dancer.html"


class VRMDancerPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_page_has_vrm_components(self):
        for text in ["原影片", "火柴人", "3D VRM", "同步時間軸"]:
            self.assertIn(text, self.html)
        for element_id in [
            'id="sourceVideo"',
            'id="skeletonCanvas"',
            'id="vrmStage"',
            'id="timeline"',
        ]:
            self.assertIn(element_id, self.html)

    def test_page_supports_vrm_bones_animation(self):
        self.assertIn("applyVRMBonesAnimationAt", self.html)
        self.assertIn("state.poseRecord.bones", self.html)
        self.assertIn("duration_ms", self.html)
        self.assertIn("此檔案為 3D 骨骼旋轉格式 (vrm_animation.json)", self.html)


if __name__ == "__main__":
    unittest.main()
