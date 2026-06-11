import json
import os
import tempfile

import cv2

from pose_motion_core import write_json_atomic


def is_probable_youtube_url(url):
    return isinstance(url, str) and ("youtube.com/" in url or "youtu.be/" in url)


def write_source_video_info(record_folder, info):
    return write_json_atomic(os.path.join(record_folder, "source_video_info.json"), info)


def download_authorized_youtube_video(url, output_dir, max_duration_seconds=300):
    try:
        import yt_dlp
    except ImportError as ex:
        raise RuntimeError("yt-dlp 未安裝，無法處理 YouTube URL。請安裝 requirements 或改用螢幕框選模式。") from ex
    opts = {
        "outtmpl": os.path.join(output_dir, "source.%(ext)s"),
        "format": "mp4[height<=720]/mp4/best[height<=720]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = int(info.get("duration") or 0)
        if duration and duration > max_duration_seconds:
            raise RuntimeError("影片長度超過上限 %s 秒，請先換短片或調整設定。" % max_duration_seconds)
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
    return filepath, info


def iter_video_frames(video_path, fps_target=15, max_duration_seconds=300):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("無法開啟影片: %s" % video_path)
    source_fps = cap.get(cv2.CAP_PROP_FPS) or fps_target
    frame_interval = max(1, int(round(float(source_fps) / float(fps_target))))
    frame_index = 0
    emitted_index = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        time_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
        if max_duration_seconds and time_ms > max_duration_seconds * 1000:
            break
        if frame_index % frame_interval == 0:
            yield emitted_index, time_ms, frame
            emitted_index += 1
        frame_index += 1
    cap.release()
