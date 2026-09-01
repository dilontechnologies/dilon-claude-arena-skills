from __future__ import annotations

import json
from typing import Any, Optional

from ..core import mcp, reset_connection, _get_access_token
from .. import config

__all__ = [
    "list_environments",
    "get_active_environment",
    "set_environment",
    "switch_environment",
    "delete_environment",
]

_FIELD_TO_CONFIG_ATTR = {
    "client_id": "ARENA_CLIENT_ID",
    "client_secret": "ARENA_CLIENT_SECRET",
    "workspace_id": "ARENA_WORKSPACE_ID",
    "token_url": "ARENA_TOKEN_URL",
    "api_base": "ARENA_API_BASE",
    "usage_reason": "ARENA_USAGE_REASON",
}


def _current_effective() -> dict[str, str]:
    return {field: getattr(config, attr) for field, attr in _FIELD_TO_CONFIG_ATTR.items()}


def _mask(effective: dict[str, str]) -> dict[str, Any]:
    masked = dict(effective)
    masked["client_secret_set"] = bool(masked.pop("client_secret", ""))
    return masked


def _apply(fields: dict[str, Optional[str]]) -> None:
    for field, value in fields.items():
        if value is None:
            continue
        if field == "api_base":
            value = value.rstrip("/")
        setattr(config, _FIELD_TO_CONFIG_ATTR[field], value)


def _validate() -> dict[str, Any]:
    reset_connection()
    try:
        _get_access_token(force_refresh=True)
    except RuntimeError as exc:
        return {"error": True, "message": str(exc)}
    return {"error": False}


@mcp.tool()
def list_environments() -> dict[str, Any]:
    """List every saved environment plus which one (if any) is active.

    client_secret is never included, only a client_secret_set boolean.
    """
    config.ENVIRONMENTS_DIR.mkdir(parents=True, exist_ok=True)
    environments = []
    for path in sorted(config.ENVIRONMENTS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        entry = {"name": path.stem}
        entry.update({k: v for k, v in data.items() if k != "client_secret"})
        entry["client_secret_set"] = bool(data.get("client_secret"))
        environments.append(entry)
    return {"active": config._active_name, "environments": environments}


@mcp.tool()
def get_active_environment() -> dict[str, Any]:
    """The currently effective Arena connection config (secret redacted)."""
    return {"active": config._active_name, **_mask(_current_effective())}


@mcp.tool()
def set_environment(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    workspace_id: Optional[str] = None,
    token_url: Optional[str] = None,
    api_base: Optional[str] = None,
    usage_reason: Optional[str] = None,
    save_as: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply ad hoc credential/workspace overrides, resetting the connection.

    Layers the given fields on top of the currently effective config, then
    validates by fetching a fresh OAuth token immediately (rather than
    waiting for the next real call to surface an auth failure) — a failed
    validation rolls back to the previous config and returns an error dict
    instead of raising. Without save_as, this is session-only (lost on
    restart, doesn't touch the persisted "active environment" state). With
    save_as, persists the fully-resolved fields as a new named environment
    file and remembers it across restarts.
    """
    given = {
        "client_id": client_id, "client_secret": client_secret,
        "workspace_id": workspace_id, "token_url": token_url,
        "api_base": api_base, "usage_reason": usage_reason,
    }
    given = {k: v for k, v in given.items() if v is not None}
    previous = _current_effective()
    merged = {**previous, **given}

    if dry_run:
        return {"dry_run": True, "would_apply": _mask(merged), "save_as": save_as}

    _apply(given)
    result = _validate()
    if result.get("error"):
        _apply(previous)
        reset_connection()
        return result

    if save_as:
        config.ENVIRONMENTS_DIR.mkdir(parents=True, exist_ok=True)
        (config.ENVIRONMENTS_DIR / f"{save_as}.json").write_text(
            json.dumps(merged, indent=2), encoding="utf-8"
        )
        config.ACTIVE_ENV_STATE_FILE.write_text(json.dumps({"name": save_as}), encoding="utf-8")
        config._active_name = save_as
    else:
        config._active_name = None

    return {"applied": _mask(merged), "saved_as": save_as, "auth": "ok"}


@mcp.tool()
def switch_environment(name: str) -> dict[str, Any]:
    """Switch the running server to a previously saved named environment."""
    path = config.ENVIRONMENTS_DIR / f"{name}.json"
    if not path.exists():
        return {"error": True, "message": f"No saved environment named {name!r}."}
    saved = json.loads(path.read_text(encoding="utf-8"))
    previous = _current_effective()
    resolved = {
        field: (saved.get(field) or config._plain_env(field))
        for field in _FIELD_TO_CONFIG_ATTR
    }

    _apply(resolved)
    result = _validate()
    if result.get("error"):
        _apply(previous)
        reset_connection()
        return result

    config.ACTIVE_ENV_STATE_FILE.write_text(json.dumps({"name": name}), encoding="utf-8")
    config._active_name = name
    return {"active": name, "applied": _mask(resolved), "auth": "ok"}


@mcp.tool()
def delete_environment(name: str) -> dict[str, Any]:
    """Delete a saved environment. Reverts the live session to plain .env
    values and resets the connection if it was the active one."""
    path = config.ENVIRONMENTS_DIR / f"{name}.json"
    if not path.exists():
        return {"error": True, "message": f"No saved environment named {name!r}."}
    path.unlink()

    was_active = config._active_name == name
    if was_active:
        for field, attr in _FIELD_TO_CONFIG_ATTR.items():
            setattr(config, attr, config._plain_env(field))
        reset_connection()
        if config.ACTIVE_ENV_STATE_FILE.exists():
            config.ACTIVE_ENV_STATE_FILE.unlink()
        config._active_name = None

    return {"deleted": name, "was_active": was_active}
