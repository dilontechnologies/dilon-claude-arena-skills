from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_INSTALL_ROOT = Path(__file__).resolve().parent.parent

ENVIRONMENTS_DIR = _INSTALL_ROOT / "environments.local"
ACTIVE_ENV_STATE_FILE = _INSTALL_ROOT / "active_environment.local.json"

_ENV_VAR_DEFAULTS = {
    "client_id": ("ARENA_CLIENT_ID", ""),
    "client_secret": ("ARENA_CLIENT_SECRET", ""),
    "workspace_id": ("ARENA_WORKSPACE_ID", ""),
    "token_url": ("ARENA_TOKEN_URL", "https://oauth.bom.com/oauth2/token"),
    "api_base": ("ARENA_API_BASE", "https://api.arenasolutions.com/v1"),
    "usage_reason": ("ARENA_USAGE_REASON", "Claude / Arena MCP tooling"),
}


def _plain_env(field: str) -> str:
    """The plain .env/os.environ value for `field`, ignoring any active
    named-environment override. Used both as the override fallthrough and
    to revert to defaults when the active environment is deleted."""
    env_var, default = _ENV_VAR_DEFAULTS[field]
    return str(os.environ.get(env_var, default)).strip()


def _load_active_environment_overrides() -> tuple[dict[str, str], Optional[str]]:
    """Read ACTIVE_ENV_STATE_FILE and the named environment file it points
    at, if any. Returns (overrides, active_name) — ({}, None) if there's no
    active environment, the state file is missing/corrupt, or the named
    file it references no longer exists.

    Pulled out as its own function (rather than inlined at module level) so
    tests can call it directly after monkeypatching ENVIRONMENTS_DIR/
    ACTIVE_ENV_STATE_FILE, without needing to re-import the module (the
    ARENA_* constants below are only computed once, at first import).
    """
    if not ACTIVE_ENV_STATE_FILE.exists():
        return {}, None
    try:
        state = json.loads(ACTIVE_ENV_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, None
    name = state.get("name")
    if not name:
        return {}, None
    env_file = ENVIRONMENTS_DIR / f"{name}.json"
    if not env_file.exists():
        return {}, None
    try:
        overrides = json.loads(env_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, None
    return overrides, name


_active_overrides, _active_name = _load_active_environment_overrides()


def _configured(field: str) -> str:
    return str(_active_overrides.get(field) or _plain_env(field)).strip()


ARENA_CLIENT_ID = _configured("client_id")
ARENA_CLIENT_SECRET = _configured("client_secret")
ARENA_WORKSPACE_ID = _configured("workspace_id")
ARENA_TOKEN_URL = _configured("token_url")
ARENA_API_BASE = _configured("api_base").rstrip("/")
ARENA_USAGE_REASON = _configured("usage_reason")

SNAPSHOT_DIR = Path(
    os.environ.get("ARENA_SNAPSHOT_DIR") or _INSTALL_ROOT / "snapshots"
).expanduser().resolve()
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

_MISSING = [
    name for name, val in [
        ("ARENA_CLIENT_ID", ARENA_CLIENT_ID),
        ("ARENA_CLIENT_SECRET", ARENA_CLIENT_SECRET),
        ("ARENA_WORKSPACE_ID", ARENA_WORKSPACE_ID),
    ] if not val
]
if _MISSING:
    raise SystemExit(
        f"Missing required env var(s): {', '.join(_MISSING)}.\n"
        "Copy .env.example to .env and fill in your Arena Client Credentials."
    )
