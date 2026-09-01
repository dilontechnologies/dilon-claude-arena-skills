from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_INSTALL_ROOT = Path(__file__).resolve().parent.parent


def _configured(key: str, env_var: str, default: str = "") -> str:
    return str(os.environ.get(env_var, default)).strip()


ARENA_CLIENT_ID = _configured("client_id", "ARENA_CLIENT_ID")
ARENA_CLIENT_SECRET = _configured("client_secret", "ARENA_CLIENT_SECRET")
ARENA_WORKSPACE_ID = _configured("workspace_id", "ARENA_WORKSPACE_ID")

ARENA_TOKEN_URL = _configured(
    "token_url", "ARENA_TOKEN_URL", "https://oauth.bom.com/oauth2/token"
)
ARENA_API_BASE = _configured(
    "api_base", "ARENA_API_BASE", "https://api.arenasolutions.com/v1"
).rstrip("/")
ARENA_USAGE_REASON = _configured(
    "usage_reason", "ARENA_USAGE_REASON", "Claude / Arena MCP tooling"
)

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
