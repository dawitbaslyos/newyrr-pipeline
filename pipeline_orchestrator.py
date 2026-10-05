import os
import re
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image, ImageDraw, ImageFont

from config import Config
from script_generator import ScriptGenerator
from image_runner import ImageGenerator
from minimax_runner import MiniMaxRunPodClient
from audio_generator import AudioGenerator
from openrouter_video import OpenRouterVideoClient
from repurpose_slicer import repurpose_slicer

class VideoPipelineOrchestrator:
    """
    Coordinates staged production:
    Stage 1: Script & Scene Breakdown
    Stage 2: Frames First (Nano Banana 2 Keyframes + Studio Audio)
    Stage 3: Video Animation (MiniMax H3 Max Turbo on RunPod or Seedance 2.0 on OpenRouter)
    Stage 4: Assembly & Subtitle Placement
    """

    def __init__(self):
        self.script_gen = ScriptGenerator()
        self.image_gen = ImageGenerator()
        self.minimax_client = MiniMaxRunPodClient()
        self.audio_gen = AudioGenerator()
        self.openrouter_video = OpenRouterVideoClient()

    def create_project_slug(self, title: str) -> str:
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_')
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"{slug[:25]}_{timestamp}"

    def create_draft(
        self,
        topic: str,
        aspect_ratio: str = "9:16",
        art_style: Optional[str] = None,
        tts_voice: Optional[str] = None,
        channel_handle: Optional[str] = None,
        channel_niche: Optional[str] = None,
        reference_url: Optional[str] = None,
        project_type: str = "create"
    ) -> Dict[str, Any]:
        """
        Stage 1: Generates script and scene layout. Does NOT generate frames or videos yet.
        """
        try:
            from channel_manager import ChannelManager
            cm = ChannelManager()
            active = cm.get_data().get("active_channel") or {}
            handle = channel_handle or active.get("handle", "@Newyrr")
            niche = channel_niche or active.get("niche", "Shorts science. How and what if moments.")
        except Exception:
            handle = channel_handle or "@Newyrr"
            niche = channel_niche or "Shorts science. How and what if moments."

        print(f"[Orchestrator] Creating Draft for Topic: '{topic}' ({aspect_ratio}), Mode: {project_type}, Style: {art_style}, Voice: {tts_voice}, Channel: {handle}, Reference: {reference_url}")
        script_data = self.script_gen.generate_script(
            topic,
            art_style=art_style,
            channel_handle=handle,
            channel_niche=niche,
            reference_url=reference_url
        )
        project_slug = self.create_project_slug(script_data.get("title", topic))
        project_dir = Config.PROJECTS_DIR / project_slug
        project_dir.mkdir(parents=True, exist_ok=True)

        source_video_path = None
        timeline = []
        if project_type == "repurpose" and reference_url:
            try:
                dest_video = project_dir / "source_video.mp4"
                source_video_path = repurpose_slicer.download_source_video(reference_url, dest_video)
                total_dur = repurpose_slicer.get_video_duration(source_video_path)
                cuts = repurpose_slicer.detect_scenes(source_video_path)
                num_sc = len(script_data.get("scenes", [])) or 5
                timeline = repurpose_slicer.calculate_scene_timeline(total_dur, num_sc, cuts)
                print(f"[Orchestrator] Repurpose Source Ready: {source_video_path} ({total_dur:.1f}s, {len(cuts)} cuts detected)")
            except Exception as e:
                print(f"[Orchestrator] Repurpose download warning: {e}")

        manifest = {
            "project_name": project_slug,
            "topic": topic,
            "aspect_ratio": aspect_ratio,
            "project_type": project_type,
            "source_video_path": str(source_video_path) if source_video_path else None,
            "art_style": art_style or getattr(Config, "ACTIVE_ART_STYLE", "photo_35mm"),
            "tts_voice": tts_voice or getattr(Config, "ACTIVE_TTS_VOICE", "Charon"),
            "reference_url": reference_url,
            "title": script_data.get("title"),
            "hook": script_data.get("hook"),
            "loop_connection": script_data.get("loop_connection"),
            "caption_y_percent": 72.0,
            "status": "DRAFT_CREATED",
            "scenes": []
        }

        for idx, scene in enumerate(script_data.get("scenes", [])):
            sc_timing = timeline[idx] if idx < len(timeline) else {"start": idx * 5.0, "duration": 5.0}
            manifest["scenes"].append({
                "scene_number": scene["scene_number"],
                "escalation_level": scene.get("escalation_level", f"Beat {scene['scene_number']}"),
                "focal_point": scene.get("focal_point", ""),
                "narration": scene["narration"],
                "duration_seconds": scene.get("duration_seconds", sc_timing.get("duration", 5)),
                "source_start_time": sc_timing.get("start", idx * 5.0),
                "source_duration": sc_timing.get("duration", 5.0),
                "flux_image_prompt": scene.get("flux_image_prompt", ""),
                "minimax_motion_prompt": scene.get("minimax_motion_prompt", ""),
                "sfx_cue": scene.get("sfx_cue", "Cinematic"),
                "image_file": None,
                "audio_file": None,
                "video_file": None,
                "status": "PENDING_FRAME"
            })

        self._save_manifest(project_slug, manifest)
        return manifest

    def generate_single_scene_frame(self, project_name: str, scene_number: int) -> Dict[str, Any]:
        """
        Generates Keyframe Still + Audio for a single scene and saves immediately.
        In Repurpose mode: Slices keyframe from source video footage (Zero OpenRouter credits).
        """
        manifest = self.get_manifest(project_name)
        project_dir = Config.PROJECTS_DIR / project_name
        width, height = (768, 1344) if manifest.get("aspect_ratio", "9:16") == "9:16" else (1344, 768)
        voice = manifest.get("tts_voice") or getattr(Config, "ACTIVE_TTS_VOICE", "Charon")
        is_repurpose = manifest.get("project_type") == "repurpose"
        source_video = manifest.get("source_video_path")

        for scene in manifest.get("scenes", []):
            if scene["scene_number"] == scene_number:
                num = scene["scene_number"]
                # 1. Audio
                audio_path = project_dir / f"scene_{num:02d}_audio.mp3"
                self.audio_gen.generate_speech(scene["narration"], str(audio_path), voice=voice)
                scene["audio_file"] = str(audio_path)
                scene["actual_audio_duration"] = self.audio_gen.get_audio_duration(str(audio_path))

                # 2. Keyframe Image
                image_path = project_dir / f"scene_{num:02d}_flux.png"
                if is_repurpose and source_video and Path(source_video).exists():
                    print(f"[Orchestrator] Repurpose Workflow: Extracting keyframe from source footage for Scene {num} (Zero OpenRouter)")
                    start_t = scene.get("source_start_time", (num - 1) * 5.0)
                    repurpose_slicer.extract_scene_keyframe(
                        source_video=Path(source_video),
                        output_image=image_path,
                        timestamp=start_t + 0.5,
                        aspect_ratio=manifest.get("aspect_ratio", "9:16"),
                        punch_in=True
                    )
                else:
                    self.image_gen.generate_image(
                        prompt=scene["flux_image_prompt"],
                        output_path=str(image_path),
                        width=width,
                        height=height
                    )
                scene["image_file"] = str(image_path)
                scene["status"] = "FRAME_READY"
                break

        # Check if all frames are ready
        all_ready = all(s.get("image_file") for s in manifest.get("scenes", []))
        if all_ready:
            manifest["status"] = "FRAMES_READY"
        self._save_manifest(project_name, manifest)
        return manifest

    def generate_frames_for_project(self, project_name: str) -> Dict[str, Any]:
        """
        Stage 2: Generates Keyframe Stills FIRST for all scenes + Audio.
        In Repurpose mode: Uses local video slicer, zero OpenRouter image models.
        """
        manifest = self.get_manifest(project_name)
        project_dir = Config.PROJECTS_DIR / project_name
        width, height = (768, 1344) if manifest.get("aspect_ratio", "9:16") == "9:16" else (1344, 768)
        is_repurpose = manifest.get("project_type") == "repurpose"
        source_video = manifest.get("source_video_path")

        print(f"[Orchestrator] Generating Keyframes First for {project_name} (Repurpose={is_repurpose})...")
        voice = manifest.get("tts_voice") or getattr(Config, "ACTIVE_TTS_VOICE", "Charon")
        for scene in manifest.get("scenes", []):
            num = scene["scene_number"]
            # 1. Audio
            audio_path = project_dir / f"scene_{num:02d}_audio.mp3"
            self.audio_gen.generate_speech(scene["narration"], str(audio_path), voice=voice)
            scene["audio_file"] = str(audio_path)
            scene["actual_audio_duration"] = self.audio_gen.get_audio_duration(str(audio_path))

            # 2. Keyframe Image
            image_path = project_dir / f"scene_{num:02d}_flux.png"
            if is_repurpose and source_video and Path(source_video).exists():
                print(f"[Orchestrator] Repurpose Workflow: Slicing keyframe for Scene {num} from source")
                start_t = scene.get("source_start_time", (num - 1) * 5.0)
                repurpose_slicer.extract_scene_keyframe(
                    source_video=Path(source_video),
                    output_image=image_path,
                    timestamp=start_t + 0.5,
                    aspect_ratio=manifest.get("aspect_ratio", "9:16"),
                    punch_in=True
                )
            else:
                self.image_gen.generate_image(
                    prompt=scene["flux_image_prompt"],
                    output_path=str(image_path),
                    width=width,
                    height=height
                )
            scene["image_file"] = str(image_path)
            scene["status"] = "FRAME_READY"
            self._save_manifest(project_name, manifest)

        manifest["status"] = "FRAMES_READY"
        self._save_manifest(project_name, manifest)
        return manifest

    def regenerate_single_frame(self, project_name: str, scene_number: int, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Re-rolls a specific frame if the creator wants to tweak or redo it.
        """
        manifest = self.get_manifest(project_name)
        project_dir = Config.PROJECTS_DIR / project_name
        width, height = (768, 1344) if manifest.get("aspect_ratio", "9:16") == "9:16" else (1344, 768)
        is_repurpose = manifest.get("project_type") == "repurpose"
        source_video = manifest.get("source_video_path")

        for scene in manifest.get("scenes", []):
            if scene["scene_number"] == scene_number:
                prompt = custom_prompt or scene["flux_image_prompt"]
                scene["flux_image_prompt"] = prompt
                image_path = project_dir / f"scene_{scene_number:02d}_flux.png"
                if is_repurpose and source_video and Path(source_video).exists():
                    print(f"[Orchestrator] Repurpose Workflow: Re-extracting keyframe for Scene {scene_number}")
                    start_t = scene.get("source_start_time", (scene_number - 1) * 5.0)
                    repurpose_slicer.extract_scene_keyframe(
                        source_video=Path(source_video),
                        output_image=image_path,
                        timestamp=start_t + 1.8,
                        aspect_ratio=manifest.get("aspect_ratio", "9:16"),
                        punch_in=True
                    )
                else:
                    self.image_gen.generate_image(
                        prompt=prompt,
                        output_path=str(image_path),
                        width=width,
                        height=height,
                        seed=int(time.time())
                    )
                scene["image_file"] = str(image_path)
                scene["status"] = "FRAME_READY"
                break

        self._save_manifest(project_name, manifest)
        return manifest

    def _render_scene_video_internal(
        self,
        scene: Dict[str, Any],
        project_dir: Path,
        aspect_ratio: str,
        provider: str,
        prompt_enhance: bool = False,
        upscale_2k: bool = False
    ) -> str:
        num = scene["scene_number"]
        image_file = scene.get("image_file")
        audio_file = scene.get("audio_file")
        video_file = project_dir / f"scene_{num:02d}_video.mp4"
        scene_duration = int(round(max(4, scene.get("actual_audio_duration", 5))))

        # Repurpose Workflow: Slices segment from source footage with muted audio (Zero OpenRouter video credits!)
        manifest = self.get_manifest(project_dir.name)
        if manifest.get("project_type") == "repurpose":
            source_video = manifest.get("source_video_path")
            if source_video and Path(source_video).exists():
                print(f"[Orchestrator] Repurpose Workflow: Slicing video from source footage for Scene {num} (Zero OpenRouter)")
                start_t = scene.get("source_start_time", (num - 1) * 5.0)
                repurpose_slicer.slice_scene_video(
                    source_video=Path(source_video),
                    output_video=video_file,
                    start_time=start_t,
                    duration=scene_duration,
                    aspect_ratio=aspect_ratio,
                    punch_in=True
                )
                scene["video_file"] = str(video_file)
                scene["status"] = "VIDEO_READY"
                return str(video_file)

        # 1. MiniMax H3 Max Turbo on RunPod Serverless (if configured and explicit)
        if "runpod" in provider.lower() and self.minimax_client.api_key and self.minimax_client.endpoint_id:
            try:
                payload = self.minimax_client.build_runpod_payload(
                    image_path_or_url=str(image_file),
                    motion_prompt=scene["minimax_motion_prompt"],
                    duration=scene_duration,
                    prompt_enhance=prompt_enhance,
                    upscale_2k=upscale_2k
                )
                self.minimax_client.render_scene_video(payload, str(video_file))
            except Exception as e:
                print(f"[MiniMax H3] RunPod error: {e}. Falling back to OpenRouter Seedance 2.0 Mini...")
                self.openrouter_video.render_video_i2v(
                    image_path=str(image_file),
                    motion_prompt=scene["minimax_motion_prompt"],
                    output_path=str(video_file),
                    model="bytedance/seedance-2.0-mini",
                    duration=scene_duration,
                    aspect_ratio=aspect_ratio,
                    resolution="720p"
                )

        # 2. MiniMax Hailuo-3 via OpenRouter
        elif "hailuo" in provider.lower():
            self.openrouter_video.render_video_i2v(
                image_path=str(image_file),
                motion_prompt=scene["minimax_motion_prompt"],
                output_path=str(video_file),
                model="minimax/hailuo-3",
                duration=scene_duration,
                aspect_ratio=aspect_ratio,
                resolution="720p"
            )

        # 3. Default: ByteDance Seedance 2.0 Mini via OpenRouter ($0.03363/s)
        else:
            self.openrouter_video.render_video_i2v(
                image_path=str(image_file),
                motion_prompt=scene["minimax_motion_prompt"],
                output_path=str(video_file),
                model="bytedance/seedance-2.0-mini",
                duration=scene_duration,
                aspect_ratio=aspect_ratio,
                resolution="720p"
            )

        scene["video_file"] = str(video_file)
        scene["status"] = "VIDEO_READY"
        return str(video_file)

    def generate_single_scene_video(self, project_name: str, scene_number: int, custom_motion_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Renders video animation for a single scene and saves immediately.
        """
        manifest = self.get_manifest(project_name)
        project_dir = Config.PROJECTS_DIR / project_name
        provider = getattr(Config, "ACTIVE_VIDEO_PROVIDER", "bytedance/seedance-2.0-mini")
        aspect_ratio = manifest.get("aspect_ratio", "9:16")

        for scene in manifest.get("scenes", []):
            if scene["scene_number"] == scene_number:
                if custom_motion_prompt:
                    scene["minimax_motion_prompt"] = custom_motion_prompt
                self._render_scene_video_internal(scene, project_dir, aspect_ratio, provider)
                break

        all_ready = all(s.get("video_file") for s in manifest.get("scenes", []))
        if all_ready:
            manifest["status"] = "VIDEOS_READY"
        self._save_manifest(project_name, manifest)
        return manifest

    def render_videos_for_project(self, project_name: str, prompt_enhance: bool = False, upscale_2k: bool = False) -> Dict[str, Any]:
        """
        Stage 3: Triggers Video Animation for all scenes.
        Saves manifest incrementally after every scene finishes.
        """
        manifest = self.get_manifest(project_name)
        project_dir = Config.PROJECTS_DIR / project_name
        provider = getattr(Config, "ACTIVE_VIDEO_PROVIDER", "bytedance/seedance-2.0-mini")
        aspect_ratio = manifest.get("aspect_ratio", "9:16")

        print(f"[Orchestrator] Rendering Videos for approved frames in {project_name} using '{provider}'...")
        for scene in manifest.get("scenes", []):
            self._render_scene_video_internal(scene, project_dir, aspect_ratio, provider, prompt_enhance, upscale_2k)
            # Incremental save so UI displays completed video immediately!
            self._save_manifest(project_name, manifest)

        manifest["status"] = "VIDEOS_READY"
        self._save_manifest(project_name, manifest)
        return manifest

    def regenerate_single_video(self, project_name: str, scene_number: int, custom_motion_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Re-rolls video animation for a single scene independently.
        """
        manifest = self.get_manifest(project_name)
        project_dir = Config.PROJECTS_DIR / project_name
        provider = getattr(Config, "ACTIVE_VIDEO_PROVIDER", "bytedance/seedance-2.0-mini")
        aspect_ratio = manifest.get("aspect_ratio", "9:16")

        for scene in manifest.get("scenes", []):
            if scene["scene_number"] == scene_number:
                if custom_motion_prompt:
                    scene["minimax_motion_prompt"] = custom_motion_prompt
                self._render_scene_video_internal(scene, project_dir, aspect_ratio, provider)
                break

        self._save_manifest(project_name, manifest)
        return manifest

    def save_scene_text(self, project_name: str, scene_number: int, narration: Optional[str] = None, flux_prompt: Optional[str] = None, motion_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Saves user edits to narration or prompts for a scene without re-rolling yet.
        """
        manifest = self.get_manifest(project_name)
        for scene in manifest.get("scenes", []):
            if scene["scene_number"] == scene_number:
                if narration is not None:
                    scene["narration"] = narration
                if flux_prompt is not None:
                    scene["flux_image_prompt"] = flux_prompt
                if motion_prompt is not None:
                    scene["minimax_motion_prompt"] = motion_prompt
                break
        self._save_manifest(project_name, manifest)
        return manifest

    def generate_thumbnail(self, project_name: str, headline: Optional[str] = None) -> str:
        """
        CapCut-Style Thumbnail Generator: Takes the best scene frame,
        applies high-contrast color grading and bold punchy text overlay.
        """
        manifest = self.get_manifest(project_name)
        project_dir = Config.PROJECTS_DIR / project_name
        thumb_path = project_dir / "thumbnail.png"

        # Use Scene 1 image as base
        base_img_path = None
        for s in manifest.get("scenes", []):
            if s.get("image_file") and os.path.exists(s["image_file"]):
                base_img_path = s["image_file"]
                break

        if not base_img_path:
            return ""

        img = Image.open(base_img_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        w, h = img.size

        text_to_draw = headline or manifest.get("hook", manifest.get("title", "DON'T LOOK AWAY")).upper()
        # Clean text
        text_to_draw = text_to_draw[:40]

        # Draw dark gradient box at bottom or top
        box_y = int(h * 0.65)
        draw.rectangle([(0, box_y), (w, box_y + 180)], fill=(0, 0, 0, 200))
        # Draw bold border around text box
        draw.rectangle([(0, box_y), (w, box_y + 180)], outline=(6, 182, 212), width=5)

        # Draw headline
        draw.text((w // 2, box_y + 90), text_to_draw, fill=(255, 255, 0), anchor="mm")

        img.save(thumb_path)
        manifest["thumbnail_file"] = str(thumb_path)
        self._save_manifest(project_name, manifest)
        print(f"[Orchestrator] Created high-CTR thumbnail: {thumb_path}")
        return str(thumb_path)

    def _create_mock_video_clip(self, image_path: str, audio_path: str, output_path: str, duration: float = 5.0):
        import subprocess
        clean_img = image_path.replace("\\", "/")
        clean_out = output_path.replace("\\", "/")
        clean_aud = audio_path.replace("\\", "/")
        
        # Clean static hold without any childish zoompan
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", clean_img,
            "-i", clean_aud,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=768:1344:force_original_aspect_ratio=increase,crop=768:1344,fps=30",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            clean_out
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            print(f"[Orchestrator] Warning generating static clip: {e}")

    def get_manifest(self, project_name: str) -> Dict[str, Any]:
        p = Config.PROJECTS_DIR / project_name / "manifest.json"
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_manifest(self, project_name: str, manifest: Dict[str, Any]):
        p = Config.PROJECTS_DIR / project_name / "manifest.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
