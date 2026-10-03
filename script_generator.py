import json
import os
import re
import requests
from typing import Dict, Any, Optional
from config import Config
from youtube_analytics import YouTubeAnalyticsManager

# ─────────────────────────────────────────────────────────────────────────────
# THE UNIFIED 5-BEAT CAUSAL STORYTELLING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are an elite cinematic director and master short-form screenwriter for the channel {channel_handle} ('{channel_niche}').

{archetype_directive}

{analytics_context}

## CURRENT ART STYLE DIRECTIVE:
{art_style_directive}

---

## CORE ARCHITECTURAL LAWS (NON-NEGOTIABLE):

### 1. THE 5-BEAT CAUSAL CHAIN SCRIPT
Every script consists of EXACTLY 5 progressive scenes (25–30 seconds total, 12–16 spoken words per scene, ~70 words total).
Every scene MUST follow the Causal Chain ("Because of A, B happens; which triggers C"):

- **Scene 1 (The Paradox Hook, 0–2s)**:
  * State a shocking, counter-intuitive fact or impossible reality with absolute documentary authority.
  * **STRICT PROHIBITION**: NEVER use greetings ("Hey everyone"), rhetorical questions ("Have you ever wondered?"), exclamation marks, childish nicknames ("cheesy menace", "stinky bugs"), or generic hype ("You won't believe this").
- **Scene 2 (The Underlying Mechanism / Context, 2–8s)**:
  * Deliver the exact physical mechanism, biological organ, historical origin year, or life context.
- **Scene 3 (The Kinetic Reaction / The Escalation, 8–16s)**:
  * The unseen physical reaction, physiological cascade, or escalating human crisis.
- **Scene 4 (The Turning Point / Consequence, 16–24s)**:
  * The extreme metric, medical anomaly, or historical shift that reveals the true scale.
- **Scene 5 (The Closed-Loop Reveal, 24–30s)**:
  * The shocking resolution that makes total sense in retrospect.
  * **Infinite Loop Requirement**: The final sentence MUST end on a grammatical setup that loops seamlessly back into the very first word of Scene 1.

### 2. NARRATOR VOICE & TONE:
* Zero preachy advice. NEVER write "Remember to...", "Be sure to clean...", "Always make sure...", or moralistic lectures.
* Zero exclamation marks.
* Cold, intelligent, highly respectful of the viewer's intellect. Speak with the cadence of an elite documentary narrator.

### 3. MASTER SCENE ANCHORING (STRICT CONTINUITY):
To prevent jarring visual disconnects between cuts, you MUST define ONE persistent Master Subject and spatial world before writing prompts:
- All 5 scenes are progressive camera shots of the **SAME physical subject and environment**.
- Maintain the exact same lighting signature and color palette across all scenes.

### 4. KEYFRAME PROMPT ARCHITECTURE ('flux_image_prompt'):
- Uncluttered, vertical 9:16 mobile composition.
- **Formula**: `[Shot distance and lens] of [Master Subject performing this beat's action], [consistent environment backdrop], [lighting signature]. Single clear central focal point, clean negative space, uncluttered composition.`
- **BANNED BUZZWORDS**: NEVER write "hyperrealistic", "4k", "trending on artstation", "halftone patterns", "abstract glowing lines", or meta phrases like "prompt for flux". Keep it purely physical and tangible.

### 5. MOTION GUIDANCE ('minimax_motion_prompt'):
- Direct the **physical kinetics of the subject**, NOT the camera. Video AI models morph or ruin the shot when told to zoom or pan.
- **Formula**: `The [master subject] [actively physically deforms / breaks / releases fluid / moves with momentum], [secondary physical particle/fluid reaction], fixed static camera frame.`
- **STRICT PROHIBITION**: NEVER include timestamps ("At 0.00 seconds", "[00:15]"). Video models generate single isolated 5-second clips.

---

You MUST output ONLY valid JSON matching this exact schema:
{{
  "title": "5-7 word compelling title with one relevant emoji",
  "hook": "Opening hook line from Scene 1",
  "master_visual_bible": {{
    "master_subject": "Precise description of the single persistent subject/character/organ",
    "environment": "Unified spatial background and room/setting",
    "color_palette": "Specific 3-color harmony and film/render lighting tone"
  }},
  "loop_connection": "Explanation of how Scene 5 grammatically flows into Scene 1",
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 5,
      "narration": "12-16 words of authoritative spoken narration",
      "flux_image_prompt": "Clean, uncluttered 9:16 prompt establishing master subject with clear single focal point...",
      "minimax_motion_prompt": "Physical kinetic momentum and material deformation of the subject, fixed static camera...",
      "sfx_cue": "Specific tactile sound design cue"
    }},
    {{
      "scene_number": 2,
      "duration_seconds": 5,
      "narration": "12-16 words explaining the underlying physical or historical mechanism",
      "flux_image_prompt": "Medium cutaway shot maintaining the exact master subject in the same environment...",
      "minimax_motion_prompt": "Physical kinetic action of the subject, fixed static camera...",
      "sfx_cue": "Specific tactile sound design cue"
    }},
    {{
      "scene_number": 3,
      "duration_seconds": 5,
      "narration": "12-16 words on the unseen reaction or crisis escalation",
      "flux_image_prompt": "Detailed macro cross-section or closer framing of the master subject...",
      "minimax_motion_prompt": "Physical fluid or mechanical reaction of the subject, fixed static camera...",
      "sfx_cue": "Specific tactile sound design cue"
    }},
    {{
      "scene_number": 4,
      "duration_seconds": 5,
      "narration": "12-16 words on the extreme consequence or turning point",
      "flux_image_prompt": "Dramatic framing maintaining continuity of the master subject and lighting...",
      "minimax_motion_prompt": "Kinetic reaction or deformation, fixed static camera...",
      "sfx_cue": "Specific tactile sound design cue"
    }},
    {{
      "scene_number": 5,
      "duration_seconds": 5,
      "narration": "12-16 words revealing the resolution and ending on the infinite loop bridge",
      "flux_image_prompt": "Final full perspective of the master subject in the environment...",
      "minimax_motion_prompt": "Final physical momentum completing the loop, fixed static camera...",
      "sfx_cue": "Specific tactile sound design cue"
    }}
  ]
}}
"""

ARCHETYPE_DIRECTIVES = {
    "tactile_origins": """## CHANNEL PERSONA: TACTILE ORIGINS & ANATOMY (@Newyrr Standard)
You are directing high-end tactile 3D anatomical and historical origin breakdowns in the benchmark caliber of @zackdfilms and @simplihowww.
- Focus: Human body mechanics, medical curiosities, and the surprising physical origins of everyday fashion, inventions, and habits.
- Visuals: Stylized 3D tactile cutaways, cross-sections showing interior muscular/skeletal/cellular layers, or authentic historical craftsmanship.
- Pacing: Clinical precision, physical cause-and-effect, visceral curiosity.""",

    "human_drama": """## CHANNEL PERSONA: EXTRAORDINARY HUMAN STORIES (@internetChill Standard)
You are directing gripping real-life human interest documentaries and bizarre true phenomena in the benchmark caliber of @afrimaxenglish, @wholesomewendy, and @hisystory.
- Focus: Unbelievable real people, extreme survival feats, medical anomalies, and wild, weird, or unforgettable life moments.
- Visuals: Cinematic 35mm film stills, high-contrast atmospheric lighting, realistic character portraits, expressive human emotion, dramatic natural environments.
- Pacing: High-stakes tension, emotional depth, escalating suspense, and profound psychological turns.""",

    "badass_cinema": """## CHANNEL PERSONA: BADASS CINEMA MOMENTS (@MainQuestCC Standard)
You are directing high-octane cinematic scene breakdowns and badass character showdowns.
- Focus: Calculated moves, psychological outsmarting, iconic dialogue beats, and intense character confrontations.
- Visuals: Cinematic anamorphic film stills, moody chiaroscuro lighting, razor-sharp focus on expressions and tactical gear.
- Pacing: Tight, tension-building, punchy."""
}

ART_STYLE_MAP = {
    "render_unreal": "3D Cinematic CGI Render (Unreal Engine 5 Lumen lighting, smooth tactile physical surfaces, soft ambient occlusion, crisp single focal point)",
    "photo_35mm": "35mm Cinematic Film Still (Kodak Vision3 500T, authentic fine grain, natural depth of field, documentary realism, clean composition)",
    "digital_xray": "Tactile Anatomical Cutaway (translucent internal biological layers, soft internal illumination, clean slate background, medical precision)",
    "paint_chiaroscuro": "Dramatic Chiaroscuro (deep moody shadow contrast, focused warm key light, rich sculptural depth, timeless painterly weight)"
}


class ScriptGenerator:
    """
    Unified High-Retention Storytelling Engine for YouTube Shorts.
    Enforces the 5-Beat Causal Story Arc, Master Subject Continuity,
    and Decluttered Keyframe & Motion Directives.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.model = model or Config.OPENROUTER_MODEL
        self.analytics = YouTubeAnalyticsManager()

    def _determine_archetype(self, handle: str, niche: str) -> str:
        handle_lower = handle.lower()
        niche_lower = niche.lower()
        if "internetchill" in handle_lower or "people" in niche_lower or "story" in niche_lower or "moment" in niche_lower:
            return "human_drama"
        elif "mainquest" in handle_lower or "movie" in niche_lower or "badass" in niche_lower:
            return "badass_cinema"
        else:
            return "tactile_origins"

    def generate_script(
        self,
        topic: str,
        max_retries: int = 2,
        art_style: Optional[str] = None,
        channel_handle: Optional[str] = None,
        channel_niche: Optional[str] = None
    ) -> Dict[str, Any]:
        handle = channel_handle or "@Newyrr"
        niche = channel_niche or "How-to and origins of the human body, fashion, lifestyle, and physical mechanics."
        archetype_key = self._determine_archetype(handle, niche)
        archetype_directive = ARCHETYPE_DIRECTIVES.get(archetype_key, ARCHETYPE_DIRECTIVES["tactile_origins"])

        # Fetch performance intelligence
        analytics_context = self.analytics.get_prompt_context(handle)
        try:
            from competitor_tracker import competitor_tracker
            from channel_manager import channel_mgr
            tracked = channel_mgr.get_data().get("tracked_channels", [])
            comp_context = competitor_tracker.get_competitor_context_for_llm(tracked)
            full_context = f"{analytics_context}\n\n{comp_context}"
        except Exception:
            full_context = analytics_context

        art_key = art_style or getattr(Config, "ACTIVE_ART_STYLE", "render_unreal")
        clio_info = getattr(Config, "CLIO_STYLES", {}).get(art_key)
        if clio_info:
            art_name = clio_info.get("name", art_key)
            art_directive = f"Aesthetic: {art_name}. Visual Direction: {clio_info.get('prompt', '')}"
        else:
            art_name = art_key
            art_directive = ART_STYLE_MAP.get(art_key, ART_STYLE_MAP["render_unreal"])

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            channel_handle=handle,
            channel_niche=niche,
            archetype_directive=archetype_directive,
            analytics_context=full_context,
            art_style_directive=art_directive
        )
        user_prompt = (
            f"Produce an elite 5-scene viral Short for this topic: '{topic}'.\n"
            f"Enforce the 5-Beat Causal Storytelling Chain, absolute master subject continuity, "
            f"zero preachy advice, and uncluttered visual prompts."
        )

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
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }

        models_to_try = [self.model, "anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"]
        # Deduplicate models
        seen = set()
        clean_models = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

        for model in clean_models:
            payload["model"] = model
            for attempt in range(max_retries):
                try:
                    print(f"[Script Generator] Calling OpenRouter ({model}) for topic: '{topic}'...")
                    res = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=55
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

        # Fallback if cloud APIs are unavailable
        return self._get_fallback_script(topic, archetype_key)

    def _sanitize_prompts(self, script_data: Dict[str, Any]):
        """
        Strips meta-instruction leaks, unwanted buzzwords, and all timeline timestamps.
        """
        forbidden_image_phrases = [
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
            "An image of",
            "trending on artstation",
            "4k resolution",
            "8k resolution",
            "hyperrealistic"
        ]

        for scene in script_data.get("scenes", []):
            # 1. Clean Keyframe Image Prompt
            f_prompt = scene.get("flux_image_prompt", "")
            for phrase in forbidden_image_phrases:
                f_prompt = f_prompt.replace(phrase, "").strip()
            # Clean leading lowercase or punctuation
            f_prompt = re.sub(r'^[,.\s]+', '', f_prompt)
            if f_prompt and f_prompt[0].islower():
                f_prompt = f_prompt[0].upper() + f_prompt[1:]
            scene["flux_image_prompt"] = f_prompt

            # 2. Clean Motion Prompt: Strip timestamps and camera panning
            m_prompt = scene.get("minimax_motion_prompt", "")
            m_prompt = re.sub(r'^[Aa]t \d+(\.\d+)? seconds?,?\s*', '', m_prompt)
            m_prompt = re.sub(r'^[Aa]t \d+:\d+,?\s*', '', m_prompt)
            m_prompt = re.sub(r'^\d+(\.\d+)? seconds? in,?\s*', '', m_prompt)
            m_prompt = re.sub(r'\[?\d+:\d+\]?\s*', '', m_prompt)
            m_prompt = re.sub(r'^[,.\s]+', '', m_prompt).strip()
            if m_prompt and m_prompt[0].islower():
                m_prompt = m_prompt[0].upper() + m_prompt[1:]
            scene["minimax_motion_prompt"] = m_prompt

            # 3. Clean Narration: Eradicate exclamation marks and preachy phrases
            narration = scene.get("narration", "")
            narration = narration.replace("!", ".").replace("  ", " ").strip()
            scene["narration"] = narration

    def _get_fallback_script(self, topic: str, archetype: str) -> Dict[str, Any]:
        """Provides instant high-quality zero-API fallback scripts matching the archetype."""
        if archetype == "human_drama":
            return {
                "title": "Fell Two Miles and Survived ✈️🌿",
                "hook": "In 1971, a seventeen-year-old girl fell two miles out of an airplane strapped to her seat.",
                "master_visual_bible": {
                    "master_subject": "Seventeen-year-old Juliane Koepcke in torn clothing, determined and wounded",
                    "environment": "Dense Peruvian Amazon rainforest, muddy riverbanks, dense mist canopy",
                    "color_palette": "Deep jungle emerald, muted earth tones, soft atmospheric canopy daylight"
                },
                "loop_connection": "The final sentence ends with 'which began when', flowing into 'In 1971...'",
                "scenes": [
                    {
                        "scene_number": 1,
                        "duration_seconds": 5,
                        "narration": "In 1971, a seventeen-year-old girl fell two miles out of an airplane strapped to her seat.",
                        "flux_image_prompt": "Cinematic medium shot of 17-year-old Juliane Koepcke awakening amidst tangled Amazon foliage, airplane seat strapped to her back, morning jungle mist filtering through canopy trees. Single clear central focal point, clean negative space, uncluttered composition.",
                        "minimax_motion_prompt": "The young girl slowly blinks and raises her wounded hand to shield her eyes, moisture dripping from surrounding broad palm leaves, fixed static camera frame.",
                        "sfx_cue": "Distant jungle canopy thunder and morning bird call"
                    },
                    {
                        "scene_number": 2,
                        "duration_seconds": 5,
                        "narration": "The row of passenger seats spun like a maple seed, cushioning her terminal velocity impact.",
                        "flux_image_prompt": "Cutaway angle showing the broken blue airline seat resting against thick springy forest branches, torn fabric and bent metal frame resting in dense vegetation. Clean composition, natural diffused daylight.",
                        "minimax_motion_prompt": "The bent metal seat frame settles with a quiet creak into the thick moss layer, dislodging tiny water droplets, fixed static camera frame.",
                        "sfx_cue": "Metallic creak and foliage rustle"
                    },
                    {
                        "scene_number": 3,
                        "duration_seconds": 5,
                        "narration": "Armed only with a bag of candy, she remembered her father's rule: follow water downstream.",
                        "flux_image_prompt": "Low-angle close-up of Juliane wading through shallow murky river water, determined expression, dense foliage bordering both sides. Single clear focal point, cinematic depth of field.",
                        "minimax_motion_prompt": "Murky river water ripples outward as her bare foot steps firmly onto the riverbed gravel, small bubbles rising to the surface, fixed static camera frame.",
                        "sfx_cue": "Gentle water wading and flowing stream"
                    },
                    {
                        "scene_number": 4,
                        "duration_seconds": 5,
                        "narration": "For eleven days she floated past crocodiles and stinging insects, treating open wounds with gasoline.",
                        "flux_image_prompt": "Intimate cinematic portrait of Juliane floating on her back down a wide jungle river under open sky, exhausted yet resolute, sunlight reflecting off the calm water. Clean balanced framing.",
                        "minimax_motion_prompt": "Calm river currents slowly drift her floating silhouette down the water surface, gentle eddies swirling around her shoulders, fixed static camera frame.",
                        "sfx_cue": "Lapping river water and deep drone"
                    },
                    {
                        "scene_number": 5,
                        "duration_seconds": 5,
                        "narration": "Local lumbermen discovered her inside a river hut, ending an impossible survival journey that began when...",
                        "flux_image_prompt": "Wide cinematic shot from inside an open wooden river shelter, warm lantern light illuminating Juliane resting on a wooden floor, lumbermen silhouette in doorway. High contrast, atmospheric rim light.",
                        "minimax_motion_prompt": "Warm lantern smoke rises gently toward the thatched roof as the wooden door swings slowly open, fixed static camera frame.",
                        "sfx_cue": "Warm wooden door creak and soft acoustic exhale"
                    }
                ]
            }
        else:
            return {
                "title": "Why High Heels Were For Men 👠⚔️",
                "hook": "High heels were not invented for women. In 1599, they were heavy military combat gear.",
                "master_visual_bible": {
                    "master_subject": "16th-century Persian cavalry warrior in polished leather boots with raised 2-inch block heels",
                    "environment": "High-altitude desert combat terrain, dusty warm sunlight, clear sky",
                    "color_palette": "Deep saddle brown, burnished bronze, warm terracotta sand, clean studio lighting"
                },
                "loop_connection": "The final sentence ends with 'which is why in 1599', looping into 'High heels were not invented...'",
                "scenes": [
                    {
                        "scene_number": 1,
                        "duration_seconds": 5,
                        "narration": "High heels were not invented for women. In 1599, they were heavy military combat gear.",
                        "flux_image_prompt": "3D tactile full-length shot of a 16th-century Persian cavalry warrior mounted on a warhorse, wearing thick leather boots with distinct 2-inch wooden block heels. Clear single focal subject, clean neutral background, warm directional sunlight.",
                        "minimax_motion_prompt": "The horse shifts its weight, causing the warrior's leather boots to plant firmly into the bronze stirrups with rigid balance, fixed static camera frame.",
                        "sfx_cue": "Heavy leather creak and horse hoof thud"
                    },
                    {
                        "scene_number": 2,
                        "duration_seconds": 5,
                        "narration": "Persian archers needed stability to stand up in their horse stirrups while firing arrows.",
                        "flux_image_prompt": "Medium cutaway shot focusing on the warrior's boot heel hooked securely beneath the curved bronze stirrup ring, horse leather flank in background. Clean tactile textures, soft ambient occlusion.",
                        "minimax_motion_prompt": "The thick boot heel locks downward with physical weight, wedging tightly against the bronze stirrup ring with zero slipping, fixed static camera frame.",
                        "sfx_cue": "Metallic stirrup clink and leather strain"
                    },
                    {
                        "scene_number": 3,
                        "duration_seconds": 5,
                        "narration": "Without a raised heel, a rider's foot would slip through, throwing them into the stampede.",
                        "flux_image_prompt": "Anatomical tactile simulation showing a flat-soled leather shoe sliding dangerously forward through a stirrup ring, motion blur lines. Clean studio lighting, uncluttered frame.",
                        "minimax_motion_prompt": "The flat leather sole rapidly slips through the stirrup ring, friction dust particles scattering as it loses grip, fixed static camera frame.",
                        "sfx_cue": "Sharp sliding leather whoosh"
                    },
                    {
                        "scene_number": 4,
                        "duration_seconds": 5,
                        "narration": "When Persian diplomats visited Europe, aristocratic kings adopted the shoes to appear taller and formidable.",
                        "flux_image_prompt": "Stylized 3D render of King Louis XIV in ornate royal court attire wearing red-lacquered wooden high heels on polished marble floor. Single focal subject, elegant palace rim lighting.",
                        "minimax_motion_prompt": "The King's red-heeled shoe strikes down firmly on the polished marble floor, volumetric dust motes swirling in light beams, fixed static camera frame.",
                        "sfx_cue": "Sharp resonant heel tap on marble"
                    },
                    {
                        "scene_number": 5,
                        "duration_seconds": 5,
                        "narration": "It took two centuries of male combat fashion before heels ever shifted to women, which is why...",
                        "flux_image_prompt": "Wide split composition comparing a rugged Persian combat boot side-by-side with a modern high-heel shoe, showcasing the identical arch angle. Clean studio backdrop, high contrast lighting.",
                        "minimax_motion_prompt": "Both shoes settle simultaneously onto the flat pedestal, a subtle puff of air dispersing between them, fixed static camera frame.",
                        "sfx_cue": "Deep sub-bass impact with sharp cut"
                    }
                ]
            }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    sg = ScriptGenerator()
    test_script = sg.generate_script("What Happens If You Swallow a Needle?", channel_handle="@Newyrr")
    print("Title:", test_script["title"])
    print("Master Subject:", test_script.get("master_visual_bible", {}).get("master_subject"))
    print("Scene 1 Narration:", test_script["scenes"][0]["narration"])
    print("Scene 1 Image Prompt:", test_script["scenes"][0]["flux_image_prompt"])
    print("Scene 1 Motion Prompt:", test_script["scenes"][0]["minimax_motion_prompt"])
