import re
import time
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

COMPETITOR_CACHE_FILE = Path(__file__).resolve().parent / "competitor_cache.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

class CompetitorTracker:
    """
    Tracks competitor YouTube channels completely FREE (0 API Quota).
    Resolves channels via public HTML tags and fetches recent uploads via Atom RSS feeds.
    Deconstructs titles, themes, and hooks for the LLM topic & script engine.
    """

    def __init__(self):
        self.cache_file = COMPETITOR_CACHE_FILE
        self._ensure_cache()

    def _ensure_cache(self):
        if not self.cache_file.exists():
            try:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)
            except Exception:
                pass

    def _load_cache(self) -> Dict[str, Any]:
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_cache(self, data: Dict[str, Any]):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Competitor Tracker] Error saving cache: {e}")

    @staticmethod
    def resolve_channel_free(handle_or_url: str) -> Optional[Dict[str, Any]]:
        """
        Resolves @handle, URL, or channel ID to channel metadata (channelId, title, avatar)
        without consuming any YouTube API quota.
        """
        clean = handle_or_url.strip()
        if not clean.startswith("http"):
            clean_handle = clean if clean.startswith("@") else f"@{clean}"
            url = f"https://www.youtube.com/{clean_handle}"
        else:
            url = clean
            clean_handle = "@" + url.split("@")[-1].split("/")[0] if "@" in url else ""

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            channel_id = None
            id_patterns = [
                r'itemprop="channelId"\s+content="(UC[\w-]+)"',
                r'"externalId"\s*:\s*"(UC[\w-]+)"',
                r'"channelId"\s*:\s*"(UC[\w-]+)"'
            ]
            for pat in id_patterns:
                m = re.search(pat, html)
                if m:
                    channel_id = m.group(1)
                    break

            if not channel_id and "channel/UC" in url:
                m = re.search(r'channel/(UC[\w-]+)', url)
                if m:
                    channel_id = m.group(1)

            if not channel_id:
                return None

            title = "Tracked Channel"
            title_m = re.search(r'<meta property="og:title" content="(.*?)">', html)
            if title_m:
                title = title_m.group(1).replace("&amp;", "&").replace("&quot;", '"')

            avatar_url = ""
            img_m = re.search(r'<meta property="og:image" content="(.*?)">', html)
            if img_m:
                avatar_url = img_m.group(1)

            return {
                "id": channel_id,
                "title": title,
                "handle": clean_handle,
                "avatar_url": avatar_url,
                "url": f"https://www.youtube.com/channel/{channel_id}"
            }
        except Exception as e:
            print(f"[Competitor Tracker] Free resolution failed for {handle_or_url}: {e}")
            return None

    @staticmethod
    def fetch_channel_videos_rss(channel_id: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """
        Fetches recent uploads for a channel via YouTube's public Atom RSS feed.
        Consumes 0 API quota.
        """
        if not channel_id:
            return []

        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        videos = []
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_data = resp.read()

            root = ET.fromstring(xml_data)
            atom_ns = "{http://www.w3.org/2005/Atom}"
            yt_ns = "{http://www.youtube.com/xml/schemas/2015}"
            media_ns = "{http://search.yahoo.com/mrss/}"

            for entry in root.findall(f"{atom_ns}entry")[:max_results]:
                vid_elem = entry.find(f"{yt_ns}videoId")
                if vid_elem is None or not vid_elem.text:
                    continue
                vid_id = vid_elem.text.strip()

                title_elem = entry.find(f"{atom_ns}title")
                title = title_elem.text if title_elem is not None and title_elem.text else "Untitled"

                pub_elem = entry.find(f"{atom_ns}published")
                published_at = pub_elem.text if pub_elem is not None and pub_elem.text else ""

                thumbnail_url = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                desc = ""
                media_grp = entry.find(f"{media_ns}group")
                if media_grp is not None:
                    thumb_elem = media_grp.find(f"{media_ns}thumbnail")
                    if thumb_elem is not None and "url" in thumb_elem.attrib:
                        thumbnail_url = thumb_elem.attrib["url"]
                    desc_elem = media_grp.find(f"{media_ns}description")
                    if desc_elem is not None and desc_elem.text:
                        desc = desc_elem.text

                videos.append({
                    "id": vid_id,
                    "title": title,
                    "published_at": published_at,
                    "thumbnail_url": thumbnail_url,
                    "video_url": f"https://www.youtube.com/watch?v={vid_id}",
                    "description": desc
                })
        except Exception as e:
            print(f"[Competitor Tracker] Error fetching RSS for {channel_id}: {e}")

        return videos

    def sync_tracked_channels_for_workspace(self, tracked_channels: List[Dict[str, Any]], force: bool = False) -> Dict[str, Any]:
        """
        Syncs videos for all competitor channels tracked under the active user workspace.
        """
        cache = self._load_cache()
        now = time.time()
        results = {}

        for ch in tracked_channels:
            handle = (ch.get("handle") or "").strip().lower()
            if not handle:
                continue

            cached_entry = cache.get(handle, {})
            # Refresh if older than 3 hours or force or if videos list is empty
            if not force and cached_entry and cached_entry.get("videos") and (now - cached_entry.get("updated_at", 0) < 10800):
                results[handle] = cached_entry.get("videos", [])
                continue

            channel_id = ch.get("channel_id") or cached_entry.get("channel_id")
            title = ch.get("name") or cached_entry.get("title")
            avatar_url = ch.get("avatar_url") or cached_entry.get("avatar_url")

            # Resolve if channel ID missing
            if not channel_id:
                meta = self.resolve_channel_free(handle)
                if meta:
                    channel_id = meta.get("id")
                    title = meta.get("title") or title
                    avatar_url = meta.get("avatar_url") or avatar_url
                    ch["channel_id"] = channel_id
                    ch["name"] = title
                    ch["avatar_url"] = avatar_url

            if channel_id:
                vids = self.fetch_channel_videos_rss(channel_id, max_results=12)
                cache[handle] = {
                    "channel_id": channel_id,
                    "handle": handle,
                    "title": title,
                    "avatar_url": avatar_url,
                    "focus": ch.get("focus", ""),
                    "videos": vids,
                    "updated_at": now
                }
                results[handle] = vids

        self._save_cache(cache)
        return results

    def get_competitor_context_for_llm(self, tracked_channels: List[Dict[str, Any]]) -> str:
        """
        Synthesizes recent competitor video titles and narrative concepts into a concise brief
        for OpenRouter / DeepSeek when generating new topics or scripts.
        """
        cache = self._load_cache()
        lines = ["### Verified Tracked Competitor Intelligence:"]

        has_data = False
        for ch in tracked_channels:
            handle = (ch.get("handle") or "").strip().lower()
            name = ch.get("name") or handle
            entry = cache.get(handle, {})
            videos = entry.get("videos", [])
            if not videos:
                continue

            has_data = True
            lines.append(f"- Recent High-Velocity Uploads from {name} ({handle}):")
            for v in videos[:6]:
                lines.append(f"  * \"{v.get('title')}\"")

        if not has_data:
            # Fallback baseline for Zack D Films & science inspiration
            lines.extend([
                "- Trending Competitor Formats (@zackdfilms, @TheActionLab, @Veritasium):",
                "  * Tactile microscopic anticipation ('What Happens If You Swallow A Magnet?')",
                "  * Hidden everyday mechanical contradictions ('Why Glass Is Secretly Dripping Downward')",
                "  * Biological defense mechanisms ('How Your Immune System Attacks Ink')"
            ])

        lines.extend([
            "- Viral Deconstruction Patterns to Emulate:",
            "  1. Immediate Physical Set: Establish the physical object / subject in pristine state 0 anticipation within 1.5 seconds.",
            "  2. The Catalyst: A single physical action (shear, burst, dissolve, drop) breaks stillness.",
            "  3. Seamless Loop: Last sentence connects directly to opening sentence."
        ])

        return "\n".join(lines)

competitor_tracker = CompetitorTracker()
