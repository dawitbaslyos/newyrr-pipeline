import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from config import Config

ENGINES_DIR = Path(__file__).resolve().parent
RENDERER_DIR = ENGINES_DIR / "mograph_renderer"
RENDER_SCRIPT = RENDERER_DIR / "render_scene.js"

CLAUDE_MOGRAPH_SYSTEM_PROMPT = """You are Claude 5.5, the world's foremost Motion Design Director and Front-End Kinetic Graphics Architect.
Your task is to generate a standalone, high-retention 9:16 vertical (1080x1920) motion design scene for YouTube Shorts (in the caliber of Vox, Kurzgesagt, Zack D. Films, and 3Blue1Brown).

MANDATORY RULES:
1. Output ONLY valid, raw, standalone HTML inside an ```html codeblock. No conversational chat, no introductions.
2. The HTML MUST include:
   - Full 1080x1920 styling: `width: 1080px; height: 1920px; overflow: hidden; background: #07090e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;`
   - Crisp, detailed SVG vector artwork inside a centralized stage with glowing radial backgrounds and dark-mode aesthetic.
   - Distinct SVG `<g id="...">` layers with semantic names (e.g. `main_subject`, `internal_core`, `measuring_ring`, `radar_grid`, `pulse_wave`).
   - A modern typography callout with high-contrast badge and bold punchy headline.
   - GSAP timeline animation (GSAP script will be included via `<script>` tag).
3. GSAP TIMELINE & FRAME CONTROL (CRITICAL):
   - You MUST declare `const tl = gsap.timeline({ paused: true });`
   - Build a smooth timeline lasting EXACTLY `__DURATION__` seconds with entrance choreography and kinetic looping/oscillations.
   - You MUST expose:
     ```javascript
     window.seekTimeline = function(t) { tl.seek(t); };
     window.__ready = true;
     ```
4. PALETTE & AESTHETIC:
   - High contrast neon accents: Electric Cyan (`#00f2fe`), Neon Gold (`#ffd000`), Vivid Emerald (`#10b981`), Radiant Rose (`#ff2a6d`).
   - Dark graphite / obsidian backgrounds with subtle ambient blur radial gradients.
   - Zero external font downloads or external image links. Pure self-contained CSS and SVG!
"""

class ClaudeNativeMograph:
    """
    Claude 5.5 (Opus / Sonnet) Native Motion Graphics Engine.
    Leverages Claude's elite spatial reasoning to author bespoke HTML5/SVG/GSAP kinetic scenes,
    rendered deterministically into 1080x1920 30fps MP4s via headless Chromium.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.model = model or getattr(Config, "OPENROUTER_MODEL", "anthropic/claude-sonnet-5.5")
        self.renderer_dir = RENDERER_DIR
        self.render_script = RENDER_SCRIPT
        
        # Load local bundled GSAP script
        gsap_path = self.renderer_dir / "node_modules" / "gsap" / "dist" / "gsap.min.js"
        if gsap_path.exists():
            self.gsap_script = gsap_path.read_text(encoding="utf-8")
        else:
            self.gsap_script = ""

    def generate_scene_code(
        self,
        prompt: str,
        narration: str,
        duration: float = 5.0,
        aspect_ratio: str = "9:16",
        escalation_badge: Optional[str] = None
    ) -> str:
        """
        Calls Claude 5.5 via OpenRouter to author the complete self-contained HTML/SVG/GSAP file.
        """
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        badge = escalation_badge or "Key Visual"

        user_prompt = (
            f"Topic/Concept: {prompt}\n"
            f"Narration Context: '{narration}'\n"
            f"Aspect Ratio: {width}x{height} ({aspect_ratio})\n"
            f"Duration: {duration} seconds\n"
            f"Badge Label: '{badge}'\n\n"
            "Author a visually breathtaking, kinetic vector motion graphic scene with animated SVG layers and GSAP timeline."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/internetchill/newyrr-pipeline",
            "X-Title": "Newyrr Studio - Claude Mograph",
            "Content-Type": "application/json"
        }

        # Prioritize Claude 5.5 / 3.7 models for code generation
        models = [
            self.model,
            "anthropic/claude-sonnet-5.5",
            "anthropic/claude-opus-5.5",
            "anthropic/claude-3.7-sonnet",
            "google/gemini-2.5-flash",
            "deepseek/deepseek-chat"
        ]
        seen = set()
        clean_models = [m for m in models if m and not (m in seen or seen.add(m))]

        for mod in clean_models:
            try:
                print(f"[Claude Mograph] Calling {mod} for bespoke motion design...")
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": mod,
                        "messages": [
                            {"role": "system", "content": CLAUDE_MOGRAPH_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.4,
                        "max_tokens": 4096
                    },
                    timeout=90
                )

                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "").strip()
                        # Extract HTML
                        m = re.search(r'```(?:html)?\s*(<!DOCTYPE[\s\S]*?<\/html>)\s*```', content, re.IGNORECASE)
                        if m:
                            html = m.group(1)
                        else:
                            m2 = re.search(r'(<!DOCTYPE[\s\S]*?<\/html>)', content, re.IGNORECASE)
                            html = m2.group(1) if m2 else content

                        # Inject local GSAP bundle if external or placeholder
                        if "<script>__GSAP_SCRIPT__</script>" in html:
                            html = html.replace("<script>__GSAP_SCRIPT__</script>", f"<script>{self.gsap_script}</script>")
                        elif "cdnjs.cloudflare.com/ajax/libs/gsap" in html:
                            html = re.sub(r'<script\s+src="[^"]*gsap[^"]*"><\/script>', f"<script>{self.gsap_script}</script>", html)
                        elif "</head>" in html and "window.seekTimeline" in html and "gsap" in html:
                            # Prepend local GSAP before first script tag
                            html = html.replace("</head>", f"<script>{self.gsap_script}</script>\n</head>")

                        # Ensure duration variable is set
                        html = html.replace("__DURATION__", str(duration))
                        return html
            except Exception as e:
                print(f"[Claude Mograph] Attempt on {mod} failed: {e}")

        # Fallback to internal procedural template if all cloud calls fail
        from .mograph_engine import HTML_SCENE_TEMPLATE
        return HTML_SCENE_TEMPLATE.replace("__DURATION__", str(duration)).replace("__WIDTH__", str(width)).replace("__HEIGHT__", str(height))

    def render_motion_scene(
        self,
        scene_number: int,
        prompt: str,
        narration: str,
        duration: float,
        output_dir: Path,
        aspect_ratio: str = "9:16",
        escalation_badge: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End-to-End Claude Motion Pipeline:
        1. Claude 5.5 writes bespoke HTML5 + SVG + GSAP code
        2. Saves to scene_XX_claude_mograph.html
        3. Headless Chromium executes frame-by-frame and streams to FFmpeg
        4. Produces scene_XX_video.mp4 and scene_XX_flux.png
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        num = scene_number
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        dur = max(2.0, round(float(duration), 2))

        # 1. Generate code from Claude
        html_code = self.generate_scene_code(
            prompt=prompt,
            narration=narration,
            duration=dur,
            aspect_ratio=aspect_ratio,
            escalation_badge=escalation_badge
        )

        html_file = output_dir / f"scene_{num:02d}_claude_mograph.html"
        html_file.write_text(html_code, encoding="utf-8")

        # 2. Render to MP4 via Chromium pipe
        video_output = output_dir / f"scene_{num:02d}_video.mp4"
        cmd = [
            "node",
            str(self.render_script),
            "--html", str(html_file),
            "--output", str(video_output),
            "--duration", str(dur),
            "--fps", "30",
            "--width", str(width),
            "--height", str(height)
        ]

        print(f"[Claude Mograph] Rendering Scene {num} ({dur}s @ 30fps)...")
        res = subprocess.run(
            cmd,
            cwd=str(self.renderer_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if not video_output.exists() or video_output.stat().st_size < 1000:
            # Fallback to standard mograph engine if custom html failed headless execution
            print(f"[Claude Mograph] Chromium render issue: {res.stderr[:200]}, falling back to robust template...")
            from .mograph_engine import mograph_engine
            return mograph_engine.render_programmatic_scene(
                scene_number=num,
                prompt=prompt,
                narration=narration,
                duration=dur,
                output_dir=output_dir,
                aspect_ratio=aspect_ratio,
                escalation_badge=escalation_badge
            )

        # 3. Extract Keyframe Still (at 0.5s) for UI preview
        image_output = output_dir / f"scene_{num:02d}_flux.png"
        extract_cmd = [
            "ffmpeg", "-y",
            "-ss", "0.5",
            "-i", str(video_output),
            "-vframes", "1",
            "-q:v", "2",
            str(image_output)
        ]
        subprocess.run(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print(f"[Claude Mograph] Scene {num} Rendered Successfully -> {video_output.name}")
        return {
            "success": True,
            "scene_number": num,
            "video_file": str(video_output),
            "image_file": str(image_output),
            "html_file": str(html_file),
            "duration": dur
        }

claude_mograph = ClaudeNativeMograph()
