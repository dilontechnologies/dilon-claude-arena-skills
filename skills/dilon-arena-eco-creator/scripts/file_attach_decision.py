#!/usr/bin/env python3
"""Decide which step 8 branch applies for one expected file format.

This is the exact decision that produced the real ECO-000262 mistake
(create_file called for formats that already had an attached edition,
producing 8 orphaned duplicate file records) -- it existing as prose the
agent re-derives every time is the risk this script removes.

NOTE on field matching: this looks for an existing attachment by checking
each get_item_files() entry's filename-like field
(name/title/file.name/file.title) for a "....<format>" extension, since
file `name` follows the "<Item Number> Rev <Revision Number>.<ext>"
convention. Not independently verified against a raw API response; if
Arena's actual get_item_files shape nests differently, fix
`_candidate_names` below.

Usage:
    echo '{"item_files": [...], "target_format": "pdf",
           "revision_status": "WORKING"}' | python file_attach_decision.py

Output, one of:
    {"action": "CREATE_FILE", "reason": "..."}
    {"action": "UPLOAD_CONTENT", "file_guid": "...", "assoc_guid": "...", "reason": "..."}
    {"action": "BLOCKED_NEEDS_EDITION", "file_guid": "...", "assoc_guid": "...", "reason": "..."}
Exit code 0 on a successful decision, 1 on malformed input.
"""
from __future__ import annotations

import json
import sys
from typing import Any


def _candidate_names(entry: dict[str, Any]) -> list[str]:
    file_obj = entry.get("file") or {}
    return [
        n
        for n in (
            entry.get("name"),
            entry.get("title"),
            file_obj.get("name"),
            file_obj.get("title"),
        )
        if n
    ]


def decide(
    item_files: list[dict[str, Any]], target_format: str, revision_status: str
) -> dict[str, Any]:
    ext = "." + target_format.lstrip(".").lower()
    match = None
    for entry in item_files:
        if any(name.lower().endswith(ext) for name in _candidate_names(entry)):
            match = entry
            break

    if match is None:
        return {
            "action": "CREATE_FILE",
            "reason": f"No existing {target_format} attachment found for this item.",
        }

    file_obj = match.get("file") or {}
    file_guid = file_obj.get("guid") or match.get("fileGuid")
    assoc_guid = match.get("guid") or match.get("associationGuid")

    if revision_status == "WORKING":
        return {
            "action": "UPLOAD_CONTENT",
            "file_guid": file_guid,
            "assoc_guid": assoc_guid,
            "reason": (
                "Existing attachment found; item revision is WORKING under "
                "this change -- replace content in place with "
                "upload_file_content, no edition bump."
            ),
        }
    if revision_status == "RELEASED":
        return {
            "action": "BLOCKED_NEEDS_EDITION",
            "file_guid": file_guid,
            "assoc_guid": assoc_guid,
            "reason": (
                "Existing attachment found; item revision is still RELEASED "
                "-- needs a genuine new edition via create_file_edition, "
                "which is currently confirmed broken (see SKILL.md's Known "
                "Limitations). Do not call it blind; tell the user."
            ),
        }
    raise ValueError(f"Unknown revision_status: {revision_status!r} (expected WORKING or RELEASED)")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = decide(
            payload["item_files"], payload["target_format"], payload["revision_status"]
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"error": True, "message": f"Bad input: {exc}"}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
