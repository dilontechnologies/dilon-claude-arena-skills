#!/usr/bin/env python3
"""Check a drafted change description against SKILL.md step 4's
golden-standard structure, before create_change is called.

Checks, each producing an error (structure is missing) or a warning
(structure present but not in the exact documented form):
- At least one of "Released to <phase>:" / "Released:" / "Obsoleted:".
- A "Ref:" line.
- The 6-question screening block header.
- Each of the 6 (or caller-supplied) screening questions present, each
  immediately followed by a plain YES/NO on its own line (not inline).

This is a *sibling* check to the document-verification script -- that one
checks the compiled documents' own content; this one checks the change
record's own description text, before it's ever written to Arena.

Usage:
    echo '{"description": "..."}' | python lint_description.py
    # optionally: {"description": "...", "questions": ["custom q1", ...]}

Output: {"ok": bool, "errors": [...], "warnings": [...]}
Exit code 0 if ok (no errors; warnings still allowed), 1 if any error.
"""
from __future__ import annotations

import json
import re
import sys

_DEFAULT_QUESTIONS = [
    "Could reasonably affect device safety or effectiveness",
    "Materially affects intended purpose, design, clinical performance, or benefit-risk profile",
    "Results in a change to QMS scope",
    "Introduces a new intended purpose, patient population, or clinical indication",
    "Major design change affecting performance, safety, operating principles, or clinical function",
    "Adds a product or process not covered by the current ISO certification",
]


def lint(description: str, questions: list[str] | None = None) -> dict:
    questions = questions or _DEFAULT_QUESTIONS
    lines = description.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    if not any(
        re.search(r"^(Released to .+:|Released:|Obsoleted:)", line.strip())
        for line in lines
    ):
        errors.append(
            "No 'Released to <phase>:' / 'Released:' / 'Obsoleted:' line found."
        )

    if not any(line.strip().startswith("Ref:") for line in lines):
        errors.append("No 'Ref:' line found.")

    if "does this change meet any of the following criteria" not in description.lower():
        errors.append(
            "Screening-question block header "
            "('Does this change meet any of the following criteria? (Yes / No)') not found."
        )

    for question in questions:
        idx = next(
            (i for i, line in enumerate(lines) if question in line), None
        )
        if idx is None:
            errors.append(f"Question not found verbatim: {question!r}")
            continue
        # Find the next non-blank line after the question.
        answer_line = None
        for line in lines[idx + 1:]:
            if line.strip():
                answer_line = line.strip()
                break
        if answer_line is None:
            errors.append(f"No answer line found after question: {question!r}")
        elif answer_line.upper() not in ("YES", "NO"):
            warnings.append(
                f"Answer line after {question!r} is {answer_line!r}, "
                "expected a plain YES or NO on its own line."
            )
        elif answer_line not in ("YES", "NO"):
            warnings.append(
                f"Answer for {question!r} is {answer_line!r} -- SKILL.md's example "
                "uses uppercase YES/NO; consider matching that casing."
            )

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = lint(payload["description"], payload.get("questions"))
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"error": True, "message": f"Bad input: {exc}"}))
        return 1
    print(json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
