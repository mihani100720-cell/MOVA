"""
MOVA Game: Swipe Rush
Swipe your hand LEFT, RIGHT, UP, or DOWN to match rapidly flashing arrows.
Uses SwipeDetector for real motion velocity analysis.
"""

import cv2
import numpy as np
import time
import random
from engine.draw_utils import (put_text, draw_hand_skeleton, draw_hud_overlay,
                                ACCENT, GREEN, RED, GOLD, WHITE, PURPLE, CYAN, DARK)

DIRECTIONS = ["SWIPE_LEFT", "SWIPE_RIGHT", "SWIPE_UP", "SWIPE_DOWN"]
ARROWS = {"SWIPE_LEFT": "←", "SWIPE_RIGHT": "→", "SWIPE_UP": "↑", "SWIPE_DOWN": "↓"}
ARROW_COLORS = {
    "SWIPE_LEFT": ACCENT, "SWIPE_RIGHT": (0, 200, 255),
    "SWIPE_UP": GREEN, "SWIPE_DOWN": PURPLE
}


def _draw_arrow(frame, direction, cx, cy, size=80):
    col = ARROW_COLORS.get(direction, WHITE)
    if direction == "SWIPE_RIGHT":
        cv2.arrowedLine(frame, (cx-size, cy), (cx+size, cy), col, 12, cv2.LINE_AA, tipLength=0.35)
    elif direction == "SWIPE_LEFT":
        cv2.arrowedLine(frame, (cx+size, cy), (cx-size, cy), col, 12, cv2.LINE_AA, tipLength=0.35)
    elif direction == "SWIPE_UP":
        cv2.arrowedLine(frame, (cx, cy+size), (cx, cy-size), col, 12, cv2.LINE_AA, tipLength=0.35)
    elif direction == "SWIPE_DOWN":
        cv2.arrowedLine(frame, (cx, cy-size), (cx, cy+size), col, 12, cv2.LINE_AA, tipLength=0.35)


def run(pipe, max_time: float = 60.0) -> dict:
    from engine.gesture_ml import HandAnalyser, SwipeDetector
    analyser_r = HandAnalyser()
    analyser_l = HandAnalyser()

    score = 0; correct = 0; wrong = 0; combo = 0; max_combo = 0; level = 1.0
    target = random.choice(DIRECTIONS)
    t_per = 2.5  # seconds to complete each swipe
    gesture_timer = t_per
    t_start = time.perf_counter()

    # Countdown
    for countdown in [3, 2, 1]:
        fd = pipe.read()
        if fd.frame is None: continue
        frame = fd.frame.copy()
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0,0),(w,h),(0,0,0),-1)
        put_text(frame, "SWIPE RUSH", (w//2-200, h//2-80), 2.0, ACCENT, 4)
        put_text(frame, "Swipe your hand in the arrow direction!", (w//2-330, h//2), 0.75, WHITE, 1)
        put_text(frame, str(countdown), (w//2-40, h//2+130), 3.0, GREEN, 5)
        cv2.imshow("MOVA — Swipe Rush", frame)
        cv2.waitKey(1000)

    cv2.namedWindow("MOVA — Swipe Rush", cv2.WINDOW_NORMAL)

    while True:
        fd = pipe.read()
        if fd.frame is None: break
        frame = fd.frame.copy()
        h, w  = frame.shape[:2]
        now   = time.perf_counter()
        elapsed = now - t_start
        time_left = max(0.0, max_time - elapsed)
        dt = fd.dt
        gesture_timer -= dt
        level = 1.0 + score / 500.0
        t_per = max(1.2, 2.5 - level * 0.12)

        # Detect swipes
        swipe_detected = None
        for hand, analyser in [(fd.right_hand, analyser_r), (fd.left_hand, analyser_l)]:
            if not hand.detected: continue
            g, c, swipe = analyser.analyse(hand.landmarks, hand.label)
            hand.gesture = g
            if swipe:
                swipe_detected = swipe

        # Score swipe
        if swipe_detected:
            if swipe_detected == target:
                reaction = max(0.1, t_per - gesture_timer)
                speed_bonus = max(1, int(2.5 / reaction))
                combo += 1
                max_combo = max(max_combo, combo)
                pts = 100 * speed_bonus * combo
                score += pts; correct += 1
                # Flash
                ff = frame.copy(); ff[:] = (0,50,0)
                cv2.addWeighted(ff, 0.3, frame, 0.7, 0, frame)
                put_text(frame, f"✓ +{pts}", (w//2-100, h//2), 1.5, GREEN, 3)
                cv2.imshow("MOVA — Swipe Rush", frame); cv2.waitKey(300)
            else:
                wrong += 1; combo = 0
                ff = frame.copy(); ff[:] = (0,0,50)
                cv2.addWeighted(ff, 0.3, frame, 0.7, 0, frame)
                put_text(frame, f"✗ WRONG!", (w//2-130, h//2), 1.5, RED, 3)
                cv2.imshow("MOVA — Swipe Rush", frame); cv2.waitKey(200)
            target = random.choice([d for d in DIRECTIONS if d != target])
            gesture_timer = t_per

        if gesture_timer <= 0:
            wrong += 1; combo = 0
            target = random.choice(DIRECTIONS); gesture_timer = t_per

        # Draw
        col = ARROW_COLORS.get(target, WHITE)
        frac = max(0.0, gesture_timer / t_per)
        pulse = int(100 + 60 * np.sin(now * 8))
        cv2.circle(frame, (w//2, h//2), 120 + pulse//10, (*col, 50), 3, cv2.LINE_AA)
        _draw_arrow(frame, target, w//2, h//2)
        put_text(frame, target.replace("_"," "), (w//2-120, h//2+150), 1.0, col, 2)
        # Timer ring
        angle = int(frac * 360)
        tc = GREEN if frac > 0.5 else (0,165,255) if frac>0.25 else RED
        cv2.ellipse(frame, (w//2,h//2), (140,140), -90, 0, -angle, tc, 4, cv2.LINE_AA)

        if fd.right_hand.detected: draw_hand_skeleton(frame, fd.right_hand.landmarks, ACCENT)
        if fd.left_hand.detected:  draw_hand_skeleton(frame, fd.left_hand.landmarks, (0,200,255))

        if combo > 1:
            put_text(frame, f"✦ COMBO x{combo}", (w//2-110,90), 1.0, GOLD, 2)

        rg = fd.right_hand.gesture if fd.right_hand.detected else "---"
        draw_hud_overlay(frame, score, time_left, level, rg, fd.fps,
                         fd.pose.detected, fd.right_hand.detected+fd.left_hand.detected)

        if time_left <= 0:
            for _ in range(90):
                fd2 = pipe.read()
                if fd2.frame is None: break
                ef = fd2.frame.copy()
                cv2.rectangle(ef,(0,0),(w,h),(5,5,15),-1)
                put_text(ef, "ROUND OVER",(w//2-220,h//2-120),2.2,ACCENT,4)
                put_text(ef, f"SCORE: {score:,}",(w//2-150,h//2-20),1.5,GOLD,3)
                put_text(ef, f"HIT: {correct}  MISS: {wrong}",(w//2-180,h//2+60),1.0,WHITE,2)
                put_text(ef, f"MAX COMBO: x{max_combo}",(w//2-170,h//2+120),1.0,GREEN,2)
                put_text(ef, "ESC to menu",(w//2-120,h//2+190),0.7,(150,150,150),1)
                cv2.imshow("MOVA — Swipe Rush", ef)
                if (cv2.waitKey(33)&0xFF)==27: break
            break

        cv2.imshow("MOVA — Swipe Rush", frame)
        if (cv2.waitKey(1)&0xFF)==27: break

    cv2.destroyWindow("MOVA — Swipe Rush")
    return {"game":"swipe_rush","score":score,"correct":correct,"wrong":wrong,
            "max_combo":max_combo,"level_reached":round(level,1),
            "duration":round(time.perf_counter()-t_start,1)}
