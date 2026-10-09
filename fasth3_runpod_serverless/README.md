# FastVideo FastH3 (MiniMax H3) RunPod Serverless Worker

This repository contains the production RunPod Serverless worker for **FastVideo FastH3 8-Step DMD2-Distilled Image-to-Video**.

## Files Included
- **`Dockerfile`**: Builds PyTorch 2.4 + CUDA 12.4, ComfyUI, FastVideo nodes, and bakes the 38.5 GB models directly into `/comfyui/models/`.
- **`fasth3_api.json`**: Compiled 22-node headless API prompt graph.
- **`rp_handler.py`**: Serverless request handler that manages inputs, WebSocket status tracking, and base64 video output.
- **`start.sh`**: Initializes ComfyUI and launches the serverless handler.
- **`test_client.py`**: Python script to test the deployed endpoint.

---

## Deployment Instructions

### Option 1: Automatic Build via RunPod GitHub Integration (Easiest)
1. Push this folder to your GitHub repository:
   ```bash
   git add fasth3_runpod_serverless
   git commit -m "feat: add FastH3 serverless worker"
   git push origin main
   ```
2. In the [RunPod Console](https://www.runpod.io/console/user/settings):
   - Go to **My Docker / Container Registry**.
   - Select your GitHub repository and specify the path to `Dockerfile`.
   - Add build argument: `HF_TOKEN=<your-huggingface-token>`.
   - RunPod's cloud builders will build the image and push it to `registry.runpod.net/dawitbaslyos-...`.

---

### Option 2: Deploy Endpoint with runpodctl
Once your container image is built:

```powershell
# 1. Create Serverless Template (80 GB container disk)
.\runpodctl.exe template create `
  --name "fasth3-serverless-template" `
  --image "<your-image-tag>" `
  --serverless `
  --container-disk-in-gb 80

# 2. Create the Endpoint (RTX 4090 / A40 / L40)
.\runpodctl.exe sls create `
  --name "fasth3-endpoint" `
  --template-id "<template-id>" `
  --gpu-id "NVIDIA GeForce RTX 4090,NVIDIA A40,NVIDIA L40" `
  --workers-min 0 `
  --workers-max 1 `
  --idle-timeout 5
```

---

## Testing Your Live Endpoint
```powershell
$env:RUNPOD_FASTH3_ENDPOINT_ID = "<YOUR_ENDPOINT_ID>"
python test_client.py
```
