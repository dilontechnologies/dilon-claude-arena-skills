"""Standalone extraction-verification helper — not a pytest file.

Usage: python tests/_extraction_smoke.py <dotted.module.path> <comma,separated,expected,__all__,names>

Imports the given module directly, asserts its __all__ matches the
expected name set exactly, then calls every exported function with
generic dummy args (forcing dry_run=True where the signature has it)
against a catch-all 200-OK mock, asserting each call returns a dict
without raising. Used only during the arena_mcp_server.py split to
verify each new server/tools/*.py module is self-contained (no missing
imports) before it's wired into server/__init__.py.
"""
import inspect
import os
import sys
from pathlib import Path

os.environ.setdefault("ARENA_CLIENT_ID", "test-client-id")
os.environ.setdefault("ARENA_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("ARENA_WORKSPACE_ID", "test-workspace-id")
os.environ.setdefault("ARENA_TOKEN_URL", "https://oauth.bom.com/oauth2/token")
os.environ.setdefault("ARENA_API_BASE", "https://api.arenasolutions.com/v1")
os.environ.setdefault("ARENA_SNAPSHOT_DIR", str(Path(__file__).parent / "_snapshots_test"))

sys.path.insert(0, str(Path(__file__).parent.parent / "arena_mcp"))

import importlib
import httpx
import respx


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


def main(module_path: str, expected_names: set[str]) -> None:
    mod = importlib.import_module(module_path)
    actual = set(mod.__all__)
    assert actual == expected_names, (
        f"__all__ mismatch for {module_path}\n"
        f"  missing: {expected_names - actual}\n"
        f"  extra:   {actual - expected_names}"
    )

    from server import config

    with respx.mock:
        respx.post(config.ARENA_TOKEN_URL).mock(
            return_value=httpx.Response(200, json={"access_token": "t", "expires_in": 5399})
        )
        respx.route(url__startswith=config.ARENA_API_BASE).mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "totalResults": 0, "guid": "GUID000000000000TEST"},
            )
        )
        for name in sorted(mod.__all__):
            fn = getattr(mod, name)
            result = fn(**_dummy_args(fn))
            assert isinstance(result, dict), f"{name} returned {type(result)}, expected dict"

    print(f"OK  {module_path}  ({len(mod.__all__)} tools verified)")


if __name__ == "__main__":
    main(sys.argv[1], set(sys.argv[2].split(",")))
