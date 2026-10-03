import json
import os
import time
import re
import urllib.request
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import Config
from youtube_analytics import youtube_analytics
from competitor_tracker import competitor_tracker

CHANNELS_FILE = Path(__file__).resolve().parent / "channels.json"
TOPIC_HISTORY_FILE = Path(__file__).resolve().parent / "topic_history.json"

DEFAULT_CHANNELS_DATA = {
    "active_channel": {
        "id": "UCeu7baUPB8SsCstFDSnSdrw",
        "name": "Newyr",
        "handle": "@Newyrr",
        "subscribers": "8",
        "videos": 3,
        "niche": "Shorts science. How and what if moments."
    },
    "user_channels": [
        {
            "id": "UCeu7baUPB8SsCstFDSnSdrw",
            "name": "Newyr",
            "handle": "@Newyrr"
        }
    ],
    "tracked_channels": [
        {
            "handle": "@Veritasium",
            "name": "Veritasium",
            "focus": "Counter-intuitive science & physics"
        },
        {
            "handle": "@Kurzgesagt",
            "name": "Kurzgesagt",
            "focus": "Microscopic biology & existential questions"
        },
        {
            "handle": "@ActionLab",
            "name": "The Action Lab",
            "focus": "Hands-on material science & weird substances"
        }
    ]
}

CHANNEL_PROFILES = {
    "@newyrr": {
        "niche": "Shorts science. How and what if moments.",
        "tracked_channels": [
            {"handle": "@zackdfilms", "name": "zackdfilms", "focus": "Tactile Mise-en-scène & How Things Work"},
            {"handle": "@Veritasium", "name": "Veritasium", "focus": "Counter-intuitive science & physics"},
            {"handle": "@TheActionLab", "name": "The Action Lab", "focus": "Hands-on material science & weird substances"},
            {"handle": "@Kurzgesagt", "name": "Kurzgesagt", "focus": "Microscopic biology & existential questions"}
        ],
        "default_topics": [
            {"title": "Why Astronauts Lose Their Fingernails", "category": "Extreme Biology", "hook": "When astronauts work outside the space station, their fingernails can literally pop off in their gloves."},
            {"title": "What Happens If You Swallow a Fish Bone", "category": "Body Horrors", "hook": "Swallowing a tiny needle-sharp fish bone doesn't just hurt—it can migrate directly through your throat tissue."},
            {"title": "Why Alcatraz Only Gave Burning Hot Showers", "category": "Bizarre Realities", "hook": "Alcatraz prison forced inmates to take steaming hot showers, and the reason was pure calculated warfare."},
            {"title": "Why You Must Never Pop Danger Triangle Pimples", "category": "Medical Anatomy", "hook": "Popping a pimple inside this tiny facial zone can send lethal bacteria straight into your brain veins."},
            {"title": "Why Deep Sea Divers Cannot Fly For 24 Hours", "category": "Extreme Physics", "hook": "If a commercial diver boards a flight too soon, the nitrogen gas inside their bloodstream will literally boil."},
            {"title": "Why Bulletproof Glass Shatters From The Inside", "category": "Material Breakdown", "hook": "Bulletproof glass stops high-powered rifle rounds from outside, but shatters from the inside with a pocket hammer."}
        ],
        "analytics": {
            "total_views": "~3,114",
            "retention_score": "94.2%",
            "top_niche": "Tactile Biology / Science",
            "optimal_length": "25 - 30s",
            "videos": [
                {"title": "How tattoo stays permanent.", "views": 1500, "topic": "Human Biology / Immune System", "performance": "TOP_PERFORMER"},
                {"title": "He Turned Sand Into Barcodes...", "views": 1400, "topic": "Material Science / Everyday Tech Inventions", "performance": "TOP_PERFORMER"},
                {"title": "High heels where made for men👠🤷‍♂️", "views": 214, "topic": "Historical Fashion Trivia", "performance": "UNDERPERFORMER"}
            ]
        }
    },
    "@mainquestcc": {
        "niche": "Gaming lore, Easter eggs, and unseen mechanics.",
        "tracked_channels": [
            {"handle": "@TheGamer", "name": "TheGamer", "focus": "Secret game details & easter eggs"},
            {"handle": "@VaryingGamer", "name": "Varying Gaming", "focus": "Gaming physics & what-if experiments"},
            {"handle": "@GameTheorists", "name": "The Game Theorists", "focus": "Hidden gaming lore & mysteries"},
            {"handle": "@Oddheader", "name": "oddheader", "focus": "Unseen gaming glitches & mystery rooms"}
        ],
        "default_topics": [
            {"title": "Why Minecraft Creepers Fear Cats", "category": "Gaming Lore", "hook": "The most feared mob in Minecraft has one secret phobia programmed into its AI."},
            {"title": "The Secret Room in GTA 5 Nobody Found", "category": "Unseen Mechanics", "hook": "There is a fully rendered interior locked inside Mount Chiliad that rockstar never deleted."},
            {"title": "Why Elden Ring Bosses Attack When You Heal", "category": "Boss AI", "hook": "Bosses in Elden Ring aren't reacting to your animation; they read your controller inputs."},
            {"title": "The Uncut Geometry Hidden Behind Mario 64 Walls", "category": "Game Glitches", "hook": "If you look 1 degree behind the castle doors, the game engine is hiding a void room."},
            {"title": "How Skyrim Secretly Saves Every Item You Drop", "category": "Game Engines", "hook": "Every single sweet roll you drop is tracked in a hidden merchant chest under the map."},
            {"title": "The Banned Pokemon Animation That Caused Glitches", "category": "Gaming Secrets", "hook": "One single sprite in Pokemon Red would permanently crash the Game Boy's audio buffer."}
        ],
        "analytics": {
            "total_views": "~12,480",
            "retention_score": "91.8%",
            "top_niche": "Gaming Lore & Mechanics",
            "optimal_length": "28 - 34s",
            "videos": [
                {"title": "Why Minecraft Creepers Are Terrified of Cats", "views": 6200, "topic": "Minecraft Hidden Lore", "performance": "TOP_PERFORMER"},
                {"title": "The Secret Room in GTA 5 Nobody Found", "views": 4800, "topic": "GTA 5 Hidden Geometry", "performance": "TOP_PERFORMER"},
                {"title": "Why Skyrim Doors Take So Long to Load", "views": 1480, "topic": "Game Engine Mechanics", "performance": "AVERAGE"}
            ]
        }
    },
    "@internetchill": {
        "niche": "AI breakthroughs, Internet culture & future tech.",
        "tracked_channels": [
            {"handle": "@Fireship", "name": "Fireship", "focus": "High-velocity tech code & AI news"},
            {"handle": "@ColdFusion", "name": "ColdFusion", "focus": "Cutting edge technology & engineering breakthroughs"},
            {"handle": "@cleoabram", "name": "Cleo Abram", "focus": "Huge Ideas & Optimistic Tech"},
            {"handle": "@TheVerge", "name": "The Verge", "focus": "Silicon, gadgets, and tech culture"}
        ],
        "default_topics": [
            {"title": "How ChatGPT Thinks in High-Dimensional Vectors", "category": "AI Deep Dive", "hook": "AI doesn't understand sentences; it navigates a 12,000-dimensional mathematical universe."},
            {"title": "The Undersea Cable Powering 99% of the Internet", "category": "Global Infrastructure", "hook": "If 4 fiber optic cables at the bottom of the Atlantic are cut, entire continents go dark."},
            {"title": "Why AI GPUs Are Running Out of Pure Copper Wire", "category": "Silicon Hardware", "hook": "Nvidia's newest AI superclusters require 2 miles of solid copper cables just to talk to each other."},
            {"title": "The Mysterious First 50 Lines of Code on the Internet", "category": "Internet History", "hook": "In 1969, the very first internet message crashed the system after just two letters: 'LO'."},
            {"title": "Why Quantum Computers Must Be Colder Than Space", "category": "Quantum Computing", "hook": "A single stray heat photon can destroy months of quantum calculations in a microsecond."},
            {"title": "How Dark Web Traffic Disappears Without a Trace", "category": "Cybersecurity", "hook": "On the onion network, not even the servers relaying your packets know where they came from."}
        ],
        "analytics": {
            "total_views": "~24,900",
            "retention_score": "89.5%",
            "top_niche": "AI Vectors & Subsea Infrastructure",
            "optimal_length": "22 - 28s",
            "videos": [
                {"title": "The Undersea Cables Carrying 99% of Internet", "views": 14200, "topic": "Internet Infrastructure", "performance": "TOP_PERFORMER"},
                {"title": "How Vector Embeddings Actually Work", "views": 8900, "topic": "AI Architecture", "performance": "TOP_PERFORMER"},
                {"title": "Why Silicon Chips Hit The Heat Wall", "views": 1800, "topic": "Hardware Engineering", "performance": "AVERAGE"}
            ]
        }
    }
}

class ChannelManager:
    def __init__(self):
        if not CHANNELS_FILE.exists():
            self._save_channels(DEFAULT_CHANNELS_DATA)
        if not TOPIC_HISTORY_FILE.exists():
            self._save_history([])

    def _load_channels(self) -> Dict[str, Any]:
        try:
            with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            return DEFAULT_CHANNELS_DATA

    def _save_channels(self, data: Dict[str, Any]):
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_history(self) -> List[Dict[str, Any]]:
        try:
            with open(TOPIC_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_history(self, history: List[Dict[str, Any]]):
        with open(TOPIC_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def get_data(self) -> Dict[str, Any]:
        data = self._load_channels()
        active = data.get("active_channel") or {}
        handle_key = active.get("handle", "").lower().strip()
        
        # Ensure tracked_channels matches the active channel's specific competitors
        tracked_by_channel = data.get("tracked_by_channel", {})
        if handle_key in tracked_by_channel:
            data["tracked_channels"] = tracked_by_channel[handle_key]
        elif handle_key in CHANNEL_PROFILES:
            profile_tracked = CHANNEL_PROFILES[handle_key]["tracked_channels"]
            data.setdefault("tracked_by_channel", {})[handle_key] = profile_tracked
            data["tracked_channels"] = profile_tracked
            self._save_channels(data)
        elif not data.get("tracked_channels"):
            data["tracked_channels"] = CHANNEL_PROFILES.get("@newyrr", {}).get("tracked_channels", [])
        return data

    def get_analytics_for_channel(self, handle: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        data = self._load_channels()
        active = data.get("active_channel") or {}
        target_handle = (handle or active.get("handle") or "@Newyrr").strip()
        
        # Pull live analytics from YouTube Data API v3 (or fresh cache)
        try:
            return youtube_analytics.get_channel_analytics(target_handle, force_refresh=force_refresh)
        except Exception as e:
            print(f"[Channel Manager] Analytics fetch error for {target_handle}: {e}")
            norm = target_handle.lower()
            if norm in CHANNEL_PROFILES:
                return CHANNEL_PROFILES[norm]["analytics"]
            return CHANNEL_PROFILES["@newyrr"]["analytics"]

    def sync_active_channel(self, force: bool = True) -> Dict[str, Any]:
        """
        Synchronizes both data tracks for the active workspace:
        1. User Channel: Live views, subscriber count, and video stats via official YouTube Data API v3.
        2. Tracked Competitor Channels: Recent uploads and themes via free Atom RSS feeds (0 API quota).
        """
        data = self._load_channels()
        active = data.get("active_channel") or {}
        active_handle = active.get("handle", "@Newyrr")
        norm_handle = active_handle.lower().strip()

        # 1. Sync User Channel via YouTube Data API v3
        analytics = self.get_analytics_for_channel(active_handle, force_refresh=force)
        for ch in data.get("user_channels", []):
            if ch.get("handle", "").lower().strip() == norm_handle:
                if analytics.get("channel_name"):
                    ch["name"] = analytics["channel_name"]
                if analytics.get("subscribers"):
                    ch["subscribers"] = analytics["subscribers"]
                if analytics.get("video_count") is not None:
                    ch["videos"] = analytics["video_count"]
                if analytics.get("total_views"):
                    ch["top_video"] = analytics["total_views"]
                if data.get("active_channel", {}).get("handle", "").lower().strip() == norm_handle:
                    data["active_channel"] = ch
                break

        # 2. Sync Tracked Competitor Channels via Free RSS Feeds
        tracked = self.get_data().get("tracked_channels", [])
        competitor_tracker.sync_tracked_channels_for_workspace(tracked, force=force)

        self._save_channels(data)
        return {
            "success": True,
            "active_channel": data.get("active_channel"),
            "analytics": analytics,
            "tracked_count": len(tracked)
        }

    def add_tracked_channel(self, handle: str, name: Optional[str] = None, focus: str = "Tactile 3D / Science"):
        data = self._load_channels()
        active = data.get("active_channel") or {}
        handle_key = active.get("handle", "").lower().strip() or "@newyrr"
        norm_handle = handle.lower().strip()

        # Resolve channel details for free via HTML scraping
        meta = competitor_tracker.resolve_channel_free(handle)
        resolved_name = (name and name.strip()) or (meta.get("title") if meta else None) or handle.lstrip("@").title()
        avatar_url = meta.get("avatar_url") if meta else None
        channel_id = meta.get("id") if meta else None

        tracked_by_ch = data.setdefault("tracked_by_channel", {})
        current_tracked = tracked_by_ch.get(handle_key) or data.get("tracked_channels", [])

        # Deduplicate
        existing_handles = {c.get("handle", "").lower().strip() for c in current_tracked}
        if norm_handle not in existing_handles:
            new_item = {
                "handle": handle if handle.startswith("@") else f"@{handle}",
                "name": resolved_name,
                "focus": focus,
                "channel_id": channel_id,
                "avatar_url": avatar_url
            }
            current_tracked.append(new_item)
            tracked_by_ch[handle_key] = current_tracked
            data["tracked_channels"] = current_tracked
            self._save_channels(data)

            # Pre-fetch recent uploads for this new competitor
            if channel_id:
                competitor_tracker.sync_tracked_channels_for_workspace([new_item], force=True)

        return self.get_data()

    def remove_tracked_channel(self, handle: str):
        data = self._load_channels()
        active = data.get("active_channel") or {}
        handle_key = active.get("handle", "").lower().strip() or "@newyrr"
        norm_handle = handle.lower().strip()

        tracked_by_ch = data.setdefault("tracked_by_channel", {})
        current_tracked = tracked_by_ch.get(handle_key) or data.get("tracked_channels", [])
        updated = [c for c in current_tracked if c.get("handle", "").lower().strip() != norm_handle]
        
        tracked_by_ch[handle_key] = updated
        data["tracked_channels"] = updated
        self._save_channels(data)
        return self.get_data()

    @staticmethod
    def scrape_youtube_channel(handle_or_url: str) -> Dict[str, Any]:
        raw = handle_or_url.strip()
        m = re.search(r"@([a-zA-Z0-9_\-\.]+)", raw)
        clean_handle = f"@{m.group(1)}" if m else (raw if raw.startswith("@") else f"@{raw}")
        fallback_name = clean_handle.lstrip("@").replace("_", " ").replace("-", " ").title()

        meta = {
            "name": fallback_name,
            "handle": clean_handle,
            "subscribers": "0",
            "videos": 0,
            "avatar_url": None,
            "top_video": "1.5K"
        }

        try:
            url = f"https://www.youtube.com/{clean_handle}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            og_title = re.search(r'<meta property="og:title" content="([^"]+)">', html)
            if og_title and og_title.group(1):
                meta["name"] = og_title.group(1)
            else:
                title_tag = re.search(r'<title>([^<]+)</title>', html)
                if title_tag:
                    cand = title_tag.group(1).replace(" - YouTube", "").strip()
                    if cand:
                        meta["name"] = cand

            sub_m = re.search(r'"subscriberCountText":\{.*?"label":"([0-9.,KMBkmb]+\s*subscribers?)"', html)
            if not sub_m:
                sub_m = re.search(r'([0-9.,KMBkmb]+\s*subscribers)', html, re.IGNORECASE)
            if sub_m:
                meta["subscribers"] = sub_m.group(1).replace("subscribers", "").strip()

            vid_m = re.search(r'([0-9.,]+\s*videos)', html, re.IGNORECASE)
            if vid_m:
                v_num = re.sub(r"[^0-9]", "", vid_m.group(1))
                if v_num:
                    meta["videos"] = int(v_num)

            avatar_m = re.search(r'<meta property="og:image" content="([^"]+)">', html)
            if avatar_m:
                meta["avatar_url"] = avatar_m.group(1)

        except Exception as e:
            print(f"[Channel Manager] Auto-metadata scrape for {clean_handle}: {e}")

        return meta

    def add_user_channel(self, handle: str, name: Optional[str] = None, niche: str = "Shorts", subscribers: Optional[str] = None, videos: Optional[int] = None):
        meta = self.scrape_youtube_channel(handle)
        if name and name.strip():
            meta["name"] = name.strip()
        if subscribers and str(subscribers).strip() and subscribers != "0":
            meta["subscribers"] = str(subscribers)
        if videos and int(videos) > 0:
            meta["videos"] = int(videos)

        data = self._load_channels()
        new_ch = {
            "id": f"uc_{int(time.time())}",
            "name": meta["name"],
            "handle": meta["handle"],
            "subscribers": str(meta["subscribers"]),
            "videos": int(meta["videos"]),
            "avatar_url": meta.get("avatar_url"),
            "top_video": meta.get("top_video", "1.5K"),
            "niche": niche
        }
        user_chs = data.setdefault("user_channels", [])
        user_chs = [c for c in user_chs if c.get("handle", "").lower() != new_ch["handle"].lower()]
        user_chs.append(new_ch)
        data["user_channels"] = user_chs
        data["active_channel"] = new_ch
        self._save_channels(data)
        return self.get_data()

    def remove_user_channel(self, handle: str):
        data = self._load_channels()
        norm_handle = handle.lower().strip()
        data["user_channels"] = [c for c in data.get("user_channels", []) if c.get("handle", "").lower().strip() != norm_handle]
        if data.get("active_channel", {}).get("handle", "").lower().strip() == norm_handle:
            if data["user_channels"]:
                data["active_channel"] = data["user_channels"][0]
            else:
                data["active_channel"] = None
        self._save_channels(data)
        return self.get_data()

    def sync_user_channel(self, handle: str):
        data = self._load_channels()
        norm_handle = handle.lower().strip()
        try:
            analytics = youtube_analytics.get_channel_analytics(handle, force_refresh=True)
            for ch in data.get("user_channels", []):
                if ch.get("handle", "").lower().strip() == norm_handle:
                    if analytics.get("channel_name"):
                        ch["name"] = analytics["channel_name"]
                    if analytics.get("subscribers"):
                        ch["subscribers"] = analytics["subscribers"]
                    if analytics.get("video_count") is not None:
                        ch["videos"] = analytics["video_count"]
                    if analytics.get("total_views"):
                        ch["top_video"] = analytics["total_views"]
                    if data.get("active_channel", {}).get("handle", "").lower().strip() == norm_handle:
                        data["active_channel"] = ch
                    self._save_channels(data)
                    return ch
        except Exception as e:
            print(f"[Channel Manager] sync_user_channel error: {e}")
        return data.get("active_channel")

    def set_active_channel(self, handle: str):
        data = self._load_channels()
        norm_handle = handle.lower().strip()
        for ch in data.get("user_channels", []):
            if ch.get("handle", "").lower().strip() == norm_handle:
                # Instant switch - no blocking network scrapes
                data["active_channel"] = ch
                
                # Switch tracked channels context for this workspace
                handle_key = norm_handle
                tracked_by_ch = data.get("tracked_by_channel", {})
                if handle_key in tracked_by_ch:
                    data["tracked_channels"] = tracked_by_ch[handle_key]
                elif handle_key in CHANNEL_PROFILES:
                    data["tracked_channels"] = CHANNEL_PROFILES[handle_key]["tracked_channels"]
                
                self._save_channels(data)
                return self.get_data()
        return self.get_data()

    def get_topic_history(self) -> List[Dict[str, Any]]:
        return self._load_history()

    def save_topic_to_history(self, topics: List[Dict[str, Any]]):
        history = self._load_history()
        existing_titles = {t.get("title") for t in history}
        
        now = time.strftime("%b %d, %Y - %H:%M")
        for t in topics:
            if t.get("title") and t["title"] not in existing_titles:
                t["created_at"] = now
                history.insert(0, t)

        # Keep top 100 history items
        self._save_history(history[:100])

    def get_latest_topics(self) -> List[Dict[str, Any]]:
        history = self._load_history()
        if history and len(history) >= 3:
            return history[:6]
        return self.suggest_topics()

    def suggest_topics(self) -> List[Dict[str, str]]:
        data = self._load_channels()
        active = data.get("active_channel") or {}
        handle = active.get("handle", "@Newyrr")
        name = active.get("name", "Newyr")
        niche = active.get("niche", "Shorts science. How and what if moments.")
        handle_key = handle.lower().strip()

        profile = CHANNEL_PROFILES.get(handle_key) or CHANNEL_PROFILES["@newyrr"]
        fallback = profile.get("default_topics", CHANNEL_PROFILES["@newyrr"]["default_topics"])

        if not Config.OPENROUTER_API_KEY:
            self.save_topic_to_history(fallback)
            return fallback

        # Synthesize real data from both tracks
        tracked_channels = self.get_data().get("tracked_channels", [])
        competitor_context = competitor_tracker.get_competitor_context_for_llm(tracked_channels)
        performance_context = youtube_analytics.get_prompt_context(handle)

        prompt = f"""You are an elite viral YouTube Shorts director and narrative architect for {name} ({handle}).
Channel Theme: '{niche}'.
Style Benchmark: Zack D. Films, Veritasium, The Action Lab.

{performance_context}

{competitor_context}

MANDATORY VIRAL TOPIC CRITERIA:
Do NOT generate generic trivia, broad school science, or bland "did you know" facts.
Every single topic MUST follow one of these 3 high-velocity conversion archetypes:
1. **Visceral Human Anatomy & Medical Horrors**: Bizarre body reactions, accidental swallowing, cellular warfare, pain reflexes, physical body phenomena (e.g., 'What Happens If You Swallow a Fish Bone', 'Why Astronauts Lose Their Fingernails', 'Why Your Skin Peels After Severe Sunburn', 'What Happens When You Step On A Rusty Nail').
2. **Extreme Institutional Rules & Strange Realities**: Bizarre, high-stakes real-world procedures (e.g., 'Why Alcatraz Only Gave Prisoners Hot Showers', 'Why Deep Sea Divers Cannot Fly For 24 Hours', 'Why Airplane Tires Don't Burst on Landing').
3. **Counter-Intuitive Material & Mechanical Breakdown**: Extreme forces acting on everyday objects (e.g., 'Why Water at 60,000 PSI Cuts Through Titanium', 'Why Bulletproof Glass Shatters on The Inside', 'How Tattoos Stay Trapped In Skin Forever').

TASK:
Generate 6 brand new, high-velocity YouTube Short concepts that guarantee a 85%+ retention rate.
Each topic MUST have an immediate 1.5-second scroll-stopping State 0 hook sentence.

Return JSON ONLY matching:
{{
  "topics": [
    {{
      "title": "Punchy 5-7 word title",
      "category": "Body Anatomy | Extreme Physics | Bizarre Rules",
      "hook": "Visceral 1.5s immediate contradiction or shock opening sentence",
      "archetype": "Visceral Anatomy | High-Stakes Rule | Material Breakdown"
    }}
  ]
}}"""

        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": Config.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.85,
            "response_format": {"type": "json_object"}
        }

        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                parsed = json.loads(data["choices"][0]["message"]["content"])
                topics = parsed.get("topics", [])
                if topics:
                    self.save_topic_to_history(topics)
                    return topics
        except Exception:
            pass

        self.save_topic_to_history(fallback)
        return fallback

channel_mgr = ChannelManager()

if __name__ == "__main__":
    print("History count:", len(channel_mgr.get_topic_history()))
