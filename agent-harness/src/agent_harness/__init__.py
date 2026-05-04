"""Agent Harness - A simple, reusable agent loop.

LLM + loop + tools = agent

Exports:
    - AgentHarness: The core agent loop
    - Message, ToolCall, StreamChunk: Data structures
    - Tool, tool, create_tool: Tool definition helpers
    - Hook, HookResult: Safety check base classes
    - ModelClient, OpenAICompatibleClient: LLM provider interfaces
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .clients import BaseModelClient, ModelClient
from .core import AgentHarness
from .hooks import Hook, HookResult
from .messages import Message, StreamChunk, ToolCall, ToolCallDelta
from .tools import Tool, create_tool, tool

if TYPE_CHECKING:
    from .clients.anthropic import AnthropicClient
    from .clients.azure import AzureModelClient
    from .clients.openai_compat import OpenAICompatibleClient


def __getattr__(name: str):
    if name == "OpenAICompatibleClient":
        from .clients.openai_compat import OpenAICompatibleClient

        return OpenAICompatibleClient
    if name == "AzureModelClient":
        from .clients.azure import AzureModelClient

        return AzureModelClient
    if name == "AnthropicClient":
        from .clients.anthropic import AnthropicClient

        return AnthropicClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AgentHarness",
    "Message",
    "StreamChunk",
    "ToolCall",
    "ToolCallDelta",
    "Tool",
    "tool",
    "create_tool",
    "Hook",
    "HookResult",
    "ModelClient",
    "BaseModelClient",
    "AnthropicClient",
    "AzureModelClient",
    "OpenAICompatibleClient",
]
