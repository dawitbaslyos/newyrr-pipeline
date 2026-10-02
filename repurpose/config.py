import json
import os
from typing import Dict, Any

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")

DEFAULT_CONFIG = {
    "openrouter_api_key": "",
    "openrouter_model": "google/gemini-2.0-flash-001",
    "runpod_api_key": "",
    "runpod_flux_endpoint": "",
    "runpod_ltx_endpoint": "",
    "runpod_tts_endpoint": "",
    "google_drive_folder_id": "",
    "youtube_api_client_secrets": "",
    "auto_publish_hours": 3
}

try:
    from config import Config
except (ImportError, ValueError):
    Config = None

def get_config() -> Dict[str, Any]:
    cfg = DEFAULT_CONFIG.copy()
    if Config:
        cfg["openrouter_api_key"] = getattr(Config, "OPENROUTER_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
        cfg["openrouter_model"] = getattr(Config, "OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
        cfg["runpod_api_key"] = getattr(Config, "RUNPOD_API_KEY", "") or os.getenv("RUNPOD_API_KEY", "")

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg.update({k: v for k, v in saved.items() if v})
        except Exception:
            pass
    return cfg

def save_config(updates: Dict[str, Any]):
    cfg = get_config()
    cfg.update(updates)
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return cfg
