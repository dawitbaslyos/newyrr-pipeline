import sqlite3
import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "..", "data", "tracker.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Accounts Table (Destination YouTube Channels / Niches)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        target_niche TEXT,
        prompt_preset TEXT,
        avatar_url TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    
    # 2. Channels Table (Tracked Competitor Channels)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id TEXT PRIMARY KEY,
        account_id TEXT,
        title TEXT NOT NULL,
        handle TEXT,
        channel_url TEXT,
        custom_prompt TEXT,
        avatar_url TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT,
        last_checked TEXT,
        FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL
    )
    """)
    
    # Ensure account_id column exists if table existed previously
    try:
        cursor.execute("ALTER TABLE channels ADD COLUMN account_id TEXT")
    except sqlite3.OperationalError:
        pass # Already exists
        
    # 3. Videos Table (Discovered Videos from 0-Quota RSS Tracker)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id TEXT PRIMARY KEY,
        channel_id TEXT NOT NULL,
        title TEXT NOT NULL,
        published_at TEXT,
        thumbnail_url TEXT,
        video_url TEXT,
        description TEXT,
        transcript TEXT,
        transcript_status TEXT DEFAULT 'pending',
        pipeline_status TEXT DEFAULT 'discovered',
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (channel_id) REFERENCES channels (id) ON DELETE CASCADE
    )
    """)
    
    # 4. Projects Table (Production Pipeline: Topic -> Script -> Storyboard -> LTX -> Ready)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        source_type TEXT NOT NULL, -- 'scratch' or 'repurpose'
        source_video_id TEXT,
        title TEXT NOT NULL,
        topic TEXT,
        stage TEXT DEFAULT 'topic', -- 'topic', 'script', 'storyboard', 'rendering', 'ready'
        script_data TEXT, -- JSON structure with scenes, narration, flux/ltx prompts
        assets_data TEXT, -- JSON structure with image paths, video paths, audio paths
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
        FOREIGN KEY (source_video_id) REFERENCES videos (id) ON DELETE SET NULL
    )
    """)

    # Seed Default Account if none exists
    cursor.execute("SELECT COUNT(*) FROM accounts")
    if cursor.fetchone()[0] == 0:
        now = datetime.utcnow().isoformat()
        default_account_id = "main-channel"
        default_preset = (
            "Analyze the core breakthrough in the video. Hook the viewer in the first 3 seconds with a bold insight. "
            "Structure into 4 scenes: Hook -> The Problem -> How It Works -> Future Impact. "
            "For Flux, generate cinematic tech laboratory keyframes in 16:9 with dramatic blue/amber volumetric lighting. "
            "For LTX, direct subtle forward camera zooms with slow particle motion. Tone: confident, technical, snappy."
        )
        cursor.execute("""
        INSERT INTO accounts (id, name, target_niche, prompt_preset, avatar_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (default_account_id, "Main Channel Studio", "AI & Future Technology", default_preset, "", now, now))
        
        # Associate existing channels with this default account
        cursor.execute("UPDATE channels SET account_id = ? WHERE account_id IS NULL", (default_account_id,))

    conn.commit()
    conn.close()

# ----------------- Account CRUD -----------------
def get_all_accounts() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_account_by_id(account_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_account(account_id: str, name: str, target_niche: str = "", prompt_preset: str = "", avatar_url: str = "") -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO accounts (id, name, target_niche, prompt_preset, avatar_url, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (account_id, name, target_niche, prompt_preset, avatar_url, now, now))
    conn.commit()
    conn.close()
    return get_account_by_id(account_id)

def update_account(account_id: str, name: Optional[str] = None, target_niche: Optional[str] = None, prompt_preset: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    fields = []
    values = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if target_niche is not None:
        fields.append("target_niche = ?")
        values.append(target_niche)
    if prompt_preset is not None:
        fields.append("prompt_preset = ?")
        values.append(prompt_preset)
    fields.append("updated_at = ?")
    values.append(now)
    values.append(account_id)
    cursor.execute(f"UPDATE accounts SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_account_by_id(account_id)

def delete_account(account_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()

# ----------------- Channel CRUD -----------------
def get_all_channels(account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    if account_id:
        cursor.execute("SELECT * FROM channels WHERE account_id = ? ORDER BY created_at DESC", (account_id,))
    else:
        cursor.execute("SELECT * FROM channels ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_channel(channel_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_channel(channel_id: str, title: str, handle: str = "", channel_url: str = "", custom_prompt: str = "", avatar_url: str = "", active: int = 1, account_id: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    INSERT INTO channels (id, account_id, title, handle, channel_url, custom_prompt, avatar_url, active, created_at, last_checked)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        account_id = COALESCE(excluded.account_id, channels.account_id),
        title = excluded.title,
        handle = COALESCE(NULLIF(excluded.handle, ''), channels.handle),
        channel_url = COALESCE(NULLIF(excluded.channel_url, ''), channels.channel_url),
        custom_prompt = COALESCE(NULLIF(excluded.custom_prompt, ''), channels.custom_prompt),
        avatar_url = COALESCE(NULLIF(excluded.avatar_url, ''), channels.avatar_url),
        active = excluded.active
    """, (channel_id, account_id, title, handle, channel_url, custom_prompt, avatar_url, active, now, None))
    conn.commit()
    conn.close()

def update_channel_prompt(channel_id: str, custom_prompt: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE channels SET custom_prompt = ? WHERE id = ?", (custom_prompt, channel_id))
    conn.commit()
    conn.close()

def update_channel_status(channel_id: str, active: bool):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE channels SET active = ? WHERE id = ?", (1 if active else 0, channel_id))
    conn.commit()
    conn.close()

def update_channel_checked(channel_id: str):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("UPDATE channels SET last_checked = ? WHERE id = ?", (now, channel_id))
    conn.commit()
    conn.close()

def delete_channel(channel_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
    cursor.execute("DELETE FROM videos WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

# ----------------- Video CRUD -----------------
def save_video(video_dict: Dict[str, Any]) -> bool:
    """Returns True if newly inserted, False if updated."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM videos WHERE id = ?", (video_dict['id'],))
    exists = cursor.fetchone() is not None
    now = datetime.utcnow().isoformat()
    
    if not exists:
        cursor.execute("""
        INSERT INTO videos (id, channel_id, title, published_at, thumbnail_url, video_url, description, transcript, transcript_status, pipeline_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_dict['id'],
            video_dict['channel_id'],
            video_dict['title'],
            video_dict.get('published_at', now),
            video_dict.get('thumbnail_url', ''),
            video_dict.get('video_url', f"https://www.youtube.com/watch?v={video_dict['id']}"),
            video_dict.get('description', ''),
            video_dict.get('transcript', None),
            video_dict.get('transcript_status', 'pending'),
            video_dict.get('pipeline_status', 'discovered'),
            now,
            now
        ))
        conn.commit()
        conn.close()
        return True
    else:
        cursor.execute("""
        UPDATE videos SET
            title = ?,
            thumbnail_url = ?,
            description = ?,
            updated_at = ?
        WHERE id = ?
        """, (
            video_dict['title'],
            video_dict.get('thumbnail_url', ''),
            video_dict.get('description', ''),
            now,
            video_dict['id']
        ))
        conn.commit()
        conn.close()
        return False

def get_videos(channel_id: Optional[str] = None, account_id: Optional[str] = None, pipeline_status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    query = """
    SELECT v.*, COALESCE(c.title, 'Source Creator') as channel_name, COALESCE(c.handle, '') as channel_handle, COALESCE(c.custom_prompt, '') as channel_prompt, c.account_id
    FROM videos v
    LEFT JOIN channels c ON v.channel_id = c.id
    WHERE 1=1
    """
    params = []
    if account_id:
        query += " AND c.account_id = ?"
        params.append(account_id)
    if channel_id:
        query += " AND v.channel_id = ?"
        params.append(channel_id)
    if pipeline_status:
        query += " AND v.pipeline_status = ?"
        params.append(pipeline_status)
        
    query += " ORDER BY v.published_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_video_by_id(video_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT v.*, COALESCE(c.title, 'Source Creator') as channel_name, COALESCE(c.handle, '') as channel_handle, COALESCE(c.custom_prompt, '') as channel_prompt, c.account_id
    FROM videos v
    LEFT JOIN channels c ON v.channel_id = c.id
    WHERE v.id = ?
    """, (video_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_video_transcript(video_id: str, transcript_text: str, status: str = 'fetched'):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
    UPDATE videos SET
        transcript = ?,
        transcript_status = ?,
        updated_at = ?
    WHERE id = ?
    """, (transcript_text, status, now, video_id))
    conn.commit()
    conn.close()

# ----------------- Projects CRUD (Pipeline) -----------------
def create_project(project_id: str, account_id: str, source_type: str, title: str, topic: str = "", source_video_id: Optional[str] = None, stage: str = "topic", script_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    script_json = json.dumps(script_data or {})
    assets_json = json.dumps({})
    cursor.execute("""
    INSERT INTO projects (id, account_id, source_type, source_video_id, title, topic, stage, script_data, assets_data, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_id, account_id, source_type, source_video_id, title, topic, stage, script_json, assets_json, now, now))
    conn.commit()
    conn.close()
    return get_project_by_id(project_id)

def get_all_projects(account_id: Optional[str] = None, stage: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT p.*, a.name as account_name FROM projects p JOIN accounts a ON p.account_id = a.id WHERE 1=1"
    params = []
    if account_id:
        query += " AND p.account_id = ?"
        params.append(account_id)
    if stage:
        query += " AND p.stage = ?"
        params.append(stage)
    query += " ORDER BY p.updated_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        d = dict(r)
        d["script_data"] = json.loads(d["script_data"]) if d.get("script_data") else {}
        d["assets_data"] = json.loads(d["assets_data"]) if d.get("assets_data") else {}
        result.append(d)
    return result

def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT p.*, a.name as account_name FROM projects p JOIN accounts a ON p.account_id = a.id WHERE p.id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["script_data"] = json.loads(d["script_data"]) if d.get("script_data") else {}
    d["assets_data"] = json.loads(d["assets_data"]) if d.get("assets_data") else {}
    return d

def update_project(project_id: str, stage: Optional[str] = None, title: Optional[str] = None, script_data: Optional[Dict[str, Any]] = None, assets_data: Optional[Dict[str, Any]] = None):
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    fields = []
    values = []
    if stage is not None:
        fields.append("stage = ?")
        values.append(stage)
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if script_data is not None:
        fields.append("script_data = ?")
        values.append(json.dumps(script_data))
    if assets_data is not None:
        fields.append("assets_data = ?")
        values.append(json.dumps(assets_data))
    fields.append("updated_at = ?")
    values.append(now)
    values.append(project_id)
    
    cursor.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_project_by_id(project_id)

def delete_project(project_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

# ----------------- Stats -----------------
def get_stats(account_id: Optional[str] = None) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM accounts")
    total_accounts = cursor.fetchone()[0]
    
    if account_id:
        cursor.execute("SELECT COUNT(*) FROM channels WHERE account_id = ?", (account_id,))
        total_channels = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM channels WHERE account_id = ? AND active = 1", (account_id,))
        active_channels = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM videos v JOIN channels c ON v.channel_id = c.id WHERE c.account_id = ?", (account_id,))
        total_videos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM projects WHERE account_id = ?", (account_id,))
        total_projects = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM projects WHERE account_id = ? AND stage = 'ready'", (account_id,))
        ready_projects = cursor.fetchone()[0]
    else:
        cursor.execute("SELECT COUNT(*) FROM channels")
        total_channels = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM channels WHERE active = 1")
        active_channels = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM videos")
        total_videos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM projects WHERE stage = 'ready'")
        ready_projects = cursor.fetchone()[0]
        
    conn.close()
    return {
        "total_accounts": total_accounts,
        "total_channels": total_channels,
        "active_channels": active_channels,
        "total_videos": total_videos,
        "total_projects": total_projects,
        "ready_projects": ready_projects
    }
