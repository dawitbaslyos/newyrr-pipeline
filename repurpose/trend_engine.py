import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

try:
    from .database import get_videos, get_account_by_id
    from .config import get_config
except (ImportError, ValueError):
    from database import get_videos, get_account_by_id
    from config import get_config

def call_openrouter(messages: List[Dict[str, str]], json_mode: bool = True) -> Optional[str]:
    """Helper to query OpenRouter API."""
    cfg = get_config()
    api_key = cfg.get("openrouter_api_key", "").strip()
    model = cfg.get("openrouter_model", "google/gemini-2.0-flash-001").strip()
    
    if not api_key or "••••" in api_key:
        return None
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
        
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8000",
            "X-Title": "YouTube Automation Studio"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[OpenRouter Error]: {e}")
        return None

def generate_trending_topics(account_id: str) -> List[Dict[str, Any]]:
    """
    Analyzes recent uploads from all competitor channels under the account
    and proposes 5 high-potential, hook-driven video topics.
    """
    account = get_account_by_id(account_id)
    niche = account.get("target_niche", "Technology & AI") if account else "Technology & AI"
    prompt_preset = account.get("prompt_preset", "") if account else ""
    
    # Gather up to 30 recent videos from tracked channels in this account
    recent_videos = get_videos(account_id=account_id, limit=30)
    titles_sample = [f"- {v['title']} (from {v['channel_name']})" for v in recent_videos[:20]]
    titles_block = "\n".join(titles_sample) if titles_sample else "No recent videos tracked yet."
    
    sys_prompt = (
        "You are an elite YouTube growth strategist and content director. "
        "Your task is to analyze recent trending videos from competitor channels in a specific niche "
        "and generate 5 fresh, high-velocity video topics that will captivate audiences.\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        '  "topics": [\n'
        '    {\n'
        '      "id": 1,\n'
        '      "topic": "Catchy, High-CTR Video Title",\n'
        '      "hook": "The opening 3-second spoken sentence that stops the scroll.",\n'
        '      "angle": "The unique psychological angle or surprising twist.",\n'
        '      "story_arc": "3-stage narrative summary (The Problem -> The Shift -> The Climax)",\n'
        '      "estimated_scenes": 4\n'
        '    }\n'
        '  ]\n'
        "}"
    )
    
    user_prompt = (
        f"Target Niche: {niche}\n"
        f"Account Creative Preset: {prompt_preset}\n\n"
        f"Here are recent high-performing video titles from tracked competitor channels:\n"
        f"{titles_block}\n\n"
        "Synthesize the emerging trends and propose 5 viral, story-driven video topics."
    )
    
    raw_response = call_openrouter([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ], json_mode=True)
    
    if raw_response:
        try:
            parsed = json.loads(raw_response)
            if "topics" in parsed:
                return parsed["topics"]
        except Exception as e:
            print(f"[Trend Engine] Parse error: {e}")
            
    # Fallback topics if API key not set yet
    return [
        {
            "id": 1,
            "topic": "Why Autonomous AI Agents Will Replace Middle Management First",
            "hook": "Everyone thought robots would replace blue-collar workers, but AI just targeted the Fortune 500 boardroom.",
            "angle": "Inversion of common belief: showing how agentic coding & planning hits middle management instead of entry-level jobs.",
            "story_arc": "The Old Assumption -> The Quiet Reality in Tech Labs -> The 2026 Shift",
            "estimated_scenes": 4
        },
        {
            "id": 2,
            "topic": "The $100 Billion Chip War Nobody Is Talking About",
            "hook": "Behind closed doors, three companies are quietly carving up the next decade of computing power.",
            "angle": "Investigative documentary style revealing the supply chain choke points behind next-gen AI.",
            "story_arc": "The Silicon Bottleneck -> The Secret Alliances -> What Happens If It Breaks",
            "estimated_scenes": 4
        },
        {
            "id": 3,
            "topic": "The 100-Hour Rule: How AI Changed Mastery Forever",
            "hook": "It used to take 10,000 hours to master a skill. Today, an agentic loop does it in a weekend.",
            "angle": "High-velocity personal leverage breakdown with clear actionable paradigm shifts.",
            "story_arc": "The Traditional Skill Curve -> The Agentic Multiplier -> How to Build Your Advantage",
            "estimated_scenes": 4
        },
        {
            "id": 4,
            "topic": "Inside The Secret Lab Redefining Physics Simulations",
            "hook": "Physicists just spent decades on a calculation that a neural model solved in four seconds.",
            "angle": "Awe-inspiring science mystery exploring AI surrogates for Navier-Stokes and quantum mechanics.",
            "story_arc": "The Impossible Equation -> The Neural Leap -> The New Frontier",
            "estimated_scenes": 4
        },
        {
            "id": 5,
            "topic": "The Death of Software as We Know It",
            "hook": "Static codebases are officially obsolete. Here is what is replacing them right now.",
            "angle": "Bold technological insight into self-modifying, autonomous agent architecture.",
            "story_arc": "The Static Era -> Dynamic Agentic Loops -> The Survival Guide",
            "estimated_scenes": 4
        }
    ]

def generate_story_script(account_id: str, topic: str, hook: str, angle: str) -> Dict[str, Any]:
    """
    Generates a full story-paced script, complete with:
    - YouTube SEO metadata
    - Scene-by-scene narrator script (for TTS)
    - Scene-by-scene Flux keyframe prompt (Text-to-Image)
    - Scene-by-scene LTX camera motion directives (Image-to-Video)
    """
    account = get_account_by_id(account_id)
    niche = account.get("target_niche", "Technology") if account else "Technology"
    prompt_preset = account.get("prompt_preset", "") if account else ""
    
    sys_prompt = (
        "You are an expert director of viral, high-retention video stories. "
        "You craft scripts that hook immediately and keep viewers watching until the final second.\n"
        "For each scene, you provide:\n"
        "1. Narration: snappy, natural spoken words for the voice actor (approx 15-20 words per scene).\n"
        "2. Flux Prompt: highly detailed photorealistic/cinematic image generation prompt for the opening keyframe.\n"
        "3. LTX Motion Prompt: precise camera motion and atmospheric dynamics to animate that keyframe into video.\n\n"
        "Return ONLY a JSON object with this exact schema:\n"
        "{\n"
        '  "title": "Optimized Video Title",\n'
        '  "description": "Video description with hook, breakdown, and hashtags",\n'
        '  "tags": ["AI", "Technology", "Future"],\n'
        '  "cta": "Closing question or call to action",\n'
        '  "scenes": [\n'
        '    {\n'
        '      "scene_id": 1,\n'
        '      "heading": "Scene 1: The Hook",\n'
        '      "narration": "Exact words spoken by narrator.",\n'
        '      "duration_est": 5,\n'
        '      "flux_prompt": "Cinematic 16:9, dramatic lighting, 8k...",\n'
        '      "ltx_motion_prompt": "Slow camera push-in, subtle motion..."\n'
        '    }\n'
        '  ]\n'
        "}"
    )
    
    user_prompt = (
        f"Topic: {topic}\n"
        f"Opening Hook: {hook}\n"
        f"Core Angle: {angle}\n"
        f"Niche: {niche}\n"
        f"Style & Pacing Preset:\n{prompt_preset}\n\n"
        "Generate a complete 4-scene story script ready for Flux and LTX-Video production."
    )
    
    raw_response = call_openrouter([
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ], json_mode=True)
    
    if raw_response:
        try:
            return json.loads(raw_response)
        except Exception as e:
            print(f"[Trend Engine] Script parse error: {e}")
            
    # High quality fallback script
    return {
        "title": topic,
        "description": f"{hook}\n\nIn this breakdown, we explore {topic.lower()} and what it means for the future.\n\n#Tech #AI #Innovation #Future",
        "tags": ["AI", "Tech", "Future", "Breakthrough", "Automation"],
        "cta": "Which side of this shift are you preparing for? Let us know below.",
        "scenes": [
            {
                "scene_id": 1,
                "heading": "Scene 1: The Hook",
                "narration": hook,
                "duration_est": 5,
                "flux_prompt": "Cinematic wide angle, high-tech server room with glowing blue quantum processors, dramatic rim lighting, photorealistic, 8k, volumetric smoke",
                "ltx_motion_prompt": "Smooth forward camera dolly into the central processor, glowing pulses along optical cables"
            },
            {
                "scene_id": 2,
                "heading": "Scene 2: The Problem",
                "narration": "For decades, software development was bottlenecked by human keystrokes. But now, machines are writing the machines.",
                "duration_est": 6,
                "flux_prompt": "Close-up of holographic code floating in darkness, neon cyan and amber symbols dissolving into binary geometry, macro cinematic focus",
                "ltx_motion_prompt": "Pan right across the floating code, particles drifting slowly towards the lens"
            },
            {
                "scene_id": 3,
                "heading": "Scene 3: The Breakthrough",
                "narration": "New autonomous agents don't just complete your thoughts—they run entire development pipelines while you sleep.",
                "duration_est": 6,
                "flux_prompt": "Futuristic workstation in a minimalist glass penthouse overlooking a neon city skyline at dusk, screens displaying automated workflows, hyper-detailed",
                "ltx_motion_prompt": "Slow upward crane tilt from the glowing monitors to the twilight metropolis outside"
            },
            {
                "scene_id": 4,
                "heading": "Scene 4: The Verdict",
                "narration": "The question is no longer whether your industry will be automated, but whether you'll be the one directing the agents.",
                "duration_est": 5,
                "flux_prompt": "Silhouette of a visionary strategist standing before a massive glowing digital globe, warm golden cinematic backlighting, atmospheric depth",
                "ltx_motion_prompt": "Subtle slow zoom out as the global network connections illuminate with light pulses"
            }
        ]
    }
