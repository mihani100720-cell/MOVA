"""
MOVA AI Coach: Orchestrates providers and provides non-medical personal guidance
"""

from typing import Dict, Any, Optional
from config.settings import settings
from ai.provider import AIProvider
from ai.local_provider import LocalAIProvider
from ai.gemini_provider import GeminiAIProvider, OpenAIProvider
from utils.logger import logger

class AICoach:
    def __init__(self):
        self.local_provider = LocalAIProvider()
        self.gemini_provider = GeminiAIProvider() if settings.GEMINI_API_KEY else None
        self.openai_provider = OpenAIProvider() if settings.OPENAI_API_KEY else None

    def get_coach_feedback(self, structured_metrics: Dict[str, Any], trend_context: Dict[str, Any]) -> str:
        # Try cloud provider first if configured
        feedback = ""
        if self.gemini_provider:
            feedback = self.gemini_provider.generate_coach_feedback(structured_metrics, trend_context)
        elif self.openai_provider:
            feedback = self.openai_provider.generate_coach_feedback(structured_metrics, trend_context)

        # Fallback to local deterministic AI provider if cloud is empty or unavailable
        if not feedback:
            feedback = self.local_provider.generate_coach_feedback(structured_metrics, trend_context)

        return feedback

    def get_session_summary(self, session_data: Dict[str, Any]) -> str:
        summary = ""
        if self.gemini_provider:
            summary = self.gemini_provider.generate_session_summary(session_data)
        if not summary:
            summary = self.local_provider.generate_session_summary(session_data)
        return summary

ai_coach = AICoach()
