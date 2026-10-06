"""
MOVA Vision Confidence & Lighting Estimator
Evaluates frame brightness, contrast, and landmark tracking confidences.
"""

import cv2
import numpy as np
from typing import Dict, Any, Tuple

class QualityEvaluator:
    @staticmethod
    def evaluate_frame_lighting(frame: np.ndarray) -> Tuple[float, str]:
        """
        Analyzes frame luminance and returns a normalized score [0..1] and status message.
        """
        if frame is None or frame.size == 0:
            return 0.0, "No camera frame"

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        contrast = np.std(gray)

        # Optimal mean brightness is roughly 90-170, contrast > 30
        if mean_brightness < 40:
            return 0.3, "Lighting too dark - Move to a brighter area"
        elif mean_brightness > 220:
            return 0.4, "Lighting too bright / overexposed"
        elif contrast < 20:
            return 0.5, "Low contrast - improve room lighting"
        else:
            norm_score = min(1.0, max(0.5, (mean_brightness / 128.0) * 0.9))
            return round(norm_score, 2), "Optimal lighting"

    @staticmethod
    def compute_landmarks_confidence(landmarks_list) -> float:
        """
        Computes the average visibility/presence confidence from landmarks.
        """
        if not landmarks_list:
            return 0.0
        scores = []
        for lm in landmarks_list:
            if hasattr(lm, 'visibility') and lm.visibility is not None:
                scores.append(float(lm.visibility))
            elif hasattr(lm, 'presence') and lm.presence is not None:
                scores.append(float(lm.presence))
            else:
                scores.append(1.0)
        return round(float(np.mean(scores)) if scores else 0.0, 2)
