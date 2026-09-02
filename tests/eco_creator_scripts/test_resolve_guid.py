RESULTS = [
    {"name": "Form", "guid": "G1"},
    {"name": "Work Instructions", "guid": "G2"},
    {"name": "form", "guid": "G3"},  # duplicate name, different case
]


def test_exact_match(run_cli):
    code, out = run_cli("resolve_guid.py", {"results": RESULTS[:2], "target_name": "Work Instructions"})
    assert code == 0
    assert out["guid"] == "G2"


def test_case_insensitive_match(run_cli):
    code, out = run_cli("resolve_guid.py", {"results": RESULTS[:2], "target_name": "form"})
    assert code == 0
    assert out["guid"] == "G1"


def test_no_match_lists_available_names(run_cli):
    code, out = run_cli("resolve_guid.py", {"results": RESULTS[:2], "target_name": "Nope"})
    assert code == 1
    assert out["error"] is True
    assert "Form" in out["available_names"]


def test_ambiguous_match_errors(run_cli):
    code, out = run_cli("resolve_guid.py", {"results": RESULTS, "target_name": "form"})
    assert code == 1
    assert out["error"] is True
    assert set(out["guids"]) == {"G1", "G3"}


def test_bad_input_exits_nonzero(run_cli):
    code, out = run_cli("resolve_guid.py", "not json")
    assert code == 1
