#!/bin/sh
# Local convenience runner: wait for compare.sh (PID $1), then compute pairwise cross-lingual agreement for each model.
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
IMG=ghcr.io/ggml-org/llama.cpp@sha256:af8c29600d1de84945de13fa7f126d06fdae16c4b19dc7db1c69c74287eae257
log() { echo "$(date +%T) $*"; }
if [ -n "${1:-}" ]; then while kill -0 "$1" 2>/dev/null; do sleep 30; done; fi
docker rm -f apertus-judge >/dev/null 2>&1 || true
docker run -d --name apertus-judge -p 127.0.0.1:8089:8080 -v "$HOME/models:/models:ro" $IMG \
  -m /models/gemma-3-12b-it-Q4_K_M.gguf -c 4096 -t 14 --jinja --host 0.0.0.0 --port 8080 >/dev/null
until curl -sf http://127.0.0.1:8089/health >/dev/null; do sleep 5; done
for M in apertus-v1.5-8b-text-q8_0 qwen3-8b-q8_0; do
  log "pairs $M"
  python3 -m swisscivicqa.pairs --responses data/results/responses_$M.jsonl \
    --judge-url http://127.0.0.1:8089/v1 --judge-model gemma-3-12b-it-q4_k_m
done
docker stop apertus-judge >/dev/null || true
log "done"
