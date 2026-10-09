#!/bin/bash
set -e

echo "[Startup] Starting ComfyUI server in background..."
python /comfyui/main.py --listen 127.0.0.1 --port 8188 --highvram &

# Wait for ComfyUI to become ready
echo "[Startup] Waiting for ComfyUI to bind to port 8188..."
until curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; do
    sleep 2
done

echo "[Startup] ComfyUI is online and ready!"
echo "[Startup] Starting RunPod Serverless worker handler..."
python -u /rp_handler.py
