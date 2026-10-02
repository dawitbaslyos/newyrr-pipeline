import xml.etree.ElementTree as ET
import urllib.request
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from .database import save_video, update_channel_checked, get_all_channels
except (ImportError, ValueError):
    from database import save_video, update_channel_checked, get_all_channels

ATOM_NS = "{http://www.w3.org/2005/Atom}"
YT_NS = "{http://www.youtube.com/xml/schemas/2015}"
MEDIA_NS = "{http://search.yahoo.com/mrss/}"

FEED_USER_AGENT = "Mozilla/5.0"

def fetch_channel_videos(channel_id: str) -> List[Dict[str, Any]]:
    """
    Fetches the 15 most recent videos for a channel using YouTube's public Atom RSS feed.
    Zero API quota consumed.
    """
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={"User-Agent": FEED_USER_AGENT})
    
    videos = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read()
            
        root = ET.fromstring(content)
        
        for entry in root.findall(f"{ATOM_NS}entry"):
            video_id_elem = entry.find(f"{YT_NS}videoId")
            if video_id_elem is None or not video_id_elem.text:
                continue
            video_id = video_id_elem.text.strip()
            
            title_elem = entry.find(f"{ATOM_NS}title")
            title = title_elem.text if title_elem is not None and title_elem.text else "Untitled Video"
            
            pub_elem = entry.find(f"{ATOM_NS}published")
            published_at = pub_elem.text if pub_elem is not None and pub_elem.text else datetime.utcnow().isoformat()
            
            # Media group for thumbnails and description
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            description = ""
            
            media_group = entry.find(f"{MEDIA_NS}group")
            if media_group is not None:
                thumb_elem = media_group.find(f"{MEDIA_NS}thumbnail")
                if thumb_elem is not None and "url" in thumb_elem.attrib:
                    thumbnail_url = thumb_elem.attrib["url"]
                    
                desc_elem = media_group.find(f"{MEDIA_NS}description")
                if desc_elem is not None and desc_elem.text:
                    description = desc_elem.text
            
            videos.append({
                "id": video_id,
                "channel_id": channel_id,
                "title": title,
                "published_at": published_at,
                "thumbnail_url": thumbnail_url,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "description": description
            })
            
    except Exception as e:
        print(f"[Tracker] Error fetching feed for channel {channel_id}: {e}")
        
    return videos

def track_channel(channel_id: str) -> Dict[str, Any]:
    """Polls a channel, stores newly discovered videos, and updates state."""
    videos = fetch_channel_videos(channel_id)
    new_count = 0
    for v in videos:
        is_new = save_video(v)
        if is_new:
            new_count += 1
            
    update_channel_checked(channel_id)
    return {
        "channel_id": channel_id,
        "fetched_total": len(videos),
        "new_videos": new_count
    }

def track_all_active_channels() -> Dict[str, Any]:
    """Scans all enabled channels in database."""
    channels = get_all_channels()
    active_channels = [c for c in channels if c.get("active")]
    
    total_new = 0
    results = []
    
    for ch in active_channels:
        res = track_channel(ch["id"])
        total_new += res["new_videos"]
        results.append(res)
        
    return {
        "scanned_channels": len(active_channels),
        "total_new_videos": total_new,
        "details": results
    }

def fetch_videos_for_handle_or_id(handle_or_id: str, limit: int = 6) -> List[Dict[str, Any]]:
    clean = handle_or_id.strip()
    
    # 1. Primary: High-reliability flat extraction via yt-dlp (0 API quota, works on handles & URLs)
    try:
        import yt_dlp
        target_url = clean
        if not clean.startswith("http"):
            if clean.startswith("@"):
                target_url = f"https://www.youtube.com/{clean}/videos"
            elif clean.startswith("UC") and len(clean) == 24:
                target_url = f"https://www.youtube.com/channel/{clean}/videos"
            else:
                target_url = f"https://www.youtube.com/@{clean}/videos"
        elif not target_url.endswith("/videos"):
            target_url = f"{target_url.rstrip('/')}/videos"

        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'playlist_items': f'1-{limit}'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(target_url, download=False)
            entries = res.get('entries', []) if res else []
            if entries:
                videos = []
                for e in entries:
                    vid_id = e.get('id')
                    if not vid_id:
                        continue
                    thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    if e.get('thumbnails'):
                        thumb = e['thumbnails'][-1].get('url', thumb)
                    videos.append({
                        "id": vid_id,
                        "title": e.get('title') or "Untitled Video",
                        "published_at": e.get('timestamp') or datetime.utcnow().isoformat(),
                        "thumbnail_url": thumb,
                        "video_url": e.get('url') or f"https://www.youtube.com/watch?v={vid_id}",
                        "description": e.get('description', '')
                    })
                return videos
    except Exception as e:
        print(f"[Tracker] yt-dlp flat extraction fallback to RSS: {e}")

    # 2. Fallback: Atom RSS feed
    if clean.startswith("UC") and len(clean) == 24:
        channel_id = clean
    else:
        try:
            from .resolver import resolve_channel
            res = resolve_channel(clean)
            channel_id = res.get("id") if res else None
        except Exception:
            channel_id = None

    if not channel_id:
        return []
    return fetch_channel_videos(channel_id)
