def clamp(value, min_value, max_value):
    if value is None:
        return 0.0
    return max(min_value, min(max_value, float(value)))


DEFAULT_MAPPING = [
    {"id": "ParamBodyAngleX", "source": "torso_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "ParamBodyBounce", "source": "body_center_y", "scale": -60.0, "offset": 30.0, "clamp": [-30, 30]},
    {"id": "ParamArmL", "source": "left_arm_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "ParamArmR", "source": "right_arm_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
]


def build_live2d_params(pose_record, mapping=None):
    mapping = mapping or DEFAULT_MAPPING
    fps = int(pose_record.get("source", {}).get("fps_target", 30) or 30)
    frames = pose_record.get("frames", [])
    duration_ms = frames[-1]["time_ms"] if frames else 0
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
    return {"version": 1, "fps": fps, "duration_ms": int(duration_ms), "parameters": parameters}


def build_motion3(live2d_params):
    curves = []
    total_segments = 0
    total_points = 0
    for param in live2d_params.get("parameters", []):
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
