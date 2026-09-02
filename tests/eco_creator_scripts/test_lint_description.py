GOOD_DESCRIPTION = """Update Manufacturing Documents for 820-00006 Detector Head.

Released to Prototype Release: FO-00127.
Released: WI-00077.
Obsoleted: none.

Ref: CAPA-1234.

Does this change meet any of the following criteria? (Yes / No)

1. Could reasonably affect device safety or effectiveness
NO
2. Materially affects intended purpose, design, clinical performance, or benefit-risk profile
NO
3. Results in a change to QMS scope
NO
4. Introduces a new intended purpose, patient population, or clinical indication
NO
5. Major design change affecting performance, safety, operating principles, or clinical function
NO
6. Adds a product or process not covered by the current ISO certification
NO
"""


def test_golden_standard_description_passes(run_cli):
    code, out = run_cli("lint_description.py", {"description": GOOD_DESCRIPTION})
    assert code == 0
    assert out["ok"] is True
    assert out["errors"] == []


def test_missing_ref_line_is_an_error(run_cli):
    broken = GOOD_DESCRIPTION.replace("Ref: CAPA-1234.\n\n", "")
    code, out = run_cli("lint_description.py", {"description": broken})
    assert code == 1
    assert out["ok"] is False
    assert any("Ref:" in e for e in out["errors"])


def test_missing_question_is_an_error(run_cli):
    broken = GOOD_DESCRIPTION.replace(
        "6. Adds a product or process not covered by the current ISO certification\nNO\n", ""
    )
    code, out = run_cli("lint_description.py", {"description": broken})
    assert code == 1
    assert any("ISO certification" in e for e in out["errors"])


def test_lowercase_answer_is_a_warning_not_an_error(run_cli):
    broken = GOOD_DESCRIPTION.replace(
        "1. Could reasonably affect device safety or effectiveness\nNO\n",
        "1. Could reasonably affect device safety or effectiveness\nno\n",
    )
    code, out = run_cli("lint_description.py", {"description": broken})
    assert code == 0
    assert out["ok"] is True
    assert any("no" in w for w in out["warnings"])


def test_missing_screening_header_is_an_error(run_cli):
    broken = GOOD_DESCRIPTION.replace(
        "Does this change meet any of the following criteria? (Yes / No)\n\n", ""
    )
    code, out = run_cli("lint_description.py", {"description": broken})
    assert code == 1
    assert any("header" in e.lower() for e in out["errors"])


def test_bad_input_exits_nonzero(run_cli):
    code, out = run_cli("lint_description.py", "not json")
    assert code == 1
