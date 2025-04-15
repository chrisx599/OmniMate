export CUDA_VISIBLE_DEVICES=4,5,6,7
vllm serve /share/project/models_cache/Qwen2.5-14B-Instruct-1M \
 --dtype auto \
 --api-key token-abc123 \
 --tensor-parallel-size 4 \
 --served-model-name Qwen2.5-14B-Instruct-1M \
 --port 8001 \
 --max-model-len 1010000 \
 --enable-auto-tool-choice \
 --tool-call-parser hermes \