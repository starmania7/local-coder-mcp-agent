from __future__ import annotations

import json
from typing import Any


class ActionParseError(Exception):
    pass


def parse_action(text: str) -> dict[str, Any]:
    text = text.strip()

    if text.startswith("```"):
        text = text.strip("`")

        if text.startswith("json"):
            text = text[4:].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ActionParseError(f"Model did not return valid JSON:\n{text}") from exc

    if not isinstance(data, dict):
        raise ActionParseError("Action must be a JSON object.")

    action = data.get("action")
    allowed = {
        "list_files",
        "read_file",
        "write_file",
        "run_pytest",
        "git_status",
        "git_diff",
        "finish",
        "apply_patch",
        "run_command",
        "search_text",
    }

    if action not in allowed:
        raise ActionParseError(f"Unknown action: {action}")

    return data
