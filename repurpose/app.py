import os
import sys
import uuid
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from database import (
    init_db, get_all_accounts, get_account_by_id, create_account, update_account, delete_account,
    get_all_channels, get_channel, upsert_channel, update_channel_prompt, update_channel_status, delete_channel,
    get_videos, get_video_by_id, update_video_transcript,
    create_project, get_all_projects, get_project_by_id, update_project, delete_project,
    get_stats
)
from resolver import resolve_channel
from tracker import track_channel, track_all_active_channels
from fetcher import get_video_transcript
from config import get_config, save_config
from trend_engine import generate_trending_topics, generate_story_script
from repurpose_engine import (
    repurpose_viral_video, generate_explainer_script, render_repurposed_video, RENDERS_DIR
)

init_db()

app = FastAPI(title="YouTube Automation Studio", version="2.0.0")

# Request Models
class AccountCreateRequest(BaseModel):
    name: str
    target_niche: Optional[str] = "Technology"
    prompt_preset: Optional[str] = ""

class AccountUpdateRequest(BaseModel):
    name: Optional[str] = None
    target_niche: Optional[str] = None
    prompt_preset: Optional[str] = None

class ChannelCreateRequest(BaseModel):
    url_or_handle: str
    custom_prompt: Optional[str] = ""
    account_id: Optional[str] = None

class ChannelUpdateRequest(BaseModel):
    title: Optional[str] = None
    custom_prompt: Optional[str] = None
    active: Optional[bool] = None

class TranscriptUpdateRequest(BaseModel):
    transcript: str

class TopicProjectRequest(BaseModel):
    account_id: str
    topic: str
    hook: str
    angle: str

class RepurposeProjectRequest(BaseModel):
    video_id: str
    account_id: str

class RepurposePlanRequest(BaseModel):
    video_id: str
    account_id: str
    target_seconds: Optional[int] = 45

class RepurposeRenderRequest(BaseModel):
    video_id: str
    account_id: str
    narration_text: str
    voice: Optional[str] = "christopher"
    format_mode: Optional[str] = "original_16_9"
    watermark_defense: Optional[str] = "punch_in"
    burn_subtitles: Optional[bool] = True

class ProjectUpdateRequest(BaseModel):
    stage: Optional[str] = None
    title: Optional[str] = None
    script_data: Optional[Dict[str, Any]] = None
    assets_data: Optional[Dict[str, Any]] = None

class ConfigUpdateRequest(BaseModel):
    openrouter_api_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    runpod_api_key: Optional[str] = None
    runpod_flux_endpoint: Optional[str] = None
    runpod_ltx_endpoint: Optional[str] = None
    runpod_tts_endpoint: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    youtube_api_client_secrets: Optional[str] = None

# ----------------- System Stats -----------------
@app.get("/api/status")
def status_endpoint(account_id: Optional[str] = None):
    stats = get_stats(account_id=account_id)
    return {
        "status": "online",
        "stats": stats
    }

# ----------------- Accounts API -----------------
@app.get("/api/accounts")
def list_accounts():
    return get_all_accounts()

@app.post("/api/accounts")
def add_account(payload: AccountCreateRequest):
    account_id = f"acc-{uuid.uuid4().hex[:8]}"
    acc = create_account(
        account_id=account_id,
        name=payload.name,
        target_niche=payload.target_niche or "Technology",
        prompt_preset=payload.prompt_preset or ""
    )
    return {"message": "Account created", "account": acc}

@app.get("/api/accounts/{account_id}")
def single_account(account_id: str):
    acc = get_account_by_id(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return acc

@app.put("/api/accounts/{account_id}")
def edit_account(account_id: str, payload: AccountUpdateRequest):
    acc = update_account(
        account_id=account_id,
        name=payload.name,
        target_niche=payload.target_niche,
        prompt_preset=payload.prompt_preset
    )
    return {"message": "Account updated", "account": acc}

@app.delete("/api/accounts/{account_id}")
def remove_account(account_id: str):
    delete_account(account_id)
    return {"message": f"Account {account_id} deleted"}

# ----------------- Channels API (Filtered by Account) -----------------
@app.get("/api/channels")
def list_channels(account_id: Optional[str] = None):
    return get_all_channels(account_id=account_id)

@app.post("/api/channels")
def add_channel(payload: ChannelCreateRequest):
    resolved = resolve_channel(payload.url_or_handle)
    if not resolved:
        raise HTTPException(status_code=400, detail="Could not resolve YouTube channel from input.")
    
    # Associate with active account if provided
    upsert_channel(
        channel_id=resolved["id"],
        title=resolved["title"],
        handle=resolved.get("handle", ""),
        channel_url=resolved.get("url", ""),
        custom_prompt=payload.custom_prompt or "",
        avatar_url=resolved.get("avatar_url", ""),
        active=1,
        account_id=payload.account_id
    )
    
    track_result = track_channel(resolved["id"])
    return {
        "message": "Channel added and synced successfully",
        "channel": get_channel(resolved["id"]),
        "sync_result": track_result
    }

@app.put("/api/channels/{channel_id}")
def edit_channel(channel_id: str, payload: ChannelUpdateRequest):
    ch = get_channel(channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    if payload.custom_prompt is not None:
        update_channel_prompt(channel_id, payload.custom_prompt)
    if payload.active is not None:
        update_channel_status(channel_id, payload.active)
    return {"message": "Channel updated", "channel": get_channel(channel_id)}

@app.delete("/api/channels/{channel_id}")
def remove_channel(channel_id: str):
    delete_channel(channel_id)
    return {"message": f"Channel {channel_id} deleted"}

@app.post("/api/channels/{channel_id}/fetch")
def sync_channel(channel_id: str):
    ch = get_channel(channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    result = track_channel(channel_id)
    return {"message": f"Synced {ch['title']}", "result": result}

@app.post("/api/fetch-all")
def sync_all_channels():
    result = track_all_active_channels()
    return {"message": "All active channels checked", "result": result}

# ----------------- Videos API -----------------
@app.get("/api/videos")
def list_videos(
    channel_id: Optional[str] = None,
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    return get_videos(channel_id=channel_id, account_id=account_id, pipeline_status=status, limit=limit)

@app.get("/api/videos/{video_id}")
def single_video(video_id: str):
    v = get_video_by_id(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")
    return v

@app.get("/api/videos/{video_id}/transcript")
def get_transcript(video_id: str, refresh: bool = False, whisper_ai: bool = False):
    return get_video_transcript(video_id, force_refresh=refresh, use_ai_fallback=whisper_ai)

@app.put("/api/videos/{video_id}/transcript")
def update_transcript(video_id: str, payload: TranscriptUpdateRequest):
    v = get_video_by_id(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")
    update_video_transcript(video_id, payload.transcript, status="manual")
    return {"message": "Transcript updated", "status": "manual"}

# ----------------- Trend Engine (5 Topics & Scripting) -----------------
@app.post("/api/accounts/{account_id}/generate-topics")
def get_topics_endpoint(account_id: str):
    topics = generate_trending_topics(account_id)
    return {"account_id": account_id, "topics": topics}

@app.post("/api/projects/from-topic")
def create_project_from_topic(payload: TopicProjectRequest):
    # Generate full 4-scene script
    script_data = generate_story_script(
        account_id=payload.account_id,
        topic=payload.topic,
        hook=payload.hook,
        angle=payload.angle
    )
    
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    project = create_project(
        project_id=project_id,
        account_id=payload.account_id,
        source_type="scratch",
        title=script_data.get("title", payload.topic),
        topic=payload.topic,
        stage="script",
        script_data=script_data
    )
    return {"message": "Project created with generated 4-scene script", "project": project}

# ----------------- Repurposing Engine -----------------
@app.post("/api/projects/repurpose")
def repurpose_endpoint(payload: RepurposeProjectRequest):
    project = repurpose_viral_video(video_id=payload.video_id, account_id=payload.account_id)
    return {"message": "Viral video repurposed into project", "project": project}

@app.post("/api/repurpose/plan")
def repurpose_plan_endpoint(payload: RepurposePlanRequest):
    plan = generate_explainer_script(
        video_id=payload.video_id,
        account_id=payload.account_id,
        target_seconds=payload.target_seconds or 45
    )
    return {"video_id": payload.video_id, "plan": plan}

@app.post("/api/repurpose/render")
def repurpose_render_endpoint(payload: RepurposeRenderRequest):
    result = render_repurposed_video(
        video_id=payload.video_id,
        account_id=payload.account_id,
        narration_text=payload.narration_text,
        voice_key=payload.voice or "christopher",
        format_mode=payload.format_mode or "original_16_9",
        watermark_defense=payload.watermark_defense or "punch_in",
        burn_subtitles=payload.burn_subtitles if payload.burn_subtitles is not None else True
    )
    return {"message": "Render completed successfully", "result": result}

# ----------------- Projects Pipeline API -----------------
@app.get("/api/projects")
def list_projects(account_id: Optional[str] = None, stage: Optional[str] = None):
    return get_all_projects(account_id=account_id, stage=stage)

@app.get("/api/projects/{project_id}")
def single_project(project_id: str):
    p = get_project_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p

@app.put("/api/projects/{project_id}")
def edit_project(project_id: str, payload: ProjectUpdateRequest):
    p = update_project(
        project_id=project_id,
        stage=payload.stage,
        title=payload.title,
        script_data=payload.script_data,
        assets_data=payload.assets_data
    )
    return {"message": "Project updated", "project": p}

@app.delete("/api/projects/{project_id}")
def remove_project(project_id: str):
    delete_project(project_id)
    return {"message": f"Project {project_id} deleted"}

# ----------------- Config Credentials -----------------
@app.get("/api/config")
def read_config():
    cfg = get_config()
    masked = {}
    for k, v in cfg.items():
        if "key" in k or "secret" in k:
            if v and len(str(v)) > 8:
                masked[k] = str(v)[:4] + "••••••••" + str(v)[-4:]
            elif v:
                masked[k] = "••••••••"
            else:
                masked[k] = ""
        else:
            masked[k] = v
    return masked

@app.post("/api/config")
def update_config_settings(payload: ConfigUpdateRequest):
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    save_config(updates)
    return {"message": "Credentials saved securely locally", "updated_keys": list(updates.keys())}

# ----------------- Static Frontend -----------------
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

if os.path.exists(RENDERS_DIR):
    app.mount("/renders", StaticFiles(directory=RENDERS_DIR), name="renders")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"message": "Frontend UI file not found. API is active."})
