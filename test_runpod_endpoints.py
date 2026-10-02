import requests
import json
from config import Config

api_key = Config.RUNPOD_API_KEY
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

def test_chatterbox():
    print("Testing RunPod Chatterbox TTS (xu98042j0lmcdl)...")
    url = "https://api.runpod.ai/v2/xu98042j0lmcdl/runsync"
    payload = {"input": {"prompt": "Your skin is not holding your tattoo ink."}}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=45)
        print("Chatterbox status code:", res.status_code)
        print("Chatterbox response snippet:", json.dumps(res.json(), indent=2)[:500])
    except Exception as e:
        print("Chatterbox test exception:", e)

def test_flux_krea():
    print("\nTesting RunPod Flux Krea (e1s3ntmcuotb7y)...")
    url = "https://api.runpod.ai/v2/e1s3ntmcuotb7y/runsync"
    payload = {"input": {"prompt": "cinematic macro shot of glowing tattoo ink in human skin, 9:16 vertical"}}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        print("Flux Krea status code:", res.status_code)
        print("Flux Krea response snippet:", json.dumps(res.json(), indent=2)[:500])
    except Exception as e:
        print("Flux Krea test exception:", e)

if __name__ == "__main__":
    test_chatterbox()
    test_flux_krea()
