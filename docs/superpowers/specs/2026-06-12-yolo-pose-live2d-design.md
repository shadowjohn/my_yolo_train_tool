# YOLO Pose Recorder to Live2D Motion Design

## Purpose

Add a two-stage motion workflow to `my_yolo_train_tool`:

1. **A: Pose Recorder** records a selected screen region, detects the main dancer with YOLO pose, and writes a clean skeleton time-series JSON.
2. **B: Live2D Motion Mapper** reads that JSON and converts body rhythm into Live2D-friendly parameter curves, with `.motion3.json` export as the practical target.

The first implementation should prioritize repeatable capture, inspectable data, and fast validation over perfect character retargeting.

## Current Project Fit

The existing tool already has the core primitives needed for Stage A:

- tkinter desktop controls and global state in `my_yolo_train_tool.py`.
- ROI selection and screenshot capture through `mss`.
- Ultralytics YOLO inference loop in `run_keep_screen_predict()`.
- transparent overlay rendering through `OverlayWindow`.
- project-scoped storage under `data/projects/{project_name}/`.
- FastAPI and static Web UI for later review/preview screens.

Stage A should reuse these patterns and avoid replacing the existing detection or training flows.

## External References

- Ultralytics pose models expose detected person instances with `result.keypoints.xy`, `result.keypoints.xyn`, and `result.keypoints.data`.
- The default human pose layout has 17 COCO keypoints: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, and ankles.
- Live2D Cubism can import/export `.motion3.json`; frame rate alignment matters when importing motion data.
- Live2D SDK has consistency checks for `.motion3.json`, so exported files should stay simple and conservative at first.

## Stage A: Pose Recorder

### User Flow

1. User selects or reuses the current screen ROI.
2. User clicks a new pose-recording button such as `骨架錄製(開始)`.
3. The tool captures frames from the ROI with monotonic timestamps.
4. YOLO pose runs on each sampled frame.
5. The main dancer is selected from detected people.
6. Keypoints are normalized, smoothed, and stored.
7. User clicks stop.
8. The tool writes `pose_record.json` and an optional skeleton preview.

### Main Dancer Selection

For the first version, choose the main dancer by this priority:

1. highest average pose confidence;
2. largest person bounding box area;
3. closest center to previous selected dancer center;
4. closest center to ROI center when there is no previous frame.

This handles the reference hallway video where a second person appears in the background.

### Pose JSON Contract

Write Stage A output to:

```text
data/projects/{project_name}/pose_record/{record_id}/pose_record.json
```

Recommended schema:

```json
{
  "version": 1,
  "created_at": "2026-06-12T00:00:00+08:00",
  "project_name": "project",
  "source": {
    "type": "screen_roi",
    "roi": { "left": 0, "top": 0, "width": 720, "height": 1280 },
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

## Error Handling

- If no ROI is selected, prompt the user to select a region first.
- If no project is selected, write under a default project or block with a clear message consistent with existing UI behavior.
- If the pose model cannot be loaded, show a clear error and do not start recording.
- If no person is detected for several consecutive frames, keep recording but mark those frames with quality flags.
- If capture fails repeatedly, stop recording and write any usable partial data.

## Performance Constraints

- Default target should be 15-30 FPS for pose recording, not 60 FPS.
- Store pose data incrementally in memory and flush on stop for the first version.
- Avoid retaining full raw frames in memory unless preview video generation needs them.
- Use a small pose model first (`n` size) for interactive testing.

## Testing And Validation

Minimum validation:

1. Unit-test geometry helpers for angles, normalization, interpolation, and smoothing.
2. Unit-test main dancer selection with two-person synthetic detections.
3. Unit-test JSON writer shape and required fields.
4. Unit-test Live2D parameter mapper with a small synthetic `pose_record.json`.
5. Smoke-test recording a short ROI clip and confirm `pose_record.json` has increasing `time_ms`.
6. Smoke-test mapper output and confirm parameter values stay within configured clamps.

## Out Of Scope For First Implementation

- Full 3D pose reconstruction.
- Automatic Live2D model introspection.
- Perfect hand/finger motion.
- Physics baking.
- Audio-driven lip-sync.
- Training a custom pose model.
- Downloading or archiving third-party video content.

## Open Implementation Choices

- Whether Stage A preview should be MP4 or HTML first.
- Whether the pose model file should be bundled or selected manually.
- Whether Stage B should expose mapping controls in Web UI immediately or start as a button/CLI-style backend action.

Recommended defaults:

- HTML skeleton preview first, because it is lightweight and uses the JSON directly.
- Manual pose model path with a default `example_pt/yolo26n-pose.pt` or `example_pt/yolo11n-pose.pt`.
- Start B as a backend converter triggered from the desktop tool or API; add a fuller mapping UI later.
