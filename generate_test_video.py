import os
import sys
import json
import time

sys.stdout.reconfigure(encoding='utf-8')

from typing import Optional
from config import Config
from pipeline_orchestrator import VideoPipelineOrchestrator
from video_assembler import VideoAssembler

def run_test_production(project_name: Optional[str] = None):
    orchestrator = VideoPipelineOrchestrator()
    assembler = VideoAssembler()

    if project_name and (Config.PROJECTS_DIR / project_name).exists():
        print(f"==================================================")
        print(f"🎬 RESUMING END-TO-END PRODUCTION")
        print(f"Project: '{project_name}'")
        print(f"==================================================\n")
    else:
        topic = "Why glass is secretly a moving liquid"
        print(f"==================================================")
        print(f"🎬 STARTING FULL END-TO-END PRODUCTION TEST")
        print(f"Topic: '{topic}'")
        print(f"==================================================\n")

        # 1. Draft & Script
        print("[Step 1/4] Writing Viral Screenplay via OpenRouter...")
        draft = orchestrator.create_draft(topic, aspect_ratio="9:16")
        project_name = draft["project_name"]
        print(f"Project created: {project_name}")
        print(f"Title: {draft['title']}")
        print(f"Hook: \"{draft['hook']}\"")
        print(f"Scenes count: {len(draft['scenes'])}\n")

        # 2. Frames First
        print("[Step 2/4] Generating Keyframes First (Nano Banana 2)...")
        manifest = orchestrator.generate_frames_for_project(project_name)
        print(f"Keyframes generated for all {len(manifest['scenes'])} scenes!\n")

    # 3. Animate Videos (MiniMax H3)
    print("[Step 3/4] Animating Scenes with MiniMax H3 Max Turbo...")
    video_manifest = orchestrator.render_videos_for_project(project_name)
    print(f"Video animation pass completed!\n")

    # 4. Assemble Final Video & Subtitles
    print("[Step 4/4] Assembling Final Short with Burned Bouncing Subtitles at 72%...")
    manifest_path = Config.PROJECTS_DIR / project_name / "manifest.json"
    final_video = assembler.assemble_final_short(str(manifest_path), caption_y_percent=72.0)
    print(f"Final Video Exported: {final_video}\n")

    # 5. Generate Thumbnail
    print("[Bonus] Generating CapCut-Style Thumbnail...")
    thumb = orchestrator.generate_thumbnail(project_name, headline="IS GLASS ACTUALLY LIQUID?")
    print(f"Thumbnail saved: {thumb}\n")

    print(f"==================================================")
    print(f"🎉 PRODUCTION RUN COMPLETED SUCCESSFULLY!")
    print(f"Final Video Path: {final_video}")
    print(f"File Size: {os.path.getsize(final_video):,} bytes")
    print(f"Thumbnail Path: {thumb}")
    print(f"==================================================")

if __name__ == "__main__":
    p_name = sys.argv[1] if len(sys.argv) > 1 else "glass_the_liquid_mystery_20260925_193721"
    run_test_production(p_name)
