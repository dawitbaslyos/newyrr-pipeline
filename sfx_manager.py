import os
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from config import Config

class SFXManager:
    """
    Manages and indexes local sound effects from the user's SFX folder:
    C:\\Users\\dawit\\Videos\\Editing Source\\Video SoundEffects
    
    Provides categorized SFX matching for:
    - Transition whooshes/swooshes between scenes
    - Hook punch/impact on Scene 1
    - Tactile accents (clicks, pops, shutters, dings) for specific visual moments
    - Tension risers and clock ticks
    """

    def __init__(self, sfx_dir: Optional[Path] = None):
        self.sfx_dir = Path(sfx_dir or Config.SFX_DIR)
        self.categories: Dict[str, List[Path]] = {
            "transitions": [],
            "impacts": [],
            "accents": [],
            "tension": []
        }
        self.all_files: List[Path] = []
        self._indexed = False
        self._index_library()

    def _index_library(self):
        if not self.sfx_dir.exists():
            print(f"[SFX Manager] Warning: SFX directory not found: {self.sfx_dir}")
            return

        extensions = {".wav", ".mp3", ".aac", ".ogg", ".flac", ".m4a"}
        for f in self.sfx_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in extensions:
                self.all_files.append(f)
                name = f.stem.lower()

                # Categorization keywords
                if any(w in name for w in ["whoosh", "swoosh", "transition", "rewind", "swipe", "wind", "sfx swoosh"]):
                    self.categories["transitions"].append(f)
                elif any(w in name for w in ["boom", "drop", "hit", "thud", "sub", "bass", "smash", "slam", "impact", "dark"]):
                    self.categories["impacts"].append(f)
                elif any(w in name for w in ["riser", "build", "tension", "clock", "tick", "ascending", "drum", "robo"]):
                    self.categories["tension"].append(f)
                else:
                    self.categories["accents"].append(f)

        self._indexed = True
        print(f"[SFX Manager] Indexed {len(self.all_files)} audio files: "
              f"{len(self.categories['transitions'])} transitions, "
              f"{len(self.categories['impacts'])} impacts, "
              f"{len(self.categories['accents'])} accents, "
              f"{len(self.categories['tension'])} tension.")

    def get_transition_sound(self) -> Optional[Path]:
        """Returns a crisp whoosh/swoosh for scene transitions."""
        if self.categories["transitions"]:
            return random.choice(self.categories["transitions"])
        return self.get_fallback()

    def get_hook_impact(self) -> Optional[Path]:
        """Returns a deep sub-bass boom or cinematic hit for the 0.0s viral hook."""
        if self.categories["impacts"]:
            # Prefer deep sub bass or boom
            booms = [p for p in self.categories["impacts"] if "boom" in p.name.lower() or "drop" in p.name.lower() or "sub" in p.name.lower()]
            if booms:
                return random.choice(booms)
            return random.choice(self.categories["impacts"])
        return self.get_fallback()

    def get_accent_sound(self, tag: Optional[str] = None) -> Optional[Path]:
        """Returns a click, pop, shutter, or ding."""
        if tag and self.categories["accents"]:
            matches = [p for p in self.categories["accents"] if tag.lower() in p.name.lower()]
            if matches:
                return random.choice(matches)
        if self.categories["accents"]:
            return random.choice(self.categories["accents"])
        return self.get_fallback()

    def get_fallback(self) -> Optional[Path]:
        if self.all_files:
            return random.choice(self.all_files)
        return None

    def match_sfx(self, cue_text: str) -> Optional[Path]:
        """
        Matches an LLM sfx cue string (e.g. 'high frequency hum and punch', 'bubble burst', 'shutter click')
        to the best matching local audio file.
        """
        if not cue_text or not self.all_files:
            return None

        clean_cue = re.sub(r"[^\w\s]", " ", cue_text.lower()).strip()
        cue_tokens = set(clean_cue.split())

        best_score = 0
        best_match = None

        # 1. Direct keyword match against filenames
        for sound_path in self.all_files:
            name_tokens = set(re.sub(r"[^\w\s]", " ", sound_path.stem.lower()).split())
            overlap = len(cue_tokens & name_tokens)
            if overlap > best_score:
                best_score = overlap
                best_match = sound_path

        if best_match and best_score >= 1:
            return best_match

        # 2. Semantic category fallback
        if any(w in cue_tokens for w in ["whoosh", "swoosh", "wipe", "swipe", "fly", "passing"]):
            return self.get_transition_sound()
        elif any(w in cue_tokens for w in ["boom", "hit", "punch", "drop", "thud", "slam", "impact", "shockwave", "explode"]):
            return self.get_hook_impact()
        elif any(w in cue_tokens for w in ["riser", "rise", "climax", "tension", "build", "countdown", "tick", "ticking"]):
            if self.categories["tension"]:
                return random.choice(self.categories["tension"])
        elif any(w in cue_tokens for w in ["click", "pop", "shutter", "ding", "bell", "cash", "coin", "snap", "boing", "bubble"]):
            # Check for specific accents
            for kw in ["click", "pop", "shutter", "ding", "bell", "boing"]:
                if kw in cue_tokens:
                    acc = self.get_accent_sound(kw)
                    if acc:
                        return acc
            return self.get_accent_sound()

        # Default to a subtle accent
        return self.get_accent_sound()

    def build_scene_sfx_cues(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Constructs an intelligent, non-bloated sound design timeline for all scenes:
        - Scene 1 gets a powerful Hook Impact (at 0.0s).
        - Scene transitions get a clean Whoosh (placed at scene transition boundaries).
        - Specific visual catalyst moments get an Accent SFX.
        - Strictly maintains 1-2 sounds max per scene to avoid meme-soundboard clutter.
        """
        sfx_timeline = []
        cumulative_time = 0.0

        for i, scene in enumerate(scenes):
            duration = float(scene.get("actual_audio_duration", scene.get("duration_seconds", 5.0)))
            cue_text = scene.get("sfx_cue", "")

            # 1. Scene 1 Viral Hook Impact
            if i == 0:
                hook_sound = self.get_hook_impact()
                if hook_sound:
                    sfx_timeline.append({
                        "file": str(hook_sound),
                        "offset_seconds": 0.0,
                        "volume": 0.40,
                        "type": "hook_impact"
                    })
            # 2. Transition Whoosh for subsequent scenes (fires right as scene cuts)
            elif i > 0:
                trans_sound = self.get_transition_sound()
                if trans_sound:
                    # Place whoosh 0.05s before transition for seamless visual sweep
                    trans_time = max(0.0, cumulative_time - 0.05)
                    sfx_timeline.append({
                        "file": str(trans_sound),
                        "offset_seconds": trans_time,
                        "volume": 0.28,
                        "type": "transition"
                    })

            # 3. Key Moment Accent SFX (if specified in scene narration/cue)
            matched_sfx = self.match_sfx(cue_text)
            if matched_sfx and (i > 0 or matched_sfx != hook_sound):
                # Place accent at ~1.2s into the scene (where catalyst happens)
                accent_time = cumulative_time + min(1.2, duration * 0.3)
                sfx_timeline.append({
                    "file": str(matched_sfx),
                    "offset_seconds": accent_time,
                    "volume": 0.32,
                    "type": "moment_accent"
                })

            cumulative_time += duration

        return sfx_timeline

sfx_manager = SFXManager()
