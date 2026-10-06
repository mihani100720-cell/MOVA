"""
MOVA Movement Classifier & Anomaly Detector
Implements Section 24:
- Predefined movement pattern classifier (Reaching, Dodging, Glyph Casting, Rhythm Tapping, Balance Shift)
- Isolation Forest anomaly detection strictly relative to user's OWN previous sessions.
- Transparent rule-based fallback when insufficient history exists.
"""

import numpy as np
try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except (ImportError, Exception):
    IsolationForest = None
    SKLEARN_AVAILABLE = False

class MovementClassifier:
    """
    Classifies the dominant movement pattern observed in the session.
    """
    PATTERNS = ["Reaching / Spatial", "Rapid Dodge / Evasion", "Glyph Trajectory", "Rhythm Synchronization", "Postural Balance"]

    @classmethod
    def classify(cls, metrics_summary: Dict[str, Any], extra_metrics: Dict[str, Any]) -> Dict[str, Any]:
        speed = metrics_summary.get("avg_speed", 0.0)
        stability = metrics_summary.get("avg_stability", 90.0)
        reps = metrics_summary.get("total_repetitions", 0)
        glyph_score = extra_metrics.get("glyph_accuracy", 0.0)
        rhythm_acc = extra_metrics.get("rhythm_sync", 0.0)

        if glyph_score > 0.6:
            pattern = "Glyph Trajectory"
            confidence = round(min(0.98, glyph_score), 2)
        elif rhythm_acc > 0.6:
            pattern = "Rhythm Synchronization"
            confidence = round(min(0.98, rhythm_acc), 2)
        elif stability < 75.0 or extra_metrics.get("dodge_count", 0) > 3:
            pattern = "Rapid Dodge / Evasion"
            confidence = 0.88
        elif reps > 8:
            pattern = "Reaching / Spatial"
            confidence = 0.92
        else:
            pattern = "Postural Balance"
            confidence = 0.82

        return {
            "dominant_pattern": pattern,
            "confidence": confidence,
            "description": f"Observed movement dynamics characteristic of {pattern}."
        }

class PersonalAnomalyDetector:
    """
    Detects deviations relative ONLY to user's own previous baseline history.
    Never compares against other individuals.
    """
    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.is_fitted: bool = False

    def fit_user_baseline(self, previous_feature_matrix: np.ndarray):
        if SKLEARN_AVAILABLE and IsolationForest is not None and previous_feature_matrix.shape[0] >= 5:
            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.model.fit(previous_feature_matrix)
            self.is_fitted = True
        else:
            self.is_fitted = False

    def check_anomaly(self, current_vector: np.ndarray, baseline_mean: Optional[np.ndarray] = None) -> Dict[str, Any]:
        if self.is_fitted and self.model is not None:
            pred = self.model.predict(current_vector.reshape(1, -1))[0]
            # -1 = anomaly, 1 = normal
            score = float(self.model.decision_function(current_vector.reshape(1, -1))[0])
            is_unusual = (pred == -1)
            return {
                "method": "IsolationForest",
                "is_atypical_for_user": bool(is_unusual),
                "decision_score": round(score, 3),
                "status": "Consistent with your personal baseline" if not is_unusual else "Observed variation from your typical movement speed or reaction"
            }
        elif baseline_mean is not None:
            # Transparent statistical rule fallback
            diff = np.abs(current_vector - baseline_mean)
            norm_diff = np.mean(diff / (np.abs(baseline_mean) + 1e-4))
            is_unusual = norm_diff > 0.40
            return {
                "method": "StatisticalBaselineComparison",
                "is_atypical_for_user": bool(is_unusual),
                "decision_score": round(float(norm_diff), 3),
                "status": "Consistent with your personal baseline" if not is_unusual else "Distinct pacing variation observed relative to your baseline"
            }
        else:
            return {
                "method": "BaselineAccumulation",
                "is_atypical_for_user": False,
                "decision_score": 0.0,
                "status": "Building personal baseline history (Session 1-4)"
            }
