from __future__ import annotations

import os

from openai import OpenAI


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class LocalModelClient:
    def __init__(self) -> None:
        self.base_url = os.getenv(
            "LOCAL_CODER_BASE_URL",
            "http://127.0.0.1:8080/v1",
        )
        self.model = os.getenv("LOCAL_CODER_MODEL", "default_model")
        self.api_key = os.getenv("LOCAL_CODER_API_KEY", "local")
        self.temperature = float(os.getenv("LOCAL_CODER_TEMPERATURE", "0"))
        self.enable_thinking = _env_bool("LOCAL_CODER_ENABLE_THINKING", False)

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
    ):
        token_limit = max_tokens or int(os.getenv("LOCAL_CODER_MAX_TOKENS", "4096"))

        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=token_limit,
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": self.enable_thinking,
                },
            },
        )
