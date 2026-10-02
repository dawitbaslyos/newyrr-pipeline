import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ENV_PATH = BASE_DIR / ".env"
SETTINGS_PATH = BASE_DIR / "user_settings.json"

# Load .env if present
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Load user settings if present
_saved_settings = {}
if SETTINGS_PATH.exists():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            _saved_settings = json.load(f)
    except Exception:
        pass

CLIO_STYLES_PATH = BASE_DIR / "clio_styles.json"
CLIO_STYLES = {}
if CLIO_STYLES_PATH.exists():
    try:
        with open(CLIO_STYLES_PATH, "r", encoding="utf-8") as f:
            CLIO_STYLES = json.load(f)
    except Exception:
        pass

class Config:
    BASE_DIR: Path = BASE_DIR
    SETTINGS_PATH: Path = SETTINGS_PATH
    CLIO_STYLES_PATH: Path = CLIO_STYLES_PATH
    CLIO_STYLES: dict = CLIO_STYLES
    
    # LLM & Scripting (OpenRouter)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = _saved_settings.get("llm_model") or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    OPENROUTER_FALLBACK_MODEL: str = os.getenv("OPENROUTER_FALLBACK_MODEL", "openai/gpt-4o-mini")
    
    # Active Models from Settings Modal
    ACTIVE_IMAGE_MODEL: str = _saved_settings.get("image_model", "krea/krea-2-medium-turbo")
    ACTIVE_VIDEO_PROVIDER: str = _saved_settings.get("video_provider", "bytedance/seedance-2.0-mini")
    ACTIVE_TTS_MODEL: str = _saved_settings.get("tts_model", "google/gemini-3.8-flash-lite-tts")
    ACTIVE_TTS_VOICE: str = _saved_settings.get("tts_voice", "Charon")
    ACTIVE_ART_STYLE: str = _saved_settings.get("art_style", "photo_35mm")
    
    # Image Generation API (Krea 2 Turbo, Nano Banana 2, etc.)
    IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "openrouter")
    OPENROUTER_IMAGE_MODEL: str = ACTIVE_IMAGE_MODEL
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")
    REPLICATE_IMAGE_MODEL: str = os.getenv("REPLICATE_IMAGE_MODEL", "black-forest-labs/flux-schnell")
    
    # Voice / Narration API
    VOICE_PROVIDER: str = os.getenv("VOICE_PROVIDER", "openrouter_google")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_VOICE: str = os.getenv("OPENAI_VOICE", "onyx")
    KOKORO_VOICE: str = os.getenv("KOKORO_VOICE", "am_adam")
    
    # RunPod Serverless API (Video Generation: MiniMax H3 Max Turbo)
    RUNPOD_API_KEY: str = os.getenv("RUNPOD_API_KEY", "")
    RUNPOD_MINIMAX_ENDPOINT_ID: str = os.getenv("RUNPOD_MINIMAX_ENDPOINT_ID", "ucla82uhwqfvd8")
    RUNPOD_FLUX_ENDPOINT_ID: str = os.getenv("RUNPOD_FLUX_ENDPOINT_ID", "e1s3ntmcuotb7y")
    RUNPOD_CHATTERBOX_ENDPOINT_ID: str = os.getenv("RUNPOD_CHATTERBOX_ENDPOINT_ID", "xu98042j0lmcdl")
    
    # YouTube Data API v3 (Performance Feedback Loop)
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    YOUTUBE_CHANNEL_ID: str = os.getenv("YOUTUBE_CHANNEL_ID", "UCeu7baUPB8SsCstFDSnSdrw") # @Newyrr

    # Directories
    OUTPUT_DIR: Path = BASE_DIR / "output"
    PROJECTS_DIR: Path = BASE_DIR / "projects"
    USED_DIR: Path = PROJECT_ROOT / "used"

# Ensure runtime directories exist
Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
Config.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
Config.USED_DIR.mkdir(parents=True, exist_ok=True)
