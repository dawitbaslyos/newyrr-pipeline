import os
import json
import time
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import Config
from youtube_analytics import YouTubeAnalyticsManager
from channel_manager import ChannelManager
from pipeline_orchestrator import VideoPipelineOrchestrator
from video_assembler import VideoAssembler
from sfx_manager import sfx_manager

app = FastAPI(title="Newyrr Media Studio", version="2.0.0")

# Mount static media directories
app.mount("/static_output", StaticFiles(directory=str(Config.OUTPUT_DIR)), name="output")
app.mount("/static_projects", StaticFiles(directory=str(Config.PROJECTS_DIR)), name="projects")

SFX_BANK_DIR = Config.BASE_DIR / "data" / "sfx_bank"
SFX_BANK_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static_sfx", StaticFiles(directory=str(SFX_BANK_DIR)), name="sfx_bank")

RENDERS_DIR = Config.BASE_DIR / "data" / "renders"
RENDERS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static_renders", StaticFiles(directory=str(RENDERS_DIR)), name="renders")

FRONTEND_DIST = Path(__file__).resolve().parent / "frontend" / "dist"
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend_assets")

analytics_mgr = YouTubeAnalyticsManager()
channel_mgr = ChannelManager()
orchestrator = VideoPipelineOrchestrator()
assembler = VideoAssembler()

class DraftRequest(BaseModel):
    topic: str
    aspect_ratio: str = "9:16"
    art_style: Optional[str] = None
    tts_voice: Optional[str] = None
    reference_url: Optional[str] = None
    project_type: Optional[str] = "create"

class ProjectActionRequest(BaseModel):
    project_name: str

class RerollFrameRequest(BaseModel):
    project_name: str
    scene_number: int
    custom_prompt: Optional[str] = None

class RerollVideoRequest(BaseModel):
    project_name: str
    scene_number: int
    custom_motion_prompt: Optional[str] = None

class SaveSceneRequest(BaseModel):
    project_name: str
    scene_number: int
    narration: Optional[str] = None
    flux_prompt: Optional[str] = None
    motion_prompt: Optional[str] = None

class SceneActionRequest(BaseModel):
    project_name: str
    scene_number: int
    custom_prompt: Optional[str] = None

class AssembleRequest(BaseModel):
    project_name: str
    caption_y_percent: float = 72.0
    caption_color: str = "yellow"
    font_family: str = "Impact"
    font_size: int = 52
    outline_thickness: float = 4.5
    all_caps: bool = True
    chunk_size: int = 3
    bgm_path: Optional[str] = None
    archive: bool = False

class ThumbnailRequest(BaseModel):
    project_name: str
    headline: Optional[str] = None

class UpdateProjectMetadataRequest(BaseModel):
    project_name: str
    art_style: Optional[str] = None
    title: Optional[str] = None
    caption_y_percent: Optional[float] = None

class AddChannelRequest(BaseModel):
    handle: str
    name: str
    focus: str = "Science Trivia"

class SelectActiveChannelRequest(BaseModel):
    handle: str

class AddUserChannelRequest(BaseModel):
    handle: str
    name: Optional[str] = None
    niche: Optional[str] = "Shorts"
    subscribers: Optional[str] = None
    videos: Optional[int] = None

class RemoveTrackedRequest(BaseModel):
    handle: str

class SettingsRequest(BaseModel):
    llm_model: str
    image_model: str
    video_provider: str
    tts_model: str
    tts_voice: str
    art_style: str

@app.get("/api/settings")
def get_settings():
    settings_file = Config.BASE_DIR / "user_settings.json"
    data = {
        "llm_model": getattr(Config, "OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        "image_model": getattr(Config, "ACTIVE_IMAGE_MODEL", "krea/krea-2-medium-turbo"),
        "video_provider": getattr(Config, "ACTIVE_VIDEO_PROVIDER", "bytedance/seedance-2.0-mini"),
        "tts_model": getattr(Config, "ACTIVE_TTS_MODEL", "google/gemini-3.8-flash-lite-tts"),
        "tts_voice": getattr(Config, "ACTIVE_TTS_VOICE", "Charon"),
        "art_style": getattr(Config, "ACTIVE_ART_STYLE", "cinematic_film")
    }
    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data.update(json.load(f))
        except Exception:
            pass
    return data

@app.post("/api/settings")
def save_settings(req: SettingsRequest):
    settings_file = Config.BASE_DIR / "user_settings.json"
    data = req.dict()
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    Config.OPENROUTER_MODEL = data["llm_model"]
    Config.ACTIVE_IMAGE_MODEL = data["image_model"]
    Config.OPENROUTER_IMAGE_MODEL = data["image_model"]
    Config.ACTIVE_VIDEO_PROVIDER = data["video_provider"]
    Config.ACTIVE_TTS_MODEL = data["tts_model"]
    Config.ACTIVE_TTS_VOICE = data["tts_voice"]
    Config.ACTIVE_ART_STYLE = data["art_style"]
    
    return {"status": "success", "settings": data}

@app.get("/api/styles")
def get_styles():
    styles_file = Config.BASE_DIR / "clio_styles.json"
    if styles_file.exists():
        try:
            with open(styles_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

@app.get("/api/status")
def get_status():
    return {
        "openrouter_ready": bool(Config.OPENROUTER_API_KEY),
        "image_provider": Config.IMAGE_PROVIDER,
        "image_model": getattr(Config, "ACTIVE_IMAGE_MODEL", "krea/krea-2-medium-turbo"),
        "voice_provider": Config.VOICE_PROVIDER,
        "tts_voice": getattr(Config, "ACTIVE_TTS_VOICE", "Charon"),
        "openai_tts_ready": bool(Config.OPENAI_API_KEY),
        "replicate_ready": bool(Config.REPLICATE_API_TOKEN),
        "runpod_minimax_ready": bool(Config.RUNPOD_MINIMAX_ENDPOINT_ID and Config.RUNPOD_API_KEY),
        "youtube_api_ready": bool(Config.YOUTUBE_API_KEY),
        "channel_id": Config.YOUTUBE_CHANNEL_ID
    }

@app.get("/api/topics")
@app.get("/api/topics/suggest")
def get_topic_suggestions(refresh: bool = False):
    if refresh:
        return channel_mgr.suggest_topics(refresh=True)
    return channel_mgr.get_latest_topics()

@app.get("/api/topics/history")
def get_topic_history():
    return channel_mgr.get_topic_history()

@app.get("/api/analytics")
def get_analytics(handle: Optional[str] = None, refresh: bool = False):
    return channel_mgr.get_analytics_for_channel(handle, force_refresh=refresh)

@app.post("/api/channels/sync")
def sync_channels(force: bool = True):
    return channel_mgr.sync_active_channel(force=force)

@app.get("/api/channels")
def get_channels():
    return channel_mgr.get_data()

@app.post("/api/channels/add")
def add_channel(req: AddChannelRequest):
    return channel_mgr.add_tracked_channel(req.handle, req.name, req.focus)

@app.post("/api/channels/remove-tracked")
def remove_tracked(req: RemoveTrackedRequest):
    return channel_mgr.remove_tracked_channel(req.handle)

@app.post("/api/channels/select-active")
def select_active_channel(req: SelectActiveChannelRequest):
    return channel_mgr.set_active_channel(req.handle)

@app.post("/api/channels/remove-user")
def remove_user(req: RemoveTrackedRequest):
    return channel_mgr.remove_user_channel(req.handle)

@app.post("/api/channels/sync-user")
def sync_user(req: RemoveTrackedRequest):
    return channel_mgr.sync_user_channel(req.handle)

@app.post("/api/channels/user-add")
def add_user_channel(req: AddUserChannelRequest):
    return channel_mgr.add_user_channel(req.handle, req.name, req.niche, req.subscribers, req.videos)

@app.get("/api/projects")
def list_projects():
    projects = []
    for p_dir in Config.PROJECTS_DIR.iterdir():
        if p_dir.is_dir():
            manifest_file = p_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if data.get("deleted_at"):
                        continue

                    final_vid = Config.OUTPUT_DIR / f"{data['project_name']}_final.mp4"
                    data["final_video_url"] = f"/static_output/{final_vid.name}" if final_vid.exists() else None
                        
                    # Add web accessible paths for scene assets with cache busting
                    for s in data.get("scenes", []):
                        if s.get("image_file"):
                            mtime = int(os.path.getmtime(s["image_file"])) if os.path.exists(s["image_file"]) else int(time.time())
                            s["image_url"] = f"/static_projects/{data['project_name']}/{Path(s['image_file']).name}?t={mtime}"
                        if s.get("video_file"):
                            mtime = int(os.path.getmtime(s["video_file"])) if os.path.exists(s["video_file"]) else int(time.time())
                            s["video_url"] = f"/static_projects/{data['project_name']}/{Path(s['video_file']).name}?t={mtime}"
                        if s.get("audio_file"):
                            mtime = int(os.path.getmtime(s["audio_file"])) if os.path.exists(s["audio_file"]) else int(time.time())
                            s["audio_url"] = f"/static_projects/{data['project_name']}/{Path(s['audio_file']).name}?t={mtime}"
                    if data.get("thumbnail_file"):
                        mtime = int(os.path.getmtime(data["thumbnail_file"])) if os.path.exists(data["thumbnail_file"]) else int(time.time())
                        data["thumbnail_url"] = f"/static_projects/{data['project_name']}/{Path(data['thumbnail_file']).name}?t={mtime}"

                    projects.append(data)
                except Exception:
                    pass
    projects.sort(key=lambda x: x.get("project_name", ""), reverse=True)
    return projects

@app.get("/api/projects/trash")
def list_trash_projects():
    trash = []
    now = time.time()
    for p_dir in Config.PROJECTS_DIR.iterdir():
        if p_dir.is_dir():
            manifest_file = p_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    deleted_at = data.get("deleted_at")
                    if deleted_at:
                        elapsed = now - deleted_at
                        if elapsed > 7 * 86400:
                            shutil.rmtree(p_dir, ignore_errors=True)
                            continue
                        days_left = max(1, 7 - int(elapsed / 86400))
                        data["days_left"] = days_left
                        
                        for s in data.get("scenes", []):
                            if s.get("image_file"):
                                s["image_url"] = f"/static_projects/{data['project_name']}/{Path(s['image_file']).name}"
                        if data.get("thumbnail_file"):
                            data["thumbnail_url"] = f"/static_projects/{data['project_name']}/{Path(data['thumbnail_file']).name}"
                        trash.append(data)
                except Exception:
                    pass
    trash.sort(key=lambda x: x.get("deleted_at", 0), reverse=True)
    return trash

@app.post("/api/projects/delete")
def move_project_to_trash(req: ProjectActionRequest):
    manifest_file = Config.PROJECTS_DIR / req.project_name / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["deleted_at"] = time.time()
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {"status": "success", "message": "Project moved to trash"}

@app.post("/api/projects/restore")
def restore_project_from_trash(req: ProjectActionRequest):
    manifest_file = Config.PROJECTS_DIR / req.project_name / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop("deleted_at", None)
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return {"status": "success", "message": "Project restored"}

@app.post("/api/projects/purge")
def permanently_delete_project(req: ProjectActionRequest):
    p_dir = Config.PROJECTS_DIR / req.project_name
    if p_dir.exists():
        shutil.rmtree(p_dir, ignore_errors=True)
    final_vid = Config.OUTPUT_DIR / f"{req.project_name}_final.mp4"
    if final_vid.exists():
        try:
            final_vid.unlink()
        except Exception:
            pass
    return {"status": "success", "message": "Project deleted permanently"}

@app.post("/api/projects/empty-trash")
def empty_all_trash():
    count = 0
    for p_dir in Config.PROJECTS_DIR.iterdir():
        if p_dir.is_dir():
            manifest_file = p_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("deleted_at"):
                        shutil.rmtree(p_dir, ignore_errors=True)
                        final_vid = Config.OUTPUT_DIR / f"{data.get('project_name', '')}_final.mp4"
                        if final_vid.exists():
                            try:
                                final_vid.unlink()
                            except Exception:
                                pass
                        count += 1
                except Exception:
                    pass
    return {"status": "success", "purged_count": count}

@app.get("/api/project/load")
def load_project(project_name: str):
    return get_project(project_name)

@app.get("/api/project/{project_name}")
def get_project(project_name: str):
    try:
        data = orchestrator.get_manifest(project_name)
        final_vid = Config.OUTPUT_DIR / f"{project_name}_final.mp4"
        data["final_video_url"] = f"/static_output/{final_vid.name}" if final_vid.exists() else None
        for s in data.get("scenes", []):
            if s.get("image_file"):
                mtime = int(os.path.getmtime(s["image_file"])) if os.path.exists(s["image_file"]) else int(time.time())
                s["image_url"] = f"/static_projects/{project_name}/{Path(s['image_file']).name}?t={mtime}"
            if s.get("video_file"):
                mtime = int(os.path.getmtime(s["video_file"])) if os.path.exists(s["video_file"]) else int(time.time())
                s["video_url"] = f"/static_projects/{project_name}/{Path(s['video_file']).name}?t={mtime}"
            if s.get("audio_file"):
                mtime = int(os.path.getmtime(s["audio_file"])) if os.path.exists(s["audio_file"]) else int(time.time())
                s["audio_url"] = f"/static_projects/{project_name}/{Path(s['audio_file']).name}?t={mtime}"
        if data.get("thumbnail_file"):
            mtime = int(os.path.getmtime(data["thumbnail_file"])) if os.path.exists(data["thumbnail_file"]) else int(time.time())
            data["thumbnail_url"] = f"/static_projects/{project_name}/{Path(data['thumbnail_file']).name}?t={mtime}"
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# Stage 1: Create Draft (Script Only)
@app.post("/api/project/create-draft")
def create_draft(req: DraftRequest):
    try:
        manifest = orchestrator.create_draft(
            topic=req.topic,
            aspect_ratio=req.aspect_ratio,
            art_style=req.art_style,
            tts_voice=req.tts_voice,
            reference_url=req.reference_url,
            project_type=req.project_type or "create"
        )
        return get_project(manifest["project_name"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stage 2: Generate Frames First (Flux Krea stills + Audio) - Batch
@app.post("/api/project/generate-frames")
def generate_frames(req: ProjectActionRequest):
    try:
        manifest = orchestrator.generate_frames_for_project(req.project_name)
        return get_project(req.project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Progressive: Generate single scene frame & audio
@app.post("/api/project/generate-scene-frame")
def generate_scene_frame(req: SceneActionRequest):
    try:
        manifest = orchestrator.generate_single_scene_frame(req.project_name, req.scene_number)
        return get_project(req.project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Progressive: Render single scene video
@app.post("/api/project/render-scene-video")
def render_scene_video(req: SceneActionRequest):
    try:
        manifest = orchestrator.generate_single_scene_video(req.project_name, req.scene_number, req.custom_prompt)
        return get_project(req.project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Re-roll a single frame
@app.post("/api/project/reroll-frame")
def reroll_frame(req: RerollFrameRequest):
    try:
        manifest = orchestrator.regenerate_single_frame(req.project_name, req.scene_number, req.custom_prompt)
        return get_project(req.project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Re-roll a single scene's video
@app.post("/api/project/reroll-video")
def reroll_video(req: RerollVideoRequest):
    try:
        manifest = orchestrator.regenerate_single_video(req.project_name, req.scene_number, req.custom_motion_prompt)
        return get_project(req.project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Save scene texts and prompts
@app.post("/api/project/save-scene")
def save_scene(req: SaveSceneRequest):
    try:
        manifest = orchestrator.save_scene_text(
            req.project_name,
            req.scene_number,
            narration=req.narration,
            flux_prompt=req.flux_prompt,
            motion_prompt=req.motion_prompt
        )
        return get_project(req.project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update project-level metadata (e.g. art direction style, title, subtitle position)
@app.post("/api/project/update-metadata")
def update_project_metadata(req: UpdateProjectMetadataRequest):
    try:
        manifest = orchestrator.update_project_metadata(
            req.project_name,
            art_style=req.art_style,
            title=req.title,
            caption_y_percent=req.caption_y_percent
        )
        return get_project(req.project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stage 3: Render Videos (Seedance 2.0 / MiniMax H3)
@app.post("/api/project/render-videos")
def render_videos(req: ProjectActionRequest):
    try:
        manifest = orchestrator.render_videos_for_project(req.project_name)
        return get_project(req.project_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/project/upload-scene-video")
async def upload_scene_video(
    project_name: str = Form(...),
    scene_number: int = Form(...),
    file: UploadFile = File(...)
):
    """
    Manual Video Drop-In (RunPod / Local MP4):
    Uploads a creator-generated video for a specific scene, saves it directly to
    projects/{project_name}/scene_{num:02d}_video.mp4, updates manifest, and extracts a keyframe still.
    """
    project_dir = Config.PROJECTS_DIR / project_name
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    target_video = project_dir / f"scene_{scene_number:02d}_video.mp4"
    with open(target_video, "wb") as f:
        content = await file.read()
        f.write(content)

    manifest_file = project_dir / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=404, detail="Project manifest not found")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Extract keyframe still if missing
    still_target = project_dir / f"scene_{scene_number:02d}_flux.png"
    if not still_target.exists():
        cmd = [
            "ffmpeg", "-y",
            "-ss", "0.5",
            "-i", str(target_video),
            "-vframes", "1",
            "-q:v", "2",
            str(still_target)
        ]
        import subprocess
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for scene in manifest.get("scenes", []):
        if scene["scene_number"] == scene_number:
            scene["video_file"] = str(target_video)
            scene["status"] = "VIDEO_READY"
            if still_target.exists():
                scene["image_file"] = str(still_target)

    # Check if all scenes are ready
    if all(s.get("video_file") and Path(s["video_file"]).exists() for s in manifest.get("scenes", [])):
        manifest["status"] = "VIDEOS_READY"

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return get_project(project_name)

@app.get("/api/project/{project_name}/runpod-package")
def get_runpod_package(project_name: str):
    """
    Returns structured data for batch execution on RunPod instances.
    """
    manifest_path = Config.PROJECTS_DIR / project_name / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    pkg = {
        "project_name": project_name,
        "title": manifest.get("title", ""),
        "scenes": []
    }
    for s in manifest.get("scenes", []):
        num = s["scene_number"]
        img_name = Path(s["image_file"]).name if s.get("image_file") else f"scene_{num:02d}_flux.png"
        target_dur = float(s.get("actual_audio_duration", s.get("duration_seconds", 5.0)))
        pkg["scenes"].append({
            "scene_number": num,
            "filename": f"scene_{num:02d}_video.mp4",
            "image_filename": img_name,
            "image_url": f"/static_projects/{project_name}/{img_name}",
            "motion_prompt": s.get("minimax_motion_prompt", ""),
            "duration": round(target_dur, 2),
            "frames_25fps": int(round(target_dur * 25)),
            "frames_24fps": int(round(target_dur * 24)),
            "shot_perspective": s.get("shot_perspective", s.get("shot_type", "Dynamic Angle")),
            "physical_blocking": s.get("physical_blocking", s.get("focal_point", "")),
            "kinetic_vector": s.get("kinetic_vector", "Continuous motion momentum"),
            "narration": s.get("narration", "")
        })
    return pkg

@app.get("/api/project/{project_name}/runpod-package/zip")
def download_runpod_package_zip(project_name: str):
    """
    Generates a downloadable ZIP file containing all keyframe still images
    and a motion_prompts.txt file for easy batch execution on RunPod.
    Includes exact audio duration and frame count calculations for LTX / Wan / Seedance.
    """
    project_dir = Config.PROJECTS_DIR / project_name
    manifest_path = project_dir / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    zip_path = project_dir / f"{project_name}_runpod_batch.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        txt_lines = [
            f"RUNPOD BATCH PACKAGE FOR: {manifest.get('title', project_name)}\n"
            + "="*60 + "\n"
            + "DIRECTOR DIRECTIVE: Pure Visual Pantomime (Zero Lip-Sync / Dialogue).\n"
            + "Characters perform physical actions, handle props, or react viscerally.\n"
            + "="*60 + "\n"
        ]
        for s in manifest.get("scenes", []):
            num = s["scene_number"]
            prompt = s.get("minimax_motion_prompt", "")
            img_file = s.get("image_file")
            target_dur = float(s.get("actual_audio_duration", s.get("duration_seconds", 5.0)))
            f25 = int(round(target_dur * 25))
            f24 = int(round(target_dur * 24))

            txt_lines.append(f"--- SCENE {num:02d} ---")
            txt_lines.append(f"Video Output: scene_{num:02d}_video.mp4")
            txt_lines.append(f"Target Duration: {target_dur:.2f}s")
            txt_lines.append(f"Recommended Frames: {f25} frames @ 25fps (LTX-Video) | {f24} frames @ 24fps (Wan2.1 / Kling)")
            txt_lines.append(f"Perspective: {s.get('shot_perspective', s.get('shot_type', 'Dynamic Angle'))}")
            if s.get("physical_blocking"):
                txt_lines.append(f"Physical Blocking: {s.get('physical_blocking')}")
            if s.get("kinetic_vector"):
                txt_lines.append(f"Kinetic Vector: {s.get('kinetic_vector')}")
            txt_lines.append(f"Narration Voiceover: {s.get('narration', '')}")
            txt_lines.append(f"Motion Prompt: {prompt}\n")

            if img_file and Path(img_file).exists():
                z.write(img_file, arcname=Path(img_file).name)
        z.writestr("motion_prompts.txt", "\n".join(txt_lines))

    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=f"{project_name}_runpod_batch.zip"
    )

# Stage 4: Assemble Final Video with Custom Caption Placement Y% and BGM
@app.post("/api/project/assemble")
def assemble_video(req: AssembleRequest):
    try:
        manifest_path = Config.PROJECTS_DIR / req.project_name / "manifest.json"
        final_video_path = assembler.assemble_final_short(
            str(manifest_path),
            caption_y_percent=req.caption_y_percent,
            caption_color=req.caption_color,
            font_family=req.font_family,
            font_size=req.font_size,
            outline_thickness=req.outline_thickness,
            all_caps=req.all_caps,
            chunk_size=req.chunk_size,
            bgm_path=req.bgm_path,
            archive_when_done=req.archive
        )
        return {
            "status": "success",
            "final_video_url": f"/static_output/{Path(final_video_path).name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Generate CapCut Style Thumbnail
@app.post("/api/project/generate-thumbnail")
def generate_thumbnail(req: ThumbnailRequest):
    try:
        thumb_path = orchestrator.generate_thumbnail(req.project_name, req.headline)
        return {
            "status": "success",
            "thumbnail_url": f"/static_projects/{req.project_name}/{Path(thumb_path).name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- Curated SFX & JEV Sound Design APIs -----------------
@app.get("/api/sfx/catalog")
def get_sfx_catalog():
    """Returns the 18 curated, normalized sound effects with transient peak metadata."""
    return sfx_manager.catalog

@app.get("/api/project/{project_name}/sfx-timeline")
def get_project_sfx_timeline(project_name: str):
    """Returns the peak-aligned SFX design timeline for the project."""
    timeline_path = Config.PROJECTS_DIR / project_name / "sfx_timeline.json"
    if timeline_path.exists():
        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    manifest_path = Config.PROJECTS_DIR / project_name / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    return sfx_manager.generate_sfx_timeline(manifest, use_ai=True)

@app.post("/api/project/generate-sfx")
def generate_project_sfx(req: ProjectActionRequest):
    """Runs TypeSafe JEV Router on OpenRouter to generate or re-generate sound design."""
    manifest_path = Config.PROJECTS_DIR / req.project_name / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    timeline = sfx_manager.generate_sfx_timeline(manifest, use_ai=True)
    timeline_path = Config.PROJECTS_DIR / req.project_name / "sfx_timeline.json"
    try:
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(timeline, f, indent=2)
    except Exception:
        pass
    return {
        "status": "success",
        "timeline": timeline
    }

# ----------------- Viral Repurpose Engine APIs -----------------
class RepurposeDeconstructRequest(BaseModel):
    url: str
    target_seconds: int = 45
    account_id: str = "main-channel"

class RepurposeRenderRequest(BaseModel):
    video_id: str
    narration_text: str
    voice_key: str = "christopher"
    format_mode: str = "shorts_9_16"
    watermark_defense: str = "punch_in"
    burn_subtitles: bool = True
    account_id: str = "main-channel"

@app.post("/api/repurpose/deconstruct")
def api_repurpose_deconstruct(req: RepurposeDeconstructRequest):
    try:
        from repurpose.repurpose_engine import deconstruct_source_video
        result = deconstruct_source_video(req.url, req.target_seconds, req.account_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/repurpose/render")
def api_repurpose_render(req: RepurposeRenderRequest):
    try:
        from repurpose.repurpose_engine import render_repurposed_video
        result = render_repurposed_video(
            video_id=req.video_id,
            account_id=req.account_id,
            narration_text=req.narration_text,
            voice_key=req.voice_key,
            format_mode=req.format_mode,
            watermark_defense=req.watermark_defense,
            burn_subtitles=req.burn_subtitles
        )
        if "video_url" in result and result["video_url"].startswith("/renders/"):
            result["video_url"] = result["video_url"].replace("/renders/", "/static_renders/")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- Reference Ingestion & Blueprint APIs -----------------
class ReferenceIngestRequest(BaseModel):
    url: str

@app.post("/api/reference/ingest")
def api_reference_ingest(req: ReferenceIngestRequest):
    try:
        from transcript_service import transcript_service
        result = transcript_service.ingest_reference(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

FEED_CACHE_FILE = Config.BASE_DIR / "data" / "shorts_feed_cache.json"

@app.get("/api/channels/shorts-feed")
@app.get("/api/repurpose/competitor-feed")
def api_channels_shorts_feed(
    handle: Optional[str] = None,
    refresh: bool = False,
    format_type: Optional[str] = None,
    sort_by: Optional[str] = "latest"
):
    try:
        data = channel_mgr.get_data()
        tracked = data.get("tracked_channels", [])
        avatar_map = {ch.get("handle", "").lower().strip(): ch.get("avatar_url", "") for ch in tracked}

        all_videos = []
        if not refresh and FEED_CACHE_FILE.exists():
            try:
                with open(FEED_CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    all_videos = cache_data.get("videos", [])
            except Exception:
                all_videos = []

        if refresh or not all_videos:
            from repurpose.tracker import fetch_videos_for_handle_or_id
            all_videos = []
            for ch in tracked:
                h = ch.get("handle")
                if h:
                    vids = fetch_videos_for_handle_or_id(h)
                    for v in vids[:10]:
                        v["channel_name"] = ch.get("name", h)
                        v["channel_handle"] = h
                        v["avatar_url"] = ch.get("avatar_url") or avatar_map.get(h.lower().strip(), "")
                        all_videos.append(v)
            FEED_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(FEED_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "videos": all_videos}, f, indent=2)

        # Ensure avatars are always populated from channel registry
        for v in all_videos:
            h = v.get("channel_handle", "").lower().strip()
            if not v.get("avatar_url") and h in avatar_map:
                v["avatar_url"] = avatar_map[h]

        # 1. Filter by Channel Handle
        res = all_videos
        if handle and handle.strip():
            norm = handle.lower().strip()
            res = [v for v in res if v.get("channel_handle", "").lower().strip() == norm]

        # 2. Filter by Format (Shorts vs Videos vs All)
        if format_type == "shorts":
            res = [v for v in res if v.get("is_short", True)]
        elif format_type == "videos":
            res = [v for v in res if not v.get("is_short", False)]

        # 3. Sort Order
        if sort_by == "popular":
            res = sorted(res, key=lambda x: x.get("view_count", 0), reverse=True)
        elif sort_by == "oldest":
            res = sorted(res, key=lambda x: str(x.get("published_at", "")))
        else:  # default latest
            res = sorted(res, key=lambda x: str(x.get("published_at", "")), reverse=True)

        return res
    except Exception as e:
        print(f"[Shorts Feed Error]: {e}")
        return []

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    react_index = FRONTEND_DIST / "index.html"
    if not react_index.exists():
        raise HTTPException(
            status_code=500,
            detail="React frontend build not found. Please run 'npm run build' inside the frontend directory."
        )
    with open(react_index, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
