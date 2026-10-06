"""
MOVA Game: Gesture Battle
Flash gesture icons on screen — match them with your hand before time runs out.
ML-classified gestures: FIST, OPEN_PALM, POINT, PEACE, THUMBS_UP, PINCH
Score multiplies with speed and combo streak.
"""

import cv2
import numpy as np
import time
import random
from typing import Optional

from engine.draw_utils import (put_text, draw_hand_skeleton, draw_hud_overlay,
                                ACCENT, GREEN, RED, GOLD, WHITE, PURPLE, DARK, PINK, CYAN)


CHALLENGE_GESTURES = [
    # Hand Gestures
    "FIST", "OPEN_PALM", "POINT", "PEACE", "THUMBS_UP", "PINCH",
    # Face Gestures
    "SMILE", "MOUTH_OPEN", "HEAD_TILT"
]

GESTURE_DESC = {
    "FIST":       "Close all fingers into a FIST [HAND]",
    "OPEN_PALM":  "Spread all 5 fingers wide [HAND]",
    "POINT":      "Extend INDEX finger only [HAND]",
    "PEACE":      "Extend INDEX + MIDDLE (V sign) [HAND]",
    "THUMBS_UP":  "Extend THUMB, curl other fingers [HAND]",
    "PINCH":      "Touch THUMB tip to INDEX tip [HAND]",
    "SMILE":      "SMILE big at the camera! 😊 [FACE]",
    "MOUTH_OPEN": "OPEN your mouth wide! 😮 [FACE]",
    "HEAD_TILT":  "TILT your head sideways! 🙃 [FACE]",
}

GESTURE_ICONS = {
    "FIST":      "✊",
    "OPEN_PALM": "✋",
    "POINT":     "☝",
    "PEACE":     "✌",
    "THUMBS_UP": "👍",
    "PINCH":     "🤏",
    "SMILE":     "😊",
    "MOUTH_OPEN": "😮",
    "HEAD_TILT":  "🙃",
}

COLORS = {
    "FIST": RED, "OPEN_PALM": GREEN, "POINT": ACCENT,
    "PEACE": PURPLE, "THUMBS_UP": GOLD, "PINCH": PINK,
    "SMILE": (0, 230, 255), "MOUTH_OPEN": (255, 140, 0), "HEAD_TILT": (220, 50, 240),
}


def _draw_gesture_diagram(frame: np.ndarray, gesture: str, cx: int, cy: int, size: int = 90):
    """Draw a simple diagram representing the target gesture."""
    col = COLORS.get(gesture, WHITE)

    if gesture == "FIST":
        # Closed fist: filled circle
        cv2.circle(frame, (cx, cy), size//2, col, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), size//2, WHITE, 2, cv2.LINE_AA)
        # Knuckle lines
        for i in range(4):
            kx = cx - size//3 + i*(size//5)
            cv2.circle(frame, (kx, cy - size//5), size//15, WHITE, -1)

    elif gesture == "OPEN_PALM":
        # Palm base
        cv2.ellipse(frame, (cx, cy+size//8), (size//3, size//4), 0, 0, 360, col, -1, cv2.LINE_AA)
        # Five fingers
        for i, angle in enumerate([-40, -15, 5, 25, 50]):
            rad = np.radians(angle - 90)
            fx = int(cx + np.cos(rad) * size//2)
            fy = int(cy + np.sin(rad) * size//2)
            cv2.line(frame, (cx, cy), (fx, fy), col, 8, cv2.LINE_AA)
            cv2.circle(frame, (fx, fy), 6, WHITE, -1)

    elif gesture == "POINT":
        # Palm base + index pointing up
        cv2.ellipse(frame, (cx, cy+size//5), (size//4, size//5), 0, 0, 360, col, -1)
        # Index finger
        cv2.rectangle(frame, (cx-8, cy-size//2), (cx+8, cy+size//5), col, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy - size//2), 10, WHITE, -1)
        # Curled fingers (small bumps)
        for i, dx in enumerate([-18, 18, -24]):
            cv2.rectangle(frame, (cx+dx-6, cy-5), (cx+dx+6, cy+size//5), col, -1)

    elif gesture == "PEACE":
        cv2.ellipse(frame, (cx, cy+size//5), (size//4, size//5), 0, 0, 360, col, -1)
        # Index + middle
        cv2.rectangle(frame, (cx-16, cy-size//2), (cx-4, cy+size//5), col, -1, cv2.LINE_AA)
        cv2.rectangle(frame, (cx+4,  cy-size//2), (cx+16, cy+size//5), col, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx-10, cy-size//2), 8, WHITE, -1)
        cv2.circle(frame, (cx+10, cy-size//2), 8, WHITE, -1)

    elif gesture == "THUMBS_UP":
        # Fist body
        cv2.rectangle(frame, (cx-size//4, cy-size//6), (cx+size//4, cy+size//3), col, -1, cv2.LINE_AA)
        # Thumb pointing up
        cv2.rectangle(frame, (cx-size//4-12, cy-size//2), (cx-size//4, cy+5), col, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx-size//4-6, cy-size//2), 9, WHITE, -1)
        cv2.rectangle(frame, (cx-size//4, cy-size//6), (cx+size//4, cy+size//3), WHITE, 2)

    elif gesture == "PINCH":
        cv2.ellipse(frame, (cx, cy+size//5), (size//4, size//5), 0, 0, 360, col, -1)
        # Index + thumb meeting
        ix = cx - size//4
        ty = cy - size//3
        cv2.line(frame, (cx, cy+size//5), (ix, ty), col, 10, cv2.LINE_AA)
        cv2.line(frame, (cx, cy+size//5), (cx+size//4, ty), col, 10, cv2.LINE_AA)
        cv2.circle(frame, (int((ix + cx+size//4)/2), ty), 10, WHITE, -1)

    elif gesture == "SMILE":
        # Face outline
        cv2.circle(frame, (cx, cy), size//2, col, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), size//2, WHITE, 2, cv2.LINE_AA)
        # Two eyes
        cv2.circle(frame, (cx - size//5, cy - size//8), size//12, (20, 20, 30), -1, cv2.LINE_AA)
        cv2.circle(frame, (cx + size//5, cy - size//8), size//12, (20, 20, 30), -1, cv2.LINE_AA)
        # Big smiling curve
        cv2.ellipse(frame, (cx, cy + size//12), (size//4, size//5), 0, 20, 160, (20, 20, 30), 5, cv2.LINE_AA)

    elif gesture == "MOUTH_OPEN":
        # Face outline
        cv2.circle(frame, (cx, cy), size//2, col, -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), size//2, WHITE, 2, cv2.LINE_AA)
        # Two eyes
        cv2.circle(frame, (cx - size//5, cy - size//7), size//12, (20, 20, 30), -1, cv2.LINE_AA)
        cv2.circle(frame, (cx + size//5, cy - size//7), size//12, (20, 20, 30), -1, cv2.LINE_AA)
        # Wide open mouth
        cv2.ellipse(frame, (cx, cy + size//6), (size//6, size//4), 0, 0, 360, (20, 20, 30), -1, cv2.LINE_AA)

    elif gesture == "HEAD_TILT":
        # Tilted face outline
        cv2.ellipse(frame, (cx, cy), (size//2, size//2), 25, 0, 360, col, -1, cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy), (size//2, size//2), 25, 0, 360, WHITE, 2, cv2.LINE_AA)
        # Tilted eyes
        cv2.circle(frame, (cx - size//5, cy - size//6), size//12, (20, 20, 30), -1, cv2.LINE_AA)
        cv2.circle(frame, (cx + size//6, cy - size//10), size//12, (20, 20, 30), -1, cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + size//7), (size//4, size//6), 25, 0, 180, (20, 20, 30), 4, cv2.LINE_AA)

    cv2.rectangle(frame, (cx-size//2-4, cy-size//2-4), (cx+size//2+4, cy+size//2+4), col, 2, cv2.LINE_AA)


def run(pipe, max_time: float = 60.0) -> dict:
    from engine.gesture_ml import HandAnalyser
    analyser_r = HandAnalyser()
    analyser_l = HandAnalyser()

    score = 0
    correct = 0
    wrong   = 0
    combo   = 0
    max_combo = 0
    level   = 1.0

    target_gesture  = random.choice(CHALLENGE_GESTURES)
    hold_required   = 0.8   # seconds to hold gesture
    hold_start      = None
    reaction_start  = time.perf_counter()
    time_per_gesture = 4.0
    gesture_timer   = time_per_gesture

    t_start = time.perf_counter()

    # Countdown
    for countdown in [3, 2, 1]:
        fd = pipe.read()
        if fd.frame is None: continue
        frame = fd.frame.copy()
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0,0), (w,h), (0,0,0), -1)
        put_text(frame, "GESTURE BATTLE", (w//2-250, h//2-80), 2.0, ACCENT, 4)
        put_text(frame, "Match the gesture shown on screen!", (w//2-300, h//2), 0.75, WHITE, 1)
        put_text(frame, "Hold it for 0.8s to score", (w//2-240, h//2+45), 0.75, GOLD, 1)
        put_text(frame, str(countdown), (w//2-40, h//2+130), 3.0, GREEN, 5)
        cv2.imshow("MOVA — Gesture Battle", frame)
        cv2.waitKey(1000)

    cv2.namedWindow("MOVA — Gesture Battle", cv2.WINDOW_NORMAL)

    while True:
        fd = pipe.read()
        if fd.frame is None: break

        frame = fd.frame.copy()
        h, w  = frame.shape[:2]
        now   = time.perf_counter()
        elapsed   = now - t_start
        time_left = max(0.0, max_time - elapsed)
        dt = fd.dt

        gesture_timer -= dt
        level = 1.0 + score / 600.0
        time_per_gesture = max(2.0, 4.0 - level * 0.2)

        # ── Detect user gesture ───────────────────────────────
        detected_gesture = "NONE"
        best_conf = 0.0

        is_face_challenge = target_gesture in ["SMILE", "MOUTH_OPEN", "HEAD_TILT"]
        if is_face_challenge:
            if fd.face.detected:
                if target_gesture == "SMILE" and (fd.face.is_smiling or fd.face.gesture == "SMILE"):
                    detected_gesture = "SMILE"
                    best_conf = max(0.85, fd.face.smile_score)
                elif target_gesture == "MOUTH_OPEN" and (fd.face.mouth_open or fd.face.gesture == "MOUTH_OPEN"):
                    detected_gesture = "MOUTH_OPEN"
                    best_conf = max(0.85, fd.face.mouth_score)
                elif target_gesture == "HEAD_TILT" and (abs(fd.face.head_roll) > 10.0 or "TILT" in fd.face.gesture):
                    detected_gesture = "HEAD_TILT"
                    best_conf = 0.92
                else:
                    detected_gesture = fd.face.gesture
        else:
            for hand, analyser in [(fd.right_hand, analyser_r), (fd.left_hand, analyser_l)]:
                if not hand.detected: continue
                g, c, _ = analyser.analyse(hand.landmarks, hand.label)
                hand.gesture = g
                if c > best_conf:
                    best_conf = c
                    detected_gesture = g

        # ── Hold logic ────────────────────────────────────────
        matched = (detected_gesture == target_gesture)
        if matched:
            if hold_start is None:
                hold_start = now
            hold_held = now - hold_start
        else:
            hold_start = None
            hold_held = 0.0

        # ── Score on sustained match ──────────────────────────
        if hold_held >= hold_required:
            reaction_time = now - reaction_start
            speed_bonus = max(1, int(3.0 / max(0.5, reaction_time)))
            combo += 1
            max_combo = max(max_combo, combo)
            pts = (100 * speed_bonus * combo)
            score += pts
            correct += 1
            # Flash green
            gf = frame.copy()
            gf[:] = (0, 60, 0)
            cv2.addWeighted(gf, 0.3, frame, 0.7, 0, frame)
            put_text(frame, f"+{pts} CORRECT!", (w//2-200, h//2), 1.5, GREEN, 3)
            cv2.imshow("MOVA — Gesture Battle", frame)
            cv2.waitKey(400)

            # Next gesture
            target_gesture = random.choice([g for g in CHALLENGE_GESTURES if g != target_gesture])
            hold_start = None
            reaction_start = now
            gesture_timer = time_per_gesture
            hold_held = 0.0

        # ── Timeout on gesture ────────────────────────────────
        if gesture_timer <= 0:
            wrong += 1
            combo = 0
            # Flash red briefly
            rf = frame.copy()
            rf[:] = (0, 0, 60)
            cv2.addWeighted(rf, 0.3, frame, 0.7, 0, frame)
            put_text(frame, "TOO SLOW!", (w//2-170, h//2), 1.5, RED, 3)
            cv2.imshow("MOVA — Gesture Battle", frame)
            cv2.waitKey(300)
            target_gesture = random.choice(CHALLENGE_GESTURES)
            hold_start = None
            reaction_start = now
            gesture_timer = time_per_gesture

        # ── Draw target gesture diagram ───────────────────────
        tgt_col = COLORS.get(target_gesture, WHITE)

        # Big panel on left
        cv2.rectangle(frame, (20, 90), (320, 400), (15, 15, 25), -1)
        cv2.rectangle(frame, (20, 90), (320, 400), tgt_col, 2, cv2.LINE_AA)
        put_text(frame, "MATCH THIS:", (30, 125), 0.65, GOLD, 1)
        put_text(frame, target_gesture, (30, 160), 0.9, tgt_col, 2)
        _draw_gesture_diagram(frame, target_gesture, 170, 270, size=90)
        desc = GESTURE_DESC.get(target_gesture, "")
        # Wrap description
        words = desc.split()
        line = ""
        dy = 370
        for word in words:
            if len(line + word) > 22:
                put_text(frame, line, (30, dy), 0.5, (180,180,180), 1)
                dy += 22; line = word + " "
            else:
                line += word + " "
        if line:
            put_text(frame, line, (30, dy), 0.5, (180,180,180), 1)

        # ── Timer arc around diagram ──────────────────────────
        frac = max(0.0, gesture_timer / time_per_gesture)
        angle = int(frac * 360)
        arc_col = GREEN if frac > 0.5 else (0,165,255) if frac > 0.25 else RED
        cv2.ellipse(frame, (170, 270), (80, 80), -90, 0, -angle, arc_col, 4, cv2.LINE_AA)

        # ── User gesture display ──────────────────────────────
        user_col = GREEN if matched else (120, 120, 120)
        put_text(frame, f"YOU: {detected_gesture}", (w-280, 130), 0.8, user_col, 2)
        if fd.right_hand.detected:
            put_text(frame, f"Conf: {best_conf:.2f}", (w-210, 165), 0.6, WHITE, 1)

        # Hold progress bar
        if matched and hold_held > 0:
            bar_w = int((hold_held / hold_required) * 200)
            cv2.rectangle(frame, (w-280, 190), (w-80, 210), (40,40,40), -1)
            cv2.rectangle(frame, (w-280, 190), (w-280+bar_w, 210), GREEN, -1)
            cv2.rectangle(frame, (w-280, 190), (w-80, 210), WHITE, 1)
            put_text(frame, "HOLD!", (w-280, 225), 0.6, GREEN, 1)

        # ── Draw hand skeleton ────────────────────────────────
        if fd.right_hand.detected:
            draw_hand_skeleton(frame, fd.right_hand.landmarks, ACCENT)
        if fd.left_hand.detected:
            draw_hand_skeleton(frame, fd.left_hand.landmarks, (0,200,255))

        # ── Combo display ─────────────────────────────────────
        if combo > 1:
            put_text(frame, f"✦ STREAK x{combo}", (w//2-100, 90), 1.0, GOLD, 2)

        # ── HUD ───────────────────────────────────────────────
        draw_hud_overlay(frame, score, time_left, level, detected_gesture,
                         fd.fps, fd.pose.detected, fd.right_hand.detected + fd.left_hand.detected)

        if time_left <= 0:
            for _ in range(120):
                fd2 = pipe.read()
                if fd2.frame is None: break
                ef = fd2.frame.copy()
                cv2.rectangle(ef, (0,0), (w,h), (5,5,15), -1)
                put_text(ef, "ROUND OVER", (w//2-220, h//2-120), 2.2, ACCENT, 4)
                put_text(ef, f"SCORE:  {score:,}", (w//2-150, h//2-20), 1.5, GOLD, 3)
                put_text(ef, f"CORRECT: {correct}   WRONG: {wrong}", (w//2-220, h//2+60), 1.0, WHITE, 2)
                put_text(ef, f"MAX STREAK: x{max_combo}", (w//2-180, h//2+120), 1.0, GREEN, 2)
                put_text(ef, "ESC to return to menu", (w//2-190, h//2+190), 0.7, (150,150,150), 1)
                cv2.imshow("MOVA — Gesture Battle", ef)
                if (cv2.waitKey(33) & 0xFF) == 27: break
            break

        cv2.imshow("MOVA — Gesture Battle", frame)
        if (cv2.waitKey(1) & 0xFF) == 27: break

    cv2.destroyWindow("MOVA — Gesture Battle")
    return {
        "game": "gesture_battle", "score": score,
        "correct": correct, "wrong": wrong,
        "max_combo": max_combo, "level_reached": round(level, 1),
        "duration": round(time.perf_counter() - t_start, 1),
    }
