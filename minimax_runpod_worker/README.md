# MiniMax H3 Max Turbo — RunPod Serverless Worker

Deploy your ComfyUI MiniMax H3 Max Turbo workflow on RunPod Serverless with zero idle GPU cost.

---

## 🚀 How to Deploy to RunPod Serverless (Via GitHub)

### Step 1: Push this folder to GitHub
In terminal inside this `minimax_runpod_worker` folder:
```bash
git init
git add .
git commit -m "MiniMax H3 Max Turbo RunPod Serverless Worker"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/minimax-runpod-worker.git
git push -u origin main
```

### Step 2: Build & Deploy on RunPod Serverless
1. Log into your [RunPod Console](https://www.runpod.io/console/serverless).
2. Go to **Serverless** -> **Templates** -> **New Template**.
   * **Template Name:** `minimax-h3-max-turbo`
   * **Container Image / GitHub:** Select your GitHub repo (`YOUR_GITHUB_USERNAME/minimax-runpod-worker`) or link your Docker Hub image.
3. Click **Endpoints** -> **New Endpoint**:
   * Select your `minimax-h3-max-turbo` template.
   * **GPU:** Select an RTX 4090, L40, or A40.
   * **Active Workers:** Set `Min = 0` (so it costs $0 when idle) and `Max = 1` or `2`.
4. Copy the generated **Endpoint ID** (e.g. `abc123xyz`).
5. Paste it into your `pipeline/.env`:
   ```env
   RUNPOD_MINIMAX_ENDPOINT_ID=abc123xyz
   ```

---

## 📡 API Input Payload Schema

When calling this endpoint:
```json
{
  "input": {
    "first_frame": "https://your-storage.com/scene_01.png",
    "prompt": "At 0.00 seconds, slow macro push-in on skin pores...",
    "duration": 5,
    "prompt_enhance": false,
    "upscale_2k": false,
    "seed": 424242
  }
}
```

The worker returns:
```json
{
  "status": "success",
  "video_base64": "...",
  "filename": "MiniMax_H3_Max_turbo_0001.mp4"
}
```
