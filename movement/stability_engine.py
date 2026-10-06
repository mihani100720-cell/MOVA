"""
MOVA Stability Engine: Analyzes body center variation, torso lean, posture sway
Produces a non-medical stability score [0..100] based on center-of-gravity variance.
"""

from typing import List, Tuple, Dict, Any
import numpy as np

class StabilityEngine:
    def __init__(self, window_size: int = 45):
        self.window_size = window_size
        self.center_history: List[Tuple[float, float]] = []

    def update(self, body_center: Tuple[float, float]) -> Dict[str, Any]:
        self.center_history.append((body_center[0], body_center[1]))
        if len(self.center_history) > self.window_size:
            self.center_history.pop(0)

        if len(self.center_history) < 10:
            return {
                "stability_score": 95.0,
                "sway_x": 0.01,
                "sway_y": 0.01,
                "posture_status": "Calibrating"
            }

        arr = np.array(self.center_history)
        std_x = float(np.std(arr[:, 0]))
        std_y = float(np.std(arr[:, 1]))
        sway_magnitude = float(np.hypot(std_x, std_y))

        # Standard sway in resting posture is ~0.005 - 0.03 in normalized units
        # Sway > 0.15 indicates heavy displacement or dynamic leaning
        score = max(20.0, 100.0 - (sway_magnitude * 350.0))
        score = min(100.0, round(score, 1))

        status = "Steady"
        if sway_magnitude > 0.08:
            status = "Dynamic Shift"
        elif sway_magnitude > 0.04:
            status = "Moderate Sway"

        return {
            "stability_score": score,
            "sway_x": round(std_x, 4),
            "sway_y": round(std_y, 4),
            "sway_magnitude": round(sway_magnitude, 4),
            "posture_status": status
        }

    def reset(self):
        self.center_history.clear()
