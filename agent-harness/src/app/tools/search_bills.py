"""PLACEHOLDER: Knowledge base search tool using create_tool() factory.

This file demonstrates the factory pattern for tools that need
dependency injection (e.g., a search service, database connection).

Things to consider building:
    - Semantic search over billing policies
    - Chargemaster lookups
    - FAQ matching
    - Document retrieval with citations
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from agent_harness import Tool, create_tool


class SearchService(Protocol):
    """Protocol for a search backend."""

    def search(self, query: str, top: int = 5) -> list[dict[str, Any]]:
        ...


def create_search_bills_tool(search_service: SearchService) -> Tool:
    """Create a knowledge-base search tool.

    This factory captures search_service in a closure so the harness
    can call it without knowing about the search implementation.

    Args:
        search_service: Any object implementing the SearchService protocol.

    Returns:
        A Tool instance ready to register with the harness.
    """

    def search_handler(args: dict) -> str:
        query = args.get("query", "")
        top = args.get("top", 5)

        if not query.strip():
            return json.dumps({"error": "Query must not be empty"})

        # TODO: You may want to add pre-processing, query expansion,
        # or post-processing of results here.
        results = search_service.search(query, top=top)
        return json.dumps({"query": query, "count": len(results), "results": results})

    return create_tool(
        name="search_knowledge_base",
        description="TODO: Describe what this tool searches and what it returns",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language search query",
                },
                "top": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["query"],
        },
        handler=search_handler,
    )
