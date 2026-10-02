import asyncio
import edge_tts
import os
from typing import Optional

VOICE_PROFILES = {
    "christopher": "en-US-ChristopherNeural",  # Authoritative, documentary explainer
    "guy": "en-US-GuyNeural",                  # Natural, casual, dynamic
    "jenny": "en-US-JennyNeural",              # Clear, intelligent, professional
    "eric": "en-US-EricNeural",                # Bold, punchy, energetic
    "brian": "en-GB-BrianNeural",              # British, refined, intellectual
}

async def generate_narration_async(text: str, output_path: str, voice_key: str = "christopher", rate: str = "+0%", pitch: str = "+0%") -> str:
    """Generates studio-quality narration audio using Edge-TTS for free."""
    voice = VOICE_PROFILES.get(voice_key.lower(), VOICE_PROFILES["christopher"])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)
    return output_path

def generate_narration(text: str, output_path: str, voice_key: str = "christopher", rate: str = "+0%", pitch: str = "+0%") -> str:
    """Synchronous wrapper for narration generation."""
    return asyncio.run(generate_narration_async(text, output_path, voice_key, rate, pitch))
