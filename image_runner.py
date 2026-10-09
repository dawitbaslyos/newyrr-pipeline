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

    def _prepare_reference_image(self, ref_path: Optional[str]) -> Optional[str]:
        """
        Loads reference image from disk, scales it down to max 768px,
        compresses as JPEG (quality 80) to keep payload ~50KB, and returns data URI.
        """
        if not ref_path:
            return None
        try:
            p = Path(ref_path)
            if not p.exists() or not p.is_file():
                return None
            import io
            with Image.open(p) as img:
                img = img.convert("RGB")
                img.thumbnail((768, 768))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=80)
                b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
                return f"data:image/jpeg;base64,{b64_img}"
        except Exception as e:
            print(f"[Image Generator] Warning: Failed to prepare reference image {ref_path}: {e}")
            return None

    def generate_image(
        self,
        prompt: str,
        output_path: str,
        width: int = 768,
        height: int = 1344,
        aspect_ratio: str = "9:16",
        seed: Optional[int] = None,
        art_style: Optional[str] = None,
        reference_image: Optional[str] = None
    ) -> str:
        output_path = str(Path(output_path).resolve())
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        model = Config.ACTIVE_IMAGE_MODEL or Config.OPENROUTER_IMAGE_MODEL or "krea/krea-2-medium-turbo"

        # 1. OpenRouter (Krea 2 Turbo or Nano Banana)
        if self.openrouter_key:
            try:
                img_path = self._generate_openrouter(
                    prompt=prompt,
                    output_path=output_path,
                    model=model,
                    aspect_ratio=aspect_ratio,
                    art_style=art_style,
                    reference_image=reference_image
                )
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
                img_path = self._generate_replicate(
                    prompt=prompt,
                    output_path=output_path,
                    width=width,
                    height=height,
                    aspect_ratio=aspect_ratio,
                    art_style=art_style,
                    reference_image=reference_image
                )
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

    def _generate_openrouter(
        self,
        prompt: str,
        output_path: str,
        model: str,
        aspect_ratio: str = "9:16",
        art_style: Optional[str] = None,
        reference_image: Optional[str] = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://github.com/internetchill/newyrr-pipeline",
            "X-Title": "Newyrr Studio",
            "Content-Type": "application/json"
        }

        # Resolve active art style details from clio_styles
        art_key = art_style or getattr(Config, "ACTIVE_ART_STYLE", "photo_35mm")
        clio_info = getattr(Config, "CLIO_STYLES", {}).get(art_key)
        style_prompt = clio_info.get("prompt", "") if clio_info else ""

        # Prepare reference image data URI if provided
        ref_data_uri = self._prepare_reference_image(reference_image) if reference_image else None

        # Candidate models: requested model first, then automatic fallback to Gemini flash image
        models_to_try = [model]
        fallback_model = "google/gemini-2.5-flash-image"
        if fallback_model not in models_to_try and "gemini" not in model.lower():
            models_to_try.append(fallback_model)

        last_error = None
        for current_model in models_to_try:
            is_native_images_api = (
                "krea" in current_model.lower() or
                "dall-e" in current_model.lower() or
                ("imagen" in current_model.lower() and "gemini" not in current_model.lower())
            )

            # Retry up to 2 attempts per model with backoff
            for attempt in range(1, 3):
                try:
                    if is_native_images_api:
                        raw_prompt = prompt.strip()
                        # Enrich prompt with selected Art Style and ensure rich environmental backgrounds
                        if style_prompt and not any(k in raw_prompt.lower() for k in ["art style:", "aesthetic:"]):
                            final_prompt = (
                                f"Art Style: {style_prompt}. "
                                f"Scene Composition: {raw_prompt}. "
                                f"Atmospheric environmental background, authentic setting details, cinematic lighting, natural depth, clean {aspect_ratio} vertical composition."
                            )
                        else:
                            final_prompt = (
                                f"{raw_prompt}. "
                                f"Atmospheric environmental background, authentic setting details, cinematic lighting, natural depth, clean {aspect_ratio} vertical composition."
                            )

                        payload = {
                            "model": current_model,
                            "prompt": final_prompt,
                            "aspect_ratio": aspect_ratio
                        }
                        if ref_data_uri and "krea" in current_model.lower():
                            payload["input_references"] = [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": ref_data_uri
                                    }
                                }
                            ]
                            print(f"[Image Generator] Chaining Master Reference Image into {current_model} for scene consistency")

                        print(f"[Image Generator] Calling OpenRouter /images ({current_model}) attempt {attempt} for: '{prompt[:45]}...'")
                        # 120s timeout allows heavy diffusion models ample time without false premature aborts
                        res = requests.post(
                            "https://openrouter.ai/api/v1/images",
                            headers=headers,
                            json=payload,
                            timeout=(15, 120)
                        )
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
                                    print(f"[Image Generator] Saved image ({current_model}): {output_path}")
                                    return output_path
                                elif item.get("url"):
                                    u_res = requests.get(item["url"], timeout=45)
                                    with open(output_path, "wb") as f:
                                        f.write(u_res.content)
                                    print(f"[Image Generator] Saved image ({current_model}): {output_path}")
                                    return output_path
                        else:
                            print(f"[Image Generator] /images ({current_model}) returned status {res.status_code}: {res.text[:120]}")
                            last_error = f"HTTP {res.status_code}: {res.text[:120]}"

                    else:
                        # Chat completions image endpoint (e.g. Gemini 2.5/3.1 flash image)
                        style_clause = f"Art Style & Aesthetic: {style_prompt}. " if style_prompt else ""
                        continuity_clause = "CRITICAL CONTINUITY DIRECTIVE: Maintain exact character facial structure, age, hair, clothing, room environment, and rendering style from the attached reference image. " if ref_data_uri else ""
                        enriched_prompt = (
                            f"Generate a cinematic, high-impact vertical {aspect_ratio} still storyboard frame. "
                            f"{style_clause}"
                            f"{continuity_clause}"
                            f"Scene Description: {prompt.strip()}. "
                            f"Atmospheric environmental background, rich authentic setting details, expressive character presence, cinematic depth, natural lighting. "
                            f"Respect the specified shot framing (wide, medium establishing, or close-up) with full environmental setting and zero text overlays or subtitles."
                        )

                        if ref_data_uri:
                            user_content = [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": ref_data_uri}
                                },
                                {
                                    "type": "text",
                                    "text": enriched_prompt
                                }
                            ]
                        else:
                            user_content = enriched_prompt

                        payload = {
                            "model": current_model,
                            "messages": [{"role": "user", "content": user_content}]
                        }
                        print(f"[Image Generator] Calling OpenRouter chat ({current_model}) attempt {attempt} for: '{prompt[:45]}...'")
                        res = requests.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=(15, 120)
                        )
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
                                        print(f"[Image Generator] Saved image ({current_model}): {output_path}")
                                        return output_path
                                    elif url_val.startswith("http"):
                                        u_res = requests.get(url_val, timeout=45)
                                        with open(output_path, "wb") as f:
                                            f.write(u_res.content)
                                        print(f"[Image Generator] Saved image ({current_model}): {output_path}")
                                        return output_path
                        else:
                            print(f"[Image Generator] chat ({current_model}) returned status {res.status_code}: {res.text[:120]}")
                            last_error = f"HTTP {res.status_code}: {res.text[:120]}"

                except requests.exceptions.Timeout as e:
                    print(f"[Image Generator] Timeout ({current_model}, attempt {attempt}/2): {e}")
                    last_error = f"Read timed out ({current_model}): {e}"
                except requests.exceptions.RequestException as e:
                    print(f"[Image Generator] Network error ({current_model}, attempt {attempt}/2): {e}")
                    last_error = str(e)
                except Exception as e:
                    if "spending limit reached" in str(e).lower() or "key limit exceeded" in str(e).lower():
                        raise e
                    print(f"[Image Generator] Unexpected error ({current_model}, attempt {attempt}/2): {e}")
                    last_error = str(e)

                # Brief delay before retry
                if attempt < 2:
                    time.sleep(2)

            # If current_model exhausted attempts, inform and move to fallback
            if current_model != models_to_try[-1]:
                print(f"[Image Generator] {current_model} timed out or failed. Falling back to {fallback_model}...")

        raise RuntimeError(f"OpenRouter image generation failed: {last_error or 'Unknown error'}")

    def _generate_replicate(
        self,
        prompt: str,
        output_path: str,
        width: int = 768,
        height: int = 1344,
        aspect_ratio: str = "9:16",
        art_style: Optional[str] = None,
        reference_image: Optional[str] = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.replicate_token}",
            "Content-Type": "application/json"
        }
        art_key = art_style or getattr(Config, "ACTIVE_ART_STYLE", "photo_35mm")
        clio_info = getattr(Config, "CLIO_STYLES", {}).get(art_key)
        style_prompt = clio_info.get("prompt", "") if clio_info else ""
        if style_prompt and not any(k in prompt.lower() for k in ["art style:", "aesthetic:"]):
            flux_prompt = f"Art Style: {style_prompt}. Scene: {prompt}. Atmospheric environmental background, authentic setting details, cinematic lighting, natural depth."
        else:
            flux_prompt = f"{prompt}. Atmospheric environmental background, authentic setting details, cinematic lighting, natural depth."

        payload = {
            "version": "black-forest-labs/flux-schnell",
            "input": {"prompt": flux_prompt, "aspect_ratio": aspect_ratio, "output_format": "png"}
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
