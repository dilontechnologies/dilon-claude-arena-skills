#!/usr/bin/env python3
"""Compute the next revision-number string for an affected item.

Two independent modes, matching the two distinct numbering schemes the
document-standard skills document:

- "standard": the baseline/prototype/production scheme every
  dilon-arena-document-standard-<type> skill states (two-digit numeric
  for production, "<next-numeric>-<letter>" for prototype).
- "reissue": the PL/RE "<root>-<NN>" reissue-as-new-item numbering.

Usage:
    echo '{"mode": "standard", "current_revision": "01",
           "target_family": "PROTOTYPE"}' | python revision_numbers.py
    # -> {"next_revision": "02-A", ...}

    echo '{"mode": "reissue", "item_number": "PL-00004",
           "existing_numbers": ["PL-00004-01"]}' | python revision_numbers.py
    # -> {"next_revision": "PL-00004-02", ...}

Exit code 0 on success, 1 on malformed/invalid input.
"""
from __future__ import annotations

import json
import sys
from typing import Optional


def _parse_standard_revision(current: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Split "02-A" -> ("02", "A"); "02" -> ("02", None); None -> (None, None)."""
    if current is None:
        return None, None
    if "-" in current:
        numeric, letter = current.split("-", 1)
        return numeric, letter
    return current, None


def next_standard_revision(current_revision: Optional[str], target_family: str) -> str:
    numeric, letter = _parse_standard_revision(current_revision)
    target_family = target_family.upper()

    if target_family == "PRODUCTION":
        if letter is not None:
            # Promotion: the letter suffix drops, numeric stays as-is.
            return numeric
        if numeric is None:
            return "00"
        return f"{int(numeric) + 1:02d}"

    if target_family == "PROTOTYPE":
        if letter is not None:
            # Next iteration ahead of the same upcoming production release.
            return f"{numeric}-{chr(ord(letter) + 1)}"
        base = "00" if numeric is None else f"{int(numeric) + 1:02d}"
        return f"{base}-A"

    raise ValueError(f"Unknown target_family: {target_family!r} (expected PRODUCTION or PROTOTYPE)")


def root_number(item_number: str) -> str:
    """Strip an existing "-NN" reissue suffix, if present.

    "PL-00004" (base, 2 segments) -> "PL-00004" (unchanged).
    "PL-00004-01" (already reissued, 3 segments) -> "PL-00004".
    """
    parts = item_number.split("-")
    if len(parts) == 3:
        return "-".join(parts[:2])
    return item_number


def next_reissue_number(item_number: str, existing_numbers: list[str]) -> str:
    root = root_number(item_number)
    prefix = root + "-"
    max_n = 0
    for num in existing_numbers:
        if not num.startswith(prefix):
            continue
        suffix = num[len(prefix):]
        if suffix.isdigit():
            max_n = max(max_n, int(suffix))
    return f"{root}-{max_n + 1:02d}"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        mode = payload["mode"]
        if mode == "standard":
            next_rev = next_standard_revision(
                payload.get("current_revision"), payload["target_family"]
            )
            result = {"next_revision": next_rev, "mode": "standard"}
        elif mode == "reissue":
            next_rev = next_reissue_number(
                payload["item_number"], payload.get("existing_numbers", [])
            )
            result = {"next_revision": next_rev, "mode": "reissue"}
        else:
            raise ValueError(f"Unknown mode: {mode!r} (expected 'standard' or 'reissue')")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"error": True, "message": f"Bad input: {exc}"}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
