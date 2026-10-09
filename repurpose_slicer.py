import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import yt_dlp

try:
    import scenedetect
    from scenedetect import detect, ContentDetector
    HAS_SCENEDETECT = True
except ImportError:
    HAS_SCENEDETECT = False


class RepurposeSlicer:
    """
    Local Video-as-Code & Slicing Engine (Under-the-Hood Repurposing):
    - Zero OpenRouter credits used
    - Downloader: Direct high-res mp4 fetch via yt-dlp
    - Scene Detection: PySceneDetect boundary detection
    - Frame Extractor: FFmpeg smart center-crop & punch-in keyframes
    - Video Slicer: FFmpeg lossless segment slicing & audio muting
    """

    @staticmethod
    def extract_video_id(url_or_id: str) -> str:
        clean = url_or_id.strip()
        if "shorts/" in clean:
            return clean.split("shorts/")[1].split("?")[0].split("/")[0]
        elif "v=" in clean:
            return clean.split("v=")[1].split("&")[0]
        elif "youtu.be/" in clean:
            return clean.split("youtu.be/")[1].split("?")[0]
        return clean

    @classmethod
    def download_source_video(cls, video_url_or_id: str, target_path: Path) -> Path:
        """
        Downloads high-resolution MP4 (up to 1080p) via yt-dlp to target_path.
        Re-uses existing download if already valid.
        """
        if target_path.exists() and target_path.stat().st_size > 100_000:
            print(f"[Repurpose Slicer] Using cached source video: {target_path}")
            return target_path

        target_path.parent.mkdir(parents=True, exist_ok=True)
        video_id = cls.extract_video_id(video_url_or_id)
        url = f"https://www.youtube.com/watch?v={video_id}"

        print(f"[Repurpose Slicer] Downloading source footage for {video_id} (Best 1080p stream)...")
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'outtmpl': str(target_path.with_suffix('')) + '.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
            'max_filesize': 350 * 1024 * 1024
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if target_path.exists():
            return target_path

        # Check if downloaded with variant extension
        parent = target_path.parent
        stem = target_path.stem
        for f in parent.glob(f"{stem}.*"):
            if f.suffix in [".mp4", ".mkv", ".webm"]:
                return f

        raise FileNotFoundError(f"Could not download source video for {video_url_or_id}")

    @classmethod
    def get_video_duration(cls, video_path: Path) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            return float(res.stdout.strip())
        except Exception:
            return 30.0

    @classmethod
    def detect_scenes(cls, video_path: Path, min_duration: float = 2.0) -> List[Dict[str, float]]:
        """
        Uses PySceneDetect to detect physical cuts in the source video.
        Falls back to proportional segmentation if scene detection finds fewer cuts.
        """
        cuts: List[Dict[str, float]] = []
        if HAS_SCENEDETECT:
            try:
                scene_list = detect(str(video_path), ContentDetector(threshold=27.0))
                for scene in scene_list:
                    start_s = getattr(scene[0], 'seconds', scene[0].get_seconds())
                    end_s = getattr(scene[1], 'seconds', scene[1].get_seconds())
                    dur = end_s - start_s
                    if dur >= min_duration:
                        cuts.append({"start": start_s, "end": end_s, "duration": dur})
            except Exception as e:
                print(f"[Repurpose Slicer] PySceneDetect warning: {e}")

        return cuts

    @classmethod
    def calculate_scene_timeline(cls, total_duration: float, num_scenes: int = 5, detected_cuts: Optional[List[Dict[str, float]]] = None) -> List[Dict[str, float]]:
        """
        Aligns scene time windows. If detected cuts exist, uses them; otherwise evenly partitions.
        """
        timeline = []
        if detected_cuts and len(detected_cuts) >= num_scenes:
            for i in range(num_scenes):
                c = detected_cuts[i]
                timeline.append({
                    "start": round(c["start"], 2),
                    "duration": round(c["duration"], 2)
                })
            return timeline

        # Even partitioning fallback
        step = total_duration / max(1, num_scenes)
        for i in range(num_scenes):
            start = round(i * step, 2)
            dur = round(min(step, total_duration - start), 2)
            timeline.append({
                "start": start,
                "duration": max(3.0, dur)
            })
        return timeline

    @classmethod
    def extract_scene_keyframe(
        cls,
        source_video: Path,
        output_image: Path,
        timestamp: float,
        aspect_ratio: str = "9:16",
        punch_in: bool = True
    ) -> Path:
        """
        Extracts a clean still keyframe from the source footage at timestamp.
        Applies smart 9:16 center-crop + 8% punch-in to clean outer watermarks.
        Zero OpenRouter image API calls.
        """
        output_image.parent.mkdir(parents=True, exist_ok=True)
        width, height = (768, 1344) if aspect_ratio == "9:16" else (1344, 768)

        filters = []
        if aspect_ratio == "9:16":
            filters.append("crop=ih*9/16:ih")
            filters.append(f"scale={width}:{height}")
        else:
            filters.append(f"scale={width}:{height}")

        if punch_in:
            filters.append("scale=1.08*iw:-1,crop=iw/1.08:ih/1.08")

        vf_str = ",".join(filters)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(max(0.1, timestamp)),
            "-i", str(source_video),
            "-vframes", "1",
            "-vf", vf_str,
            "-q:v", "2",
            str(output_image)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if not output_image.exists():
            # Fallback without filters
            cmd_fallback = [
                "ffmpeg", "-y",
                "-ss", str(max(0.1, timestamp)),
                "-i", str(source_video),
                "-vframes", "1",
                "-q:v", "2",
                str(output_image)
            ]
            subprocess.run(cmd_fallback, check=True)

        return output_image

    @classmethod
    def slice_scene_video(
        cls,
        source_video: Path,
        output_video: Path,
        start_time: float,
        duration: float,
        aspect_ratio: str = "9:16",
        punch_in: bool = True
    ) -> Path:
        """
        Slices a video segment from source footage with 9:16 framing and muted audio.
        Zero OpenRouter video API calls.
        """
        output_video.parent.mkdir(parents=True, exist_ok=True)
        width, height = (768, 1344) if aspect_ratio == "9:16" else (1344, 768)

        filters = []
        if aspect_ratio == "9:16":
            filters.append("crop=ih*9/16:ih")
            filters.append(f"scale={width}:{height}")
        else:
            filters.append(f"scale={width}:{height}")

        if punch_in:
            filters.append("scale=1.08*iw:-1,crop=iw/1.08:ih/1.08")

        vf_str = ",".join(filters)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(max(0.0, start_time)),
            "-t", str(max(2.0, duration)),
            "-i", str(source_video),
            "-vf", vf_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-an",  # Strip original audio so fresh narration takes over
            "-pix_fmt", "yuv420p",
            str(output_video)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_video


repurpose_slicer = RepurposeSlicer()
