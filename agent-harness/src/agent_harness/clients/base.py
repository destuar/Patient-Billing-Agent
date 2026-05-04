"""Base interface for model clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generator, Protocol

from ..messages import StreamChunk


class ModelClient(Protocol):
    """Protocol for model clients."""

    def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Generator[StreamChunk, None, None]:
        ...


class BaseModelClient(ABC):
    """Abstract base class for model clients."""

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Generator[StreamChunk, None, None]:
        ...

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Non-streaming chat completion."""
        text = ""
        tool_calls: list[dict[str, Any]] = []
        tool_call_buffer: dict[int, dict[str, Any]] = {}

        for chunk in self.chat_stream(messages, tools):
            if chunk.text:
                text += chunk.text

            if chunk.tool_call:
                tc = chunk.tool_call
                if tc.index not in tool_call_buffer:
                    tool_call_buffer[tc.index] = {
                        "id": "",
                        "name": "",
                        "arguments": "",
                    }
                buf = tool_call_buffer[tc.index]
                if tc.id:
                    buf["id"] = tc.id
                if tc.name:
                    buf["name"] = tc.name
                if tc.arguments:
                    buf["arguments"] += tc.arguments

        for idx in sorted(tool_call_buffer.keys()):
            tool_calls.append(tool_call_buffer[idx])

        return text, tool_calls
