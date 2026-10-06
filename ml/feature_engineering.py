"""
MOVA Feature Engineering: Vectorizes movement kinematics and multimodal metrics for ML models
"""

import numpy as np
from typing import Dict, Any, List

class FeatureEngineer:
    FEATURE_NAMES = [
        "avg_speed",
        "avg_stability",
        "avg_symmetry",
        "avg_accuracy",
        "avg_reaction_time",
        "movement_consistency",
        "multimodal_coordination",
        "total_repetitions",
        "difficulty_level"
    ]

    @classmethod
    def extract_session_features(cls, metrics_summary: Dict[str, Any],
                                 fusion_summary: Dict[str, Any],
                                 difficulty: float = 1.0) -> np.ndarray:
        vec = [
            float(metrics_summary.get("avg_speed", 0.0)),
            float(metrics_summary.get("avg_stability", 90.0)),
            float(metrics_summary.get("avg_symmetry", 0.85)),
            float(metrics_summary.get("avg_accuracy", 0.80)),
            float(metrics_summary.get("avg_reaction_time", 0.70)),
            float(metrics_summary.get("movement_consistency", 0.80)),
            float(fusion_summary.get("avg_multimodal_coordination", 85.0)),
            float(metrics_summary.get("total_repetitions", 5)),
            float(difficulty)
        ]
        return np.array(vec, dtype=float)
