"""Action-surface helpers backed by the canonical tool registry."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol

from core.domain.types.tools import ToolSurface
from core.tool.contracts import RegisteredTool
from core.tool.execution import availability_view
from infrastructure.harness_providers import get_surface_tool_map, get_surface_tools
from infrastructure.observability.trace.redaction import redact_sensitive

_ACTION_SESSION_SOURCE = "_action_session"


class _IntegrationsSessionView(Protocol):
    """Session view exposing configured integrations."""

    @property
    def configured_integrations(self) -> Iterable[str]:
        """Names of configured integration instances."""

    @property
    def configured_integrations_known(self) -> bool:
        """True when the configured integrations set is authoritative."""


class IntegrationsView(Protocol):
    """View over resolved session integrations for tool availability."""

    @property
    def session(self) -> _IntegrationsSessionView:
        """Session instance exposing configured integrations."""


# Backwards compatibility alias for protocol importers.
IntegrationsContext = IntegrationsView


def _sources_for_view(
    view: IntegrationsView,
    resolved_integrations: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    raw_sources = availability_view(resolved_integrations or {})
    sources = dict(raw_sources)
    sources[_ACTION_SESSION_SOURCE] = {
        "session": view.session,
        "configured_integrations": tuple(view.session.configured_integrations),
        "configured_integrations_known": view.session.configured_integrations_known,
        "available_capabilities": getattr(view.session, "available_capabilities", {}),
    }
    return sources


_sources_for_context = _sources_for_view


def get_action_tools_from_integrations_view(
    view: IntegrationsView,
    *,
    resolved_integrations: dict[str, Any] | None = None,
) -> list[RegisteredTool]:
    """Return canonical registered tools available to the action agent."""
    sources = _sources_for_view(view, resolved_integrations)
    tools: list[RegisteredTool] = []
    for candidate in get_surface_tools(ToolSurface.ACTION):
        try:
            if not candidate.is_available(sources):
                continue
        except Exception as exc:
            safe_sources = redact_sensitive(sources)
            raise RuntimeError(
                f"{candidate.name} availability check failed for sources {safe_sources!r}: {exc}"
            ) from exc
        tools.append(candidate)
    return tools


get_action_tools_from_integrations_context = get_action_tools_from_integrations_view


def get_action_tool(name: str) -> RegisteredTool | None:
    """Return a registered action tool by name."""
    return get_surface_tool_map(ToolSurface.ACTION).get(name)


def action_tool_names(tools: Iterable[RegisteredTool]) -> tuple[str, ...]:
    return tuple(tool.name for tool in tools)


__all__ = [
    "IntegrationsContext",
    "IntegrationsView",
    "action_tool_names",
    "get_action_tool",
    "get_action_tools_from_integrations_context",
    "get_action_tools_from_integrations_view",
]
