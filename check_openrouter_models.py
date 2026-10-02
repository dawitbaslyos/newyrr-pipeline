import requests
from config import Config

def check_models():
    url = "https://openrouter.ai/api/v1/models"
    headers = {"Authorization": f"Bearer {Config.OPENROUTER_API_KEY}"}
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code == 200:
        models = [m["id"] for m in res.json().get("data", [])]
        print(f"Total models available: {len(models)}")
        # Look for claude-3, gpt-4o, deepseek
        candidates = [m for m in models if "claude-3" in m or "deepseek" in m or "gpt-4o" in m]
        print("Sample matching models on OpenRouter:")
        for c in candidates[:15]:
            print("-", c)
    else:
        print("Error fetching models:", res.text)

if __name__ == "__main__":
    check_models()
