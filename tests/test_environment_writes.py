"""Tests for the runtime environment-switching tools (server/tools/environments.py).

Because these tools mutate module-level globals on server.config (by
design — that's what makes a switch take effect without a restart), every
test in this file runs through the _isolate_environment_state autouse
fixture, which points ENVIRONMENTS_DIR/ACTIVE_ENV_STATE_FILE at a tmp_path
and restores every ARENA_* attribute + _active_name after each test.
"""
import json
import time

import httpx
import pytest

import arena_mcp_server as arena


@pytest.fixture(autouse=True)
def _isolate_environment_state(monkeypatch, tmp_path):
    cfg = arena.server.config
    monkeypatch.setattr(cfg, "ENVIRONMENTS_DIR", tmp_path / "environments.local")
    monkeypatch.setattr(cfg, "ACTIVE_ENV_STATE_FILE", tmp_path / "active_environment.local.json")
    for attr in (
        "ARENA_CLIENT_ID", "ARENA_CLIENT_SECRET", "ARENA_WORKSPACE_ID",
        "ARENA_TOKEN_URL", "ARENA_API_BASE", "ARENA_USAGE_REASON", "_active_name",
    ):
        monkeypatch.setattr(cfg, attr, getattr(cfg, attr))
    yield
    arena.server.core.reset_connection()


def test_set_environment_applies_overrides_and_validates(arena_api):
    result = arena.set_environment(workspace_id="SANDBOX123")
    assert result["auth"] == "ok"
    assert arena.server.config.ARENA_WORKSPACE_ID == "SANDBOX123"
    assert result["applied"]["workspace_id"] == "SANDBOX123"
    assert "client_secret" not in result["applied"]


def test_set_environment_resets_connection(arena_api):
    token_route = arena_api.post(arena.server.config.ARENA_TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "fresh-token", "expires_in": 5399})
    )
    arena.server.core._token_cache["access_token"] = "stale-token"
    arena.server.core._token_cache["expires_at"] = time.time() + 3600
    arena.set_environment(workspace_id="SANDBOX123")
    assert token_route.call_count == 1
    assert arena.server.core._token_cache["access_token"] == "fresh-token"


def test_set_environment_dry_run_applies_nothing(arena_api):
    before = arena.server.config.ARENA_WORKSPACE_ID
    result = arena.set_environment(workspace_id="SHOULD_NOT_APPLY", dry_run=True)
    assert result["dry_run"] is True
    assert result["would_apply"]["workspace_id"] == "SHOULD_NOT_APPLY"
    assert arena.server.config.ARENA_WORKSPACE_ID == before
    assert not arena.server.config.ACTIVE_ENV_STATE_FILE.exists()


def test_set_environment_validation_failure_rolls_back(arena_api):
    before = arena.server.config.ARENA_WORKSPACE_ID
    arena_api.post(arena.server.config.ARENA_TOKEN_URL).mock(
        return_value=httpx.Response(401, json={"message": "bad credentials"})
    )
    result = arena.set_environment(client_secret="wrong-secret")
    assert result["error"] is True
    assert arena.server.config.ARENA_WORKSPACE_ID == before


def test_set_environment_save_as_persists_named_environment(arena_api):
    result = arena.set_environment(workspace_id="SANDBOX123", save_as="sandbox")
    assert result["saved_as"] == "sandbox"
    saved = json.loads((arena.server.config.ENVIRONMENTS_DIR / "sandbox.json").read_text())
    assert saved["workspace_id"] == "SANDBOX123"
    state = json.loads(arena.server.config.ACTIVE_ENV_STATE_FILE.read_text())
    assert state == {"name": "sandbox"}
    assert arena.server.config._active_name == "sandbox"


def test_set_environment_without_save_as_is_session_only(arena_api):
    arena.set_environment(workspace_id="AD_HOC_ID")
    assert not arena.server.config.ACTIVE_ENV_STATE_FILE.exists()
    assert arena.server.config._active_name is None


def test_switch_environment_loads_named_file_with_env_fallthrough(arena_api, monkeypatch):
    monkeypatch.setenv("ARENA_CLIENT_ID", "fallthrough-client-id")
    arena.server.config.ENVIRONMENTS_DIR.mkdir(parents=True, exist_ok=True)
    (arena.server.config.ENVIRONMENTS_DIR / "sandbox.json").write_text(
        json.dumps({"workspace_id": "SANDBOX123"})
    )
    result = arena.switch_environment("sandbox")
    assert result["active"] == "sandbox"
    assert arena.server.config.ARENA_WORKSPACE_ID == "SANDBOX123"
    assert arena.server.config.ARENA_CLIENT_ID == "fallthrough-client-id"
    state = json.loads(arena.server.config.ACTIVE_ENV_STATE_FILE.read_text())
    assert state == {"name": "sandbox"}


def test_switch_environment_unknown_name_errors(arena_api):
    result = arena.switch_environment("does-not-exist")
    assert result["error"] is True


def test_list_environments_never_returns_raw_secret(arena_api):
    arena.set_environment(workspace_id="SANDBOX123", client_secret="super-secret", save_as="sandbox")
    result = arena.list_environments()
    assert result["active"] == "sandbox"
    entry = next(e for e in result["environments"] if e["name"] == "sandbox")
    assert entry["client_secret_set"] is True
    assert "client_secret" not in entry
    assert "super-secret" not in json.dumps(result)


def test_get_active_environment_never_returns_raw_secret(arena_api):
    arena.set_environment(client_secret="super-secret")
    result = arena.get_active_environment()
    assert "client_secret" not in result
    assert result["client_secret_set"] is True
    assert "super-secret" not in json.dumps(result)


def test_delete_environment_reverts_active_session_to_env_defaults(arena_api, monkeypatch):
    monkeypatch.setenv("ARENA_WORKSPACE_ID", "DEFAULT_FROM_ENV")
    arena.set_environment(workspace_id="SANDBOX123", save_as="sandbox")
    result = arena.delete_environment("sandbox")
    assert result["was_active"] is True
    assert arena.server.config.ARENA_WORKSPACE_ID == "DEFAULT_FROM_ENV"
    assert arena.server.config._active_name is None
    assert not arena.server.config.ACTIVE_ENV_STATE_FILE.exists()
    assert not (arena.server.config.ENVIRONMENTS_DIR / "sandbox.json").exists()


def test_delete_environment_unknown_name_errors(arena_api):
    result = arena.delete_environment("does-not-exist")
    assert result["error"] is True


@pytest.mark.parametrize("bad_name", ["../../etc/passwd", "..", "a/b", "a\\b", ""])
def test_switch_environment_rejects_path_traversal_names(arena_api, bad_name):
    result = arena.switch_environment(bad_name)
    assert result["error"] is True


@pytest.mark.parametrize("bad_name", ["../../etc/passwd", "..", "a/b", "a\\b", ""])
def test_delete_environment_rejects_path_traversal_names(arena_api, bad_name):
    result = arena.delete_environment(bad_name)
    assert result["error"] is True


@pytest.mark.parametrize("bad_name", ["../../etc/passwd", "..", "a/b", "a\\b"])
def test_set_environment_rejects_path_traversal_save_as(arena_api, bad_name):
    result = arena.set_environment(workspace_id="SANDBOX123", save_as=bad_name)
    assert result["error"] is True
    assert not arena.server.config.ACTIVE_ENV_STATE_FILE.exists()
