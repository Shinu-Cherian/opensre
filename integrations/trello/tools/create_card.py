"""Trello create card tool for investigation workflows."""

from __future__ import annotations

from typing import Any

from core.tool_framework.base import BaseTool
from core.tool_framework.utils.tool_availability import tool_unavailable
from integrations.trello.client import create_trello_card
from integrations.trello.config import build_trello_config


class CreateTrelloCardTool(BaseTool):
    """Create a new card in Trello for tracking tasks or incidents."""

    name = "create_trello_card"
    source = "trello"
    description = (
        "Create a new card in Trello to track incident resolution, action items, "
        "or postmortem tasks. Requires the name and description of the card."
    )
    use_cases = [
        "Creating a tracking card for a newly discovered bug",
        "Adding action items from an incident postmortem",
        "Tracking remediation steps during an active incident",
    ]
    requires = ["api_key", "token", "name", "desc"]
    injected_params = ["api_key", "token", "board_id", "list_id"]
    input_schema = {
        "type": "object",
        "properties": {
            "api_key": {"type": "string", "description": "Trello API key"},
            "token": {"type": "string", "description": "Trello token"},
            "board_id": {"type": "string", "description": "Trello Board ID (optional)"},
            "list_id": {"type": "string", "description": "Trello List ID"},
            "name": {"type": "string", "description": "Title of the card"},
            "desc": {"type": "string", "description": "Detailed description for the card"},
        },
        "required": ["api_key", "token", "name", "desc"],
    }
    outputs = {
        "id": "The ID of the created card",
        "url": "The URL of the created card",
    }

    def is_available(self, sources: dict) -> bool:
        trello_config = sources.get("trello", {})
        return bool(trello_config.get("api_key") and trello_config.get("token"))

    def extract_params(self, sources: dict) -> dict[str, Any]:
        trello = sources.get("trello", {})
        return {
            "api_key": trello.get("api_key", ""),
            "token": trello.get("token", ""),
            "board_id": trello.get("board_id", ""),
            "list_id": trello.get("list_id", ""),
            "name": "",
            "desc": "",
        }

    def run(
        self,
        api_key: str,
        token: str,
        name: str,
        desc: str,
        board_id: str = "",
        list_id: str = "",
        **_kwargs: Any,
    ) -> dict[str, Any]:
        if not api_key or not token:
            return tool_unavailable("trello", "Trello integration is not configured.")
        if not name:
            return tool_unavailable("trello", "Card name is required.")
        if not desc:
            return tool_unavailable("trello", "Card description is required.")

        config = build_trello_config(
            {
                "api_key": api_key,
                "token": token,
                "board_id": board_id,
                "list_id": list_id,
            }
        )

        try:
            result = create_trello_card(
                config=config,
                name=name,
                desc=desc,
                list_id=list_id if list_id else None,
            )
            return {
                "source": "trello",
                "available": True,
                "card_id": result.get("id", ""),
                "url": result.get("shortUrl", ""),
            }
        except Exception as err:
            return tool_unavailable("trello", str(err))


create_trello_card_tool = CreateTrelloCardTool()
