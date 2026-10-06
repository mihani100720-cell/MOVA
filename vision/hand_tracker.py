"""
MOVA Hand Tracker: Dual Hand Tracking, Gesture Recognition, and Kinematics
Detects: Wrist, Palm, Fingers, Fingertips, Hand Velocity, Gestures (open palm, fist, point, pinch, swipe)
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from vision.landmark_processor import LandmarkProcessor, ExponentialMovingAverage
from engine.gesture_ml import HandAnalyser

class SingleHandData:
    def __init__(self, label: str = "Right"):
        self.label: str = label  # "Left" or "Right"
        self.detected: bool = False
        self.confidence: float = 0.0
        self.wrist: Tuple[float, float, float] = (0.5, 0.5, 0.0)
        self.palm_center: Tuple[float, float] = (0.5, 0.5)
        self.index_tip: Tuple[float, float, float] = (0.5, 0.5, 0.0)
        self.thumb_tip: Tuple[float, float, float] = (0.5, 0.5, 0.0)
        self.middle_tip: Tuple[float, float, float] = (0.5, 0.5, 0.0)
        self.gesture: str = "None"  # "open_palm", "fist", "point", "pinch", "swipe_left", "swipe_right"
        self.pinch_distance: float = 1.0
        self.is_pinching: bool = False
        self.is_open_palm: bool = False
        self.is_fist: bool = False
        self.is_pointing: bool = False
        self.velocity: Tuple[float, float] = (0.0, 0.0)
        self.speed: float = 0.0
        self.raw_landmarks: List[Tuple[float, float, float]] = []

class HandTrackingResult:
    def __init__(self):
        self.left_hand = SingleHandData("Left")
        self.right_hand = SingleHandData("Right")
        self.hands_count: int = 0

class HandTracker:
    # Key indices
    WRIST = 0
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20

    def __init__(self):
        self.prev_positions = {"Left": None, "Right": None}
        self.smoothers = {
            "Left": ExponentialMovingAverage(alpha=0.7),
            "Right": ExponentialMovingAverage(alpha=0.7)
        }
        self.analysers = {
            "Left": HandAnalyser(),
            "Right": HandAnalyser()
        }

    def process_mediapipe_result(self, hand_result, dt: float = 0.033) -> HandTrackingResult:
        result = HandTrackingResult()
        if not hand_result or not hand_result.hand_landmarks:
            return result

        num_hands = len(hand_result.hand_landmarks)
        result.hands_count = num_hands

        for i in range(num_hands):
            landmarks = hand_result.hand_landmarks[i]
            label = "Right"
            if hasattr(hand_result, 'handedness') and len(hand_result.handedness) > i:
                handedness_list = hand_result.handedness[i]
                if handedness_list:
                    # In mirrored camera view, MediaPipe handedness flips
                    raw_cat = handedness_list[0].category_name
                    label = "Left" if raw_cat == "Right" else "Right"
            elif i == 1:
                label = "Left"

            target_hand = result.left_hand if label == "Left" else result.right_hand
            target_hand.detected = True

            # Extract coordinates
            pts = [(float(lm.x), float(lm.y), float(lm.z) if hasattr(lm, 'z') else 0.0) for lm in landmarks]
            target_hand.raw_landmarks = pts

            target_hand.wrist = pts[self.WRIST]
            target_hand.thumb_tip = pts[self.THUMB_TIP]
            target_hand.index_tip = pts[self.INDEX_TIP]
            target_hand.middle_tip = pts[self.MIDDLE_TIP]

            # Palm center: average of wrist, index_mcp, and pinky_mcp (17)
            pm = (
                (pts[self.WRIST][0] + pts[self.INDEX_MCP][0] + pts[17][0]) / 3.0,
                (pts[self.WRIST][1] + pts[self.INDEX_MCP][1] + pts[17][1]) / 3.0
            )
            smoothed_pm = self.smoothers[label].update(np.array(pm))
            target_hand.palm_center = (float(smoothed_pm[0]), float(smoothed_pm[1]))

            # Velocity calculation
            prev = self.prev_positions[label]
            if prev is not None and dt > 0.001:
                vx = (target_hand.palm_center[0] - prev[0]) / dt
                vy = (target_hand.palm_center[1] - prev[1]) / dt
                target_hand.velocity = (round(vx, 3), round(vy, 3))
                target_hand.speed = round(float(np.sqrt(vx**2 + vy**2)), 3)
            self.prev_positions[label] = target_hand.palm_center

            # ── ML + Geometric Gesture Detection ──────────────
            pts_arr = np.array([[p[0], p[1]] for p in pts], dtype=np.float32)
            analyser = self.analysers.get(label, self.analysers["Right"])
            g_name, conf, swipe = analyser.analyse(pts_arr, label)

            target_hand.confidence = conf
            pinch_dist = float(np.linalg.norm(pts_arr[self.THUMB_TIP] - pts_arr[self.INDEX_TIP]))
            target_hand.pinch_distance = round(pinch_dist, 3)

            is_pinch = (g_name == "PINCH") or (pinch_dist < 0.065)
            is_open  = (g_name == "OPEN_PALM")
            is_fist  = (g_name == "FIST")
            is_point = (g_name == "POINT")

            target_hand.is_pinching  = is_pinch
            target_hand.is_open_palm = is_open
            target_hand.is_fist      = is_fist
            target_hand.is_pointing  = is_point

            if swipe:
                target_hand.gesture = swipe.lower()
            elif is_pinch:
                target_hand.gesture = "pinch"
            elif is_point:
                target_hand.gesture = "point"
            elif is_open:
                target_hand.gesture = "open_palm"
            elif is_fist:
                target_hand.gesture = "fist"
            else:
                target_hand.gesture = g_name.lower()

        return result

    def create_simulated(self, t: float) -> HandTrackingResult:
        """Realistic simulated dual hand kinematics for Demo Mode."""
        res = HandTrackingResult()
        res.hands_count = 2

        # Right Hand: active circular / reaching movement
        rh = res.right_hand
        rh.detected = True
        rh.confidence = 0.99
        rx = 0.65 + np.sin(t * 2.2) * 0.18
        ry = 0.55 + np.cos(t * 1.8) * 0.15
        rh.palm_center = (rx, ry)
        rh.wrist = (rx + 0.02, ry + 0.1, 0.0)
        rh.index_tip = (rx - 0.02, ry - 0.08, 0.0)
        rh.thumb_tip = (rx - 0.05, ry - 0.03, 0.0)
        rh.pinch_distance = 0.07 + np.sin(t * 3.0) * 0.04
        rh.is_pinching = rh.pinch_distance < 0.05
        rh.gesture = "pinch" if rh.is_pinching else ("point" if int(t) % 3 == 0 else "open_palm")
        rh.velocity = (round(float(np.cos(t * 2.2) * 0.4), 2), round(float(-np.sin(t * 1.8) * 0.3), 2))
        rh.speed = float(np.sqrt(rh.velocity[0]**2 + rh.velocity[1]**2))

        # Left Hand: balancing / holding gesture
        lh = res.left_hand
        lh.detected = True
        lh.confidence = 0.98
        lx = 0.35 + np.cos(t * 1.5) * 0.14
        ly = 0.60 + np.sin(t * 1.4) * 0.12
        lh.palm_center = (lx, ly)
        lh.wrist = (lx - 0.02, ly + 0.1, 0.0)
        lh.index_tip = (lx + 0.01, ly - 0.07, 0.0)
        lh.thumb_tip = (lx + 0.04, ly - 0.03, 0.0)
        lh.gesture = "open_palm"
        lh.velocity = (round(float(-np.sin(t * 1.5) * 0.2), 2), round(float(np.cos(t * 1.4) * 0.2), 2))
        lh.speed = float(np.sqrt(lh.velocity[0]**2 + lh.velocity[1]**2))

        return res
