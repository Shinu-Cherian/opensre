from __future__ import annotations

from typing import Any

from integrations.hermes.tools.hermes_session_evidence_tool import (
    get_hermes_adapter_catalog,
    get_hermes_approval_events,
    get_hermes_audit_trail,
    get_hermes_config,
    get_hermes_credential_state,
    get_hermes_cron_state,
    get_hermes_kv_cache_state,
    get_hermes_message_history,
    get_hermes_runtime_state,
    get_hermes_session_log,
    get_hermes_session_topology,
)
from tools.investigation.stages.gather_evidence.tools import merge_tool_evidence


class _FakeHermesBackend:
    def get_session_log(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {"source": "hermes", "available": True, "session_id": session_id, "events": []}

    def get_message_history(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {"source": "hermes", "available": True, "session_id": session_id, "messages": []}

    def get_kv_cache_state(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "cache_hits": 1,
            "cache_misses": 0,
            "messages_with_cache_miss": [],
        }

    def get_runtime_state(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "is_blocked": False,
        }

    def get_cron_state(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "schedule_cron": "* * * * *",
            "last_run": {"delivery_status": "ok"},
        }

    def get_session_topology(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "visible_session_id": session_id,
            "all_sessions": [],
        }

    def get_adapter_catalog(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "messaging_adapters": ["telegram"],
            "llm_providers": ["bedrock"],
            "execution_backends": ["local"],
        }

    def get_config(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "provider": "bedrock",
            "model": "claude-3-5-sonnet",
        }

    def get_audit_trail(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "events": [{"id": "ev1"}],
        }

    def get_approval_events(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "events": [{"id": "app1"}],
        }

    def get_credential_state(self, session_id: str = "", **_: Any) -> dict[str, Any]:
        return {
            "source": "hermes",
            "available": True,
            "session_id": session_id,
            "mode": "isolated",
            "outbound_calls": [{"target": "api"}],
        }


def test_tools_delegate_to_backend() -> None:
    backend = _FakeHermesBackend()

    assert get_hermes_session_log("s1", hermes_backend=backend)["available"] is True
    assert get_hermes_message_history("s1", hermes_backend=backend)["available"] is True
    assert get_hermes_kv_cache_state("s1", hermes_backend=backend)["cache_hits"] == 1
    assert get_hermes_runtime_state("s1", hermes_backend=backend)["is_blocked"] is False
    assert (
        get_hermes_cron_state("s1", hermes_backend=backend)["last_run"]["delivery_status"] == "ok"
    )
    assert get_hermes_session_topology("s1", hermes_backend=backend)["visible_session_id"] == "s1"
    assert get_hermes_adapter_catalog("s1", hermes_backend=backend)["messaging_adapters"] == [
        "telegram"
    ]
    assert get_hermes_config("s1", hermes_backend=backend)["provider"] == "bedrock"
    assert get_hermes_audit_trail("s1", hermes_backend=backend)["events"] == [{"id": "ev1"}]
    assert get_hermes_approval_events("s1", hermes_backend=backend)["events"] == [{"id": "app1"}]
    assert get_hermes_credential_state("s1", hermes_backend=backend)["mode"] == "isolated"


def test_tools_require_backend_when_not_configured() -> None:
    result = get_hermes_session_log(session_id="")
    assert result["available"] is False
    assert "requires a Hermes backend" in str(result["error"])


def test_hermes_evidence_mappers_record_catalog_entries() -> None:
    evidence: dict[str, Any] = {}

    merge_tool_evidence(
        evidence,
        "get_hermes_adapter_catalog",
        {
            "available": True,
            "messaging_adapters": ["telegram"],
            "llm_providers": ["bedrock"],
            "execution_backends": ["local"],
        },
        {},
    )
    merge_tool_evidence(
        evidence,
        "get_hermes_approval_events",
        {"available": True, "events": [{"id": "app1"}]},
        {},
    )
    merge_tool_evidence(
        evidence,
        "get_hermes_audit_trail",
        {"available": True, "events": [{"id": "ev1"}]},
        {},
    )
    merge_tool_evidence(
        evidence,
        "get_hermes_config",
        {"available": True, "provider": "bedrock", "model": "claude-3-5-sonnet"},
        {},
    )
    merge_tool_evidence(
        evidence,
        "get_hermes_credential_state",
        {"available": True, "mode": "isolated", "outbound_calls": [{"target": "api"}]},
        {},
    )
    merge_tool_evidence(
        evidence,
        "get_hermes_cron_state",
        {"available": True, "schedule_cron": "* * * * *"},
        {},
    )

    entries = evidence.get("catalog_entries", [])
    assert isinstance(entries, list)
    sources = {e["source"] for e in entries}

    assert "hermes_adapter_catalog" in sources
    assert "hermes_approval_events" in sources
    assert "hermes_audit_trail" in sources
    assert "hermes_config" in sources
    assert "hermes_credential_state" in sources
    assert "hermes_cron_state" in sources


def test_hermes_report_claims_attach_to_catalog_entries() -> None:
    from types import SimpleNamespace

    from tools.investigation.reporting.context.evidence_catalog import (
        attach_evidence_to_claims,
        build_evidence_catalog,
    )

    evidence: dict[str, Any] = {}
    merge_tool_evidence(
        evidence,
        "get_hermes_adapter_catalog",
        {
            "available": True,
            "messaging_adapters": ["telegram"],
            "llm_providers": ["bedrock"],
            "execution_backends": ["local"],
        },
        {},
    )

    ns = SimpleNamespace(
        evidence=evidence,
        cloudwatch_region=None,
        cloudwatch_url=None,
        grafana_endpoint=None,
        datadog_site=None,
    )
    catalog, source_to_id = build_evidence_catalog(ns)
    assert "hermes_adapter_catalog" in source_to_id

    display_map = {eid: entry["label"] for eid, entry in catalog.items()}
    claims = [{"statement": "Adapter listed", "evidence_sources": ["hermes_adapter_catalog"]}]
    attached = attach_evidence_to_claims(claims, source_to_id, display_map)

    assert attached[0].get("evidence_ids") == [source_to_id["hermes_adapter_catalog"]]
    assert attached[0].get("evidence_labels") == ["Hermes Adapter Catalog"]
