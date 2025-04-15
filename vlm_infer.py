from openai import OpenAI
import time
import os
import base64
from io import BytesIO
from PIL import Image # pip install Pillow
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import sys
import json
from datetime import datetime
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
# from milvus_store import MilvusStore

from utils import extract_dict, check_embedding, is_same_already, init_memory

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('omnimate_server.log', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# --- 配置 ---
WATCH_FOLDER = "/share/project/liangzy/infer/video_stream"  # watch folder
MODEL_NAME = "Qwen2.5-VL-7B-Instruct" # --served-model-name
OPENAI_BASE_URL = "http://localhost:8000/v1"
OPENAI_API_KEY = "token-abc123"
# IMAGE_PROMPT = "Please provide a detailed description of the image so that the reader can obtain all the information about the image through your description. Make sure to fully extract any text, numbers, formulas, and code in the image."
with open("prompt/vlm_image_caption_prompt_zh.txt", "r") as f:
    IMAGE_PROMPT = f.read()
MAX_TOKENS = 32768
SUPPORTED_IMAGE_EXT = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
SUPPORTED_TEXT_EXT = ['.txt']

MODEL_PATH = "/share/project/models_cache/bge-m3"
bge_model = SentenceTransformer(MODEL_PATH, device='cuda:4')

# description_index_file = "description_memory.index"
# summary_index_file = "summary_memory.index"
# dimension = 1024
# k = 5

# if os.path.exists(index_file_name):
#     index = faiss.read_index(index_file_name)
#     with open("memory.pkl", "rb") as f:
#         metadata_map = pickle.load(f)
# else:
#     # index = faiss.IndexFlatL2(dimension)
#     index = faiss.IndexFlatIP(dimension)
#     metadata_map = {}
description_index_name="description"
summary_index_name="summary"
description_index, description_metadata_map, summary_index, summary_metadata_map = init_memory(description_index_name, summary_index_name)



client = OpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY
)


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



def trigger_inference(file_path):
    """根据文件类型准备消息并调用 vLLM 推理"""
    logging.info(f"\nwatch new file: {file_path}")
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    messages = []

    try:
        # 处理图片文件
        if file_extension in SUPPORTED_IMAGE_EXT:
            # logging.info(f"image file:")
            base64_uri = image_to_base64_data_uri(file_path)
            if base64_uri:
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": IMAGE_PROMPT},
                            {"type": "image_url", "image_url": {"url": base64_uri}}
                        ],
                    }
                ]
            else:
                logging.info(f"can not handle this file: {file_path}")
                return # 无法编码图片，不进行推理

        # 处理文本文件
        elif file_extension in SUPPORTED_TEXT_EXT:
            # logging.info("文件类型识别为文本，将使用文件内容作为提示。")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                if content:
                    messages = [{"role": "user", "content": content}]
                else:
                    logging.info(f"text file empty: {file_path}")
                    return # 空文件不进行推理
            except Exception as e:
                logging.info(f"read text file error {file_path}: {e}")
                return

        # 不支持的文件类型
        else:
            logging.info(f"can not handle this file type: {file_extension} ({os.path.basename(file_path)})")
            return

        # 如果成功准备了消息，则进行推理
        if messages:
            logging.info(f"using '{MODEL_NAME}' handle '{os.path.basename(file_path)}' inference...")
            start_time = time.time()
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=MAX_TOKENS,
                # 可以添加 temperature, top_p 等参数
            )
            end_time = time.time()
            logging.info(f"complete infer (using: {end_time - start_time:.2f} s)")
            logging.info("-" * 10 + " model response " + "-" * 10)
            # logging.info(completion.choices[0].message.content)

            time_ = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            response = completion.choices[0].message.content
            try:
                response = extract_dict(response)
            except Exception as e:
                response = {"response": response}
                logging.info(f"error: {e}")
            image_description = response.get("image_description", response)
            image_summary = response.get("image_summary", response)
            user_preference = response.get("user_preference", " ")


            dict_ = {
                "time": time_,
                "image_description": image_description,
                "image_summary": image_summary,
                "user_preference": user_preference,
                "file": file_path
            }

            dict_ = {
                "time": time_,
                "image_description": image_description,
                "image_summary": image_summary,
                "user_preference": user_preference,
                "file": file_path
            }

            description_embedding = bge_model.encode(image_description, normalize_embeddings=True)
            summary_embedding = bge_model.encode(image_summary, normalize_embeddings=True)
            with open("memory.jsonl", "a") as f:
              f.write(json.dumps(dict_) + "\n")

            logging.info(f"save to memory.jsonl")

            # if not embedding.flags['C_CONTIGUOUS']: # Faiss 需要 C 连续数组
            #     embedding = np.ascontiguousarray(embedding)
            # if embedding.ndim == 1: # Faiss 需要 2D 数组 (n_vectors, dimension)
            #     embedding = np.expand_dims(embedding, axis=0)
            # embedding = np.array(embedding).astype('float32')

            description_embedding = check_embedding(description_embedding)
            is_same_description = is_same_already(description_embedding, description_index, threshold=0.8)
            summary_embedding = check_embedding(summary_embedding)
            is_same_summary = is_same_already(summary_embedding, summary_index, threshold=0.6)  # TODO: modify summary index

            if not is_same_description:
                description_index.add(description_embedding) # Faiss 通常使用 float32
                escription_new_id = description_index.ntotal - 1 # 获取新向量在 Faiss 中的 ID (通常是总数-1)
                description_metadata_map[escription_new_id] = {
                    "time": time_,
                    "file": file_path,
                    "text": completion.choices[0].message.content
                }
                faiss.write_index(description_index, f"{description_index_name}.index")
                with open(f"{description_index_name}.pkl", "wb") as f:
                    pickle.dump(description_metadata_map, f)
            if not is_same_summary:
                summary_index.add(summary_embedding)
                summary_new_id = summary_index.ntotal - 1 # 获取新向量在 Faiss 中的 ID (通常是总数-1)
                # logging.info(f"111")
                summary_metadata_map[summary_new_id] = {
                    "time": time_,
                    "file": file_path,
                    "text": completion.choices[0].message.content
                }

                logging.info(f"save to faiss index")
                faiss.write_index(summary_index, f"{summary_index_name}.index")
                with open(f"{summary_index_name}.pkl", "wb") as f:
                    pickle.dump(summary_metadata_map, f)
            
            

            logging.info("-" * 30)

    except Exception as e:
        logging.info(f"\nusing '{MODEL_NAME}' error: {e}")


# --- Watchdog 事件处理器 ---
class NewFileHandler(FileSystemEventHandler):
    """仅在文件创建完成时触发推理"""
    def on_created(self, event):
        if not event.is_directory:
            # 添加一点点延迟，确保文件写入完成（尤其对于大文件）
            # 你可能需要根据实际情况调整这个延迟
            time.sleep(0.5)
            trigger_inference(event.src_path)

# --- 主程序 ---
if __name__ == "__main__":
    
    logging.info("try to connecting vllm server...")
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="token-abc123",
    )
    logging.info("sucessfully connecting vllm server...")

    logging.info("available models list:")
    models = client.models.list()
    for model in models.data:
        logging.info(f"- ID: {model.id}") # model.id 通常是你在启动服务器时指定的模型名称

    # 检查监控文件夹是否存在
    if not os.path.isdir(WATCH_FOLDER):
        logging.info(f"error: file '{WATCH_FOLDER}' is not exist")
        exit()

    logging.info(f"start to watch file: {WATCH_FOLDER}")
    logging.info("send ctrl-c to stop")

    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False) # recursive=False 表示不监控子目录
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("\nstoping now")
        observer.stop()
        # 保存记忆系统状态
    observer.join()
    logging.info("watch server closed")

