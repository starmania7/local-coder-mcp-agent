from __future__ import annotations

import logging
from pathlib import Path

from workers.coding.client import LocalModelClient
from workers.coding.parser import ActionParseError, parse_action
from workers.coding.tools import WorkspaceTools


logger = logging.getLogger(__name__)


class CodingWorker:
    def __init__(
        self,
        workspace: str,
        max_steps: int = 50,
    ) -> None:
        self.workspace = workspace
        self.max_steps = max_steps

        self.client = LocalModelClient()
        self.tools = WorkspaceTools(workspace)

        prompt_path = Path(__file__).parent / "prompts" / "system.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    def _extract_text(self, response) -> str:
        message = response.choices[0].message

        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content

        for field in ("reasoning_content", "reasoning", "thinking"):
            value = getattr(message, field, None)
            if isinstance(value, str) and value.strip():
                return value

        extra = getattr(message, "model_extra", None)
        if isinstance(extra, dict):
            for field in ("reasoning_content", "reasoning", "thinking", "content"):
                value = extra.get(field)
                if isinstance(value, str) and value.strip():
                    return value

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            return str(tool_calls)

        try:
            dumped = message.model_dump()
        except Exception:
            dumped = repr(message)

        raise RuntimeError("Model returned no usable text.\n" f"Raw message: {dumped}")

    def run(self, task: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": f"Workspace: {self.workspace}\n\nTask:\n{task}",
            },
        ]

        for step in range(1, self.max_steps + 1):
            logger.info("=== STEP %s ===", step)

            response = self.client.chat(messages, max_tokens=4096)
            text = self._extract_text(response)

            logger.info("MODEL:\n%s", text)

            try:
                action = parse_action(text)
            except ActionParseError as exc:
                messages.append({"role": "assistant", "content": text})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was invalid. "
                            "Return exactly one valid JSON action."
                        ),
                    }
                )
                logger.warning("Action parse error: %s", exc)
                continue

            if action["action"] == "finish":
                return action.get("summary", "Task completed.")

            try:
                result = self.tools.execute(action)
            except Exception as exc:
                result = f"TOOL ERROR: {type(exc).__name__}: {exc}"

            logger.info("TOOL RESULT:\n%s", result)

            messages.append({"role": "assistant", "content": text})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Tool result:\n"
                        f"{result}\n\n"
                        "Continue the task. Return exactly one JSON action."
                    ),
                }
            )

        raise RuntimeError("Worker exceeded maximum number of steps.")
