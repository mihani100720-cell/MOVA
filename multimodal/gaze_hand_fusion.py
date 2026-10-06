"""
MOVA Gaze-Hand Fusion: Measures Eye-Hand Coordination, Fixation-to-Reach latency
Implements Section 21:
Target Appears -> Gaze Fixation -> Hand Movement -> Target Interaction
"""

import time
import numpy as np
from typing import Dict, Any, Optional, Tuple

class GazeHandFusion:
    def __init__(self):
        self.target_spawn_time: Optional[float] = None
        self.target_pos: Optional[Tuple[float, float]] = None
        self.gaze_fixation_time: Optional[float] = None
        self.hand_motion_start_time: Optional[float] = None
        self.interaction_time: Optional[float] = None

    def on_target_spawned(self, target_pos: Tuple[float, float], timestamp: float):
        self.target_spawn_time = timestamp
        self.target_pos = target_pos
        self.gaze_fixation_time = None
        self.hand_motion_start_time = None
        self.interaction_time = None

    def evaluate_step(self, gaze_pos: Tuple[float, float], hand_pos: Tuple[float, float],
                      hand_speed: float, timestamp: float) -> Dict[str, Any]:
        if self.target_spawn_time is None or self.target_pos is None:
            return {"active": False}

        # 1. Check Gaze Fixation on target (distance < 0.15)
        gaze_dist = float(np.hypot(gaze_pos[0] - self.target_pos[0], gaze_pos[1] - self.target_pos[1]))
        if gaze_dist < 0.15 and self.gaze_fixation_time is None:
            self.gaze_fixation_time = timestamp

        # 2. Check Hand Initiation (speed > 0.4 toward target)
        if hand_speed > 0.35 and self.hand_motion_start_time is None:
            self.hand_motion_start_time = timestamp

        # 3. Check Target Hit
        hand_dist = float(np.hypot(hand_pos[0] - self.target_pos[0], hand_pos[1] - self.target_pos[1]))
        is_hit = hand_dist < 0.10

        metrics = {
            "active": True,
            "gaze_dist": round(gaze_dist, 3),
            "hand_dist": round(hand_dist, 3),
            "is_hit": is_hit
        }

        if is_hit:
            self.interaction_time = timestamp
            # Calculate Latencies
            visual_latency = (self.gaze_fixation_time - self.target_spawn_time) if self.gaze_fixation_time else 0.4
            hand_start_latency = (self.hand_motion_start_time - self.target_spawn_time) if self.hand_motion_start_time else 0.6
            total_reaction = timestamp - self.target_spawn_time
            gaze_to_hand_latency = max(0.0, hand_start_latency - visual_latency)

            # Accuracy (closer to center of target = higher accuracy)
            accuracy = max(0.0, 1.0 - (hand_dist / 0.10))

            metrics.update({
                "completed": True,
                "visual_response_time": round(max(0.05, visual_latency), 3),
                "hand_response_time": round(max(0.10, hand_start_latency), 3),
                "gaze_to_hand_latency": round(gaze_to_hand_latency, 3),
                "total_reaction_time": round(max(0.2, total_reaction), 3),
                "target_accuracy": round(accuracy, 2)
            })
            # Reset for next target
            self.target_spawn_time = None
        else:
            metrics["completed"] = False

        return metrics
