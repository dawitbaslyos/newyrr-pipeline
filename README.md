# Newyrr Studio — Automated YouTube Shorts Production Pipeline

An end-to-end automated production pipeline built specifically for **@Newyrr** (*"Shorts science. How and what if moments."*).

---

## 🏗️ Architecture Overview

```
1. YouTube Data API v3  ───> Pulls historical performance & algorithm retention cues
2. OpenRouter API       ───> Generates 5-scene viral screenplay (hooks, narration, cues)
3. ElevenLabs / TTS     ───> Synthesizes scene narration tracks (.mp3)
4. RunPod Flux Krea     ───> Generates ultra-detailed 9:16 vertical keyframes (.png)
5. RunPod MiniMax H3    ───> Animates each still with physical realism (ComfyUI API)
6. FFmpeg & Whisper     ───> Assembles clips & burns kinetic bouncing ASS captions
7. Local Web Dashboard  ───> Minimal Primitives UI to control the whole flow
```

---

## 🚀 Quick Start

### 1. Configure Your API Keys
Copy `.env.example` to `.env` in this directory:
```bash
copy .env.example .env
```
Fill in your keys:
- `OPENROUTER_API_KEY`: For script & visual prompt generation.
- `RUNPOD_API_KEY`: For cloud GPU image & video rendering.
- `RUNPOD_MINIMAX_ENDPOINT_ID`: Your ComfyUI MiniMax H3 Max Turbo serverless endpoint.
- `RUNPOD_FLUX_ENDPOINT_ID`: Your Flux Krea serverless endpoint.
- `YOUTUBE_API_KEY`: To connect live analytics from `@Newyrr`.
- `ELEVENLABS_API_KEY`: For character voice narration.

*(Note: The system contains built-in fallbacks for all APIs, allowing complete offline dry runs and test renders without consuming cloud balance!)*

### 2. Launch the Local Studio Dashboard
Double-click `run_studio.bat` or run:
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
Open your browser to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📁 Project Structure

* **`minimax_h3_api.json`**: ComfyUI API prompt execution graph for MiniMax H3 Max Turbo.
* **`minimax_runner.py`**: Parameterizes the ComfyUI graph and dispatches jobs to RunPod Serverless.
* **`flux_runner.py`**: Dispatches 9:16 keyframe image generations to RunPod Flux Krea.
* **`audio_generator.py`**: Synthesizes narration tracks and calculates word timings with FFmpeg.
* **`script_generator.py`**: OpenRouter LLM engine conditioned on channel performance data.
* **`youtube_analytics.py`**: Queries YouTube Data API v3 for `@Newyrr` retention & topic analysis.
* **`video_assembler.py`**: FFmpeg stitching engine with dynamic bouncing ASS subtitle burn-in.
* **`pipeline_orchestrator.py`**: Coordinates script -> audio -> image -> video -> assembly.
* **`app.py` & `index.html`**: FastAPI backend and minimal primitive-first web UI.
* **`projects/`**: Active staging folders holding scene assets for each Short.
* **`output/`**: Fully rendered, captioned, ready-to-upload YouTube Shorts.
* **`../used/`**: Archive directory for completed source files (matching your channel convention).
