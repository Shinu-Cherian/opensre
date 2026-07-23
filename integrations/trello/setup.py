"""What Trello needs before it is considered configured."""

from __future__ import annotations

from integrations.setup_flow import IntegrationSetupSpec, SetupField
from integrations.trello.verifier import verify_trello

TRELLO_SETUP = IntegrationSetupSpec(
    service="trello",
    fields=(
        SetupField(
            name="api_key",
            label="API Key",
            prompt="Trello API Key",
            env_var="TRELLO_API_KEY",
            secret=True,
        ),
        SetupField(
            name="token",
            label="Token",
            prompt="Trello Token",
            env_var="TRELLO_TOKEN",
            secret=True,
        ),
        SetupField(
            name="board_id",
            label="Board ID",
            prompt="Trello Board ID (optional)",
            env_var="TRELLO_BOARD_ID",
            optional=True,
        ),
        SetupField(
            name="list_id",
            label="List ID",
            prompt="Trello List ID",
            env_var="TRELLO_LIST_ID",
            optional=False,
        ),
    ),
    verify=verify_trello,
)

__all__ = ["TRELLO_SETUP"]
