"""
MOVA Pose Tracker: Body, Shoulders, Arms, and Torso Tracking
Tracks full-body & upper-body landmarks, posture orientation, and joint angles.
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from vision.landmark_processor import LandmarkProcessor, ExponentialMovingAverage

class PoseData:
    def __init__(self):
        self.detected: bool = False
        self.confidence: float = 0.0
        self.landmarks: Dict[str, Tuple[float, float, float]] = {}
        self.body_center: Tuple[float, float] = (0.5, 0.5)
        self.torso_tilt: float = 0.0  # degrees lean
        self.left_elbow_angle: float = 0.0
        self.right_elbow_angle: float = 0.0
        self.left_shoulder_angle: float = 0.0
        self.right_shoulder_angle: float = 0.0
        self.upper_body_only: bool = True

class PoseTracker:
    # Standard MediaPipe Pose landmark indices
    LM_NOSE = 0
    LM_LEFT_SHOULDER = 11
    LM_RIGHT_SHOULDER = 12
    LM_LEFT_ELBOW = 13
    LM_RIGHT_ELBOW = 14
    LM_LEFT_WRIST = 15
    LM_RIGHT_WRIST = 16
    LM_LEFT_HIP = 23
    LM_RIGHT_HIP = 24

    def __init__(self):
        self.center_filter = ExponentialMovingAverage(alpha=0.6)

    def extract_from_mediapipe(self, pose_result) -> PoseData:
        data = PoseData()
        if not pose_result or not pose_result.pose_landmarks:
            return data

        landmarks = pose_result.pose_landmarks[0]
        if len(landmarks) < 17:
            return data

        data.detected = True

        def get_pt(idx: int) -> Tuple[float, float, float]:
            p = landmarks[idx]
            return (float(p.x), float(p.y), float(p.z) if hasattr(p, 'z') else 0.0)

        # Extract primary landmarks
        data.landmarks["nose"] = get_pt(self.LM_NOSE)
        data.landmarks["left_shoulder"] = get_pt(self.LM_LEFT_SHOULDER)
        data.landmarks["right_shoulder"] = get_pt(self.LM_RIGHT_SHOULDER)
        data.landmarks["left_elbow"] = get_pt(self.LM_LEFT_ELBOW)
        data.landmarks["right_elbow"] = get_pt(self.LM_RIGHT_ELBOW)
        data.landmarks["left_wrist"] = get_pt(self.LM_LEFT_WRIST)
        data.landmarks["right_wrist"] = get_pt(self.LM_RIGHT_WRIST)

        has_hips = len(landmarks) > self.LM_RIGHT_HIP
        if has_hips:
            data.landmarks["left_hip"] = get_pt(self.LM_LEFT_HIP)
            data.landmarks["right_hip"] = get_pt(self.LM_RIGHT_HIP)
            data.upper_body_only = False

        # Calculate body center (midpoint of shoulders, or shoulders + hips)
        ls = data.landmarks["left_shoulder"]
        rs = data.landmarks["right_shoulder"]
        if has_hips:
            lh = data.landmarks["left_hip"]
            rh = data.landmarks["right_hip"]
            raw_cx = (ls[0] + rs[0] + lh[0] + rh[0]) / 4.0
            raw_cy = (ls[1] + rs[1] + lh[1] + rh[1]) / 4.0
        else:
            raw_cx = (ls[0] + rs[0]) / 2.0
            raw_cy = (ls[1] + rs[1]) / 2.0

        smoothed_c = self.center_filter.update(np.array([raw_cx, raw_cy]))
        data.body_center = (float(smoothed_c[0]), float(smoothed_c[1]))

        # Calculate Torso lean angle (from shoulder slope)
        dx = rs[0] - ls[0]
        dy = rs[1] - ls[1]
        data.torso_tilt = float(np.degrees(np.arctan2(dy, dx)))

        # Joint angles
        data.left_elbow_angle = LandmarkProcessor.calculate_angle_3p(
            ls[:2], data.landmarks["left_elbow"][:2], data.landmarks["left_wrist"][:2]
        )
        data.right_elbow_angle = LandmarkProcessor.calculate_angle_3p(
            rs[:2], data.landmarks["right_elbow"][:2], data.landmarks["right_wrist"][:2]
        )

        if has_hips:
            data.left_shoulder_angle = LandmarkProcessor.calculate_angle_3p(
                data.landmarks["left_hip"][:2], ls[:2], data.landmarks["left_elbow"][:2]
            )
            data.right_shoulder_angle = LandmarkProcessor.calculate_angle_3p(
                data.landmarks["right_hip"][:2], rs[:2], data.landmarks["right_elbow"][:2]
            )

        data.confidence = 0.95
        return data

    def create_simulated(self, t: float) -> PoseData:
        """Generates realistic kinematics for Demo Mode."""
        data = PoseData()
        data.detected = True
        data.confidence = 0.99
        # gentle swaying motion
        lean = np.sin(t * 1.5) * 0.08
        cx = 0.5 + lean
        cy = 0.55

        data.body_center = (cx, cy)
        data.torso_tilt = float(lean * 40.0)

        # Shoulders
        ls = (cx - 0.15, cy - 0.15, 0.0)
        rs = (cx + 0.15, cy - 0.15, 0.0)
        data.landmarks["left_shoulder"] = ls
        data.landmarks["right_shoulder"] = rs

        # Left arm moving dynamically
        le = (ls[0] - 0.1, ls[1] + 0.12, 0.0)
        lw = (le[0] - 0.05 + np.sin(t * 2.0) * 0.08, le[1] - 0.1 + np.cos(t * 2.0) * 0.08, 0.0)
        data.landmarks["left_elbow"] = le
        data.landmarks["left_wrist"] = lw

        # Right arm
        re = (rs[0] + 0.1, rs[1] + 0.12, 0.0)
        rw = (re[0] + 0.05 + np.cos(t * 2.5) * 0.08, re[1] - 0.1 + np.sin(t * 2.5) * 0.08, 0.0)
        data.landmarks["right_elbow"] = re
        data.landmarks["right_wrist"] = rw

        data.left_elbow_angle = 120.0 + np.sin(t * 2.0) * 30.0
        data.right_elbow_angle = 110.0 + np.cos(t * 2.5) * 35.0
        return data
