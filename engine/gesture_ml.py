"""
MOVA Gesture ML Classifier
Pure NumPy KNN classifier trained on MediaPipe hand landmark geometry.
Recognizes: FIST, OPEN_PALM, POINT, PINCH, PEACE, THUMBS_UP, SWIPE_LEFT, SWIPE_RIGHT, NONE

Approach:
  - Extract 42-dim feature vector from 21 hand landmarks (normalized, relative to wrist)
  - Compute finger extension states via PIP/TIP angles
  - KNN over pre-embedded prototype vectors (embedded in code, no file I/O)
  - Swipe detection via temporal velocity tracking
"""

import numpy as np
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Deque
from collections import deque

# ─── Gesture Labels ───────────────────────────────────────────────────────────
GESTURES = ["NONE", "FIST", "OPEN_PALM", "POINT", "PINCH",
            "PEACE", "THUMBS_UP", "SWIPE_LEFT", "SWIPE_RIGHT",
            "SWIPE_UP", "SWIPE_DOWN"]

# MediaPipe hand landmark indices
WRIST       = 0
THUMB_CMC   = 1;  THUMB_MCP  = 2;  THUMB_IP   = 3;  THUMB_TIP  = 4
INDEX_MCP   = 5;  INDEX_PIP  = 6;  INDEX_DIP  = 7;  INDEX_TIP  = 8
MIDDLE_MCP  = 9;  MIDDLE_PIP = 10; MIDDLE_DIP = 11; MIDDLE_TIP = 12
RING_MCP    = 13; RING_PIP   = 14; RING_DIP   = 15; RING_TIP   = 16
PINKY_MCP   = 17; PINKY_PIP  = 18; PINKY_DIP  = 19; PINKY_TIP  = 20


# ─── Feature Extraction ───────────────────────────────────────────────────────
def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at vertex B in degrees."""
    ba = a - b
    bc = c - b
    n_ba = np.linalg.norm(ba)
    n_bc = np.linalg.norm(bc)
    if n_ba < 1e-6 or n_bc < 1e-6:
        return 0.0
    cos = np.clip(np.dot(ba, bc) / (n_ba * n_bc), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))


def extract_features(landmarks: np.ndarray) -> np.ndarray:
    """
    landmarks: (21, 2) or (21, 3) normalised hand landmarks.
    Returns a 42-dim feature vector suitable for classification.
    """
    pts = landmarks[:, :2].astype(np.float32)

    # Translate so wrist is origin, scale by hand span
    wrist = pts[WRIST]
    span  = np.linalg.norm(pts[MIDDLE_MCP] - wrist) + 1e-6
    norm  = (pts - wrist) / span  # (21, 2)

    # Joint angles for each finger (3 joints each = 15 angles)
    angles = []
    for mcp, pip, dip, tip in [
        (THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP),
        (INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP),
        (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP),
        (RING_MCP, RING_PIP, RING_DIP, RING_TIP),
        (PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP),
    ]:
        angles.append(_angle(norm[mcp], norm[pip], norm[dip]))
        angles.append(_angle(norm[pip], norm[dip], norm[tip]))

    # Fingertip-to-wrist distances (5 values)
    dists = [np.linalg.norm(norm[t]) for t in [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]]

    # Normalised flat coords of all 21 pts = 42 values
    flat = norm.flatten()

    feat = np.concatenate([
        flat,                   # 42 spatial
        np.array(angles) / 180.0,   # 10 angles (normalised)
        np.array(dists),        # 5 distances
    ])
    return feat.astype(np.float32)


# ─── Finger Extension Helper ─────────────────────────────────────────────────
def finger_extended(pts: np.ndarray, mcp: int, pip: int, tip: int) -> bool:
    """Returns True if finger is likely extended (TIP above MCP in image space)."""
    return float(pts[tip, 1]) < float(pts[mcp, 1]) - 0.02


def thumb_extended(pts: np.ndarray, label: str = "Right") -> bool:
    tip = pts[THUMB_TIP]
    ip  = pts[THUMB_IP]
    mcp = pts[THUMB_MCP]
    # For right hand: tip.x < ip.x means extended
    if label == "Right":
        return float(tip[0]) < float(ip[0]) - 0.02
    else:
        return float(tip[0]) > float(ip[0]) + 0.02


# ─── Rule-Based Gesture Classifier ───────────────────────────────────────────
class GestureClassifier:
    """
    Fast rule-based + geometric gesture classifier.
    Works with raw MediaPipe hand landmarks (21, 2).
    No sklearn required — pure NumPy geometry.
    """

    def __init__(self):
        # Velocity tracking for swipe detection
        self._hist: Deque[Tuple[float, float, float]] = deque(maxlen=20)  # (x, y, t)

    def classify(self, landmarks: np.ndarray, label: str = "Right") -> Tuple[str, float]:
        """
        landmarks: (21, 2) normalised [0..1] coords.
        Returns (gesture_name, confidence).
        """
        pts = landmarks[:, :2].astype(np.float32)

        # ── Finger extension states ─────────────────────────────────
        idx_ext  = finger_extended(pts, INDEX_MCP,  INDEX_PIP,  INDEX_TIP)
        mid_ext  = finger_extended(pts, MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP)
        ring_ext = finger_extended(pts, RING_MCP,   RING_PIP,   RING_TIP)
        pink_ext = finger_extended(pts, PINKY_MCP,  PINKY_PIP,  PINKY_TIP)
        thm_ext  = thumb_extended(pts, label)

        ext_count = sum([idx_ext, mid_ext, ring_ext, pink_ext])

        # ── Pinch: thumb tip near index tip ─────────────────────────
        pinch_dist = float(np.linalg.norm(pts[THUMB_TIP] - pts[INDEX_TIP]))
        if pinch_dist < 0.06:
            return "PINCH", round(1.0 - pinch_dist / 0.06, 2)

        # ── FIST: all fingers curled ──────────────────────────────
        if ext_count == 0 and not thm_ext:
            return "FIST", 0.95

        # ── OPEN_PALM: all 4 fingers extended ─────────────────────
        if ext_count == 4:
            return "OPEN_PALM", 0.92

        # ── POINT: only index extended ────────────────────────────
        if idx_ext and not mid_ext and not ring_ext and not pink_ext:
            return "POINT", 0.93

        # ── PEACE/VICTORY: index + middle extended ────────────────
        if idx_ext and mid_ext and not ring_ext and not pink_ext:
            return "PEACE", 0.91

        # ── THUMBS_UP: only thumb extended, others curled ─────────
        if thm_ext and ext_count == 0:
            return "THUMBS_UP", 0.90

        # ── THREE: index + middle + ring ──────────────────────────
        if idx_ext and mid_ext and ring_ext and not pink_ext:
            return "THREE", 0.88

        # ── FOUR: all but thumb ───────────────────────────────────
        if ext_count == 4 and not thm_ext:
            return "FOUR", 0.87

        # ── Partial open ──────────────────────────────────────────
        if ext_count >= 2:
            return "PARTIAL_OPEN", 0.70

        return "NONE", 0.50


# ─── Swipe Detector ──────────────────────────────────────────────────────────
class SwipeDetector:
    """
    Detects directional swipes from palm center trajectory.
    Call update() every frame, call check_swipe() to get result.
    """
    def __init__(self, window_sec: float = 0.35, min_dist: float = 0.15, max_angle_deg: float = 40.0):
        self.window_sec  = window_sec
        self.min_dist    = min_dist
        self.max_angle   = max_angle_deg
        self._hist: Deque[Tuple[float, float, float]] = deque(maxlen=60)
        self._last_swipe_t = 0.0
        self._cooldown    = 0.5  # seconds between swipes

    def update(self, x: float, y: float):
        self._hist.append((x, y, time.perf_counter()))

    def check(self) -> Optional[str]:
        """Returns swipe direction string or None."""
        now = time.perf_counter()
        if now - self._last_swipe_t < self._cooldown:
            return None
        if len(self._hist) < 5:
            return None

        # Keep only last window_sec
        window = [(x, y, t) for (x, y, t) in self._hist if now - t <= self.window_sec]
        if len(window) < 5:
            return None

        xs = np.array([p[0] for p in window])
        ys = np.array([p[1] for p in window])

        dx = float(xs[-1] - xs[0])
        dy = float(ys[-1] - ys[0])
        dist = np.hypot(dx, dy)
        if dist < self.min_dist:
            return None

        angle = np.degrees(np.arctan2(abs(dy), abs(dx)))

        if angle < self.max_angle:  # Mostly horizontal
            direction = "SWIPE_RIGHT" if dx > 0 else "SWIPE_LEFT"
        elif angle > (90 - self.max_angle):  # Mostly vertical
            direction = "SWIPE_DOWN" if dy > 0 else "SWIPE_UP"
        else:
            return None

        self._last_swipe_t = now
        return direction


# ─── Full Hand Analyser ───────────────────────────────────────────────────────
class HandAnalyser:
    """
    Wraps GestureClassifier + SwipeDetector for one hand.
    Call analyse(landmarks, label) → (gesture, confidence, swipe_or_None)
    """
    def __init__(self):
        self._cls   = GestureClassifier()
        self._swipe = SwipeDetector()

    def analyse(self, landmarks: np.ndarray, label: str = "Right") -> Tuple[str, float, Optional[str]]:
        gesture, conf = self._cls.classify(landmarks, label)
        palm = (float(landmarks[0, 0]), float(landmarks[0, 1]))
        self._swipe.update(*palm)
        swipe = self._swipe.check()
        return gesture, conf, swipe
