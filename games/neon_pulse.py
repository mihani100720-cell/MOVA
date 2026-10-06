"""
GAME 10 — NEON PULSE ⚡
Concept: Spatial rhythm and bilateral timing game.
Neon beat rings collapse toward left and right rhythm pads in sync with a rhythmic beat.
User strikes the target pads precisely when rings align to score Perfect / Good timing hits.
Inputs: Eyes, Hands, Arms, Body, Optional Voice
"""

import numpy as np
import cv2
from typing import Dict, Any, List, Tuple
from games.base_game import BaseGame

class NeonPulseGame(BaseGame):
    def __init__(self):
        super().__init__(game_id="neon_pulse", game_name="Neon Pulse ⚡", duration_sec=45.0)
        self.required_modalities = ["eyes", "hands", "arms", "body"]
        self.optional_modalities = ["voice"]
        self.movement_focus = "Bilateral Spatial Rhythm & Millisecond Timing Accuracy"

        self.bpm = 100.0
        self.beat_interval = 60.0 / self.bpm  # ~0.60 sec per beat
        self.beat_timer = 0.0
        self.rhythm_pads = [
            {"id": "left_pad", "pos": (0.25, 0.55), "hand": "Left", "color": (255, 60, 180)},
            {"id": "right_pad", "pos": (0.75, 0.55), "hand": "Right", "color": (80, 240, 255)},
            {"id": "top_pad", "pos": (0.50, 0.30), "hand": "Any", "color": (60, 255, 120)}
        ]
        self.active_pulses: List[Dict[str, Any]] = []
        self.perfect_hits: int = 0
        self.good_hits: int = 0

    def on_start(self):
        self.active_pulses.clear()
        self.perfect_hits = 0
        self.good_hits = 0
        self.beat_timer = 0.0
        self.objective_text = "Strike the Neon Pads with your hands exactly when the collapsing ring hits the center!"

    def on_stop(self):
        pass

    def update(self, dt: float, frame_data, movement_metrics: Dict[str, Any], fusion_result: Dict[str, Any]):
        self.beat_timer += dt
        if self.beat_timer >= self.beat_interval:
            self.beat_timer -= self.beat_interval
            # Spawn incoming beat ring
            import random
            target_pad = random.choice(self.rhythm_pads)
            self.active_pulses.append({
                "pad": target_pad,
                "radius": 0.16,
                "collapse_speed": 0.18 * self.difficulty_engine.current_level,
                "hit": False,
                "spawn_t": self.elapsed_time
            })

        rh = frame_data.hands.right_hand.palm_center if frame_data.hands.right_hand.detected else (0.8, 0.8)
        lh = frame_data.hands.left_hand.palm_center if frame_data.hands.left_hand.detected else (0.2, 0.8)

        # Update collapsing pulses
        for pulse in self.active_pulses[:]:
            pulse["radius"] -= pulse["collapse_speed"] * dt
            pad = pulse["pad"]
            px, py = pad["pos"]

            # Perfect hit zone: radius between 0.03 and 0.065
            if not pulse["hit"] and 0.02 <= pulse["radius"] <= 0.07:
                d_r = np.hypot(rh[0] - px, rh[1] - py)
                d_l = np.hypot(lh[0] - px, lh[1] - py)
                min_hand_dist = min(d_r, d_l)

                if min_hand_dist < 0.10:
                    pulse["hit"] = True
                    is_perfect = (0.035 <= pulse["radius"] <= 0.055)
                    points = 250 if is_perfect else 120
                    if is_perfect:
                        self.perfect_hits += 1
                    else:
                        self.good_hits += 1

                    self.record_hit(reaction_time=round(self.beat_interval, 3),
                                    accuracy=1.0 if is_perfect else 0.85,
                                    points=points)
                    self.active_pulses.remove(pulse)
                    continue

            # Pulse missed / collapsed past center
            if pulse["radius"] < 0.015:
                if not pulse["hit"]:
                    self.record_miss()
                if pulse in self.active_pulses:
                    self.active_pulses.remove(pulse)

    def render(self, frame: np.ndarray, width: int, height: int):
        self.draw_universal_hud(frame, width, height)

        # Draw Static Rhythm Pads
        for pad in self.rhythm_pads:
            px, py = int(pad["pos"][0] * width), int(pad["pos"][1] * height)
            cv2.circle(frame, (px, py), 32, (30, 20, 45), -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 32, pad["color"], 2, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 8, pad["color"], -1, cv2.LINE_AA)
            cv2.putText(frame, pad["hand"], (px - 18, py + 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 240), 1)

        # Draw Collapsing Beat Rings
        for pulse in self.active_pulses:
            pad = pulse["pad"]
            px, py = int(pad["pos"][0] * width), int(pad["pos"][1] * height)
            pr = int(pulse["radius"] * width)
            if pr > 5:
                cv2.circle(frame, (px, py), pr, pad["color"], 3, cv2.LINE_AA)
                cv2.circle(frame, (px, py), max(2, pr - 3), (255, 255, 255), 1, cv2.LINE_AA)

        # BPM Indicator
        cv2.putText(frame, f"BPM: {int(self.bpm)}", (width // 2 - 40, 95),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 220, 80), 1, cv2.LINE_AA)

    def handle_input(self, command: str):
        pass

    def get_extra_metrics(self) -> Dict[str, Any]:
        total_hits = self.perfect_hits + self.good_hits
        perfect_ratio = (self.perfect_hits / max(1, total_hits))
        return {"rhythm_sync": round(perfect_ratio, 2), "perfect_hits": self.perfect_hits, "good_hits": self.good_hits}
