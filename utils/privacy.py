"""
MOVA Utilities: Logger, Timers, Validation, and Privacy
"""

import logging
import time
import sys
from typing import Dict, Any, Optional

def setup_logger(name: str = "MOVA") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()

class Timer:
    """High-precision execution timer."""
    def __init__(self):
        self.start_time: float = time.perf_counter()
        self.split_time: float = self.start_time

    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time

    def split(self) -> float:
        now = time.perf_counter()
        diff = now - self.split_time
        self.split_time = now
        return diff

    def reset(self):
        self.start_time = time.perf_counter()
        self.split_time = self.start_time

class FPSCounter:
    """Moving average FPS counter."""
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.timestamps = []

    def tick(self) -> float:
        now = time.perf_counter()
        self.timestamps.append(now)
        if len(self.timestamps) > self.window_size:
            self.timestamps.pop(0)
        if len(self.timestamps) > 1:
            duration = self.timestamps[-1] - self.timestamps[0]
            if duration > 0:
                return (len(self.timestamps) - 1) / duration
        return 30.0

def sanitize_metrics_for_cloud(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Privacy guard: Strip any raw images, frames, or biometric identifiers.
    Only numeric scalars, movement patterns, and structured scores are permitted.
    """
    safe_keys = {
        "game_id", "game_name", "score", "accuracy", "reaction_time",
        "movement_score", "repetitions", "left_right_balance",
        "stability_score", "gaze_accuracy", "gesture_accuracy",
        "coordination_score", "multimodal_coordination", "difficulty_level",
        "targets_attempted", "targets_successful", "duration", "timestamp",
        "combo", "trend_delta"
    }
    sanitized = {}
    for k, v in metrics.items():
        if k in safe_keys and isinstance(v, (int, float, str, bool)):
            sanitized[k] = v
    return sanitized
