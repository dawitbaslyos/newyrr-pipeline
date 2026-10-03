import os
import json
import base64
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw
from config import Config

class ImageGenerator:
    """
    Pure-Cloud Multi-Model Image Generator:
    - Krea 2 Medium Turbo (openrouter.ai/api/v1/images)
    - Nano Banana 2 (google/gemini-3.1-flash-image via chat/completions)
    - Replicate & RunPod compatible
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or Config.IMAGE_PROVIDER or "openrouter"
        self.openrouter_key = Config.OPENROUTER_API_KEY
        self.replicate_token = Config.REPLICATE_API_TOKEN
        self.runpod_key = Config.RUNPOD_API_KEY
        self.runpod_endpoint = Config.RUNPOD_FLUX_ENDPOINT_ID

    def generate_image(
        self,
        prompt: str,
        output_path: str,
        width: int = 768,
        height: int = 1344,
        aspect_ratio: str = "9:16",
        seed: Optional[int] = None
    ) -> str:
        output_path = str(Path(output_path).resolve())
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        model = Config.ACTIVE_IMAGE_MODEL or Config.OPENROUTER_IMAGE_MODEL or "krea/krea-2-medium-turbo"

        # 1. OpenRouter (Krea 2 Turbo or Nano Banana)
        if self.openrouter_key:
            try:
                img_path = self._generate_openrouter(prompt, output_path, model, aspect_ratio)
                if img_path and os.path.exists(img_path):
                    return img_path
            except Exception as e:
                print(f"[Image Generator] OpenRouter image error ({model}): {e}")
                # Propagate key limit or quota errors directly
                if "spending limit reached" in str(e).lower() or "key limit exceeded" in str(e).lower() or "403" in str(e):
                    raise e
                last_err = e

        # 2. Replicate (if configured)
        if self.replicate_token:
            try:
                img_path = self._generate_replicate(prompt, output_path, width, height)
                if img_path and os.path.exists(img_path):
                    return img_path
            except Exception as e:
                print(f"[Image Generator] Replicate error: {e}...")
                last_err = e

        # If both fail, raise the real error instead of silently drawing a confusing wireframe
        raise RuntimeError(
            f"Image generation failed for '{prompt[:40]}...': {last_err if 'last_err' in locals() else 'No active image provider'}. "
            "Please verify your API key credits in Settings."
        )

    def _generate_openrouter(self, prompt: str, output_path: str, model: str, aspect_ratio: str = "9:16") -> str:
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://github.com/internetchill/newyrr-pipeline",
            "X-Title": "Newyrr Studio",
            "Content-Type": "application/json"
        }

        # A. Krea 2 Turbo & Native Image Models (via /api/v1/images)
        if "krea" in model.lower() or "dall-e" in model.lower() or "imagen" in model.lower() and not "gemini" in model.lower():
            final_prompt = prompt
            if not prompt.strip().startswith("Style:"):
                art_key = getattr(Config, "ACTIVE_ART_STYLE", "photo_35mm")
                clio_info = getattr(Config, "CLIO_STYLES", {}).get(art_key)
                if clio_info:
                    final_prompt = f"Style: {clio_info['name']}: {clio_info['prompt']}. Subject: {prompt}"

            payload = {
                "model": model,
                "prompt": final_prompt,
                "aspect_ratio": aspect_ratio
            }
            print(f"[Image Generator] Calling OpenRouter /images ({model}) for: '{prompt[:45]}...'")
            res = requests.post("https://openrouter.ai/api/v1/images", headers=headers, json=payload, timeout=45)
            if res.status_code == 403 and "Key limit exceeded" in res.text:
                raise RuntimeError(
                    "OpenRouter API Key spending limit reached ($1.00 cap). "
                    "Please raise or remove the limit in your OpenRouter Dashboard (https://openrouter.ai/settings/keys) to continue generating images."
                )
            if res.status_code == 200:
                data = res.json()
                items = data.get("data", [])
                if items:
                    item = items[0]
                    b64 = item.get("b64_json")
                    if b64:
                        with open(output_path, "wb") as f:
                            f.write(base64.b64decode(b64))
                        print(f"[Image Generator] Saved Krea image: {output_path}")
                        return output_path
                    elif item.get("url"):
                        u_res = requests.get(item["url"], timeout=30)
                        with open(output_path, "wb") as f:
                            f.write(u_res.content)
                        return output_path
            else:
                print(f"[Image Generator] /images returned status {res.status_code}: {res.text[:120]}")

        # B. Gemini / Nano Banana (via chat/completions)
        enriched_prompt = (
            f"Generate a cinematic, high-resolution vertical {aspect_ratio} photograph. "
            f"Professional cinematography, Hasselblad macro lens, 8k photorealistic textures: {prompt}"
        )
        payload = {
            "model": model if "gemini" in model.lower() else "google/gemini-3.1-flash-image",
            "messages": [{"role": "user", "content": enriched_prompt}]
        }

        print(f"[Image Generator] Calling OpenRouter chat ({payload['model']}) for: '{prompt[:45]}...'")
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=45)
        if res.status_code == 403 and "Key limit exceeded" in res.text:
            raise RuntimeError(
                "OpenRouter API Key spending limit reached ($1.00 cap). "
                "Please raise or remove the limit in your OpenRouter Dashboard (https://openrouter.ai/settings/keys) to continue generating images."
            )
        if res.status_code == 200:
            data = res.json()
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                images = msg.get("images", [])
                if images and isinstance(images, list):
                    url_val = images[0].get("image_url", {}).get("url", "")
                    if url_val.startswith("data:image"):
                        b64_data = url_val.split(",")[-1]
                        with open(output_path, "wb") as f:
                            f.write(base64.b64decode(b64_data))
                        print(f"[Image Generator] Saved image: {output_path}")
                        return output_path

        raise RuntimeError(f"OpenRouter image generation failed for model {model}")

    def _generate_replicate(self, prompt: str, output_path: str, width: int = 768, height: int = 1344) -> str:
        headers = {
            "Authorization": f"Bearer {self.replicate_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "version": "black-forest-labs/flux-schnell",
            "input": {"prompt": prompt, "aspect_ratio": "9:16", "output_format": "png"}
        }
        res = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload, timeout=30)
        data = res.json()
        pred_id = data.get("id")
        if not pred_id:
            raise RuntimeError(f"Replicate start failed: {data}")

        for _ in range(20):
            time.sleep(1.5)
            chk = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers, timeout=15).json()
            if chk.get("status") == "succeeded":
                img_url = chk.get("output", [None])[0]
                img_bytes = requests.get(img_url, timeout=30).content
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                return output_path
            elif chk.get("status") in ["failed", "canceled"]:
                raise RuntimeError(f"Replicate job failed: {chk.get('error')}")

        raise TimeoutError("Replicate timed out.")

    def _generate_local_fallback(self, prompt: str, output_path: str, width: int = 768, height: int = 1344) -> str:
        img = Image.new("RGB", (width, height), color=(15, 20, 30))
        draw = ImageDraw.Draw(img)
        for y in range(height):
            c = int(15 + (y / height) * 30)
            draw.line([(0, y), (width, y)], fill=(c, c + 5, c + 20))
        draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(14, 165, 233), width=3)
        draw.text((40, height // 3), f"[KEYFRAME]\n{prompt[:90]}...", fill=(240, 245, 255))
        img.save(output_path)
        return output_path

# Alias for backwards compatibility
FluxRunPodClient = ImageGenerator
