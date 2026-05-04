"""Core agent harness - the loop that powers everything.

The Loop:
    1. Call the model with messages and tools schema
    2. Stream response chunks, yielding text to caller
    3. If model requests tool calls, execute them and add results to messages
    4. Repeat until model returns text without tool calls (done)
    5. Safety limit: max_iterations prevents infinite loops
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Generator

from .clients.base import ModelClient
from .hooks import Hook, HookResult
from .messages import Message, StreamChunk, ToolCall, ToolCallDelta
from .tools import Tool

logger = logging.getLogger(__name__)


class AgentHarness:
    """The core agent loop.

    Usage:
        client = OpenAICompatibleClient(...)
        harness = AgentHarness(client, "You are a helpful assistant.", tools=[...])

        for chunk in harness.run_stream([Message(role="user", content="Hello")]):
            print(chunk, end="")
    """

    def __init__(
        self,
        client: ModelClient,
        system_prompt: str,
        tools: list[Tool] | None = None,
        max_iterations: int = 30,
        hooks: list[Hook] | None = None,
        on_tool_call: Callable[[str, str, dict[str, Any]], None] | None = None,
        on_tool_result: Callable[[str, str, str], None] | None = None,
        on_tool_call_message: Callable[[str | None, list[ToolCall]], None] | None = None,
    ):
        self.client = client
        self.system_prompt = system_prompt
        self.tools = {t.name: t for t in (tools or [])}
        self.max_iterations = max_iterations
        self.hooks = hooks or []
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.on_tool_call_message = on_tool_call_message

    def _build_api_messages(
        self, messages: list[Message]
    ) -> list[dict[str, Any]]:
        api_messages = [{"role": "system", "content": self.system_prompt}]
        api_messages.extend(m.to_api_format() for m in messages)
        return api_messages

    def _build_tools_schema(self) -> list[dict[str, Any]] | None:
        if not self.tools:
            return None
        return [t.to_api_format() for t in self.tools.values()]

    def _accumulate_tool_calls(
        self,
        buffer: dict[int, dict[str, Any]],
        delta: ToolCallDelta,
    ) -> None:
        if delta.index not in buffer:
            buffer[delta.index] = {"id": "", "name": "", "arguments": ""}

        buf = buffer[delta.index]
        if delta.id:
            buf["id"] = delta.id
        if delta.name:
            buf["name"] = delta.name
        if delta.arguments:
            buf["arguments"] += delta.arguments

    def _execute_tool(self, tool_call_id: str, name: str, arguments: dict[str, Any]) -> str:
        tool = self.tools.get(name)
        if not tool:
            return json.dumps({"error": f"Unknown tool: {name}"})

        if self.on_tool_call:
            self.on_tool_call(tool_call_id, name, arguments)

        effective_args = arguments
        for hook in self.hooks:
            hook_result = hook.before_tool_call(name, effective_args)
            if not hook_result.allowed:
                logger.info(f"Hook {hook.__class__.__name__} blocked tool {name}: {hook_result.reason}")
                result = json.dumps({"blocked": True, "reason": hook_result.reason})
                if self.on_tool_result:
                    self.on_tool_result(tool_call_id, name, result)
                return result
            if hook_result.modified_args is not None:
                effective_args = hook_result.modified_args

        try:
            result = tool.handler(effective_args)
        except Exception as e:
            logger.exception(f"Tool {name} failed")
            result = json.dumps({"error": str(e)})

        for hook in self.hooks:
            result = hook.after_tool_call(name, effective_args, result)

        if self.on_tool_result:
            self.on_tool_result(tool_call_id, name, result)

        return result

    def run_stream(
        self,
        messages: list[Message],
    ) -> Generator[str, None, str]:
        """Run the agent loop with streaming. Yields text chunks."""
        api_messages = self._build_api_messages(messages)
        tools_schema = self._build_tools_schema()

        for iteration in range(self.max_iterations):
            logger.debug(f"Agent iteration {iteration + 1}")

            text_parts: list[str] = []
            tool_call_buffer: dict[int, dict[str, Any]] = {}

            for chunk in self.client.chat_stream(api_messages, tools_schema):
                if chunk.text:
                    text_parts.append(chunk.text)
                    yield chunk.text

                if chunk.tool_call:
                    self._accumulate_tool_calls(tool_call_buffer, chunk.tool_call)

            text = "".join(text_parts)

            if not tool_call_buffer:
                return text

            tool_calls = []
            for idx in sorted(tool_call_buffer.keys()):
                tc_data = tool_call_buffer[idx]
                try:
                    arguments = json.loads(tc_data["arguments"]) if tc_data["arguments"] else {}
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in tool arguments for {tc_data['name']}: {e}")
                    arguments = {"_parse_error": str(e), "_raw": tc_data["arguments"][:500]}
                tool_calls.append(
                    ToolCall(
                        id=tc_data["id"],
                        name=tc_data["name"],
                        arguments=arguments,
                    )
                )

            api_messages.append({
                "role": "assistant",
                "content": text or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in tool_calls
                ],
            })

            if self.on_tool_call_message:
                self.on_tool_call_message(text or None, tool_calls)

            for tc in tool_calls:
                logger.info(f"Executing tool: {tc.name}")
                result = self._execute_tool(tc.id, tc.name, tc.arguments)

                api_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return text

    def run(self, messages: list[Message]) -> str:
        """Run the agent loop without streaming. Returns the complete response."""
        result = ""
        for chunk in self.run_stream(messages):
            result += chunk
        return result
