"""
MOVA Coordination Engine: Bilateral hand synchronization and cross-modality timing
"""

from typing import Dict, Any, List, Tuple
import numpy as np

class CoordinationEngine:
    def __init__(self, history_len: int = 30):
        self.history_len = history_len
        self.left_speeds: List[float] = []
        self.right_speeds: List[float] = []

    def update_bilateral(self, left_speed: float, right_speed: float) -> Dict[str, Any]:
        self.left_speeds.append(left_speed)
        self.right_speeds.append(right_speed)
        if len(self.left_speeds) > self.history_len:
            self.left_speeds.pop(0)
            self.right_speeds.pop(0)

        if len(self.left_speeds) < 8:
            return {"bilateral_sync_score": 0.85, "phase_relationship": "Synchronous"}

        # Correlation between left and right speed envelopes
        l_arr = np.array(self.left_speeds)
        r_arr = np.array(self.right_speeds)
        if np.std(l_arr) < 1e-4 or np.std(r_arr) < 1e-4:
            sync = 0.90
        else:
            corr = np.corrcoef(l_arr, r_arr)[0, 1]
            sync = float(np.clip((corr + 1.0) / 2.0, 0.0, 1.0))

        phase = "Synchronous"
        if sync < 0.35:
            phase = "Alternating / Asymmetric"
        elif sync < 0.65:
            phase = "Partially Coupled"

        return {
            "bilateral_sync_score": round(sync, 2),
            "phase_relationship": phase
        }
