"""
MOVA Angle Engine: Computes joint angles, ranges of motion (ROM), and angular velocity
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
from vision.landmark_processor import LandmarkProcessor

class AngleEngine:
    def __init__(self):
        self.prev_angles: Dict[str, float] = {}

    def compute_arm_angles(self, pose_landmarks: Dict[str, Tuple[float, float, float]]) -> Dict[str, float]:
        """
        Computes left/right elbow and shoulder angles.
        """
        res = {
            "left_elbow": 0.0,
            "right_elbow": 0.0,
            "left_shoulder": 0.0,
            "right_shoulder": 0.0
        }

        # Elbows
        if "left_shoulder" in pose_landmarks and "left_elbow" in pose_landmarks and "left_wrist" in pose_landmarks:
            res["left_elbow"] = LandmarkProcessor.calculate_angle_3p(
                pose_landmarks["left_shoulder"][:2],
                pose_landmarks["left_elbow"][:2],
                pose_landmarks["left_wrist"][:2]
            )

        if "right_shoulder" in pose_landmarks and "right_elbow" in pose_landmarks and "right_wrist" in pose_landmarks:
            res["right_elbow"] = LandmarkProcessor.calculate_angle_3p(
                pose_landmarks["right_shoulder"][:2],
                pose_landmarks["right_elbow"][:2],
                pose_landmarks["right_wrist"][:2]
            )

        # Shoulders
        if "left_hip" in pose_landmarks and "left_shoulder" in pose_landmarks and "left_elbow" in pose_landmarks:
            res["left_shoulder"] = LandmarkProcessor.calculate_angle_3p(
                pose_landmarks["left_hip"][:2],
                pose_landmarks["left_shoulder"][:2],
                pose_landmarks["left_elbow"][:2]
            )

        if "right_hip" in pose_landmarks and "right_shoulder" in pose_landmarks and "right_elbow" in pose_landmarks:
            res["right_shoulder"] = LandmarkProcessor.calculate_angle_3p(
                pose_landmarks["right_hip"][:2],
                pose_landmarks["right_shoulder"][:2],
                pose_landmarks["right_elbow"][:2]
            )

        return res

    def compute_angular_velocities(self, current_angles: Dict[str, float], dt: float) -> Dict[str, float]:
        velocities = {}
        if dt < 0.001:
            return {k: 0.0 for k in current_angles}

        for k, v in current_angles.items():
            prev = self.prev_angles.get(k, v)
            vel = (v - prev) / dt
            velocities[k] = round(vel, 2)
            self.prev_angles[k] = v
        return velocities
