ATTRS = [
    {"guid": "A1", "name": "Product Change?", "multiSelect": False, "possibleValues": ["Yes", "No"]},
    {
        "guid": "A2",
        "name": "Affected Items",
        "multiSelect": True,
        "possibleValues": ["Other Document(s)", "Form (FO)", "Work Instruction (WI)"],
    },
    {"guid": "A3", "name": "Evaluation Performed By", "multiSelect": False},
]


def test_single_select_string_passthrough(run_cli):
    code, out = run_cli("additional_attributes.py", {"attributes": ATTRS, "values": {"Product Change?": "No"}})
    assert code == 0
    assert out["additional_attributes"] == [{"guid": "A1", "value": "No"}]


def test_multiselect_string_wrapped_in_array(run_cli):
    code, out = run_cli(
        "additional_attributes.py",
        {"attributes": ATTRS, "values": {"Affected Items": "Other Document(s)"}},
    )
    assert code == 0
    assert out["additional_attributes"] == [{"guid": "A2", "value": ["Other Document(s)"]}]


def test_multiselect_already_a_list_left_alone(run_cli):
    code, out = run_cli(
        "additional_attributes.py",
        {"attributes": ATTRS, "values": {"Affected Items": ["Form (FO)", "Work Instruction (WI)"]}},
    )
    assert code == 0
    assert out["additional_attributes"] == [{"guid": "A2", "value": ["Form (FO)", "Work Instruction (WI)"]}]


def test_value_not_in_possible_values_is_a_warning_not_error(run_cli):
    code, out = run_cli(
        "additional_attributes.py",
        {"attributes": ATTRS, "values": {"Product Change?": "Maybe"}},
    )
    assert code == 0
    assert out["additional_attributes"] == [{"guid": "A1", "value": "Maybe"}]
    assert any("Maybe" in w for w in out["warnings"])


def test_unmatched_display_name_is_a_hard_error(run_cli):
    code, out = run_cli(
        "additional_attributes.py",
        {"attributes": ATTRS, "values": {"Nonexistent Field": "x"}},
    )
    assert code == 1
    assert out["error"] is True
    assert "Nonexistent Field" in out["message"]


def test_bad_input_exits_nonzero(run_cli):
    code, out = run_cli("additional_attributes.py", "not json")
    assert code == 1
