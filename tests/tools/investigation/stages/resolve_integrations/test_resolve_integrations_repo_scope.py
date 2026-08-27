"""Tests for VCS repo scope enrichment in the investigation resolve-integrations stage."""

from __future__ import annotations

from typing import Any

from core.agent_harness.session.integration_resolution import IntegrationResolutionResult
from tools.investigation.stages.resolve_integrations import node


def _stub_metadata(
    resolved: dict[str, Any],
    *,
    progress_message: str = "Resolved",
) -> Any:
    """Return a monkeypatch-friendly factory for ``resolve_integrations_with_metadata``."""
    return lambda _state: IntegrationResolutionResult(
        resolved_integrations=resolved,
        progress_message=progress_message,
    )


def test_resolve_calls_repo_scope_enrichment(monkeypatch: Any) -> None:
    """``_resolve`` must pass the base result through ``enrich_resolved_with_repo_scopes``."""
    base = {"datadog": {"site": "datadoghq.com"}}
    enriched = {"datadog": {"site": "datadoghq.com"}, "github": {"owner": "Acme", "repo": "app"}}
    enrichment_calls: list[dict[str, Any]] = []

    def _fake_enrich(**kwargs: Any) -> dict[str, Any]:
        enrichment_calls.append(kwargs)
        return enriched

    monkeypatch.setattr(node, "get_tracker", lambda: None)
    monkeypatch.setattr(node, "resolve_integrations_with_metadata", _stub_metadata(base))
    monkeypatch.setattr(node, "enrich_resolved_with_repo_scopes", _fake_enrich)

    state: dict[str, Any] = {"raw_alert": "Pod crash in https://github.com/Acme/app"}
    updates = node.resolve_integrations(state)  # type: ignore[arg-type]

    assert updates["resolved_integrations"] == enriched
    assert len(enrichment_calls) == 1
    call = enrichment_calls[0]
    assert call["resolved"] == base
    assert call["message"] == "Pod crash in https://github.com/Acme/app"
    assert call["conversation_messages"] is None
    assert call["cached_scopes"] == {}


def test_enrichment_receives_stringified_dict_alert(monkeypatch: Any) -> None:
    """When ``raw_alert`` is a dict, it must be stringified for URL parsing."""
    base = {"sentry": {}}

    def _fake_enrich(**kwargs: Any) -> dict[str, Any]:
        assert isinstance(kwargs["message"], str)
        return kwargs["resolved"]

    monkeypatch.setattr(node, "get_tracker", lambda: None)
    monkeypatch.setattr(node, "resolve_integrations_with_metadata", _stub_metadata(base))
    monkeypatch.setattr(node, "enrich_resolved_with_repo_scopes", _fake_enrich)

    state: dict[str, Any] = {"raw_alert": {"title": "OOMKilled", "url": "https://github.com/X/Y"}}
    result = node.resolve_integrations(state)  # type: ignore[arg-type]

    assert result["resolved_integrations"] == base


def test_enrichment_skipped_for_idempotent_resolve(monkeypatch: Any) -> None:
    """When resolved_integrations already exist in state, enrichment must not run."""
    enrichment_called = False

    def _unexpected_enrich(**_kwargs: Any) -> dict[str, Any]:
        nonlocal enrichment_called
        enrichment_called = True
        raise AssertionError("enrichment should not be called for cached state")

    monkeypatch.setattr(node, "enrich_resolved_with_repo_scopes", _unexpected_enrich)

    state: dict[str, Any] = {"resolved_integrations": {"github": {"owner": "X", "repo": "Y"}}}
    updates = node.resolve_integrations(state)  # type: ignore[arg-type]

    assert updates == {"resolved_integrations": {"github": {"owner": "X", "repo": "Y"}}}
    assert not enrichment_called
