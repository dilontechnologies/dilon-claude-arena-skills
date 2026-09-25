def test_confirmed_reachable(run_cli):
    code, out = run_cli(
        "phase_transitions.py",
        {
            "current_stage": "PRELIMINARY",
            "current_phase": "Unreleased",
            "target_stage": "PRODUCTION",
            "target_phase": "RELEASED",
        },
    )
    assert code == 0
    assert out["verdict"] == "REACHABLE"


def test_confirmed_blocked(run_cli):
    code, out = run_cli(
        "phase_transitions.py",
        {
            "current_stage": "PRELIMINARY",
            "current_phase": "Unreleased",
            "target_stage": "PRODUCTION",
            "target_phase": "Obsolete",
        },
    )
    assert code == 0
    assert out["verdict"] == "BLOCKED"


def test_unconfirmed_pair_is_unknown_not_reachable(run_cli):
    code, out = run_cli(
        "phase_transitions.py",
        {
            "current_stage": "DESIGN",
            "current_phase": "Prototype Release",
            "target_stage": "PRODUCTION",
            "target_phase": "RELEASED",
        },
    )
    assert code == 0
    assert out["verdict"] == "UNKNOWN"


def test_bad_input_exits_nonzero(run_cli):
    code, out = run_cli("phase_transitions.py", "not json")
    assert code == 1
