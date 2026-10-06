"""
GAME 05 — BEE SWARM 🐝
Concept: Dynamic visual-motor tracking. Friendly golden bees and stinging hornets buzz across the MOVA Zone.
User must visually track the Golden Queen Bee and intercept it with their hand while avoiding hornets.
Inputs: Hands, Eyes, Arms
"""

import random
import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame

class BeeSwarmGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="bee_swarm", game_name="Bee Swarm 🐝", duration_sec=45.0)
        self.required_modalities = ["hands", "eyes", "arms"]
        self.optional_modalities = ["body"]
        self.movement_focus = "Visual Selectivity & Rapid Hand Interception"

        self.bees: List[Dict[str, Any]] = []
        self.bees_caught: int = 0
        self.spawn_timer: float = 0.0

    def on_start(self):
        self.bees.clear()
        self.bees_caught = 0
        self.spawn_timer = 0.0
        self.objective_text = "Catch the Glowing Golden Queen Bee with your hand! Avoid red stingers!"
        self._spawn_swarm()

    def on_stop(self):
        pass

    def _spawn_swarm(self):
        self.bees.clear()
        # 1 Golden Queen
        self.bees.append({
            "is_queen": True,
            "x": random.uniform(0.2, 0.8),
            "y": random.uniform(0.2, 0.8),
            "vx": random.uniform(-0.15, 0.15),
            "vy": random.uniform(-0.15, 0.15),
            "radius": 0.055,
            "spawn_t": self.elapsed_time
        })
        # 2 Hornets (avoid)
        for _ in range(2):
            self.bees.append({
                "is_queen": False,
                "x": random.uniform(0.15, 0.85),
                "y": random.uniform(0.15, 0.85),
                "vx": random.uniform(-0.2, 0.2),
                "vy": random.uniform(-0.2, 0.2),
                "radius": 0.048,
                "spawn_t": self.elapsed_time
            })

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        rh = frame_data.hands.right_hand
        lh = frame_data.hands.left_hand
        r_pos = rh.palm_center if rh.detected else (0.8, 0.8)
        l_pos = lh.palm_center if lh.detected else (0.2, 0.8)

        # Update bee positions
        for bee in self.bees:
            # Flutter oscillation
            bee["x"] += (bee["vx"] + np.sin(self.elapsed_time * 8.0 + bee["x"] * 10) * 0.05) * dt
            bee["y"] += (bee["vy"] + np.cos(self.elapsed_time * 8.0 + bee["y"] * 10) * 0.05) * dt

            # Bounce walls
            if bee["x"] < 0.1 or bee["x"] > 0.9: bee["vx"] *= -1
            if bee["y"] < 0.15 or bee["y"] > 0.85: bee["vy"] *= -1

            # Check hand catch
            dist_r = np.hypot(r_pos[0] - bee["x"], r_pos[1] - bee["y"])
            dist_l = np.hypot(l_pos[0] - bee["x"], l_pos[1] - bee["y"])
            min_dist = min(dist_r, dist_l)

            if min_dist < (bee["radius"] + 0.04):
                if bee["is_queen"]:
                    self.bees_caught += 1
                    react = max(0.3, self.elapsed_time - bee["spawn_t"])
                    acc = max(0.5, 1.0 - (min_dist / 0.08))
                    self.record_hit(reaction_time=react, accuracy=acc, points=180)
                    self._spawn_swarm()
                    break
                else:
                    # Stung by hornet
                    self.record_miss()
                    bee["x"] = random.uniform(0.2, 0.8)
                    bee["y"] = random.uniform(0.2, 0.8)

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        for bee in self.bees:
            bx, by = int(bee["x"] * width), int(bee["y"] * height)
            br = int(bee["radius"] * width)

            if bee["is_queen"]:
                # Golden Queen glowing aura
                pulse = int(4 * np.sin(self.elapsed_time * 10.0))
                cv2.circle(frame, (bx, by), br + pulse + 4, (0, 240, 255), 2, cv2.LINE_AA)
                cv2.circle(frame, (bx, by), br, (30, 215, 255), -1, cv2.LINE_AA)
                # Wings
                cv2.ellipse(frame, (bx - 12, by - 12), (10, 6), 45, 0, 360, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.ellipse(frame, (bx + 12, by - 12), (10, 6), -45, 0, 360, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(frame, "QUEEN", (bx - 20, by + br + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 240, 255), 1)
            else:
                # Red Hornet
                cv2.circle(frame, (bx, by), br, (20, 20, 220), -1, cv2.LINE_AA)
                cv2.circle(frame, (bx, by), br + 2, (50, 50, 255), 1, cv2.LINE_AA)
                cv2.putText(frame, "!", (bx - 3, by + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    def handle_input(self, command: str):
        pass

    def get_extra_metrics(self) -> Dict[str, Any]:
        return {"bees_caught": self.bees_caught}
