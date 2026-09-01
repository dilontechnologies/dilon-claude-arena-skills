# `dilon-arena-document-standard-re` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-document-standard-re/SKILL.md`. Folds together what
was previously split across `dilon-arena-file-naming`,
`dilon-arena-file-revision`, and
`dilon-arena-file-revision-amendment-pl-re-item-numbering` (2026-09-01) —
see `../README.md` for why those retired in favor of one skill per
document type, `../dilon-arena-document-standard-fo/core.md` for the base
naming/revision scheme's empirical verification record, and
`../dilon-arena-document-standard-pl/core.md` for the reissue mechanism's
full empirical investigation (item-numbering override, Item Reference
mechanics) — that investigation was done jointly for PL and RE and isn't
duplicated here.

## Purpose

Answer, for an RE (Test Report) controlled document: what goes in its file
`name`/`title`, what revision-number string Arena needs (or, once a
completed report exists against the plan it tests, what new-item number
instead), which file category and Affected-Items picklist value it maps
to, and how it's compiled.

## Naming and base revision — RESOLVED (inherited, not independently tested)

Same convention and scheme as `dilon-arena-document-standard-fo` — see
that skill's `core.md` for the empirical verification record. Applies to
RE up until the reissue exception below fires.

## Reissue-instead-of-revision exception — RESOLVED mechanism

Same mechanism as `dilon-arena-document-standard-pl` — see that skill's
`core.md` for the full empirical investigation (number-format mechanism,
Item Reference bidirectionality/immediacy, the `notes`->`note` bug fix in
`arena_mcp/arena_mcp_server.py`). One RE-specific data point: `RE-00019-01`
was also created via this mechanism in production (2026-09-01), but was,
per the user's direction mid-session, associated with a different,
not-yet-created ECO rather than the one `PL-00004-01` was being attached
to — so it doesn't itself add to the end-to-end attach-flow confirmation
(see Known gaps).

## Known gaps / not yet covered

- Same open questions as `dilon-arena-document-standard-pl`: "completed"
  definition unconfirmed, suffix zero-padding past `-99` unspecified, no
  backfill plan for pre-existing pairs.
- **Not yet tested end-to-end** inside `dilon-arena-eco-creator`'s actual
  step 8 attach flow on a real report reissue — `RE-00019-01`'s creation
  didn't exercise the attach flow either (see Reissue exception above).
- Doesn't cover file *content* editing — only naming and revision-numbering.
