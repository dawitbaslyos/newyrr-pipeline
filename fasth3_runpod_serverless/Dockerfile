# Base image with CUDA 12.4 and PyTorch 2.4
FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
WORKDIR /

# 1. Install system tools and fast download utilities
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "huggingface_hub[cli]" hf_transfer runpod websocket-client requests Pillow

# Enable accelerated Hugging Face downloads
ENV HF_HUB_ENABLE_HF_TRANSFER=1

# 2. Clone ComfyUI Core
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui
WORKDIR /comfyui
RUN pip install --no-cache-dir -r requirements.txt

# 3. Install FastVideo & ComfyUI extensions
WORKDIR /comfyui/custom_nodes
RUN git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git
RUN git clone https://github.com/FastVideo/FastVideo.git || true

# 4. Bake FastH3 Models
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

WORKDIR /comfyui/models

# Download 8-step Distilled Diffusion Model, Qwen3-VL Text Encoder, and VAEs in one optimized batch
RUN huggingface-cli download FastVideo/FastVideo-FastH3-Comfy \
    diffusion_models/fastvideo_fasth3_8step_v2_pruned_int8_convrot.safetensors \
    text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors \
    vae/minimax_h3_video_vae_int8_convrot.safetensors \
    vae/minimax_h3_audio_vae_fp32.safetensors \
    --local-dir /comfyui/models --token ${HF_TOKEN}

# 5. Copy Runner Scripts and Workflow
WORKDIR /
COPY fasth3_api.json /fasth3_api.json
COPY rp_handler.py /rp_handler.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
