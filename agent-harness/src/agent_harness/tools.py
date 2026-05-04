"""Tool definitions for the agent harness.

Creation Patterns:
    1. @tool decorator: For simple, standalone tool functions
    2. create_tool(): For dynamic tools or closures capturing state
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    """A tool that can be called by the model."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any]], str]

    def to_api_format(self) -> dict[str, Any]:
        """Convert to OpenAI API tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def tool(
    name: str,
    description: str,
    parameters: dict[str, Any] | None = None,
) -> Callable[[Callable], Tool]:
    """Decorator to create a Tool from a function."""
    if parameters is None:
        parameters = {"type": "object", "properties": {}}

    def decorator(fn: Callable[[dict[str, Any]], str]) -> Tool:
        return Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=fn,
        )

    return decorator


def create_tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    handler: Callable[[dict[str, Any]], str],
) -> Tool:
    """Factory function to create a Tool dynamically."""
    return Tool(
        name=name,
        description=description,
        parameters=parameters,
        handler=handler,
    )
