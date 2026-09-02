#!/usr/bin/env python3
"""Look up whether a lifecycle-phase transition is confirmed reachable.

Encodes the confirmed reachable/blocked (stage, phase-name) pairs from
SKILL.md step 7 "Lifecycle phase transitions" as a static table, instead
of relying on the agent recalling the table correctly from prose. A pair
not in the table returns UNKNOWN, not REACHABLE -- absence of evidence is
not evidence of safety here.

Usage:
    echo '{"current_stage": "PRELIMINARY", "current_phase": "Unreleased",
           "target_stage": "PRODUCTION", "target_phase": "RELEASED"}' \
        | python phase_transitions.py

Output (stdout, JSON): {"verdict": "REACHABLE"|"BLOCKED"|"UNKNOWN", "note": str}
Exit code 0 on a successful lookup (regardless of verdict); 1 if the input
itself is malformed.
"""
from __future__ import annotations

import json
import sys

# (current_stage, current_phase, target_stage, target_phase) -> reachable?
# Source: SKILL.md step 7, confirmed against the sandbox workspace before
# use in production. NOT exhaustive -- only pairs actually tested so far.
_CONFIRMED: dict[tuple[str, str, str, str], bool] = {
    ("PRELIMINARY", "Unreleased", "PRODUCTION", "RELEASED"): True,
    ("PRELIMINARY", "Unreleased", "DESIGN", "In Design"): True,
    ("DESIGN", "In Design", "DESIGN", "Abandoned"): True,
    ("PRODUCTION", "RELEASED", "PRODUCTION", "RELEASED"): True,
    ("PRODUCTION", "RELEASED", "PRODUCTION", "Prototype Release"): True,
    ("PRELIMINARY", "Unreleased", "PRODUCTION", "Obsolete"): False,
    ("PRELIMINARY", "Unreleased", "DESIGN", "Abandoned"): False,
    ("PRODUCTION", "RELEASED", "DESIGN", "Prototype Release"): False,
}


def check_transition(
    current_stage: str, current_phase: str, target_stage: str, target_phase: str
) -> dict:
    key = (current_stage, current_phase, target_stage, target_phase)
    if key not in _CONFIRMED:
        return {
            "verdict": "UNKNOWN",
            "note": (
                f"({current_stage}, {current_phase!r}) -> "
                f"({target_stage}, {target_phase!r}) is not in the confirmed "
                'table. Test it in the sandbox workspace ("Dilon Technologies '
                'Validation") before trying it against production -- a '
                "rejected transition returns error 3063."
            ),
        }
    if _CONFIRMED[key]:
        return {"verdict": "REACHABLE", "note": "Confirmed reachable."}
    return {
        "verdict": "BLOCKED",
        "note": (
            "Confirmed blocked (error 3063: \"Lifecycle transition from X to "
            "Y is not supported\"). Route through an intermediate phase "
            "instead of retrying with different parameters."
        ),
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = check_transition(
            payload["current_stage"],
            payload["current_phase"],
            payload["target_stage"],
            payload["target_phase"],
        )
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"error": True, "message": f"Bad input: {exc}"}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
