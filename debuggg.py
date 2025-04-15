from flask import Flask, request, jsonify
import json
from utils import init_client, apply_chat_qwen2vl, analyze_response_message, find_user_name, add_memory, init_memory
import os
from mem0 import Memory
import logging
from PIL import Image
from io import BytesIO
import base64

def image_to_base64_data_uri(image_path):
    """将图片文件转换为 Base64编码的 Data URI"""
    try:
        with Image.open(image_path) as img:
            img_format = img.format if img.format else 'JPEG' # 默认 JPEG
            if img_format == 'MPO': # Pillow 可能将某些 JPEG 识别为 MPO
                img_format = 'JPEG'
            buffered = BytesIO()
            # 确保图像是 RGB 模式，以避免 RGBA 或 P 模式保存问题
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buffered, format=img_format)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return f"data:image/{img_format.lower()};base64,{img_base64}"
    except FileNotFoundError:
        logging.info(f"error: can not find image file {image_path}")
        return None
    except Exception as e:
        logging.info(f"error: can not encode image file {image_path}: {e}")
        return None

os.environ["OPENAI_BASE_URL"] = "http://localhost:8001/v1"
os.environ["OPENAI_API_KEY"] = "token-abc123"
client, bge_model = init_client()
mem_graph_config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "Qwen2.5-14B-Instruct-1M",
                    "temperature": 0.2,
                    "max_tokens": 8192,
                }
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": "neo4j://localhost:7687",
                    "username": "neo4j",
                    "password": "omnimate666"
                }
            },
            "embedder": {
                "provider": "lmstudio",
                "config": {
                    "model": "bge-m3",
                    "embedding_dims": 1024,
                    "lmstudio_base_url": "http://localhost:8002/v1",
                    "api_key": "token-abc123"
                }
            }
        }
mem_graph = Memory.from_config(config_dict=mem_graph_config)
# mem_graph.embedding_model = bge_model
print("memory graph initialized")




# import debugpy
# debugpy.listen(("0.0.0.0", 5678))
# print("Waiting for debugger attach...")
# debugpy.wait_for_client()



user_id = "token123"
user_name = find_user_name(user_id)
description_index, description_metadata_map, summary_index, summary_metadata_map = init_memory(user_id)
image = image_to_base64_data_uri("test/2025-04-12-01-15-44.png")

messages = apply_chat_qwen2vl(image)

completion = client.chat.completions.create(
                model="Qwen2.5-VL-7B-Instruct",
                messages=messages,
                max_tokens=32768,
            )
content = completion.choices[0].message.content
image_description, image_summary, user_preference = analyze_response_message(content, user_name)

# add_memory(user_id, bge_model, image_description, image_summary, description_index, description_metadata_map, summary_index, summary_metadata_map)
mem_graph.add(user_preference, user_id)

print("image description:", image_description)