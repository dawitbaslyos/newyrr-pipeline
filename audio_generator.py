import os
import json
import base64
import time
import requests
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from config import Config

class AudioGenerator:
    """
    Pure-Cloud Studio Audio Generator:
    1. Google Gemini Flash Studio TTS via OpenRouter (/api/v1/audio/speech)
       Voices: Charon (Deep Documentary), Puck (Storyteller), Fenrir (Intense Cinematic), Aoede, etc.
    2. Hexgrad Kokoro-82M API
    3. Fallback
    """

    def __init__(self, openrouter_key: Optional[str] = None):
        self.openrouter_key = openrouter_key or Config.OPENROUTER_API_KEY
        self.replicate_token = Config.REPLICATE_API_TOKEN
        self.openai_key = Config.OPENAI_API_KEY

    def generate_speech(self, text: str, output_path: str, voice: Optional[str] = None, tts_model: Optional[str] = None) -> str:
        output_path = str(Path(output_path).resolve())
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        tts_model = tts_model or getattr(Config, "ACTIVE_TTS_MODEL", "google/gemini-3.8-flash-lite-tts")
        voice = voice or getattr(Config, "ACTIVE_TTS_VOICE", "Charon")

        # 1. Google Gemini Flash TTS on OpenRouter (Primary)
        if self.openrouter_key and "google" in tts_model.lower():
            try:
                res = self._call_openrouter_google_tts(text, output_path, tts_model, voice)
                if res and os.path.exists(res):
                    return res
            except Exception as e:
                print(f"[Audio Generator] Google Gemini TTS error: {e}...")

        # 2. Deepgram Flux TTS on OpenRouter (Free)
        if self.openrouter_key and ("deepgram" in tts_model.lower() or voice.startswith("flux-")):
            try:
                actual_voice = voice if voice.startswith("flux-") else "flux-cliff-en"
                res = self._call_openrouter_deepgram(text, output_path, actual_voice)
                if res and os.path.exists(res):
                    return res
            except Exception as e:
                print(f"[Audio Generator] Deepgram Flux TTS error: {e}...")

        # 2. Kokoro on OpenRouter or Replicate
        if "kokoro" in tts_model.lower():
            try:
                res = self._call_openrouter_kokoro(text, output_path, voice)
                if res and os.path.exists(res):
                    return res
            except Exception as e:
                print(f"[Audio Generator] Kokoro error: {e}...")

        # 3. OpenAI TTS API (if key available)
        if self.openai_key:
            try:
                res = self._call_openai_tts(text, output_path, voice)
                if res and os.path.exists(res):
                    return res
            except Exception as e:
                print(f"[Audio Generator] OpenAI TTS error: {e}...")

        # 4. Edge-TTS Free Studio Narration (Christopher, Guy, etc.)
        try:
            from repurpose.tts import generate_narration
            edge_voice = "christopher"
            if voice and any(k in voice.lower() for k in ["guy", "jenny", "eric", "brian", "christopher"]):
                edge_voice = voice.lower()
            res = generate_narration(text, output_path, voice_key=edge_voice)
            if res and os.path.exists(res) and os.path.getsize(res) > 1000:
                print(f"[Audio Generator] Fallback to Edge-TTS ({edge_voice}) succeeded!")
                return res
        except Exception as e:
            print(f"[Audio Generator] Edge-TTS fallback warning: {e}...")

        # 5. Fallback timed audio
        return self._generate_fallback_audio(text, output_path)

    def _call_openrouter_google_tts(self, text: str, output_path: str, model: str, voice: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "input": text,
            "voice": voice
        }

        print(f"[Audio Generator] Calling Google Studio TTS ({voice}) for: \"{text[:45]}...\"")
        res = requests.post("https://openrouter.ai/api/v1/audio/speech", headers=headers, json=payload, timeout=30)
        
        if res.status_code == 200 and len(res.content) > 1000:
            temp_pcm = output_path + ".raw"
            with open(temp_pcm, "wb") as f:
                f.write(res.content)
            
            # Convert raw 24kHz PCM into broadcast-quality MP3 via local FFmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "s16le",
                "-ar", "24000",
                "-ac", "1",
                "-i", temp_pcm,
                "-c:a", "libmp3lame",
                "-b:a", "192k",
                output_path
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if os.path.exists(temp_pcm):
                    os.remove(temp_pcm)
                print(f"[Audio Generator] Saved Google Studio audio ({voice}): {output_path}")
                return output_path
            except Exception as e:
                print(f"[Audio Generator] PCM encoding error: {e}")
                return temp_pcm
        else:
            print(f"[Audio Generator] Google TTS returned {res.status_code}: {res.text[:120]}")
            return None

    def _call_openrouter_deepgram(self, text: str, output_path: str, voice: str = "flux-cliff-en") -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepgram/flux-tts:free",
            "input": text,
            "voice": voice
        }
        print(f"[Audio Generator] Calling Deepgram Flux TTS ({voice}) for: \"{text[:45]}...\"")
        res = requests.post("https://openrouter.ai/api/v1/audio/speech", headers=headers, json=payload, timeout=30)
        if res.status_code == 200 and len(res.content) > 500:
            with open(output_path, "wb") as f:
                f.write(res.content)
            print(f"[Audio Generator] Saved Deepgram Flux audio ({voice}): {output_path}")
            return output_path
        else:
            print(f"[Audio Generator] Deepgram returned status {res.status_code}: {res.text[:120]}")
            return None

    def _call_openrouter_kokoro(self, text: str, output_path: str, voice: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "hexgrad/kokoro-82m",
            "input": text,
            "voice": voice or "am_adam"
        }
        print(f"[Audio Generator] Calling Kokoro-82M on OpenRouter ({payload['voice']})...")
        res = requests.post("https://openrouter.ai/api/v1/audio/speech", headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(res.content)
            return output_path
        return None

    def _call_openai_tts(self, text: str, output_path: str, voice: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1-hd",
            "input": text,
            "voice": voice or "onyx",
            "response_format": "mp3"
        }
        res = requests.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(res.content)
            return output_path
        return None

    def _generate_fallback_audio(self, text: str, output_path: str) -> str:
        words = len(text.split())
        est_duration = max(3.0, min(7.0, round(words / 2.6, 2)))
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={est_duration}",
            "-filter:a", "volume=0.01",
            "-c:a", "libmp3lame",
            "-b:a", "128k",
            output_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            pass
        return output_path

    def get_audio_duration(self, audio_path: str) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            return 5.0

if __name__ == "__main__":
    gen = AudioGenerator()
    test_out = os.path.join(os.path.dirname(__file__), "test_voice.mp3")
    res = gen.generate_speech("Cold water at night tricks your brain into feeling alive.", test_out)
    print("Voice test output:", res)
