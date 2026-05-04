"""OpenAI-compatible client for custom endpoints."""

from __future__ import annotations

import logging
from typing import Any, Generator

from openai import OpenAI

from ..messages import StreamChunk, ToolCallDelta
from .base import BaseModelClient

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(BaseModelClient):
    """Client for any OpenAI-compatible API endpoint."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o",
    ):
        self.model = model

        if base_url.endswith("/responses"):
            base_url = base_url.rsplit("/responses", 1)[0]
        if not base_url.endswith("/v1") and "/v1" not in base_url:
            base_url = base_url.rstrip("/") + "/v1"

        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Generator[StreamChunk, None, None]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)

        for chunk in response:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if delta.content:
                yield StreamChunk(text=delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    yield StreamChunk(
                        tool_call=ToolCallDelta(
                            index=tc.index,
                            id=tc.id,
                            name=tc.function.name if tc.function else None,
                            arguments=tc.function.arguments if tc.function else None,
                        )
                    )

            if choice.finish_reason:
                yield StreamChunk(finish_reason=choice.finish_reason)
