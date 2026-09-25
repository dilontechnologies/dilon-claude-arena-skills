EXISTING_PDF = [
    {
        "guid": "ASSOC1",
        "name": "FO-00127 Rev 02-A.pdf",
        "file": {"guid": "FILE1", "name": "FO-00127 Rev 02-A.pdf"},
    }
]


def test_nothing_attached_yet_creates_file(run_cli):
    code, out = run_cli(
        "file_attach_decision.py",
        {"item_files": [], "target_format": "pdf", "revision_status": "WORKING"},
    )
    assert code == 0
    assert out["action"] == "CREATE_FILE"


def test_existing_attachment_working_revision_uploads_in_place(run_cli):
    code, out = run_cli(
        "file_attach_decision.py",
        {"item_files": EXISTING_PDF, "target_format": "pdf", "revision_status": "WORKING"},
    )
    assert code == 0
    assert out["action"] == "UPLOAD_CONTENT"
    assert out["file_guid"] == "FILE1"
    assert out["assoc_guid"] == "ASSOC1"


def test_existing_attachment_released_revision_is_blocked(run_cli):
    code, out = run_cli(
        "file_attach_decision.py",
        {"item_files": EXISTING_PDF, "target_format": "pdf", "revision_status": "RELEASED"},
    )
    assert code == 0
    assert out["action"] == "BLOCKED_NEEDS_EDITION"
    assert out["file_guid"] == "FILE1"


def test_format_mismatch_is_treated_as_not_attached(run_cli):
    code, out = run_cli(
        "file_attach_decision.py",
        {"item_files": EXISTING_PDF, "target_format": "docx", "revision_status": "WORKING"},
    )
    assert code == 0
    assert out["action"] == "CREATE_FILE"


def test_unknown_revision_status_errors(run_cli):
    # Needs a matching existing attachment -- with nothing attached, the
    # decision is CREATE_FILE regardless of revision_status, so this must
    # exercise the "already attached" branch to actually reach the check.
    code, out = run_cli(
        "file_attach_decision.py",
        {"item_files": EXISTING_PDF, "target_format": "pdf", "revision_status": "BOGUS"},
    )
    assert code == 1


def test_bad_input_exits_nonzero(run_cli):
    code, out = run_cli("file_attach_decision.py", "not json")
    assert code == 1
