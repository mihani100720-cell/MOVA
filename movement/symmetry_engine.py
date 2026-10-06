"""
MOVA Symmetry Engine: Bilateral comparison of left and right arm/hand metrics
Calculates symmetry index [0..1.0] where 1.0 represents balanced movement.
"""

from typing import Dict, Any, Tuple
import numpy as np

class SymmetryEngine:
    @staticmethod
    def calculate_balance_ratio(left_val: float, right_val: float) -> float:
        """
        Returns symmetry ratio [0..1.0].
        1.0 means perfectly balanced.
        """
        denom = left_val + right_val
        if denom < 1e-4:
            return 1.0
        # Absolute difference normalized
        diff = abs(left_val - right_val) / denom
        return round(float(np.clip(1.0 - diff, 0.0, 1.0)), 3)

    def evaluate_arms_symmetry(self, left_reach: float, right_reach: float,
                               left_speed: float, right_speed: float) -> Dict[str, Any]:
        reach_symmetry = self.calculate_balance_ratio(left_reach, right_reach)
        speed_symmetry = self.calculate_balance_ratio(left_speed, right_speed)
        overall_symmetry = round((reach_symmetry * 0.5 + speed_symmetry * 0.5), 3)

        dominant_side = "Balanced"
        if left_reach > right_reach * 1.25 or left_speed > right_speed * 1.25:
            dominant_side = "Left active"
        elif right_reach > left_reach * 1.25 or right_speed > left_speed * 1.25:
            dominant_side = "Right active"

        return {
            "reach_symmetry": reach_symmetry,
            "speed_symmetry": speed_symmetry,
            "overall_symmetry": overall_symmetry,
            "side_balance": dominant_side
        }
