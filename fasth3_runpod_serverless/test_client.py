import requests
import json
import time
import os

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")
ENDPOINT_ID = os.getenv("RUNPOD_FASTH3_ENDPOINT_ID", "<YOUR_ENDPOINT_ID>")
SAMPLE_IMAGE = "https://raw.githubusercontent.com/Comfy-Org/workflow_templates/refs/heads/main/input/red_line_barrier.png"

headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

def test_fasth3_endpoint():
    print(f"Testing FastH3 Serverless Endpoint: {ENDPOINT_ID}...")
    
    # 1. Check health
    h = requests.get(f"https://api.runpod.ai/v2/{ENDPOINT_ID}/health", headers=headers, timeout=10)
    print("Health response:", h.json())
    
    # 2. Submit test job
    payload = {
        "input": {
            "first_frame": SAMPLE_IMAGE,
            "prompt": "Cinematic live-action arc shot, intense atmosphere, slow motion push in",
            "duration": 5.0
        }
    }
    
    print("\nDispatching job via /run...")
    start_t = time.time()
    r = requests.post(f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run", headers=headers, json=payload, timeout=20)
    res_data = r.json()
    job_id = res_data.get("id")
    print("Job ID:", job_id)
    
    if not job_id:
        print("Dispatch failed:", res_data)
        return

    # 3. Poll status
    status_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"
    while time.time() - start_t < 300:
        stat_res = requests.get(status_url, headers=headers, timeout=10).json()
        status = stat_res.get("status")
        print(f"[{int(time.time() - start_t)}s] Status: {status}")
        
        if status == "COMPLETED":
            out = stat_res.get("output", {})
            print("\n=== SUCCESS ===")
            print(f"Render time: {out.get('render_time_seconds')}s")
            print(f"Filename: {out.get('filename')}")
            # Save base64 video
            if "video_base64" in out:
                import base64
                with open("output_fasth3.mp4", "wb") as vf:
                    vf.write(base64.b64decode(out["video_base64"]))
                print("Saved video to output_fasth3.mp4")
            break
        elif status in ["FAILED", "CANCELLED", "TIMED_OUT"]:
            print("\nJob failed:", json.dumps(stat_res, indent=2))
            break
            
        time.sleep(5)

if __name__ == "__main__":
    test_fasth3_endpoint()
