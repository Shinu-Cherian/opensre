"""Resolve integrations node — discovers which integrations are available for this alert."""

from __future__ import annotations

import os
from typing import Any

from core.state import InvestigationState
from infrastructure.harness_providers import (
    enrich_resolved_with_repo_scopes,
    resolve_integrations_with_metadata,
)
from infrastructure.observability import get_progress_tracker as get_tracker


def resolve_integrations(state: InvestigationState) -> dict[str, Any]:
    """Discover and classify all integrations available for this investigation.

    Reads  : _auth_token, org_id, resolved_integrations (idempotency guard)
    Writes : resolved_integrations
    """
    return {"resolved_integrations": _resolve(state, emit_progress=True)}


def resolve_integrations_quiet(state: InvestigationState) -> dict[str, Any]:
    """Like :func:`resolve_integrations` but without progress-tracker UI."""
    return _resolve(state, emit_progress=False)


def _resolve(state: InvestigationState, *, emit_progress: bool) -> dict[str, Any]:
    """Return the raw integrations dict (keyed by vendor name)."""
    if state.get("resolved_integrations"):
        return dict(state["resolved_integrations"])

    tracker = get_tracker() if emit_progress else None
    if tracker is not None:
        tracker.start("resolve_integrations", "Fetching org integrations")

    result = resolve_integrations_with_metadata(state)
    _complete_tracker(
        tracker,
        "resolve_integrations",
        fields_updated=["resolved_integrations"],
        message=result.progress_message,
    )
    return _enrich_with_repo_scopes(result.resolved_integrations, state)


def _enrich_with_repo_scopes(
    resolved: dict[str, Any],
    state: InvestigationState,
) -> dict[str, Any]:
    """Inject VCS repo scopes (owner/repo) inferred from the alert and environment."""
    raw_alert = state.get("raw_alert", "")
    message = raw_alert if isinstance(raw_alert, str) else str(raw_alert)
    return enrich_resolved_with_repo_scopes(
        resolved=resolved,
        message=message,
        conversation_messages=None,
        env=os.environ,
        cwd=None,
        cached_scopes={},
    )


def _complete_tracker(tracker: Any | None, node_name: str, **kwargs: Any) -> None:
    if kwargs.get("message") is None:
        kwargs.pop("message", None)
    if tracker is not None:
        tracker.complete(node_name, **kwargs)
