# `dilon-arena-document-standard-definer` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-document-standard-definer/SKILL.md`. Added 2026-09-01
alongside the `dilon-arena-document-standard-<type>` split, to resolve the
"Other Document(s)" gap: a document type with no declared standard used to
have nothing to defer to.

## Purpose

When `dilon-arena-eco-creator` (or a direct user request) encounters a
document type with no matching `dilon-arena-document-standard-<type>`
skill, interview the user into a new one instead of guessing or falling
back to an unconfirmed default, and get that new standard in front of the
developer for review.

## Decisions (2026-09-01)

- **Both standalone-invokable and reactive**: fires both when directly
  asked and when `dilon-arena-eco-creator` hits an undeclared type
  mid-flow.
- **Writes files directly**, not draft-only — low-risk, local, reversible
  via git, same as any other skill/doc file in this repo.
- **Updates `docs/requirements/README.md` and `CLAUDE.md` automatically**
  — keeps the index authoritative without a separate manual step.
- **Always prompts to send the submission file to the developer**,
  regardless of whether it's running in the source repo or an installed
  plugin copy — one code path, no context-detection logic. Even the
  developer running it here gets prompted and can simply skip the step
  since they already have write access.
- **Submission mechanism is a plain markdown file, not an automated
  `gh issue create`** — the skill's job stops at producing
  `submission.md`; the developer opens the GitHub issue themselves from
  the received file.

## Known gaps / not yet covered

- No live validation of interview answers against a real Arena workspace
  (see `SKILL.md`'s Known limitations).
- No duplicate-submission detection.
- Not yet exercised end-to-end against a real undeclared document type —
  this skill's own interview flow hasn't been run yet.
