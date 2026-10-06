"""
MOVA Game Recommendation Engine
Implements Section 34:
Recommends the next game based on previous performance gaps and modality strengths.
Fully explainable and transparent.
"""

from typing import Dict, Any, List, Optional

class RecommendationEngine:
    GAMES_CATALOG = [
        {"id": "gravity_flip", "name": "Gravity Flip 🪐", "modalities": ["body", "arms", "head"], "focus": "Stability & Directional Shift"},
        {"id": "dragon_dash", "name": "Dragon Dash 🐉", "modalities": ["eyes", "hands", "arms", "body"], "focus": "Obstacle Evasion & Multimodal Energy Catch"},
        {"id": "galaxy_rescue", "name": "Galaxy Rescue 🌌", "modalities": ["gaze", "hand", "arm", "body"], "focus": "Gaze Fixation & Spatial Reach"},
        {"id": "spellcaster", "name": "Spellcaster 🪄", "modalities": ["hands", "arms", "voice"], "focus": "Glyph Trajectory & Gesture Precision"},
        {"id": "bee_swarm", "name": "Bee Swarm 🐝", "modalities": ["hands", "eyes", "arms"], "focus": "Visual Selectivity & Hand Speed"},
        {"id": "treasure_storm", "name": "Treasure Storm 🏴‍☠️", "modalities": ["body", "arms", "hands", "gaze"], "focus": "Hazard Navigation & Precision Unlock"},
        {"id": "robot_factory", "name": "Robot Factory 🤖", "modalities": ["hands", "arms", "eyes", "voice"], "focus": "Sequential Assembly & Multimodal Flow"},
        {"id": "ocean_guardian", "name": "Ocean Guardian 🌊", "modalities": ["body", "arms", "hands", "gaze"], "focus": "Submarine Steering & Arm Reach"},
        {"id": "mirror_mage", "name": "Mirror Mage 🪞", "modalities": ["eyes", "face", "hands", "arms", "body"], "focus": "Multimodal Synchronization & Sequence Memory"},
        {"id": "neon_pulse", "name": "Neon Pulse ⚡", "modalities": ["eyes", "hands", "arms", "body"], "focus": "Spatial Rhythm & Bilateral Timing"}
    ]

    @classmethod
    def recommend_next_game(cls, last_result: Optional[Dict[str, Any]],
                            all_recent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not last_result:
            return {
                "game_id": "galaxy_rescue",
                "game_name": "Galaxy Rescue 🌌",
                "reason": "An ideal entry experience combining gaze target fixation and natural arm reach.",
                "target_focus": "Eye-Hand Coordination"
            }

        gaze_acc = last_result.get("gaze_accuracy", 0.8)
        gesture_acc = last_result.get("gesture_accuracy", 0.8)
        stability = last_result.get("stability_score", 85.0)
        coordination = last_result.get("multimodal_coordination", 80.0)
        curr_id = last_result.get("game_id", "")

        # 1. Low gaze fixation or accuracy -> Recommend Galaxy Rescue or Bee Swarm
        if gaze_acc < 0.65 and curr_id != "galaxy_rescue":
            return {
                "game_id": "galaxy_rescue",
                "game_name": "Galaxy Rescue 🌌",
                "reason": "Challenges gaze fixation and visual-spatial target alignment.",
                "target_focus": "Gaze-To-Reach Coupling"
            }

        # 2. Low posture stability or body sway -> Recommend Gravity Flip or Ocean Guardian
        if stability < 75.0 and curr_id != "gravity_flip":
            return {
                "game_id": "gravity_flip",
                "game_name": "Gravity Flip 🪐",
                "reason": "Develops deliberate body displacement and posture stabilization during gravitational shifts.",
                "target_focus": "Core Stability & Posture"
            }

        # 3. High hand speed and accuracy -> Recommend Spellcaster or Neon Pulse
        if gesture_acc > 0.85 and curr_id != "spellcaster":
            return {
                "game_id": "spellcaster",
                "game_name": "Spellcaster 🪄",
                "reason": "Your hand accuracy is prime. Spellcaster tests fine spatial glyph trajectories and smooth casting.",
                "target_focus": "Trajectory Precision & Gestures"
            }

        # 4. Ready for complete multimodal challenge -> Mirror Mage or Robot Factory
        if coordination >= 85.0 and curr_id != "mirror_mage":
            return {
                "game_id": "mirror_mage",
                "game_name": "Mirror Mage 🪞",
                "reason": "Synchronizes eyes, face orientation, dual hands, and body posture into memory sequences.",
                "target_focus": "Full Multimodal Synchronization"
            }

        # Default rotation to an unplayed or different game
        played_ids = {r.get("game_id") for r in all_recent_results}
        for g in cls.GAMES_CATALOG:
            if g["id"] not in played_ids and g["id"] != curr_id:
                return {
                    "game_id": g["id"],
                    "game_name": g["name"],
                    "reason": f"Explore fresh mechanics: {g['focus']}.",
                    "target_focus": g["focus"]
                }

        # Alternate game
        next_g = cls.GAMES_CATALOG[(hash(curr_id) + 1) % len(cls.GAMES_CATALOG)]
        return {
            "game_id": next_g["id"],
            "game_name": next_g["name"],
            "reason": f"Progressive challenge focusing on {next_g['focus']}.",
            "target_focus": next_g["focus"]
        }
