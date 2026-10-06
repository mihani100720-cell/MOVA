"""
MOVA Speech-to-Text & Microphone Listener
Listens for audio cues and fails gracefully if microphone is unavailable.
"""

import time
from typing import Optional, Callable
from utils.logger import logger
from voice.voice_commands import VoiceCommandParser

class SpeechToTextService:
    def __init__(self):
        self.is_available: bool = False
        self.last_detected_command: Optional[str] = None
        self.last_command_time: float = 0.0
        self._check_hardware()

    def _check_hardware(self):
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
            self.is_available = len(input_devices) > 0
            logger.info(f"Microphone detected: {self.is_available}")
        except Exception as e:
            logger.warning(f"Audio device check failed: {e}. Voice will run in browser/fallback mode.")
            self.is_available = False

    def push_transcription(self, text: str) -> Optional[str]:
        """Receives speech transcription (e.g. from browser Web Speech API or whisper)."""
        cmd = VoiceCommandParser.parse_utterance(text)
        if cmd:
            self.last_detected_command = cmd
            self.last_command_time = time.perf_counter()
            logger.info(f"Voice command recognized: {cmd}")
        return cmd

    def consume_last_command(self) -> Optional[str]:
        cmd = self.last_detected_command
        self.last_detected_command = None
        return cmd

stt_service = SpeechToTextService()
