import requests
import json
from config import Config

api_key = Config.RUNPOD_API_KEY
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

def test_minimax_endpoint():
    print("Testing RunPod MiniMax H3 Max Turbo (ucla82uhwqfvd8)...")
    url = "https://api.runpod.ai/v2/ucla82uhwqfvd8/health"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        print("Health status code:", res.status_code)
        print("Health response:", res.text)
    except Exception as e:
        print("Health exception:", e)

    # Check status via empty or minimal prompt
    run_url = "https://api.runpod.ai/v2/ucla82uhwqfvd8/run"
    with open("minimax_h3_api.json", "r", encoding="utf-8") as f:
        wf = json.load(f)
    payload = {"input": {"workflow": wf}}
    try:
        res = requests.post(run_url, headers=headers, json=payload, timeout=20)
        print("\nMiniMax run test status code:", res.status_code)
        print("MiniMax run response:", res.text)
    except Exception as e:
        print("MiniMax run exception:", e)

if __name__ == "__main__":
    test_minimax_endpoint()
