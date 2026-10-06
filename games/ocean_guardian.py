"""
GAME 08 — OCEAN GUARDIAN 🌊
Concept: Deep ocean submarine navigation. User tilts their torso & arms to pilot the submarine
through underwater currents, dodging explosive mines and collecting glowing ocean pearls.
Inputs: Body, Arms, Hands, Gaze
"""

import random
import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame

class OceanGuardianGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="ocean_guardian", game_name="Ocean Guardian 🌊", duration_sec=45.0)
        self.required_modalities = ["body", "arms", "hands"]
        self.optional_modalities = ["gaze"]
        self.movement_focus = "Torso Lateral Steering & Peripheral Reach"

        self.sub_x: float = 0.5
        self.sub_y: float = 0.75
        self.pearls: List[Dict[str, Any]] = []
        self.mines: List[Dict[str, Any]] = []
        self.pearls_rescued: int = 0
        self.spawn_timer: float = 0.0

    def on_start(self):
        self.sub_x = 0.5
        self.sub_y = 0.75
        self.pearls.clear()
        self.mines.clear()
        self.pearls_rescued = 0
        self.spawn_timer = 0.0
        self.objective_text = "Lean torso to steer submarine! Reach hands out to collect ocean pearls & avoid sea mines!"

    def on_stop(self):
        pass

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        params = self.difficulty_engine.get_game_parameters()
        speed = params["speed_multiplier"]

        self.spawn_timer += dt
        if self.spawn_timer >= params["spawn_interval"]:
            self.spawn_timer = 0.0
            # Spawn falling pearl
            self.pearls.append({"x": random.uniform(0.15, 0.85), "y": 0.05, "radius": 0.045, "vy": 0.18 * speed})
            # Spawn sea mine
            if random.random() < 0.6:
                self.mines.append({"x": random.uniform(0.15, 0.85), "y": 0.05, "radius": 0.055, "vy": 0.22 * speed})

        # Steer submarine using torso tilt and body displacement
        tilt = frame_data.pose.torso_tilt
        target_sub_x = 0.5 + (tilt / 30.0) * 0.4
        self.sub_x += (target_sub_x - self.sub_x) * dt * 4.0
        self.sub_x = float(np.clip(self.sub_x, 0.1, 0.9))

        # Check pearl collection (submarine hull or hands)
        rh = frame_data.hands.right_hand.palm_center if frame_data.hands.right_hand.detected else (0.8, 0.8)
        lh = frame_data.hands.left_hand.palm_center if frame_data.hands.left_hand.detected else (0.2, 0.8)

        for p in self.pearls[:]:
            p["y"] += p["vy"] * dt
            # Dist to sub or hands
            d_sub = np.hypot(self.sub_x - p["x"], self.sub_y - p["y"])
            d_rh = np.hypot(rh[0] - p["x"], rh[1] - p["y"])
            d_lh = np.hypot(lh[0] - p["x"], lh[1] - p["y"])

            if min(d_sub, d_rh, d_lh) < (p["radius"] + 0.06):
                self.pearls_rescued += 1
                self.record_hit(reaction_time=0.6, accuracy=0.9, points=160)
                self.pearls.remove(p)
            elif p["y"] > 1.05:
                self.pearls.remove(p)

        # Check mine collision
        for m in self.mines[:]:
            m["y"] += m["vy"] * dt
            d_mine = np.hypot(self.sub_x - m["x"], self.sub_y - m["y"])
            if d_mine < (m["radius"] + 0.06):
                self.record_miss()
                self.mines.remove(m)
            elif m["y"] > 1.05:
                self.mines.remove(m)

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Pearls (Cyan bioluminescent glow)
        for p in self.pearls:
            px, py = int(p["x"] * width), int(p["y"] * height)
            pr = int(p["radius"] * width)
            cv2.circle(frame, (px, py), pr, (255, 230, 80), -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), pr + 3, (255, 255, 200), 1, cv2.LINE_AA)

        # Draw Sea Mines (Spiked dark red orbs)
        for m in self.mines:
            mx, my = int(m["x"] * width), int(m["y"] * height)
            mr = int(m["radius"] * width)
            cv2.circle(frame, (mx, my), mr, (20, 30, 180), -1, cv2.LINE_AA)
            cv2.line(frame, (mx - mr - 4, my), (mx + mr + 4, my), (60, 60, 240), 2)
            cv2.line(frame, (mx, my - mr - 4), (mx, my + mr + 4), (60, 60, 240), 2)

        # Draw Submarine
        sx, sy = int(self.sub_x * width), int(self.sub_y * height)
        # Sub hull
        cv2.ellipse(frame, (sx, sy), (40, 20), 0, 0, 360, (0, 180, 255), -1, cv2.LINE_AA)
        cv2.ellipse(frame, (sx, sy), (40, 20), 0, 0, 360, (255, 255, 255), 2, cv2.LINE_AA)
        # Porthole
        cv2.circle(frame, (sx, sy - 2), 8, (255, 240, 0), -1, cv2.LINE_AA)
        # Propeller bubbles
        cv2.circle(frame, (sx - 48, sy), 4, (255, 255, 255), 1)

    def handle_input(self, command: str):
        pass

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"pearls_rescued": self.pearls_rescued}
