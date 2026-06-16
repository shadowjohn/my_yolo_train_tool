import math

def euler_to_quaternion(pitch, yaw, roll):
    # pitch (X), yaw (Y), roll (Z) in radians
    p = pitch / 2.0
    y = yaw / 2.0
    r = roll / 2.0
    
    sinp = math.sin(p)
    cosp = math.cos(p)
    siny = math.sin(y)
    cosy = math.cos(y)
    sinr = math.sin(r)
    cosr = math.cos(r)
    
    qx = sinp * cosy * cosr - cosp * siny * sinr
    qy = cosp * siny * cosr + sinp * cosy * sinr
    qz = cosp * cosy * sinr - sinp * siny * cosr
    qw = cosp * cosy * cosr + sinp * siny * sinr
    
    return [qx, qy, qz, qw]

def build_vrm_bones_animation(pose_record):
    """
    將 pose_record 中的 frames 特徵轉換為 VRM 骨骼旋轉
    輸出格式：
    {
      "duration_ms": 1234,
      "fps": 30,
      "bones": {
        "leftUpperArm": [{"time_ms": 0, "rot": [qx, qy, qz, qw]}, ...],
        ...
      },
      "hips_position": [{"time_ms": 0, "pos": [x, y, z]}, ...]
    }
    """
    frames = pose_record.get("frames", [])
    duration_ms = frames[-1]["time_ms"] if frames else 0
    fps = int(pose_record.get("source", {}).get("fps_target", 30) or 30)
    
    bones_animation = {
        "leftUpperArm": [],
        "rightUpperArm": [],
        "leftLowerArm": [],
        "rightLowerArm": [],
        "spine": [],
        "head": [],
        "leftUpperLeg": [],
        "rightUpperLeg": []
    }
    hips_position = []
    
    for frame in frames:
        time_ms = int(frame["time_ms"])
        features = frame.get("features", {})
        
        # 1. Head
        hx = features.get("head_angle_x_deg")
        hy = features.get("head_angle_y_deg")
        hz = features.get("head_angle_z_deg")
        # VRM Head rotation:
        # pitch -> X (hy), yaw -> Y (hx), roll -> Z (hz)
        pitch = math.radians(0.0 if hy is None else hy)
        yaw = math.radians(0.0 if hx is None else hx)
        roll = math.radians(0.0 if hz is None else hz)
        bones_animation["head"].append({
            "time_ms": time_ms,
            "rot": euler_to_quaternion(pitch, yaw, roll)
        })
        
        # 2. Spine (Torso Z roll/tilt)
        torso = features.get("torso_angle_deg")
        t_angle = math.radians(0.0 if torso is None else (torso + 90.0))
        # 身體左右傾斜繞 Z 軸
        bones_animation["spine"].append({
            "time_ms": time_ms,
            "rot": euler_to_quaternion(0.0, 0.0, t_angle)
        })
        
        # 3. Arms
        l_arm = features.get("left_arm_angle_deg")
        r_arm = features.get("right_arm_angle_deg")
        
        # Left Upper Arm rotation
        l_rot = math.radians(0.0 if l_arm is None else l_arm)
        # Right Upper Arm rotation
        r_rot = math.radians(0.0 if r_arm is None else (r_arm - 180.0))
        
        bones_animation["leftUpperArm"].append({
            "time_ms": time_ms,
            "rot": euler_to_quaternion(0.0, 0.0, l_rot)
        })
        bones_animation["rightUpperArm"].append({
            "time_ms": time_ms,
            "rot": euler_to_quaternion(0.0, 0.0, r_rot)
        })
        
        # 4. Elbows (Lower Arm)
        l_elbow = features.get("left_elbow_angle_deg")
        r_elbow = features.get("right_elbow_angle_deg")
        
        le_rot = math.radians(0.0 if l_elbow is None else (180.0 - l_elbow))
        re_rot = math.radians(0.0 if r_elbow is None else (180.0 - r_elbow))
        
        bones_animation["leftLowerArm"].append({
            "time_ms": time_ms,
            "rot": euler_to_quaternion(0.0, 0.0, -le_rot)
        })
        bones_animation["rightLowerArm"].append({
            "time_ms": time_ms,
            "rot": euler_to_quaternion(0.0, 0.0, re_rot)
        })
        
        # 5. Legs
        l_leg = features.get("left_leg_angle_deg")
        r_leg = features.get("right_leg_angle_deg")
        ll_rot = math.radians(0.0 if l_leg is None else (l_leg - 90.0))
        rl_rot = math.radians(0.0 if r_leg is None else (r_leg - 90.0))
        
        bones_animation["leftUpperLeg"].append({
            "time_ms": time_ms,
            "rot": euler_to_quaternion(0.0, 0.0, ll_rot)
        })
        bones_animation["rightUpperLeg"].append({
            "time_ms": time_ms,
            "rot": euler_to_quaternion(0.0, 0.0, rl_rot)
        })
        
        # 6. Hips position
        cx = features.get("body_center_x")
        cy = features.get("body_center_y")
        px = 0.0 if cx is None else (cx - 0.5) * 2.0
        py = 0.0 if cy is None else (0.5 - cy) * 2.0
        hips_position.append({
            "time_ms": time_ms,
            "pos": [px, py, 0.0]
        })
        
    return {
        "version": 1,
        "duration_ms": duration_ms,
        "fps": fps,
        "bones": bones_animation,
        "hips_position": hips_position
    }
