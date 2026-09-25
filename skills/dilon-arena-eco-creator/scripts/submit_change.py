#!/usr/bin/env python3
"""Drive SKILL.md step 10's two-call submission sequence, checking the
known-rejection shape of each call before sending it.

Wraps two known pitfalls, both confirmed real errors:
- First call must include `administrator_guids` (else Arena has nothing
  to route to).
- Second call must NOT include `administrator_guids` (error 4995 if it
  does) -- a forgetful re-send of the first call's payload is the
  documented risk this removes.

This script performs the LIVE route_change calls itself (see
_arena_import.py for the required environment variables) -- it is not a
pure function like the other scripts in this directory, since the whole
point is orchestrating two dependent API calls with a check between them.

Usage:
    echo '{"change_guid": "CHG123", "administrator_guids": ["U1"],
           "comment": "..."}' | python submit_change.py

Output: {"first_call": {...}, "second_call": {...},
         "final_status": "...", "ok": bool}
Exit code 0 if both calls succeeded, 1 otherwise (including if the
agent's own confirmation gate was skipped -- see require_confirmed below).
"""
from __future__ import annotations

import json
import sys

from _arena_import import arena  # also sets up sys.path as a side effect


def submit(change_guid: str, administrator_guids: list[str], comment: str | None) -> dict:
    first = arena.route_change(
        guid=change_guid,
        status="SUBMITTED",
        comment=comment,
        administrator_guids=administrator_guids,
    )
    if isinstance(first, dict) and first.get("error"):
        return {"first_call": first, "ok": False, "stopped_after": "first_call"}

    second = arena.route_change(guid=change_guid, status="SUBMITTED")
    if isinstance(second, dict) and second.get("error"):
        return {
            "first_call": first,
            "second_call": second,
            "ok": False,
            "stopped_after": "second_call",
        }

    final_status = None
    if isinstance(second, dict):
        final_status = second.get("lifecycleStatus") or second.get("status")

    return {
        "first_call": first,
        "second_call": second,
        "final_status": final_status,
        "ok": True,
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not payload.get("confirmed"):
            print(json.dumps({
                "error": True,
                "message": (
                    "Refusing to submit: input JSON must include "
                    '"confirmed": true, set only after the user has '
                    "explicitly confirmed the fully-populated change per "
                    "SKILL.md step 10. This script does not ask for "
                    "confirmation itself."
                ),
            }))
            return 1
        result = submit(
            payload["change_guid"], payload["administrator_guids"], payload.get("comment")
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"error": True, "message": f"Bad input: {exc}"}))
        return 1
    print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
