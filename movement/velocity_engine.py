"""
MOVA Velocity & Acceleration Engine
Calculates movement velocity, acceleration, and jerk for hands, arms, and torso.
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional, List

class KinematicTracker:
    def __init__(self, history_len: int = 15):
        self.history_len = history_len
        self.positions: List[Tuple[float, float, float]] = []  # (x, y, timestamp)
        self.velocities: List[Tuple[float, float]] = []
        self.accelerations: List[float] = []

    def update(self, pos: Tuple[float, float], timestamp: float) -> Dict[str, float]:
        self.positions.append((pos[0], pos[1], timestamp))
        if len(self.positions) > self.history_len:
            self.positions.pop(0)

        vx, vy, speed, accel = 0.0, 0.0, 0.0, 0.0

        if len(self.positions) >= 2:
            p1 = self.positions[-2]
            p2 = self.positions[-1]
            dt = p2[2] - p1[2]
            if dt > 0.001:
                vx = (p2[0] - p1[0]) / dt
                vy = (p2[1] - p1[1]) / dt
                speed = float(np.hypot(vx, vy))
                self.velocities.append((vx, vy))
                if len(self.velocities) > self.history_len:
                    self.velocities.pop(0)

        if len(self.velocities) >= 2 and len(self.positions) >= 3:
            dt = self.positions[-1][2] - self.positions[-2][2]
            if dt > 0.001:
                dvx = self.velocities[-1][0] - self.velocities[-2][0]
                dvy = self.velocities[-1][1] - self.velocities[-2][1]
                accel = float(np.hypot(dvx, dvy) / dt)
                self.accelerations.append(accel)
                if len(self.accelerations) > self.history_len:
                    self.accelerations.pop(0)

        return {
            "vx": round(vx, 3),
            "vy": round(vy, 3),
            "speed": round(speed, 3),
            "acceleration": round(accel, 3)
        }

class VelocityEngine:
    def __init__(self):
        self.trackers = {
            "right_hand": KinematicTracker(),
            "left_hand": KinematicTracker(),
            "body_center": KinematicTracker(),
            "head": KinematicTracker()
        }

    def update(self, positions: Dict[str, Tuple[float, float]], timestamp: float) -> Dict[str, Dict[str, float]]:
        results = {}
        for key, pos in positions.items():
            if key not in self.trackers:
                self.trackers[key] = KinematicTracker()
            results[key] = self.trackers[key].update(pos, timestamp)
        return results
