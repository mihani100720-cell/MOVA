"""
MOVA Adaptive Difficulty Engine
Implements Section 25:
Dynamically adjusts speed, size, reaction window, obstacle density, and sequence length
based on user accuracy and reaction performance.
"""

from typing import Dict, Any

class AdaptiveDifficultyEngine:
    def __init__(self, base_level: float = 1.0, min_level: float = 0.5, max_level: float = 3.0):
        self.current_level = float(base_level)
        self.min_level = min_level
        self.max_level = max_level
        self.consecutive_hits = 0
        self.consecutive_misses = 0

    def record_hit(self, reaction_time: float, accuracy: float):
        self.consecutive_misses = 0
        self.consecutive_hits += 1

        # Quick adaptation: 3 hits in a row with fast response triggers gradual increase
        if self.consecutive_hits >= 3 and reaction_time < 0.65 and accuracy >= 0.85:
            self.current_level = min(self.max_level, round(self.current_level + 0.15, 2))
            self.consecutive_hits = 0

    def record_miss(self):
        self.consecutive_hits = 0
        self.consecutive_misses += 1

        # Gentle ease back on 2 consecutive misses
        if self.consecutive_misses >= 2:
            self.current_level = max(self.min_level, round(self.current_level - 0.20, 2))
            self.consecutive_misses = 0

    def get_game_parameters(self) -> Dict[str, Any]:
        """
        Calculates dynamic mechanics modifiers according to difficulty level [0.5..3.0].
        """
        lvl = self.current_level
        # Target speed: faster at higher difficulty
        speed_mult = 0.7 + (lvl - 1.0) * 0.35
        # Target radius: slightly smaller at higher difficulty
        size_mult = max(0.65, 1.0 - (lvl - 1.0) * 0.15)
        # Reaction window: tighter at higher difficulty
        reaction_window_sec = max(1.2, 3.0 - (lvl - 1.0) * 0.6)
        # Spawn interval: targets appear faster
        spawn_interval_sec = max(1.0, 2.5 - (lvl - 1.0) * 0.5)

        return {
            "difficulty_level": round(lvl, 2),
            "speed_multiplier": round(speed_mult, 2),
            "size_multiplier": round(size_mult, 2),
            "reaction_window": round(reaction_window_sec, 2),
            "spawn_interval": round(spawn_interval_sec, 2),
            "density_multiplier": round(0.8 + (lvl * 0.2), 2)
        }
