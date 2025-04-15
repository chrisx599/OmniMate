export CUDA_VISIBLE_DEVICES=0,1,2,3
vllm serve /share/project/models_cache/bge-m3 \
 --task embed \
 --dtype auto \
 --api-key token-abc123 \
 --tensor-parallel-size 4 \
 --served-model-name bge-m3 \
 --port 8002 \