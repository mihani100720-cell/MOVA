"""
MOVA AI Provider Abstraction
Implements Section 29: AI Provider architecture with Gemini, OpenAI, and Local providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AIProvider(ABC):
    @abstractmethod
    def generate_coach_feedback(self, structured_metrics: Dict[str, Any], trend_context: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def generate_session_summary(self, session_data: Dict[str, Any]) -> str:
        pass
