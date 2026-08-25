from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class WorkspaceTools:
    def __init__(self, workspace: str) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.command_timeout = int(os.getenv("LOCAL_CODER_COMMAND_TIMEOUT", "120"))
        self.search_limit = int(os.getenv("LOCAL_CODER_SEARCH_LIMIT", "20000"))

        if not self.workspace.exists():
            raise ValueError(f"Workspace does not exist: {self.workspace}")

        if not self.workspace.is_dir():
            raise ValueError(f"Workspace is not a directory: {self.workspace}")

    def _safe_path(self, relative_path: str) -> Path:
        path = (self.workspace / relative_path).resolve()

        if self.workspace not in path.parents and path != self.workspace:
            raise PermissionError("Access outside workspace is forbidden.")

        return path

    def list_files(self) -> list[str]:
        result = []

        for path in self.workspace.rglob("*"):
            if (
                path.is_file()
                and ".git" not in path.parts
                and "__pycache__" not in path.parts
                and ".pytest_cache" not in path.parts
                and ".venv" not in path.parts
                and "node_modules" not in path.parts
            ):
                result.append(str(path.relative_to(self.workspace)))

        return sorted(result)

    def read_file(self, relative_path: str) -> str:
        path = self._safe_path(relative_path)

        if not path.is_file():
            raise FileNotFoundError(relative_path)

        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> None:
        path = self._safe_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def git_status(self) -> str:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + result.stderr

    def git_diff(self) -> str:
        result = subprocess.run(
            ["git", "diff", "--"],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout + result.stderr

    def run_pytest(self) -> str:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=self.command_timeout,
        )
        return self._format_result(result)

    def execute(self, action: dict) -> str:
        name = action["action"]

        if name == "list_files":
            return "\n".join(self.list_files())

        if name == "read_file":
            return self.read_file(action["path"])

        if name == "write_file":
            self.write_file(action["path"], action["content"])
            return f"Wrote {action['path']}"

        if name == "run_pytest":
            return self.run_pytest()

        if name == "git_status":
            return self.git_status()

        if name == "git_diff":
            return self.git_diff()

        if name == "apply_patch":
            return self.apply_patch(
                action["path"],
                action["old_text"],
                action["new_text"],
            )

        if name == "run_command":
            return self.run_command(action["command"])

        if name == "search_text":
            return self.search_text(action["query"])

        raise ValueError(f"Unsupported tool action: {name}")

    def apply_patch(self, relative_path: str, old_text: str, new_text: str) -> str:
        path = self._safe_path(relative_path)

        if not path.is_file():
            raise FileNotFoundError(relative_path)

        content = path.read_text(encoding="utf-8")
        count = content.count(old_text)

        if count == 0:
            raise ValueError(f"Target text not found in {relative_path}")

        if count > 1:
            raise ValueError(f"Target text is ambiguous: found {count} matches")

        updated = content.replace(old_text, new_text, 1)
        path.write_text(updated, encoding="utf-8")
        return f"Patched {relative_path}"

    ALLOWED_COMMANDS = {
        "python",
        "python3",
        "pytest",
        "ruff",
        "mypy",
        "uv",
    }

    def run_command(self, command: list[str], timeout: int | None = None) -> str:
        if not command:
            raise ValueError("Empty command.")

        executable = command[0]

        if executable not in self.ALLOWED_COMMANDS:
            raise PermissionError(f"Command not allowed: {executable}")

        result = subprocess.run(
            command,
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=timeout or self.command_timeout,
        )
        return self._format_result(result)

    def search_text(self, query: str) -> str:
        result = subprocess.run(
            [
                "grep",
                "-RIn",
                "--exclude-dir=.git",
                "--exclude-dir=.venv",
                "--exclude-dir=__pycache__",
                "--exclude-dir=.pytest_cache",
                query,
                ".",
            ],
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout[: self.search_limit]

    @staticmethod
    def _format_result(result: subprocess.CompletedProcess[str]) -> str:
        return (
            f"exit_code={result.returncode}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )
