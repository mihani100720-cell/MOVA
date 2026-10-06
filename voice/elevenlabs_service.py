"""
MOVA Voice AI: ElevenLabs Integration & Audio Feedback Generator
Implements Section 28:
Countdown cues ("Ready?", "Three...", "Two...", "One..."), encouragement, and game cues.
Fails gracefully if API is unavailable. Never blocks or breaks gameplay.
"""

import os
import requests
from typing import Optional
from config.settings import settings
from utils.logger import logger

class VoiceSynthesisService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
        self.enabled = bool(self.api_key)

    def speak(self, text: str) -> Optional[bytes]:
        """
        Synthesizes audio using ElevenLabs REST API if configured.
        Returns MP3 bytes or None.
        """
        if not self.enabled or not self.api_key:
            return None

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.65,
                "similarity_boost": 0.75
            }
        }
        try:
            res = requests.post(url, json=data, headers=headers, timeout=3.5)
            if res.status_code == 200:
                return res.content
            else:
                logger.warning(f"ElevenLabs error ({res.status_code}): {res.text[:100]}")
                return None
        except Exception as e:
            logger.warning(f"ElevenLabs synthesis error: {e}")
            return None

tts_service = VoiceSynthesisService()
