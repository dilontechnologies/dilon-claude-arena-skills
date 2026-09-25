from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get
from .. import config

__all__ = [
    "whoami",
    "list_users",
    "get_user",
    "list_user_groups",
]


@mcp.tool()
def whoami() -> dict[str, Any]:
    """Verify auth is working and report Arena workspace context."""
    settings = _arena_get("/settings/arena")
    return {
        "auth": "ok" if not (isinstance(settings, dict) and settings.get("error")) else "failed",
        "workspace_id": config.ARENA_WORKSPACE_ID,
        "arena_version": settings.get("arenaVersionId") if isinstance(settings, dict) else None,
        "api_base": config.ARENA_API_BASE,
        "snapshot_dir": str(config.SNAPSHOT_DIR),
        "raw": settings,
    }

@mcp.tool()
def list_users(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    user_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """Search workspace users — the primary way to resolve a person's GUID
    for creator_guid / owner_guid filters on other tools.

    Args:
        first_name: First name; wildcards (*) supported.
        last_name: Last name; wildcards supported.
        full_name: Full name "First Last"; wildcards supported.
        email: Email address.
        user_type: EMPLOYEE | PARTNER | BASIC_SUPPLIER | ADVANCED_SUPPLIER | INTEGRATION.
        enabled: True for active users, False for disabled.
        limit: Max results, default 25, max 400.
        offset: Pagination offset.
    """
    params: dict[str, Any] = {"limit": min(max(limit, 1), 400), "offset": max(offset, 0)}
    if first_name: params["firstName"] = first_name
    if last_name: params["lastName"] = last_name
    if full_name: params["fullName"] = full_name
    if email: params["email"] = email
    if user_type: params["type"] = user_type
    if enabled is not None: params["enabled"] = "true" if enabled else "false"
    return _arena_get("/settings/users", params=params)

@mcp.tool()
def get_user(guid: str) -> dict[str, Any]:
    """Get a single workspace user by GUID."""
    return _arena_get(f"/settings/users/{guid}")

@mcp.tool()
def list_user_groups() -> dict[str, Any]:
    """List all user groups in the workspace.

    Returns groups with their assignability scopes (ACCESS_POLICIES,
    CHANGES, QUALITY, etc.). Only available in Access Policies–enabled
    workspaces.
    """
    return _arena_get("/settings/usergroups")

