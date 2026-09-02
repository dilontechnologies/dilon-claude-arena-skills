#!/usr/bin/env python3
"""Build a create_change-ready `additional_attributes` payload.

Resolves each desired {display name: value} pair against a fresh
list_change_category_attributes(..., include_possible_values=True)
response, and auto-wraps `multiSelect: true` fields in a single-element
array -- the exact shape Arena requires (a bare string is rejected with
error 2026, "not a valid option for multi additional attribute", even
though the value is real and listed).

NOTE on field names: this assumes each attribute entry exposes `name`
(display name) and `multiSelect` (bool), and optionally `possibleValues`
(list[str]) when the caller included include_possible_values=True on the
underlying MCP call -- matching the field names SKILL.md's step 2
already uses verbatim. Not independently verified against a raw API
response by this script; if Arena's actual JSON uses different key names,
fix `_ATTR_NAME_KEYS` below rather than guessing silently at runtime.

Usage:
    echo '{"attributes": [...], "values": {"Product Change?": "No",
          "Affected Items": "Other Document(s)"}}' \
        | python additional_attributes.py

Output: {"additional_attributes": [{"guid": ..., "value": ...}, ...],
         "warnings": [...]}
Exit code 0 on success (even with warnings), 1 if any display name has no
match (a hard error, per SKILL.md's "match ... exactly as Arena shows
them" requirement -- silently dropping a field is worse than failing loud).
"""
from __future__ import annotations

import json
import sys
from typing import Any

_ATTR_NAME_KEYS = ("name", "displayName")


def _attr_name(attr: dict[str, Any]) -> str | None:
    for key in _ATTR_NAME_KEYS:
        if attr.get(key):
            return attr[key]
    return None


def build_additional_attributes(
    attributes: list[dict[str, Any]], values: dict[str, Any]
) -> dict[str, Any]:
    by_name = {}
    for attr in attributes:
        name = _attr_name(attr)
        if name:
            by_name[name] = attr

    result: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing: list[str] = []

    for display_name, value in values.items():
        attr = by_name.get(display_name)
        if attr is None:
            missing.append(display_name)
            continue

        guid = attr.get("guid")
        multi_select = bool(attr.get("multiSelect"))
        shaped_value = value

        if multi_select and not isinstance(value, list):
            shaped_value = [value]
        elif not multi_select and isinstance(value, list):
            warnings.append(
                f"{display_name!r} is not multiSelect but a list was given "
                f"({value!r}) -- passed through unchanged; verify this is intended."
            )

        possible_values = attr.get("possibleValues")
        if possible_values:
            check_values = shaped_value if isinstance(shaped_value, list) else [shaped_value]
            for v in check_values:
                if v not in possible_values:
                    warnings.append(
                        f"{display_name!r} value {v!r} is not in this attribute's "
                        f"possibleValues {possible_values!r} -- Arena will likely reject it."
                    )

        result.append({"guid": guid, "value": shaped_value})

    if missing:
        return {
            "error": True,
            "message": f"No attribute matched by display name: {missing!r}",
            "available_names": sorted(by_name.keys()),
        }

    return {"additional_attributes": result, "warnings": warnings}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = build_additional_attributes(payload["attributes"], payload["values"])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"error": True, "message": f"Bad input: {exc}"}))
        return 1
    print(json.dumps(result))
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
