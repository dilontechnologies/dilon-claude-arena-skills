import os
from pathlib import Path

# Must run before `import arena_mcp_server` anywhere — the module raises
# SystemExit at import time if these are unset. conftest.py loads before any
# test module in this directory, so this ordering is safe.
os.environ.setdefault("ARENA_CLIENT_ID", "test-client-id")
os.environ.setdefault("ARENA_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("ARENA_WORKSPACE_ID", "test-workspace-id")
os.environ.setdefault("ARENA_TOKEN_URL", "https://oauth.bom.com/oauth2/token")
os.environ.setdefault("ARENA_API_BASE", "https://api.arenasolutions.com/v1")
os.environ.setdefault(
    "ARENA_SNAPSHOT_DIR", str(Path(__file__).parent / "_snapshots_test")
)

import httpx
import pytest

import arena_mcp_server as arena


@pytest.fixture
def arena_api(respx_mock):
    """A respx mock router with the Arena OAuth token endpoint pre-mocked.

    Tests add their own route mocks on top, e.g.:
        arena_api.get(f"{arena.ARENA_API_BASE}/items/GUID123").mock(
            return_value=httpx.Response(200, json={...})
        )
    """
    respx_mock.post(arena.ARENA_TOKEN_URL).mock(
        return_value=httpx.Response(
            200, json={"access_token": "test-token", "expires_in": 5399}
        )
    )
    return respx_mock
