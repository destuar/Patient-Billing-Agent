"""PLACEHOLDER: Tool for explaining healthcare bill line items.

This file demonstrates the @tool decorator pattern. Replace the stub
implementation with your own logic.

Things to consider building:
    - Medical code lookups (CPT, ICD-10, HCPCS)
    - Chargemaster reference data
    - Insurance plan detail parsing
    - Plain-language translation of billing jargon
"""

from __future__ import annotations

import json

from agent_harness import tool


@tool(
    name="explain_bill_item",
    description="TODO: Describe what this tool does for the model",
    parameters={
        "type": "object",
        "properties": {
            # TODO: Define the parameters your tool accepts
            # Example:
            # "description": {
            #     "type": "string",
            #     "description": "The line-item description from the bill",
            # },
            # "charge_amount": {
            #     "type": "number",
            #     "description": "The billed charge amount in dollars",
            # },
        },
        "required": [],  # TODO: List required parameter names
    },
)
def explain_bill(args: dict) -> str:
    """TODO: Implement bill line-item explanation logic."""
    # Your implementation here
    raise NotImplementedError("Implement this tool")
