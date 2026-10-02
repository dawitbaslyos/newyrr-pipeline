import os
import sys
import shutil
import json
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r"c:\Users\dawit\Videos\Youtube Channels\internetchill\pipeline")
from config import Config
from audio_generator import AudioGenerator
from video_assembler import VideoAssembler

PROJECT_DIR = Config.PROJECTS_DIR / "glass_the_liquid_mystery_20260925_193721"
MANIFEST_PATH = PROJECT_DIR / "manifest.json"

IMAGE_PATHS = [
    r"C:\Users\dawit\.gemini\antigravity\brain\468e43fb-175f-4c0d-8357-b181ee708704\glass_liquid_scene1_1790373395489.jpg",
    r"C:\Users\dawit\.gemini\antigravity\brain\468e43fb-175f-4c0d-8357-b181ee708704\glass_liquid_scene2_1790373707635.jpg",
    r"C:\Users\dawit\.gemini\antigravity\brain\468e43fb-175f-4c0d-8357-b181ee708704\glass_liquid_scene3_1790373999761.jpg",
    r"C:\Users\dawit\.gemini\antigravity\brain\468e43fb-175f-4c0d-8357-b181ee708704\glass_liquid_scene4_1790413835283.jpg",
    r"C:\Users\dawit\.gemini\antigravity\brain\468e43fb-175f-4c0d-8357-b181ee708704\glass_liquid_scene5_1790434694183.jpg",
]

def build_full_production():
    print("==================================================")
    print("🎬 RENDERING FULL PRODUCTION SHORT (REAL VOICE + IMAGES + MOTION)")
    print("==================================================\n")

    audio_gen = AudioGenerator()
    assembler = VideoAssembler()

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Update Images and Voiceover for each scene
    for i, scene in enumerate(manifest["scenes"]):
        num = scene["scene_number"]
        narration = scene["narration"]
        
        # Copy high-res AI image
        img_dest = PROJECT_DIR / f"scene_{num:02d}_flux.png"
        src_img = IMAGE_PATHS[i]
        shutil.copy2(src_img, img_dest)
        scene["image_file"] = str(img_dest)
        print(f"[Scene {num}] Copied photorealistic AI keyframe: {img_dest.name}")

        # Generate Real Neural Voiceover (edge-tts)
        audio_dest = PROJECT_DIR / f"scene_{num:02d}_audio.mp3"
        audio_gen.generate_speech(narration, str(audio_dest))
        actual_dur = audio_gen.get_audio_duration(str(audio_dest))
        scene["audio_file"] = str(audio_dest)
        scene["actual_audio_duration"] = actual_dur
        print(f"[Scene {num}] Generated neural voiceover ({actual_dur:.2f}s): \"{narration}\"")

        # Render Scene Video Clip with smooth cinematic slow zoom
        video_dest = PROJECT_DIR / f"scene_{num:02d}_minimax.mp4"
        clean_img = str(img_dest).replace("\\", "/")
        clean_aud = str(audio_dest).replace("\\", "/")
        clean_vid = str(video_dest).replace("\\", "/")
        
        # Ken Burns push-in zoom filter
        total_frames = int(max(1, actual_dur) * 30)
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0006,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=768x1344:fps=30"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", clean_img,
            "-i", clean_aud,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-t", str(actual_dur),
            "-pix_fmt", "yuv420p",
            "-vf", vf,
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            clean_vid
        ]
        import subprocess
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        scene["video_file"] = str(video_dest)
        scene["status"] = "VIDEO_READY"
        print(f"[Scene {num}] Rendered cinematic motion video clip: {video_dest.name}\n")

    manifest["status"] = "VIDEOS_READY"
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # 2. Assemble Final Video with Subtitles at 72%
    print("[Assembler] Stitching all 5 scenes & burning kinetic bouncing ASS subtitles at 72%...")
    final_video = assembler.assemble_final_short(str(MANIFEST_PATH), caption_y_percent=72.0)
    print(f"Final Video Exported: {final_video}\n")

    # 3. Generate CapCut-Style Thumbnail using the real Scene 1 image
    print("[Thumbnail] Generating CapCut-Style High-CTR Thumbnail from Scene 1...")
    thumb_path = PROJECT_DIR / "thumbnail.png"
    img = Image.open(IMAGE_PATHS[0]).convert("RGB").resize((768, 1344))
    draw = ImageDraw.Draw(img)
    w, h = img.size
    box_y = int(h * 0.65)
    draw.rectangle([(0, box_y), (w, box_y + 180)], fill=(0, 0, 0, 210))
    draw.rectangle([(0, box_y), (w, box_y + 180)], outline=(6, 182, 212), width=6)
    draw.text((w // 2, box_y + 90), "IS GLASS ACTUALLY LIQUID?", fill=(255, 255, 0), anchor="mm")
    img.save(thumb_path)
    print(f"Thumbnail saved: {thumb_path}\n")

    print("==================================================")
    print("🎉 FULL PRODUCTION SUCCESS!")
    print(f"Final Video: {final_video}")
    print(f"File Size: {os.path.getsize(final_video):,} bytes")
    print(f"Thumbnail: {thumb_path}")
    print("==================================================")

if __name__ == "__main__":
    build_full_production()
