"""
MOVA Local AI Provider
Deterministic, reliable, fast local insight generator with zero external network dependencies.
Strictly non-medical language (Section 2, 27).
"""

from typing import Dict, Any
from ai.provider import AIProvider

class LocalAIProvider(AIProvider):
    def generate_coach_feedback(self, metrics: Dict[str, Any], trend_context: Dict[str, Any]) -> str:
        game_name = metrics.get("game_name", "the activity")
        acc = metrics.get("accuracy", 0.8)
        reaction = metrics.get("reaction_time", 0.7)
        consistency = metrics.get("movement_consistency", 0.8)
        coord = metrics.get("multimodal_coordination", 80.0)

        # Observations
        obs = []
        if acc >= 0.85:
            obs.append(f"Excellent precision during {game_name}, landing {int(acc * 100)}% of attempted interactions.")
        else:
            obs.append(f"Solid interaction engagement during {game_name} with steady target pacing.")

        if reaction < 0.65:
            obs.append(f"Your reaction latency averaged a swift {reaction}s.")
        else:
            obs.append(f"Movement cadence was deliberate and focused (avg {reaction}s).")

        if coord >= 85.0:
            obs.append(f"Multimodal coordination between your tracked modalities was synchronized at {coord}%.")

        # Trend context
        trend_status = trend_context.get("trend_status", "")
        if trend_status and trend_context.get("has_previous"):
            obs.append(f"Compared to your previous sessions: {trend_status}.")

        # Practical next suggestion
        suggestion = "For your next round, try maintaining smooth limb acceleration when engaging peripheral targets."
        if acc < 0.75:
            suggestion = "Focus on visually locking onto targets before initiating arm extension."
        elif reaction > 0.85:
            suggestion = "Try initiating arm movement as soon as your gaze registers the target cue."

        return " ".join(obs) + " " + suggestion

    def generate_session_summary(self, session_data: Dict[str, Any]) -> str:
        games_count = session_data.get("games_completed", 1)
        total_score = session_data.get("total_score", 0)
        avg_acc = session_data.get("avg_accuracy", 0.8)
        avg_react = session_data.get("avg_reaction_time", 0.7)
        coord = session_data.get("multimodal_coordination", 85.0)

        return (
            f"Session finished with {games_count} activities completed and {total_score} total points earned. "
            f"Average interaction accuracy stood at {int(avg_acc * 100)}% with a mean reaction latency of {avg_react}s. "
            f"Overall multimodal spatial coordination reached {coord}%. "
            f"Movement consistency across your session remained stable and fluid."
        )
