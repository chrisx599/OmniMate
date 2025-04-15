from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import uvicorn
import faiss
import numpy as np
import pickle
import logging
import uuid
import re
import json
import os
from mem0 import Memory
from openai import OpenAI
from utils import check_embedding, init_memory

logger = logging.getLogger()

os.environ["OPENAI_BASE_URL"] = "http://localhost:8001/v1"
os.environ["OPENAI_API_KEY"] = "token-abc123"
USER_FILE = "server/service/id_map.json"

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


with open(USER_FILE, "r") as f:
    user_dict = json.load(f)
with open("server/service/name_map.json", "r") as f:
    name_dict = json.load(f)


def save_user(user_dict):
    """保存用户数据到JSONL文件"""
    with open(USER_FILE, 'w', encoding='utf-8') as f:
        f.write(json.dumps(user_dict, f, ensure_ascii=False) + '\n')
    logger.info(f"update user data")

def generate_user_id():
    return str(uuid.uuid4())


# index_file = "memory.index"
# index = faiss.read_index(index_file)
# with open("memory.pkl", "rb") as f:
#     metadata_map = pickle.load(f)

mcp = FastMCP("OmniMate")

# from sentence_transformers import SentenceTransformer
# MODEL_PATH = "/share/project/models_cache/bge-m3"
# bge_model = SentenceTransformer(MODEL_PATH, device='cuda:4')

openai_api_key  = "token-abc123"
openai_api_base = "http://localhost:8002/v1"

bge_model = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

def bge_encode(query):
    responses = bge_model.embeddings.create(
        input=[
            query
        ],
        model="bge-m3",
    )

    return responses.data[0].embedding

def search_similar(query_embedding, user_id, task, k=5):
    query_embedding = check_embedding(query_embedding)

    description_index, description_metadata_map, summary_index, summary_metadata_map = init_memory(user_id)

    if task == "summary":
        index = summary_index
        metadata_map = summary_metadata_map
    else:
        index = description_index
        metadata_map = description_metadata_map
    distances, indices = index.search(query_embedding.astype(np.float32), k)

    results = []
    logging.info("检索结果 (Faiss ID, 距离, 元数据):")
    for i in range(indices.shape[1]): # 遍历返回的 k 个结果
        faiss_id = indices[0, i]
        if faiss_id == -1: # 可能索引为空或 k 值过大
            continue
        dist = distances[0, i]

        meta = metadata_map.get(faiss_id, "元数据未找到")
        logging.info(f"- ID: {faiss_id}, 距离: {dist:.4f}, 元数据: {meta}")
        results.append({"id": faiss_id, "distance": dist, "metadata": meta})
    return results


@mcp.tool()
async def process_user_name(name: str) -> tuple[str, str]:
    """
    用户第一次输入自己的名字时，通过这个函数可以得到关于用户的user_id和偏好信息。
    
    参数:
        name (str): 用户输入的名字
        
    返回:
        str: 包含用户名、用户ID和偏好信息的格式化字符串
    """
    if name in user_dict:
        user_id = user_dict[name]
        res = mem_graph.get_all(user_id)
        relations = res["relations"]
        prompt = f"{name}您好，您的user_id是{user_id}，这是您的偏好信息：\n"
        for relation in relations:
            if relation["source"] == user_id:
                relation["source"] = name
            temp = relation["source"] + " " + relation["relationship"] + " " + relation["target"]
            prompt += temp + "\n"
        return prompt

    else:
        # user_id = generate_user_id()
        # user_dict[name] = user_id
        # save_user(user_dict)  # 保存新用户数据
        # logger.info(f"新用户注册: {name} -> {user_id}")
        prompt = f"{name}您好，您还没有注册，请先到系统注册\n"
        return prompt


@mcp.tool()
async def retrieve_memory(user_query: str, user_id: str, task: str) -> str:
    """
    根据用户的查询和用户ID以及任务类型，检索到关于用户的信息。当获取到user_id，之后用户提问，都可以调用这个函数来获取到用户的信息。

    参数:
        user_query (str): 用户输入的提问内容
        user_id (str): 用户的ID
        task (str): 用户的任务类型，有 "summary"|"normal"|"preference" 三种类型,如果用户的查询包含一些关于总结的内容，任务的类型就为"summary";如果用户的查询中有一些关于用户喜好的内容，任务类型就为"preference";如果用户问一些比较寻常细节的问题，任务类型为"normal"。
    返回:
        str: 返回和用户相关的信息
    """

    if task == "summary":
        query_vec = bge_encode(user_query)
        query_vec = np.expand_dims(query_vec, axis=0)
        query_vec = np.array(query_vec).astype('float32')
        result = search_similar(query_vec, user_id, task=task, k=10)
        description_prompt = "以上是用户计算机的一些截图信息，与用户当前的问题相关，请根据这些信息回答用户的问题。"
        res_text = [item["metadata"]["text"] for item in result]
        res_text = "\n".join(res_text)
        prompt = res_text + "\n" + description_prompt
    elif task == "preference":
        res = mem_graph.get_all(user_id)
        name = name_dict[user_id]
        relations = res["relations"]
        prompt = f"以下这些内容是关于您的一些偏好信息：\n"
        for relation in relations:
            if relation["source"] == user_id:
                relation["source"] = name
            temp = relation["source"] + " " + relation["relationship"] + " " + relation["target"]
            prompt += temp + "\n"
        return prompt
    else:
        # query_vec = bge_model.encode(user_query)
        query_vec = bge_encode(user_query)
        query_vec = np.expand_dims(query_vec, axis=0)
        query_vec = np.array(query_vec).astype('float32')
        result = search_similar(query_vec, user_id, task=task)
        description_prompt = "以上是用户计算机的一些截图信息，与用户当前的问题相关，请根据这些信息回答用户的问题。"
        res_text = [item["metadata"]["text"] for item in result]
        res_text = "\n".join(res_text)
        prompt = res_text + "\n" + description_prompt

    return prompt

if __name__ == "__main__":
    # SSE 端点通常是 /sse
    uvicorn.run(mcp.sse_app(), host="127.0.0.1", port=12345)

