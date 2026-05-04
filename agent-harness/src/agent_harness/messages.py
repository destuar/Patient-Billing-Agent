"""Message types for the agent harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ToolCall:
    """A tool call requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    """A conversation message."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_api_format(self) -> dict[str, Any]:
        """Convert to OpenAI API message format."""
        msg: dict[str, Any] = {"role": self.role}

        if self.content is not None:
            msg["content"] = self.content

        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                }
                for tc in self.tool_calls
            ]

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        if self.name:
            msg["name"] = self.name

        return msg


@dataclass
class StreamChunk:
    """A chunk from a streaming response."""

    text: str | None = None
    tool_call: ToolCallDelta | None = None
    finish_reason: str | None = None


@dataclass
class ToolCallDelta:
    """Incremental tool call data from streaming."""

    index: int
    id: str | None = None
    name: str | None = None
    arguments: str | None = None
