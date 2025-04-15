export CUDA_VISIBLE_DEVICES=0,1,2,3
vllm serve /share/project/models_cache/Qwen2.5-VL-32B-Instruct \
 --dtype auto \
 --api-key token-abc123 \
 --tensor-parallel-size 4 \
 --served-model-name Qwen2.5-VL-32B-Instruct \
 --max-num-batched-tokens 32768 \