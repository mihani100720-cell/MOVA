"""
MOVA Landmark Processor: Coordinate normalization, smoothing, and geometric helpers
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional, List

class ExponentialMovingAverage:
    """Smoothes jittery landmark stream."""
    def __init__(self, alpha: float = 0.65):
        self.alpha = alpha
        self.value: Optional[np.ndarray] = None

    def update(self, val: np.ndarray) -> np.ndarray:
        if self.value is None:
            self.value = np.array(val, dtype=float)
        else:
            self.value = self.alpha * np.array(val, dtype=float) + (1.0 - self.alpha) * self.value
        return self.value

    def reset(self):
        self.value = None

class LandmarkProcessor:
    @staticmethod
    def to_pixel_coords(norm_x: float, norm_y: float, width: int, height: int) -> Tuple[int, int]:
        px = int(np.clip(norm_x * width, 0, width - 1))
        py = int(np.clip(norm_y * height, 0, height - 1))
        return px, py

    @staticmethod
    def calculate_distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return float(np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2))

    @staticmethod
    def calculate_distance_3d(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
        return float(np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2))

    @staticmethod
    def calculate_angle_3p(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
        """
        Calculates angle at joint vertex B in degrees: ABC.
        """
        ba = np.array([a[0] - b[0], a[1] - b[1]])
        bc = np.array([c[0] - b[0], c[1] - b[1]])
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)
        if norm_ba == 0 or norm_bc == 0:
            return 0.0
        cosine = np.dot(ba, bc) / (norm_ba * norm_bc)
        cosine = np.clip(cosine, -1.0, 1.0)
        angle = np.degrees(np.arccos(cosine))
        return float(angle)
