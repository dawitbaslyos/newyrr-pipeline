import re
import urllib.request
import json
from typing import Optional, Dict, Any

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def resolve_channel(input_str: str) -> Optional[Dict[str, Any]]:
    """
    Takes a channel handle (@handle), full URL, or Channel ID (UC...)
    and returns dict with: id, title, handle, url, avatar_url
    """
    clean = input_str.strip()
    
    # Direct Channel ID check
    if clean.startswith("UC") and len(clean) == 24 and not "/" in clean:
        channel_id = clean
        url = f"https://www.youtube.com/channel/{channel_id}"
    else:
        # Handle or custom URL
        if not clean.startswith("http"):
            if clean.startswith("@"):
                url = f"https://www.youtube.com/{clean}"
            else:
                url = f"https://www.youtube.com/@{clean}"
        else:
            url = clean
            
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9"
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
        # Extract Channel ID
        channel_id = None
        id_patterns = [
            r'itemprop="channelId"\s+content="(UC[\w-]+)"',
            r'"externalId"\s*:\s*"(UC[\w-]+)"',
            r'"channelId"\s*:\s*"(UC[\w-]+)"',
            r'https://www.youtube.com/channel/(UC[\w-]+)'
        ]
        for pat in id_patterns:
            m = re.search(pat, html)
            if m:
                channel_id = m.group(1)
                break
                
        if not channel_id:
            # Check if input was already a channel id
            if "channel/UC" in url:
                m = re.search(r'channel/(UC[\w-]+)', url)
                if m:
                    channel_id = m.group(1)
                    
        if not channel_id:
            return None
            
        # Extract Title
        title = "Tracked Channel"
        title_m = re.search(r'<meta property="og:title" content="(.*?)">', html)
        if title_m:
            title = title_m.group(1).replace("&amp;", "&").replace("&quot;", '"')
        else:
            t_m = re.search(r'<title>(.*?) - YouTube</title>', html)
            if t_m:
                title = t_m.group(1)

        # Extract Avatar
        avatar_url = ""
        img_m = re.search(r'<meta property="og:image" content="(.*?)">', html)
        if img_m:
            avatar_url = img_m.group(1)
            
        # Extract Canonical handle
        handle = ""
        if "@" in url:
            handle = "@" + url.split("@")[-1].split("/")[0]
            
        return {
            "id": channel_id,
            "title": title,
            "handle": handle,
            "url": f"https://www.youtube.com/channel/{channel_id}",
            "avatar_url": avatar_url
        }
        
    except Exception as e:
        print(f"Error resolving channel {input_str}: {e}")
        # Fallback if channel ID was supplied directly
        if clean.startswith("UC") and len(clean) == 24:
            return {
                "id": clean,
                "title": f"Channel {clean[:8]}",
                "handle": "",
                "url": f"https://www.youtube.com/channel/{clean}",
                "avatar_url": ""
            }
        return None
