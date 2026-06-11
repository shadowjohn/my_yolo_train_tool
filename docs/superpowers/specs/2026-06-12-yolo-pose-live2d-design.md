# YOLO Pose Recorder to Live2D Motion Design

## Purpose

Add a motion workflow to `my_yolo_train_tool`:

1. **A1: YouTube URL Pose** accepts a YouTube URL, obtains an authorized local working copy, detects pose frames, and writes a clean skeleton time-series JSON.
2. **A2: Screen ROI Pose Recorder** records a selected screen region, draws a live skeleton canvas/overlay when a person appears, and writes a clean skeleton time-series JSON.
3. **B: Live2D Motion Mapper** reads the Stage A JSON and converts body rhythm into Live2D-friendly parameter curves, with `.motion3.json` export as the practical target.
4. **C: Live2D Desktop Dancer** opens a desktop Live2D character, lets the user choose a recorded dance JSON/motion file, and experimentally applies the motion.
5. **D: Face CopyCat** tracks a face from the same desktop ROI or a face-specific ROI, records facial expression time-series data, and maps expressions/head pose to Live2D face parameters.

The first implementation should prioritize repeatable capture, inspectable data, and fast validation over perfect character retargeting. The broader product direction is an action library: dance moves first, then reusable daily motions such as drinking coffee, elegant coffee sip, shrug smile, and stretching.

## Current Project Fit

The existing tool already has the core primitives needed for Stage A:

- tkinter desktop controls and global state in `my_yolo_train_tool.py`.
- ROI selection and screenshot capture through `mss`.
- Ultralytics YOLO inference loop in `run_keep_screen_predict()`.
- transparent overlay rendering through `OverlayWindow`.
- project-scoped storage under `data/projects/{project_name}/`.
- FastAPI and static Web UI for later review/preview screens.
- Python/OpenCV/mss frame handling that can feed MediaPipe Face Landmarker without moving capture work into the browser.

Stage A should reuse these patterns and avoid replacing the existing detection or training flows.

Implementation must keep a separate `pose_model_file` / `pose_model` and must not reuse or overwrite the current object-detection `model`.

## External References

- Ultralytics pose models expose detected person instances with `result.keypoints.xy`, `result.keypoints.xyn`, and `result.keypoints.data`.
- The default human pose layout has 17 COCO keypoints: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, and ankles.
- Live2D Cubism can import/export `.motion3.json`; frame rate alignment matters when importing motion data.
- Live2D SDK has consistency checks for `.motion3.json`, so exported files should stay simple and conservative at first.
- YouTube URL mode must be limited to user-owned, licensed, or otherwise authorized videos. The tool must not bypass DRM, paywalls, login-only content, or access controls. If a URL cannot be processed safely, the UI should tell the user to use screen ROI recording or a local authorized video file instead.
- MediaPipe Face Landmarker can return face landmarks, facial expression blendshapes, and a facial transformation matrix. It supports video/live-stream modes with timestamps, which fits screen ROI recording.
- The GitHub `face-tracking` topic has several candidates. OpenSeeFace is strong for VTuber-style CPU tracking and UDP integration, Jeeliz is strong for browser/WebGL face filters, and VTuber-Python-Unity is useful as a Live2D mapping reference. For this app, MediaPipe Face Landmarker should be the first backend because it stays inside the Python desktop capture pipeline and outputs blendshapes that map directly to Live2D.
- KennardWang/VTuber-MomoseHiyori is a useful Live2D VTuber reference. It tracks and sends a compact control set: head roll/pitch/yaw, left/right eye openness, eyeball X/Y, left/right eyebrow, mouth width, and mouth open. It also documents why calibration often needs linear, discrete, or piecewise mapping instead of directly applying raw face ratios.

## Stage A: Pose Extraction

### Shared Output Contract

Both A1 and A2 write the same JSON shape:

```text
data/projects/{project_name}/pose_record/{record_id}/pose_record.json
```

This makes B independent of the capture source.

### A1: YouTube URL Pose

#### User Flow

1. User clicks `YouTube URL Pose`.
2. Tool asks for a YouTube URL.
3. Tool validates the URL shape and shows a short notice that the user should only process authorized content.
4. Tool obtains a temporary local working video when permitted by the environment and site access.
5. Tool samples frames at a target FPS, runs YOLO pose, selects the main person, and writes `pose_record.json`.
6. Tool reports the generated JSON path.

#### File Layout

```text
data/projects/{project_name}/pose_record/record_{timestamp}/
  source_video_info.json
  pose_record.json
  preview.html
```

`source_video_info.json` should store URL, title if available, duration if available, tool status, and a note that the user is responsible for content rights. The first version should not retain the downloaded video after pose extraction unless the user explicitly enables a debug option.

#### Failure Handling

- If download/access fails, show a clear message and do not mark the recording as complete.
- If the video is too long, cap default processing to a configurable maximum duration.
- If no person is detected, still write a diagnostic `source_video_info.json` and show the failure reason.

### A2: Screen ROI Pose Recorder

#### User Flow

1. User selects or reuses the current screen ROI.
2. User clicks a new pose-recording button such as `骨架錄製(開始)`.
3. The tool captures frames from the ROI with monotonic timestamps.
4. YOLO pose runs on each sampled frame.
5. When a person is detected, the tool draws a live skeleton on a canvas/overlay.
6. The main dancer is selected from detected people.
7. Keypoints are normalized, smoothed, and stored with time coordinates.
8. User clicks stop.
9. The tool drains the queue, writes `pose_record.json`, and reports the generated file path.

#### Live Skeleton Canvas

The recorder should draw COCO17 keypoint lines over the ROI preview or a transparent overlay. The first version only needs one active skeleton for the selected main person. If multiple people are detected, draw the selected person strongly and either ignore or faintly draw others.

The live view is a verification surface, not the source of truth. `pose_record.json` remains the source of truth.

#### Recorder Robustness

The recorder should reuse proven patterns from `D:\mytools\my_cam_py`:

- bounded frame queue instead of unbounded `frame_list`;
- `time.monotonic()` for timestamps;
- `mss` preflight before starting;
- `with_cursor=False`;
- stop/finalize path with `recording` and `stop_in_progress`;
- repeated capture error guard, treating GDI `GetDIBits` / `BitBlt` failures as unsafe and stopping cleanly;
- worker threads must not update Tkinter directly, and should use `root.after`.

Pose recording and existing desktop object detection should be mutually exclusive unless separate overlays and model state are implemented.

### Main Dancer Selection

For the first version, choose the main dancer by this priority:

1. highest average pose confidence;
2. largest person bounding box area;
3. closest center to previous selected dancer center;
4. closest center to ROI center when there is no previous frame.

This handles the reference hallway video where a second person appears in the background.

### Pose JSON Contract

Recommended schema:

```json
{
  "version": 1,
  "created_at": "2026-06-12T00:00:00+08:00",
  "project_name": "project",
  "source": {
    "type": "screen_roi",
    "input_mode": "screen_roi",
    "roi": { "left": 0, "top": 0, "width": 720, "height": 1280 },
    "url": null,
    "fps_target": 30,
    "model": "yolo26n-pose.pt"
  },
  "keypoint_format": {
    "name": "coco17",
    "points": [
      "nose",
      "left_eye",
      "right_eye",
      "left_ear",
      "right_ear",
      "left_shoulder",
      "right_shoulder",
      "left_elbow",
      "right_elbow",
      "left_wrist",
      "right_wrist",
      "left_hip",
      "right_hip",
      "left_knee",
      "right_knee",
      "left_ankle",
      "right_ankle"
    ]
  },
  "frames": [
    {
      "frame_index": 0,
      "time_ms": 0,
      "bbox": { "x1": 0, "y1": 0, "x2": 100, "y2": 200, "confidence": 0.95 },
      "center": { "x": 50, "y": 100 },
      "scale": 1.0,
      "quality": {
        "mean_keypoint_confidence": 0.9,
        "visible_keypoints": 15,
        "is_interpolated": false
      },
      "keypoints": [
        { "name": "nose", "x": 50.0, "y": 20.0, "confidence": 0.9 },
        { "name": "left_eye", "x": 45.0, "y": 18.0, "confidence": 0.8 }
      ],
      "normalized_keypoints": [
        { "name": "nose", "x": 0.5, "y": 0.1, "confidence": 0.9 },
        { "name": "left_eye", "x": 0.45, "y": 0.09, "confidence": 0.8 }
      ],
      "features": {
        "shoulder_angle_deg": 0.0,
        "hip_angle_deg": 0.0,
        "torso_angle_deg": 0.0,
        "body_center_x": 0.5,
        "body_center_y": 0.5,
        "left_arm_angle_deg": 0.0,
        "right_arm_angle_deg": 0.0,
        "left_leg_angle_deg": 0.0,
        "right_leg_angle_deg": 0.0
      }
    }
  ]
}
```

The actual implementation may omit repeated `name` fields in each frame if a compact format is needed, but the first saved output should favor readability.

### Cleaning Rules

- Drop keypoints below a configurable confidence threshold.
- Interpolate short gaps when the same keypoint is missing for 1-3 frames.
- Keep longer gaps as missing, not guessed.
- Smooth normalized coordinates and derived angles with a small moving average or exponential moving average.
- Preserve raw confidence so later tuning can be audited.

### Preview

Stage A should provide at least one verification artifact:

- `preview.mp4` with skeleton lines drawn over the ROI frame, or
- `preview.html` that replays the skeleton from JSON without storing video.

The first version can implement one of these; both are not required.

## Stage B: Live2D Motion Mapper

### Input

Stage B reads only `pose_record.json`. It should not depend on the original video or screen capture frames.

### Output Files

Write mapper output to the same `pose_record/{record_id}/` folder:

```text
live2d_params.json
motion3.json
```

### Mapping Strategy

The first mapper should generate conservative parameter curves:

| Pose Feature | Live2D Target |
| --- | --- |
| head / neck inferred from nose and shoulders | `ParamAngleX`, `ParamAngleY`, `ParamAngleZ` |
| torso lean from shoulder/hip center | `ParamBodyAngleX`, `ParamBodyAngleY`, `ParamBodyAngleZ` |
| body center vertical rhythm | custom `ParamBodyBounce` |
| shoulder-to-wrist angles | custom `ParamArmL`, `ParamArmR` |
| hip-to-ankle rhythm | custom `ParamLegL`, `ParamLegR` |

The mapper should be configurable because real Live2D models often use custom parameter IDs.

### `live2d_params.json` Contract

```json
{
  "version": 1,
  "source_pose_record": "pose_record.json",
  "fps": 30,
  "duration_ms": 5000,
  "parameters": [
    {
      "id": "ParamBodyAngleX",
      "source": "torso_angle_deg",
      "scale": 0.5,
      "offset": 0.0,
      "clamp": [-30, 30],
      "keys": [
        { "time_ms": 0, "value": 0.0 },
        { "time_ms": 33, "value": 1.0 }
      ]
    }
  ]
}
```

### `.motion3.json` Export

The first export should use simple linear curves. Bezier tuning is out of scope for the first pass.

The export should include:

- metadata duration;
- FPS-aligned key timing;
- parameter curves for the configured Live2D parameter IDs;
- no audio, expression, or physics baking in the first version.

## Stage C: Live2D Desktop Dancer

### User Flow

1. User clicks a button such as `Live2D 人物`.
2. A desktop Live2D character appears.
3. The default character can be replaced later.
4. User clicks the character.
5. Character asks `要跳哪支舞？`.
6. User selects a Stage A `pose_record.json`, `live2d_params.json`, or `motion3.json`.
7. The character attempts to play the mapped motion.

### First Version Target

The first version does not need perfect full-body dance. It should prove that a recorded motion file can drive visible Live2D parameters:

- head/body angle;
- body bounce;
- left/right arm rhythm if the model has compatible custom parameters;
- mouth or message bubble when asking the user to choose a dance.
- optional face parameter overlay from Stage D when a face record or live copycat stream is enabled.

### Live2D Integration Style

Prefer a local explicit Live2D loader page and small public API:

```js
window.ScreenAiLive2D = {
  speak,
  stopSpeak,
  setExpression,
  startMotion,
  setParam,
  clearParams,
  getCurrentModel
};
```

Parameter overrides must be reapplied during the Live2D model update loop because stock motions can reset values every frame.

If no Live2D assets exist in this repository, first implementation may create the control page and loader contract, then require adding model/runtime assets before full playback verification.

## Stage D: Face CopyCat

### Recommended Backend

Use **MediaPipe Face Landmarker** as the first implementation backend.

Reasons:

- It is Python-friendly and can consume the same OpenCV/mss frames as A2.
- It returns 478 face landmarks, 52 blendshape scores, and a facial transform matrix, which is exactly the data shape needed for Live2D expression/head-pose mapping.
- It supports live-stream processing with timestamps, so the UI can keep recording while inference skips frames if the tracker is busy.
- It avoids moving the first implementation into a browser camera stack.

Keep **OpenSeeFace** as a later optional backend when the goal becomes a VTuber-style tracker process with UDP, CPU robustness, calibration, or VTube Studio-like behavior. Use **Jeeliz** only if a pure web/browser face filter path becomes important. Use **VTuber-Python-Unity** and **VTuber-MomoseHiyori** as references for eye blink, iris/eyeball, mouth, calibration, and Live2D mapping concepts, not as main dependencies.

### User Flow

1. User clicks `表情 CopyCat`.
2. Tool asks whether to use the current ROI or select a smaller face ROI.
3. Tool captures frames from that ROI.
4. MediaPipe Face Landmarker detects the primary face.
5. The app writes `face_record.json` with timestamps, blendshapes, landmarks, and head transform data.
6. The app maps face data to `live2d_face_params.json`.
7. Live2D desktop character can load the face file or later receive live values to mirror the user's expression.

### File Layout

```text
data/projects/{project_name}/face_record/record_{timestamp}/
  face_record.json
  live2d_face_params.json
  preview.html
```

Stage D should also allow a dance `pose_record` folder to reference a face record later, so body dance and facial expression can be combined without forcing both to be captured at the same time.

### Face JSON Contract

```json
{
  "version": 1,
  "created_at": "2026-06-12T00:00:00+08:00",
  "project_name": "project",
  "source": {
    "type": "screen_roi",
    "input_mode": "face_roi",
    "roi": { "left": 0, "top": 0, "width": 640, "height": 480 },
    "fps_target": 30,
    "backend": "mediapipe_face_landmarker",
    "model": "face_landmarker.task"
  },
  "frames": [
    {
      "frame_index": 0,
      "time_ms": 0,
      "face_detected": true,
      "quality": { "blendshape_count": 52, "landmark_count": 478 },
      "blendshapes": { "eyeBlinkLeft": 0.0, "eyeBlinkRight": 0.0, "jawOpen": 0.2 },
      "head_pose": { "yaw": 0.0, "pitch": 0.0, "roll": 0.0 },
      "facial_transformation_matrix": [1.0, 0.0, 0.0, 0.0],
      "landmarks": [
        { "x": 0.5, "y": 0.4, "z": -0.02 }
      ]
    }
  ]
}
```

The first implementation may store compact landmark arrays if JSON size becomes too large, but blendshapes and head pose must remain human-readable.

### Live2D Face Mapping

Write mapped values beside the face record:

```text
live2d_face_params.json
```

Recommended first mapping:

| Face Source | Live2D Target |
| --- | --- |
| `eyeBlinkLeft` | `ParamEyeLOpen` inverted |
| `eyeBlinkRight` | `ParamEyeROpen` inverted |
| `jawOpen` | `ParamMouthOpenY` |
| average `mouthSmileLeft` + `mouthSmileRight` | `ParamMouthForm` |
| brow up/down blendshapes | `ParamBrowLY`, `ParamBrowRY` |
| head yaw/pitch/roll | `ParamAngleX`, `ParamAngleY`, `ParamAngleZ` |
| eye look blendshapes when stable | `ParamEyeBallX`, `ParamEyeBallY` |

Because model parameter names vary, the mapper must use configurable parameter IDs. The defaults should match common Live2D/Cubism names but allow replacement later.

MomoseHiyori's 11-control-value protocol is a good sanity target for the first practical Face CopyCat result: if our JSON can reliably drive head, eyes, brows, and mouth with those same conceptual controls, the Live2D side is on the right path even if exact parameter IDs differ by model.

### Runtime Behavior

- Default face FPS should be 15-30 FPS.
- Use MediaPipe live-stream mode for live copycat and video mode for file processing.
- If MediaPipe or `face_landmarker.task` is missing, show a clear UI message and keep the rest of A/B/C usable.
- Face copycat and pose recording may run separately first. Running both at once is optional until the capture/inference budget is proven.
- Live2D parameter overrides must be applied every animation frame, like body motion overrides, because model motions can reset parameters.

## Motion Library Direction

Future action files should be organized as reusable motion assets:

```text
data/projects/{project_name}/pose_record/{record_id}/
  pose_record.json
  live2d_params.json
  motion3.json
  face_record.json
  live2d_face_params.json
  action_meta.json
```

`action_meta.json` can later categorize motions:

- dance;
- coffee;
- elegant coffee sip;
- shrug smile;
- stretch;
- idle;
- greeting;
- custom.

The first implementation only needs dance selection, but the storage should not block these later categories.

## Error Handling

- If no ROI is selected, prompt the user to select a region first.
- If no project is selected, write under a default project or block with a clear message consistent with existing UI behavior.
- If the pose model cannot be loaded, show a clear error and do not start recording.
- If no person is detected for several consecutive frames, keep recording but mark those frames with quality flags.
- If capture fails repeatedly, stop recording and write any usable partial data.
- If YouTube URL processing fails or is not allowed, provide the screen ROI mode as the fastest fallback.
- If Live2D assets are missing, keep B output valid and show that C requires model/runtime assets.
- If MediaPipe or the face landmarker model is missing, show that Face CopyCat is unavailable and point to dependency setup.

## Performance Constraints

- Default target should be 15-30 FPS for pose recording, not 60 FPS.
- YouTube URL mode should sample frames at the target FPS instead of processing every source frame by default.
- Store pose data incrementally in memory and flush on stop for the first version.
- Avoid retaining full raw frames in memory unless preview video generation needs them.
- Use a small pose model first (`n` size) for interactive testing.
- Store face landmarks/blendshapes instead of face images by default to reduce privacy and disk impact.

## Testing And Validation

Minimum validation:

1. Unit-test geometry helpers for angles, normalization, interpolation, and smoothing.
2. Unit-test main dancer selection with two-person synthetic detections.
3. Unit-test JSON writer shape and required fields.
4. Unit-test Live2D parameter mapper with a small synthetic `pose_record.json`.
5. Smoke-test YouTube URL mode with an authorized short test video or local equivalent and confirm output path is reported.
6. Smoke-test recording a short ROI clip and confirm live skeleton appears and `pose_record.json` has increasing `time_ms`.
7. Smoke-test mapper output and confirm parameter values stay within configured clamps.
8. Smoke-test Live2D desktop page loads or reports missing assets clearly.
9. Unit-test face blendshape-to-Live2D mapping with synthetic blendshape values.
10. Smoke-test face ROI capture and confirm `face_record.json` has increasing `time_ms` and readable blendshape keys.

## Out Of Scope For First Implementation

- Full 3D pose reconstruction.
- Automatic Live2D model introspection.
- Perfect hand/finger motion.
- Physics baking.
- Audio-driven lip-sync.
- Training a custom pose model.
- Full emotion classification beyond blendshape-driven expression copycat.
- Multi-face expression mixing.
- Downloading or archiving unauthorized third-party video content.
- Bypassing YouTube DRM, login, paywall, or access controls.
- Full production-quality Live2D retargeting.

## Open Implementation Choices

- Whether Stage A preview should be MP4 or HTML first.
- Whether the pose model file should be bundled or selected manually.
- Whether Stage B should expose mapping controls in Web UI immediately or start as a button/CLI-style backend action.
- Whether Stage C should use a browser-served Live2D page first or a native desktop overlay wrapper.
- Whether Face CopyCat should default to current ROI or ask for a separate smaller face ROI.

Recommended defaults:

- HTML skeleton preview first, because it is lightweight and uses the JSON directly.
- Manual pose model path with a default `example_pt/yolo26n-pose.pt` or `example_pt/yolo11n-pose.pt`.
- Start B as a backend converter triggered from the desktop tool or API; add a fuller mapping UI later.
- Stage C starts as a locally served Live2D control page opened from the desktop app; native overlay polish can follow after motion playback is proven.
- Face CopyCat starts with a separate face ROI option, because face tracking needs less screen area and lower inference cost than full-body pose.
