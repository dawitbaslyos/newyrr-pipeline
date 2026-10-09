import os
import requests
from typing import Optional
from config import Config

def call_llm(
    prompt: str,
    system_prompt: str = "",
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 4096
) -> str:
    """
    Unified OpenRouter LLM caller for text/code/SVG generation across all engines.
    """
    api_key = getattr(Config, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/internetchill/newyrr-pipeline",
        "X-Title": "Newyrr Studio",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    preferred = model or "openai/gpt-4o-mini"
    fallback_models = [preferred, "openai/gpt-4o-mini", "google/gemini-2.5-flash", "anthropic/claude-3.5-haiku"]
    seen = set()
    models = [m for m in fallback_models if m and not (m in seen or seen.add(m))]

    for m in models:
        try:
            payload = {
                "model": m,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45
            )
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    if content and content.strip():
                        return content
            else:
                print(f"[llm_client] Model {m} returned {res.status_code}: {res.text[:100]}")
        except Exception as e:
            print(f"[llm_client] Exception calling {m}: {e}")

    raise RuntimeError(f"All LLM models failed to generate response for prompt: {prompt[:50]}...")
