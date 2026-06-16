import os
import tempfile
import unittest

import cv2
import numpy as np

from pose_video_source import is_probable_youtube_url, iter_video_frames


class PoseVideoSourceTests(unittest.TestCase):
    def test_is_probable_youtube_url(self):
        self.assertTrue(is_probable_youtube_url("https://www.youtube.com/watch?v=abc"))
        self.assertTrue(is_probable_youtube_url("https://youtu.be/abc"))
        self.assertFalse(is_probable_youtube_url("https://example.com/video.mp4"))

    def test_iter_video_frames_samples_with_increasing_indexes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = os.path.join(tmp_dir, "sample.mp4")
            writer = cv2.VideoWriter(
                video_path,
                cv2.VideoWriter_fourcc(*"mp4v"),
                10,
                (32, 24),
            )
            for i in range(10):
                frame = np.full((24, 32, 3), i * 20, dtype=np.uint8)
                writer.write(frame)
            writer.release()

            frames = list(iter_video_frames(video_path, fps_target=5, max_duration_seconds=2))

        self.assertGreaterEqual(len(frames), 4)
        self.assertEqual(frames[0][0], 0)
        self.assertTrue(all(frames[i][0] < frames[i + 1][0] for i in range(len(frames) - 1)))
        self.assertTrue(all(frames[i][1] <= frames[i + 1][1] for i in range(len(frames) - 1)))
        self.assertEqual(frames[0][2].shape[:2], (24, 32))


if __name__ == "__main__":
    unittest.main()
