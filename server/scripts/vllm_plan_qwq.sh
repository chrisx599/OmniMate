export CUDA_VISIBLE_DEVICES=4,5,6,7
vllm serve /share/project/models_cache/QwQ-32B \
 --dtype auto \
 --api-key token-abc123 \
 --tensor-parallel-size 4 \
 --served-model-name QwQ-32B \
 --port 8001 \
 --max-model-len 131072 \
 --enable-auto-tool-choice \
 --tool-call-parser hermes \