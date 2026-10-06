"""
GAME 02 — DRAGON DASH 🐉
Concept: Fantasy obstacle evasion game. Incoming dragon fire hazards advance down the screen.
User dodges with body/torso displacement while reaching with hands to collect dragon energy spheres.
Inputs: Eyes, Hands, Arms, Body
"""

import random
import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame

class DragonDashGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="dragon_dash", game_name="Dragon Dash 🐉", duration_sec=45.0)
        self.required_modalities = ["eyes", "hands", "arms", "body"]
        self.optional_modalities = ["voice"]
        self.movement_focus = "Visual Reaction & Whole-Body Coordination"

        self.obstacles: List[Dict[str, Any]] = []
        self.energy_orbs: List[Dict[str, Any]] = []
        self.orbs_collected: int = 0
        self.dodges_completed: int = 0
        self.spawn_timer: float = 0.0

    def on_start(self):
        self.obstacles.clear()
        self.energy_orbs.clear()
        self.orbs_collected = 0
        self.dodges_completed = 0
        self.spawn_timer = 0.0
        self.objective_text = "Dodge dragon fire with your body, reach with hands to collect Energy Orbs!"

    def on_stop(self):
        pass

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        params = self.difficulty_engine.get_game_parameters()
        speed_mult = params["speed_multiplier"]

        self.spawn_timer += dt
        if self.spawn_timer >= params["spawn_interval"]:
            self.spawn_timer = 0.0
            # Spawn incoming dragon fire obstacle
            self.obstacles.append({
                "x": random.uniform(0.15, 0.85),
                "y": 0.05,
                "radius": 0.06,
                "vy": 0.28 * speed_mult,
                "dodged": False
            })
            # Spawn collectible energy orb
            self.energy_orbs.append({
                "x": random.uniform(0.15, 0.85),
                "y": 0.05,
                "radius": 0.05,
                "vy": 0.20 * speed_mult
            })

        body_x, body_y = frame_data.pose.body_center if frame_data.pose.detected else (0.5, 0.6)
        r_hand = frame_data.hands.right_hand.palm_center if frame_data.hands.right_hand.detected else (0.7, 0.7)
        l_hand = frame_data.hands.left_hand.palm_center if frame_data.hands.left_hand.detected else (0.3, 0.7)

        # Update obstacles
        for obs in self.obstacles[:]:
            obs["y"] += obs["vy"] * dt

            # Check collision with body center
            dist_body = np.hypot(body_x - obs["x"], body_y - obs["y"])
            if dist_body < (obs["radius"] + 0.07):
                self.record_miss()
                self.obstacles.remove(obs)
                continue

            # Check successful dodge (passed user y level safely)
            if not obs["dodged"] and obs["y"] > (body_y + 0.05):
                obs["dodged"] = True
                self.dodges_completed += 1
                self.record_hit(reaction_time=0.6, accuracy=1.0, points=80)

            if obs["y"] > 1.05:
                if obs in self.obstacles:
                    self.obstacles.remove(obs)

        # Update energy orbs (collect with either hand)
        for orb in self.energy_orbs[:]:
            orb["y"] += orb["vy"] * dt

            dist_r = np.hypot(r_hand[0] - orb["x"], r_hand[1] - orb["y"])
            dist_l = np.hypot(l_hand[0] - orb["x"], l_hand[1] - orb["y"])

            if dist_r < (orb["radius"] + 0.06) or dist_l < (orb["radius"] + 0.06):
                self.orbs_collected += 1
                hit_dist = min(dist_r, dist_l)
                acc = max(0.5, 1.0 - (hit_dist / 0.06))
                self.record_hit(reaction_time=0.5, accuracy=acc, points=150)
                self.energy_orbs.remove(orb)
            elif orb["y"] > 1.05:
                self.energy_orbs.remove(orb)

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Obstacles (Dragon Fire Meteors)
        for obs in self.obstacles:
            ox, oy = int(obs["x"] * width), int(obs["y"] * height)
            r = int(obs["radius"] * width)
            cv2.circle(frame, (ox, oy), r, (20, 70, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, (ox, oy), r + 4, (0, 160, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "FIRE", (ox - 18, oy + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Draw Collectible Energy Orbs (Cyan / Gold)
        for orb in self.energy_orbs:
            ex, ey = int(orb["x"] * width), int(orb["y"] * height)
            r = int(orb["radius"] * width)
            cv2.circle(frame, (ex, ey), r, (240, 220, 0), -1, cv2.LINE_AA)
            cv2.circle(frame, (ex, ey), r + 3, (255, 255, 200), 2, cv2.LINE_AA)

    def handle_input(self, command: str):
        pass

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"orbs_collected": self.orbs_collected, "dodges_completed": self.dodges_completed}
