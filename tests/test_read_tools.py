import inspect
import json
from pathlib import Path

import httpx
import pytest

import arena_mcp_server as arena

FIXTURES = Path(__file__).parent / "fixtures"

# get_snapshot reads ARENA_SNAPSHOT_DIR directly, not the Arena API — tested
# separately below against a real local fixture file instead of the network mock.
EXCLUDED_FROM_GENERIC_MOCK = {"get_snapshot"}


def _discover_read_tools():
    tools = []
    for name, fn in inspect.getmembers(arena, inspect.isfunction):
        if fn.__module__ != arena.__name__:
            continue
        if name in EXCLUDED_FROM_GENERIC_MOCK:
            continue
        if name == "whoami" or name.startswith(("get_", "list_", "search_")):
            tools.append((name, fn))
    return tools


READ_TOOLS = _discover_read_tools()


def _dummy_args(fn):
    sig = inspect.signature(fn)
    kwargs = {}
    for pname, param in sig.parameters.items():
        if param.default is not inspect.Parameter.empty:
            continue  # optional — leave at its default
        ann = param.annotation
        if ann is list or "list" in str(ann):
            kwargs[pname] = ["GUID000000000000TEST"]
        elif ann is int:
            kwargs[pname] = 1
        else:
            kwargs[pname] = "GUID000000000000TEST"
    return kwargs


def test_discovery_found_a_substantial_number_of_read_tools():
    # Guards against the discovery logic silently finding zero tools if
    # arena_mcp_server.py's naming convention ever changes.
    assert len(READ_TOOLS) > 100


@pytest.mark.parametrize("name,fn", READ_TOOLS, ids=[t[0] for t in READ_TOOLS])
def test_read_tool_succeeds_against_mocked_arena(name, fn, arena_api):
    arena_api.route(url__startswith=arena.ARENA_API_BASE).mock(
        return_value=httpx.Response(200, json={"results": [], "totalResults": 0})
    )
    result = fn(**_dummy_args(fn))
    assert isinstance(result, dict), f"{name} returned {type(result)}, expected dict"
    assert not result.get("error"), f"{name} returned an error against a 200 mock: {result}"


def test_get_snapshot_reads_local_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(arena, "SNAPSHOT_DIR", tmp_path)
    (tmp_path / "snap-001.json").write_text(json.dumps({"id": "snap-001", "kind": "test"}))
    result = arena.get_snapshot("snap-001")
    assert result == {"id": "snap-001", "kind": "test"}


def test_list_item_categories_shape(arena_api):
    fixture = json.loads((FIXTURES / "list_item_categories.json").read_text())
    arena_api.get(f"{arena.ARENA_API_BASE}/settings/items/categories").mock(
        return_value=httpx.Response(200, json=fixture)
    )
    result = arena.list_item_categories()
    assert result == fixture


def test_search_items_shape(arena_api):
    fixture = json.loads((FIXTURES / "search_items.json").read_text())
    arena_api.get(url__startswith=f"{arena.ARENA_API_BASE}/items").mock(
        return_value=httpx.Response(200, json=fixture)
    )
    result = arena.search_items()
    assert result == fixture
