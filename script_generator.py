import json
import os
import requests
from typing import Dict, Any, Optional
from config import Config
from youtube_analytics import YouTubeAnalyticsManager

# Advanced Cinematic Cohesion & Prompt Engineering System (Zack D Films Mise-en-scène Standard)
SYSTEM_PROMPT_TEMPLATE = """You are an elite cinematic visual director, storyteller, and motion choreographer in the style of Zack D Films for the YouTube Shorts channel {channel_handle} ('{channel_niche}').

{analytics_context}

## REQUIRED VISUAL AESTHETIC / ART DIRECTION:
{art_style_directive}

## YOUR OBJECTIVE:
Turn the user's topic into an extraordinary, 5-scene viral YouTube Short (25-30 seconds). Treat every scene as its own self-contained cinematic video production with independent camera setup, photography, tactile blocking, and pacing.

## ZACK D FILMS MISE-EN-SCÈNE & VISUAL ARCHITECTURE:
Every scene operates in two distinct phases: The Stage Picture (First Frame) and The Action Catalyst (Motion Guidance).

1. **First Frame Generation (The Stage Picture / The Set - 'flux_image_prompt')**:
   - Establishes the static "Stage Picture" just BEFORE action triggers (State 0 anticipation).
   - **Set Building & Spatial Blocking**: Precise object/subject placement in 3D space, cutaway cross-sections, anatomical layers, or mechanical assemblies.
   - **Tactile Details**: Subsurface scattering, viscous fluid droplets, microscopic fissures, cellular membranes, surface textures.
   - **Lighting & Lens**: Depth of field (e.g., "Shot on 85mm anamorphic lens at f/1.8"), volumetric rim lighting, unified color signature adhering to {art_style_name}.
   - **STRICT PROHIBITION**: NEVER write meta phrases ('Hyper-realistic 9:16 vertical prompt for Flux Krea', 'An image of', 'A photorealistic shot'). Start immediately with the physical subject and scene blocking.

2. **Motion Guidance (Action Catalyst & Camera Choreography - 'minimax_motion_prompt')**:
   - Each scene is an independent 5-second video clip. The AI video model receives only the initial frame.
   - **ABSOLUTE RULE - ZERO TIMESTAMPS**: NEVER write "At 0.00 seconds", "At 15.00 seconds", or ANY timeline timestamps. The AI model generates a single 4-5s clip from scratch and has no timeline concept.
   - **Camera Choreography**: Direct the camera's physical movement: "Slow continuous macro push-in along the optical axis", "Subtle 20-degree rotational orbit centered on the subject", "Low-angle creeping dolly shot tracking right".
   - **Action Catalyst (The Trigger Event)**: Specify the exact physical event that breaks the stillness (e.g., "The needle shears through the epidermis, unleashing a wave of...", "Viscous cellular foam erupts across the surface, causing...").
   - **Physical Dynamics & Secondary Physics**: Fluid viscosity, particulate dispersion, cellular membrane elasticity, light refracting across moving curves.

3. **Scriptwriting & Viral Hook Rules**:
   - **Hook (0-1.5s)**: Immediate visceral contradiction or mind-bending tactile fact. No greetings, no "did you know".
   - **Pacing**: Exactly 5 scenes. 10-14 spoken words per scene (~5 seconds each).
   - **Infinite Loop**: The final sentence of Scene 5 MUST grammatically connect back into the first word of Scene 1.

You MUST return ONLY valid JSON matching this schema:
{{
  "title": "Viral 5-7 word title with emoji",
  "hook": "Opening hook text",
  "visual_style_bible": "Unified color palette, lighting motif, and tactile aesthetic across all scenes",
  "loop_connection": "Explanation of how Scene 5 loops back to Scene 1",
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 5,
      "narration": "Exact spoken narration text",
      "flux_image_prompt": "Tactile stage picture establishing [subject and set blocking], [materials and textures], [lighting and color palette], shot on [lens/camera]...",
      "minimax_motion_prompt": "[Camera choreography move] as [action catalyst trigger event occurs], capturing [physical reactions, fluid dynamics, and material deformation] with cinematic physics.",
      "sfx_cue": "Specific sound effect cue"
    }}
  ]
}}
"""

ART_STYLE_MAP = {
    "cinematic_film": "35mm Cinematic Film Stock (Kodak Vision3 500T 5219, anamorphic 85mm lens at f/1.8, cool cyan and deep slate shadows, warm amber rim lighting)",
    "macro_science": "Extreme Macro Scientific Realism (85mm macro lens, ultra-detailed tactile textures, cellular subsurface scattering, sterile surgical contrast)",
    "vintage_retro": "1970s Vintage Technicolor Retro (warm Kodachrome 64 tones, authentic halation, slight analog grain, rich saturated ambers and faded teals)",
    "cyberpunk_neon": "Cyberpunk Neon Slate (high contrast chiaroscuro, electric cyan and ultraviolet specular highlights, wet reflective dark surfaces)",
    "documentary_clean": "Clean Modern Documentary (Hasselblad H6D-100c medium format, neutral daylight temperature, hyper-crisp architectural precision)"
}

class ScriptGenerator:
    """
    Generates high-retention screenplays with professional cinematic visual cohesion
    and zero meta-text leakage.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.model = model or Config.OPENROUTER_MODEL
        self.analytics = YouTubeAnalyticsManager()

    def generate_script(self, topic: str, max_retries: int = 2, art_style: Optional[str] = None, channel_handle: Optional[str] = None, channel_niche: Optional[str] = None) -> Dict[str, Any]:
        analytics_context = self.analytics.get_prompt_context()
        art_key = art_style or getattr(Config, "ACTIVE_ART_STYLE", "photo_35mm")
        
        clio_info = getattr(Config, "CLIO_STYLES", {}).get(art_key)
        if clio_info:
            art_name = clio_info.get("name", art_key)
            art_directive = f"Aesthetic Style Name: {art_name}.\nArt Direction: {clio_info.get('prompt', '')}"
        else:
            art_name = art_key
            art_directive = ART_STYLE_MAP.get(art_key, "35mm Photography with authentic Kodak film grain and organic bokeh.")
            
        handle = channel_handle or "@Newyrr"
        niche = channel_niche or "Shorts science. How and what if moments."

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            channel_handle=handle,
            channel_niche=niche,
            analytics_context=analytics_context,
            art_style_directive=art_directive,
            art_style_name=art_name
        )
        user_prompt = f"Create a viral 5-scene cinematic YouTube Short for this topic: '{topic}'"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/internetchill/newyrr-pipeline",
            "X-Title": "Newyrr Studio",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.75,
            "response_format": {"type": "json_object"}
        }

        models_to_try = [self.model, "deepseek/deepseek-v4.1-flash", "openai/gpt-4o-mini"]
        for model in models_to_try:
            payload["model"] = model
            for attempt in range(2):
                try:
                    print(f"[Script Generator] Calling OpenRouter ({model}) for topic: '{topic}'...")
                    res = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=50
                    )

                    if res.status_code == 200:
                        data = res.json()
                        content = data["choices"][0]["message"]["content"]
                        script_data = json.loads(content)
                        self._sanitize_prompts(script_data)
                        return script_data
                    else:
                        print(f"[Script Generator] {model} status {res.status_code}: {res.text[:150]}")
                except Exception as e:
                    print(f"[Script Generator] Attempt {attempt+1} on {model} failed: {e}")

        # High-quality fallback if API fails
        return self._get_fallback_script(topic)

    def _sanitize_prompts(self, script_data: Dict[str, Any]):
        """
        Removes any accidental meta-instruction phrases like 'Hyper-realistic prompt for Flux Krea'
        and strips any timeline timestamps like 'At 0.00 seconds' or 'At 15.00 seconds'.
        """
        import re
        forbidden_phrases = [
            "Hyper-realistic 9:16 vertical prompt for Flux Krea,",
            "Hyper-realistic 9:16 vertical prompt for Flux Krea",
            "prompt for Flux Krea,",
            "prompt for Flux Krea",
            "for Flux Krea,",
            "for Flux Krea",
            "9:16 vertical prompt,",
            "9:16 vertical prompt",
            "A photorealistic 9:16 shot of",
            "A cinematic 9:16 photo of",
            "An image of"
        ]

        for scene in script_data.get("scenes", []):
            # 1. Sanitize Flux Image Prompt (Stage Picture)
            f_prompt = scene.get("flux_image_prompt", "")
            for phrase in forbidden_phrases:
                f_prompt = f_prompt.replace(phrase, "").strip()
            if f_prompt and f_prompt[0].islower():
                f_prompt = f_prompt[0].upper() + f_prompt[1:]
            scene["flux_image_prompt"] = f_prompt

            # 2. Sanitize Motion Guidance Prompt (Action Catalyst) - Strip all timestamps!
            m_prompt = scene.get("minimax_motion_prompt", "")
            # Remove "At 0.00 seconds, ", "At 15.00 seconds, ", "[00:15] ", etc.
            m_prompt = re.sub(r'^[Aa]t \d+(\.\d+)? seconds?,?\s*', '', m_prompt)
            m_prompt = re.sub(r'^[Aa]t \d+:\d+,?\s*', '', m_prompt)
            m_prompt = re.sub(r'^\d+(\.\d+)? seconds? in,?\s*', '', m_prompt)
            m_prompt = re.sub(r'\[?\d+:\d+\]?\s*', '', m_prompt)
            m_prompt = m_prompt.strip()
            if m_prompt and m_prompt[0].islower():
                m_prompt = m_prompt[0].upper() + m_prompt[1:]
            scene["minimax_motion_prompt"] = m_prompt

    def _get_fallback_script(self, topic: str) -> Dict[str, Any]:
        return {
            "title": f"{topic} 🧬",
            "hook": "Your skin isn't holding your tattoo ink. Your immune cells are trapped eating it.",
            "visual_style_bible": "Kodak Vision3 500T 5219 color grade, bioluminescent cyan and warm tungsten amber, 85mm anamorphic macro, volumetric rim light",
            "loop_connection": "The final sentence ends with 'which is why', linking into 'Your skin isn't holding...'",
            "scenes": [
                {
                    "scene_number": 1,
                    "duration_seconds": 5,
                    "narration": "Your skin isn't holding your tattoo ink. Your immune cells are trapped eating it.",
                    "flux_image_prompt": "Tactile stage picture establishing a microscopic cross-section of the human dermis, sharp obsidian black pigment clusters anchored in elastic cellular tissue, surrounding white macrophages frozen in anticipation, Kodak Vision3 500T color science, teal shadows with warm amber rim light, shot on 85mm anamorphic macro lens at f/1.8.",
                    "minimax_motion_prompt": "Slow continuous macro push-in along the optical axis as translucent cellular membranes suddenly flex, engulfing stationary black pigment clusters with organic fluid physics.",
                    "sfx_cue": "Deep biological heartbeat thump"
                },
                {
                    "scene_number": 2,
                    "duration_seconds": 5,
                    "narration": "When a needle pierces your dermis, your body thinks it's under foreign invasion.",
                    "flux_image_prompt": "Tactile stage picture of a polished surgical steel tattoo needle hovering micrometers above elastic skin tissue, microscopic mist droplet spray suspended in atmospheric rim light, dark moody studio backdrop, shot on 85mm macro lens at f/1.8.",
                    "minimax_motion_prompt": "Low-angle creeping dolly tracking downward as the needle shears cleanly through the epidermis, sending microscopic acoustic shockwaves across the elastic skin surface.",
                    "sfx_cue": "High-frequency mechanical hum and skin punch"
                },
                {
                    "scene_number": 3,
                    "duration_seconds": 5,
                    "narration": "Millions of microscopic macrophages rush in to devour the ink, trying to cleanse the wound.",
                    "flux_image_prompt": "Tactile stage picture inside the intercellular matrix, golden glowing macrophage immune cells positioned around crystalline black pigment particles, deep indigo fluid backdrop, shot on 85mm macro lens at f/1.8.",
                    "minimax_motion_prompt": "Subtle 20-degree rotational orbit centered on the subject as amoebic white blood cells extend fluid pseudopods, wrapping around and absorbing shiny pigment granules.",
                    "sfx_cue": "Viscous fluid swoosh"
                },
                {
                    "scene_number": 4,
                    "duration_seconds": 5,
                    "narration": "The ink particles are too massive to digest, so the cells lock in place and die holding them.",
                    "flux_image_prompt": "Tactile stage picture of a single crystallized immune cell locked around an immovable black metallic pigment cluster, cellular wall showing delicate micro-fractures, shot on 85mm macro lens at f/1.8.",
                    "minimax_motion_prompt": "Slow macro push-in as the macrophage cellular structure locks rigid and freezes permanently around the immovable pigment mass.",
                    "sfx_cue": "Crystalline freeze crackle"
                },
                {
                    "scene_number": 5,
                    "duration_seconds": 5,
                    "narration": "Whenever an old cell dies, a new one immediately eats the same ink again, which is why...",
                    "flux_image_prompt": "Tactile stage picture of a dying immune cell releasing trapped obsidian ink, directly adjacent to a fresh vibrant macrophage reaching outward in an infinite cycle, shot on 85mm macro lens at f/1.8.",
                    "minimax_motion_prompt": "Continuous forward dolly tracking through the cellular handover as the dying cell disperses and is instantly engulfed by the incoming macrophage, seamlessly cycling back to scene one.",
                    "sfx_cue": "Rising tension riser cutting sharply"
                }
            ]
        }

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sg = ScriptGenerator()
    test_script = sg.generate_script("Can you taste colors?")
    print("Title:", test_script["title"])
    print("Visual Bible:", test_script.get("visual_style_bible"))
    print("Scene 1 Flux Prompt:", test_script["scenes"][0]["flux_image_prompt"])
    print("Scene 1 Motion Prompt:", test_script["scenes"][0]["minimax_motion_prompt"])
