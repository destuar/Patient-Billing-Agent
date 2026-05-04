"""Hook system for the agent harness.

Hooks run before and after tool execution to enforce safety policies.
Subclass Hook and override before_tool_call / after_tool_call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HookResult:
    """Result from a before_tool_call hook.

    Attributes:
        allowed: Whether the tool call should proceed.
        reason: Explanation if blocked (returned to the model as the tool result).
        modified_args: If set, replaces the original args for downstream hooks
                       and the tool handler.
    """

    allowed: bool
    reason: str = ""
    modified_args: dict[str, Any] | None = None


class Hook:
    """Base class for safety hooks.

    Subclass this and override before_tool_call and/or after_tool_call.
    """

    def before_tool_call(self, tool_name: str, args: dict[str, Any]) -> HookResult:
        """Run before tool execution. Return allowed=False to block."""
        return HookResult(allowed=True)

    def after_tool_call(self, tool_name: str, args: dict[str, Any], result: str) -> str:
        """Run after tool execution. Can modify/redact the result."""
        return result
