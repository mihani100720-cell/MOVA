"""
MOVA Spatial Intent Engine: Fuses Gaze, Hand Pointing, and Head Orientation to resolve user focus
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional

class SpatialIntentEngine:
    def __init__(self):
        pass

    def estimate_intent_target(self,
                               gaze_target: Tuple[float, float],
                               hand_pos: Tuple[float, float],
                               hand_gesture: str,
                               head_yaw: float,
                               face_center: Tuple[float, float]) -> Dict[str, Any]:
        """
        Calculates the weighted focal point in the spatial environment.
        Weights shift depending on whether the hand is pointing/reaching vs gaze fixation.
        """
        # If hand is pointing or reaching forward, hand takes higher spatial intent weight
        if hand_gesture == "point":
            w_hand = 0.65
            w_gaze = 0.25
            w_head = 0.10
        elif hand_gesture in ("pinch", "open_palm"):
            w_hand = 0.50
            w_gaze = 0.40
            w_head = 0.10
        else:
            w_hand = 0.20
            w_gaze = 0.65
            w_head = 0.15

        # Head yaw offset
        head_x = np.clip(face_center[0] + (head_yaw / 60.0) * 0.3, 0.05, 0.95)
        head_y = face_center[1]

        intent_x = (hand_pos[0] * w_hand) + (gaze_target[0] * w_gaze) + (head_x * w_head)
        intent_y = (hand_pos[1] * w_hand) + (gaze_target[1] * w_gaze) + (head_y * w_head)

        # Confidence of intent: higher when gaze and hand are pointing to same spatial quadrant
        spatial_agreement = 1.0 - float(np.hypot(hand_pos[0] - gaze_target[0], hand_pos[1] - gaze_target[1]))
        intent_confidence = float(np.clip(spatial_agreement * 0.7 + 0.3, 0.3, 0.99))

        return {
            "intent_target": (round(float(intent_x), 3), round(float(intent_y), 3)),
            "intent_confidence": round(intent_confidence, 2),
            "primary_driver": "Hand" if w_hand >= 0.5 else "Gaze"
        }
