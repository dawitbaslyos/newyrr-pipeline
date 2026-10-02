import json
import os

# Create pipeline directory
pipeline_dir = r"c:\Users\dawit\Videos\Youtube Channels\internetchill\pipeline"
os.makedirs(pipeline_dir, exist_ok=True)

# The raw UI workflow data provided by the user
raw_ui_workflow = {
  "nodes": [
    {
      "id": 2,
      "type": "SaveVideo",
      "inputs": [
        {"name": "video", "link": 36},
        {"name": "filename_prefix", "link": None},
        {"name": "format", "link": None},
        {"name": "format.codec", "link": None},
        {"name": "codec", "link": None}
      ],
      "widgets_values_named": {
        "codec": "auto",
        "filename_prefix": "video/video/MiniMax_H3_Max_turbo_i2v_768P",
        "format": "auto",
        "format.codec": "auto"
      }
    },
    {
      "id": 7,
      "type": "MinimaxHailuo03ContextIRNode",
      "inputs": [
        {"name": "first_frame", "link": 38},
        {"name": "last_frame", "link": None},
        {"name": "model", "link": None},
        {"name": "model.prompt", "link": 22},
        {"name": "model.duration", "link": None},
        {"name": "model.ratio", "link": None},
        {"name": "model.reference_images.image_1", "link": None},
        {"name": "model.reference_videos.video_1", "link": None},
        {"name": "model.reference_audios.audio_1", "link": None}
      ],
      "widgets_values_named": {
        "model": "MiniMax H3",
        "model.duration": 5,
        "model.prompt": "",
        "model.ratio": "adaptive"
      }
    },
    {
      "id": 8,
      "type": "SaveText",
      "inputs": [
        {"name": "text", "link": 23},
        {"name": "filename_prefix", "link": None},
        {"name": "format", "link": None}
      ],
      "widgets_values_named": {
        "filename_prefix": "H3_prompt",
        "format": "txt"
      }
    },
    {
      "id": 10,
      "type": "MinimaxHailuo03RegenerateNode",
      "inputs": [
        {"name": "video", "link": 10},
        {"name": "first_frame", "link": 39},
        {"name": "last_frame", "link": None},
        {"name": "model", "link": None},
        {"name": "model.prompt", "link": 12},
        {"name": "model.resolution", "link": None},
        {"name": "watermark", "link": None}
      ],
      "widgets_values_named": {
        "model": "MiniMax H3",
        "model.prompt": "",
        "model.resolution": "2K",
        "watermark": False
      }
    },
    {
      "id": 11,
      "type": "SaveVideo",
      "inputs": [
        {"name": "video", "link": 20},
        {"name": "filename_prefix", "link": None},
        {"name": "format", "link": None},
        {"name": "format.codec", "link": None},
        {"name": "codec", "link": None}
      ],
      "widgets_values_named": {
        "codec": "auto",
        "filename_prefix": "video/Minimax_h3_max",
        "format": "auto",
        "format.codec": "auto"
      }
    },
    {
      "id": 12,
      "type": "ComfySwitchNode",
      "inputs": [
        {"name": "on_false", "link": 21},
        {"name": "on_true", "link": 17},
        {"name": "switch", "link": 26}
      ],
      "widgets_values_named": {
        "switch": False
      }
    },
    {
      "id": 13,
      "type": "ComfySwitchNode",
      "inputs": [
        {"name": "on_false", "link": 37},
        {"name": "on_true", "link": 18},
        {"name": "switch", "link": 25}
      ],
      "widgets_values_named": {
        "switch": False
      }
    },
    {
      "id": 14,
      "type": "PrimitiveStringMultiline",
      "inputs": [
        {"name": "value", "link": None}
      ],
      "widgets_values_named": {
        "value": "Prompt text here"
      }
    },
    {
      "id": 18,
      "type": "PrimitiveBoolean",
      "inputs": [
        {"name": "value", "link": None}
      ],
      "widgets_values_named": {
        "value": False
      }
    },
    {
      "id": 19,
      "type": "PrimitiveBoolean",
      "inputs": [
        {"name": "value", "link": None}
      ],
      "widgets_values_named": {
        "value": False
      }
    },
    {
      "id": 24,
      "type": "MinimaxHailuo03FirstLastFrameNode",
      "inputs": [
        {"name": "first_frame", "link": 31},
        {"name": "last_frame", "link": None},
        {"name": "model", "link": None},
        {"name": "model.prompt", "link": 35},
        {"name": "model.resolution", "link": None},
        {"name": "model.duration", "link": None},
        {"name": "model.prompt_expansion_mode", "link": None},
        {"name": "seed", "link": None},
        {"name": "watermark", "link": None}
      ],
      "widgets_values_named": {
        "control_after_generate": "randomize",
        "model": "MiniMax H3 Max Turbo",
        "model.duration": 5,
        "model.prompt": "",
        "model.prompt_expansion_mode": "balanced",
        "model.resolution": "768P",
        "seed": 2188635952,
        "watermark": False
      }
    },
    {
      "id": 25,
      "type": "LoadImage",
      "inputs": [
        {"name": "image", "link": None},
        {"name": "choose file to upload", "link": None}
      ],
      "widgets_values_named": {
        "image": "input_first_frame.png",
        "upload": "image"
      }
    }
  ],
  "links": [
    [17, 7, 0, 12, 1, "STRING"],
    [18, 10, 0, 13, 1, "VIDEO"],
    [21, 14, 0, 12, 0, "STRING"],
    [23, 12, 0, 8, 0, "STRING"],
    [25, 19, 0, 13, 2, "BOOLEAN"],
    [26, 18, 0, 12, 2, "BOOLEAN"],
    [37, 24, 0, 13, 0, "VIDEO"],
    [36, 24, 0, 2, 0, "VIDEO"],
    [38, 25, 0, 7, 0, "IMAGE"],
    [22, 14, 0, 7, 3, "STRING"],
    [10, 2, 0, 10, 0, "VIDEO"],
    [39, 25, 0, 10, 1, "IMAGE"],
    [12, 8, 0, 10, 4, "STRING"],
    [20, 13, 0, 11, 0, "VIDEO"],
    [31, 25, 0, 24, 0, "IMAGE"],
    [35, 12, 0, 24, 3, "STRING"]
  ]
}

# Mapping link_id -> [from_node_id_str, from_socket_idx]
link_map = {}
for link in raw_ui_workflow["links"]:
    link_id, from_node, from_socket, to_node, to_socket, link_type = link
    link_map[link_id] = [str(from_node), from_socket]

# Convert to ComfyUI API Prompt format
api_prompt = {}

for node in raw_ui_workflow["nodes"]:
    node_id_str = str(node["id"])
    class_type = node["type"]
    inputs_dict = {}

    # 1. Fill widget values
    for k, v in node.get("widgets_values_named", {}).items():
        inputs_dict[k] = v

    # 2. Wire linked inputs
    for inp in node.get("inputs", []):
        inp_name = inp["name"]
        link_id = inp.get("link")
        if link_id is not None and link_id in link_map:
            inputs_dict[inp_name] = link_map[link_id]

    api_prompt[node_id_str] = {
        "inputs": inputs_dict,
        "class_type": class_type,
        "_meta": {
            "title": f"Node {node['id']} ({class_type})"
        }
    }

out_path = os.path.join(pipeline_dir, "minimax_h3_api.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(api_prompt, f, indent=2)

print(f"Successfully generated ComfyUI API workflow at: {out_path}")
print(f"Total nodes in API graph: {len(api_prompt)}")
