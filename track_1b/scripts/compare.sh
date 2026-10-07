#!/bin/sh
# Local convenience runner (not used by judges): baseline model inference, then judge and score.
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
M=qwen3-8b-q8_0
R=data/results/responses_$M.jsonl
IMG=ghcr.io/ggml-org/llama.cpp@sha256:af8c29600d1de84945de13fa7f126d06fdae16c4b19dc7db1c69c74287eae257
log() { echo "$(date +%T) $*"; }
log "inference $M"
python3 -m swisscivicqa.infer --base-url http://127.0.0.1:8091/v1 --model $M --out $R \
  --extra-body '{"chat_template_kwargs": {"enable_thinking": false}}'
log "inference rows: $(wc -l < $R)"
docker stop qwen-llm >/dev/null || true
docker rm -f apertus-judge >/dev/null 2>&1 || true
docker run -d --name apertus-judge -p 127.0.0.1:8089:8080 -v "$HOME/models:/models:ro" $IMG \
  -m /models/gemma-3-12b-it-Q4_K_M.gguf -c 4096 -t 14 --jinja --host 0.0.0.0 --port 8080 >/dev/null
until curl -sf http://127.0.0.1:8089/health >/dev/null; do sleep 5; done
log "judging"
python3 -m swisscivicqa.grade --responses $R --judge-url http://127.0.0.1:8089/v1 --judge-model gemma-3-12b-it-q4_k_m
log "judgment rows: $(wc -l < data/results/judgments_$M.jsonl)"
docker stop apertus-judge >/dev/null || true
log "done"
