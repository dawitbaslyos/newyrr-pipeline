import os
import sys
import json
import subprocess
from pathlib import Path
import yt_dlp
import whisper

OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "case_studies"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEOS = [
    {
        "channel": "@zackdfilms",
        "type": "recent",
        "url": "https://www.youtube.com/shorts/dLQQV73fUI0",
        "id": "dLQQV73fUI0",
        "label": "zackdfilms_recent_spider_bite"
    },
    {
        "channel": "@zackdfilms",
        "type": "popular",
        "url": "https://www.youtube.com/shorts/ttuKeS5k4Uo",
        "id": "ttuKeS5k4Uo",
        "label": "zackdfilms_popular_stitches"
    },
    {
        "channel": "@LoadedDiceShorts",
        "type": "recent",
        "url": "https://www.youtube.com/shorts/AuX7znns3fs",
        "id": "AuX7znns3fs",
        "label": "loadeddice_recent_illegal_gamble"
    },
    {
        "channel": "@LoadedDiceShorts",
        "type": "popular",
        "url": "https://www.youtube.com/shorts/B5fQLSLsXCw",
        "id": "B5fQLSLsXCw",
        "label": "loadeddice_popular_eye_in_the_sky"
    },
    {
        "channel": "@PracticalPsychology",
        "type": "recent",
        "url": "https://www.youtube.com/shorts/2MuqNwAockc",
        "id": "2MuqNwAockc",
        "label": "practical_recent_make_million"
    },
    {
        "channel": "@PracticalPsychology",
        "type": "popular",
        "url": "https://www.youtube.com/shorts/O_c7hX8Kkck",
        "id": "O_c7hX8Kkck",
        "label": "practical_popular_lie_truth"
    }
]

print("Loading Whisper base model...")
model = whisper.load_model("base")

all_data = {}

for item in VIDEOS:
    label = item["label"]
    vid = item["id"]
    vid_dir = OUTPUT_DIR / label
    vid_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n=======================================================")
    print(f"Processing: {label} ({vid})")
    
    # Check info
    info = {}
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
    except Exception as e:
        print(f"Metadata extract warning: {e}")
        
    title = info.get("title", label)
    duration = info.get("duration", 30) or 30
    view_count = info.get("view_count", 0) or 0
    channel_name = info.get("uploader", item["channel"])
    
    # 1. Download audio
    audio_path = vid_dir / f"{vid}.mp3"
    if not audio_path.exists() or audio_path.stat().st_size < 1000:
        print("Downloading audio...")
        cmd_audio = [
            "yt-dlp",
            "-f", "ba/b",
            "-x", "--audio-format", "mp3",
            f"https://www.youtube.com/watch?v={vid}",
            "-o", str(vid_dir / f"{vid}.%(ext)s")
        ]
        subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # Check audio candidates
    if not audio_path.exists():
        for cand in vid_dir.glob(f"*{vid}*.mp3*"):
            if cand.stat().st_size > 1000:
                import shutil
                shutil.copy(cand, audio_path)
                break
                
    # 2. Download lightweight video for frame inspection (360p/480p)
    video_path = vid_dir / f"{vid}_video.mp4"
    if not video_path.exists() or video_path.stat().st_size < 10000:
        print("Downloading video for keyframe extraction...")
        cmd_video = [
            "yt-dlp",
            "-f", "bv*[height<=480]+ba/b[height<=480]/worstvideo+worstaudio/worst",
            "--merge-output-format", "mp4",
            f"https://www.youtube.com/watch?v={vid}",
            "-o", str(video_path)
        ]
        subprocess.run(cmd_video, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. Transcribe audio with Whisper
    full_transcript = ""
    segments = []
    if audio_path.exists() and audio_path.stat().st_size > 1000:
        print(f"Transcribing {audio_path.name}...")
        try:
            res = model.transcribe(str(audio_path), fp16=False)
            full_transcript = res.get("text", "").strip()
            for seg in res.get("segments", []):
                segments.append({
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2),
                    "text": seg["text"].strip()
                })
        except Exception as e:
            print(f"Whisper transcription failed: {e}")
    else:
        print(f"Audio file missing or empty for {vid}")

    # 4. Extract keyframe snapshots from video
    frame_files = []
    if video_path.exists() and video_path.stat().st_size > 10000:
        print(f"Extracting keyframes from {video_path.name}...")
        # Get exact duration
        try:
            out = subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
            ]).decode().strip()
            duration = float(out)
        except Exception:
            pass
            
        points = [1.0, max(2.0, duration * 0.25), max(4.0, duration * 0.5), max(6.0, duration * 0.75), max(1.0, duration - 2.0)]
        for idx, pt in enumerate(points):
            fpath = vid_dir / f"frame_{idx+1}_{int(pt)}s.jpg"
            if not fpath.exists():
                subprocess.run([
                    "ffmpeg", "-y", "-ss", str(pt), "-i", str(video_path),
                    "-vframes", "1", "-q:v", "2", str(fpath)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if fpath.exists():
                frame_files.append(str(fpath.name))

    words = len(full_transcript.split())
    wpm = round((words / (duration / 60)), 1) if duration > 0 else 0

    item_data = {
        "channel": item["channel"],
        "type": item["type"],
        "url": item["url"],
        "id": vid,
        "title": title,
        "duration": round(duration, 1),
        "view_count": view_count,
        "word_count": words,
        "words_per_minute": wpm,
        "transcript": full_transcript,
        "segments": segments,
        "frames": frame_files
    }

    # Save data.json and transcript.txt
    with open(vid_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(item_data, f, indent=2, ensure_ascii=False)
        
    with open(vid_dir / "transcript.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n")
        f.write(f"Channel: {channel_name} | Views: {view_count:,} | Duration: {round(duration, 1)}s | WPM: {wpm}\n")
        f.write(f"URL: {item['url']}\n\n")
        f.write("=== FULL SCRIPT / TRANSCRIPT ===\n")
        f.write(full_transcript + "\n\n")
        f.write("=== TIMED BEATS (AUDIO SEGMENTS) ===\n")
        for seg in segments:
            f.write(f"[{seg['start']}s -> {seg['end']}s]: {seg['text']}\n")

    all_data[label] = item_data
    print(f"FINISHED {label}: {words} words, {len(segments)} beats, {len(frame_files)} frames extracted.")

with open(OUTPUT_DIR / "all_case_studies.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print("\n>>> ALL 6 CASE STUDIES DOWNLOADED, TRANSCRIBED & SAVED SUCCESSFULLY! <<<")
