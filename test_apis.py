import os
import requests
from config import Config

def test_openrouter():
    print("Testing OpenRouter API...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [{"role": "user", "content": "Respond with the single word: READY"}],
        "max_tokens": 10
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        print("OpenRouter status code:", res.status_code)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"].strip()
            print("OpenRouter response:", content)
            return True
        else:
            print("OpenRouter error response:", res.text)
            return False
    except Exception as e:
        print("OpenRouter exception:", e)
        return False

def test_youtube():
    print("\nTesting YouTube Data API...")
    url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={Config.YOUTUBE_CHANNEL_ID}&key={Config.YOUTUBE_API_KEY}"
    try:
        res = requests.get(url, timeout=15)
        print("YouTube status code:", res.status_code)
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [])
            if items:
                title = items[0]["snippet"]["title"]
                subs = items[0]["statistics"].get("subscriberCount", "Hidden")
                videos = items[0]["statistics"].get("videoCount", "0")
                print(f"YouTube Channel: {title} | Subs: {subs} | Videos: {videos}")
                return True
            else:
                print("No items returned for channel ID:", Config.YOUTUBE_CHANNEL_ID)
                return False
        else:
            print("YouTube error response:", res.text)
            return False
    except Exception as e:
        print("YouTube exception:", e)
        return False

if __name__ == "__main__":
    test_openrouter()
    test_youtube()
