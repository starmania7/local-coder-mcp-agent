# Local Coder MCP Agent

This project packages a local coding agent workflow:

1. A Qwen coding model runs locally behind an OpenAI-compatible `/v1/chat/completions` API.
2. A Python worker talks to that local API with the OpenAI SDK.
3. A `local-coder` MCP server exposes `delegate_to_local_coder` to Codex.
4. Codex delegates implementation tasks to the local worker, then reviews tests and diffs itself.

No model weights are included. Use your own local model directory through `MODEL_DIR`.

## Architecture

```text
Codex
  -> MCP tool: delegate_to_local_coder(task, workspace, max_steps)
    -> mcp_servers.local_coder.server
      -> workers.coding.worker.CodingWorker
        -> OpenAI-compatible local model server
        -> restricted file/test/git tools inside the requested workspace
```

The worker can list files, read files, write files, patch exact text, run pytest,
run a small allowlist of commands, search text, inspect git status, and inspect
git diff. It refuses paths outside the selected workspace.

## Install

```bash
git clone <your-repo-url>
cd local-coder-mcp-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev,mlx]"
cp .env.example .env
```

Edit `.env`:

```bash
MODEL_DIR=${HOME}/models/Qwen3-Coder-30B-A3B-Instruct-4bit
ALLOWED_WORKSPACE_ROOT=${HOME}/AI/projects
LOCAL_CODER_BASE_URL=http://127.0.0.1:8080/v1
LOCAL_CODER_MODEL=default_model
LOCAL_CODER_API_KEY=local
```

`ALLOWED_WORKSPACE_ROOT` is the directory tree the worker is allowed to edit.
For multiple roots, use `ALLOWED_WORKSPACE_ROOTS` separated by `:` on macOS/Linux.

## Start The Model Server

For an MLX model on Apple Silicon:

```bash
source .venv/bin/activate
./scripts/start_qwen3_coder_server.sh
```

The script starts:

```bash
python -m mlx_lm.server \
  --model "${MODEL_DIR}" \
  --host 127.0.0.1 \
  --port 8080 \
  --max-tokens 4096 \
  --temp 0
```

Any OpenAI-compatible server works if it exposes
`http://127.0.0.1:8080/v1/chat/completions`, or if you update
`LOCAL_CODER_BASE_URL`.

## Start The MCP Server Manually

```bash
source .venv/bin/activate
./scripts/start_local_coder_mcp.sh
```

Normally Codex starts the MCP server for you from `config.toml`.

## Configure Codex MCP

Copy the `local-coder` block from `config.example.toml` into your Codex
`config.toml`, then replace placeholders with local values:

```toml
[mcp_servers.local-coder]
enabled = true
command = "${PROJECT_ROOT}/.venv/bin/python"
args = ["-m", "mcp_servers.local_coder.server"]
cwd = "${PROJECT_ROOT}"

[mcp_servers.local-coder.env]
LOCAL_CODER_BASE_URL = "http://127.0.0.1:8080/v1"
LOCAL_CODER_MODEL = "default_model"
LOCAL_CODER_API_KEY = "local"
ALLOWED_WORKSPACE_ROOT = "${ALLOWED_WORKSPACE_ROOT}"
```

Use real local paths only in your private Codex config, never in committed files.

## Delegate A Task From Codex

Example prompt to Codex:

```text
Use the local-coder MCP server and specifically call delegate_to_local_coder.

Workspace:
${ALLOWED_WORKSPACE_ROOT}/sandbox

Task:
Add multiply(a: int, b: int) -> int to calculator.py.

Requirements:
- Do not change add(), subtract(), or divide().
- Add pytest coverage for multiply().
- Run all tests.
- Inspect git diff before finishing.

After the local worker completes the task, review its changes yourself.
Do not implement the change yourself unless the local worker fails.
```

The included `examples/sandbox` folder is a tiny pytest project for smoke tests.

## Common Errors

### Workspace is not inside an allowed root

Set `ALLOWED_WORKSPACE_ROOT` or `ALLOWED_WORKSPACE_ROOTS` so the requested
workspace is inside an approved directory. This is intentional: the worker
should not be allowed to edit arbitrary local files.

### Worker exceeded maximum number of steps

Increase `max_steps` for larger tasks, or split the task into smaller steps.
Good local-worker tasks are specific and verifiable.

### Model returned no usable text

The local model server returned a response without usable `content`,
`reasoning_content`, `reasoning`, or `thinking`. Try:

- Confirm the server implements OpenAI-compatible chat completions.
- Set `LOCAL_CODER_ENABLE_THINKING=false`.
- Reduce task size.
- Test the server with a direct `/v1/chat/completions` request.

### Connection failed

Confirm the model server is running, the port matches `LOCAL_CODER_BASE_URL`,
and no firewall or proxy is intercepting localhost traffic.

## Security Notes

- Do not commit `.env`, private Codex config files, model weights, logs, keys, or
  generated caches.
- Keep `ALLOWED_WORKSPACE_ROOT` narrow.
- The local worker can edit and run limited commands inside allowed workspaces;
  review every diff before accepting changes.
- Keep the API server bound to `127.0.0.1` unless you have a separate network
  security plan.
- This repository intentionally uses placeholders such as `${HOME}`,
  `${MODEL_DIR}`, `${PROJECT_ROOT}`, and `${ALLOWED_WORKSPACE_ROOT}`.

## Run Checks

```bash
python -m pytest -q
python -m py_compile \
  mcp_servers/local_coder/server.py \
  workers/coding/client.py \
  workers/coding/parser.py \
  workers/coding/tools.py \
  workers/coding/worker.py
```
