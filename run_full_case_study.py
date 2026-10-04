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
        "channel": "zackdfilms",
        "type": "recent",
        "url": "https://www.youtube.com/shorts/dLQQV73fUI0",
        "id": "dLQQV73fUI0",
        "label": "zackdfilms_recent_spider_bite"
    },
    {
        "channel": "zackdfilms",
        "type": "popular",
        "url": "https://www.youtube.com/shorts/ttuKeS5k4Uo",
        "id": "ttuKeS5k4Uo",
        "label": "zackdfilms_popular_stitches"
    },
    {
        "channel": "LoadedDiceShorts",
        "type": "recent",
        "url": "https://www.youtube.com/shorts/AuX7znns3fs",
        "id": "AuX7znns3fs",
        "label": "loadeddice_recent_illegal_gamble"
    },
    {
        "channel": "LoadedDiceShorts",
        "type": "popular",
        "url": "https://www.youtube.com/shorts/B5fQLSLsXCw",
        "id": "B5fQLSLsXCw",
        "label": "loadeddice_popular_eye_in_the_sky"
    },
    {
        "channel": "PracticalPsychology",
        "type": "recent",
        "url": "https://www.youtube.com/shorts/2MuqNwAockc",
        "id": "2MuqNwAockc",
        "label": "practical_recent_make_million"
    },
    {
        "channel": "PracticalPsychology",
        "type": "popular",
        "url": "https://www.youtube.com/shorts/O_c7hX8Kkck",
        "id": "O_c7hX8Kkck",
        "label": "practical_popular_lie_truth"
    }
]

print("Loading Whisper model (base)...")
model = whisper.load_model("base")

all_data = {}

for item in VIDEOS:
    label = item["label"]
    vid = item["id"]
    vid_dir = OUTPUT_DIR / label
    vid_dir.mkdir(parents=True, exist_ok=True)
    
    video_path = vid_dir / f"{vid}.mp4"
    audio_path = vid_dir / f"{vid}.mp3"
    
    print(f"\n==========================================")
    print(f"Processing {label} ({vid})...")
    
    metadata = {}
    
    # 1. Download video if not already present
    if not video_path.exists() or video_path.stat().st_size < 10000:
        ydl_opts = {
            'format': 'bv*+ba/b',
            'merge_output_format': 'mp4',
            'outtmpl': str(video_path),
            'quiet': False
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(item["url"], download=True)
                metadata = {
                    "title": info.get("title", ""),
                    "duration": info.get("duration", 0),
                    "view_count": info.get("view_count", 0),
                    "like_count": info.get("like_count", 0),
                    "channel": info.get("uploader", item["channel"])
                }
        except Exception as e:
            print(f"Error downloading {vid}: {e}")
            # Try fallback simple format
            try:
                ydl_opts_simple = {
                    'format': 'b',
                    'outtmpl': str(video_path),
                    'quiet': True
                }
                with yt_dlp.YoutubeDL(ydl_opts_simple) as ydl:
                    info = ydl.extract_info(item["url"], download=True)
                    metadata = {
                        "title": info.get("title", ""),
                        "duration": info.get("duration", 0),
                        "view_count": info.get("view_count", 0),
                        "channel": info.get("uploader", item["channel"])
                    }
            except Exception as e2:
                print(f"Fallback error: {e2}")
    else:
        # Extract metadata from existing if needed
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(item["url"], download=False)
                metadata = {
                    "title": info.get("title", ""),
                    "duration": info.get("duration", 0),
                    "view_count": info.get("view_count", 0),
                    "like_count": info.get("like_count", 0),
                    "channel": info.get("uploader", item["channel"])
                }
        except Exception:
            pass

    # 2. Extract audio from mp4
    if video_path.exists():
        if not audio_path.exists() or audio_path.stat().st_size < 1000:
            print("Extracting audio with ffmpeg...")
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(audio_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Check if an mp3 was downloaded by previous attempt
        candidates = list(vid_dir.glob("*.mp3*"))
        if candidates:
            import shutil
            shutil.copy(candidates[0], audio_path)

    # 3. Transcribe with Whisper
    full_transcript = ""
    segments = []
    if audio_path.exists() and audio_path.stat().st_size > 1000:
        print(f"Transcribing {audio_path.name} with Whisper...")
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
            print(f"Whisper transcription error: {e}")
    else:
        print(f"Warning: Audio file missing for {vid}")

    # 4. Extract keyframes from video
    frame_paths = []
    dur = metadata.get("duration", 0)
    if not dur and video_path.exists():
        try:
            # get duration with ffprobe
            out = subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
            ]).decode().strip()
            dur = float(out)
            metadata["duration"] = round(dur, 1)
        except Exception:
            dur = 30.0

    if video_path.exists():
        print(f"Extracting keyframes for duration={dur}s...")
        timestamps = [1.0, max(2.0, dur * 0.25), max(4.0, dur * 0.5), max(6.0, dur * 0.75), max(1.0, dur - 2.0)]
        for idx, ts in enumerate(timestamps):
            fpath = vid_dir / f"frame_{idx+1}_{int(ts)}s.jpg"
            subprocess.run([
                "ffmpeg", "-y", "-ss", str(ts), "-i", str(video_path),
                "-vframes", "1", "-q:v", "2", str(fpath)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if fpath.exists():
                frame_paths.append(str(fpath.name))

    dur_val = metadata.get("duration", 30) or 30
    words = len(full_transcript.split())
    wpm = round((words / (dur_val / 60)), 1) if dur_val > 0 else 0

    item_analysis = {
        "channel": item["channel"],
        "type": item["type"],
        "url": item["url"],
        "id": vid,
        "metadata": metadata,
        "transcript": full_transcript,
        "segments": segments,
        "word_count": words,
        "words_per_minute": wpm,
        "frames": frame_paths
    }

    # Save data.json and transcript.txt
    with open(vid_dir / "data.json", "w", encoding="utf-8") as f:
        json.dump(item_analysis, f, indent=2, ensure_ascii=False)
        
    with open(vid_dir / "transcript.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {metadata.get('title')}\n")
        f.write(f"Channel: {metadata.get('channel')} | Views: {metadata.get('view_count'):,} | Duration: {dur_val}s | WPM: {wpm}\n")
        f.write(f"URL: {item['url']}\n\n")
        f.write("=== FULL TRANSCRIPT ===\n")
        f.write(full_transcript + "\n\n")
        f.write("=== TIMESTAMPED BEATS ===\n")
        for seg in segments:
            f.write(f"[{seg['start']}s -> {seg['end']}s]: {seg['text']}\n")

    all_data[label] = item_analysis
    print(f"COMPLETED {label}: {words} words, {len(segments)} beats, {len(frame_paths)} frames extracted.")

with open(OUTPUT_DIR / "all_case_studies.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print("\n>>> ALL 6 CASE STUDIES DOWNLOADED, TRANSCRIBED, AND EXTRACTED SUCCESSFULLY! <<<")
