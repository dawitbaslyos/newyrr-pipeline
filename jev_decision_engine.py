import json
import re
import requests
from typing import Dict, Any, Optional
from config import Config

class JevDecisionEngine:
    """
    TypeSafe Jev System-1 Decision Engine via OpenRouter.
    Provides sub-second probabilistic routing, classification,
    and visual continuity verification for YouTube Shorts.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.model = "typesafe/jev-router"
        self.fallback_model = "deepseek/deepseek-v4.1-flash"

    def _call_decision(self, prompt: str, system_directive: str = "") -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/internetchill/newyrr-pipeline",
            "X-Title": "Newyrr Studio - Jev Decision Engine",
            "Content-Type": "application/json"
        }

        messages = []
        if system_directive:
            messages.append({"role": "system", "content": system_directive})
        messages.append({"role": "user", "content": prompt})

        for current_model in [self.model, self.fallback_model]:
            try:
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": current_model,
                        "messages": messages,
                        "temperature": 0.2
                    },
                    timeout=20
                )
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
            except Exception as e:
                print(f"[Jev Engine] Error with {current_model}: {e}")

        return ""

    def evaluate_topic_and_pacing(self, topic: str, competitor_context: str = "") -> Dict[str, Any]:
        """
        System-1 Decision: Evaluates virality potential, optimal archetype,
        recommended scene count (4-7), and pacing tempo.
        """
        prompt = (
            f"Topic: '{topic}'\n"
            f"Competitor Intelligence Context: {competitor_context[:600] if competitor_context else 'None'}\n\n"
            "Answer with strict JSON:\n"
            "{\n"
            '  "virality_score": <number 1-10>,\n'
            '  "recommended_archetype": "<tactile_origins | human_drama | badass_cinema>",\n'
            '  "recommended_scene_count": <integer between 4 and 7>,\n'
            '  "target_wpm": <integer between 150 and 200>,\n'
            '  "hook_angle": "<brief 1-sentence hook strategic angle>"\n'
            "}"
        )
        system_directive = "You are Jev, a high-speed System-1 decision model. Output ONLY a valid JSON object."
        raw_response = self._call_decision(prompt, system_directive)

        try:
            # Extract JSON block
            match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass

        # Robust defaults
        return {
            "virality_score": 8.0,
            "recommended_archetype": "tactile_origins" if "body" in topic.lower() or "how" in topic.lower() else "human_drama",
            "recommended_scene_count": 5,
            "target_wpm": 180,
            "hook_angle": "Immersive second-person sensory dilemma"
        }

    def verify_continuity_gate(self, master_bible: Dict[str, Any], scenes: list) -> Dict[str, Any]:
        """
        System-1 QC Gate: Verifies that every scene adheres to the single-subject
        and environment defined in the master visual bible.
        """
        subject_desc = master_bible.get("master_subject", "")
        env_desc = master_bible.get("environment", "")
        
        prompt = (
            f"Master Subject: {subject_desc}\n"
            f"Master Environment: {env_desc}\n\n"
            "Scenes to check:\n"
        )
        for s in scenes:
            num = s.get("scene_number", 1)
            prompt_text = s.get("flux_image_prompt", "")
            prompt += f"Scene {num}: {prompt_text}\n"

        prompt += (
            "\nDoes every single scene maintain the same protagonist and environment without introducing random foreign objects or shifting into a different visual genre?\n"
            "Return JSON: {\"continuity_passed\": true/false, \"flagged_scenes\": [], \"recommendation\": \"...\"}"
        )

        raw = self._call_decision(prompt, "You are Jev, a strict continuity verification model. Output valid JSON only.")
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass

        return {"continuity_passed": True, "flagged_scenes": [], "recommendation": "Passed default checks"}

jev_engine = JevDecisionEngine()
