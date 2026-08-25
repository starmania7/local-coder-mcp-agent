from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

try:
    from mcp.server import MCPServer
except ImportError:  # pragma: no cover - depends on installed mcp version
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError:

        class MCPServer:  # type: ignore[no-redef]
            def __init__(self, _name: str) -> None:
                pass

            def tool(self):
                def decorator(func):
                    return func

                return decorator

            def run(self) -> None:
                raise RuntimeError(
                    "The 'mcp' package is required to run the MCP server. "
                    "Install with: python -m pip install -e ."
                )

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

server = MCPServer("local-coder")


def _split_roots(value: str) -> list[str]:
    normalized = value.replace(",", os.pathsep)
    return [part.strip() for part in normalized.split(os.pathsep) if part.strip()]


def allowed_roots() -> list[Path]:
    values: list[str] = []

    if os.getenv("ALLOWED_WORKSPACE_ROOT"):
        values.append(os.environ["ALLOWED_WORKSPACE_ROOT"])

    if os.getenv("ALLOWED_WORKSPACE_ROOTS"):
        values.extend(_split_roots(os.environ["ALLOWED_WORKSPACE_ROOTS"]))

    if not values:
        values.append(str(Path.cwd() / "examples"))

    return [Path(value).expanduser().resolve() for value in values]


def validate_workspace(workspace: str) -> str:
    path = Path(workspace).expanduser().resolve()

    if not path.exists():
        raise ValueError(f"Workspace does not exist: {path}")

    if not path.is_dir():
        raise ValueError(f"Workspace is not a directory: {path}")

    roots = allowed_roots()
    allowed = any(path == root or root in path.parents for root in roots)

    if not allowed:
        safe_roots = ", ".join(str(root) for root in roots)
        raise PermissionError(
            "Workspace is not inside an allowed root. "
            f"Set ALLOWED_WORKSPACE_ROOT or ALLOWED_WORKSPACE_ROOTS. "
            f"Allowed roots: {safe_roots}"
        )

    return str(path)


@server.tool()
def delegate_to_local_coder(
    task: str,
    workspace: str,
    max_steps: int = 20,
) -> str:
    """
    Delegate a coding implementation task to the local Qwen worker.

    The worker can inspect project files, patch code, create files, run tests,
    and inspect git diff. Codex should review the result afterwards.
    """

    safe_workspace = validate_workspace(workspace)
    from workers.coding.worker import CodingWorker

    worker = CodingWorker(workspace=safe_workspace, max_steps=max_steps)
    return worker.run(task)


if __name__ == "__main__":
    server.run()
