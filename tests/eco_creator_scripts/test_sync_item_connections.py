import httpx

import sync_item_connections
from sync_item_connections import arena


def test_unapproved_target_is_skipped_and_never_queried_or_created(arena_api):
    get_route = arena_api.get(f"{arena.ARENA_API_BASE}/items/ITEM1/items")
    create_route = arena_api.post(f"{arena.ARENA_API_BASE}/items/ITEM1/items")

    result = sync_item_connections.sync("ITEM1", [{"to_item_guid": "ITEM2"}])

    assert result["ok"] is True
    assert result["results"][0]["action"] == "SKIPPED_NOT_APPROVED"
    assert get_route.call_count == 0
    assert create_route.call_count == 0


def test_approved_false_is_also_skipped(arena_api):
    result = sync_item_connections.sync("ITEM1", [{"to_item_guid": "ITEM2", "approved": False}])
    assert result["results"][0]["action"] == "SKIPPED_NOT_APPROVED"


def test_approved_and_already_linked_is_skipped(arena_api):
    arena_api.get(f"{arena.ARENA_API_BASE}/items/ITEM1/items").mock(
        return_value=httpx.Response(
            200, json={"count": 1, "results": [{"guid": "REF1", "item": {"guid": "ITEM2"}}]}
        )
    )
    create_route = arena_api.post(f"{arena.ARENA_API_BASE}/items/ITEM1/items")

    result = sync_item_connections.sync("ITEM1", [{"to_item_guid": "ITEM2", "approved": True}])

    assert result["ok"] is True
    assert result["results"][0]["action"] == "SKIPPED_ALREADY_LINKED"
    assert create_route.call_count == 0


def test_approved_and_not_linked_creates(arena_api):
    arena_api.get(f"{arena.ARENA_API_BASE}/items/ITEM1/items").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    arena_api.post(f"{arena.ARENA_API_BASE}/items/ITEM1/items").mock(
        return_value=httpx.Response(201, json={"guid": "NEWREF"})
    )

    result = sync_item_connections.sync("ITEM1", [{"to_item_guid": "ITEM2", "approved": True}])

    assert result["ok"] is True
    assert result["results"][0]["action"] == "CREATED"


def test_create_error_is_reported_not_swallowed(arena_api):
    arena_api.get(f"{arena.ARENA_API_BASE}/items/ITEM1/items").mock(
        return_value=httpx.Response(200, json={"count": 0, "results": []})
    )
    arena_api.post(f"{arena.ARENA_API_BASE}/items/ITEM1/items").mock(
        return_value=httpx.Response(400, json={"message": "boom"})
    )

    result = sync_item_connections.sync("ITEM1", [{"to_item_guid": "ITEM2", "approved": True}])

    assert result["ok"] is False
    assert result["results"][0]["action"] == "ERROR"


def test_multiple_targets_independent_approval(arena_api):
    arena_api.get(f"{arena.ARENA_API_BASE}/items/ITEM1/items").mock(
        return_value=httpx.Response(
            200, json={"count": 1, "results": [{"guid": "REF1", "item": {"guid": "ITEM2"}}]}
        )
    )
    arena_api.post(f"{arena.ARENA_API_BASE}/items/ITEM1/items").mock(
        return_value=httpx.Response(201, json={"guid": "NEWREF"})
    )

    result = sync_item_connections.sync(
        "ITEM1",
        [
            {"to_item_guid": "ITEM2", "approved": True},  # already linked
            {"to_item_guid": "ITEM3", "approved": True},  # not linked -> created
            {"to_item_guid": "ITEM4"},  # not approved -> skipped, no calls
        ],
    )

    actions = {r["to_item_guid"]: r["action"] for r in result["results"]}
    assert actions["ITEM2"] == "SKIPPED_ALREADY_LINKED"
    assert actions["ITEM3"] == "CREATED"
    assert actions["ITEM4"] == "SKIPPED_NOT_APPROVED"
