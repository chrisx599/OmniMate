import json
import re
import ast
import numpy as np
import os
import faiss
import pickle
import logging
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import sys

logger = logging.getLogger()

def extract_dict(s):
    start = s.find('{')
    end = s.rfind('}') + 1  # add 1 to include the closing bracket

    dict_str = s[start:end]

    clean_dict_str = re.sub(r'[`\n]', '', dict_str)

    d = ast.literal_eval(clean_dict_str)
    return d

def check_embedding(embedding):
    if not embedding.flags['C_CONTIGUOUS']: # Faiss 需要 C 连续数组
        embedding = np.ascontiguousarray(embedding)
    if embedding.ndim == 1: # Faiss 需要 2D 数组 (n_vectors, dimension)
        embedding = np.expand_dims(embedding, axis=0)
    embedding = np.array(embedding).astype('float32')

    return embedding

def is_same_already(query_embedding, index, k=10, threshold=0.9) -> bool:
    distances, indices = index.search(query_embedding.astype(np.float32), k)

    for i in range(indices.shape[1]):
        faiss_id = indices[0, i]
        if faiss_id == -1:
            continue
        dist = distances[0, i]
        if dist > threshold:
            return True
    return False


def init_faiss_index(index_file_name):
    faiss_file = index_file_name + ".index"
    if os.path.exists(faiss_file):
        index = faiss.read_index(faiss_file)
        with open(f"{index_file_name}.pkl", "rb") as f:
            metadata_map = pickle.load(f)
    else:
        # index = faiss.IndexFlatL2(dimension)
        index = faiss.IndexFlatIP(1024)
        metadata_map = {}

    return index, metadata_map

def init_memory(user_id, memory_base_path="memory"):
    description_index_name = f"{memory_base_path}/{user_id}_description"
    summary_index_name = f"{memory_base_path}/{user_id}_summary"
    description_index, description_metadata_map = init_faiss_index(description_index_name)
    summary_index, summary_metadata_map = init_faiss_index(summary_index_name)

    return description_index, description_metadata_map, summary_index, summary_metadata_map


def add_memory(user_id, bge_model, description, summary, description_index, description_metadata_map, summary_index, summary_metadata_map, memory_base_path="memory",):
    description_index_name = f"{memory_base_path}/{user_id}_description"
    summary_index_name = f"{memory_base_path}/{user_id}_summary"

    description_embedding = bge_model.encode(description, normalize_embeddings=True)
    summary_embedding = bge_model.encode(summary, normalize_embeddings=True)

    description_embedding = check_embedding(description_embedding)
    is_same_description = is_same_already(description_embedding, description_index, threshold=0.8)
    summary_embedding = check_embedding(summary_embedding)
    is_same_summary = is_same_already(summary_embedding, summary_index, threshold=0.6)

    if not is_same_description:
        description_index.add(description_embedding)
        escription_new_id = description_index.ntotal - 1
        description_metadata_map[escription_new_id] = {
            "text": description
        }
        faiss.write_index(description_index, f"{description_index_name}.index")
        with open(f"{description_index_name}.pkl", "wb") as f:
            pickle.dump(description_metadata_map, f)
    if not is_same_summary:
        summary_index.add(summary_embedding)
        summary_new_id = summary_index.ntotal - 1
        summary_metadata_map[summary_new_id] = {
            "text": summary
        }
        faiss.write_index(summary_index, f"{summary_index_name}.index")
        with open(f"{summary_index_name}.pkl", "wb") as f:
            pickle.dump(summary_metadata_map, f)


def init_client():
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="token-abc123",
    )

    MODEL_PATH = "/share/project/models_cache/bge-m3"
    bge_model = SentenceTransformer(MODEL_PATH, device='cuda:4')

    return client, bge_model


def apply_chat_qwen2vl(image):
    with open("prompt/vlm_image_caption_prompt_zh.txt", "r") as f:
        prompt = f.read()
    messages =  [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image}}
                        ],
                    }
                ]
    
    return messages


def analyze_response_message(response, user_name: str):
    logger.info(f"response: {response}")
    try:
        response = extract_dict(response)
    except Exception as e:
        response = {"response": response}
        logging.info(f"error: {e}")
    image_description = response.get("image_description", response)
    image_summary = response.get("image_summary", response)
    user_preference = response.get("user_preference", None)

    user_preference = user_preference if type(user_preference) == str else None

    if user_preference is not None:
        try:
            if user_preference.startswith("用户"):
                user_preference = user_preference.replace("用户", user_name)
            else:
                user_preference = f"{user_name} " + user_preference
        except Exception as e:
            user_preference = f"{user_name} " + user_preference
            logging.info(f"error: {e}")

    return image_description, image_summary, user_preference


def find_user_name(user_id: str) -> str:
    with open("server/service/name_map.json", "r") as f:
        name_map = json.load(f)

    user_name = name_map.get(user_id, "James")
    return user_name

def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler('omnimate_server.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger