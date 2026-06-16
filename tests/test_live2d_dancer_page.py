import unittest
from pathlib import Path


PAGE = Path(__file__).resolve().parents[1] / "www" / "live2d_dancer.html"
ASSETS = PAGE.parent / "live2d" / "assets"


class Live2DDancerPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_page_has_three_synchronized_comparison_panels(self):
        for text in ["原影片", "火柴人", "Live2D", "同步時間軸"]:
            self.assertIn(text, self.html)
        for element_id in [
            'id="sourceVideo"',
            'id="sourceVideoMissing"',
            'id="skeletonCanvas"',
            'id="live2dStage"',
            'id="timeline"',
        ]:
            self.assertIn(element_id, self.html)

    def test_page_supports_video_url_and_frame_controls(self):
        for token in [
            "query.video_url",
            "loadSourceVideo",
            "drawSkeletonAt",
            "stepFrame(-1)",
            "stepFrame(1)",
        ]:
            self.assertIn(token, self.html)

    def test_page_defaults_to_fullbody_and_falls_back_to_shizuku(self):
        for token in [
            "hiyori",
            "model3.json",
            "loadFullbodyModel",
            "fallbackToShizuku",
            'query.model || "hiyori"',
            "此角色只能近似手臂/身體，腿部不保證對齊",
        ]:
            self.assertIn(token, self.html)
        self.assertNotIn('query.model || "mock_hiyori"', self.html)
        self.assertNotIn("fallbackToMockHiyori", self.html)

    def test_page_registers_official_model3_samples_for_real_live2d(self):
        for token in [
            "live2dcubismcore.min.js",
            "pixi.min.js",
            "pixi-live2d-display",
            "ren: {",
            "mark: {",
            "hiyori: {",
            "/www/live2d/models/ren/Ren.model3.json",
            "/www/live2d/models/mark/Mark.model3.json",
            "/www/live2d/models/hiyori/Hiyori.model3.json",
            "ParamLegL",
            "ParamLegR",
            "ParamLeftLeg",
            "ParamRightLeg",
        ]:
            self.assertIn(token, self.html)

    def test_three_views_have_balanced_stage_sizing(self):
        for token in [
            "grid-template-columns: repeat(3, minmax(0, 1fr))",
            "height: min(72vh, 680px)",
            "aspect-ratio: 10 / 13",
            "object-fit: contain",
        ]:
            self.assertIn(token, self.html)

    def test_model3_fallback_keeps_fullbody_canvas_in_dom(self):
        for token in [
            "function ensureFullbodyCanvas",
            "state.fullbodyApp.destroy(false",
            "ensureFullbodyCanvas()",
        ]:
            self.assertIn(token, self.html)

    def test_cubism4_runtime_globals_are_bridged_before_plugin_loads(self):
        self.assertIn("/www/live2d/assets/live2d-runtime-shim.js", self.html)
        self.assertLess(
            self.html.index("live2d-runtime-shim.js"),
            self.html.index("pixi-live2d-display-cubism4.min.js"),
        )

        shim = ASSETS / "live2d-runtime-shim.js"
        self.assertTrue(shim.exists())
        script = shim.read_text(encoding="utf-8")
        for token in [
            "window.Live2DCubismCore = Live2DCubismCore",
            "window.PIXI = PIXI",
        ]:
            self.assertIn(token, script)

    def test_playback_stops_at_end_instead_of_wrapping_video(self):
        self.assertIn("seekTo(state.durationMs, true);", self.html)
        self.assertIn("if (state.currentTimeMs >= state.durationMs) seekTo(0);", self.html)
        self.assertNotIn("next % state.durationMs", self.html)

    def test_vrm_format_detection_error(self):
        self.assertIn("偵測到 VRM 3D 骨骼動畫格式 (vrm_animation.json)", self.html)
        self.assertIn("data.bones", self.html)

    def test_internal_model_update_override(self):
        self.assertIn("model.internalModel.update = function (dt, now)", self.html)
        self.assertIn("shouldRequestIdleMotion = function () { return false; }", self.html)


if __name__ == "__main__":
    unittest.main()
