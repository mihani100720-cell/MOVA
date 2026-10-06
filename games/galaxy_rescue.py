"""
GAME 03 — GALAXY RESCUE 🌌
Concept: Stranded cosmic creatures are marooned on highlighted exoplanets in the MOVA Zone.
User looks at the target planet (gaze fixation), reaches toward it with hand, and activates
the tractor beam to rescue the creature.
Inputs: Gaze, Hand, Arm, Body
"""

import random
import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame

class GalaxyRescueGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="galaxy_rescue", game_name="Galaxy Rescue 🌌", duration_sec=45.0)
        self.required_modalities = ["gaze", "hand", "arm", "body"]
        self.optional_modalities = ["voice"]
        self.movement_focus = "Gaze-To-Reach Coupling & Spatial Reach"

        self.planets: List[Dict[str, Any]] = []
        self.target_planet_idx: int = 0
        self.rescued_count: int = 0
        self.beam_active: bool = False
        self.beam_progress: float = 0.0
        self.target_spawn_time: float = 0.0

    def on_start(self):
        self.rescued_count = 0
        self.beam_active = False
        self.beam_progress = 0.0
        self.objective_text = "Look at highlighted Planet with your eyes, then reach and hold hand over it to rescue!"
        self._generate_planets()

    def on_stop(self):
        pass

    def _generate_planets(self):
        self.planets = [
            {"name": "Aethel", "pos": (0.25, 0.28), "color": (255, 120, 80), "radius": 0.065},
            {"name": "Nova", "pos": (0.75, 0.25), "color": (80, 220, 255), "radius": 0.060},
            {"name": "Zion", "pos": (0.20, 0.70), "color": (150, 100, 255), "radius": 0.070},
            {"name": "Solara", "pos": (0.80, 0.72), "color": (80, 255, 180), "radius": 0.065},
            {"name": "Krypton", "pos": (0.50, 0.40), "color": (255, 80, 220), "radius": 0.055},
        ]
        self.target_planet_idx = random.randint(0, len(self.planets) - 1)
        self.target_spawn_time = self.elapsed_time

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        target = self.planets[self.target_planet_idx]
        tx, ty = target["pos"]

        # Gaze check (within 0.18 of planet)
        gaze_x, gaze_y = frame_data.eyes.gaze_target_coords
        gaze_dist = np.hypot(gaze_x - tx, gaze_y - ty)
        gaze_aligned = gaze_dist < 0.18

        # Hand reach check
        rh = frame_data.hands.right_hand
        lh = frame_data.hands.left_hand
        hand_pos = rh.palm_center if rh.detected else (lh.palm_center if lh.detected else (0.5, 0.9))
        hand_dist = np.hypot(hand_pos[0] - tx, hand_pos[1] - ty)
        hand_aligned = hand_dist < 0.10

        # Activation condition: Gaze on target AND Hand on target
        if gaze_aligned and hand_aligned:
            self.beam_active = True
            self.beam_progress += dt * 1.8
            if self.beam_progress >= 1.0:
                # Successfully rescued
                self.rescued_count += 1
                reaction = max(0.4, self.elapsed_time - self.target_spawn_time)
                acc = max(0.6, 1.0 - (hand_dist / 0.10))
                self.record_hit(reaction_time=reaction, accuracy=acc, points=200)

                # Pick next planet
                available = [i for i in range(len(self.planets)) if i != self.target_planet_idx]
                self.target_planet_idx = random.choice(available)
                self.target_spawn_time = self.elapsed_time
                self.beam_progress = 0.0
                self.beam_active = False
        else:
            self.beam_active = False
            self.beam_progress = max(0.0, self.beam_progress - dt * 0.8)

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Starfield Planets
        for i, planet in enumerate(self.planets):
            px, py = int(planet["pos"][0] * width), int(planet["pos"][1] * height)
            pr = int(planet["radius"] * width)
            is_target = (i == self.target_planet_idx)

            if is_target:
                # Pulsing target rings
                halo = int(pr + 12 + 6 * np.sin(self.elapsed_time * 6.0))
                cv2.circle(frame, (px, py), halo, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.circle(frame, (px, py), halo + 6, (0, 240, 255), 1, cv2.LINE_AA)

            # Planet sphere
            cv2.circle(frame, (px, py), pr, planet["color"], -1, cv2.LINE_AA)
            cv2.putText(frame, planet["name"], (px - 22, py + pr + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 255), 1, cv2.LINE_AA)

            if is_target:
                # Stranded creature beacon
                cv2.putText(frame, "RESCUE ME!", (px - 36, py - pr - 8),
                            cv2.FONT_HERSHEY_DUPLEX, 0.45, (0, 255, 200), 1, cv2.LINE_AA)

        # Draw Tractor Beam if Active
        target = self.planets[self.target_planet_idx]
        tx, ty = int(target["pos"][0] * width), int(target["pos"][1] * height)
        if self.beam_active or self.beam_progress > 0.0:
            beam_alpha = min(1.0, self.beam_progress)
            beam_w = int(25 * beam_alpha)
            cv2.line(frame, (tx, ty), (tx, height), (0, 255, 255), max(2, beam_w), cv2.LINE_AA)
            # Beam charge circle
            cv2.circle(frame, (tx, ty), int(40 * self.beam_progress), (255, 255, 0), 3, cv2.LINE_AA)

    def handle_input(self, command: str):
        pass

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"rescued_creatures": self.rescued_count}
