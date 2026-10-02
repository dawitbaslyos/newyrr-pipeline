import os
import time
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from config import Config

class OpenRouterVideoClient:
    """
    Client for OpenRouter Video Generation API:
    - bytedance/seedance-2.0-mini ($0.03363/s ~ $0.84/Short)
    - minimax/hailuo-3 ($0.13/s ~ $3.25/Short)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/videos"

    def render_video_i2v(
        self,
        image_path: str,
        motion_prompt: str,
        output_path: str,
        model: str = "bytedance/seedance-2.0-mini",
        duration: int = 5,
        aspect_ratio: str = "9:16",
        resolution: str = "720p"
    ) -> str:
        """
        Dispatches an Image-to-Video generation job to OpenRouter, polls for completion,
        and saves the MP4 video to output_path.
        """
        output_path = str(Path(output_path).resolve())
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Input image not found: {image_path}")

        with open(image_path, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/internetchill/newyrr-pipeline",
            "X-Title": "Newyrr Studio"
        }

        # Seedance 2.0 Mini accepted durations: 4 to 15
        valid_duration = max(4, min(10, int(round(duration))))

        payload = {
            "model": model,
            "prompt": motion_prompt,
            "duration": valid_duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "frame_images": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_image}"
                    },
                    "frame_type": "first_frame"
                }
            ]
        }

        print(f"[OpenRouter Video] Submitting I2V job ({model}) for {os.path.basename(image_path)}: '{motion_prompt[:45]}...'")
        res = requests.post(self.base_url, headers=headers, json=payload, timeout=40)
        
        if res.status_code not in (200, 201, 202):
            raise RuntimeError(f"OpenRouter Video submit failed ({res.status_code}): {res.text}")

        job_data = res.json()
        job_id = job_data.get("id")
        if not job_id:
            raise RuntimeError(f"No job ID in response: {job_data}")

        print(f"[OpenRouter Video] Job accepted: {job_id}. Polling status...")

        # Poll until complete
        poll_url = f"{self.base_url}/{job_id}"
        max_attempts = 35 # ~100-120 seconds
        for attempt in range(max_attempts):
            time.sleep(3.5)
            try:
                chk = requests.get(poll_url, headers=headers, timeout=20)
                if chk.status_code == 200:
                    status_data = chk.json()
                    status = status_data.get("status")
                    if status == "completed":
                        # Check for video download URL
                        urls = status_data.get("unsigned_urls") or []
                        if urls and urls[0]:
                            vid_url = urls[0]
                            dl_res = requests.get(vid_url, timeout=40)
                            with open(output_path, "wb") as f:
                                f.write(dl_res.content)
                            print(f"[OpenRouter Video] Downloaded finished video: {output_path}")
                            return output_path
                        
                        # Alternative content endpoint
                        content_url = f"{poll_url}/content"
                        content_res = requests.get(content_url, headers=headers, timeout=40)
                        if content_res.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(content_res.content)
                            print(f"[OpenRouter Video] Saved video from content API: {output_path}")
                            return output_path
                        
                    elif status in ("failed", "cancelled", "expired"):
                        err_msg = status_data.get("error", "Unknown error")
                        raise RuntimeError(f"OpenRouter Video job {job_id} {status}: {err_msg}")
                    else:
                        print(f"[OpenRouter Video] Job {job_id} status: {status} (attempt {attempt+1}/{max_attempts})")
            except requests.RequestException as e:
                print(f"[OpenRouter Video] Polling check warning: {e}")

        raise TimeoutError(f"OpenRouter Video job {job_id} timed out after {max_attempts * 3.5}s")
