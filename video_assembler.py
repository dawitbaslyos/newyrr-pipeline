import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import Config
from sfx_manager import sfx_manager

class VideoAssembler:
    """
    Assembles scene clips into a unified 9:16 Short:
    - Prepares standardized scene clips (with graceful Ken Burns animation if video wasn't rendered)
    - Concatenates video and audio tracks seamlessly
    - Generates dynamic word-by-word bouncing CapCut ASS subtitles
    - Mixes optional background music (BGM)
    - Burns subtitles and exports the final YouTube Short (.mp4)
    """

    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
        self.used_dir = Config.USED_DIR

    def generate_ass_subtitles(
        self,
        manifest: Dict[str, Any],
        ass_output_path: str,
        video_width: int = 768,
        video_height: int = 1344,
        caption_y_percent: float = 72.0,
        caption_color: str = "yellow",
        font_family: str = "Impact",
        font_size: int = 52,
        outline_thickness: float = 4.5,
        all_caps: bool = True,
        chunk_size: int = 3
    ):
        """
        Creates authentic CapCut kinetic subtitles with word-by-word karaoke bounce.
        caption_y_percent: 0 = top of screen, 50 = middle, 100 = bottom.
        ASS Alignment 2 is bottom-center, so MarginV is distance from bottom.
        """
        # Distance from bottom in pixels
        margin_v = int(video_height * max(0.06, min(0.92, (1.0 - (caption_y_percent / 100.0)))))

        color_map = {
            "yellow": "&H0000FFFF&",
            "cyan": "&H00FFFF00&",
            "emerald": "&H0050FA7B&",
            "white": "&H00FFFFFF&",
            "red": "&H002020FF&",
            "orange": "&H000080FF&"
        }
        highlight_color = color_map.get(caption_color.lower(), "&H0000FFFF&")
        safe_font = font_family if font_family in ["Impact", "Montserrat", "Arial Black", "Anton", "Arial"] else "Impact"

        ass_header = f"""[Script Info]
Title: CapCut Style Kinetic Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: {video_width}
PlayResY: {video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapCutDefault,{safe_font},{font_size},&H00FFFFFF,{highlight_color},&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,{outline_thickness},2,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        current_time_offset = 0.0
        c_size = max(1, min(6, chunk_size))

        for scene in manifest.get("scenes", []):
            narration = scene.get("narration", "").strip()
            duration = scene.get("actual_audio_duration", scene.get("duration_seconds", 5.0))
            words = narration.split()
            if not words:
                current_time_offset += duration
                continue

            word_dur = duration / len(words)

            for i in range(0, len(words), c_size):
                chunk_words = words[i:i + c_size]
                chunk_start = current_time_offset + (i * word_dur)

                # Generate a kinetic sub-event for each word in the chunk
                for j, word in enumerate(chunk_words):
                    word_start = chunk_start + (j * word_dur)
                    word_end = chunk_start + ((j + 1) * word_dur)

                    # Build text where current word is highlighted and popped, others white
                    formatted_words = []
                    for k, w in enumerate(chunk_words):
                        clean_w = w.upper().replace("{", "").replace("}", "") if all_caps else w.replace("{", "").replace("}", "")
                        if k == j:
                            formatted_words.append(f"{{\\c{highlight_color}\\fscx108\\fscy108}}{clean_w}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}")
                        else:
                            formatted_words.append(f"{{\\c&H00FFFFFF&}}{clean_w}")

                    dialogue_text = " ".join(formatted_words)
                    start_str = self._format_ass_time(word_start)
                    end_str = self._format_ass_time(word_end)
                    event_line = f"Dialogue: 0,{start_str},{end_str},CapCutDefault,,0,0,0,,{dialogue_text}"
                    events.append(event_line)

            current_time_offset += duration

        with open(ass_output_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(events) + "\n")

        print(f"[Assembler] Generated CapCut kinetic ASS subtitles: {ass_output_path}")
        return ass_output_path

    def _format_ass_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int(round((seconds - int(seconds)) * 100))
        if centisecs >= 100:
            centisecs = 99
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def _get_media_duration(self, file_path: str) -> float:
        try:
            out = subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", file_path
            ], stderr=subprocess.DEVNULL).decode().strip()
            return float(out)
        except Exception:
            return 0.0

    def prepare_scene_clip(self, scene: Dict[str, Any], project_dir: Path, target_w: int = 768, target_h: int = 1344) -> Path:
        """
        Prepares a standardized 768x1344 30fps clip for a scene:
        - If video exists, muxes narration audio with elastic retiming/final-frame hold (NEVER loops).
        - If video does NOT exist, creates a smooth Ken-Burns pan/zoom clip from image + audio.
        """
        num = scene["scene_number"]
        out_clip = project_dir / f"scene_{num:02d}_ready.mp4"
        audio_file = scene.get("audio_file")
        video_file = scene.get("video_file")
        image_file = scene.get("image_file")
        duration = float(scene.get("actual_audio_duration", scene.get("duration_seconds", 5.0)))

        # Case A: Video exists and is accessible
        if video_file and os.path.exists(video_file) and os.path.getsize(video_file) > 1000:
            clean_v = str(Path(video_file).resolve()).replace("\\", "/")
            v_dur = self._get_media_duration(clean_v)

            if audio_file and os.path.exists(audio_file):
                clean_a = str(Path(audio_file).resolve()).replace("\\", "/")

                # Temporal Flow Architecture: ZERO looping, seamless duration matching
                # 1. Video meets or exceeds audio duration -> clean cut at audio duration
                if v_dur >= duration or v_dur <= 0.0:
                    vf_filter = f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},fps=30"
                # 2. Minor shortfall (up to 25%) -> elastic cinematic slow-motion retiming
                elif (duration / v_dur) <= 1.25:
                    ratio = duration / v_dur
                    vf_filter = f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},setpts={ratio:.4f}*PTS,fps=30"
                # 3. Larger shortfall -> mild 1.15x stretch + dramatic hold on final resolved frame (NEVER snap back to frame 0)
                else:
                    retimed_dur = v_dur * 1.15
                    pad_dur = max(0.5, duration - retimed_dur + 0.5)
                    vf_filter = f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},setpts=1.15*PTS,tpad=stop_mode=clone:stop_duration={pad_dur:.2f},fps=30"

                cmd = [
                    "ffmpeg", "-y",
                    "-i", clean_v,
                    "-i", clean_a,
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-vf", vf_filter,
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-ac", "2",
                    "-t", str(duration),
                    str(out_clip).replace("\\", "/")
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", clean_v,
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},fps=30",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-ac", "2",
                    str(out_clip).replace("\\", "/")
                ]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return out_clip
            except Exception as e:
                print(f"[Assembler] Warning standardizing video clip for scene {num}: {e}. Falling back to Ken-Burns still...")

        # Case B: Graceful Fallback from Stills + Audio (Ken-Burns motion)
        if image_file and os.path.exists(image_file):
            clean_img = str(Path(image_file).resolve()).replace("\\", "/")
            # Clean static hold without childish zoompan
            vf_motion = f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},fps=30"

            if audio_file and os.path.exists(audio_file):
                clean_aud = str(Path(audio_file).resolve()).replace("\\", "/")
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", clean_img,
                    "-i", clean_aud,
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-t", str(duration),
                    "-pix_fmt", "yuv420p",
                    "-vf", vf_motion,
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-ac", "2",
                    "-shortest",
                    str(out_clip).replace("\\", "/")
                ]
            else:
                # Silent clip if audio missing
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", clean_img,
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-c:v", "libx264",
                    "-preset", "veryfast",
                    "-t", str(duration),
                    "-pix_fmt", "yuv420p",
                    "-vf", vf_motion,
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-ac", "2",
                    "-shortest",
                    str(out_clip).replace("\\", "/")
                ]

            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return out_clip
            except Exception:
                # Simpler scale if zoompan encounters complex image sizes
                cmd_simple = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", clean_img,
                    "-i", clean_aud if audio_file and os.path.exists(audio_file) else "anullsrc=r=44100:cl=stereo",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-t", str(duration),
                    "-pix_fmt", "yuv420p",
                    "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},fps=30",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-ar", "44100",
                    "-ac", "2",
                    "-shortest",
                    str(out_clip).replace("\\", "/")
                ]
                subprocess.run(cmd_simple, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return out_clip

        raise RuntimeError(f"Scene {num} does not have an image or video file to assemble!")

    def assemble_final_short(
        self,
        manifest_path: str,
        caption_y_percent: float = 72.0,
        caption_color: str = "yellow",
        font_family: str = "Impact",
        font_size: int = 52,
        outline_thickness: float = 4.5,
        all_caps: bool = True,
        chunk_size: int = 3,
        bgm_path: Optional[str] = None,
        archive_when_done: bool = False
    ) -> str:
        """
        Merges scene clips, adds dynamic CapCut word bounce subtitles,
        mixes optional background audio, and exports the final 9:16 MP4.
        """
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        project_dir = Path(manifest_path).parent
        project_name = manifest["project_name"]
        final_output_path = self.output_dir / f"{project_name}_final.mp4"
        ass_sub_path = project_dir / "subtitles.ass"

        # 1. Create CapCut Subtitles at custom Y position and styling
        self.generate_ass_subtitles(
            manifest, 
            str(ass_sub_path), 
            caption_y_percent=caption_y_percent,
            caption_color=caption_color,
            font_family=font_family,
            font_size=font_size,
            outline_thickness=outline_thickness,
            all_caps=all_caps,
            chunk_size=chunk_size
        )

        # 2. Prepare standardized scene clips (with Ken-Burns fallback if needed)
        ready_clips = []
        for scene in manifest.get("scenes", []):
            clip = self.prepare_scene_clip(scene, project_dir)
            ready_clips.append(clip)

        # 3. Prepare concat list
        concat_txt = project_dir / "concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for clip in ready_clips:
                clean_v = str(clip.resolve()).replace("\\", "/")
                f.write(f"file '{clean_v}'\n")

        # 4. Concatenate standardized video clips
        stitched_raw = project_dir / "stitched_raw.mp4"
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt).replace("\\", "/"),
            "-c", "copy",
            str(stitched_raw).replace("\\", "/")
        ]
        print("[Assembler] Concatenating scene clips...")
        try:
            subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            print("[Assembler] Stream copy failed, re-encoding concat...")
            cmd_concat_re = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_txt).replace("\\", "/"),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-c:a", "aac",
                str(stitched_raw).replace("\\", "/")
            ]
            subprocess.run(cmd_concat_re, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 5. Burn subtitles & mix audio (Narration + Local SFX timeline + optional BGM)
        escaped_ass = str(ass_sub_path).replace("\\", "/").replace(":", "\\:")
        
        # Build intelligent sound design timeline via TypeSafe JEV router
        sfx_timeline = sfx_manager.generate_sfx_timeline(manifest, use_ai=True)
        print(f"[Assembler] Layering {len(sfx_timeline)} peak-aligned SFX cues across video timeline...")

        # Save sound design timeline into project directory for transparency
        sfx_timeline_path = project_dir / "sfx_timeline.json"
        try:
            with open(sfx_timeline_path, "w", encoding="utf-8") as f:
                json.dump(sfx_timeline, f, indent=2)
        except Exception:
            pass

        cmd_inputs = ["-i", str(stitched_raw).replace("\\", "/")]
        filter_parts = []
        mix_inputs = ["[0:a]"]
        input_counter = 1

        # Add each SFX cue with its millisecond delay and appropriate volume
        for idx, ev in enumerate(sfx_timeline):
            sfx_file = ev.get("file")
            if sfx_file and os.path.exists(sfx_file):
                cmd_inputs.extend(["-i", str(Path(sfx_file).resolve()).replace("\\", "/")])
                delay_ms = int(round(ev.get("aligned_offset_seconds", 0.0) * 1000))
                vol = ev.get("volume", 0.28)
                filter_parts.append(f"[{input_counter}:a]aresample=44100,volume={vol},adelay={delay_ms}|{delay_ms}[sfx{idx}]")
                mix_inputs.append(f"[sfx{idx}]")
                input_counter += 1

        # Mix optional background music (BGM)
        if bgm_path and os.path.exists(bgm_path):
            clean_bgm = str(Path(bgm_path).resolve()).replace("\\", "/")
            print(f"[Assembler] Mixing BGM track: {clean_bgm}")
            cmd_inputs.extend(["-i", clean_bgm])
            filter_parts.append(f"[{input_counter}:a]aresample=44100,volume=0.15[bgm]")
            mix_inputs.append("[bgm]")
            input_counter += 1

        # Combine all audio tracks into [a_out] WITHOUT altering or scaling the narrator audio
        if len(mix_inputs) > 1:
            # normalize=0 and dropout_transition=0 ensures the narrator's generated voice is 100% untouched and unscaled
            mix_str = "".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=0:normalize=0[a_out]"
            filter_parts.append(mix_str)
            audio_map = "[a_out]"
        else:
            audio_map = "0:a"

        # Video filter with ASS subtitle burning
        filter_parts.append(f"[0:v]ass='{escaped_ass}'[v_out]")
        filter_complex_str = ";".join(filter_parts)

        cmd_burn = [
            "ffmpeg", "-y",
            *cmd_inputs,
            "-filter_complex", filter_complex_str,
            "-map", "[v_out]",
            "-map", audio_map,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            str(final_output_path).replace("\\", "/")
        ]

        print("[Assembler] Burning animated CapCut captions and rendering final Short with full SFX design...")
        try:
            subprocess.run(cmd_burn, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            print(f"[Assembler] Filter complex burn failed: {e}. Trying simple subtitles fallback...")
            cmd_burn_fb = [
                "ffmpeg", "-y",
                "-i", str(stitched_raw).replace("\\", "/"),
                "-vf", f"subtitles='{escaped_ass}'",
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "aac",
                "-b:a", "192k",
                str(final_output_path).replace("\\", "/")
            ]
            subprocess.run(cmd_burn_fb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        print(f"\n=======================================================")
        print(f"[Assembler] FINAL SHORT CREATED SUCCESSFULLY!")
        print(f"File location: {final_output_path}")
        print(f"=======================================================\n")

        # 6. Archive to used folder if requested
        if archive_when_done:
            self._archive_project(project_dir)

        return str(final_output_path)

    def _archive_project(self, project_dir: Path):
        """
        Copies completed source assets to the 'used' folder to maintain clean workspace.
        """
        import shutil
        print(f"[Assembler] Archiving source assets to {self.used_dir}...")
        for item in project_dir.iterdir():
            if item.suffix in [".mp4", ".png", ".mp3"] and not item.name.startswith("stitched"):
                dest = self.used_dir / f"{project_dir.name}_{item.name}"
                shutil.copy2(item, dest)
        print(f"[Assembler] Project assets archived into {self.used_dir}")

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    assembler = VideoAssembler()

    # Find the most recent project manifest to test assembly
    projects = list(Config.PROJECTS_DIR.glob("*/manifest.json"))
    if projects:
        latest_manifest = sorted(projects, key=os.path.getmtime)[-1]
        print(f"Testing assembly on: {latest_manifest}")
        result = assembler.assemble_final_short(str(latest_manifest), archive_when_done=False)
        print("Assembled output path:", result)
    else:
        print("No project manifest found. Run pipeline_orchestrator first.")
