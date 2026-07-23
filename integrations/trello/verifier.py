"""Trello credential and connectivity verification."""

import logging
from typing import Any

import httpx

import integrations.trello.client as client
from integrations._validation_helpers import report_validation_failure
from integrations.trello.config import build_trello_config
from integrations.verification import register_verifier, result

logger = logging.getLogger(__name__)


@register_verifier("trello")
def verify_trello(source: str, config: dict[str, Any]) -> dict[str, str]:
    """Validate Trello connectivity via the standard registry."""
    try:
        trello_config = build_trello_config(config)
    except Exception as err:
        return result("trello", source, "missing", f"Invalid Trello configuration: {err}")

    if not trello_config.api_key:
        return result("trello", source, "missing", "Trello API key is required.")
    if not trello_config.token:
        return result("trello", source, "missing", "Trello token is required.")

    try:
        member = client.validate_trello_connection(config=trello_config)
        username = member.get("username", "unknown")
        return result(
            "trello",
            source,
            "passed",
            f"Trello connectivity successful. Authenticated as @{username}",
        )
    except httpx.HTTPStatusError as err:
        detail = err.response.text.strip() or str(err)
        return result("trello", source, "failed", f"Trello validation failed: {detail}")
    except Exception as err:
        report_validation_failure(
            err,
            logger=logger,
            integration="trello",
            method="verify_trello",
        )
        return result("trello", source, "error", f"Trello validation failed: {err}")
