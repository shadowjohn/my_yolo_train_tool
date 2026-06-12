def clamp(value, min_value, max_value):
    if value is None:
        return 0.0
    return max(min_value, min(max_value, float(value)))


DEFAULT_MAPPING = [
    {"id": "PARAM_ANGLE_Z", "source": "torso_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "PARAM_BODY_ANGLE_X", "source": "torso_angle_deg", "scale": 0.25, "offset": 0.0, "clamp": [-15, 15]},
    {"id": "PARAM_BODY_ANGLE_Y", "source": "body_center_y", "scale": -12.0, "offset": 6.0, "clamp": [-8, 8]},
    {"id": "PARAM_BASE_X", "source": "body_center_x", "scale": 80.0, "offset": -40.0, "clamp": [-50, 50]},
    {"id": "PARAM_BASE_Y", "source": "body_center_y", "scale": -50.0, "offset": 30.0, "clamp": [-20, 40]},
    {"id": "PARAM_ARM_L", "source": "left_arm_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "PARAM_ARM_R", "source": "right_arm_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "PARAM_BREATH", "source": "body_center_y", "scale": -0.8, "offset": 0.8, "clamp": [0, 1]},
]


def build_live2d_params(pose_record, mapping=None, source_pose_record="pose_record.json"):
    mapping = mapping or DEFAULT_MAPPING
    fps = int(pose_record.get("source", {}).get("fps_target", 30) or 30)
    frames = pose_record.get("frames", [])
    duration_ms = frames[-1]["time_ms"] if frames else 0
    source_name = pose_record.get("source_pose_record", source_pose_record)
    parameters = []
    for spec in mapping:
        lo, hi = spec["clamp"]
        keys = []
        for frame in frames:
            features = frame.get("features", {})
            raw_value = features.get(spec["source"])
            value = clamp((0.0 if raw_value is None else raw_value) * spec["scale"] + spec["offset"], lo, hi)
            keys.append({"time_ms": int(frame["time_ms"]), "value": value})
        parameters.append(dict(spec, keys=keys))
    return {
        "version": 1,
        "source_pose_record": source_name,
        "fps": fps,
        "duration_ms": int(duration_ms),
        "parameters": parameters,
    }


def build_motion3(live2d_params):
    curves = []
    total_segments = 0
    total_points = 0
    for param in live2d_params.get("parameters", []):
        if len(param.get("keys", [])) < 2:
            continue
        segments = []
        first = True
        for key in param.get("keys", []):
            time_sec = round(float(key["time_ms"]) / 1000.0, 6)
            value = float(key["value"])
            if first:
                segments.extend([time_sec, value])
                first = False
            else:
                segments.extend([0, time_sec, value])
                total_segments += 1
            total_points += 1
        curves.append({"Target": "Parameter", "Id": param["id"], "Segments": segments})
    return {
        "Version": 3,
        "Meta": {
            "Duration": round(float(live2d_params.get("duration_ms", 0)) / 1000.0, 6),
            "Fps": int(live2d_params.get("fps", 30) or 30),
            "Loop": False,
            "AreBeziersRestricted": True,
            "CurveCount": len(curves),
            "TotalSegmentCount": total_segments,
            "TotalPointCount": total_points,
            "UserDataCount": 0,
            "TotalUserDataSize": 0,
        },
        "Curves": curves,
    }
