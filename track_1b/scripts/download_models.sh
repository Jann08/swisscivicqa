#!/bin/sh
# Download the exact GGUF files used for the published results and verify their SHA-256.
set -eu
mkdir -p models
dl() {
  url=$1; file=$2; sum=$3
  if [ ! -f "models/$file" ]; then curl -L --fail --retry 5 -o "models/$file.part" "$url" && mv "models/$file.part" "models/$file"; fi
  echo "$sum  models/$file" | sha256sum -c -
}
dl https://huggingface.co/andreasmartin/apertus-v1.5-8b-text-Q8_0-GGUF/resolve/main/apertus-v1.5-8b-text-q8_0.gguf \
   apertus-v1.5-8b-text-q8_0.gguf dea904ad80cd725ec89962abae464477f5d8114d1f4377514f381f7dc2ed202d
dl https://huggingface.co/ggml-org/gemma-3-12b-it-GGUF/resolve/main/gemma-3-12b-it-Q4_K_M.gguf \
   gemma-3-12b-it-Q4_K_M.gguf 7bb69bff3f48a7b642355d64a90e481182a7794707b3133890646b1efa778ff5
