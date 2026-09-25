#!/usr/bin/env python3
"""Create SKILL.md step 8b's item-to-item connections, idempotently, and
only for targets the user has actually approved.

Each target must carry `"approved": true` -- set only after SKILL.md step
8b's "get user approval before creating any of them" step, listing the
proposed connections and getting explicit confirmation. A target missing
`approved` (or with it false) is skipped, not created -- this script does
not ask for approval itself, and refuses to guess consent from omission.

For each approved target, checks get_item_references(from_item_guid)
fresh before creating a link -- get_item_references is bidirectional
(querying either item in a link returns it), so this avoids creating a
duplicate reference record when two documents that list each other (e.g.
a WI and its Traveler) each run this script during the same or a later ECO.

This script performs LIVE calls itself (see _arena_import.py for the
required environment variables).

Usage:
    echo '{"from_item_guid": "ITEM1",
           "targets": [{"to_item_guid": "ITEM2", "approved": true, "notes": "optional"}]}' \
        | python sync_item_connections.py

Output: {"results": [{"to_item_guid": ..., "action":
         "SKIPPED_NOT_APPROVED"|"SKIPPED_ALREADY_LINKED"|"CREATED"|"ERROR",
         "detail": {...}}, ...]}
Exit code 0 if every approved target succeeded or was already linked, 1
if any approved target's create call errored.
"""
from __future__ import annotations

import json
import sys
from typing import Any

from _arena_import import arena


def _already_linked(from_item_guid: str, to_item_guid: str) -> bool:
    existing = arena.get_item_references(from_item_guid)
    if not isinstance(existing, dict) or existing.get("error"):
        # Can't confirm either way -- treat as not-yet-linked and let the
        # create call itself be the source of truth, rather than silently
        # skipping a link this check couldn't actually verify.
        return False
    for entry in existing.get("results", []) or []:
        item = entry.get("item") or {}
        if item.get("guid") == to_item_guid:
            return True
    return False


def sync(from_item_guid: str, targets: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    any_error = False
    for target in targets:
        to_item_guid = target["to_item_guid"]
        if not target.get("approved"):
            results.append({"to_item_guid": to_item_guid, "action": "SKIPPED_NOT_APPROVED"})
            continue
        if _already_linked(from_item_guid, to_item_guid):
            results.append({"to_item_guid": to_item_guid, "action": "SKIPPED_ALREADY_LINKED"})
            continue
        outcome = arena.create_item_reference(
            from_item_guid=from_item_guid,
            to_item_guid=to_item_guid,
            notes=target.get("notes"),
        )
        if isinstance(outcome, dict) and outcome.get("error"):
            any_error = True
            results.append({"to_item_guid": to_item_guid, "action": "ERROR", "detail": outcome})
        else:
            results.append({"to_item_guid": to_item_guid, "action": "CREATED", "detail": outcome})
    return {"results": results, "ok": not any_error}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = sync(payload["from_item_guid"], payload["targets"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"error": True, "message": f"Bad input: {exc}"}))
        return 1
    print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
