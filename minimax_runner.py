import json
import os
import base64
import time
import requests
from typing import Optional, Dict, Any
from config import Config

WORKFLOW_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "minimax_h3_api.json")

class MiniMaxRunPodClient:
    """
    Client for dispatching MiniMax H3 Max Turbo to RunPod Serverless ComfyUI Wizard (ucla82uhwqfvd8).
    Supports both runsync and async polling.
    """

    def __init__(self, api_key: Optional[str] = None, endpoint_id: Optional[str] = None):
        self.api_key = api_key or Config.RUNPOD_API_KEY
        self.endpoint_id = endpoint_id or Config.RUNPOD_MINIMAX_ENDPOINT_ID or "ucla82uhwqfvd8"
        with open(WORKFLOW_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            self.base_workflow = json.load(f)

    def build_workflow(
        self,
        image_ref: str,
        motion_prompt: str,
        duration: int = 5,
        prompt_enhance: bool = False,
        upscale_2k: bool = False,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        workflow = json.loads(json.dumps(self.base_workflow))

        # Node 14: Prompt text
        workflow["14"]["inputs"]["value"] = motion_prompt

        # Node 25: Image filename
        workflow["25"]["inputs"]["image"] = image_ref

        # Node 18: Prompt Enhance Switch
        workflow["18"]["inputs"]["value"] = bool(prompt_enhance)

        # Node 19: Upscale 2K Switch
        workflow["19"]["inputs"]["value"] = bool(upscale_2k)

        # Node 24: Seed
        actual_seed = seed if seed is not None else int(time.time() % 1000000000)
        workflow["24"]["inputs"]["seed"] = actual_seed

        if "7" in workflow and "inputs" in workflow["7"]:
            workflow["7"]["inputs"]["model.duration"] = duration

        return workflow

    def build_runpod_payload(
        self,
        image_path_or_url: str,
        motion_prompt: str,
        duration: int = 5,
        prompt_enhance: bool = False,
        upscale_2k: bool = False,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        image_name = os.path.basename(image_path_or_url)
        if not image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            image_name = "input_frame.png"

        image_data = image_path_or_url
        if os.path.exists(image_path_or_url):
            with open(image_path_or_url, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                image_data = f"data:image/png;base64,{b64}"

        workflow = self.build_workflow(
            image_ref=image_name,
            motion_prompt=motion_prompt,
            duration=duration,
            prompt_enhance=prompt_enhance,
            upscale_2k=upscale_2k,
            seed=seed
        )

        return {
            "input": {
                "workflow": workflow,
                "images": [
                    {
                        "name": image_name,
                        "image": image_data
                    }
                ]
            }
        }

    def render_scene_video(self, payload: Dict[str, Any], output_path: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Submit via /run
        url_run = f"https://api.runpod.ai/v2/{self.endpoint_id}/run"
        print(f"[MiniMax H3] Submitting scene job to RunPod ({self.endpoint_id})...")
        res = requests.post(url_run, headers=headers, json=payload, timeout=30)
        job_data = res.json()
        job_id = job_data.get("id")

        if not job_id:
            raise RuntimeError(f"MiniMax submission failed: {job_data}")

        print(f"[MiniMax H3] Job queued: {job_id}. Awaiting GPU render...")
        status_data = self.poll_job_status(job_id)
        return self.download_output_video(status_data, output_path)

    def poll_job_status(self, job_id: str, timeout: int = 360, poll_interval: int = 5) -> Dict[str, Any]:
        url = f"https://api.runpod.ai/v2/{self.endpoint_id}/status/{job_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        start = time.time()

        while time.time() - start < timeout:
            res = requests.get(url, headers=headers, timeout=15)
            data = res.json()
            status = data.get("status")
            print(f"[MiniMax H3] Job {job_id}: {status} ({int(time.time() - start)}s)")

            if status == "COMPLETED":
                return data
            elif status in ["FAILED", "CANCELLED", "TIMED_OUT"]:
                error_detail = data.get("output", {}).get("details", data.get("error", status))
                raise RuntimeError(f"MiniMax job {job_id} failed: {error_detail}")

            time.sleep(poll_interval)

        raise TimeoutError(f"MiniMax job {job_id} timed out.")

    def download_output_video(self, job_result: Dict[str, Any], output_path: str) -> str:
        output = job_result.get("output", {})
        video_url = None

        if isinstance(output, dict):
            videos = output.get("videos") or output.get("message", {}).get("videos", [])
            if videos and isinstance(videos, list):
                video_url = videos[0]
            elif "video_url" in output:
                video_url = output["video_url"]
            elif "video_base64" in output:
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(output["video_base64"]))
                print(f"[MiniMax H3] Saved base64 video to: {output_path}")
                return output_path
        elif isinstance(output, list) and output:
            video_url = output[0]

        if video_url and str(video_url).startswith("http"):
            print(f"[MiniMax H3] Downloading video from {video_url} to {output_path}...")
            res = requests.get(video_url, timeout=60)
            with open(output_path, "wb") as f:
                f.write(res.content)
            return output_path
        else:
            raise ValueError(f"Could not extract video output from MiniMax result: {output}")

if __name__ == "__main__":
    client = MiniMaxRunPodClient()
    print("MiniMax client ready for endpoint:", client.endpoint_id)
