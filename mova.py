"""
MOVA — Multimodal Spatial Gaming & Movement Intelligence Platform
Pure OpenCV + MediaPipe Application Entry Point.
Run:  python mova.py

Controls:
  ↑ / ↓  or W / S  — navigate menu
  ENTER  or SPACE   — select game
  D                 — toggle diagnostic overlay
  ESC               — quit
"""

import cv2
import numpy as np
import time
import sys
import os
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from engine.capture    import MOVAPipeline, FrameData
from engine.gesture_ml import HandAnalyser
from engine.draw_utils import (
    put_text, draw_hand_skeleton, draw_pose_skeleton,
    draw_rounded_rect, draw_menu_bg,
    ACCENT, GREEN, RED, GOLD, WHITE, DARK, PURPLE, PINK, CYAN, BLACK
)

# ── Game registry ─────────────────────────────────────────────────────────────
# ── Game registry ─────────────────────────────────────────────────────────────
GAMES: List[Dict[str, Any]] = [
    {
        "id":       "bubble_pop",
        "title":    "Bubble Pop",
        "icon":     "●",
        "category": "MULTIMODAL POP",
        "desc":     "POINT/PINCH to pop bubbles! SMILE for 2X boost, OPEN MOUTH for Sonic Blast!",
        "controls": "HAND: Point / Pinch • FACE: Smile (2X Combo) & Mouth Open (Sonic Blast)",
        "color":    ACCENT,
        "module":   "engine.game_bubble_pop",
    },
    {
        "id":       "gesture_battle",
        "title":    "Gesture Battle",
        "icon":     "✊",
        "category": "HAND + FACE ML",
        "desc":     "Match Hand Gestures (Fist, Palm, Point...) AND Face Gestures (Smile, Open Mouth, Tilt)!",
        "controls": "HAND: Fist, Palm, Point, Peace, Thumb, Pinch • FACE: Smile, Open Mouth, Head Tilt",
        "color":    PURPLE,
        "module":   "engine.game_gesture_battle",
    },
    {
        "id":       "torso_dodge",
        "title":    "Torso Dodge",
        "icon":     "◈",
        "category": "BODY + FACE",
        "desc":     "Lean torso or TILT HEAD to steer! SMILE to activate invulnerability shield!",
        "controls": "BODY: Torso Lean / HEAD TILT • FACE: Smile Shield • HAND: Open Palm collect",
        "color":    GREEN,
        "module":   "engine.game_torso_dodge",
    },
    {
        "id":       "swipe_rush",
        "title":    "Swipe Rush",
        "icon":     "→",
        "category": "SWIPE VELOCITY",
        "desc":     "Swipe your hand LEFT / RIGHT / UP / DOWN to match rapid directional arrows!",
        "controls": "Directional hand swipe (velocity-based ML detection)",
        "color":    GOLD,
        "module":   "engine.game_swipe_rush",
    },
]


# ── Diagnostics overlay ───────────────────────────────────────────────────────
def draw_diagnostics(frame: np.ndarray, fd: FrameData,
                     rg: str, rc: float, lg: str, lc: float) -> None:
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (w-300, 0), (w, 280), (8, 8, 16), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    y = 22
    def row(label, value, color=WHITE):
        nonlocal y
        put_text(frame, f"{label}: {value}", (w-295, y), 0.52, color, 1)
        y += 22

    put_text(frame, "── DIAGNOSTICS ──", (w-290, y-4), 0.5, ACCENT, 1); y += 22
    row("FPS",       f"{fd.fps:.1f}", GREEN if fd.fps > 20 else RED)
    row("Lighting",  f"{'OK' if fd.lighting_ok else 'LOW'} ({fd.lighting_score:.2f})",
                     GREEN if fd.lighting_ok else (0,165,255))
    row("Pose",      f"{'✓' if fd.pose.detected else '✗'}  lean={fd.pose.torso_lean:+.2f}",
                     GREEN if fd.pose.detected else RED)
    row("R.Hand",    f"{'✓' if fd.right_hand.detected else '✗'}  {rg}({rc:.2f})",
                     ACCENT if fd.right_hand.detected else (100,100,100))
    row("L.Hand",    f"{'✓' if fd.left_hand.detected else '✗'}  {lg}({lc:.2f})",
                     (0,200,255) if fd.left_hand.detected else (100,100,100))
    face_str = f"{fd.face.gesture} (tilt={fd.face.head_roll:+.0f}°)" if fd.face.detected else "OFF"
    row("Face",      f"{'✓' if fd.face.detected else '✗'}  {face_str}",
                     GOLD if fd.face.detected else (100,100,100))

    # Skeletons
    if fd.right_hand.detected:
        draw_hand_skeleton(frame, fd.right_hand.landmarks, ACCENT)
    if fd.left_hand.detected:
        draw_hand_skeleton(frame, fd.left_hand.landmarks, (0, 200, 255))
    if fd.pose.detected:
        draw_pose_skeleton(frame, fd.pose.landmarks, GREEN)


# ── Menu rendering ────────────────────────────────────────────────────────────
def draw_menu(frame: np.ndarray, selected: int, fd: FrameData,
              diag: bool, analyser_r: HandAnalyser, analyser_l: HandAnalyser) -> None:
    h, w = frame.shape[:2]

    # Dark overlay on camera feed
    overlay = frame.copy()
    overlay[:] = (8, 8, 16)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    # ── MOVA Header ───────────────────────────────────────────
    # Gradient bar at top
    for px in range(w):
        t = px / w
        b = int(121 * (1-t) + 0 * t)
        gg = int(40  * (1-t) + 229 * t)
        r  = int(202 * (1-t) + 255 * t)
        cv2.line(frame, (px, 0), (px, 6), (b, gg, r), 1)

    put_text(frame, "M O V A", (w//2 - 230, 72), 2.8, ACCENT, 5, shadow=True)
    put_text(frame, "MULTIMODAL SPATIAL GAMING  ✦  MOVE. PLAY. IMPROVE.",
             (w//2 - 365, 110), 0.65, (160, 160, 180), 1, shadow=False)

    # ── Tracking status strip ─────────────────────────────────
    face_label = f"◉ FACE: {fd.face.gesture}" if fd.face.detected else "◉ FACE"
    badges = [
        ("◉ POSE",   fd.pose.detected,         GREEN,       90),
        ("◉ R.HAND", fd.right_hand.detected,   ACCENT,      240),
        ("◉ L.HAND", fd.left_hand.detected,    (0,200,255), 390),
        (face_label, fd.face.detected,         GOLD,        540),
    ]
    for label, ok, col, bx in badges:
        c = col if ok else (60, 60, 60)
        bw = 145 if "FACE" not in label else 170
        cv2.rectangle(frame, (bx, 125), (bx+bw, 150), (20,20,30), -1)
        cv2.rectangle(frame, (bx, 125), (bx+bw, 150), c, 1, cv2.LINE_AA)
        put_text(frame, label, (bx+8, 143), 0.50, c, 1, shadow=False)

    # FPS
    fps_c = GREEN if fd.fps > 20 else RED
    put_text(frame, f"FPS {fd.fps:.0f}", (w-110, 143), 0.52, fps_c, 1)

    # ── Game cards ────────────────────────────────────────────
    card_x0 = 60
    card_y0 = 175
    card_h  = 105
    card_w  = w - 120
    gap     = 14

    for i, game in enumerate(GAMES):
        cy = card_y0 + i * (card_h + gap)
        is_sel = (i == selected)
        bg_alpha = 0.85 if is_sel else 0.4
        bg_col   = game["color"] if is_sel else (25, 25, 38)

        # Card background
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (card_x0, cy), (card_x0+card_w, cy+card_h), bg_col, -1)
        cv2.addWeighted(overlay2, 0.25 if is_sel else 0.15, frame, 1.0 - (0.25 if is_sel else 0.15), 0, frame)

        border_col = game["color"] if is_sel else (50, 50, 70)
        bw = 3 if is_sel else 1
        cv2.rectangle(frame, (card_x0, cy), (card_x0+card_w, cy+card_h), border_col, bw, cv2.LINE_AA)

        if is_sel:
            # Glow bar on left edge
            cv2.rectangle(frame, (card_x0, cy), (card_x0+5, cy+card_h), game["color"], -1)

        # Icon + Title
        icon_col = game["color"] if is_sel else (120, 120, 130)
        put_text(frame, game["icon"], (card_x0+20, cy+38), 1.0, icon_col, 2)
        title_col = WHITE if is_sel else (160, 160, 180)
        put_text(frame, game["title"].upper(), (card_x0+70, cy+38), 0.85, title_col, 2)

        # Category badge
        cat_col = game["color"]
        put_text(frame, f"[ {game['category']} ]", (card_x0+70, cy+65), 0.5, cat_col, 1)

        # Description
        put_text(frame, game["desc"], (card_x0+70, cy+90), 0.5, (150,150,170), 1)

    # ── Bottom controls ───────────────────────────────────────
    controls_y = card_y0 + len(GAMES) * (card_h + gap) + 20
    controls = [("↑↓ / W S", "Navigate"), ("ENTER / SPACE", "Play Game"),
                ("D", "Diagnostics"), ("ESC", "Quit")]
    cx_offset = 80
    for key, action in controls:
        cv2.rectangle(frame, (cx_offset, controls_y), (cx_offset+130, controls_y+28), (30,30,45), -1)
        cv2.rectangle(frame, (cx_offset, controls_y), (cx_offset+130, controls_y+28), (80,80,100), 1)
        put_text(frame, f"{key}  {action}", (cx_offset+6, controls_y+20), 0.48, (180,180,200), 1)
        cx_offset += 150

    # Diagnostic hint
    put_text(frame, "D = Diagnostics" if not diag else "D = Hide Diagnostics",
             (w-250, controls_y+22), 0.48, (100,100,120), 1)

    # ── Selected game controls footer ─────────────────────────
    sel_game = GAMES[selected]
    put_text(frame, f"Controls:  {sel_game['controls']}",
             (card_x0+6, controls_y + 50), 0.55, sel_game["color"], 1)


# ── Session result display ────────────────────────────────────────────────────
def show_results(pipe: MOVAPipeline, results: dict, game_def: dict) -> None:
    t = time.perf_counter()
    while time.perf_counter() - t < 8.0:
        fd = pipe.read()
        if fd.frame is None:
            break
        frame = fd.frame.copy()
        h, w  = frame.shape[:2]

        ov = frame.copy(); ov[:] = (5, 5, 12)
        cv2.addWeighted(ov, 0.75, frame, 0.25, 0, frame)

        col = game_def["color"]
        put_text(frame, "GAME OVER", (w//2-220, h//2-180), 2.5, col, 5)
        put_text(frame, game_def["title"].upper(), (w//2-200, h//2-120), 1.2, WHITE, 2)

        y = h//2 - 60
        for k, v in results.items():
            if k in ("game", "html_report", "report_id"): continue
            label = k.upper().replace("_", " ")
            put_text(frame, f"{label}:  {v}", (w//2 - 220, y), 0.80, (200,200,220), 2)
            y += 40

        if "report_id" in results:
            put_text(frame, f"REPORT SAVED: {results['report_id']}", (w//2-220, y+10), 0.68, GREEN, 2)
            put_text(frame, "Web Report: http://localhost:8501 (Reports View)", (w//2-220, y+40), 0.65, CYAN, 1)

        put_text(frame, "Returning to menu in a moment (or press ESC)...",
                 (w//2-270, h//2+220), 0.65, (100,100,120), 1)

        cv2.imshow("MOVA", frame)
        key = cv2.waitKey(33) & 0xFF
        if key == 27 or key == 13:
            break


# ── Main application loop ─────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  MOVA — Multimodal Spatial Gaming Platform")
    print("  Powered by OpenCV + MediaPipe Tasks API")
    print("=" * 60)
    print("Opening camera...")

    try:
        pipe = MOVAPipeline(camera_index=0, width=1280, height=720)
    except Exception as e:
        print(f"[ERROR] Failed to open camera: {e}")
        sys.exit(1)

    if pipe.cap is None or not pipe.cap.isOpened():
        print("[ERROR] Camera could not be opened. Exiting.")
        sys.exit(1)

    analyser_r = HandAnalyser()
    analyser_l = HandAnalyser()

    selected  = 0
    diag_mode = False
    rg = lg = "NONE"
    rc = lc = 0.0

    cv2.namedWindow("MOVA", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("MOVA", 1280, 720)
    print("\nMOVA is running — press ESC in the window to quit.\n")

    while True:
        fd = pipe.read()
        if fd.frame is None:
            break
        frame = fd.frame.copy()

        # Gesture recognition for menu navigation
        for hand, analyser in [(fd.right_hand, analyser_r), (fd.left_hand, analyser_l)]:
            if not hand.detected: continue
            g, c, swipe = analyser.analyse(hand.landmarks, hand.label)
            hand.gesture = g
            if hand.label == "Right":
                rg, rc = g, c
            else:
                lg, lc = g, c

        # Draw menu
        draw_menu(frame, selected, fd, diag_mode, analyser_r, analyser_l)

        if diag_mode:
            draw_diagnostics(frame, fd, rg, rc, lg, lc)

        cv2.imshow("MOVA", frame)
        key = cv2.waitKey(1) & 0xFF

        # ── Keyboard navigation ────────────────────────────────
        if key == 27:   # ESC
            break
        elif key in (82, ord('w'), ord('W')):   # Up
            selected = (selected - 1) % len(GAMES)
        elif key in (84, ord('s'), ord('S')):   # Down
            selected = (selected + 1) % len(GAMES)
        elif key in (13, 32):   # ENTER or SPACE — launch game
            game_def = GAMES[selected]
            cv2.destroyWindow("MOVA")
            try:
                import importlib
                mod = importlib.import_module(game_def["module"])
                results = mod.run(pipe, max_time=60.0)
                print(f"\n[RESULT] {game_def['title']}: {results}")
                # Automated report generation & SQLite registration
                try:
                    from reports.report_recorder import record_game_session
                    rep = record_game_session(results, game_def)
                    results["report_id"] = rep["session_id"]
                    results["html_report"] = rep["html_path"]
                    print(f"Generated Session Report: {rep['session_id']}")
                    print(f"HTML File: {rep['html_path']}")
                except Exception as r_err:
                    print(f"[REPORTS] Report generation notice: {r_err}")
                show_results(pipe, results, game_def)
            except Exception as e:
                import traceback
                print(f"[ERROR] Game crashed: {e}")
                traceback.print_exc()
            cv2.namedWindow("MOVA", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("MOVA", 1280, 720)
        elif key in (ord('d'), ord('D')):
            diag_mode = not diag_mode

    print("\nMOVA session ended. Thanks for playing!")
    pipe.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
