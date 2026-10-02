import json
import os
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import Config

CACHE_FILE = Path(__file__).resolve().parent / "analytics_cache.json"

# Known baseline data for @Newyrr if YouTube API key is not configured
BASELINE_VIDEOS = [
    {
        "title": "How tattoo stays permanent.",
        "views": 1500,
        "topic": "Human Biology / Immune System",
        "hook_type": "Microscopic revelation / Everyday mystery",
        "performance": "TOP_PERFORMER"
    },
    {
        "title": "He Turned Sand Into Barcodes...",
        "views": 1400,
        "topic": "Material Science / Everyday Tech Inventions",
        "hook_type": "Surprising origin / Transformation",
        "performance": "TOP_PERFORMER"
    },
    {
        "title": "High heels where made for men👠🤷‍♂️",
        "views": 214,
        "topic": "Historical Fashion Trivia",
        "hook_type": "Gender role inversion / Fashion history",
        "performance": "UNDERPERFORMER"
    }
]

class YouTubeAnalyticsManager:
    """
    Fetches, caches, and analyzes video performance metrics for @Newyrr.
    Provides performance insights to condition LLM generation.
    """

    def __init__(self, api_key: Optional[str] = None, channel_id: Optional[str] = None):
        self.api_key = api_key or Config.YOUTUBE_API_KEY
        self.channel_id = channel_id or Config.YOUTUBE_CHANNEL_ID

    def fetch_channel_videos(self) -> List[Dict[str, Any]]:
        """
        Queries YouTube Data API v3 for the channel's uploads and statistics.
        Falls back to local cache or baseline data if API is unconfigured.
        """
        if not self.api_key:
            print("[YouTube Analytics] No YOUTUBE_API_KEY detected. Using verified channel baseline data.")
            return self._load_cache_or_baseline()

        try:
            # 1. Get uploads playlist ID
            channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails,statistics&id={self.channel_id}&key={self.api_key}"
            res = requests.get(channel_url, timeout=10)
            data = res.json()

            if "items" not in data or not data["items"]:
                print(f"[YouTube Analytics] Channel {self.channel_id} not found via API. Using baseline data.")
                return self._load_cache_or_baseline()

            uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # 2. Get video items
            playlist_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=10&key={self.api_key}"
            p_res = requests.get(playlist_url, timeout=10)
            p_data = p_res.json()

            video_ids = [item["snippet"]["resourceId"]["videoId"] for item in p_data.get("items", [])]
            if not video_ids:
                return self._load_cache_or_baseline()

            # 3. Get video statistics
            stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={','.join(video_ids)}&key={self.api_key}"
            s_res = requests.get(stats_url, timeout=10)
            s_data = s_res.json()

            videos = []
            for item in s_data.get("items", []):
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})
                views = int(statistics.get("viewCount", 0))
                title = snippet.get("title", "")
                videos.append({
                    "id": item["id"],
                    "title": title,
                    "views": views,
                    "likes": int(statistics.get("likeCount", 0)),
                    "comments": int(statistics.get("commentCount", 0)),
                    "published_at": snippet.get("publishedAt", "")
                })

            # Sort by views descending
            videos.sort(key=lambda x: x["views"], reverse=True)
            self._save_cache(videos)
            return videos

        except Exception as e:
            print(f"[YouTube Analytics] Error fetching from YouTube API: {e}. Falling back to cached data.")
            return self._load_cache_or_baseline()

    def _save_cache(self, data: List[Dict[str, Any]]):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_cache_or_baseline(self) -> List[Dict[str, Any]]:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return BASELINE_VIDEOS

    def get_prompt_context(self) -> str:
        """
        Generates a concise performance brief formatted specifically
        for the LLM system prompt.
        """
        videos = self.fetch_channel_videos()
        top_videos = videos[:3]
        
        summary_lines = [
            "### @Newyrr Channel Performance Intelligence:",
            "- Channel Theme: 'Shorts science. How and what if moments.'",
            "- Proven Top Performers (Highest retention & algorithm pickup):"
        ]

        for v in top_videos:
            views = v.get("views", 0)
            title = v.get("title", "Untitled")
            topic = v.get("topic", "Science Trivia")
            summary_lines.append(f"  * \"{title}\" (~{views:,} views) - Topic: {topic}")

        summary_lines.extend([
            "- Key Algorithm Takeaways:",
            "  1. WINNING PATTERN: Hidden biology, material transformations, and macroscopic revelations (e.g. skin cells fighting ink, glass sand becoming barcodes) have 7x higher engagement than historical trivia.",
            "  2. HOOK RULE: Start within 1.5 seconds on an unsettling or mind-bending tactile fact (no intro, no greetings).",
            "  3. LOOP RULE: The last sentence must grammatically connect directly back into the opening hook."
        ])

        return "\n".join(summary_lines)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    manager = YouTubeAnalyticsManager()
    context = manager.get_prompt_context()
    print("\n--- EXTRACTED ANALYTICS CONTEXT FOR LLM ---")
    print(context)
