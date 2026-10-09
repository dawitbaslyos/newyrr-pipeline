import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any
from config import Config

SVG_LIBRARY_DIR = Config.BASE_DIR / "data" / "svg_library"
SVG_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

SVG_ORA_SYSTEM_PROMPT = """You are SVG-ORA, an elite AI Vector Graphics & Technical Illustration Specialist.
Your job is to generate production-quality, modern, crisp SVG vector assets for YouTube Shorts explainer videos (Vox, Kurzgesagt, Zack D. Films, MagnatesMedia style).

STRICT RULES FOR OUTPUT:
1. Output ONLY valid, raw, standalone SVG code inside ```xml or ```svg codeblocks. No conversational filler.
2. The root element must be: <svg viewBox="0 0 800 800" width="800" height="800" xmlns="http://www.w3.org/2000/svg">
3. Use a modern, high-retention dark-mode palette:
   - Primary accents: Cyan (#00f2fe), Neon Gold (#ffd000), Emerald (#10b981), Crimson (#ff3b30)
   - Secondary lines & accents: #3b82f6, #6366f1, #8b5cf6
   - Structural & base geometry: #1e293b, #0f172a, #334155
   - Highlights & Text: #ffffff, #f8fafc
4. MODULAR ANIMATION READINESS:
   - Group major logical components inside <g id="..."> tags with semantic IDs!
     Examples: <g id="main_subject">, <g id="glow_aura">, <g id="measuring_gauge">, <g id="pointer_arrow">, <g id="internal_core">, <g id="data_pulse">
   - Set transform-origin friendly coordinates.
5. High technical detail:
   - Include concentric diagnostic circles, dashed measurement lines (stroke-dasharray="8 6"), technical crosshairs, and glowing radial gradients (<defs><radialGradient ...></defs>).
6. NEVER include raster bitmap images (<img>, <image>). Everything must be 100% pure vector paths, circles, rects, and polylines.
"""

def clean_svg_output(raw_text: str) -> str:
    """Extracts clean SVG code from LLM response."""
    # Look for ```xml ... ``` or ```svg ... ```
    match = re.search(r'```(?:xml|svg)?\s*(<svg[\s\S]*?<\/svg>)\s*```', raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Fallback to direct <svg> ... </svg>
    match = re.search(r'(<svg[\s\S]*?<\/svg>)', raw_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
        
    return raw_text.strip()

def generate_vector_asset(
    prompt: str,
    asset_slug: Optional[str] = None,
    category: str = "explainer",
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calls LLM (OpenRouter / Gemini) using the SVG-ORA system prompt to produce
    a pristine vector illustration for programmatic animation.
    """
    from llm_client import call_llm
    
    active_model = model or getattr(Config, "ACTIVE_LLM_MODEL", "google/gemini-2.5-flash")
    user_prompt = f"Create a technical, high-retention SVG vector illustration for the following concept:\n{prompt}\n\nEnsure major visual elements are grouped with descriptive id attributes for animation."
    
    print(f"[SVG-ORA] Generating vector asset for: '{prompt[:60]}...' using {active_model}")
    try:
        raw_response = call_llm(
            prompt=user_prompt,
            system_prompt=SVG_ORA_SYSTEM_PROMPT,
            model=active_model,
            temperature=0.4
        )
        svg_code = clean_svg_output(raw_response)
        
        if not svg_code.startswith("<svg"):
            raise ValueError("LLM response did not contain valid SVG markup.")
            
        slug = asset_slug or f"vector_{re.sub(r'[^a-zA-Z0-9]+', '_', prompt[:30]).strip('_').lower()}"
        file_path = SVG_LIBRARY_DIR / f"{slug}.svg"
        file_path.write_text(svg_code, encoding="utf-8")
        
        print(f"[SVG-ORA] Successfully saved vector asset: {file_path.name}")
        return {
            "success": True,
            "svg_code": svg_code,
            "file_path": str(file_path),
            "slug": slug
        }
    except Exception as e:
        print(f"[SVG-ORA Error]: {e}")
        # Return fallback diagnostic SVG
        fallback_svg = f"""<svg viewBox="0 0 800 800" width="800" height="800" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="fallbackGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00f2fe" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#07090e" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <circle cx="400" cy="400" r="350" fill="url(#fallbackGlow)"/>
  <circle id="radar_ring" cx="400" cy="400" r="280" stroke="#00f2fe" stroke-width="6" stroke-dasharray="16 12" fill="none"/>
  <circle id="core_circle" cx="400" cy="400" r="140" fill="#00f2fe" fill-opacity="0.15" stroke="#ffd000" stroke-width="8"/>
  <line id="axis_h" x1="120" y1="400" x2="680" y2="400" stroke="#00f2fe" stroke-width="4" stroke-linecap="round"/>
  <line id="axis_v" x1="400" y1="120" x2="400" y2="680" stroke="#00f2fe" stroke-width="4" stroke-linecap="round"/>
</svg>"""
        return {
            "success": False,
            "error": str(e),
            "svg_code": fallback_svg,
            "file_path": None,
            "slug": "fallback_vector"
        }
