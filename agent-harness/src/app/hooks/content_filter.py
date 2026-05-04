"""PLACEHOLDER: Hook for filtering dangerous content in tool arguments.

This file demonstrates the Hook subclass pattern for before_tool_call
blocking. Replace the stub implementation with your own logic.

Things to consider blocking:
    - Destructive database operations (DROP, DELETE, INSERT)
    - Shell injection attempts
    - Prompt injection patterns
    - Requests for information outside your agent's scope
"""

from __future__ import annotations

import logging
from typing import Any

from agent_harness import Hook, HookResult

logger = logging.getLogger(__name__)


class ContentFilterHook(Hook):
    """Block tool calls whose arguments contain prohibited terms.

    TODO: Define your blocked terms and matching logic.
    """

    def __init__(self, blocked_terms: list[str] | None = None) -> None:
        # TODO: Define terms that should never appear in tool arguments
        self.blocked_terms = [t.lower() for t in (blocked_terms or [])]

    def before_tool_call(self, tool_name: str, args: dict[str, Any]) -> HookResult:
        """TODO: Implement content filtering logic."""
        # Example implementation:
        # args_str = str(args).lower()
        # for term in self.blocked_terms:
        #     if term in args_str:
        #         return HookResult(allowed=False, reason=f"Blocked: contains '{term}'")
        return HookResult(allowed=True)
