import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")
with open("data/sfx_catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

cat_summary = [
    {"id": k, "category": v["category"], "desc": v["description"], "peak_offset_ms": v["peak_offset_ms"]}
    for k, v in catalog.items()
]

system_prompt = """You are an expert Hollywood/TikTok sound designer for high-retention viral YouTube Shorts.
You place sound effects with millisecond precision to maximize viewer dopamine without cluttering the narration.

RULES:
1. Scene 1 always gets an impact at target_timestamp 0.0s (Hook punch).
2. Each subsequent scene cut (start of scene 2, 3, etc.) gets a whoosh transition at the exact cut timestamp.
3. Max 1 subtle accent/pop/ding/riser per scene, placed at the EXACT timestamp of the catalyst word or visual action.
4. Volumes: impact=0.35, whoosh=0.25, accent=0.28.
5. Return JSON format:
{
  "placements": [
    {
      "scene_number": 1,
      "sfx_id": "impact_sub_drop",
      "target_timestamp": 0.0,
      "trigger_reason": "Hook punch to grab attention",
      "volume": 0.35
    }
  ]
}
"""

user_prompt = f"""Available SFX Library:
{json.dumps(cat_summary, indent=2)}

Project: Why Vinegar Dissolves Eggshells
Scenes:
- Scene 1 (0.0s to 5.36s): 'Eggshell armor waits under vinegar, a chalky calcium carbonate shield.'
- Scene 2 (5.36s to 12.20s): 'Acetic acid attacks calcium carbonate, stealing its solid grip, molecule by molecule.' (Catalyst: 'attacks' at 6.1s)
- Scene 3 (12.20s to 17.60s): 'Carbon dioxide bubbles burst upward, lifting chalky dust into the vinegar.' (Catalyst: 'bubbles burst' at 13.5s)
- Scene 4 (17.60s to 22.44s): 'The shell softens, thins, and exposes the raw egg beneath.' (Catalyst: 'thins' at 18.9s)
- Scene 5 (22.44s to 29.08s): 'So vinegar doesn't boil it—it eats the armor, leaving a quiet eggshell.' (Catalyst: 'eats' at 24.8s)

Select the best sound effects and timestamps.
"""

payload = {
    "model": "typesafe/jev-router",
    "response_format": {"type": "json_object"},
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json=payload,
    timeout=30
)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    res = response.json()
    content = res["choices"][0]["message"]["content"]
    print("JEV Response:")
    print(content)
else:
    print(response.text)
