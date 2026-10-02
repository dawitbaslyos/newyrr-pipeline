# Base image with CUDA 12.1 and PyTorch
FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui
WORKDIR /comfyui
RUN pip install --no-cache-dir -r requirements.txt

# Install Custom Nodes
WORKDIR /comfyui/custom_nodes
# 1. ComfyUI Manager
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git
# 2. ComfyUI-Custom-Scripts (for String, Boolean and Switch primitives)
RUN git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git
# 3. ComfyUI-MiniMax / Hailuo Integration
RUN git clone https://github.com/Comfy-Org/ComfyUI_frontend.git || true

# Install RunPod Serverless worker dependencies
RUN pip install --no-cache-dir runpod websocket-client requests Pillow

# Copy Handler and Workflow
WORKDIR /
COPY rp_handler.py /rp_handler.py
COPY minimax_h3_api.json /minimax_h3_api.json
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Run startup script
CMD ["/start.sh"]
