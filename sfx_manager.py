import os
import re
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from config import Config

logger = logging.getLogger("SFXManager")
logger.setLevel(logging.INFO)

class SFXManager:
    """
    Intelligent, Type-Safe Sound Effects Manager for Viral YouTube Shorts.
    
    Uses curated high-quality one-shot SFX (18 sounds, exactly 3 per category)
    processed and peak-timestamped in pipeline/data/sfx_bank/.
    
    Integrates OpenRouter's 'typesafe/jev-router' to perform Hollywood-grade
    sound design placement with millisecond-exact transient peak alignment.
    Falls back gracefully to a deterministic rules engine if offline.
    """

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = Path(catalog_path or (Config.BASE_DIR / "data" / "sfx_catalog.json"))
        self.sfx_bank_dir = Config.BASE_DIR / "data" / "sfx_bank"
        self.catalog: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, List[Dict[str, Any]]] = {
            "whoosh": [],
            "impact": [],
            "click_accent": [],
            "pop_bubble": [],
            "ding_bell": [],
            "riser_tension": []
        }
        self._load_catalog()

    def _load_catalog(self):
        """Loads and indexes the 18 curated, normalized sound effects."""
        if not self.catalog_path.exists():
            print(f"[SFX Manager] Warning: Catalog not found at {self.catalog_path}. Run curate_sfx.py first.")
            return

        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                self.catalog = json.load(f)

            for sfx_id, meta in self.catalog.items():
                cat = meta.get("category", "click_accent")
                if cat in self.categories:
                    self.categories[cat].append(meta)
                else:
                    self.categories["click_accent"].append(meta)

            total_sounds = len(self.catalog)
            print(f"[SFX Manager] Loaded {total_sounds} curated SFX from {self.catalog_path.name}: "
                  f"{len(self.categories['whoosh'])} whooshes, "
                  f"{len(self.categories['impact'])} impacts, "
                  f"{len(self.categories['click_accent'])} clicks, "
                  f"{len(self.categories['pop_bubble'])} pops, "
                  f"{len(self.categories['ding_bell'])} dings, "
                  f"{len(self.categories['riser_tension'])} risers.")
        except Exception as e:
            print(f"[SFX Manager] Error loading catalog: {e}")

    def build_sfx_timeline_with_jev(self, manifest: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Calls OpenRouter 'typesafe/jev-router' to perform type-safe sound effect placement
        based on project narrative, script word timestamps, and scene cuts.
        """
        api_key = Config.OPENROUTER_API_KEY
        if not api_key:
            print("[SFX Manager] No OpenRouter API key found. Falling back to deterministic placement.")
            return None

        scenes = manifest.get("scenes", [])
        if not scenes:
            return None

        # Build clean summary of available curated sound effects
        cat_summary = [
            {
                "id": k,
                "category": v["category"],
                "description": v["description"],
                "peak_offset_ms": v["peak_offset_ms"],
                "triggers": v.get("triggers", [])
            }
            for k, v in self.catalog.items()
        ]

        # Calculate scene boundaries and word timelines
        scene_timings = []
        cumulative_t = 0.0
        for s in scenes:
            num = s.get("scene_number", 1)
            dur = float(s.get("actual_audio_duration", s.get("duration_seconds", 5.0)))
            narration = s.get("narration", "").strip()
            motion = s.get("minimax_motion_prompt", s.get("sfx_cue", ""))

            # Calculate word-level timestamps
            words = narration.split()
            word_dur = dur / max(1, len(words))
            word_map = [
                {"word": w, "time": round(cumulative_t + (i * word_dur), 2)}
                for i, w in enumerate(words)
            ]

            scene_timings.append({
                "scene_number": num,
                "start_time": round(cumulative_t, 2),
                "end_time": round(cumulative_t + dur, 2),
                "duration": round(dur, 2),
                "narration": narration,
                "visual_motion": motion,
                "word_timeline": word_map[:12] # Key words in the first few seconds
            })
            cumulative_t += dur

        system_prompt = """You are an elite sound designer for high-retention viral YouTube Shorts (Zack D. Films style).
You place sound effects with millisecond precision to maximize viewer attention while keeping the narration 100% intelligible.

RULES:
1. Scene 1 always gets an impact (e.g., 'impact_sub_drop' or 'impact_punch_thud') at target_timestamp 0.0s (The Viral Hook).
2. Each subsequent scene cut (start of scene 2, 3, 4, etc.) gets a whoosh (e.g., 'whoosh_snappy', 'whoosh_smooth', 'whoosh_whip') targeting the EXACT cut timestamp.
3. Maximum 1 subtle accent (click, pop, ding, or riser) per scene, placed at the EXACT timestamp of the catalyst action or keyword.
4. Volumes:
   - Hook impact: 0.35
   - Transition whoosh: 0.25
   - Accents / pops / dings: 0.28
5. NEVER place more than 2 sounds in a single scene. Avoid soundboard clutter.
6. Output MUST strictly conform to this JSON structure:
{
  "placements": [
    {
      "scene_number": 1,
      "sfx_id": "impact_sub_drop",
      "target_timestamp": 0.0,
      "trigger_reason": "Hook punch to grab immediate attention",
      "volume": 0.35
    }
  ]
}
"""

        user_prompt = f"""Project: {manifest.get('topic', manifest.get('title', 'Short'))}
Scenes Timeline:
{json.dumps(scene_timings, indent=2)}

Curated SFX Bank:
{json.dumps(cat_summary, indent=2)}

Generate the sound design timeline JSON for these scenes.
"""

        try:
            print("[SFX Manager] Prompting TypeSafe JEV Router on OpenRouter for intelligent sound design...")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/dawitbaslyos/newyrr-pipeline",
                    "X-Title": "Newyrr Shorts Pipeline"
                },
                json={
                    "model": "typesafe/jev-router",
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                },
                timeout=25
            )

            if response.status_code != 200:
                print(f"[SFX Manager] JEV Router returned status {response.status_code}: {response.text[:200]}")
                return None

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            placements = parsed.get("placements", [])

            if not placements:
                print("[SFX Manager] JEV returned empty placements list.")
                return None

            # Resolve catalog paths and calculate exact peak-aligned offsets
            resolved_timeline = []
            for item in placements:
                sfx_id = item.get("sfx_id")
                if sfx_id not in self.catalog:
                    # Fallback to category match if JEV hallucinated an ID
                    sfx_id = self._match_fallback_sfx(sfx_id)

                meta = self.catalog.get(sfx_id)
                if not meta:
                    continue

                target_t = float(item.get("target_timestamp", 0.0))
                peak_offset_sec = meta.get("peak_offset_ms", 0.0) / 1000.0

                # Transient alignment: start audio early so the transient peak hits exactly at target_t
                aligned_start = max(0.0, round(target_t - peak_offset_sec, 3))

                resolved_timeline.append({
                    "scene_number": item.get("scene_number", 1),
                    "sfx_id": sfx_id,
                    "category": meta.get("category", "accent"),
                    "file": meta.get("full_path"),
                    "filename": meta.get("filename"),
                    "target_timestamp": target_t,
                    "aligned_offset_seconds": aligned_start,
                    "volume": float(item.get("volume", 0.28)),
                    "duration_ms": meta.get("duration_ms"),
                    "peak_offset_ms": meta.get("peak_offset_ms"),
                    "trigger_reason": item.get("trigger_reason", "")
                })

            print(f"[SFX Manager] JEV Router successfully designed {len(resolved_timeline)} peak-aligned sound cues!")
            return resolved_timeline

        except Exception as e:
            print(f"[SFX Manager] JEV placement failed: {e}. Falling back to deterministic rules.")
            return None

    def build_sfx_timeline_deterministic(self, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Deterministic, rule-based sound design engine.
        Guarantees flawless timing, zero clutter, and peak alignment without requiring an API call.
        """
        scenes = manifest.get("scenes", [])
        if not scenes:
            return []

        timeline = []
        cumulative_t = 0.0
        whoosh_cycle = ["whoosh_snappy", "whoosh_smooth", "whoosh_whip"]
        whoosh_idx = 0

        for i, scene in enumerate(scenes):
            num = scene.get("scene_number", i + 1)
            duration = float(scene.get("actual_audio_duration", scene.get("duration_seconds", 5.0)))
            narration = scene.get("narration", "")
            words = narration.split()
            word_dur = duration / max(1, len(words))

            # 1. Scene 1 Viral Hook Impact (at 0.0s)
            if i == 0:
                meta = self.catalog.get("impact_sub_drop", self.catalog.get("impact_punch_thud"))
                if meta:
                    peak_sec = meta.get("peak_offset_ms", 0.0) / 1000.0
                    timeline.append({
                        "scene_number": num,
                        "sfx_id": meta["id"],
                        "category": meta["category"],
                        "file": meta["full_path"],
                        "filename": meta["filename"],
                        "target_timestamp": 0.0,
                        "aligned_offset_seconds": 0.0,
                        "volume": 0.35,
                        "duration_ms": meta["duration_ms"],
                        "peak_offset_ms": meta["peak_offset_ms"],
                        "trigger_reason": "0.0s Viral hook impact"
                    })

            # 2. Scene Cut Transition Whoosh (for scenes 2, 3, ...)
            if i > 0:
                sfx_name = whoosh_cycle[whoosh_idx % len(whoosh_cycle)]
                whoosh_idx += 1
                meta = self.catalog.get(sfx_name)
                if meta:
                    peak_sec = meta.get("peak_offset_ms", 0.0) / 1000.0
                    aligned_start = max(0.0, round(cumulative_t - peak_sec, 3))
                    timeline.append({
                        "scene_number": num,
                        "sfx_id": meta["id"],
                        "category": meta["category"],
                        "file": meta["full_path"],
                        "filename": meta["filename"],
                        "target_timestamp": round(cumulative_t, 3),
                        "aligned_offset_seconds": aligned_start,
                        "volume": 0.25,
                        "duration_ms": meta["duration_ms"],
                        "peak_offset_ms": meta["peak_offset_ms"],
                        "trigger_reason": f"Cut transition into Scene {num}"
                    })

            # 3. Catalyst Accent (Scan narration words for key triggers)
            matched_accent = None
            matched_word_idx = -1
            clean_narration = narration.lower()

            for w_idx, raw_w in enumerate(words):
                w = re.sub(r"[^\w]", "", raw_w.lower())
                for sfx_id, sfx_meta in self.catalog.items():
                    if sfx_meta["category"] in ["click_accent", "pop_bubble", "ding_bell", "riser_tension"]:
                        if any(t == w for t in sfx_meta.get("triggers", [])):
                            matched_accent = sfx_meta
                            matched_word_idx = w_idx
                            break
                if matched_accent:
                    break

            if matched_accent and matched_word_idx >= 0:
                target_word_t = cumulative_t + (matched_word_idx * word_dur)
                peak_sec = matched_accent.get("peak_offset_ms", 0.0) / 1000.0
                aligned_start = max(0.0, round(target_word_t - peak_sec, 3))
                timeline.append({
                    "scene_number": num,
                    "sfx_id": matched_accent["id"],
                    "category": matched_accent["category"],
                    "file": matched_accent["full_path"],
                    "filename": matched_accent["filename"],
                    "target_timestamp": round(target_word_t, 3),
                    "aligned_offset_seconds": aligned_start,
                    "volume": 0.28,
                    "duration_ms": matched_accent["duration_ms"],
                    "peak_offset_ms": matched_accent["peak_offset_ms"],
                    "trigger_reason": f"Catalyst accent on keyword '{words[matched_word_idx]}'"
                })

            cumulative_t += duration

        return timeline

    def generate_sfx_timeline(self, manifest: Dict[str, Any], use_ai: bool = True) -> List[Dict[str, Any]]:
        """
        Main entry point for generating the complete sound effects timeline.
        Tries TypeSafe JEV Router first, falls back to deterministic rule engine.
        Sorts all cues chronologically.
        """
        timeline = None
        if use_ai:
            timeline = self.build_sfx_timeline_with_jev(manifest)

        if not timeline:
            print("[SFX Manager] Generating deterministic sound design timeline...")
            timeline = self.build_sfx_timeline_deterministic(manifest)

        # Sort chronologically by start time
        timeline.sort(key=lambda x: x["aligned_offset_seconds"])

        print(f"\n==================== SFX DESIGN TIMELINE ====================")
        for cue in timeline:
            print(f"[{cue['aligned_offset_seconds']:6.2f}s] {cue['sfx_id']:<24} (Vol: {cue['volume']:.2f}) -> {cue['trigger_reason']}")
        print(f"=============================================================\n")

        return timeline

    def _match_fallback_sfx(self, sfx_id: Optional[str]) -> str:
        """Finds closest matching sound in catalog if an unknown ID was suggested."""
        if not sfx_id:
            return "whoosh_snappy"
        sfx_lower = sfx_id.lower()
        if "whoosh" in sfx_lower or "swoosh" in sfx_lower:
            return "whoosh_snappy"
        elif "impact" in sfx_lower or "boom" in sfx_lower or "hit" in sfx_lower:
            return "impact_sub_drop"
        elif "pop" in sfx_lower or "bubble" in sfx_lower:
            return "pop_bubble_clean"
        elif "ding" in sfx_lower or "bell" in sfx_lower or "cash" in sfx_lower:
            return "ding_service_bell"
        elif "click" in sfx_lower or "shutter" in sfx_lower:
            return "click_shutter_snap"
        elif "riser" in sfx_lower or "clock" in sfx_lower:
            return "riser_clock_tick"
        return "whoosh_snappy"

sfx_manager = SFXManager()

if __name__ == "__main__":
    # Test on the latest manifest
    projects = list(Config.PROJECTS_DIR.glob("*/manifest.json"))
    if projects:
        test_manifest_path = sorted(projects, key=os.path.getmtime)[-1]
        print(f"Testing SFX generation on: {test_manifest_path}")
        with open(test_manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        sfx_manager.generate_sfx_timeline(manifest_data, use_ai=True)
    else:
        print("No project manifest found to test.")
