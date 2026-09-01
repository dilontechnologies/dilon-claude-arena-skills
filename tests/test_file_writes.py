import json

import httpx

import arena_mcp_server as arena


def test_create_file_then_attach_to_item(arena_api, tmp_path):
    create_route = arena_api.post(f"{arena.ARENA_API_BASE}/files/json").mock(
        return_value=httpx.Response(201, json={"guid": "FILEGUID1", "title": "FO-00172 Battery Pack Traveler"})
    )
    local_pdf = tmp_path / "FO-00172 Rev 01.pdf"
    local_pdf.write_bytes(b"%PDF-1.4 fake pdf content")
    upload_route = arena_api.post(f"{arena.ARENA_API_BASE}/files/FILEGUID1/content").mock(
        return_value=httpx.Response(201, json={"ok": True})
    )
    attach_route = arena_api.post(f"{arena.ARENA_API_BASE}/items/ITEMGUID1/files").mock(
        return_value=httpx.Response(201, json={"guid": "ASSOC1", "primary": True})
    )

    file_result = arena.create_file(title="FO-00172 Battery Pack Traveler")
    assert file_result["guid"] == "FILEGUID1"
    # upload_file_content goes through _arena_post_multipart, which wraps the
    # response (Arena returns no JSON body on real multipart uploads) rather
    # than returning the JSON body directly.
    upload_result = arena.upload_file_content("FILEGUID1", str(local_pdf))
    assert upload_result == {"ok": True, "status_code": 201, "body": {"ok": True}}
    attach_result = arena.add_existing_file_to_item("ITEMGUID1", "FILEGUID1", primary=True)
    assert attach_result["primary"] is True

    sent_body = json.loads(create_route.calls[0].request.content)
    assert sent_body["title"] == "FO-00172 Battery Pack Traveler"
    assert create_route.call_count == 1
    assert upload_route.call_count == 1
    assert attach_route.call_count == 1


def test_create_file_edition_then_set_primary(arena_api, tmp_path):
    local_pdf = tmp_path / "WI-00088 Rev 02.pdf"
    local_pdf.write_bytes(b"%PDF-1.4 fake revised content")
    edition_route = arena_api.post(f"{arena.ARENA_API_BASE}/files/FILEGUID1/editions").mock(
        return_value=httpx.Response(201, json={"guid": "EDITIONGUID2", "edition": "02"})
    )
    primary_route = arena_api.put(f"{arena.ARENA_API_BASE}/items/ITEMGUID1/files/ASSOC1").mock(
        return_value=httpx.Response(200, json={"guid": "ASSOC1", "primary": True})
    )

    # create_file_edition (FILE storage) also goes through _arena_post_multipart.
    edition_result = arena.create_file_edition(
        file_guid="FILEGUID1", edition="02", local_path=str(local_pdf)
    )
    assert edition_result["ok"] is True
    assert edition_result["body"]["edition"] == "02"
    primary_result = arena.update_item_file_association(
        item_guid="ITEMGUID1", file_assoc_guid="ASSOC1", primary=True
    )
    assert primary_result["primary"] is True
    assert edition_route.call_count == 1
    assert primary_route.call_count == 1


def test_add_file_to_change_for_redline_traceability(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/CHG123/files").mock(
        return_value=httpx.Response(201, json={"guid": "REDLINEASSOC1"})
    )
    result = arena.add_file_to_change("CHG123", "REDLINEFILEGUID1")
    sent_body = json.loads(route.calls[0].request.content)
    assert sent_body == {
        "file": {"guid": "REDLINEFILEGUID1"},
        "latestEditionAssociation": True,
        "primary": False,
    }
    assert result["guid"] == "REDLINEASSOC1"
