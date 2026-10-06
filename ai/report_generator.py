"""
MOVA AI Report Generator: Prepares structured narratives and session trend briefings
"""

from typing import Dict, Any, List
from ai.coach import ai_coach
from ml.recommendation_engine import RecommendationEngine

class ReportGenerator:
    @classmethod
    def generate_full_session_brief(cls, session_metadata: Dict[str, Any],
                                    game_results: List[Dict[str, Any]],
                                    trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        last_result = game_results[0] if game_results else {}
        coach_text = ai_coach.get_coach_feedback(last_result, trend_analysis)
        recommendation = RecommendationEngine.recommend_next_game(last_result, game_results)

        return {
            "session_summary": ai_coach.get_session_summary(session_metadata),
            "coach_observation": coach_text,
            "next_recommendation": recommendation,
            "trend_status": trend_analysis.get("trend_status", "Baseline Established"),
            "trend_summary": trend_analysis.get("summary", "")
        }
