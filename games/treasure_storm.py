"""
GAME 06 — TREASURE STORM 🏴‍☠️
Concept: Swashbuckling spatial treasure hunt amid rolling lightning storm zones.
User dodges storm hazard quadrants with body posture, reaches to locked chests, and unlocks with pinch/grab.
Inputs: Body, Arms, Hands, Gaze
"""

import random
import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame

class TreasureStormGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="treasure_storm", game_name="Treasure Storm 🏴‍☠️", duration_sec=45.0)
        self.required_modalities = ["body", "arms", "hands"]
        self.optional_modalities = ["gaze"]
        self.movement_focus = "Hazard Evasion & Fine Pinch / Unlock Gestures"

        self.chests: List[Dict[str, Any]] = []
        self.storm_hazard_sector: int = 0  # 0: Top-Left, 1: Top-Right, 2: Bottom-Left, 3: Bottom-Right
        self.storm_timer: float = 0.0
        self.chests_unlocked: int = 0

    def on_start(self):
        self.chests.clear()
        self.chests_unlocked = 0
        self.storm_timer = 4.0
        self.storm_hazard_sector = random.randint(0, 3)
        self.objective_text = "Dodge the electrified storm zone! Reach chest and PINCH or GRAB to unlock!"
        self._spawn_chest()

    def on_stop(self):
        pass

    def _spawn_chest(self):
        # Place chest outside active storm hazard
        sectors = [0, 1, 2, 3]
        sectors.remove(self.storm_hazard_sector)
        sec = random.choice(sectors)
        sx = 0.25 if sec in (0, 2) else 0.75
        sy = 0.35 if sec in (0, 1) else 0.75
        self.chests = [{
            "x": sx + random.uniform(-0.08, 0.08),
            "y": sy + random.uniform(-0.08, 0.08),
            "unlocked": False,
            "unlock_progress": 0.0,
            "spawn_t": self.elapsed_time
        }]

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        # Storm sector cycling
        self.storm_timer -= dt
        if self.storm_timer <= 0:
            self.storm_hazard_sector = (self.storm_hazard_sector + 1) % 4
            self.storm_timer = max(2.5, 4.5 - (self.difficulty_engine.current_level * 0.5))

        body_center = frame_data.pose.body_center if frame_data.pose.detected else (0.5, 0.5)

        # Check if user's body is standing inside the active hazard zone
        in_hazard = False
        if self.storm_hazard_sector == 0 and body_center[0] < 0.5 and body_center[1] < 0.5: in_hazard = True
        elif self.storm_hazard_sector == 1 and body_center[0] >= 0.5 and body_center[1] < 0.5: in_hazard = True
        elif self.storm_hazard_sector == 2 and body_center[0] < 0.5 and body_center[1] >= 0.5: in_hazard = True
        elif self.storm_hazard_sector == 3 and body_center[0] >= 0.5 and body_center[1] >= 0.5: in_hazard = True

        if in_hazard:
            self.record_miss()

        # Check chest unlocking with hand pinch or fist gesture
        rh = frame_data.hands.right_hand
        lh = frame_data.hands.left_hand
        active_hand = rh if rh.detected else (lh if lh.detected else None)

        if active_hand and self.chests:
            chest = self.chests[0]
            dist = np.hypot(active_hand.palm_center[0] - chest["x"], active_hand.palm_center[1] - chest["y"])
            if dist < 0.12 and (active_hand.is_pinching or active_hand.gesture in ("pinch", "fist")):
                chest["unlock_progress"] += dt * 2.2
                if chest["unlock_progress"] >= 1.0:
                    self.chests_unlocked += 1
                    react = max(0.4, self.elapsed_time - chest["spawn_t"])
                    self.record_hit(reaction_time=react, accuracy=0.95, points=240)
                    self._spawn_chest()

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Storm Hazard Quadrant
        overlay = frame.copy()
        sec = self.storm_hazard_sector
        x1 = 0 if sec in (0, 2) else width // 2
        y1 = 55 if sec in (0, 1) else height // 2
        x2 = width // 2 if sec in (0, 2) else width
        y2 = height // 2 if sec in (0, 1) else height
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (20, 20, 200), -1)
        cv2.addWeighted(overlay, 0.28, frame, 0.72, 0, frame)

        cv2.putText(frame, f"STORM SURGE IN SECTOR {sec + 1}!", (x1 + 20, y1 + 35),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (100, 150, 255), 2, cv2.LINE_AA)

        # Draw Treasure Chest
        if self.chests:
            c = self.chests[0]
            cx, cy = int(c["x"] * width), int(c["y"] * height)
            w_box, h_box = 45, 35
            # Chest body
            cv2.rectangle(frame, (cx - w_box, cy - h_box), (cx + w_box, cy + h_box), (30, 90, 180), -1, cv2.LINE_AA)
            cv2.rectangle(frame, (cx - w_box, cy - h_box), (cx + w_box, cy + h_box), (0, 215, 255), 2, cv2.LINE_AA)
            # Lock & progress
            cv2.circle(frame, (cx, cy), 10, (0, 255, 255), -1)
            cv2.putText(frame, "PINCH TO UNLOCK", (cx - 65, cy - h_box - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

            # Circular unlock progress
            if c["unlock_progress"] > 0.0:
                angle = int(360 * c["unlock_progress"])
                cv2.ellipse(frame, (cx, cy), (22, 22), 0, 0, angle, (0, 255, 120), 3, cv2.LINE_AA)

    def handle_input(self, command: str):
        pass

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"chests_unlocked": self.chests_unlocked}
