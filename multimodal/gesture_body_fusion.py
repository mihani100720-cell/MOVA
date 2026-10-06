"""
MOVA Gesture-Body & Voice-Gesture Fusion
Measures postural compensation during reaches and multimodal voice-gesture synchronization.
"""

import time
import numpy as np
from typing import Dict, Any, Optional, Tuple

class GestureBodyFusion:
    @staticmethod
    def evaluate_reach_posture(hand_reach_x: float, body_tilt_deg: float, stability_score: float) -> Dict[str, Any]:
        """
        Evaluates how the torso compensates during deep arm reaches.
        """
        # When reaching laterally (|reach_x - 0.5| > 0.25), some torso tilt is natural
        reach_offset = abs(hand_reach_x - 0.5)
        # Expected natural lean: ~15 deg per 0.2 reach offset
        expected_lean = reach_offset * 60.0
        actual_lean = abs(body_tilt_deg)
        lean_difference = abs(actual_lean - expected_lean)

        # Smooth posture compensation score [0..1.0]
        posture_balance = max(0.2, 1.0 - (lean_difference / 45.0))
        combined_score = round(posture_balance * 0.4 + (stability_score / 100.0) * 0.6, 2)

        return {
            "reach_offset": round(reach_offset, 3),
            "torso_tilt": round(body_tilt_deg, 1),
            "posture_balance_score": posture_balance,
            "hand_body_integration_score": combined_score
        }

class VoiceGestureFusion:
    def __init__(self):
        self.pending_command: Optional[str] = None
        self.command_time: Optional[float] = None
        self.expected_gesture: Optional[str] = None

    def trigger_voice_cue(self, command: str, expected_gesture: str, timestamp: float):
        self.pending_command = command
        self.command_time = timestamp
        self.expected_gesture = expected_gesture

    def check_response(self, actual_gesture: str, timestamp: float) -> Dict[str, Any]:
        if not self.pending_command or not self.command_time:
            return {"active": False}

        elapsed = timestamp - self.command_time
        if elapsed > 4.0:  # Timeout after 4 seconds
            res = {
                "active": True,
                "completed": False,
                "timeout": True,
                "latency": 4.0,
                "gesture_correct": False
            }
            self.pending_command = None
            return res

        if actual_gesture == self.expected_gesture:
            latency = elapsed
            res = {
                "active": True,
                "completed": True,
                "timeout": False,
                "latency": round(latency, 3),
                "gesture_correct": True,
                "command": self.pending_command
            }
            self.pending_command = None
            return res

        return {"active": True, "completed": False, "timeout": False}
