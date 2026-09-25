"""Shared sys.path setup so scripts in this directory can `import
arena_mcp_server` the same way tests/conftest.py does (pyproject.toml's
`pythonpath = ["arena_mcp"]` only applies under pytest, not a standalone
`python script.py` invocation).

Requires the same environment variables as the MCP server itself
(ARENA_CLIENT_ID, ARENA_CLIENT_SECRET, ARENA_WORKSPACE_ID, ARENA_TOKEN_URL,
ARENA_API_BASE) to be set in whatever shell invokes the script -- this is
a separate, independent authentication from whatever MCP server process
Claude Desktop/Code has running; it does not reuse that process's token.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ARENA_MCP_DIR = _REPO_ROOT / "arena_mcp"

if str(_ARENA_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_ARENA_MCP_DIR))

import arena_mcp_server as arena  # noqa: E402
