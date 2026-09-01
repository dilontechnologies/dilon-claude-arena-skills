# Document verification — requirements notes

Source of truth for current behavior: the verification script under
`skills/dilon-arena-eco-creator/scripts/` (not yet built) and the relevant
step of `skills/dilon-arena-eco-creator/SKILL.md`. This is a sub-component
of `dilon-arena-eco-creator`, not a separate skill — split into its own
requirements doc because the check has enough open questions and its own
data sources (document front matter, compiled document, and change
history) to track separately from the rest of the ECO flow.

## Purpose

Before `dilon-arena-eco-creator` tells the user an ECO is ready to submit
(step 9/10), verify the documents being uploaded on two dimensions:

1. **Format compliance** — each document matches Dilon's prescribed
   document format/template.
2. **Information consistency** — information recorded inside each document
   is consistent with what's recorded on the ECO itself (e.g. a document's
   signature table names the same people the ECO actually has as
   reviewers).

## Form

A standalone script under `skills/dilon-arena-eco-creator/scripts/` (not
just `SKILL.md` prose) — deterministic parsing/comparison belongs in
testable code, per this repo's own convention for anything with new
behavior. Gets a pytest test.

## 1. Format compliance

**Not yet scoped.** OPEN QUESTION: what counts as "prescribed format"
here? Candidates to decide among (not mutually exclusive):
- Front-matter completeness against `dilon-claude-tools`'
  `dilon-document-writer`/`dilon-document-form-writer` templates
  (`TEMPLATE_Document.md` / `TEMPLATE_Form.md`) — no leftover placeholder
  values (`"--"`, `"DD_XXX_XXXXX"`), all expected keys present.
- Styling conformance of the source markdown against
  `MARKDOWN_STYLING_GUIDE.md`.
- Structural elements of the *compiled* docx (title page, table of
  contents, signature page, revision-history table) actually present, as
  `dilon-document-compiler`/`dilon-document-form-compiler` are supposed to
  produce them.

Needs definition before scripting starts on this half.

## 2. Information consistency: document vs. ECO

### 2a. Signature table vs. ECO reviewers

**Confirmed inputs (verified 2026-09-01 against production, read-only):**
- **Document side:** each document's `signature_fields` list
  (`{department, name}` pairs) in its source markdown's YAML front matter
  — the schema `dilon-claude-tools`' `dilon-document-writer` skill writes
  (see `TEMPLATE_Document.md`). This lives in the markdown source, not the
  compiled docx, so the tool needs the source `.md` path per document, not
  just the uploaded file.
- **ECO side:** `get_change_history(change_guid)`, filtered to
  `action == "Add Additional Reviewer"` (property `"Change Approver
  Record"`). Reviewer name is the `newValue` string with its trailing
  qualifier stripped — confirmed format `"<Name> (Approval Required)"` on
  a real completed ECO (ECO-000162: "Kevin Lint (Approval Required)",
  "Pedro Cruz (Approval Required)"). This is the only way to read
  reviewers — Arena has no dedicated reviewers endpoint (confirmed by
  checking the full official spec), but the history feed carries it, so
  the MCP server header comment claiming reviewers are unreadable is
  wrong and should be corrected to say "no dedicated endpoint" instead of
  implying they can't be read at all.

**Confirmed constraint: matching is name-only, not department.**
`get_user`/`list_users` expose no department field on Arena's user object
at all, and this API credential's `list_users` only ever returns 3 users
regardless of filter (looks like an integration-scope limit, not a query
bug) — confirmed 2026-09-01 querying by full name, last name, wildcard,
and email for known users who returned zero results. There is no way to
derive "this person = Manufacturing/Quality/Regulatory" from Arena. The
`department` half of each `signature_fields` entry is a label the
document's author chose and cannot be cross-checked against Arena — the
tool can only confirm the `name` half is a real reviewer on the ECO.

**Open questions:**
- On a mismatch (a signer in `signature_fields` who isn't an ECO
  reviewer, or vice versa), should the tool **block** progressing to
  "ready to submit," or just **warn** and let the user decide? Asked, not
  yet answered.
- Are there reviewer qualifier suffixes besides `"(Approval Required)"`
  (e.g. an optional/FYI reviewer type) that need including or excluding
  from the comparison set? Only one real example (ECO-000162) has been
  inspected so far.
- Does the front matter's separate `department_head` field (distinct from
  the `signature_fields` list) also need to match an ECO reviewer, or is
  it out of scope for this check?
- Name matching needs normalization — history names have observed
  whitespace quirks (`"Phillip  Gray"` double space, `"Shannon
  Buccellato "` trailing space) — trim/collapse whitespace before
  comparing. Case sensitivity not yet decided.
- Does the tool check only newly-attached/revised documents for this
  ECO, or every document in the ECO's Files view?
- If an ECO attaches multiple documents with different `signature_fields`
  lists, is each document checked independently against the same ECO
  reviewer set, or is there some combined/union requirement?

### 2b. Current-revision date vs. most recent Arena upload

The front matter's `revisions` list top entry (the one matching
`current_revision`) has an `eco_date` field. That date must reflect **when
the document was most recently pushed to Arena for this ECO**, not just
the day the ECO was originally created or drafted — a single ECO can span
multiple document re-uploads (review feedback -> author revises -> new
edition), and `eco_date` needs to track the latest one, not the first.

**Confirmed mechanism (verified 2026-09-01 against production, read-only):**
- Both `get_item_files(item_guid)` and `get_file_editions(file_guid)`
  return each file/edition with its own `creationDateTime` and
  `lastModifiedDateTime` — no extra call needed beyond what step 2 of
  `dilon-arena-eco-creator` already fetches. `get_item_files`'s per-file
  entry with `"latest": true` is the current edition.
- Confirmed accurate against a real re-upload event: `FO-00096`'s docx
  file (`HZJ27ULS8GZFYH4Z1CPH`) has edition `"1"` created
  `2024-10-18T15:20:49Z` and edition `"2"` (`latest: true`) created
  `2025-02-13T20:04:37Z`. That second edition's timestamp matches
  `AC-000008` ("Reupload of FO-00096"), submitted the same day
  (`2025-02-13T20:05:17Z`) — confirms edition `creationDateTime` tracks
  the actual push-to-Arena event, not some other unrelated timestamp.

**Open questions:**
- The docx and pdf editions of the same document can have different
  `creationDateTime`s (seconds apart, but still different) — compare
  `eco_date` against whichever is later, or check each file independently
  and require both to be consistent with `eco_date`?
- Date-only comparison (`eco_date` is `"YYYY-MM-DD"`) vs. Arena's UTC
  timestamp — a late-night UTC upload could land on a different calendar
  date once converted to Dilon's local timezone. Which timezone should
  the comparison use?
- This check can only run *after* step 8 uploads the file (the edition
  has to exist in Arena to have a timestamp) — if it then finds a
  mismatch, fixing it means updating the front matter, recompiling, and
  re-uploading, which creates yet another edition with a newer timestamp,
  requiring the check to re-run. Worth confirming this convergence loop
  terminates in practice rather than assuming it.

### 2c. Other consistency checks — not yet scoped

OPEN QUESTION: what other document fields should be cross-checked against
the ECO? Candidates worth considering, none decided yet:
- Front matter's `revisions` list top entry's `eco_number` matches this
  ECO's actual number.
- Front matter's `current_revision` matches the `new_revision_number`
  passed to `add_items_to_change`/`update_change_affected_item` (the
  relevant `dilon-arena-document-standard-<type>` skill's revision
  scheme).
- Front matter's `doc_number` matches the Arena item number the document
  is attached to.
