from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _request_bytes

__all__ = [
    "search_import_definitions",
    "get_import_definition",
    "get_import_runs",
    "get_import_run",
    "get_import_run_result_content",
    "get_import_run_error_content",
    "search_integrations",
    "get_integration",
    "get_integration_administrators",
    "list_triggers",
    "get_trigger",
    "search_outbound_event_integrations",
    "get_outbound_event_integration",
    "get_outbound_event_integration_triggers",
    "get_outbound_event_integration_trigger",
    "get_outbound_event_integration_administrators",
]


@mcp.tool()
def search_import_definitions(
    query: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Search Arena import definitions.

    Returns a list of import-job templates (e.g., bulk-item-import,
    bulk-BOM-import).
    """
    params: dict[str, Any] = {"limit": min(max(limit, 1), 400), "offset": max(offset, 0)}
    if query:
        params["any"] = query
    if name:
        params["name"] = name if "*" in name else f"{name}*"
    return _arena_get("/imports", params=params)

@mcp.tool()
def get_import_definition(guid: str) -> dict[str, Any]:
    """Get a single import definition by GUID."""
    return _arena_get(f"/imports/{guid}")

@mcp.tool()
def get_import_runs(guid: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """List runs (executions) of an import definition."""
    return _arena_get(
        f"/imports/{guid}/runs",
        params={"limit": min(max(limit, 1), 400), "offset": max(offset, 0)},
    )

@mcp.tool()
def get_import_run(import_guid: str, run_guid: str) -> dict[str, Any]:
    """Get a single import run by GUID (status, dates, file refs)."""
    return _arena_get(f"/imports/{import_guid}/runs/{run_guid}")

@mcp.tool()
def get_import_run_result_content(import_guid: str, run_guid: str) -> dict[str, Any]:
    """Download the result-content file of an import run (typically a CSV
    summarizing what was imported). Returned as base64-encoded bytes."""
    return _request_bytes(
        f"/imports/{import_guid}/runs/{run_guid}/resultContent"
    )

@mcp.tool()
def get_import_run_error_content(import_guid: str, run_guid: str) -> dict[str, Any]:
    """Download the error-content file of an import run (errors encountered
    during the run). Returned as base64-encoded bytes."""
    return _request_bytes(
        f"/imports/{import_guid}/runs/{run_guid}/errorContent"
    )

@mcp.tool()
def search_integrations(
    query: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Search outbound integrations configured in the workspace.

    Spec endpoint: GET /outboundintegrations
    """
    params: dict[str, Any] = {"limit": min(max(limit, 1), 400), "offset": max(offset, 0)}
    if query:
        params["any"] = query
    if name:
        params["name"] = name if "*" in name else f"{name}*"
    return _arena_get("/outboundintegrations", params=params)

@mcp.tool()
def get_integration(guid: str) -> dict[str, Any]:
    """Get a single outbound integration by GUID."""
    return _arena_get(f"/outboundintegrations/{guid}")

@mcp.tool()
def get_integration_administrators(guid: str) -> dict[str, Any]:
    """List administrators (users) who can manage an integration."""
    return _arena_get(f"/outboundintegrations/{guid}/administrators")

@mcp.tool()
def list_triggers() -> dict[str, Any]:
    """List ALL triggers in the workspace.

    Triggers fire integration events when specified conditions are met.
    Spec endpoint: GET /settings/integrations/triggers
    """
    return _arena_get("/settings/integrations/triggers")

@mcp.tool()
def get_trigger(guid: str) -> dict[str, Any]:
    """Get a single trigger by GUID."""
    return _arena_get(f"/settings/integrations/triggers/{guid}")

@mcp.tool()
def search_outbound_event_integrations(
    query: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Search outbound-event integrations.

    Distinct from generic integrations — these are integrations that fire
    events outbound (webhooks-style) on workspace activity.
    Spec endpoint: GET /outboundevents
    """
    params: dict[str, Any] = {"limit": min(max(limit, 1), 400), "offset": max(offset, 0)}
    if query:
        params["any"] = query
    return _arena_get("/outboundevents", params=params)

@mcp.tool()
def get_outbound_event_integration(guid: str) -> dict[str, Any]:
    """Get a single outbound-event integration by GUID."""
    return _arena_get(f"/outboundevents/{guid}")

@mcp.tool()
def get_outbound_event_integration_triggers(guid: str) -> dict[str, Any]:
    """List triggers attached to an outbound-event integration."""
    return _arena_get(f"/outboundevents/{guid}/triggers")

@mcp.tool()
def get_outbound_event_integration_trigger(
    integration_guid: str, trigger_guid: str
) -> dict[str, Any]:
    """Get a single trigger attached to an outbound-event integration."""
    return _arena_get(
        f"/outboundevents/{integration_guid}/triggers/{trigger_guid}"
    )

@mcp.tool()
def get_outbound_event_integration_administrators(guid: str) -> dict[str, Any]:
    """List administrators of an outbound-event integration."""
    return _arena_get(f"/outboundevents/{guid}/administrators")

