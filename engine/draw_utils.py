"""
MOVA Draw Utilities — OpenCV rendering helpers.
All drawing is done in BGR (OpenCV native format).
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List

# ─── Palette ──────────────────────────────────────────────────────────────────
CYAN    = (255, 235,  0)   # BGR: our "cyan" = gold-yellow in BGR
PURPLE  = (202,  40, 121)  # BGR purple
PINK    = (128,   0, 255)  # BGR pink
GREEN   = ( 80, 255, 100)  # BGR green
RED     = (  0,  60, 255)  # BGR red
WHITE   = (255, 255, 255)
BLACK   = (  0,   0,   0)
DARK    = ( 18,  18,  28)  # near-black background
ACCENT  = (  0, 229, 255)  # bright cyan BGR
GOLD    = (  0, 215, 255)  # gold BGR


def put_text(frame: np.ndarray, text: str, pos: Tuple[int, int],
             scale: float = 0.7, color=WHITE, thickness: int = 1,
             font=cv2.FONT_HERSHEY_DUPLEX, shadow: bool = True) -> None:
    if shadow:
        cv2.putText(frame, text, (pos[0]+2, pos[1]+2), font, scale, BLACK, thickness+1, cv2.LINE_AA)
    cv2.putText(frame, text, pos, font, scale, color, thickness, cv2.LINE_AA)


def bar(frame: np.ndarray, x: int, y: int, w: int, h: int,
        value: float, color=ACCENT, bg=(50, 50, 60), label: str = "") -> None:
    """Draw a filled progress bar."""
    cv2.rectangle(frame, (x, y), (x+w, y+h), bg, -1, cv2.LINE_AA)
    filled = int(np.clip(value, 0.0, 1.0) * w)
    if filled > 0:
        cv2.rectangle(frame, (x, y), (x+filled, y+h), color, -1, cv2.LINE_AA)
    cv2.rectangle(frame, (x, y), (x+w, y+h), WHITE, 1, cv2.LINE_AA)
    if label:
        put_text(frame, label, (x+4, y+h-4), 0.45, WHITE, 1)


def draw_rounded_rect(frame: np.ndarray, x1: int, y1: int, x2: int, y2: int,
                      color, radius: int = 12, thickness: int = -1) -> None:
    """Draw a filled or outlined rounded rectangle."""
    cv2.rectangle(frame, (x1+radius, y1), (x2-radius, y2), color, thickness)
    cv2.rectangle(frame, (x1, y1+radius), (x2, y2-radius), color, thickness)
    for cx, cy in [(x1+radius, y1+radius), (x2-radius, y1+radius),
                   (x1+radius, y2-radius), (x2-radius, y2-radius)]:
        cv2.circle(frame, (cx, cy), radius, color, thickness)


def draw_hud_overlay(frame: np.ndarray, score: int, time_left: float,
                     level: float, gesture: str, fps: float,
                     pose_ok: bool, hands_ok: int) -> None:
    """Standard game HUD drawn on frame."""
    h, w = frame.shape[:2]

    # Semi-transparent top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 52), (10, 10, 20), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    # Score
    put_text(frame, f"SCORE  {score:06d}", (12, 36), 0.85, ACCENT, 2)

    # Time
    tc = GREEN if time_left > 10 else RED
    put_text(frame, f"TIME  {time_left:.1f}s", (w//2 - 80, 36), 0.85, tc, 2)

    # Level / Difficulty
    put_text(frame, f"LVL  {level:.1f}", (w - 180, 36), 0.75, GOLD, 2)

    # Bottom status bar
    cv2.rectangle(overlay, (0, h-38), (w, h), (10, 10, 20), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    # Tracking badges
    pose_c = GREEN if pose_ok else RED
    put_text(frame, "● POSE", (12, h-12), 0.55, pose_c, 1)
    hand_c = GREEN if hands_ok > 0 else RED
    put_text(frame, f"● HANDS:{hands_ok}", (110, h-12), 0.55, hand_c, 1)
    put_text(frame, f"GESTURE: {gesture}", (280, h-12), 0.55, CYAN, 1)
    put_text(frame, f"FPS: {fps:.0f}", (w-110, h-12), 0.55, WHITE, 1)


def draw_hand_skeleton(frame: np.ndarray, landmarks: np.ndarray,
                       color=ACCENT, dot_radius: int = 5) -> None:
    """Draw 21-point hand skeleton on frame."""
    if landmarks is None or len(landmarks) < 21:
        return
    h, w = frame.shape[:2]

    # Connection map
    CONNECTIONS = [
        (0,1),(1,2),(2,3),(3,4),         # thumb
        (0,5),(5,6),(6,7),(7,8),          # index
        (0,9),(9,10),(10,11),(11,12),     # middle
        (0,13),(13,14),(14,15),(15,16),   # ring
        (0,17),(17,18),(18,19),(19,20),   # pinky
        (5,9),(9,13),(13,17),             # palm
    ]

    pts = [(int(landmarks[i, 0]*w), int(landmarks[i, 1]*h)) for i in range(21)]

    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], color, 2, cv2.LINE_AA)
    for i, (px, py) in enumerate(pts):
        c = (0, 200, 255) if i == 0 else color
        cv2.circle(frame, (px, py), dot_radius if i == 0 else 3, c, -1, cv2.LINE_AA)


def draw_pose_skeleton(frame: np.ndarray, landmarks: np.ndarray,
                       color=GREEN) -> None:
    """Draw body pose skeleton (33 landmarks)."""
    if landmarks is None or len(landmarks) < 33:
        return
    h, w = frame.shape[:2]

    CONNECTIONS = [
        (11,12),(11,13),(13,15),(12,14),(14,16),  # arms
        (11,23),(12,24),(23,24),                   # torso
        (23,25),(25,27),(24,26),(26,28),            # legs
    ]
    pts = [(int(landmarks[i, 0]*w), int(landmarks[i, 1]*h)) for i in range(33)]

    for a, b in CONNECTIONS:
        if a < len(pts) and b < len(pts):
            cv2.line(frame, pts[a], pts[b], color, 2, cv2.LINE_AA)
    for px, py in pts[11:]:  # skip face landmarks
        cv2.circle(frame, (px, py), 4, color, -1, cv2.LINE_AA)


def draw_target(frame: np.ndarray, cx: float, cy: float, r: float,
                color=ACCENT, label: str = "", glow: bool = True) -> None:
    """Draw a circular game target with optional glow effect."""
    h, w = frame.shape[:2]
    px, py, pr = int(cx*w), int(cy*h), int(r*min(w,h))

    if glow:
        for offset in [8, 5, 2]:
            alpha_col = tuple(max(0, c - offset*20) for c in color)
            cv2.circle(frame, (px, py), pr+offset, alpha_col, 1, cv2.LINE_AA)

    cv2.circle(frame, (px, py), pr, color, 2, cv2.LINE_AA)
    cv2.circle(frame, (px, py), max(1, pr-4), (*color[:3],), -1, cv2.LINE_AA)

    if label:
        tw, th = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)[0]
        put_text(frame, label, (px - tw//2, py + th//2), 0.5, WHITE, 1)


def draw_menu_bg(frame: np.ndarray) -> None:
    """Draw animated dark spatial background."""
    frame[:] = DARK
    h, w = frame.shape[:2]
    # Subtle grid
    for x in range(0, w, 60):
        cv2.line(frame, (x, 0), (x, h), (30, 30, 45), 1)
    for y in range(0, h, 60):
        cv2.line(frame, (0, y), (w, y), (30, 30, 45), 1)
