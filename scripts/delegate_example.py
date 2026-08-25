from __future__ import annotations

from mcp_servers.local_coder.server import delegate_to_local_coder


if __name__ == "__main__":
    result = delegate_to_local_coder(
        task=(
            "Add multiply(a: int, b: int) -> int to calculator.py, "
            "add pytest coverage, run tests, and inspect git diff."
        ),
        workspace="examples/sandbox",
        max_steps=20,
    )
    print(result)
