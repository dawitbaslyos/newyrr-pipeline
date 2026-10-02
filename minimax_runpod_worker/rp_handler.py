import os
import json
import base64
import time
import uuid
import urllib.request
import urllib.parse
import websocket
import runpod

# ComfyUI local server address (started in container)
COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_TEMPLATE = os.path.join(os.path.dirname(__file__), "minimax_h3_api.json")

def queue_comfy_prompt(prompt_workflow, client_id):
    p = {"prompt": prompt_workflow, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_URL}/prompt", data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def upload_input_image(image_input, filename):
    input_dir = "/comfyui/input"
    os.makedirs(input_dir, exist_ok=True)
    target_path = os.path.join(input_dir, filename)

    if image_input.startswith("http://") or image_input.startswith("https://"):
        urllib.request.urlretrieve(image_input, target_path)
    elif "base64," in image_input:
        b64 = image_input.split("base64,")[1]
        with open(target_path, "wb") as f:
            f.write(base64.b64decode(b64))
    else:
        # Raw base64 string
        with open(target_path, "wb") as f:
            f.write(base64.b64decode(image_input))
    return filename

def handler(job):
    """
    RunPod Serverless Handler for MiniMax H3 Max Turbo.
    Accepts:
      - first_frame (URL or base64)
      - prompt (motion text prompt)
      - duration (int, default 5)
      - prompt_enhance (bool, default False)
      - upscale_2k (bool, default False)
      - seed (int, optional)
    """
    job_input = job.get("input", {})
    first_frame = job_input.get("first_frame")
    motion_prompt = job_input.get("prompt", "Cinematic subtle motion")
    duration = int(job_input.get("duration", 5))
    prompt_enhance = bool(job_input.get("prompt_enhance", False))
    upscale_2k = bool(job_input.get("upscale_2k", False))
    seed = job_input.get("seed", int(time.time()))

    if not first_frame:
        return {"error": "first_frame (URL or base64) is required in job input."}

    # 1. Save uploaded image to ComfyUI input folder
    image_filename = f"input_{uuid.uuid4().hex[:8]}.png"
    upload_input_image(first_frame, image_filename)

    # 2. Load API workflow template
    with open(WORKFLOW_TEMPLATE, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # 3. Inject inputs
    workflow["25"]["inputs"]["image"] = image_filename
    workflow["14"]["inputs"]["value"] = motion_prompt
    workflow["18"]["inputs"]["value"] = prompt_enhance
    workflow["19"]["inputs"]["value"] = upscale_2k
    workflow["24"]["inputs"]["seed"] = seed
    workflow["24"]["inputs"]["model.duration"] = duration

    if "7" in workflow and "inputs" in workflow["7"]:
        workflow["7"]["inputs"]["model.duration"] = duration

    # 4. Queue and track execution
    client_id = str(uuid.uuid4())
    queue_res = queue_comfy_prompt(workflow, client_id)
    prompt_id = queue_res.get("prompt_id")

    # Connect to websocket to wait for completion
    ws = websocket.WebSocket()
    ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")

    output_video_path = None
    timeout = 300
    start_time = time.time()

    while time.time() - start_time < timeout:
        out = ws.recv()
        if isinstance(out, str):
            msg = json.loads(out)
            if msg.get("type") == "executing":
                data = msg.get("data", {})
                if data.get("node") is None and data.get("prompt_id") == prompt_id:
                    # Execution finished!
                    break

    # Look for generated video in ComfyUI output directory
    output_dir = "/comfyui/output"
    found_videos = []
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith((".mp4", ".webm")):
                full_p = os.path.join(root, file)
                found_videos.append((full_p, os.path.getmtime(full_p)))

    if found_videos:
        # Pick the latest generated video
        found_videos.sort(key=lambda x: x[1], reverse=True)
        latest_video = found_videos[0][0]

        with open(latest_video, "rb") as vf:
            video_b64 = base64.b64encode(vf.read()).decode("utf-8")

        return {
            "status": "success",
            "video_base64": video_b64,
            "filename": os.path.basename(latest_video)
        }

    return {"error": "Video generation timed out or failed to output file."}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
