"""Smoke-calls every @mcp.tool() function, not just the get_/list_/search_
subset test_read_tools.py covers. Exists because dozens of write tools
(items, BOM, quality, training, suppliers, supplier items) have no other
test coverage — this only proves each one runs without raising, not that
its behavior is correct (that's test_change_writes.py/test_file_writes.py's
job for the subset they cover).
"""
import inspect

import httpx
import pytest

import arena_mcp_server as arena


def _discover_all_tools():
    tools = []
    for name, fn in inspect.getmembers(arena, inspect.isfunction):
        if fn.__module__ != arena.__name__ and not fn.__module__.startswith("server."):
            continue
        if name.startswith("_"):
            continue  # internal helpers (e.g. _arena_get, _safe_json) aren't tools
        tools.append((name, fn))
    return tools


ALL_TOOLS = _discover_all_tools()


def test_discovery_found_all_tools():
    assert len(ALL_TOOLS) == 290


def _dummy_args(fn):
    sig = inspect.signature(fn)
    kwargs = {}
    for pname, param in sig.parameters.items():
        if param.default is not inspect.Parameter.empty:
            if pname == "dry_run":
                kwargs["dry_run"] = True
            continue
        ann = param.annotation
        if "list" in str(ann) and "dict" in str(ann):
            kwargs[pname] = [{"new_item_revision_guid": "GUID000000000000TEST"}]
        elif ann is list or "list" in str(ann):
            kwargs[pname] = ["GUID000000000000TEST"]
        elif ann is int:
            kwargs[pname] = 1
        else:
            kwargs[pname] = "GUID000000000000TEST"
    return kwargs


@pytest.mark.parametrize("name,fn", ALL_TOOLS, ids=[t[0] for t in ALL_TOOLS])
def test_tool_runs_without_raising(name, fn, arena_api):
    arena_api.route(url__startswith=arena.ARENA_API_BASE).mock(
        return_value=httpx.Response(
            200, json={"results": [], "totalResults": 0, "guid": "GUID000000000000TEST"}
        )
    )
    result = fn(**_dummy_args(fn))
    assert isinstance(result, dict), f"{name} returned {type(result)}, expected dict"
