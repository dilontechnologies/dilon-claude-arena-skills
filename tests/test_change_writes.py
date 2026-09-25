import json

import httpx

import arena_mcp_server as arena


def test_create_change_posts_expected_body(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes").mock(
        return_value=httpx.Response(201, json={"guid": "CHG123", "number": "ECO-00042"})
    )
    result = arena.create_change(
        title="Update Manufacturing Documents for 820-00006",
        category_guid="CATGUID1",
        additional_attributes=[{"guid": "ATTRGUID1", "value": "No effect"}],
    )
    assert result == {"guid": "CHG123", "number": "ECO-00042"}
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body["title"] == "Update Manufacturing Documents for 820-00006"
    assert sent_body["category"] == {"guid": "CATGUID1"}
    assert sent_body["additionalAttributes"] == [{"guid": "ATTRGUID1", "value": "No effect"}]


def test_create_change_dry_run_does_not_call_network(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes")
    result = arena.create_change(
        title="Update Manufacturing Documents for 820-00006",
        category_guid="CATGUID1",
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert route.call_count == 0


def test_401_then_200_retries_once_and_succeeds(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/CHG123/items")
    route.side_effect = [
        httpx.Response(401, json={"message": "token expired"}),
        httpx.Response(201, json={"guid": "ASSOC1"}),
    ]
    result = arena.add_items_to_change(
        change_guid="CHG123",
        items=[{"new_item_revision_guid": "REVGUID1", "files_view": True}],
        snapshot_first=False,
    )
    assert route.call_count == 2
    assert result["added"] == 1
    assert result["results"][0]["result"] == {"guid": "ASSOC1"}


def test_update_change_snapshots_before_writing(arena_api, tmp_path, monkeypatch):
    monkeypatch.setattr(arena.server.config, "SNAPSHOT_DIR", tmp_path)
    arena_api.get(f"{arena.ARENA_API_BASE}/changes/CHG123").mock(
        return_value=httpx.Response(200, json={"guid": "CHG123", "number": "ECO-00042"})
    )
    put_route = arena_api.put(f"{arena.ARENA_API_BASE}/changes/CHG123").mock(
        return_value=httpx.Response(200, json={"guid": "CHG123", "title": "New Title"})
    )
    result = arena.update_change(guid="CHG123", title="New Title")
    assert put_route.call_count == 1
    assert result["result"] == {"guid": "CHG123", "title": "New Title"}
    assert result["snapshot"]  # non-empty — a snapshot file was written
    assert list(tmp_path.glob("*.json")), "expected a snapshot file on disk"


def test_update_change_affected_item_sets_files_view(arena_api):
    route = arena_api.put(f"{arena.ARENA_API_BASE}/changes/CHG123/items/ASSOC1").mock(
        return_value=httpx.Response(200, json={"guid": "ASSOC1"})
    )
    arena.update_change_affected_item(
        change_guid="CHG123",
        association_guid="ASSOC1",
        views={"filesView": {"includedInThisChange": True}},
    )
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {"filesView": {"includedInThisChange": True}}


def test_cancel_change_posts_canceled_status(arena_api, tmp_path, monkeypatch):
    monkeypatch.setattr(arena.server.config, "SNAPSHOT_DIR", tmp_path)
    arena_api.get(f"{arena.ARENA_API_BASE}/changes/CHG123").mock(
        return_value=httpx.Response(200, json={"guid": "CHG123", "number": "ECO-00042"})
    )
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/statuschanges").mock(
        return_value=httpx.Response(200, json={"guid": "CHG123", "status": "CANCELED"})
    )
    result = arena.cancel_change(guid="CHG123", comment="Superseded by ECO-000300")
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {
        "change": {"guid": "CHG123"},
        "status": "CANCELED",
        "comment": "Superseded by ECO-000300",
    }
    assert result["result"]["status"] == "CANCELED"


def test_withdraw_change_posts_withdrawn_status(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/statuschanges").mock(
        return_value=httpx.Response(200, json={"guid": "CHG123", "status": "WITHDRAWN"})
    )
    arena.withdraw_change(change_guid="CHG123", comment="Pulling back for rework")
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {
        "change": {"guid": "CHG123"},
        "status": "WITHDRAWN",
        "comment": "Pulling back for rework",
    }


def test_uncomplete_change_posts_open_and_unlocked_status(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/statuschanges").mock(
        return_value=httpx.Response(200, json={"guid": "CHG123", "status": "OPEN_AND_UNLOCKED"})
    )
    arena.uncomplete_change(change_guid="CHG123")
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {"change": {"guid": "CHG123"}, "status": "OPEN_AND_UNLOCKED"}


def test_reopen_change_posts_reopened_status(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/statuschanges").mock(
        return_value=httpx.Response(200, json={"guid": "CHG123", "status": "REOPENED"})
    )
    arena.reopen_change(change_guid="CHG123")
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {"change": {"guid": "CHG123"}, "status": "REOPENED"}


def test_delete_change_calls_delete_endpoint(arena_api):
    route = arena_api.delete(f"{arena.ARENA_API_BASE}/changes/CHG123").mock(
        return_value=httpx.Response(204)
    )
    arena.delete_change(change_guid="CHG123")
    assert route.call_count == 1


def test_delete_change_dry_run_does_not_call_network(arena_api):
    route = arena_api.delete(f"{arena.ARENA_API_BASE}/changes/CHG123")
    result = arena.delete_change(change_guid="CHG123", dry_run=True)
    assert result["dry_run"] is True
    assert route.call_count == 0


def test_route_change_submits_with_administrators(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/statuschanges").mock(
        return_value=httpx.Response(200, json={"guid": "CHG123", "status": "SUBMITTED"})
    )
    result = arena.route_change(
        guid="CHG123",
        status="SUBMITTED",
        comment="Submitting for approval",
        administrator_guids=["ADMIN1"],
    )
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {
        "change": {"guid": "CHG123"},
        "status": "SUBMITTED",
        "comment": "Submitting for approval",
        "administrators": [{"guid": "ADMIN1"}],
    }
    assert result["status"] == "SUBMITTED"
