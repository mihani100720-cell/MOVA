"""
GAME 01 — GRAVITY FLIP 🪐
Concept: Controls a spatial celestial orb navigating dynamic gravity shifts (LEFT, RIGHT, NEUTRAL, DOWN).
User leans their torso / body to steer against gravitational pull, dodging hazards to reach the cosmic portal.
Inputs: Body, Arms, Head, Gaze
"""

import time
import random
import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame, GameMode

class GravityFlipGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="gravity_flip", game_name="Gravity Flip 🪐", duration_sec=45.0)
        self.required_modalities = ["body", "arms", "head"]
        self.optional_modalities = ["gaze"]
        self.movement_focus = "Directional Stability & Posture Shift"

        # Game state
        self.orb_pos = [0.5, 0.5]  # normalized [x, y]
        self.orb_vel = [0.0, 0.0]
        self.gravity_direction = "DOWN"  # "DOWN", "LEFT", "RIGHT", "UP"
        self.next_gravity_switch_timer = 6.0
        self.hazards: List[Dict[str, Any]] = []
        self.portal: Dict[str, Any] = {"pos": (0.8, 0.3), "radius": 0.08}
        self.portal_hits = 0

    def on_start(self):
        self.orb_pos = [0.5, 0.5]
        self.orb_vel = [0.0, 0.0]
        self.gravity_direction = "DOWN"
        self.next_gravity_switch_timer = 5.0
        self.hazards.clear()
        self.portal_hits = 0
        self.objective_text = "Lean your torso to steer the Orb into the glowing Portal!"
        self._spawn_hazards()
        self._respawn_portal()

    def on_stop(self):
        pass

    def _spawn_hazards(self):
        self.hazards.clear()
        count = int(3 * self.difficulty_engine.current_level)
        for _ in range(count):
            self.hazards.append({
                "pos": [random.uniform(0.2, 0.8), random.uniform(0.2, 0.8)],
                "radius": 0.05,
                "vx": random.uniform(-0.08, 0.08),
                "vy": random.uniform(-0.08, 0.08)
            })

    def _respawn_portal(self):
        self.portal["pos"] = (random.uniform(0.15, 0.85), random.uniform(0.15, 0.85))

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        # Gravity switch countdown
        self.next_gravity_switch_timer -= dt
        if self.next_gravity_switch_timer <= 0:
            dirs = ["DOWN", "LEFT", "RIGHT", "UP"]
            dirs.remove(self.gravity_direction)
            self.gravity_direction = random.choice(dirs)
            self.next_gravity_switch_timer = max(3.5, 7.0 - (self.difficulty_engine.current_level * 0.8))

        # Gravity acceleration vector
        gx, gy = 0.0, 0.0
        g_mag = 0.45 * self.difficulty_engine.current_level
        if self.gravity_direction == "DOWN": gy = g_mag
        elif self.gravity_direction == "UP": gy = -g_mag
        elif self.gravity_direction == "LEFT": gx = -g_mag
        elif self.gravity_direction == "RIGHT": gx = g_mag

        # User steering from body lean & head tilt
        tilt = frame_data.pose.torso_tilt  # degrees
        head_yaw = frame_data.face.head_yaw

        user_accel_x = (tilt / 30.0) * 1.2
        user_accel_y = (head_yaw / 40.0) * 0.6  # head turn adds vertical drift

        # Physics update with damping
        self.orb_vel[0] = (self.orb_vel[0] + (gx + user_accel_x) * dt) * 0.94
        self.orb_vel[1] = (self.orb_vel[1] + (gy + user_accel_y) * dt) * 0.94

        self.orb_pos[0] = float(np.clip(self.orb_pos[0] + self.orb_vel[0] * dt, 0.05, 0.95))
        self.orb_pos[1] = float(np.clip(self.orb_pos[1] + self.orb_vel[1] * dt, 0.05, 0.95))

        # Update hazards
        for h in self.hazards:
            h["pos"][0] += h["vx"] * dt
            h["pos"][1] += h["vy"] * dt
            if h["pos"][0] < 0.1 or h["pos"][0] > 0.9: h["vx"] *= -1
            if h["pos"][1] < 0.1 or h["pos"][1] > 0.9: h["vy"] *= -1

            # Check collision with orb
            dist_h = np.hypot(self.orb_pos[0] - h["pos"][0], self.orb_pos[1] - h["pos"][1])
            if dist_h < (0.04 + h["radius"]):
                self.record_miss()
                # Knockback orb
                self.orb_vel[0] *= -1.5
                self.orb_vel[1] *= -1.5

        # Check Portal Collision
        p_dist = np.hypot(self.orb_pos[0] - self.portal["pos"][0], self.orb_pos[1] - self.portal["pos"][1])
        if p_dist < (0.04 + self.portal["radius"]):
            self.portal_hits += 1
            self.record_hit(reaction_time=1.0, accuracy=round(1.0 - (p_dist / self.portal["radius"]), 2), points=250)
            self._respawn_portal()
            self._spawn_hazards()

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Gravity Direction Indicator Banner
        g_text = f"GRAVITY: {self.gravity_direction} ({self.next_gravity_switch_timer:.1f}s)"
        cv2.putText(frame, g_text, (width // 2 - 130, 95),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 230, 255), 2, cv2.LINE_AA)

        # Draw Portal
        px, py = int(self.portal["pos"][0] * width), int(self.portal["pos"][1] * height)
        pr = int(self.portal["radius"] * width)
        # Pulsing portal rings
        pulse = int(5 * np.sin(self.elapsed_time * 5.0))
        cv2.circle(frame, (px, py), pr + pulse, (255, 100, 200), 2, cv2.LINE_AA)
        cv2.circle(frame, (px, py), int(pr * 0.6), (200, 50, 255), -1, cv2.LINE_AA)
        cv2.putText(frame, "PORTAL", (px - 32, py + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

        # Draw Hazards (red cosmic spikes)
        for h in self.hazards:
            hx, hy = int(h["pos"][0] * width), int(h["pos"][1] * height)
            hr = int(h["radius"] * width)
            cv2.circle(frame, (hx, hy), hr, (40, 50, 240), -1, cv2.LINE_AA)
            cv2.circle(frame, (hx, hy), hr + 3, (80, 100, 255), 1, cv2.LINE_AA)

        # Draw User Orb
        ox, oy = int(self.orb_pos[0] * width), int(self.orb_pos[1] * height)
        cv2.circle(frame, (ox, oy), 22, (0, 255, 240), -1, cv2.LINE_AA)
        cv2.circle(frame, (ox, oy), 28, (180, 255, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, (ox, oy), 6, (255, 255, 255), -1)

    def handle_input(self, command: str):
        if command == "activate_portal":
            self.orb_vel[0] *= 1.5
            self.orb_vel[1] *= 1.5

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"portal_hits": self.portal_hits, "gravity_switches": int(self.elapsed_time / 5.0)}
