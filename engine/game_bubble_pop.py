"""
MOVA Game: Bubble Pop
Gesture: POINT (index finger) to pop bubbles before they escape.
Difficulty: bubbles spawn faster and move quicker as score rises.
"""

import cv2
import numpy as np
import time
import random
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

from engine.draw_utils import (put_text, draw_hud_overlay, draw_hand_skeleton,
                                draw_pose_skeleton, draw_target, ACCENT, GREEN,
                                RED, CYAN, GOLD, DARK, WHITE, PURPLE, PINK)


@dataclass
class Bubble:
    x: float        # normalised [0..1]
    y: float
    r: float        # radius, normalised
    vx: float       # velocity per second
    vy: float
    color: tuple
    points: int
    alive: bool = True
    age: float = 0.0
    max_age: float = 4.0


COLORS = [ACCENT, GREEN, GOLD, PURPLE, PINK, (0, 165, 255)]


def run(pipe, max_time: float = 60.0) -> dict:
    """
    Run Bubble Pop game. Returns results dict.
    pipe: MOVAPipeline instance.
    """
    from engine.gesture_ml import HandAnalyser
    from engine.capture import FrameData

    analyser_r = HandAnalyser()
    analyser_l = HandAnalyser()

    score = 0
    pops  = 0
    misses = 0
    bubbles: List[Bubble] = []
    level  = 1.0
    combo  = 0
    max_combo = 0

    t_start = time.perf_counter()
    last_spawn = 0.0
    spawn_interval = 1.8

    # Countdown
    for countdown in [3, 2, 1]:
        fd = pipe.read()
        if fd.frame is None:
            continue
        frame = fd.frame.copy()
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 0), -1)
        put_text(frame, "BUBBLE POP", (w//2 - 200, h//2 - 80), 2.0, ACCENT, 4)
        put_text(frame, "POINT your index finger at bubbles!", (w//2 - 310, h//2), 0.75, WHITE, 1)
        put_text(frame, str(countdown), (w//2 - 40, h//2 + 100), 3.0, GREEN, 5)
        cv2.imshow("MOVA — Bubble Pop", frame)
        key = cv2.waitKey(1000) & 0xFF
        if key == 27:
            cv2.destroyWindow("MOVA — Bubble Pop")
            return {"score": score, "pops": pops, "game": "bubble_pop"}

    cv2.namedWindow("MOVA — Bubble Pop", cv2.WINDOW_NORMAL)

    while True:
        fd = pipe.read()
        if fd.frame is None:
            break

        frame  = fd.frame.copy()
        h, w   = frame.shape[:2]
        now    = time.perf_counter()
        elapsed = now - t_start
        time_left = max(0.0, max_time - elapsed)

        dt = fd.dt

        # ── Level scaling ─────────────────────────────────────
        level = 1.0 + score / 500.0
        spawn_interval = max(0.5, 1.8 - level * 0.15)

        # ── Spawn bubbles ─────────────────────────────────────
        if now - last_spawn > spawn_interval:
            speed = 0.08 + level * 0.03
            r = random.uniform(0.04, 0.08) / level**0.3
            bub = Bubble(
                x = random.uniform(r, 1.0 - r),
                y = 1.05,
                r = r,
                vx = random.uniform(-0.05, 0.05),
                vy = -speed,
                color = random.choice(COLORS),
                points = max(10, int(100 / (r * 20))),
                max_age = 5.0 / level,
            )
            bubbles.append(bub)
            last_spawn = now

        # ── Move bubbles ──────────────────────────────────────
        for bub in bubbles:
            bub.x  += bub.vx * dt
            bub.y  += bub.vy * dt
            bub.age += dt
            # Bounce off walls
            if bub.x - bub.r < 0: bub.x = bub.r; bub.vx *= -1
            if bub.x + bub.r > 1: bub.x = 1 - bub.r; bub.vx *= -1
            # Escaped or too old
            if bub.y + bub.r < 0 or bub.age > bub.max_age:
                bub.alive = False
                misses += 1
                combo = 0

        # ── Facial Gesture Mechanics ─────────────────────────
        face_multiplier = 1
        if fd.face.detected:
            # 1. Smile Boost (2X score multiplier)
            if fd.face.is_smiling or fd.face.gesture == "SMILE":
                face_multiplier = 2
                put_text(frame, "😊 SMILE BOOST (2X COMBO ACTIVE)!", (w//2 - 240, 95), 0.75, GOLD, 2)

            # 2. Mouth Open: Sonic Shockwave pops nearby bubbles
            if fd.face.mouth_open or fd.face.gesture == "MOUTH_OPEN":
                put_text(frame, "😮 SONIC BLAST!", (w//2 - 120, 130), 0.85, CYAN, 2)
                fx, fy = fd.face.face_center
                # Sonic wave ring
                cv2.circle(frame, (int(fx * w), int(fy * h)), int(140 + 20 * np.sin(now * 15)), CYAN, 3, cv2.LINE_AA)
                for bub in bubbles:
                    if bub.alive and np.hypot(bub.x - fx, bub.y - fy) < 0.28:
                        bub.alive = False
                        pops += 1
                        pts = bub.points * combo * face_multiplier
                        score += pts
                        put_text(frame, f"+{pts} SONIC!", (int(bub.x*w), int(bub.y*h)), 0.65, CYAN, 2)

            # 3. Head Tilt wind drift
            if abs(fd.face.head_roll) > 8.0:
                tilt_wind = float(np.clip(fd.face.head_roll / 30.0, -0.08, 0.08))
                for bub in bubbles:
                    bub.vx += tilt_wind * dt

        # ── Gesture + Collision detection ─────────────────────
        popping_positions: List[Tuple[float, float]] = []

        for hand, analyser in [(fd.right_hand, analyser_r), (fd.left_hand, analyser_l)]:
            if not hand.detected:
                continue
            gesture, conf, swipe = analyser.analyse(hand.landmarks, hand.label)
            hand.gesture = gesture  # store for HUD

            if gesture in ("POINT", "PINCH", "OPEN_PALM"):
                tip = hand.landmarks[8]   # index fingertip
                popping_positions.append((float(tip[0]), float(tip[1])))

        for pp in popping_positions:
            px, py = pp
            for bub in bubbles:
                if not bub.alive:
                    continue
                dist = np.hypot(px - bub.x, py - bub.y)
                if dist < bub.r + 0.03:
                    bub.alive = False
                    combo += 1
                    max_combo = max(max_combo, combo)
                    pts = bub.points * combo * face_multiplier
                    score += pts
                    pops  += 1
                    # Pop flash
                    px_cv = int(bub.x * w)
                    py_cv = int(bub.y * h)
                    cv2.circle(frame, (px_cv, py_cv), int(bub.r * w * 2), (255,255,255), 3, cv2.LINE_AA)
                    put_text(frame, f"+{pts}", (px_cv, py_cv), 0.7, GOLD, 2)

        # ── Remove dead bubbles ───────────────────────────────
        bubbles = [b for b in bubbles if b.alive]
        if len(bubbles) > 20:
            bubbles = bubbles[-20:]

        # ── Draw bubbles ──────────────────────────────────────
        for bub in bubbles:
            age_frac = bub.age / bub.max_age
            # Pulse effect
            pulse = 1.0 + 0.07 * np.sin(now * 6 + bub.x * 10)
            draw_target(frame, bub.x, bub.y, bub.r * pulse, bub.color,
                        label=str(bub.points))
            # Age warning: darken old bubbles
            if age_frac > 0.7:
                cx, cy = int(bub.x*w), int(bub.y*h)
                cv2.circle(frame, (cx, cy), int(bub.r*w), RED, 2, cv2.LINE_AA)

        # ── Draw hand skeletons ───────────────────────────────
        if fd.right_hand.detected:
            draw_hand_skeleton(frame, fd.right_hand.landmarks, ACCENT)
        if fd.left_hand.detected:
            draw_hand_skeleton(frame, fd.left_hand.landmarks, (0, 200, 255))

        # ── Gesture labels ────────────────────────────────────
        for hand in [fd.right_hand, fd.left_hand]:
            if hand.detected:
                tip = hand.landmarks[8]
                px_t, py_t = int(tip[0]*w), int(tip[1]*h)
                cv2.circle(frame, (px_t, py_t), 14, GOLD, 2, cv2.LINE_AA)

        # ── HUD ───────────────────────────────────────────────
        rg = fd.right_hand.gesture if fd.right_hand.detected else "---"
        lg = fd.left_hand.gesture  if fd.left_hand.detected  else "---"
        gesture_str = f"R:{rg}  L:{lg}"
        draw_hud_overlay(frame, score, time_left, level, gesture_str,
                         fd.fps, fd.pose.detected, fd.right_hand.detected + fd.left_hand.detected)

        # Combo display
        if combo > 1:
            put_text(frame, f"✦ COMBO x{combo}", (w//2 - 120, 90), 1.2, GOLD, 3)

        # ── Game over ─────────────────────────────────────────
        if time_left <= 0:
            # Final screen
            for _ in range(90):
                fd2 = pipe.read()
                if fd2.frame is None:
                    break
                end_frame = fd2.frame.copy()
                cv2.rectangle(end_frame, (0,0), (w,h), (5,5,15), -1)
                put_text(end_frame, "GAME OVER", (w//2-200, h//2-120), 2.5, ACCENT, 5)
                put_text(end_frame, f"SCORE:  {score:,}", (w//2-160, h//2-30), 1.5, GOLD, 3)
                put_text(end_frame, f"POPS:   {pops}   MISSES: {misses}", (w//2-200, h//2+50), 1.0, WHITE, 2)
                put_text(end_frame, f"MAX COMBO:  x{max_combo}", (w//2-180, h//2+110), 1.0, GREEN, 2)
                put_text(end_frame, "Press ESC to return to menu", (w//2-240, h//2+180), 0.75, (150,150,150), 1)
                cv2.imshow("MOVA — Bubble Pop", end_frame)
                key = cv2.waitKey(33) & 0xFF
                if key == 27:
                    break
            break

        cv2.imshow("MOVA — Bubble Pop", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break

    cv2.destroyWindow("MOVA — Bubble Pop")
    return {
        "game": "bubble_pop", "score": score,
        "pops": pops, "misses": misses,
        "max_combo": max_combo, "level_reached": round(level, 1),
        "duration": round(time.perf_counter() - t_start, 1),
    }
