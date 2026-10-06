"""
MOVA Face Tracker: Face Presence, Head Position, and 3D Head Orientation (Yaw, Pitch, Roll)
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from vision.landmark_processor import LandmarkProcessor, ExponentialMovingAverage

class FaceData:
    def __init__(self):
        self.detected: bool = False
        self.confidence: float = 0.0
        self.face_center: Tuple[float, float] = (0.5, 0.3)
        self.head_yaw: float = 0.0    # Turn left (-) / right (+)
        self.head_pitch: float = 0.0  # Look down (-) / up (+)
        self.head_roll: float = 0.0   # Tilt left (-) / right (+)
        self.face_width: float = 0.2
        self.face_height: float = 0.25
        self.landmarks_count: int = 0
        self.blendshapes: Dict[str, float] = {}

class FaceTracker:
    # Key face landmark indices from 468-point mesh
    NOSE_TIP = 1
    CHIN = 152
    LEFT_EYE_OUTER = 33
    RIGHT_EYE_OUTER = 263
    FOREHEAD = 10

    def __init__(self):
        self.center_filter = ExponentialMovingAverage(alpha=0.6)
        self.yaw_filter = ExponentialMovingAverage(alpha=0.6)
        self.pitch_filter = ExponentialMovingAverage(alpha=0.6)

    def process_mediapipe_result(self, face_result) -> FaceData:
        data = FaceData()
        if not face_result or not face_result.face_landmarks:
            return data

        mesh = face_result.face_landmarks[0]
        if len(mesh) < 264:
            return data

        data.detected = True
        data.landmarks_count = len(mesh)
        data.confidence = 0.95

        # Face center from nose tip and eye midpoints
        nose = mesh[self.NOSE_TIP]
        left_eye = mesh[self.LEFT_EYE_OUTER]
        right_eye = mesh[self.RIGHT_EYE_OUTER]
        chin = mesh[self.CHIN]
        forehead = mesh[self.FOREHEAD]

        raw_cx = float(nose.x)
        raw_cy = float(nose.y)
        smoothed = self.center_filter.update(np.array([raw_cx, raw_cy]))
        data.face_center = (float(smoothed[0]), float(smoothed[1]))

        # Dimensions
        data.face_width = float(abs(right_eye.x - left_eye.x))
        data.face_height = float(abs(chin.y - forehead.y))

        # Roll: slope of eyes
        dx = right_eye.x - left_eye.x
        dy = right_eye.y - left_eye.y
        data.head_roll = float(np.degrees(np.arctan2(dy, dx)))

        # Yaw: distance of nose to left eye vs right eye
        d_left = abs(nose.x - left_eye.x)
        d_right = abs(nose.x - right_eye.x)
        total_eye_dist = d_left + d_right
        if total_eye_dist > 0.001:
            # normalized ratio: 0 is center, positive is turned right, negative is turned left
            yaw_ratio = (d_left - d_right) / total_eye_dist
            raw_yaw = float(yaw_ratio * 60.0)
            data.head_yaw = float(self.yaw_filter.update(np.array([raw_yaw]))[0])

        # Pitch: nose relative to forehead/chin
        total_height = abs(chin.y - forehead.y)
        if total_height > 0.001:
            ratio_y = (chin.y - nose.y) / total_height
            # Normal resting ratio is ~0.6
            raw_pitch = float((ratio_y - 0.6) * 70.0)
            data.head_pitch = float(self.pitch_filter.update(np.array([raw_pitch]))[0])

        # Blendshapes if available
        if hasattr(face_result, 'face_blendshapes') and face_result.face_blendshapes:
            for category in face_result.face_blendshapes[0]:
                data.blendshapes[category.category_name] = float(category.score)

        return data

    def create_simulated(self, t: float) -> FaceData:
        data = FaceData()
        data.detected = True
        data.confidence = 0.99
        cx = 0.5 + np.sin(t * 1.2) * 0.04
        cy = 0.3 + np.cos(t * 0.9) * 0.03
        data.face_center = (cx, cy)
        data.head_yaw = float(np.sin(t * 1.5) * 15.0)
        data.head_pitch = float(np.cos(t * 1.2) * 8.0)
        data.head_roll = float(np.sin(t * 0.8) * 5.0)
        data.face_width = 0.22
        data.face_height = 0.28
        return data
