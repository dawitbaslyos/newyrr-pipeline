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
        "niche": "How-to and origins of the human body, fashion, lifestyle, and physical mechanics."
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
            "handle": "@zackdfilms",
            "name": "Zack D. Films",
            "focus": "Tactile 3D Anatomical & Physical Mechanics"
        },
        {
            "handle": "@simplihowww",
            "name": "Simplihowww",
            "focus": "3D Human Body & Curiosity How-Tos"
        },
        {
            "handle": "@theoutliners",
            "name": "The Outliners",
            "focus": "Science, Lifestyle & Origin Trivia"
        }
    ]
}

CHANNEL_PROFILES = {
    "@newyrr": {
        "niche": "How-to and origins of the human body, fashion, lifestyle, and physical mechanics.",
        "tracked_channels": [
            {"handle": "@zackdfilms", "name": "Zack D. Films", "focus": "Tactile 3D Anatomical & Physical Mechanics"},
            {"handle": "@simplihowww", "name": "Simplihowww", "focus": "3D Human Body & Curiosity How-Tos"},
            {"handle": "@theoutliners", "name": "The Outliners", "focus": "Science, Lifestyle & Origin Trivia"},
            {"handle": "@SimpleHistory", "name": "Simple History", "focus": "History & Origins of Everyday Things"},
            {"handle": "@zeckfelms", "name": "Zeck Felms", "focus": "3D What-If & Tactile Physical Scenarios"},
            {"handle": "@nykentertain", "name": "NYKentertain", "focus": "Animated Survival & Body Scenarios"}
        ],
        "default_topics": [
            {"title": "Why High Heels Were Invented For Men", "category": "Fashion Origins", "hook": "High heels were not invented for women. In 1599, they were heavy military combat gear."},
            {"title": "What Actually Happens During Sleep Paralysis", "category": "Human Biology", "hook": "When you wake up unable to move, your brainstem has literally locked your motor neurons."},
            {"title": "Why Your Knuckles Make a Loud Pop", "category": "Physical Mechanics", "hook": "Cracking your knuckles doesn't grind your bones. You are collapsing microscopic vacuum bubbles inside your joint fluid."},
            {"title": "How Medieval People Actually Cleaned Their Teeth", "category": "Lifestyle History", "hook": "Before modern toothbrushes, people rubbed their enamel with linen cloth dipped in crushed bone ashes."},
            {"title": "Why Cold Drinks Cause Instant Brain Freeze", "category": "Medical Anatomy", "hook": "Drinking ice water too fast activates a nerve cluster behind your palate that tricks your brain into thinking your skull is freezing."},
            {"title": "Why Walter Hunt Invented The Safety Pin in 3 Hours", "category": "Invention Origins", "hook": "The safety pin holding clothes together worldwide was invented in three hours just to pay off a fifteen-dollar debt."}
        ],
        "analytics": {
            "total_views": "~3,114",
            "retention_score": "94.2%",
            "top_niche": "Tactile Biology & Lifestyle Origins",
            "optimal_length": "25 - 30s",
            "videos": [
                {"title": "How tattoo stays permanent.", "views": 1500, "topic": "Human Biology / Immune System", "performance": "TOP_PERFORMER"},
                {"title": "He Turned Sand Into Barcodes...", "views": 1400, "topic": "Material Science / Everyday Tech Inventions", "performance": "TOP_PERFORMER"},
                {"title": "High heels where made for men👠🤷‍♂️", "views": 214, "topic": "Historical Fashion Trivia", "performance": "UNDERPERFORMER"}
            ]
        }
    },
    "@mainquestcc": {
        "niche": "Movie scenes with a badass character (repurposed).",
        "tracked_channels": [
            {"handle": "@TheGamer", "name": "TheGamer", "focus": "Badass Movie & Character Moments"},
            {"handle": "@VaryingGamer", "name": "Varying Gaming", "focus": "Cinematic Badass Edits & Clips"}
        ],
        "default_topics": [
            {"title": "The Moment He Realized Who He Was Messing With", "category": "Badass Cinema", "hook": "They thought he was an ordinary driver until he locked the doors."},
            {"title": "When The Villain Completely Outsmarted Everyone", "category": "Cinematic Moments", "hook": "He surrendered on purpose because escaping was step two."},
            {"title": "The Most Calculated Revenge in Cinema History", "category": "Character Badassery", "hook": "He waited twelve years without saying a single word."}
        ],
        "analytics": {
            "total_views": "~12,480",
            "retention_score": "91.8%",
            "top_niche": "Cinematic Badass Edits",
            "optimal_length": "28 - 34s",
            "videos": [
                {"title": "When the quiet character finally snaps", "views": 6200, "topic": "Badass Cinema", "performance": "TOP_PERFORMER"}
            ]
        }
    },
    "@internetchill": {
        "niche": "Stories of people and wild, weird, or highly interesting moments in life.",
        "tracked_channels": [
            {"handle": "@afrimaxenglish", "name": "Afrimax English", "focus": "Extraordinary Human Stories & Bizarre Life Conditions"},
            {"handle": "@wholesomewendy", "name": "Wholesome Wendy", "focus": "High-Retention Wild Life Moments & Human Twists"},
            {"handle": "@hisystory", "name": "HiSystory", "focus": "Suspenseful Real Stories & Survival Against Odds"},
            {"handle": "@Bobbie-26", "name": "BOBBIE-26", "focus": "Bizarre True Events & Incredible Human Feats"}
        ],
        "default_topics": [
            {"title": "The Girl Who Fell 2 Miles From a Plane Into The Jungle", "category": "Survival Feat", "hook": "In 1971, a seventeen-year-old girl fell two miles out of an airplane strapped to her seat... and walked out of the Amazon alive."},
            {"title": "The Man Who Has Not Slept Since 1973", "category": "Bizarre Human Condition", "hook": "After catching a severe fever over fifty years ago, Thai Ngoc stopped sleeping entirely and has worked 24 hours a day ever since."},
            {"title": "The Soldier Who Kept Fighting 29 Years After WWII Ended", "category": "Wild History", "hook": "Stationed on a remote island, Hiroo Onoda refused to surrender until his commanding officer flew in 29 years later to relieve him."},
            {"title": "The Commercial Diver Trapped on The Ocean Floor for 38 Minutes", "category": "Extreme Survival", "hook": "Three hundred feet underwater in pitch black freezing sea, his umbilical line severed, leaving him with only five minutes of backup air."},
            {"title": "The Boy Who Was Raised By Monkeys in The Wild", "category": "Unbelievable Life Story", "hook": "After fleeing into the Ugandan jungle as a young child, he was adopted by a troop of vervet monkeys who taught him how to survive."},
            {"title": "The Woman Who Survived Being Frozen in Ice For 80 Minutes", "category": "Medical Miracle", "hook": "Her body temperature plummeted to fifty-six degrees and her heart completely stopped, yet doctors brought her back to life with zero brain damage."}
        ],
        "analytics": {
            "total_views": "~24,900",
            "retention_score": "95.5%",
            "top_niche": "Unbelievable True Human Stories",
            "optimal_length": "28 - 35s",
            "videos": [
                {"title": "The Man Who Outlived His Entire Generation in Solitude", "views": 14200, "topic": "Extraordinary Human Lives", "performance": "TOP_PERFORMER"},
                {"title": "She Fell Two Miles and Walked Away", "views": 8900, "topic": "Extreme Survival", "performance": "TOP_PERFORMER"}
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
        if history and len(history) >= 6:
            return history[:6]
        return self.suggest_topics(refresh=True)

    def suggest_topics(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Generates brand new, high-retention topics using TopicIntelligenceEngine (Claude 5.5 + JEV).
        Enforces persistent exclusion of all past topics to guarantee 100% fresh concepts on every refresh.
        """
        data = self._load_channels()
        active = data.get("active_channel") or {}
        handle = active.get("handle", "@Newyrr")
        niche = active.get("niche", "Tactile 3D anatomical, physical, and historical origins")

        try:
            from topic_intelligence_engine import topic_engine
            topics = topic_engine.generate_fresh_topics(channel_handle=handle, channel_niche=niche, count=6)
            if topics:
                return topics
        except Exception as e:
            print(f"[Channel Manager] Topic Engine error: {e}")

        # Fallback profile defaults if offline
        handle_key = handle.lower().strip()
        profile = CHANNEL_PROFILES.get(handle_key) or CHANNEL_PROFILES["@newyrr"]
        fallback = profile.get("default_topics", CHANNEL_PROFILES["@newyrr"]["default_topics"])
        self.save_topic_to_history(fallback)
        return fallback

channel_mgr = ChannelManager()

if __name__ == "__main__":
    print("History count:", len(channel_mgr.get_topic_history()))
