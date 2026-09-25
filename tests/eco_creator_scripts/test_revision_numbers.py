import pytest


@pytest.mark.parametrize(
    "current_revision,target_family,expected",
    [
        (None, "PRODUCTION", "00"),
        (None, "PROTOTYPE", "00-A"),
        ("00-A", "PROTOTYPE", "00-B"),
        ("01", "PROTOTYPE", "02-A"),
        ("02-B", "PRODUCTION", "02"),
        ("01", "PRODUCTION", "02"),
    ],
)
def test_standard_revision_scheme(run_cli, current_revision, target_family, expected):
    code, out = run_cli(
        "revision_numbers.py",
        {"mode": "standard", "current_revision": current_revision, "target_family": target_family},
    )
    assert code == 0
    assert out["next_revision"] == expected


def test_reissue_no_prior_items(run_cli):
    code, out = run_cli(
        "revision_numbers.py",
        {"mode": "reissue", "item_number": "PL-00004", "existing_numbers": []},
    )
    assert code == 0
    assert out["next_revision"] == "PL-00004-01"


def test_reissue_with_prior_items(run_cli):
    code, out = run_cli(
        "revision_numbers.py",
        {
            "mode": "reissue",
            "item_number": "PL-00004",
            "existing_numbers": ["PL-00004-01", "PL-00004-03"],
        },
    )
    assert code == 0
    assert out["next_revision"] == "PL-00004-04"


def test_reissue_strips_existing_suffix_from_item_being_reissued(run_cli):
    # Re-revising PL-00004-01 roots to PL-00004, not PL-00004-01.
    code, out = run_cli(
        "revision_numbers.py",
        {
            "mode": "reissue",
            "item_number": "PL-00004-01",
            "existing_numbers": ["PL-00004-01"],
        },
    )
    assert code == 0
    assert out["next_revision"] == "PL-00004-02"


def test_unknown_mode(run_cli):
    code, out = run_cli("revision_numbers.py", {"mode": "bogus"})
    assert code == 1
    assert out["error"] is True


def test_bad_input_exits_nonzero(run_cli):
    code, out = run_cli("revision_numbers.py", "not json")
    assert code == 1
