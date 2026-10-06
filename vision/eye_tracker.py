"""
MOVA Eye Tracker: Approximate Webcam Gaze Estimation & Blink Detection
Strictly adheres to Section 3: webcam-based estimation clearly labeled as approximate.
Never claims clinical eye tracking accuracy.
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from vision.landmark_processor import LandmarkProcessor, ExponentialMovingAverage

class EyeTrackingData:
    def __init__(self):
        self.detected: bool = False
        self.is_approximate: bool = True  # Always explicitly marked approximate
        self.gaze_direction: str = "CENTER"  # "CENTER", "LEFT", "RIGHT", "UP", "DOWN"
        self.gaze_target_coords: Tuple[float, float] = (0.5, 0.5)  # Normalized (x, y) on screen
        self.eye_openness_left: float = 0.8
        self.eye_openness_right: float = 0.8
        self.is_blinking: bool = False
        self.blink_count: int = 0
        self.fixation_target: Optional[Tuple[float, float]] = None
        self.fixation_duration: float = 0.0
        self.confidence: float = 0.85

class EyeTracker:
    # Landmarks for eye opening and iris centers
    # Left eye top/bottom: 159, 145. Right eye top/bottom: 386, 374
    # Left iris: 468, 469, 470, 471 (if refined), fallback to eye corners: 33, 133 / 362, 263
    def __init__(self):
        self.gaze_filter = ExponentialMovingAverage(alpha=0.5)
        self.last_blink_state: bool = False
        self.blink_counter: int = 0
        self.fixation_pos: Optional[Tuple[float, float]] = None
        self.fixation_timer: float = 0.0

    def process_face_data(self, face_landmarks, blendshapes: Dict[str, float], dt: float = 0.033) -> EyeTrackingData:
        data = EyeTrackingData()
        if not face_landmarks or len(face_landmarks) < 400:
            return data

        data.detected = True

        # Check blendshapes for eye openness and gaze if available
        if blendshapes:
            left_blink = blendshapes.get("eyeBlinkLeft", 0.0)
            right_blink = blendshapes.get("eyeBlinkRight", 0.0)
            data.eye_openness_left = round(1.0 - left_blink, 2)
            data.eye_openness_right = round(1.0 - right_blink, 2)

            is_blinking = (left_blink > 0.6 and right_blink > 0.6)
            if is_blinking and not self.last_blink_state:
                self.blink_counter += 1
            self.last_blink_state = is_blinking
            data.is_blinking = is_blinking
            data.blink_count = self.blink_counter

            # Gaze blendshapes:
            look_in_l = blendshapes.get("eyeLookInLeft", 0.0)
            look_out_l = blendshapes.get("eyeLookOutLeft", 0.0)
            look_up_l = blendshapes.get("eyeLookUpLeft", 0.0)
            look_down_l = blendshapes.get("eyeLookDownLeft", 0.0)

            look_in_r = blendshapes.get("eyeLookInRight", 0.0)
            look_out_r = blendshapes.get("eyeLookOutRight", 0.0)
            look_up_r = blendshapes.get("eyeLookUpRight", 0.0)
            look_down_r = blendshapes.get("eyeLookDownRight", 0.0)

            # Horizontal gaze offset:
            # Looking left (user's right in mirrored screen): look_out_l, look_in_r
            h_gaze = (look_out_r + look_in_l) - (look_out_l + look_in_r)
            v_gaze = ((look_up_l + look_up_r) - (look_down_l + look_down_r))

            # Approximate gaze target on screen:
            screen_x = 0.5 + h_gaze * 0.8
            screen_y = 0.5 - v_gaze * 0.8
        else:
            # Geometric estimate from eye landmarks
            p_top_l = face_landmarks[159]
            p_bot_l = face_landmarks[145]
            p_left_l = face_landmarks[33]
            p_right_l = face_landmarks[133]

            vert_dist = abs(p_top_l.y - p_bot_l.y)
            horiz_dist = abs(p_right_l.x - p_left_l.x)

            ear = vert_dist / (horiz_dist + 1e-6)
            data.eye_openness_left = min(1.0, max(0.0, ear * 3.0))
            data.eye_openness_right = data.eye_openness_left
            data.is_blinking = ear < 0.12

            if data.is_blinking and not self.last_blink_state:
                self.blink_counter += 1
            self.last_blink_state = data.is_blinking
            data.blink_count = self.blink_counter

            # Head-pose assisted gaze
            nose = face_landmarks[1]
            screen_x = float(nose.x)
            screen_y = float(nose.y)

        # Smooth gaze coordinates
        smoothed = self.gaze_filter.update(np.array([screen_x, screen_y]))
        gx = float(np.clip(smoothed[0], 0.05, 0.95))
        gy = float(np.clip(smoothed[1], 0.05, 0.95))
        data.gaze_target_coords = (gx, gy)

        # Determine qualitative gaze direction
        if gx < 0.38:
            data.gaze_direction = "LEFT"
        elif gx > 0.62:
            data.gaze_direction = "RIGHT"
        elif gy < 0.35:
            data.gaze_direction = "UP"
        elif gy > 0.65:
            data.gaze_direction = "DOWN"
        else:
            data.gaze_direction = "CENTER"

        # Check visual fixation (staying within radius 0.08 for >= 0.3 sec)
        if self.fixation_pos is None:
            self.fixation_pos = (gx, gy)
            self.fixation_timer = 0.0
        else:
            dist = LandmarkProcessor.calculate_distance_2d(self.fixation_pos, (gx, gy))
            if dist < 0.08:
                self.fixation_timer += dt
                data.fixation_target = self.fixation_pos
                data.fixation_duration = round(self.fixation_timer, 2)
            else:
                self.fixation_pos = (gx, gy)
                self.fixation_timer = 0.0

        return data

    def create_simulated(self, t: float) -> EyeTrackingData:
        data = EyeTrackingData()
        data.detected = True
        # Gaze tracking moving targets
        gx = 0.5 + np.sin(t * 1.8) * 0.25
        gy = 0.5 + np.cos(t * 1.4) * 0.20
        data.gaze_target_coords = (round(float(gx), 3), round(float(gy), 3))
        if gx < 0.38:
            data.gaze_direction = "LEFT"
        elif gx > 0.62:
            data.gaze_direction = "RIGHT"
        elif gy < 0.35:
            data.gaze_direction = "UP"
        elif gy > 0.65:
            data.gaze_direction = "DOWN"
        else:
            data.gaze_direction = "CENTER"

        data.eye_openness_left = 0.92
        data.eye_openness_right = 0.92
        data.is_blinking = (int(t * 10) % 40 == 0)
        data.blink_count = int(t / 4.0)
        data.fixation_duration = 0.45
        data.fixation_target = (0.5, 0.5)
        return data
