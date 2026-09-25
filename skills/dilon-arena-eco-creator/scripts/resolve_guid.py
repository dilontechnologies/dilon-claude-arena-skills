#!/usr/bin/env python3
"""Resolve one exact-match GUID from a list_* response, or fail loudly.

Mirrors server/core.py's internal `_resolve_name_to_guid` matching
semantics (case-insensitive exact match on `name`) so the same rule is
used whether the MCP server resolves a name internally or this skill
resolves one explicitly in step 2/8a. Removes the chance an agent picks a
close-but-wrong entry under a fuzzy read of a long results list.

Usage:
    echo '{"results": [{"name": "Form", "guid": "G1"}, ...],
           "target_name": "Form"}' | python resolve_guid.py

Output: {"guid": "G1", "match_count": 1}
     or {"error": true, "message": "...", "available_names": [...]}
Exit code 0 on a single unambiguous match, 1 otherwise.
"""
from __future__ import annotations

import json
import sys
from typing import Any


def resolve(results: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    matches = [e for e in results if (e.get("name") or "").lower() == target_name.lower()]

    if len(matches) == 0:
        available = sorted({e.get("name") for e in results if e.get("name")})
        return {
            "error": True,
            "message": f"No match for {target_name!r}.",
            "available_names": available,
        }
    if len(matches) > 1:
        return {
            "error": True,
            "message": f"Ambiguous: {len(matches)} entries named {target_name!r}.",
            "guids": [m.get("guid") for m in matches],
        }
    return {"guid": matches[0].get("guid"), "match_count": 1}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = resolve(payload["results"], payload["target_name"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"error": True, "message": f"Bad input: {exc}"}))
        return 1
    print(json.dumps(result))
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
