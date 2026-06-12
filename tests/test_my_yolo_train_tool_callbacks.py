import ast
import glob
import os
import shutil
import tempfile
import tokenize
import types
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "my_yolo_train_tool.py"


def load_functions(*function_names, extra_globals=None):
    with tokenize.open(MODULE_PATH) as source_file:
        tree = ast.parse(source_file.read(), filename=str(MODULE_PATH))

    selected = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in function_names
    ]
    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    if extra_globals:
        namespace.update(extra_globals)
    exec(compile(module, str(MODULE_PATH), "exec"), namespace)
    return namespace


class FakeMenu:
    def __init__(self):
        self.commands = []
        self.deleted = False

    def delete(self, *args):
        self.deleted = True

    def add_command(self, **kwargs):
        self.commands.append(kwargs)


class FakeOptionMenu:
    def __init__(self):
        self.menu = FakeMenu()
        self.pack_calls = []

    def __getitem__(self, key):
        if key != "menu":
            raise KeyError(key)
        return self.menu

    def pack(self, **kwargs):
        self.pack_calls.append(kwargs)


class FakeVar:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeButton:
    def __init__(self):
        self.config_calls = []

    def config(self, **kwargs):
        self.config_calls.append(kwargs)


class FakeMy:
    def __init__(self):
        self.glob_patterns = []

    def mkdir(self, path, recursive=False):
        os.makedirs(path, exist_ok=True)

    def glob(self, pattern):
        self.glob_patterns.append(pattern)
        return glob.glob(pattern)


class FakeTk:
    NORMAL = "normal"
    DISABLED = "disabled"
    LEFT = "left"

    @staticmethod
    def _setit(var, value):
        return lambda: var.set(value)


class FakeWidget:
    def __init__(self, widget_class="Frame"):
        self.widget_class = widget_class

    def winfo_class(self):
        return self.widget_class


class FakeRoot:
    def __init__(self, x=None, y=None, window_x=100, window_y=200):
        self.x = x
        self.y = y
        self.window_x = window_x
        self.window_y = window_y
        self.geometry_calls = []

    def winfo_x(self):
        return self.window_x

    def winfo_y(self):
        return self.window_y

    def geometry(self, value):
        self.geometry_calls.append(value)


class FakeTkRoot:
    def after(self, delay, callback):
        callback()


class FakeFrame:
    shape = (720, 1280, 3)


class FakePoseModel:
    def predict(self, frame, imgsz, conf, verbose):
        return [object()]


class MyYoloTrainToolCallbackTests(unittest.TestCase):
    def make_project_globals(self, base_dir):
        fake_my = FakeMy()
        gdata = {
            "basedir": base_dir,
            "UI": {
                "select_project_selected_menu": FakeOptionMenu(),
                "select_project_selected": FakeVar(),
                "select_area_button": FakeButton(),
                "status_label": FakeButton(),
            },
        }
        simpledialog = types.SimpleNamespace(askstring=lambda title, prompt: "demo")
        messagebox = types.SimpleNamespace(
            showwarning=lambda *args, **kwargs: None,
            showinfo=lambda *args, **kwargs: None,
        )
        return {
            "GDATA": gdata,
            "my": fake_my,
            "os": os,
            "simpledialog": simpledialog,
            "messagebox": messagebox,
            "tk": FakeTk,
        }, gdata, fake_my

    def test_new_project_selects_created_project_before_counting_files(self):
        with tempfile.TemporaryDirectory() as base_dir:
            os.makedirs(os.path.join(base_dir, "data", "projects"))
            globals_, gdata, fake_my = self.make_project_globals(base_dir)
            namespace = load_functions(
                "project_get_list_all",
                "method_count_wait_process_files",
                "reload_projects",
                "new_project",
                extra_globals=globals_,
            )

            namespace["new_project"]()

            expected_project_folder = os.path.join(
                base_dir, "data", "projects", "demo"
            )
            self.assertEqual(gdata["project_folder"], expected_project_folder)
            self.assertEqual(gdata["UI"]["select_project_selected"].get(), "demo")
            self.assertEqual(gdata["wait_process_files"], 0)
            self.assertEqual(fake_my.glob_patterns, [os.path.join(expected_project_folder, "*.jpg")])

    def test_win_do_move_ignores_motion_when_drag_start_was_cleared(self):
        root = FakeRoot(x=None, y=None)
        namespace = load_functions("win_do_move", extra_globals={"root": root})
        event = types.SimpleNamespace(widget=FakeWidget(), x=30, y=40)

        namespace["win_do_move"](event)

        self.assertEqual(root.geometry_calls, [])

    def test_win_do_move_updates_geometry_after_drag_start(self):
        root = FakeRoot(x=10, y=15, window_x=100, window_y=200)
        namespace = load_functions("win_do_move", extra_globals={"root": root})
        event = types.SimpleNamespace(widget=FakeWidget(), x=25, y=45)

        namespace["win_do_move"](event)

        self.assertEqual(root.geometry_calls, ["+115+230"])

    def test_youtube_pose_worker_reports_download_and_frame_progress(self):
        statuses = []
        finished = []
        person = {
            "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 20, "confidence": 0.9},
            "keypoints": [],
            "mean_keypoint_confidence": 0.9,
        }

        def iter_video_frames(video_path, fps_target, max_duration_seconds):
            for i in range(6):
                yield i, i * 100, FakeFrame()

        def download_video(url, tmp_dir, max_duration_seconds):
            video_path = os.path.join(tmp_dir, "source.mp4")
            with open(video_path, "wb") as f:
                f.write(b"fake video")
            return video_path, {"title": "demo video", "duration": 18, "extractor": "youtube"}

        globals_ = {
            "GDATA": {
                "pose_video_max_duration_seconds": 300,
                "pose_fps_target": 15,
                "project": "demo",
            },
            "tempfile": tempfile,
            "shutil": __import__("shutil"),
            "os": os,
            "root": FakeTkRoot(),
            "pose_model_file": "yolo11n-pose.pt",
            "pose_confidence": 0.35,
            "write_source_video_info": lambda record_folder, info: None,
            "ensure_pose_model": lambda: FakePoseModel(),
            "download_authorized_youtube_video": download_video,
            "iter_video_frames": iter_video_frames,
            "yolo_pose_result_to_people": lambda result, roi: [person],
            "select_main_person": lambda people, roi_center, previous_center: people[0],
            "bbox_center": lambda bbox: (5, 10),
            "build_pose_frame": lambda frame_index, time_ms, person, roi: {
                "frame_index": frame_index,
                "time_ms": time_ms,
            },
            "build_pose_record": lambda **kwargs: {"frames": kwargs["frames"]},
            "write_json_atomic": lambda path, record: None,
            "convert_pose_record_to_live2d_files": lambda output_path: {
                "live2d_params": "live2d_params.json",
                "motion3": "motion3.json",
            },
            "set_pose_status": statuses.append,
            "finish_youtube_pose_recording": lambda path, message=None, warning=None: finished.append(
                (path, message, warning)
            ),
            "urlparse": __import__("urllib.parse").parse.urlparse,
            "parse_qs": __import__("urllib.parse").parse.parse_qs,
            "logging": types.SimpleNamespace(exception=lambda *args, **kwargs: None),
        }
        namespace = load_functions(
            "normalize_youtube_pose_cache_url",
            "build_youtube_pose_cache_key",
            "schedule_pose_status",
            "report_youtube_pose_progress",
            "run_youtube_pose_worker",
            extra_globals=globals_,
        )

        with tempfile.TemporaryDirectory() as record_folder:
            namespace["run_youtube_pose_worker"]("https://youtu.be/demo", record_folder)

        self.assertIn("YouTube Pose 下載完成，開始分析影格...", statuses)
        self.assertIn("YouTube Pose 分析中：已處理 5 張影格，偵測到 5 張", statuses)
        self.assertEqual(len(finished), 1)

    def test_youtube_pose_worker_saves_source_video_with_pose_record(self):
        source_infos = []
        built_sources = []
        person = {
            "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 20, "confidence": 0.9},
            "keypoints": [],
            "mean_keypoint_confidence": 0.9,
        }

        def download_video(url, tmp_dir, max_duration_seconds):
            video_path = os.path.join(tmp_dir, "downloaded.mp4")
            with open(video_path, "wb") as f:
                f.write(b"fake video")
            return video_path, {"title": "demo video", "duration": 18, "extractor": "youtube"}

        def build_pose_record(**kwargs):
            built_sources.append(dict(kwargs["source"]))
            return {"source": kwargs["source"], "frames": kwargs["frames"]}

        globals_ = {
            "GDATA": {
                "pose_video_max_duration_seconds": 300,
                "pose_fps_target": 15,
                "project": "demo",
            },
            "tempfile": tempfile,
            "shutil": shutil,
            "os": os,
            "root": FakeTkRoot(),
            "pose_model_file": "yolo11n-pose.pt",
            "pose_confidence": 0.35,
            "write_source_video_info": lambda record_folder, info: source_infos.append(dict(info)),
            "ensure_pose_model": lambda: FakePoseModel(),
            "download_authorized_youtube_video": download_video,
            "iter_video_frames": lambda video_path, fps_target, max_duration_seconds: [(0, 0, FakeFrame())],
            "yolo_pose_result_to_people": lambda result, roi: [person],
            "select_main_person": lambda people, roi_center, previous_center: people[0],
            "bbox_center": lambda bbox: (5, 10),
            "build_pose_frame": lambda frame_index, time_ms, person, roi: {
                "frame_index": frame_index,
                "time_ms": time_ms,
            },
            "build_pose_record": build_pose_record,
            "write_json_atomic": lambda path, record: None,
            "convert_pose_record_to_live2d_files": lambda output_path: {
                "live2d_params": "live2d_params.json",
                "motion3": "motion3.json",
            },
            "set_pose_status": lambda message: None,
            "finish_youtube_pose_recording": lambda path, message=None, warning=None: None,
            "urlparse": __import__("urllib.parse").parse.urlparse,
            "parse_qs": __import__("urllib.parse").parse.parse_qs,
            "logging": types.SimpleNamespace(exception=lambda *args, **kwargs: None),
        }
        namespace = load_functions(
            "normalize_youtube_pose_cache_url",
            "build_youtube_pose_cache_key",
            "schedule_pose_status",
            "report_youtube_pose_progress",
            "run_youtube_pose_worker",
            extra_globals=globals_,
        )

        with tempfile.TemporaryDirectory() as record_folder:
            namespace["run_youtube_pose_worker"]("https://youtu.be/demo", record_folder)
            saved_video = os.path.join(record_folder, "source.mp4")
            self.assertTrue(os.path.isfile(saved_video))
            with open(saved_video, "rb") as f:
                self.assertEqual(f.read(), b"fake video")

        self.assertEqual(built_sources[-1]["source_video_file"], "source.mp4")
        self.assertTrue(source_infos[-1]["source_video_saved"])
        self.assertEqual(source_infos[-1]["source_video_file"], "source.mp4")
        self.assertEqual(source_infos[-1]["cache_key"]["url"], "youtube:demo")

    def test_start_youtube_pose_recording_reuses_cache_hit_without_worker(self):
        finished = []
        statuses = []
        created_folders = []
        thread_starts = []

        class FakeThread:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def start(self):
                thread_starts.append(True)

        with tempfile.TemporaryDirectory() as project_folder:
            cached_pose_record = os.path.join(project_folder, "pose_record", "record_1", "pose_record.json")
            os.makedirs(os.path.dirname(cached_pose_record))
            with open(cached_pose_record, "w", encoding="utf-8") as f:
                f.write("{}")

            globals_ = {
                "GDATA": {
                    "pose_recording": False,
                    "pose_url_processing": False,
                    "pose_fps_target": 15,
                    "pose_video_max_duration_seconds": 300,
                    "THREAD": {},
                },
                "pose_model_file": "yolo11n-pose.pt",
                "pose_confidence": 0.35,
                "is_run_keep_screen_predict": False,
                "get_current_project_folder": lambda: project_folder,
                "simpledialog": types.SimpleNamespace(askstring=lambda title, prompt: "https://youtu.be/demo"),
                "is_probable_youtube_url": lambda url: True,
                "messagebox": types.SimpleNamespace(
                    askokcancel=lambda title, message: True,
                    showwarning=lambda *args, **kwargs: None,
                    showerror=lambda *args, **kwargs: None,
                ),
                "find_youtube_pose_cache_record": lambda *args: cached_pose_record,
                "convert_pose_record_to_live2d_files": lambda path: {
                    "live2d_params": os.path.join(os.path.dirname(path), "live2d_params.json"),
                    "motion3": os.path.join(os.path.dirname(path), "motion3.json"),
                },
                "finish_youtube_pose_recording": lambda path, error_message=None, live2d_error=None: finished.append((path, error_message, live2d_error)),
                "set_pose_status": statuses.append,
                "create_pose_record_folder": lambda folder: created_folders.append(folder) or os.path.join(folder, "new_record"),
                "set_youtube_pose_processing_buttons": lambda is_processing: None,
                "threading": types.SimpleNamespace(Thread=FakeThread),
                "run_youtube_pose_worker": lambda url, record_folder: None,
            }
            namespace = load_functions("start_youtube_pose_recording", extra_globals=globals_)

            namespace["start_youtube_pose_recording"]()

        self.assertEqual(finished, [(cached_pose_record, None, None)])
        self.assertEqual(created_folders, [])
        self.assertEqual(thread_starts, [])
        self.assertIn("YouTube Pose 使用快取", statuses[-1])

    def test_youtube_pose_cache_key_normalizes_url_and_settings(self):
        namespace = load_functions(
            "normalize_youtube_pose_cache_url",
            "build_youtube_pose_cache_key",
            extra_globals={
                "os": os,
                "urlparse": __import__("urllib.parse").parse.urlparse,
                "parse_qs": __import__("urllib.parse").parse.parse_qs,
            },
        )

        key_a = namespace["build_youtube_pose_cache_key"](
            "https://www.youtube.com/watch?v=abc123&t=5s",
            "C:/models/yolo11n-pose.pt",
            0.35,
            15,
            300,
        )
        key_b = namespace["build_youtube_pose_cache_key"](
            "https://youtu.be/abc123",
            "D:/other/yolo11n-pose.pt",
            "0.350",
            "15",
            "300",
        )

        self.assertEqual(key_a, key_b)
        self.assertEqual(key_a["url"], "youtube:abc123")
        self.assertEqual(key_a["pose_model"], "yolo11n-pose.pt")
        self.assertEqual(key_a["pose_confidence"], 0.35)

    def test_find_youtube_pose_cache_record_returns_complete_match(self):
        namespace = load_functions(
            "normalize_youtube_pose_cache_url",
            "build_youtube_pose_cache_key",
            "youtube_pose_cache_key_matches",
            "find_youtube_pose_cache_record",
            extra_globals={
                "glob": glob,
                "json": __import__("json"),
                "os": os,
                "urlparse": __import__("urllib.parse").parse.urlparse,
                "parse_qs": __import__("urllib.parse").parse.parse_qs,
            },
        )

        with tempfile.TemporaryDirectory() as project_folder:
            incomplete = os.path.join(project_folder, "pose_record", "record_1")
            complete = os.path.join(project_folder, "pose_record", "record_2")
            os.makedirs(incomplete)
            os.makedirs(complete)
            key = namespace["build_youtube_pose_cache_key"](
                "https://youtu.be/abc123",
                "yolo11n-pose.pt",
                0.35,
                15,
                300,
            )
            with open(os.path.join(incomplete, "source_video_info.json"), "w", encoding="utf-8") as f:
                __import__("json").dump({"status": "complete", "cache_key": key}, f)
            with open(os.path.join(incomplete, "pose_record.json"), "w", encoding="utf-8") as f:
                __import__("json").dump({"source": {"source_video_file": "source.mp4"}}, f)
            with open(os.path.join(complete, "source_video_info.json"), "w", encoding="utf-8") as f:
                __import__("json").dump({"status": "complete", "cache_key": key}, f)
            with open(os.path.join(complete, "pose_record.json"), "w", encoding="utf-8") as f:
                __import__("json").dump({"source": {"source_video_file": "source.mp4"}}, f)
            with open(os.path.join(complete, "source.mp4"), "wb") as f:
                f.write(b"video")

            found = namespace["find_youtube_pose_cache_record"](
                project_folder,
                "https://www.youtube.com/watch?v=abc123",
                "C:/models/yolo11n-pose.pt",
                0.35,
                15,
                300,
            )

        self.assertEqual(found, os.path.join(complete, "pose_record.json"))


if __name__ == "__main__":
    unittest.main()
