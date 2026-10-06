"""
MOVA Trajectory Engine: Path analysis, smoothness, efficiency, and trajectory matching
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional

class TrajectoryEngine:
    def __init__(self, max_points: int = 100):
        self.max_points = max_points
        self.trail: List[Tuple[float, float]] = []

    def add_point(self, pt: Tuple[float, float]):
        self.trail.append((float(pt[0]), float(pt[1])))
        if len(self.trail) > self.max_points:
            self.trail.pop(0)

    def clear(self):
        self.trail.clear()

    def get_trail(self) -> List[Tuple[float, float]]:
        return list(self.trail)

    def calculate_path_length(self) -> float:
        if len(self.trail) < 2:
            return 0.0
        pts = np.array(self.trail)
        diffs = np.diff(pts, axis=0)
        seg_lengths = np.hypot(diffs[:, 0], diffs[:, 1])
        return float(np.sum(seg_lengths))

    def calculate_efficiency(self) -> float:
        """
        Ratio of straight-line distance to actual path length [0..1].
        1.0 means perfectly direct, lower means wandering path.
        """
        if len(self.trail) < 3:
            return 1.0
        total_len = self.calculate_path_length()
        if total_len < 1e-4:
            return 1.0
        direct_dist = np.hypot(self.trail[-1][0] - self.trail[0][0], self.trail[-1][1] - self.trail[0][1])
        return float(np.clip(direct_dist / total_len, 0.0, 1.0))

    def calculate_smoothness(self) -> float:
        """
        Evaluates smoothness using normalized jerk / change in direction.
        Higher = smoother movement pattern.
        """
        if len(self.trail) < 4:
            return 1.0
        pts = np.array(self.trail)
        diffs = np.diff(pts, axis=0)
        angles = np.arctan2(diffs[:, 1], diffs[:, 0])
        angle_diffs = np.abs(np.diff(angles))
        # Wrap angle diffs to [0, pi]
        angle_diffs = np.where(angle_diffs > np.pi, 2 * np.pi - angle_diffs, angle_diffs)
        mean_jitter = float(np.mean(angle_diffs))
        # Jitter of 0 -> score 1.0, jitter of pi -> score 0.0
        smoothness = max(0.0, 1.0 - (mean_jitter / np.pi))
        return round(smoothness, 3)

    @staticmethod
    def match_glyph(candidate: List[Tuple[float, float]], reference_shape: str) -> float:
        """
        Compares drawn trajectory against standard geometric shapes:
        'CIRCLE', 'ZIGZAG', 'STAR', 'TRIANGLE', 'HORIZONTAL', 'VERTICAL'
        Returns similarity score [0..1].
        """
        if len(candidate) < 10:
            return 0.0

        pts = np.array(candidate)
        # Normalize points to bounding box [0..1, 0..1]
        min_xy = np.min(pts, axis=0)
        max_xy = np.max(pts, axis=0)
        span = max_xy - min_xy
        if np.any(span < 0.02):
            # Flat line
            if reference_shape == "HORIZONTAL" and span[0] > span[1]:
                return 0.95
            if reference_shape == "VERTICAL" and span[1] > span[0]:
                return 0.95
            return 0.2

        norm_pts = (pts - min_xy) / (span + 1e-6)

        if reference_shape == "CIRCLE":
            # Distance of points to center should be roughly constant
            center = np.mean(norm_pts, axis=0)
            radii = np.hypot(norm_pts[:, 0] - center[0], norm_pts[:, 1] - center[1])
            std_r = np.std(radii)
            # Ideal circle has std_r near 0
            score = max(0.0, 1.0 - std_r * 3.5)
            # Check loop closure: start and end are close
            closure = np.hypot(norm_pts[0][0] - norm_pts[-1][0], norm_pts[0][1] - norm_pts[-1][1])
            score *= max(0.4, 1.0 - closure)
            return round(float(np.clip(score, 0.0, 1.0)), 2)

        elif reference_shape == "ZIGZAG":
            # Multiple reversals in dx
            diffs = np.diff(norm_pts[:, 0])
            sign_changes = np.sum(np.diff(np.sign(diffs[diffs != 0])) != 0)
            if sign_changes >= 2:
                return 0.88
            return 0.4

        elif reference_shape == "TRIANGLE":
            # 3 primary segments
            closure = np.hypot(norm_pts[0][0] - norm_pts[-1][0], norm_pts[0][1] - norm_pts[-1][1])
            if closure < 0.35:
                return 0.85
            return 0.5

        return 0.75
