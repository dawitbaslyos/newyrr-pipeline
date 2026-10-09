import json
import os
import re
import requests
from typing import Dict, Any, Optional
from config import Config
from youtube_analytics import YouTubeAnalyticsManager
from jev_decision_engine import jev_engine

# ─────────────────────────────────────────────────────────────────────────────
# THE POV ESCALATOR & FOCAL-POINT STORYTELLING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are an elite cinematic director and master short-form screenwriter for the channel {channel_handle} ('{channel_niche}').

{archetype_directive}

{analytics_context}

## CURRENT ART STYLE DIRECTIVE:
{art_style_directive}

---

## CORE ARCHITECTURAL LAWS (NON-NEGOTIABLE):

### 1. THE POV ESCALATOR STORYTELLING ENGINE (5-LEVEL STAKES LADDER):
Every script consists of EXACTLY 5 progressive scenes (25–30 seconds total, 12–16 spoken words per scene, ~75 words total).
Do NOT write third-person Wikipedia summaries. You MUST use active immersion and ratchet up the stakes beat-by-beat:

- **Scene 1 (The Role & The High-Stakes Hook, 0–5s | Level 1: The Setup)**:
  * IMMERSIVE HOOK: Force second-person POV or immediate sensory role assignment.
    - For bodily/mechanics/fashion: "When you get stitches...", "When you swallow a needle...", "In 1850, women crushed their ribs..."
    - For human drama/wild stories: "Imagine you have magic glasses that predict roulette...", "If an influencer asks you for five dollars on the street, don't answer...", "You are trapped in a cave with three inches of air..."
  * Establish what is immediately at risk or the shocking human paradox in sentence 1.
  * **STRICT PROHIBITION**: NEVER use greetings ("Hey guys"), rhetorical questions ("Have you ever wondered?"), exclamation marks, childish nicknames, or preachy hygiene/life advice.

- **Scene 2 (Ground Reality & First Friction, 5–11s | Level 2: First Friction)**:
  * The initial mechanism or action begins. The first sign of physical tension or suspicion surfaces.
  * Connect seamlessly with causal words ("At first, nobody notices, but as...", "As the needle pulls tight...").

- **Scene 3 (The Stakes Escalator Spike, 11–18s | Level 3: Pressure Doubles)**:
  * The pressure doubles. The unseen physiological cascade, surveillance clampdown, or human crisis escalates.
  * The situation starts spiraling out of ordinary control ("Now the eye in the sky locks onto you...", "White blood cells immediately flood the torn tissue...").

- **Scene 4 (The Breaking Point, 18–24s | Level 4: Point of No Return)**:
  * Peak tension. Maximum friction or dilemma. The casino crowd mobs the table, the physical threshold breaks, or security intervenes.

- **Scene 5 (The Climax & The 'Cherry on Top' Payoff, 24–30s | Level 5: The Dopamine Payoff)**:
  * The unbelievable twist, paradoxical revelation, or ironic resolution that rewards the viewer.
  * **Infinite Loop Requirement**: The final sentence MUST end on a grammatical bridge that flows seamlessly back into the very first word of Scene 1.

### 2. NARRATOR VOICE & TONE:
* Zero preachy advice. NEVER write "Remember to...", "Be sure to clean...", "Always make sure...", or moralistic lectures.
* Zero exclamation marks.
* Cold, relentless, intelligent, authoritative delivery (150–200 WPM cadence).

### 3. CINEMATOGRAPHY & STORYBOARDING BLUEPRINT:
You are not just writing text; you are the **Director of Photography** and **Lead Storyboard Artist**.
DO NOT generate repetitive extreme macro close-ups for every scene!
A watchable, viral Short tells a dynamic story through intentional shot progression:

- **Scene 1 (The Hook & Establishing World - Medium or Wide-Medium Shot)**:
  * MUST establish the **Main Character or Protagonist** in their authentic atmospheric environment or dilemma.
  * Example: If the video is about medieval teeth cleaning, Scene 1 MUST show a grubby medieval peasant sitting on a rustic bench in a candlelit apothecary, clutching his jaw in agony with relatable facial expression.
  * Instantly connects with human curiosity, humor, and world-building.

- **Scene 2 (The Apparatus / Inciting Encounter - Medium Close-Up)**:
  * Frames the character interacting with, or recoiling from, the bizarre tool, object, or antagonist (e.g. the grim barber-surgeon presenting a rusted iron scraper).

- **Scene 3 (The Friction / Tactical Macro - Close-Up / Macro)**:
  * NOW zoom into the intense tactile friction, contact, or scientific mechanism (the rusted iron tool scraping yellowed calcified enamel, or acidic bubbles dissolving bone).

- **Scene 4 (The Reaction / Breaking Point - Medium Dynamic Reaction)**:
  * Captures the character's visceral reaction, comedic shock, or catastrophic material failure.

- **Scene 5+ (The Climax & Seamless Loop - Medium / Wide Resolution)**:
  * Delivers the surprising conclusion or ironic twist, cleanly framing the resolution and setting up the infinite grammatical loop!

### 4. THE SINGLE-SUBJECT / SINGLE-REALITY LAW (MANDATORY CONTINUITY):
- **Master Protagonist & World Lock**: Scene 1 establishes the **Master Visual Anchor** (the exact recurring character, physical features, hair, wardrobe, and atmospheric setting).
- **Absolute Style & Identity Stability**: In Scenes 2 to N, you MUST PRESERVE the exact same character and world!
  * NEVER mutate between visual styles mid-video (e.g. do NOT morph from 3D CGI Unreal render into a 2D Pixar cartoon or medical stock X-ray void).
  * If the video explains bodily mechanics (e.g. knuckle cracking, stitches, swallowing), maintain the SAME protagonist in the SAME room performing the action, reacting, or receiving the procedure.
- **Continuity Prompt Anchor Formula (Scenes 2 to N)**:
  Every `flux_image_prompt` for Scene 2, 3, 4, etc. MUST explicitly begin with:
  `"Featuring the same character ({{master_subject}}) in {{environment}}: [shot type and starting pose/interaction], clean 9:16 vertical composition..."`

### 5. KEYFRAME PROMPT ARCHITECTURE ('flux_image_prompt'):
- **The Storyboard Opening Rule**: This image prompt is the **STARTING POSE (at t=0)** of the shot.
- It must be a poised, beautifully composed still frame that the video AI model can effortlessly animate.
- **BANNED IN STILLS**: NEVER describe mid-air frozen motion blur, flying debris frozen in time, disembodied floating objects without an actor, text overlays, subtitles, or split-screens.
- Focus on ONE clear action/interaction at a time with clean composition and strong character readability.
- **Pacing & Length**: Keep each image prompt concise, precise, and punchy (25–40 words following the formula: shot type + character in starting pose + setting + lighting). Do NOT write bloated paragraphs.

### 6. MOTION GUIDANCE ('minimax_motion_prompt'):
- This prompt acts as the **Video Animator & Director**. It tells the video model what physical kinetics begin to unfold FROM the starting keyframe.
- **Formula**: `[Character / Subject] [performs specific kinetic movement, changes facial expression, or operates object], [environmental reaction or subtle camera tracking], cinematic motion momentum.`
- **STRICT PROHIBITION**: NEVER include timestamps ("At 0.00 seconds", "[00:15]") or static freezes.

### 7. DYNAMIC SCENE PACING:
- Tailor the scene count (typically **4 to 7 scenes**) to match the narrative tension and escalation.
- Target short total runtime: 30 to 55 seconds.

### 8. STRICT JSON HYGIENE (CRITICAL):
- Never insert unescaped double quotes inside strings. Always use single quotes ('like this') if you must quote a term.
- Never include unescaped raw newlines inside string values.

---

You MUST output ONLY valid JSON matching this exact schema:
{{
  "title": "5-7 word compelling title with one relevant emoji",
  "hook": "Opening hook line from Scene 1",
  "master_visual_bible": {{
    "master_subject": "Precise description of the recurring character/protagonist, physical appearance, and clothing",
    "environment": "Unified atmospheric setting across scenes",
    "color_palette": "Specific color harmony and cinematic lighting tone"
  }},
  "loop_connection": "Explanation of how the final scene grammatically bridges back to Scene 1",
  "scenes": [
    {{
      "scene_number": 1,
      "escalation_level": "Level 1: The Setup & Immersion Hook",
      "shot_type": "Medium Establishing Shot",
      "focal_point": "Character in starting pose within environment",
      "duration_seconds": 5,
      "narration": "12-16 words of immersive second-person or visceral hook narration",
      "flux_image_prompt": "Medium shot of [Character in starting pose] in [Atmospheric setting], [Lighting]. Clean 9:16 vertical composition...",
      "minimax_motion_prompt": "The character [performs starting kinetic movement / expresses emotion], cinematic motion...",
      "sfx_cue": "Specific tactile sound design cue"
    }},
    {{
      "scene_number": 2,
      "escalation_level": "Level 2: Ground Reality & First Friction",
      "shot_type": "Medium Close-Up",
      "focal_point": "Character interacting with tool/apparatus",
      "duration_seconds": 5,
      "narration": "12-16 words introducing the bizarre mechanism or apparatus",
      "flux_image_prompt": "Medium close-up maintaining [Character] interacting with [Tool/Apparatus]...",
      "minimax_motion_prompt": "Character kinetic interaction with tool, fixed cinematic frame...",
      "sfx_cue": "Specific tactile sound design cue"
    }},
    {{
      "scene_number": 3,
      "escalation_level": "Level 3: The Stakes Escalator Spike",
      "shot_type": "Close-Up / Tactical Macro",
      "focal_point": "Tactile friction or mechanism point",
      "duration_seconds": 5,
      "narration": "12-16 words on the escalating physical friction or reaction",
      "flux_image_prompt": "Tactile close-up isolating the physical friction point...",
      "minimax_motion_prompt": "Physical kinetic reaction and deformation, cinematic motion...",
      "sfx_cue": "Specific tactile sound design cue"
    }},
    {{
      "scene_number": 4,
      "escalation_level": "Level 4: The Breaking Point",
      "shot_type": "Medium Dynamic Reaction",
      "focal_point": "Character reaction or catastrophic threshold",
      "duration_seconds": 5,
      "narration": "12-16 words on the breaking point or dramatic reaction",
      "flux_image_prompt": "Medium dynamic shot of [Character] in shock/reaction...",
      "minimax_motion_prompt": "Dynamic physical reaction and recoil, cinematic frame...",
      "sfx_cue": "Specific tactile sound design cue"
    }},
    {{
      "scene_number": 5,
      "escalation_level": "Level 5: The Dopamine Payoff",
      "shot_type": "Medium Punchline / Loop",
      "focal_point": "Final resolution framing",
      "duration_seconds": 5,
      "narration": "12-16 words revealing the paradoxical twist and ending on the loop bridge",
      "flux_image_prompt": "Final resolution framing of [Character] in environment...",
      "minimax_motion_prompt": "Final physical momentum completing the loop, cinematic motion...",
      "sfx_cue": "Specific tactile sound design cue"
    }}
  ]
}}
"""

ARCHETYPE_DIRECTIVES = {
    "tactile_origins": """## CHANNEL PERSONA: TACTILE ORIGINS & ANATOMY (@Newyrr Standard)
You are directing high-end tactile 3D anatomical, medical, and historical origin breakdowns in the benchmark caliber of @zackdfilms and @simplihowww.
- Narrative Hook: Visceral bodily or mechanical immersion ("When you get stitches...", "When a doctor drives a needle...", "When your skin touches...").
- Pacing: Clinical precision, physical cause-and-effect, 5-beat causal progression.
- Visuals: Stylized 3D tactile simulations, single macro focal points, clean cross-sections, soft ambient lighting, zero visual clutter.""",

    "human_drama": """## CHANNEL PERSONA: EXTRAORDINARY HUMAN STORIES (@internetChill Standard)
You are directing gripping real-life human interest stories and bizarre true events in the benchmark caliber of @LoadedDiceShorts, @afrimaxenglish, and @wholesomewendy.
- Narrative Hook: Second-person scenario immersion ("Imagine you have magic glasses...", "If an influencer stops you on the street...", "You are trapped in...").
- Pacing: The Stakes Escalator (Level 1 Setup -> Level 2 Suspicion -> Level 3 Surveillance/Crisis Spike -> Level 4 Dilemma -> Level 5 Cherry on Top Payoff).
- Visuals: Stylized 3D machinima / cinematic 35mm film stills, high-contrast atmospheric lighting, expressive character gestures, direct narrative visual synchrony.""",

    "badass_cinema": """## CHANNEL PERSONA: BADASS CINEMA MOMENTS (@MainQuestCC Standard)
You are directing high-octane cinematic scene breakdowns and badass character showdowns.
- Narrative Hook: High-stakes confrontation or calculated psychological masterclass.
- Pacing: Tight, tension-building, calculated dialogue cues.
- Visuals: Cinematic anamorphic film stills, moody chiaroscuro lighting, razor-sharp focus on expressions and tactical gear."""
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
        channel_niche: Optional[str] = None,
        reference_url: Optional[str] = None
    ) -> Dict[str, Any]:
        handle = channel_handle or "@Newyrr"
        niche = channel_niche or "How-to and origins of the human body, fashion, lifestyle, and physical mechanics."
        archetype_key = self._determine_archetype(handle, niche)
        archetype_directive = ARCHETYPE_DIRECTIVES.get(archetype_key, ARCHETYPE_DIRECTIVES["tactile_origins"])

        # Fetch performance intelligence
        analytics_context = self.analytics.get_prompt_context(handle)
        comp_context = ""
        try:
            from competitor_tracker import competitor_tracker
            from channel_manager import channel_mgr
            tracked = channel_mgr.get_data().get("tracked_channels", [])
            comp_context = competitor_tracker.get_competitor_context_for_llm(tracked)
            full_context = f"{analytics_context}\n\n{comp_context}"
        except Exception:
            full_context = analytics_context

        # Call Jev System-1 Decision Engine for sub-second topic analysis and pacing
        jev_meta = {}
        try:
            jev_meta = jev_engine.evaluate_topic_and_pacing(topic, comp_context)
            print(f"[Script Generator] Jev System-1 Decision: Archetype={jev_meta.get('recommended_archetype')}, Scenes={jev_meta.get('recommended_scene_count')}, WPM={jev_meta.get('target_wpm')}, Score={jev_meta.get('virality_score')}")
        except Exception as ex:
            print(f"[Script Generator] Jev Decision Engine bypassed: {ex}")

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

        ref_context = ""
        if reference_url:
            try:
                from transcript_service import transcript_service
                ref_data = transcript_service.ingest_reference(reference_url)
                bp = ref_data.get("blueprint", {})
                ref_meta = ref_data.get("metadata", {})
                ref_context = (
                    f"\n\n## PROVEN VIRAL REFERENCE BLUEPRINT:\n"
                    f"Model the pacing, cadence, and sentence lengths of your new script directly after this viral hit:\n"
                    f"- Reference Video: '{ref_meta.get('title')}'\n"
                    f"- Target Word Count: ~{bp.get('word_count')} words\n"
                    f"- Target Cadence: ~{bp.get('wpm')} WPM\n"
                    f"- Perspective Structure: {bp.get('pov_type')}\n"
                    f"- Reference Verbatim Transcript for Cadence Alignment:\n"
                    f"\"{ref_data.get('transcript', '')}\"\n"
                    f"Match this exact escalation tempo and sentence rhythm while writing about the new topic: '{topic}'."
                )
            except Exception as e:
                print(f"[Script Generator] Reference ingest warning: {e}")

        scene_count = jev_meta.get("recommended_scene_count", 5) if jev_meta else 5
        target_wpm = jev_meta.get("target_wpm", 180) if jev_meta else 180
        hook_angle = jev_meta.get("hook_angle", "Visceral role or bodily stakes immersion") if jev_meta else "Visceral role or bodily stakes immersion"

        jev_brief = (
            f"\n\n## JEV SYSTEM-1 DIRECTIVES:\n"
            f"- Recommended Scene Count: {scene_count} scenes (scale narrative escalation smoothly across {scene_count} scenes)\n"
            f"- Target Spoken Cadence: {target_wpm} WPM (~12-16 words per scene)\n"
            f"- Strategic Hook Angle: {hook_angle}\n"
        )

        user_prompt = (
            f"Produce an elite {scene_count}-scene viral Short for this topic: '{topic}'.\n"
            f"Enforce the POV Escalator stakes ladder, Single-Subject / Single-Reality Law (Scene 1 defines protagonist and setting; Scenes 2-{scene_count} preserve them identically), "
            f"and uncluttered 9:16 vertical composition.{jev_brief}{ref_context}"
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
            "max_tokens": 8192,
            "response_format": {"type": "json_object"}
        }

        # Claude 5.5 / 4.5 are prioritary master directors
        preferred_model = self.model or getattr(Config, "OPENROUTER_MODEL", "anthropic/claude-sonnet-5.5")
        models_to_try = [
            preferred_model,
            "anthropic/claude-sonnet-5.5",
            "anthropic/claude-opus-5.5",
            "anthropic/claude-haiku-5.5",
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-4o-mini",
            "google/gemini-2.5-flash"
        ]
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
                        timeout=90
                    )

                    if res.status_code == 200:
                        data = res.json()
                        choices = data.get("choices", [])
                        if not choices:
                            continue
                        content = choices[0].get("message", {}).get("content")
                        if not content:
                            continue

                        cleaned = content.strip()
                        if cleaned.startswith("```json"):
                            cleaned = cleaned[7:]
                        elif cleaned.startswith("```"):
                            cleaned = cleaned[3:]
                        if cleaned.endswith("```"):
                            cleaned = cleaned[:-3]
                        cleaned = cleaned.strip()

                        s_idx = cleaned.find("{")
                        e_idx = cleaned.rfind("}")
                        if s_idx != -1 and e_idx != -1:
                            cleaned = cleaned[s_idx:e_idx+1]

                        try:
                            script_data = json.loads(cleaned, strict=False)
                        except Exception:
                            try:
                                import dirtyjson
                                script_data = dict(dirtyjson.loads(cleaned))
                                if "scenes" in script_data:
                                    script_data["scenes"] = [dict(s) for s in script_data["scenes"]]
                                if "master_visual_bible" in script_data:
                                    script_data["master_visual_bible"] = dict(script_data["master_visual_bible"])
                            except Exception:
                                # Attempt repair of unescaped quotes or trailing commas
                                repaired = re.sub(r',\s*([\]}])', r'\1', cleaned)
                                try:
                                    script_data = json.loads(repaired, strict=False)
                                except Exception:
                                    repaired2 = re.sub(r'[\r\n\t]+', ' ', repaired)
                                    script_data = json.loads(repaired2, strict=False)

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

        master_bible = script_data.get("master_visual_bible", {})
        master_subject = master_bible.get("master_subject", "").strip()
        master_env = master_bible.get("environment", "").strip()

        for idx, scene in enumerate(script_data.get("scenes", [])):
            # 1. Clean Keyframe Image Prompt
            f_prompt = scene.get("flux_image_prompt", "")
            for phrase in forbidden_image_phrases:
                f_prompt = f_prompt.replace(phrase, "").strip()
            # Clean leading lowercase or punctuation
            f_prompt = re.sub(r'^[,.\s]+', '', f_prompt)
            if f_prompt and f_prompt[0].islower():
                f_prompt = f_prompt[0].upper() + f_prompt[1:]

            # 1b. Single-Subject / Continuity Enforcement for Scenes 2 to N
            if idx > 0 and master_subject:
                lower_p = f_prompt.lower()
                # Check if prompt already establishes protagonist continuity
                if "same character" not in lower_p and "same protagonist" not in lower_p and master_subject.lower()[:15] not in lower_p:
                    f_prompt = f"Featuring the same character ({master_subject}) in {master_env}: {f_prompt}"

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

        # Jev System-1 QC Continuity Gatekeeper & Auto-Healer
        if master_subject:
            try:
                continuity_result = jev_engine.verify_continuity_gate(master_bible, script_data.get("scenes", []))
                script_data["continuity_qc"] = continuity_result
                print(f"[Script Generator] Jev Continuity Gate Result: {continuity_result.get('continuity_passed')} (flagged: {continuity_result.get('flagged_scenes')})")

                # If Jev flagged any scene for continuity deviation, auto-heal its prompt
                flagged = continuity_result.get("flagged_scenes", [])
                if flagged and not continuity_result.get("continuity_passed"):
                    for s_num in flagged:
                        for sc in script_data.get("scenes", []):
                            if sc.get("scene_number") == s_num:
                                orig = sc.get("flux_image_prompt", "")
                                # Ensure prompt strictly re-anchors the protagonist and room without genre shifting
                                if "same character" not in orig.lower():
                                    sc["flux_image_prompt"] = (
                                        f"Featuring the same character ({master_subject}) in {master_env}, "
                                        f"maintaining strict single-reality visual continuity: {orig}"
                                    )
                                    print(f"[Script Generator] Jev Auto-Healed Scene {s_num} for continuity.")
            except Exception as e:
                print(f"[Script Generator] Continuity QC check bypassed: {e}")

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
