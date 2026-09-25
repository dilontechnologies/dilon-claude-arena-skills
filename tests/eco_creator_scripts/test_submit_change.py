import io
import json

import httpx

import submit_change
from submit_change import arena


def test_submit_success_two_call_sequence(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/statuschanges")
    route.side_effect = [
        httpx.Response(200, json={"guid": "CHG1", "lifecycleStatus": "SUBMITTED_FOR_ROUTING"}),
        httpx.Response(200, json={"guid": "CHG1", "lifecycleStatus": "EFFECTIVE"}),
    ]
    result = submit_change.submit("CHG1", ["ADMIN1"], "comment text")
    assert result["ok"] is True
    assert result["final_status"] == "EFFECTIVE"
    assert route.call_count == 2

    first_body = json.loads(route.calls[0].request.content)
    second_body = json.loads(route.calls[1].request.content)
    assert first_body["administrators"] == [{"guid": "ADMIN1"}]
    assert "administrators" not in second_body


def test_submit_stops_if_first_call_errors(arena_api):
    arena_api.post(f"{arena.ARENA_API_BASE}/changes/statuschanges").mock(
        return_value=httpx.Response(400, json={"message": "Invalid change administrator guid"})
    )
    result = submit_change.submit("CHG1", ["BADGUID"], None)
    assert result["ok"] is False
    assert result["stopped_after"] == "first_call"


def test_submit_stops_if_second_call_errors(arena_api):
    route = arena_api.post(f"{arena.ARENA_API_BASE}/changes/statuschanges")
    route.side_effect = [
        httpx.Response(200, json={"guid": "CHG1", "lifecycleStatus": "SUBMITTED_FOR_ROUTING"}),
        httpx.Response(400, json={"message": "some error"}),
    ]
    result = submit_change.submit("CHG1", ["ADMIN1"], None)
    assert result["ok"] is False
    assert result["stopped_after"] == "second_call"


def test_main_refuses_without_confirmed_flag(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(json.dumps({"change_guid": "CHG1", "administrator_guids": ["A1"]})),
    )
    code = submit_change.main()
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["error"] is True
