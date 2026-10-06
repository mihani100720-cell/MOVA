"""
MOVA Spatial Engine: Coordinate transforms, spatial bounds, and MOVA Zone grid geometry
"""

import numpy as np
from typing import Tuple, Dict, Any, List

class SpatialEngine:
    def __init__(self, zone_bounds: Tuple[float, float, float, float] = (0.1, 0.1, 0.9, 0.9)):
        """
        zone_bounds: (x_min, y_min, x_max, y_max) normalized in [0..1]
        """
        self.x_min, self.y_min, self.x_max, self.y_max = zone_bounds

    def is_inside_zone(self, point: Tuple[float, float]) -> bool:
        return (self.x_min <= point[0] <= self.x_max and
                self.y_min <= point[1] <= self.y_max)

    def normalize_to_zone(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """Maps point to [-1.0 .. +1.0] spatial zone relative to center."""
        cx = (self.x_min + self.x_max) / 2.0
        cy = (self.y_min + self.y_max) / 2.0
        hw = (self.x_max - self.x_min) / 2.0
        hh = (self.y_max - self.y_min) / 2.0

        zx = (point[0] - cx) / (hw + 1e-6)
        zy = (point[1] - cy) / (hh + 1e-6)
        return float(np.clip(zx, -1.0, 1.0)), float(np.clip(zy, -1.0, 1.0))

    def calculate_spatial_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return float(np.hypot(p1[0] - p2[0], p1[1] - p2[1]))

    def get_grid_cells(self, rows: int = 4, cols: int = 4) -> List[Dict[str, Any]]:
        cells = []
        dx = (self.x_max - self.x_min) / cols
        dy = (self.y_max - self.y_min) / rows
        for r in range(rows):
            for c in range(cols):
                cells.append({
                    "id": f"cell_{r}_{c}",
                    "row": r,
                    "col": c,
                    "x_min": self.x_min + c * dx,
                    "y_min": self.y_min + r * dy,
                    "x_max": self.x_min + (c + 1) * dx,
                    "y_max": self.y_min + (r + 1) * dy,
                    "center": (self.x_min + (c + 0.5) * dx, self.y_min + (r + 0.5) * dy)
                })
        return cells
