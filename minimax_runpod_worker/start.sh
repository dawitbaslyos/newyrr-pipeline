#!/bin/bash
set -e

echo "[RunPod] Starting local ComfyUI headless server..."
python3 /comfyui/main.py --listen 127.0.0.1 --port 8188 --dont-print-server &

# Wait for ComfyUI to respond on port 8188
echo "[RunPod] Waiting for ComfyUI to become available..."
until curl -s http://127.0.0.1:8188/system_stats > /dev/null; do
    sleep 1
done

echo "[RunPod] ComfyUI is live! Starting RunPod Serverless Handler..."
python3 -u /rp_handler.py
