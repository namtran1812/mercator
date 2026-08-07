from __future__ import annotations

import json
import os
from typing import Any

import requests


class LLMClient:
    def __init__(self) -> None:
        self.provider = os.getenv(
            "MERCATOR_LLM_PROVIDER",
            "ollama",
        )

        self.base_url = os.getenv(
            "MERCATOR_LLM_BASE_URL",
            "http://127.0.0.1:11434",
        ).rstrip("/")

        self.model = os.getenv(
            "MERCATOR_LLM_MODEL",
            "qwen3:4b",
        )

        self.timeout = int(
            os.getenv(
                "MERCATOR_LLM_TIMEOUT_SECONDS",
                "120",
            )
        )

        if self.provider != "ollama":
            raise ValueError(
                "Only the ollama provider "
                "is currently supported."
            )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        think: bool = False,
    ) -> str:
        user_content = user_prompt

        if not think:
            user_content += "\n\n/no_think"

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content":
                            system_prompt,
                    },
                    {
                        "role": "user",
                        "content":
                            user_content,
                    },
                ],
                "stream": False,

                "options": {
                    "temperature": 0,
                    "num_predict": 180,
                },
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()

        return (
            payload
            .get("message", {})
            .get("content", "")
            .strip()
        )

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        think: bool = False,
    ) -> dict[str, Any]:
        user_content = (
            user_prompt
            + "\n\nReturn one complete JSON object only."
        )

        if not think:
            user_content += "\n/no_think"

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content":
                            system_prompt,
                    },
                    {
                        "role": "user",
                        "content":
                            user_content,
                    },
                ],
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0,
                    "num_predict": 320,
                },
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        payload = response.json()

        raw = (
            payload
            .get("message", {})
            .get("content", "")
            .strip()
        )

        try:
            return json.loads(raw)

        except json.JSONDecodeError as error:
            raise ValueError(
                "LLM returned invalid JSON:\n"
                + raw
            ) from error
