from mem0 import Memory
import os

os.environ["OPENAI_BASE_URL"] = "http://localhost:8001/v1"
os.environ["OPENAI_API_KEY"] = "token-abc123"


config = {
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


m = Memory.from_config(config_dict=config)


# m.add("I like pizza", user_id="alice")


aa = m.get_all(user_id="api-key123")
print(aa)

bb = m.search("tell me my name.", user_id="api-key123")
print(bb)

# m.delete_all(user_id="alice")