"""
MOVA Gemini & OpenAI AI Providers
Strictly receives structured JSON metrics. Never raw camera video.
Enforces non-medical guardrails and YOU vs. YOUR PREVIOUS PERFORMANCE comparison.
"""

import json
import requests
from typing import Dict, Any, Optional
from config.settings import settings
from ai.provider import AIProvider
from utils.logger import logger
from utils.privacy import sanitize_metrics_for_cloud

COACH_SYSTEM_PROMPT = """You are the MOVA AI Movement Coach.
MOVA is an experimental multimodal spatial gaming and movement intelligence platform.
IMPORTANT RULES:
1. NEVER make any medical, neurological, or diagnostic claims. Do not mention disorders, therapy, or clinical conditions.
2. ONLY compare the user against their OWN previous performance baseline. NEVER compare to other users or population norms.
3. Use careful, positive movement terminology: "movement consistency", "interaction performance", "reaction performance", "observed movement pattern", "session trend".
4. Provide concise (2-3 sentences), encouraging feedback and one actionable gameplay tip for their next session.
"""

class GeminiAIProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY

    def generate_coach_feedback(self, metrics: Dict[str, Any], trend_context: Dict[str, Any]) -> str:
        if not self.api_key:
            return ""

        sanitized_metrics = sanitize_metrics_for_cloud(metrics)
        prompt = (
            f"{COACH_SYSTEM_PROMPT}\n\n"
            f"Here are the user's latest game metrics (YOU vs YOUR PREVIOUS BASELINE):\n"
            f"Metrics: {json.dumps(sanitized_metrics)}\n"
            f"Personal Trend Context: {json.dumps(trend_context)}\n\n"
            f"Provide encouraging coach feedback and a practical gameplay tip."
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            res = requests.post(url, json=payload, timeout=5.0)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
            else:
                logger.warning(f"Gemini API returned status {res.status_code}")
                return ""
        except Exception as e:
            logger.warning(f"Gemini API error: {e}")
            return ""

    def generate_session_summary(self, session_data: Dict[str, Any]) -> str:
        if not self.api_key:
            return ""
        prompt = f"{COACH_SYSTEM_PROMPT}\nSummarize this completed session:\n{json.dumps(session_data)}"
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=5.0)
            if res.status_code == 200:
                return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass
        return ""

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY

    def generate_coach_feedback(self, metrics: Dict[str, Any], trend_context: Dict[str, Any]) -> str:
        if not self.api_key:
            return ""
        sanitized = sanitize_metrics_for_cloud(metrics)
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": COACH_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Metrics: {json.dumps(sanitized)}\nTrend: {json.dumps(trend_context)}"}
                ],
                "max_tokens": 150
            }
            res = requests.post(url, json=payload, headers=headers, timeout=5.0)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"OpenAI API error: {e}")
        return ""

    def generate_session_summary(self, session_data: Dict[str, Any]) -> str:
        return ""
