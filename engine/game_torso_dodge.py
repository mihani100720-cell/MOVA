"""
MOVA Game: Torso Dodge
Lean your body LEFT/RIGHT to dodge incoming obstacles.
Collect green orbs with OPEN_PALM to score bonus points.
Uses pose torso lean for steering + hand gesture for collecting.
"""

import cv2
import numpy as np
import time
import random
from typing import List
from dataclasses import dataclass, field

from engine.draw_utils import (put_text, draw_hud_overlay, draw_hand_skeleton,
                                draw_pose_skeleton, draw_target,
                                ACCENT, GREEN, RED, CYAN, GOLD, WHITE, DARK, PURPLE, PINK)


@dataclass
class Obstacle:
    x: float        # normalised
    y: float
    w: float        # width
    h: float        # height
    speed: float
    color: tuple
    alive: bool = True


@dataclass
class Orb:
    x: float
    y: float
    r: float = 0.035
    speed: float = 0.18
    collected: bool = False
    color: tuple = field(default_factory=lambda: GREEN)


def run(pipe, max_time: float = 60.0) -> dict:
    from engine.gesture_ml import HandAnalyser
    analyser_r = HandAnalyser()
    analyser_l = HandAnalyser()

    score = 0
    dodged = 0
    hits = 0
    orbs_collected = 0
    level = 1.0
    combo = 0
    hp = 5  # hit points

    obstacles: List[Obstacle] = []
    orbs: List[Orb] = []

    t_start = time.perf_counter()
    last_obs = 0.0
    last_orb = 0.0
    obs_interval = 2.0
    orb_interval = 3.0

    # Player representation (torso position)
    player_x = 0.5
    player_y = 0.75
    player_w = 0.08
    player_h = 0.12

    OBSTACLE_COLORS = [RED, (0, 80, 200), PURPLE, PINK]

    # Countdown
    for countdown in [3, 2, 1]:
        fd = pipe.read()
        if fd.frame is None: continue
        frame = fd.frame.copy()
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0,0), (w,h), (0,0,0), -1)
        put_text(frame, "TORSO DODGE", (w//2-230, h//2-80), 2.0, ACCENT, 4)
        put_text(frame, "LEAN LEFT / RIGHT to dodge red obstacles", (w//2-330, h//2), 0.75, WHITE, 1)
        put_text(frame, "OPEN PALM to collect green orbs", (w//2-270, h//2+45), 0.75, GREEN, 1)
        put_text(frame, str(countdown), (w//2-40, h//2+130), 3.0, GREEN, 5)
        cv2.imshow("MOVA — Torso Dodge", frame)
        cv2.waitKey(1000)

    cv2.namedWindow("MOVA — Torso Dodge", cv2.WINDOW_NORMAL)

    while True:
        fd = pipe.read()
        if fd.frame is None: break

        frame = fd.frame.copy()
        h, w  = frame.shape[:2]
        now   = time.perf_counter()
        elapsed = now - t_start
        time_left = max(0.0, max_time - elapsed)
        dt = fd.dt

        level = 1.0 + score / 400.0
        obs_interval = max(0.6, 2.0 - level * 0.12)
        obs_speed = 0.20 + level * 0.05

        # ── Player steering from torso lean or head tilt ─────
        if fd.pose.detected:
            lean = fd.pose.torso_lean  # -1 (left) to +1 (right)
            target_x = 0.5 + lean * 0.45
            player_x += (target_x - player_x) * 0.25  # smooth follow
        elif fd.face.detected and abs(fd.face.head_roll) > 5.0:
            tilt_val = float(np.clip(fd.face.head_roll / 25.0, -1.0, 1.0))
            target_x = 0.5 + tilt_val * 0.45
            player_x += (target_x - player_x) * 0.25
        else:
            # Fall back to right hand x position
            if fd.right_hand.detected:
                palm_x = float(fd.right_hand.landmarks[0, 0])
                player_x += (palm_x - player_x) * 0.25
        player_x = float(np.clip(player_x, player_w/2, 1.0-player_w/2))

        # ── Face Gesture: SMILE Shield ─────────────────────────
        shield_active = False
        if fd.face.detected and (fd.face.is_smiling or fd.face.gesture == "SMILE"):
            shield_active = True
            put_text(frame, "🛡️ SMILE SHIELD ACTIVE!", (w//2 - 170, 95), 0.75, (0, 230, 255), 2)

        # ── Gesture: collect orbs with OPEN_PALM ──────────────
        collecting = False
        for hand, analyser in [(fd.right_hand, analyser_r), (fd.left_hand, analyser_l)]:
            if not hand.detected: continue
            gesture, conf, _ = analyser.analyse(hand.landmarks, hand.label)
            hand.gesture = gesture
            if gesture == "OPEN_PALM":
                collecting = True

        # ── Spawn obstacles ───────────────────────────────────
        if now - last_obs > obs_interval:
            ow = random.uniform(0.12, 0.22)
            obs_x = random.uniform(ow/2, 1-ow/2)
            obstacles.append(Obstacle(
                x=obs_x, y=-0.05,
                w=ow, h=random.uniform(0.06, 0.10),
                speed=obs_speed,
                color=random.choice(OBSTACLE_COLORS)
            ))
            last_obs = now

        # ── Spawn orbs ────────────────────────────────────────
        if now - last_orb > orb_interval:
            orbs.append(Orb(x=random.uniform(0.1, 0.9), y=-0.05, speed=0.14))
            last_orb = now

        # ── Move everything ───────────────────────────────────
        for obs in obstacles:
            obs.y += obs.speed * dt
            if obs.y > 1.05:
                obs.alive = False
                dodged += 1
                combo += 1
                score += 10 * max(1, combo // 3)

        for orb in orbs:
            orb.y += orb.speed * dt

        # ── Collision: player vs obstacles ────────────────────
        for obs in obstacles:
            if not obs.alive: continue
            x_overlap = abs(player_x - obs.x) < (player_w + obs.w) / 2
            y_overlap = abs(player_y - obs.y) < (player_h + obs.h) / 2
            if x_overlap and y_overlap:
                obs.alive = False
                if shield_active:
                    score += 50
                    put_text(frame, "🛡️ DEFLECTED! +50", (int(player_x*w)-80, int(player_y*h)-40), 0.8, (0,230,255), 2)
                else:
                    hits += 1
                    hp -= 1
                    combo = 0
                    # Flash red
                    red_overlay = frame.copy()
                    red_overlay[:] = (0, 0, 120)
                    cv2.addWeighted(red_overlay, 0.35, frame, 0.65, 0, frame)

        # ── Collision: player vs orbs ─────────────────────────
        for orb in orbs:
            if orb.collected: continue
            dist = np.hypot(player_x - orb.x, player_y - orb.y)
            # Can always collect if close enough, bonus if OPEN_PALM
            if dist < 0.07:
                orb.collected = True
                orbs_collected += 1
                pts = 50 * (2 if collecting else 1)
                score += pts
                cx, cy = int(orb.x*w), int(orb.y*h)
                put_text(frame, f"+{pts}", (cx, cy-20), 0.8, GOLD, 2)

        # ── Draw obstacles ────────────────────────────────────
        for obs in [o for o in obstacles if o.alive]:
            x1 = int((obs.x - obs.w/2) * w)
            y1 = int((obs.y - obs.h/2) * h)
            x2 = int((obs.x + obs.w/2) * w)
            y2 = int((obs.y + obs.h/2) * h)
            cv2.rectangle(frame, (x1, y1), (x2, y2), obs.color, -1, cv2.LINE_AA)
            cv2.rectangle(frame, (x1, y1), (x2, y2), WHITE, 1, cv2.LINE_AA)

        # ── Draw orbs ─────────────────────────────────────────
        for orb in [o for o in orbs if not o.collected]:
            draw_target(frame, orb.x, orb.y, orb.r, GREEN, label="★")

        # ── Draw player avatar ────────────────────────────────
        px1 = int((player_x - player_w/2) * w)
        py1 = int((player_y - player_h/2) * h)
        px2 = int((player_x + player_w/2) * w)
        py2 = int((player_y + player_h/2) * h)
        player_col = GREEN if hp > 2 else (0, 165, 255) if hp == 2 else RED
        cv2.rectangle(frame, (px1, py1), (px2, py2), player_col, -1, cv2.LINE_AA)
        cv2.rectangle(frame, (px1, py1), (px2, py2), WHITE, 2, cv2.LINE_AA)
        put_text(frame, "YOU", (px1 + 4, py2 - 5), 0.45, WHITE, 1)

        # ── Draw pose skeleton ─────────────────────────────────
        if fd.pose.detected:
            draw_pose_skeleton(frame, fd.pose.landmarks, GREEN)

        # ── Draw hand skeletons ───────────────────────────────
        if fd.right_hand.detected:
            draw_hand_skeleton(frame, fd.right_hand.landmarks, ACCENT)
        if fd.left_hand.detected:
            draw_hand_skeleton(frame, fd.left_hand.landmarks, (0,200,255))

        # ── HP bar ────────────────────────────────────────────
        for i in range(5):
            col = player_col if i < hp else (60, 60, 60)
            cv2.rectangle(frame, (12 + i*30, 60), (36 + i*30, 78), col, -1)
            cv2.rectangle(frame, (12 + i*30, 60), (36 + i*30, 78), WHITE, 1)
        put_text(frame, "HP", (12, 58), 0.45, WHITE, 1)

        # ── HUD ───────────────────────────────────────────────
        rg = fd.right_hand.gesture if fd.right_hand.detected else "---"
        draw_hud_overlay(frame, score, time_left, level, rg, fd.fps,
                         fd.pose.detected, fd.right_hand.detected + fd.left_hand.detected)

        # ── Lean indicator ─────────────────────────────────────
        lean_disp = fd.pose.torso_lean if fd.pose.detected else 0.0
        cv2.arrowedLine(frame,
                        (w//2, h-55),
                        (int(w//2 + lean_disp*120), h-55),
                        ACCENT, 3, cv2.LINE_AA, tipLength=0.4)
        put_text(frame, "LEAN", (w//2 - 35, h-60), 0.45, ACCENT, 1)

        # ── Clean up ──────────────────────────────────────────
        obstacles = [o for o in obstacles if o.alive and o.y < 1.1]
        orbs      = [o for o in orbs if not o.collected and o.y < 1.1]

        # ── Game over conditions ──────────────────────────────
        if time_left <= 0 or hp <= 0:
            reason = "TIME UP!" if time_left <= 0 else "YOU CRASHED!"
            for _ in range(120):
                fd2 = pipe.read()
                if fd2.frame is None: break
                ef = fd2.frame.copy()
                cv2.rectangle(ef, (0,0), (w,h), (5,5,15), -1)
                put_text(ef, reason, (w//2-200, h//2-120), 2.2, RED if hp<=0 else ACCENT, 4)
                put_text(ef, f"SCORE:  {score:,}", (w//2-160, h//2-20), 1.5, GOLD, 3)
                put_text(ef, f"DODGES: {dodged}   HITS: {hits}   ORBS: {orbs_collected}", (w//2-260, h//2+60), 0.9, WHITE, 2)
                put_text(ef, "ESC to return to menu", (w//2-190, h//2+150), 0.7, (150,150,150), 1)
                cv2.imshow("MOVA — Torso Dodge", ef)
                if (cv2.waitKey(33) & 0xFF) == 27: break
            break

        cv2.imshow("MOVA — Torso Dodge", frame)
        if (cv2.waitKey(1) & 0xFF) == 27: break

    cv2.destroyWindow("MOVA — Torso Dodge")
    return {
        "game": "torso_dodge", "score": score,
        "dodged": dodged, "hits": hits, "orbs_collected": orbs_collected,
        "level_reached": round(level, 1),
        "duration": round(time.perf_counter() - t_start, 1),
    }
