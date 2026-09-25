import httpx

import arena_mcp_server as arena


def test_delete_item_calls_delete_endpoint(arena_api):
    route = arena_api.delete(f"{arena.ARENA_API_BASE}/items/ITEMGUID1").mock(
        return_value=httpx.Response(204)
    )
    arena.delete_item(guid="ITEMGUID1")
    assert route.call_count == 1


def test_delete_item_dry_run_does_not_call_network(arena_api):
    route = arena_api.delete(f"{arena.ARENA_API_BASE}/items/ITEMGUID1")
    result = arena.delete_item(guid="ITEMGUID1", dry_run=True)
    assert result["dry_run"] is True
    assert route.call_count == 0
