"""Anthropic Claude client for the agent harness."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Generator

import anthropic

from ..messages import StreamChunk, ToolCallDelta
from .base import BaseModelClient

logger = logging.getLogger(__name__)


class AnthropicClient(BaseModelClient):
    """Client for Anthropic's Claude models via the Messages API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 16384,
        base_url: str | None = None,
    ):
        self.model = model
        self.max_tokens = max_tokens

        client_kwargs = {"api_key": api_key}
        if base_url:
            if base_url.endswith("/v1/messages"):
                base_url = base_url.rsplit("/v1/messages", 1)[0]
            elif base_url.endswith("/v1"):
                base_url = base_url.rsplit("/v1", 1)[0]
            client_kwargs["base_url"] = base_url

        self.client = anthropic.Anthropic(**client_kwargs)

    def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Generator[StreamChunk, None, None]:
        system_prompt = None
        conversation_messages = messages
        if messages and messages[0].get("role") == "system":
            system_prompt = messages[0].get("content", "")
            conversation_messages = messages[1:]

        anthropic_messages = self._convert_messages(conversation_messages)
        anthropic_tools = self._convert_tools(tools) if tools else None

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": anthropic_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if anthropic_tools:
            kwargs["tools"] = anthropic_tools

        with self.client.messages.stream(**kwargs) as stream:
            current_tool_index = -1

            for event in stream:
                if event.type == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool_index += 1
                        yield StreamChunk(
                            tool_call=ToolCallDelta(
                                index=current_tool_index,
                                id=block.id,
                                name=block.name,
                                arguments=None,
                            )
                        )

                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        yield StreamChunk(text=delta.text)
                    elif delta.type == "input_json_delta":
                        if current_tool_index >= 0:
                            yield StreamChunk(
                                tool_call=ToolCallDelta(
                                    index=current_tool_index,
                                    id=None,
                                    name=None,
                                    arguments=delta.partial_json,
                                )
                            )

                elif event.type == "message_delta":
                    stop_reason = event.delta.stop_reason
                    if stop_reason == "end_turn":
                        yield StreamChunk(finish_reason="stop")
                    elif stop_reason == "tool_use":
                        yield StreamChunk(finish_reason="tool_calls")
                    elif stop_reason:
                        yield StreamChunk(finish_reason=stop_reason)

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        pending_tool_results: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "user":
                if pending_tool_results:
                    result.append({"role": "user", "content": pending_tool_results})
                    pending_tool_results = []
                anthropic_content = self._convert_content(content)
                result.append({"role": "user", "content": anthropic_content})

            elif role == "assistant":
                if pending_tool_results:
                    result.append({"role": "user", "content": pending_tool_results})
                    pending_tool_results = []

                assistant_content = []
                if content:
                    if isinstance(content, str):
                        assistant_content.append({"type": "text", "text": content})
                    elif isinstance(content, list):
                        for part in content:
                            if part.get("type") == "text":
                                assistant_content.append({"type": "text", "text": part.get("text", "")})

                for tc in msg.get("tool_calls", []):
                    func = tc.get("function", {})
                    args_str = func.get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except json.JSONDecodeError:
                        args = {}
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tc.get("id"),
                        "name": func.get("name"),
                        "input": args,
                    })

                if assistant_content:
                    result.append({"role": "assistant", "content": assistant_content})

            elif role == "tool":
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": msg.get("tool_call_id"),
                    "content": content if isinstance(content, str) else json.dumps(content),
                }
                pending_tool_results.append(tool_result)

        if pending_tool_results:
            result.append({"role": "user", "content": pending_tool_results})

        return result

    def _convert_content(self, content: str | list[dict[str, Any]] | None) -> str | list[dict[str, Any]]:
        if content is None:
            return ""
        if isinstance(content, str):
            return content

        result = []
        for block in content:
            block_type = block.get("type")
            if block_type == "text":
                result.append({"type": "text", "text": block.get("text", "")})
            elif block_type == "image_url":
                image_url = block.get("image_url", {})
                url = image_url.get("url", "")
                if url.startswith("data:"):
                    match = re.match(r"data:([^;]+);base64,(.+)", url)
                    if match:
                        result.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": match.group(1),
                                "data": match.group(2),
                            },
                        })
                else:
                    result.append({"type": "image", "source": {"type": "url", "url": url}})

        return result if result else ""

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                result.append({
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
        return result
