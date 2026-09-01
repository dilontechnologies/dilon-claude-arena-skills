from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get

__all__ = [
    "get_arena_settings",
    "list_export_attributes",
    "get_recent_activity_user_access",
    "get_recent_activity_exports",
    "get_recent_activity_report_runs",
    "get_recent_activity_file_access",
    "get_api_usage",
]


@mcp.tool()
def get_arena_settings() -> dict[str, Any]:
    """Get top-level workspace settings.

    Returns workspace-level configuration: company info, license
    details, enabled features, default time zone, etc.
    """
    return _arena_get("/settings/arena")

@mcp.tool()
def list_export_attributes() -> dict[str, Any]:
    """List custom attributes available on export definitions.

    Even though we've scoped out the Exports / Extracts read tooling,
    knowing which attributes exist on export definitions is useful
    for understanding workspace configuration.
    """
    return _arena_get("/settings/export/attributes")

@mcp.tool()
def get_recent_activity_user_access() -> dict[str, Any]:
    """List recent user-access activity in the workspace (logins, etc.).

    Spec endpoint: GET /settings/recentactivities/useraccesses
    """
    return _arena_get("/settings/recentactivities/useraccesses")

@mcp.tool()
def get_recent_activity_exports() -> dict[str, Any]:
    """List recent export-run activity in the workspace.

    Spec endpoint: GET /settings/recentactivities/exports
    """
    return _arena_get("/settings/recentactivities/exports")

@mcp.tool()
def get_recent_activity_report_runs() -> dict[str, Any]:
    """List recent report-run activity in the workspace.

    Spec endpoint: GET /settings/recentactivities/reportruns
    """
    return _arena_get("/settings/recentactivities/reportruns")

@mcp.tool()
def get_recent_activity_file_access() -> dict[str, Any]:
    """List recent file-access activity (file downloads, content fetches).

    Spec endpoint: GET /settings/recentactivities/fileaccesses
    """
    return _arena_get("/settings/recentactivities/fileaccesses")

@mcp.tool()
def get_api_usage() -> dict[str, Any]:
    """Return every API call recorded in the workspace.

    Useful for monitoring this MCP server's own footprint against the
    workspace's API quota.
    Spec endpoint: GET /settings/recentactivities/apiusages
    """
    return _arena_get("/settings/recentactivities/apiusages")

