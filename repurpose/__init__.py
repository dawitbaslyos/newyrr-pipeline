"""
Video Repurposing & Intelligence Engine
Integrated from yt-automation into Newyrr Pipeline Studio.
"""

from .repurpose_engine import (
    deconstruct_source_video,
    render_repurposed_video,
    download_source_video,
    detect_source_credits
)
from .fetcher import get_video_transcript
from .resolver import resolve_channel
from .tracker import fetch_channel_videos, track_channel
from .subtitles import generate_srt_from_audio
