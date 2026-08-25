#!/usr/bin/env bash
set -euo pipefail

# Start an OpenAI-compatible local Qwen coding model server with mlx-lm.
# Configure MODEL_DIR in .env or export it before running this script.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -f "${PROJECT_ROOT}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.env"
  set +a
fi

: "${MODEL_DIR:?Set MODEL_DIR to the local model directory. Do not commit model files.}"
: "${LOCAL_CODER_HOST:=127.0.0.1}"
: "${LOCAL_CODER_PORT:=8080}"
: "${LOCAL_CODER_MAX_TOKENS:=4096}"
: "${LOCAL_CODER_TEMPERATURE:=0}"

exec python -m mlx_lm.server \
  --model "${MODEL_DIR}" \
  --host "${LOCAL_CODER_HOST}" \
  --port "${LOCAL_CODER_PORT}" \
  --max-tokens "${LOCAL_CODER_MAX_TOKENS}" \
  --temp "${LOCAL_CODER_TEMPERATURE}"
