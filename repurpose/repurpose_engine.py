import os
import re
import uuid
import json
import subprocess
from typing import Dict, Any, Optional, List

try:
    from .database import get_video_by_id, get_account_by_id, create_project, update_project
    from .fetcher import get_video_transcript
    from .trend_engine import call_openrouter
    from .tts import generate_narration
    from .subtitles import generate_srt_from_audio, generate_ass_from_audio
except (ImportError, ValueError):
    from database import get_video_by_id, get_account_by_id, create_project, update_project
    from fetcher import get_video_transcript
    from trend_engine import call_openrouter
    from tts import generate_narration
    from subtitles import generate_srt_from_audio, generate_ass_from_audio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOWNLOADS_DIR = os.path.join(DATA_DIR, "downloads")
RENDERS_DIR = os.path.join(DATA_DIR, "renders")
TEMP_DIR = os.path.join(DATA_DIR, "temp")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

def detect_source_credits(description: str) -> List[str]:
    """Scans video description to detect source footage credits or original links."""
    if not description:
        return []
    urls = re.findall(r'(https?://[^\s]+)', description)
    citations = []
    for line in description.splitlines():
        if any(keyword in line.lower() for keyword in ["source:", "credit:", "footage by:", "original:", "via:"]):
            citations.append(line.strip())
def extract_video_id(url_or_id: str) -> str:
    clean = url_or_id.strip()
    if len(clean) == 11 and not ("/" in clean or "." in clean or "?" in clean):
        return clean
    m = re.search(r"shorts/([a-zA-Z0-9_\-]{11})", clean)
    if m:
        return m.group(1)
    m = re.search(r"[?&]v=([a-zA-Z0-9_\-]{11})", clean)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([a-zA-Z0-9_\-]{11})", clean)
    if m:
        return m.group(1)
    return clean

def get_or_fetch_video(video_id: str) -> Dict[str, Any]:
    v = get_video_by_id(video_id)
    if v:
        return v
    try:
        import yt_dlp
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            video_data = {
                "id": video_id,
                "channel_id": info.get("channel_id") or "external_channel",
                "channel_name": info.get("uploader") or info.get("channel") or "Source Creator",
                "title": info.get("title") or f"Video {video_id}",
                "published_at": info.get("upload_date", ""),
                "thumbnail_url": info.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "description": info.get("description", "")
            }
            try:
                from .database import save_video
                save_video(video_data)
            except Exception:
                pass
            return video_data
    except Exception as e:
        print(f"[Repurpose] Warning: Could not fetch yt-dlp metadata for {video_id}: {e}")
        return {
            "id": video_id,
            "channel_id": "external_channel",
            "channel_name": "Source Creator",
            "title": f"Viral Short {video_id}",
            "description": "",
            "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "video_url": f"https://www.youtube.com/watch?v={video_id}"
        }

def deconstruct_source_video(url_or_id: str, target_seconds: int = 45, account_id: str = "main-channel") -> Dict[str, Any]:
    video_id = extract_video_id(url_or_id)
    video = get_or_fetch_video(video_id)
    plan = generate_explainer_script(video_id, account_id, target_seconds, video_data=video)
    
    return {
        "video_id": video_id,
        "title": plan.get("title", video.get("title")),
        "hook": plan.get("hook", ""),
        "full_narration": plan.get("full_narration", ""),
        "key_takeaway": plan.get("key_takeaway", ""),
        "original_title": video.get("title", ""),
        "original_channel": video.get("channel_name", ""),
        "thumbnail_url": video.get("thumbnail_url", f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"),
        "detected_credits": plan.get("detected_credits", detect_source_credits(video.get("description", "")))
    }

def repurpose_viral_video(video_id: str, account_id: str) -> Dict[str, Any]:
    video = get_or_fetch_video(video_id)
    plan = generate_explainer_script(video_id, account_id, video_data=video)
    project_id = f"proj-rep-{uuid.uuid4().hex[:8]}"
    return create_project(
        project_id=project_id,
        account_id=account_id,
        source_type="repurpose",
        title=plan.get("title", video.get("title", "Repurposed Video") if video else "Repurposed Video"),
        topic=video.get("title", "") if video else "",
        source_video_id=video_id,
        stage="script",
        script_data=plan
    )

def download_source_video(video_id: str) -> str:
    """Downloads source video cleanly up to 1080p using yt-dlp with mobile client."""
    target_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.mp4")
    if os.path.exists(target_path) and os.path.getsize(target_path) > 100000:
        return target_path

    import yt_dlp
    ydl_opts = {
        'format': 'bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4][height<=1080]/worst',
        'outtmpl': os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s"),
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        'max_filesize': 150 * 1024 * 1024  # 150MB cap
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        
    if os.path.exists(target_path):
        return target_path
        
    # Check if downloaded with another extension
    for f in os.listdir(DOWNLOADS_DIR):
        if f.startswith(video_id):
            return os.path.join(DOWNLOADS_DIR, f)
            
    raise FileNotFoundError(f"Could not download video {video_id}")

def get_media_duration(file_path: str) -> float:
    """Measures audio or video duration in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 30.0

def generate_explainer_script(video_id: str, account_id: str, target_seconds: int = 45, video_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Uses Gemini to distill original video into a punchy, structured explainer script."""
    video = video_data or get_video_by_id(video_id) or get_or_fetch_video(video_id)
    if not video:
        raise ValueError(f"Video {video_id} not found")
        
    account = get_account_by_id(account_id)
    preset = account.get("prompt_preset", "") if account else ""
    niche = account.get("target_niche", "General") if account else "General"
    
    transcript_res = get_video_transcript(video_id)
    raw_text = transcript_res.get("transcript", "") or video.get("description", "") or video.get("title", "")
    
    words = raw_text.split()
    clean_sample = " ".join(words[:2500])
    
    target_words = int(target_seconds * 2.4) # 2.4 words per second
    
    sys_prompt = (
        "You are an elite YouTube explainer director and viral storyteller. "
        "Your goal is to extract the single most compelling insight from the video content "
        "and rewrite it into a fast-paced, high-retention spoken explainer script.\n"
        "Never copy sentences verbatim. Deliver:\n"
        "1. A 3-second hook that creates irresistible curiosity.\n"
        "2. The core explanation without any filler, pauses, or fluff.\n"
        "3. A sharp takeaway.\n"
        f"Target length: exactly ~{target_words} words (approx {target_seconds} seconds spoken).\n\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        '  "title": "Fresh Explainer Title",\n'
        '  "hook": "Opening 3-second hook sentence.",\n'
        '  "full_narration": "Full spoken voiceover text ready for text-to-speech.",\n'
        '  "key_takeaway": "One sentence summary of the core insight.",\n'
        '  "detected_credits": ["source notes"]\n'
        "}"
    )
    
    user_prompt = (
        f"Original Video: {video['title']}\n"
        f"Channel: {video['channel_name']}\n"
        f"Target Niche: {niche}\n"
        f"Creative Preset: {preset}\n\n"
        f"Content Transcript:\n{clean_sample}\n\n"
        "Write the ultimate explainer script for this video."
    )
    
    raw = call_openrouter([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ], json_mode=True)
    
    if raw:
        try:
            return json.loads(raw)
        except Exception as e:
            print(f"[Repurpose Script] Parse error: {e}")
            
    # Fallback script
    orig_title = video['title']
    return {
        "title": f"How {orig_title} Actually Works",
        "hook": f"What most people don't understand about {orig_title.lower()} is the hidden mechanic behind it.",
        "full_narration": (
            f"What most people don't understand about {orig_title.lower()} is the hidden mechanic behind it. "
            "When you strip away the hype and examine the data, the real breakthrough comes down to a simple principle. "
            "Instead of relying on conventional approaches, the engineers unlocked a 10x shortcut by restructuring the entire workflow. "
            "The result changes the economics completely. Once you see it in action, you can never look at it the same way again."
        ),
        "key_takeaway": "A structural shift in workflow unlocks an order-of-magnitude efficiency gain.",
        "detected_credits": detect_source_credits(video.get("description", ""))
    }

def render_repurposed_video(
    video_id: str,
    account_id: str,
    narration_text: str,
    voice_key: str = "christopher",
    format_mode: str = "original_16_9",      # 'original_16_9' or 'shorts_9_16'
    watermark_defense: str = "punch_in",     # 'none', 'punch_in', 'scrim'
    burn_subtitles: bool = True
) -> Dict[str, Any]:
    """
    Complete end-to-end rendering pipeline:
    1. Downloads clean source video via yt-dlp
    2. Synthesizes studio narration via edge-tts
    3. Aligns subtitles with Whisper
    4. Applies FFmpeg smart crop, punch-in, or scrim defense
    5. Mutes old audio, replaces with narration, burns styled subtitles
    6. Produces final MP4 ready for YouTube!
    """
    job_id = uuid.uuid4().hex[:8]
    work_dir = os.path.join(TEMP_DIR, job_id)
    os.makedirs(work_dir, exist_ok=True)
    
    # 1. Download source video
    video_path = download_source_video(video_id)
    
    # 2. Generate Narration Audio
    audio_path = os.path.join(work_dir, "narration.mp3")
    generate_narration(narration_text, audio_path, voice_key=voice_key)
    audio_duration = get_media_duration(audio_path)
    
    # 3. Generate Subtitles (CapCut kinetic ASS with word-by-word bounce)
    ass_path = os.path.join(work_dir, "subtitles.ass")
    if burn_subtitles:
        generate_ass_from_audio(audio_path, ass_path, format_mode=format_mode)
        
    # 4. Construct FFmpeg Pipeline
    output_mp4 = os.path.join(RENDERS_DIR, f"repurposed_{video_id}_{job_id}.mp4")
    
    filter_chains = []
    
    # Format conversion
    if format_mode == "shorts_9_16":
        # 9:16 vertical center-crop (automatically cuts off 16:9 side watermarks & bottom subtitles)
        filter_chains.append("crop=ih*9/16:ih")
    elif watermark_defense == "punch_in":
        # 8% clean punch-in zoom to eliminate outer edge logos/captions
        filter_chains.append("scale=1.08*iw:-1,crop=iw/1.08:ih/1.08")
        
    # Lower-third scrim defense (if selected)
    if watermark_defense == "scrim":
        # Dark subtle vignette box over bottom 24% of frame
        filter_chains.append("drawbox=x=0:y=ih*0.76:w=iw:h=ih*0.24:color=black@0.70:t=fill")
        
    # Burn styled CapCut kinetic subtitles
    if burn_subtitles and os.path.exists(ass_path) and os.path.getsize(ass_path) > 10:
        # Windows path escaping for ffmpeg ass filter
        escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        subtitle_filter = f"ass='{escaped_ass}'"
        filter_chains.append(subtitle_filter)
        
    vf_arg = ",".join(filter_chains) if filter_chains else "null"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex", f"[0:v]{vf_arg}[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{audio_duration + 0.5:.2f}",
        "-pix_fmt", "yuv420p",
        output_mp4
    ]
    
    print(f"[FFmpeg] Executing render command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Create or update project entry in DB
    video = get_video_by_id(video_id)
    project_id = f"proj-rep-{job_id}"
    project = create_project(
        project_id=project_id,
        account_id=account_id,
        source_type="repurpose",
        title=video.get("title", "Repurposed Video") if video else "Repurposed Video",
        topic=video.get("title", ""),
        source_video_id=video_id,
        stage="ready",
        script_data={
            "narration": narration_text,
            "voice": voice_key,
            "format": format_mode,
            "watermark_defense": watermark_defense
        }
    )
    
    update_project(
        project_id=project_id,
        stage="ready",
        assets_data={
            "output_video": f"/renders/{os.path.basename(output_mp4)}",
            "local_path": output_mp4,
            "duration": audio_duration,
            "job_id": job_id
        }
    )
    
    return {
        "job_id": job_id,
        "project_id": project_id,
        "status": "completed",
        "video_url": f"/renders/{os.path.basename(output_mp4)}",
        "duration": audio_duration
    }
