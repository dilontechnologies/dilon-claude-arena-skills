---
name: dilon-arena-document-standard-fo
description: Dilon's document standard for Form (FO) controlled documents/travelers in Arena — file name/title convention, revision-numbering scheme, file-category and change Affected-Items picklist mapping, and form-vs-narrative classification. Use when creating, naming, or revising an FO-prefixed item/file, or when dilon-arena-eco-creator needs FO's naming/revision/item-connection rules.
---

# Dilon Document Standard — FO (Form / Traveler)

Single source of truth for Dilon's rules on FO-prefixed controlled
documents. `dilon-arena-eco-creator` defers to this skill for FO items
rather than duplicating this guidance.

## Naming

**File `name`** — no direct Arena API field; set via the uploaded
filename. Convention: `<Item Number> Rev <Revision Number>.<ext>` (e.g.
`FO-00127 Rev 02-A.docx`). This MCP server's `create_file`/
`create_file_edition`/`update_file_summary` tools expose no `name`
parameter — Arena populates a file's `name` from the uploaded file's own
filename on a multipart (`storage_method="FILE"`) upload. Rename a local
temp copy of the source file to this convention *before* calling
`create_file`/`create_file_edition` — there's no way to set `name` after
the fact. Resolve `<Revision Number>` per the Revision section below.

**File `title`** — stays descriptive, never carries the revision.
Convention: `<Item Number> <Item Name>` (e.g. `FO-00127 Detector Head Assy
Traveler`), no revision number in it ever, even though `name` above does
carry one. `title` identifies *what* the document is and stays stable
across revisions; `name` and the revision number are what carry *which*
revision.

## Revision

Baseline/prototype/production revision-numbering scheme. Applies to
`add_items_to_change`'s and `update_change_affected_item`'s
`new_revision_number` parameter — this is the literal string Arena stores
as the item's revision, not just a documentation convention.

- **Baseline / production revision**: two-digit numeric, `"00"`, `"01"`,
  `"02"`, ... incrementing by one on each production release. A
  never-released item's baseline is `"00"` — its first production release
  is also `"00"`.
- **Prototype Release ahead of the next production release**: revision is
  `"<next-numeric>-<letter>"`, where `<next-numeric>` is the numeric value
  that production release will carry when it happens (current baseline for
  a never-released item, or current-released + 1 for an already-released
  one). E.g. never-released item, first prototype iteration: `"00-A"`,
  second iteration before that same first production release: `"00-B"`.
  Item currently released at `"01"`: first prototype iteration ahead of
  its next release is `"02-A"`, second is `"02-B"`.
- **Promotion to actual production release**: the revision condenses back
  down to the plain numeric (`"02"`), dropping the letter suffix. The
  document's revision-history table gets **one row** for that production
  revision, consolidating the notes from every prototype iteration that
  preceded it — not one row per prototype iteration.

**Always pass `new_revision_number` explicitly**, for every transition,
rather than omitting it and relying on Arena's auto-assignment — see Known
gaps below for why omission isn't fully trusted yet.

Empirical confirmation of this scheme against real, non-dry-run Arena
writes: see this skill's own requirements doc
(`docs/requirements/dilon-arena-document-standard-fo/core.md`) for the
full verification record, tested via `FO-00001` and `FO-00161`.

## Expected file formats

Default: **docx** (non-primary) + **pdf** (primary) — no known exception
for this type. `dilon-arena-eco-creator`'s step 8 iterates whichever
formats and primary designation this section lists rather than assuming
docx+pdf on its own; if this type is ever confirmed to need a different
set (an additional format, just one, or a different primary), update this
section — that skill's step 8 loop stays generic. See this skill's own
requirements doc for the one confirmed data point (`FO-00004`'s pdf/docx
pair).

## Item connections

- **File category**: "Form" (`list_file_categories`, match by name — never
  hardcode the GUID).
- **Change Affected-Items picklist value**: `"Form (FO)"` (the multiselect
  picklist attribute on the change category,
  `list_change_category_attributes` — wrap it in a single-element array,
  e.g. `["Form (FO)"]`, since this attribute is `multiSelect: true`).

## Usage / update triggers

FO documents are **forms** (`@@@FORM_FIELD:FieldGrid@@@` /
`Form_Section_Header` markers in their Dilon markdown source) — compile
with `dilon-document-form-compiler`, not `dilon-document-compiler`.

No special reissue trigger: every change to an FO item follows the
standard revision-bump behavior above. There is no case where an FO
revision becomes a new item instead of a revision bump.

## Known gaps

- **Untested**: whether omitting `new_revision_number` on a production
  release that follows a run of prototype iterations (`02-A`, `02-B`, ...)
  correctly auto-assigns the matching plain numeric (`"02"`), or whether it
  drifts/errors. Until tested, always pass the value explicitly (above).
- No convention yet defined for what happens if a prototype sequence is
  abandoned entirely (never reaches production release) — does the
  document's revision history need any entry for `02-A`/`02-B` at all in
  that case, or only once/if `02` actually ships?
- Doesn't cover file *content* editing (markup, corrections, check-out/
  check-in) — only naming and revision-numbering.
