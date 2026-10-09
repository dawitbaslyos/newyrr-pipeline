import os
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from config import Config
from .svg_generator import generate_vector_asset

ENGINES_DIR = Path(__file__).resolve().parent
RENDERER_DIR = ENGINES_DIR / "mograph_renderer"
RENDER_SCRIPT = RENDERER_DIR / "render_scene.js"

HTML_SCENE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Mograph Scene __SCENE_NUM__</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
      width: __WIDTH__px;
      height: __HEIGHT__px;
      overflow: hidden;
      background: #07090e;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Impact", sans-serif;
    }

    #stage {
      position: relative;
      width: __WIDTH__px;
      height: __HEIGHT__px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at 50% 46%, #121929 0%, #07090e 72%);
    }

    /* Ambient Glow Core */
    .glow-orb {
      position: absolute;
      width: 700px;
      height: 700px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(0, 242, 254, 0.16) 0%, transparent 70%);
      filter: blur(50px);
      pointer-events: none;
    }

    /* SVG Stage */
    #svg-stage {
      width: 620px;
      height: 620px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      z-index: 10;
    }

    #svg-stage svg {
      width: 100%;
      height: 100%;
      overflow: visible;
      filter: drop-shadow(0 15px 35px rgba(0, 0, 0, 0.7));
    }

    /* Typography Callout */
    #text-stage {
      margin-top: 48px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 14px;
      z-index: 20;
      padding: 0 40px;
    }

    .badge-pill {
      background: rgba(0, 242, 254, 0.12);
      border: 2px solid rgba(0, 242, 254, 0.45);
      color: #00f2fe;
      padding: 8px 24px;
      border-radius: 9999px;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: 2.5px;
      text-transform: uppercase;
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.2);
    }

    .headline {
      color: #ffffff;
      font-size: 58px;
      font-weight: 900;
      text-align: center;
      line-height: 1.15;
      max-width: 880px;
      text-shadow: 0 10px 30px rgba(0,0,0,0.9);
      text-transform: uppercase;
      letter-spacing: -0.5px;
    }

    .highlight {
      color: #ffd000;
    }
  </style>

  <script>__GSAP_SCRIPT__</script>
</head>
<body>
  <div id="stage">
    <div class="glow-orb" id="glow-orb"></div>

    <div id="svg-stage">
      __SVG_CONTENT__
    </div>

    <div id="text-stage">
      __BADGE_HTML__
      __HEADLINE_HTML__
    </div>
  </div>

  <script>
    const tl = gsap.timeline({ paused: true });
    const dur = __DURATION__;

    // 1. Entrance choreography
    tl.fromTo("#svg-stage", 
      { scale: 0.3, opacity: 0, rotation: -10 },
      { scale: 1, opacity: 1, rotation: 0, duration: 0.75, ease: "back.out(1.8)" }
    )
    .fromTo("#text-stage",
      { y: 40, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }, 0.25
    );

    // 2. Animate specific SVG elements if they exist
    const animTargets = [
      { id: "#main_subject", action: { scale: 1.08, yoyo: true, repeat: 1, duration: dur * 0.45, ease: "sine.inOut" } },
      { id: "#radar_ring", action: { rotation: 180, transformOrigin: "center center", duration: dur, ease: "none" } },
      { id: "#radar-ring", action: { rotation: 180, transformOrigin: "center center", duration: dur, ease: "none" } },
      { id: "#core_circle", action: { scale: 1.25, transformOrigin: "center center", yoyo: true, repeat: 3, duration: 0.6, ease: "power2.inOut" } },
      { id: "#pulse_dot", action: { scale: 1.4, transformOrigin: "center center", yoyo: true, repeat: 3, duration: 0.5, ease: "power2.inOut" } },
      { id: "#pointer_arrow", action: { y: -15, yoyo: true, repeat: 3, duration: 0.4, ease: "power1.inOut" } },
      { id: "#axis_h", action: { scaleX: 1.15, transformOrigin: "center center", yoyo: true, repeat: 1, duration: dur * 0.4 } },
      { id: "#axis_v", action: { scaleY: 1.15, transformOrigin: "center center", yoyo: true, repeat: 1, duration: dur * 0.4 } }
    ];

    animTargets.forEach(t => {
      if (document.querySelector(t.id)) {
        tl.to(t.id, t.action, 0.4);
      }
    });

    // 3. Subtle ambient glow oscillation
    tl.to("#glow-orb", {
      scale: 1.2,
      opacity: 0.8,
      duration: dur * 0.5,
      yoyo: true,
      repeat: 1,
      ease: "sine.inOut"
    }, 0);

    window.seekTimeline = function(timeSec) {
      tl.seek(timeSec);
    };

    window.__ready = true;
  </script>
</body>
</html>
"""

class MotionGraphicsEngine:
    """
    High-Performance Programmatic Vector Animation Engine:
    - Zero OpenRouter image/video API credits
    - LLM-directed SVG generation (SVG-ORA pattern)
    - Deterministic GSAP timeline composition (Hyperframes pattern)
    - Headless Chromium + FFmpeg hardware pipe rendering to 1080x1920 MP4
    """

    def __init__(self):
        self.renderer_dir = RENDERER_DIR
        self.render_script = RENDER_SCRIPT
        gsap_path = self.renderer_dir / "node_modules" / "gsap" / "dist" / "gsap.min.js"
        if gsap_path.exists():
            self.gsap_script = gsap_path.read_text(encoding="utf-8")
        else:
            self.gsap_script = ""

    def render_programmatic_scene(
        self,
        scene_number: int,
        prompt: str,
        narration: str,
        duration: float,
        output_dir: Path,
        aspect_ratio: str = "9:16",
        escalation_badge: Optional[str] = None,
        custom_svg_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Renders a full 1080x1920 or 16:9 programmatic vector motion scene.
        Produces:
          - scene_{num:02d}_video.mp4 (Smooth vector animation)
          - scene_{num:02d}_flux.png (Keyframe preview at 0.5s)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        num = scene_number
        
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        dur = max(2.0, round(float(duration), 2))
        
        # 1. Obtain SVG Vector Asset
        if custom_svg_code and custom_svg_code.strip().startswith("<svg"):
            svg_markup = custom_svg_code
        else:
            vector_res = generate_vector_asset(prompt, asset_slug=f"scene_{num:02d}_vector")
            svg_markup = vector_res.get("svg_code", "")

        # 2. Format Badge and Headline
        badge_text = escalation_badge or f"Beat {num}"
        badge_html = f'<div class="badge-pill">{badge_text}</div>'
        
        # Extract a punchy 4-7 word headline from prompt/narration
        headline_raw = narration[:80] if narration else prompt[:60]
        words = re.sub(r'[^a-zA-Z0-9\s]', '', headline_raw).split()
        if len(words) > 7:
            words = words[:7]
        # Highlight last 2 words
        if len(words) >= 3:
            headline_text = " ".join(words[:-2]) + f' <span class="highlight">{" ".join(words[-2:])}</span>'
        else:
            headline_text = " ".join(words)
        headline_html = f'<h1 class="headline">{headline_text}</h1>'

        # 3. Assemble HTML
        html_content = (
            HTML_SCENE_TEMPLATE
            .replace("__SCENE_NUM__", str(num))
            .replace("__WIDTH__", str(width))
            .replace("__HEIGHT__", str(height))
            .replace("__DURATION__", str(dur))
            .replace("__SVG_CONTENT__", svg_markup)
            .replace("__BADGE_HTML__", badge_html)
            .replace("__HEADLINE_HTML__", headline_html)
            .replace("__GSAP_SCRIPT__", self.gsap_script)
        )

        html_file = output_dir / f"scene_{num:02d}_mograph.html"
        html_file.write_text(html_content, encoding="utf-8")

        # 4. Render Video via Headless Chrome + FFmpeg
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

        print(f"[Mograph Engine] Executing render for Scene {num} ({dur}s @ 30fps)...")
        res = subprocess.run(
            cmd,
            cwd=str(self.renderer_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if not video_output.exists() or video_output.stat().st_size < 1000:
            raise RuntimeError(f"Programmatic render failed: {res.stderr}\n{res.stdout}")

        # 5. Extract Keyframe Still (at 0.5s) for UI preview
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

        print(f"[Mograph Engine] Scene {num} Complete -> {video_output.name} & {image_output.name}")
        return {
            "success": True,
            "scene_number": num,
            "video_file": str(video_output),
            "image_file": str(image_output),
            "html_file": str(html_file),
            "duration": dur
        }

mograph_engine = MotionGraphicsEngine()
