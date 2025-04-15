# server.py
from flask import Flask, request, jsonify
import json
from utils import init_client, apply_chat_qwen2vl, analyze_response_message, find_user_name, add_memory, init_memory, set_logger
import os
from mem0 import Memory

os.environ["OPENAI_BASE_URL"] = "http://localhost:8001/v1"
os.environ["OPENAI_API_KEY"] = "token-abc123"
app = Flask(__name__)


@app.route('/receive_json', methods=['POST'])
def receive_json():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()

        user_id = data["user_id"]
        user_name = find_user_name(user_id)
        description_index, description_metadata_map, summary_index, summary_metadata_map = init_memory(user_id)
        image = data["image"]

        messages = apply_chat_qwen2vl(image)
        
        completion = client.chat.completions.create(
                        model="Qwen2.5-VL-32B-Instruct",
                        messages=messages,
                        max_tokens=32768
                    )
        content = completion.choices[0].message.content
        image_description, image_summary, user_preference = analyze_response_message(content, user_name)

        add_memory(user_id, bge_model, image_description, image_summary, description_index, description_metadata_map, summary_index, summary_metadata_map)
        mem_graph.add(user_preference, user_id)

        return jsonify({"status": "success", "message": "VLM processed successfully"}), 200
    

    except Exception as e:
        print(f"error when: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger = set_logger()
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
    logger.info("memory graph initialized")

    # import debugpy
    # debugpy.listen(("0.0.0.0", 5678))
    # print("Waiting for debugger attach...")
    # debugpy.wait_for_client()

    app.run(host='0.0.0.0', port=5000, debug=True)
