import json
import re
import urllib.request
import os
import tempfile
from typing import Optional, Dict, Any

try:
    from .database import update_video_transcript, get_video_by_id
except (ImportError, ValueError):
    from database import update_video_transcript, get_video_by_id

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

def fetch_transcript_via_api(video_id: str) -> Optional[str]:
    """Attempt extraction via youtube_transcript_api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        if transcript:
            text_lines = []
            for item in transcript:
                if isinstance(item, dict):
                    t = item.get('text', '')
                elif hasattr(item, 'text'):
                    t = item.text
                else:
                    t = str(item)
                if t and t.strip():
                    text_lines.append(t.strip())
            full_text = " ".join(text_lines)
            if len(full_text.strip()) > 30:
                return full_text.strip()
    except Exception as e:
        print(f"[Fetcher] youtube_transcript_api: {e}")
    return None

def fetch_transcript_via_whisper(video_id: str) -> Optional[str]:
    """
    Fallback using yt-dlp + android client to extract audio and whisper to transcribe.
    Bypasses YouTube 429 bot blocks.
    """
    try:
        import yt_dlp
        import whisper
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out_tmpl = os.path.join(tmpdir, "audio.%(ext)s")
            ydl_opts = {
                'format': 'ba[ext=m4a]/ba/worstaudio',
                'outtmpl': out_tmpl,
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
                'max_filesize': 50 * 1024 * 1024  # Max 50MB
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                
            # Find the downloaded audio file
            files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.startswith("audio")]
            if not files:
                return None
                
            audio_path = files[0]
            print(f"[Fetcher] Audio downloaded. Transcribing with Whisper tiny for {video_id}...")
            model = whisper.load_model("tiny")
            result = model.transcribe(audio_path, language="en")
            text = result.get("text", "").strip()
            if text and len(text) > 30:
                return text
    except Exception as e:
        print(f"[Fetcher] Whisper fallback error: {e}")
    return None

def get_video_transcript(video_id: str, force_refresh: bool = False, use_ai_fallback: bool = False) -> Dict[str, Any]:
    """
    Main entry point for getting transcript.
    Prioritizes cached -> captions api -> description -> (optional) Whisper.
    """
    video = get_video_by_id(video_id)
    if not force_refresh and video and video.get("transcript") and video.get("transcript_status") in ["fetched", "manual"]:
        return {
            "video_id": video_id,
            "status": video.get("transcript_status"),
            "source": "cache",
            "transcript": video["transcript"]
        }
        
    print(f"[Fetcher] Attempting transcript fetch for {video_id}...")
    
    # 1. Fast API fetch
    text = fetch_transcript_via_api(video_id)
    source = "youtube_captions"
    
    # 2. If AI fallback requested or forced
    if not text and use_ai_fallback:
        text = fetch_transcript_via_whisper(video_id)
        if text:
            source = "whisper_ai"
            
    # 3. Fallback to rich video description if transcript is not available
    if not text:
        desc = (video.get("description") if video else "") or ""
        if len(desc.strip()) > 30:
            text = f"[Video Description Summary]\n{desc.strip()}"
            source = "description_fallback"
            
    if text:
        status = "fetched"
        update_video_transcript(video_id, text, status=status)
        return {
            "video_id": video_id,
            "status": status,
            "source": source,
            "transcript": text
        }
    else:
        update_video_transcript(video_id, "", status="not_available")
        return {
            "video_id": video_id,
            "status": "not_available",
            "source": "none",
            "transcript": ""
        }
