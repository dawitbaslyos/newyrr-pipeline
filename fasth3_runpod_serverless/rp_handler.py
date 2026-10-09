import os
import json
import base64
import time
import uuid
import urllib.request
import urllib.parse
import websocket
import runpod

COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_TEMPLATE = "/fasth3_api.json"

def queue_comfy_prompt(prompt_workflow, client_id):
    payload = {"prompt": prompt_workflow, "client_id": client_id}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

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
        with open(target_path, "wb") as f:
            f.write(base64.b64decode(image_input))
    return filename

def handler(job):
    """
    RunPod Serverless Handler for FastVideo FastH3 (8-Step MiniMax H3).
    Input contract:
      - first_frame: string (URL or base64) [REQUIRED]
      - prompt: string (motion description and audio cues) [OPTIONAL]
      - duration: float or int (in seconds, default 5.0) [OPTIONAL]
      - seed: int (optional, default random) [OPTIONAL]
    """
    job_input = job.get("input", {})
    first_frame = job_input.get("first_frame") or job_input.get("image")
    prompt = job_input.get("prompt", "Cinematic motion, high fidelity")
    duration = float(job_input.get("duration", 5.0))
    seed = job_input.get("seed", int(time.time() % 1000000000))

    if not first_frame:
        return {"error": "Missing required field 'first_frame' (image URL or base64 string)."}

    # 1. Place frame in ComfyUI input directory
    image_filename = f"h3_{uuid.uuid4().hex[:8]}.png"
    upload_input_image(first_frame, image_filename)

    # 2. Load compiled API workflow
    if not os.path.exists(WORKFLOW_TEMPLATE):
        return {"error": f"Workflow template {WORKFLOW_TEMPLATE} not found in container."}

    with open(WORKFLOW_TEMPLATE, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # 3. Inject inputs into compiled nodes
    # Node 136: LoadImage
    workflow["136"]["inputs"]["image"] = image_filename
    # Node 104: MiniMaxH3ImageToVideo
    workflow["104"]["inputs"]["prompt"] = prompt
    # Node 111: PrimitiveFloat (Duration)
    workflow["111"]["inputs"]["value"] = duration
    # Node 15: RandomNoise (Seed)
    workflow["15"]["inputs"]["noise_seed"] = seed

    # 4. Dispatch to local ComfyUI
    client_id = str(uuid.uuid4())
    try:
        queue_res = queue_comfy_prompt(workflow, client_id)
        prompt_id = queue_res.get("prompt_id")
    except Exception as e:
        return {"error": f"Failed to queue prompt to ComfyUI: {str(e)}"}

    if not prompt_id:
        return {"error": f"ComfyUI did not return prompt_id: {queue_res}"}

    # 5. Connect WebSocket to await completion
    ws = websocket.WebSocket()
    ws.connect(f"ws://127.0.0.1:8188/ws?clientId={client_id}")

    timeout = 360 # 6 min max wait
    start_time = time.time()

    while time.time() - start_time < timeout:
        out = ws.recv()
        if isinstance(out, str):
            msg = json.loads(out)
            msg_type = msg.get("type")

            if msg_type == "execution_error":
                error_data = msg.get("data", {})
                return {
                    "error": "ComfyUI execution error",
                    "details": error_data
                }

            if msg_type == "executing":
                data = msg.get("data", {})
                if data.get("node") is None and data.get("prompt_id") == prompt_id:
                    # Rendering complete!
                    break

    # 6. Locate rendered video in /comfyui/output
    output_dir = "/comfyui/output"
    found_videos = []
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith((".mp4", ".webm")):
                full_path = os.path.join(root, file)
                found_videos.append((full_path, os.path.getmtime(full_path)))

    if found_videos:
        found_videos.sort(key=lambda x: x[1], reverse=True)
        latest_video = found_videos[0][0]

        with open(latest_video, "rb") as vf:
            video_b64 = base64.b64encode(vf.read()).decode("utf-8")

        return {
            "status": "success",
            "video_base64": video_b64,
            "filename": os.path.basename(latest_video),
            "duration": duration,
            "render_time_seconds": round(time.time() - start_time, 2)
        }

    return {"error": "Rendering completed but no video file was generated in output folder."}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
