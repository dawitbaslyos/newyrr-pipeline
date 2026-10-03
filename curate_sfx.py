"""
Curates, cleans, trims, and normalizes the top 3 sound effects per category
from the user's raw SFX collection into pipeline/data/sfx_bank/.

Computes precise metadata for each sound:
- duration_ms: total length of the sound
- peak_offset_ms: exact transient peak time from start of file
- category: whoosh, impact, click_accent, pop_bubble, ding_bell, riser_tension
- trigger_keywords: semantic cues for LLM/JEV matching
"""

import os
import json
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path

SFX_SOURCE_DIR = Path(r"C:\Users\dawit\Videos\Editing Source\Video SoundEffects")
PIPELINE_DATA_DIR = Path(__file__).parent / "data"
TARGET_SFX_BANK = PIPELINE_DATA_DIR / "sfx_bank"
CATALOG_PATH = PIPELINE_DATA_DIR / "sfx_catalog.json"

TARGET_FILES = [
    # 1. Whooshes (transitions)
    {
        "id": "whoosh_snappy",
        "category": "whoosh",
        "source_name": "swoosh 05.mp3",
        "description": "Crisp ultra-fast whip swoosh, ideal for rapid scene cuts",
        "max_duration_sec": 0.6,
        "fade_out_sec": 0.15,
        "triggers": ["cut", "transition", "swipe", "pass", "whip", "next"]
    },
    {
        "id": "whoosh_smooth",
        "category": "whoosh",
        "source_name": "swoosh 02.mp3",
        "description": "Smooth airy swoosh, ideal for cinematic perspective shifts",
        "max_duration_sec": 0.8,
        "fade_out_sec": 0.20,
        "triggers": ["turn", "rotate", "pan", "fly", "shift", "glide"]
    },
    {
        "id": "whoosh_whip",
        "category": "whoosh",
        "source_name": "whoosh-6316.mp3",
        "description": "Punchy air whip whoosh, ideal for dramatic scene transitions",
        "max_duration_sec": 0.6,
        "fade_out_sec": 0.15,
        "triggers": ["speed", "rush", "sweep", "dash", "zoom"]
    },

    # 2. Impacts (hooks & drops)
    {
        "id": "impact_sub_drop",
        "category": "impact",
        "source_name": "Drop Disto Sub 1.wav",
        "description": "Heavy saturated sub-bass drop, ideal for 0.0s viral hook punch",
        "max_duration_sec": 1.2,
        "fade_out_sec": 0.40,
        "triggers": ["hook", "drop", "bass", "heavy", "shock", "ground"]
    },
    {
        "id": "impact_cinematic_boom",
        "category": "impact",
        "source_name": "Boom Big.wav",
        "description": "Massive cinematic explosion boom with low-end rumble",
        "max_duration_sec": 1.4,
        "fade_out_sec": 0.45,
        "triggers": ["boom", "explode", "blast", "shatter", "crisis", "disaster"]
    },
    {
        "id": "impact_punch_thud",
        "category": "impact",
        "source_name": "Vine Boom.mp3",
        "description": "Iconic crisp punch hit with immediate attack",
        "max_duration_sec": 1.0,
        "fade_out_sec": 0.30,
        "triggers": ["hit", "punch", "thud", "strike", "slam", "impact"]
    },

    # 3. Click Accents (tactile / UI / focus)
    {
        "id": "click_shutter_snap",
        "category": "click_accent",
        "source_name": "camera-shutter-6305.mp3",
        "description": "Crisp high-frequency camera snap, ideal for freeze-frames and key stats",
        "max_duration_sec": 0.4,
        "fade_out_sec": 0.10,
        "triggers": ["photo", "shutter", "snapshot", "picture", "frame", "look"]
    },
    {
        "id": "click_mouse_tactile",
        "category": "click_accent",
        "source_name": "Mouse Click.mp3",
        "description": "Subtle tactile click, ideal for UI highlights, buttons, and text pop",
        "max_duration_sec": 0.35,
        "fade_out_sec": 0.08,
        "triggers": ["click", "tap", "select", "press", "touch", "toggle"]
    },
    {
        "id": "click_mechanical",
        "category": "click_accent",
        "source_name": "camera shutter 2.mp3",
        "description": "Double mechanical click, ideal for tactile switches and steps",
        "max_duration_sec": 0.5,
        "fade_out_sec": 0.12,
        "triggers": ["switch", "lock", "gear", "step", "device", "button"]
    },

    # 4. Pop / Bubble (playful & biological)
    {
        "id": "pop_suction",
        "category": "pop_bubble",
        "source_name": "ES_Suction Pop 5 - SFX Producer.mp3",
        "description": "Clean suction pop, ideal for microscopic cells, detachment, liquids",
        "max_duration_sec": 0.6,
        "fade_out_sec": 0.15,
        "triggers": ["suction", "detach", "cell", "bacteria", "bubble", "pull"]
    },
    {
        "id": "pop_cork",
        "category": "pop_bubble",
        "source_name": "bottle cork.mp3",
        "description": "Hollow cork pop, ideal for releases, opens, bursts, bubbles",
        "max_duration_sec": 0.7,
        "fade_out_sec": 0.20,
        "triggers": ["cork", "open", "bottle", "burst", "release", "pop"]
    },
    {
        "id": "pop_bubble_clean",
        "category": "pop_bubble",
        "source_name": "Pop.mp3",
        "description": "Bright bubble pop, ideal for sudden appearances, icons, ideas",
        "max_duration_sec": 0.5,
        "fade_out_sec": 0.12,
        "triggers": ["idea", "appear", "spark", "dot", "molecule", "drop"]
    },

    # 5. Ding / Bell (stats, money, alert)
    {
        "id": "ding_service_bell",
        "category": "ding_bell",
        "source_name": "Ding 2.mp3",
        "description": "Crisp high metal bell chime, ideal for correct answers or revelations",
        "max_duration_sec": 0.7,
        "fade_out_sec": 0.20,
        "triggers": ["ding", "correct", "truth", "bell", "secret", "answer"]
    },
    {
        "id": "ding_cash_register",
        "category": "ding_bell",
        "source_name": "cash ting.mp3",
        "description": "Bright coin ting / cash register hit, ideal for money, price, profit",
        "max_duration_sec": 1.0,
        "fade_out_sec": 0.30,
        "triggers": ["money", "cash", "dollar", "cost", "rich", "profit", "value"]
    },
    {
        "id": "ding_modern_chime",
        "category": "ding_bell",
        "source_name": "Apple Notification.wav",
        "description": "Clean modern alert chime, ideal for notifications, messages, warnings",
        "max_duration_sec": 0.8,
        "fade_out_sec": 0.25,
        "triggers": ["alert", "notice", "ping", "message", "warning", "chime"]
    },

    # 6. Riser / Tension (suspense, builds)
    {
        "id": "riser_clock_tick",
        "category": "riser_tension",
        "source_name": "cartoon clock.mp3",
        "description": "Rapid rhythmic clock ticks, ideal for countdowns, time pressure, tests",
        "max_duration_sec": 0.9,
        "fade_out_sec": 0.15,
        "triggers": ["clock", "tick", "time", "seconds", "wait", "hurry"]
    },
    {
        "id": "riser_tension_build",
        "category": "riser_tension",
        "source_name": "BUILD-UP.mp3",
        "description": "Ascending pitch riser, ideal for building suspense before a climax",
        "max_duration_sec": 1.5,
        "fade_out_sec": 0.30,
        "triggers": ["build", "rise", "tension", "suspense", "climax", "danger"]
    },
    {
        "id": "riser_reverse_suction",
        "category": "riser_tension",
        "source_name": "ES_Riser Suction 5 - SFX Producer.mp3",
        "description": "Reverse whoosh suction tension, ideal for suspenseful zoom or draw-in",
        "max_duration_sec": 1.5,
        "fade_out_sec": 0.30,
        "triggers": ["draw", "pull", "vacuum", "reverse", "inward", "incoming"]
    }
]

def find_file(source_name: str) -> Path:
    for f in SFX_SOURCE_DIR.rglob("*"):
        if f.is_file() and f.name.lower() == source_name.lower():
            return f
    raise FileNotFoundError(f"Could not locate {source_name} in {SFX_SOURCE_DIR}")

def process_sfx():
    TARGET_SFX_BANK.mkdir(parents=True, exist_ok=True)
    catalog = {}

    print(f"=== Curating & Normalizing SFX Library into {TARGET_SFX_BANK} ===")

    for item in TARGET_FILES:
        sfx_id = item["id"]
        source_path = find_file(item["source_name"])
        target_wav = TARGET_SFX_BANK / f"{sfx_id}.wav"

        print(f"\nProcessing [{item['category']}] {sfx_id} from {source_path.name}...")

        # 1. Convert source to uncompressed 44.1kHz stereo WAV via temp
        temp_wav = TARGET_SFX_BANK / f"temp_{sfx_id}.wav"
        cmd_convert = [
            "ffmpeg", "-y",
            "-i", str(source_path),
            "-ar", "44100",
            "-ac", "2",
            "-sample_fmt", "s16",
            str(temp_wav)
        ]
        subprocess.run(cmd_convert, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 2. Load audio array
        data, sr = sf.read(str(temp_wav))
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

        # Convert to float32 if needed
        if data.dtype != np.float32 and data.dtype != np.float64:
            data = data.astype(np.float32)

        # Mono representation for envelope/peak detection
        mono = np.mean(data, axis=1) if len(data.shape) > 1 else data

        # 3. Trim leading silence (threshold: -45 dBFS = 0.0056)
        threshold = 0.005
        active_indices = np.where(np.abs(mono) > threshold)[0]
        if len(active_indices) > 0:
            start_idx = max(0, active_indices[0] - int(sr * 0.01)) # keep 10ms pre-roll
            data = data[start_idx:]
            mono = mono[start_idx:]

        # 4. Truncate & fade out to max_duration_sec
        max_samples = int(sr * item["max_duration_sec"])
        if len(data) > max_samples:
            data = data[:max_samples]
            mono = mono[:max_samples]

        fade_samples = int(sr * item["fade_out_sec"])
        if len(data) > fade_samples:
            fade_curve = np.linspace(1.0, 0.0, fade_samples)
            if len(data.shape) > 1:
                fade_curve = fade_curve[:, np.newaxis]
            data[-fade_samples:] *= fade_curve

        # 5. Peak Normalization to -1.0 dBFS (amplitude = 0.891)
        max_amp = np.max(np.abs(data))
        if max_amp > 1e-4:
            target_peak = 0.891
            data = (data / max_amp) * target_peak

        # 6. Re-calculate transient peak position
        mono = np.mean(data, axis=1) if len(data.shape) > 1 else data
        peak_idx = int(np.argmax(np.abs(mono)))
        peak_offset_ms = round((peak_idx / sr) * 1000, 1)
        duration_ms = round((len(data) / sr) * 1000, 1)

        # 7. Save normalized, trimmed 16-bit WAV
        sf.write(str(target_wav), data, sr, subtype="PCM_16")

        # 8. Record in catalog
        rel_path = str(target_wav.relative_to(PIPELINE_DATA_DIR.parent)).replace("\\", "/")
        catalog[sfx_id] = {
            "id": sfx_id,
            "category": item["category"],
            "filename": target_wav.name,
            "rel_path": rel_path,
            "full_path": str(target_wav),
            "duration_ms": duration_ms,
            "peak_offset_ms": peak_offset_ms,
            "description": item["description"],
            "triggers": item["triggers"]
        }

        print(f" -> Saved {target_wav.name} | Dur: {duration_ms}ms | Peak: {peak_offset_ms}ms")

    # Save master catalog
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"\n[SFX Curator] Successfully processed {len(catalog)} SFX files into {CATALOG_PATH}")

if __name__ == "__main__":
    process_sfx()
