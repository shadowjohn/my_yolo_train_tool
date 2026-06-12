def clamp(value, min_value, max_value):
    if value is None:
        return 0.0
    return max(min_value, min(max_value, float(value)))


DEFAULT_MAPPING = [
    # Head rotations (X, Y, Z)
    {"id": "PARAM_ANGLE_X", "source": "head_angle_x_deg", "scale": 1.0, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "PARAM_ANGLE_Y", "source": "head_angle_y_deg", "scale": 1.0, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "PARAM_ANGLE_Z", "source": "head_angle_z_deg", "scale": 1.0, "offset": 0.0, "clamp": [-30, 30]},
    
    # Body rotations (X, Y, Z)
    {"id": "PARAM_BODY_ANGLE_X", "source": "torso_angle_deg", "scale": 0.25, "offset": 22.5, "clamp": [-15, 15]},
    {"id": "PARAM_BODY_ANGLE_Y", "source": "body_center_y", "scale": -12.0, "offset": 6.0, "clamp": [-8, 8]},
    {"id": "PARAM_BODY_ANGLE_Z", "source": "torso_angle_deg", "scale": 0.5, "offset": 45.0, "clamp": [-30, 30]},
    
    # Body Base positions
    {"id": "PARAM_BASE_X", "source": "body_center_x", "scale": 80.0, "offset": -40.0, "clamp": [-50, 50]},
    {"id": "PARAM_BASE_Y", "source": "body_center_y", "scale": -50.0, "offset": 30.0, "clamp": [-20, 40]},
    {"id": "PARAM_BODY_CENTER", "source": "body_center_x", "scale": 20.0, "offset": -10.0, "clamp": [-10, 10]},
    
    # Arms and Elbows
    {"id": "PARAM_ARM_L", "source": "left_arm_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "PARAM_ARM_R", "source": "right_arm_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    {"id": "PARAM_ARM_L_ELBOW", "source": "left_elbow_angle_deg", "scale": -0.055, "offset": 10.0, "clamp": [0, 10]},
    {"id": "PARAM_ARM_R_ELBOW", "source": "right_elbow_angle_deg", "scale": -0.055, "offset": 10.0, "clamp": [0, 10]},
    {"id": "PARAM_ARM_L_WRIST", "source": "left_arm_angle_deg", "scale": 0.3, "offset": 0.0, "clamp": [-15, 15]},
    {"id": "PARAM_ARM_R_WRIST", "source": "right_arm_angle_deg", "scale": 0.3, "offset": 0.0, "clamp": [-15, 15]},
    
    # Shoulders
    {"id": "PARAM_SHOULDER_L", "source": "left_shoulder_raise", "scale": 50.0, "offset": 0.0, "clamp": [-10, 10]},
    {"id": "PARAM_SHOULDER_R", "source": "right_shoulder_raise", "scale": 50.0, "offset": 0.0, "clamp": [-10, 10]},
    
    # Legs
    {"id": "PARAM_LEG_L", "source": "left_leg_angle_deg", "scale": 0.4, "offset": 0.0, "clamp": [-45, 45]},
    {"id": "PARAM_LEG_R", "source": "right_leg_angle_deg", "scale": 0.4, "offset": 0.0, "clamp": [-45, 45]},
    
    # Waist / Hip
    {"id": "PARAM_WAIST_ANGLE_Z", "source": "hip_angle_deg", "scale": 0.5, "offset": 0.0, "clamp": [-30, 30]},
    
    # Other / Breath & Face expressions
    {"id": "PARAM_BREATH", "source": "body_center_y", "scale": -0.8, "offset": 0.8, "clamp": [0, 1]},
    {"id": "PARAM_EYE_SMILE", "source": None, "scale": 0.0, "offset": 0.7, "clamp": [0, 1]},
]


def apply_ema_smoothing(parameters, alpha=0.35):
    for param in parameters:
        keys = param.get("keys", [])
        if not keys:
            continue
        smoothed_value = keys[0]["value"]
        for key in keys:
            smoothed_value = alpha * key["value"] + (1.0 - alpha) * smoothed_value
            key["value"] = smoothed_value
    return parameters


def build_live2d_params(pose_record, mapping=None, source_pose_record="pose_record.json", ema_alpha=None):
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
            raw_value = features.get(spec["source"]) if spec["source"] else None
            value = clamp((0.0 if raw_value is None else raw_value) * spec["scale"] + spec["offset"], lo, hi)
            keys.append({"time_ms": int(frame["time_ms"]), "value": value})
        parameters.append(dict(spec, keys=keys))

    if ema_alpha is not None and ema_alpha > 0.0:
        parameters = apply_ema_smoothing(parameters, ema_alpha)

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
