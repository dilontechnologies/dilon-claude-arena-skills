---
name: dilon-arena-document-standard-wi
description: Dilon's document standard for Work Instruction (WI) controlled documents in Arena — file name/title convention, revision-numbering scheme, file-category and change Affected-Items picklist mapping, and narrative-vs-form classification. Use when creating, naming, or revising a WI-prefixed item/file, or when dilon-arena-eco-creator needs WI's naming/revision/item-connection rules.
---

# Dilon Document Standard — WI (Work Instruction)

Single source of truth for Dilon's rules on WI-prefixed controlled
documents. `dilon-arena-eco-creator` defers to this skill for WI items
rather than duplicating this guidance.

## Naming

**File `name`** — no direct Arena API field; set via the uploaded
filename. Convention: `<Item Number> Rev <Revision Number>.<ext>` (e.g.
`WI-00042 Rev 01.docx`). This MCP server's `create_file`/
`create_file_edition`/`update_file_summary` tools expose no `name`
parameter — Arena populates a file's `name` from the uploaded file's own
filename on a multipart (`storage_method="FILE"`) upload. Rename a local
temp copy of the source file to this convention *before* calling
`create_file`/`create_file_edition` — there's no way to set `name` after
the fact. Resolve `<Revision Number>` per the Revision section below.

**File `title`** — stays descriptive, never carries the revision.
Convention: `<Item Number> <Item Name>` (e.g. `WI-00042 Detector Head
Assembly Work Instruction`), no revision number in it ever, even though
`name` above does carry one. `title` identifies *what* the document is and
stays stable across revisions; `name` and the revision number are what
carry *which* revision.

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
  that production release will carry when it happens. E.g. never-released
  item, first prototype iteration: `"00-A"`, second: `"00-B"`. Item
  currently released at `"01"`: first prototype iteration ahead of its
  next release is `"02-A"`, second is `"02-B"`.
- **Promotion to actual production release**: the revision condenses back
  down to the plain numeric (`"02"`), dropping the letter suffix. The
  document's revision-history table gets **one row** for that production
  revision, consolidating the notes from every prototype iteration that
  preceded it.

**Always pass `new_revision_number` explicitly**, for every transition,
rather than omitting it and relying on Arena's auto-assignment — see Known
gaps below.

Empirical confirmation of this scheme against real, non-dry-run Arena
writes was done via FO-prefixed items — see
`dilon-arena-document-standard-fo`'s requirements doc
(`docs/requirements/dilon-arena-document-standard-fo/core.md`) for the full
verification record; this scheme applies identically to WI.

## Expected file formats

Default: **docx** (non-primary) + **pdf** (primary) — same default every
`dilon-arena-document-standard-<type>` skill in this repo states, no
known exception for this type specifically. `dilon-arena-eco-creator`'s
step 8 iterates whichever formats and primary designation this section
lists rather than assuming docx+pdf on its own; if this type is ever
confirmed to need a different set, update this section — that skill's
step 8 loop stays generic. See `dilon-arena-document-standard-fo`'s
requirements doc for the one confirmed data point behind this default
(`FO-00004`'s pdf/docx pair).

## Item connections

- **File category**: "Work Instructions" (`list_file_categories`, match by
  name — never hardcode the GUID).
- **Change Affected-Items picklist value**: `"Work Instruction (WI)"` (the
  multiselect picklist attribute on the change category,
  `list_change_category_attributes` — wrap it in a single-element array,
  e.g. `["Work Instruction (WI)"]`, since this attribute is
  `multiSelect: true`).

## Suggested connections

Via `create_item_reference` (`dilon-arena-eco-creator` step 8b) — check
`get_item_references` first and skip a target that's already linked
(queryable from either side, so the other item's own connections step may
have already created it):
- The Traveler (FO) for the item this WI produces.
- The part/subassembly item this WI's instructions create.
- The qualification Plan (PL) for this process.
- The qualification Report (RE) for this process.
- Any Functional Test Procedure(s) (FTP) used to verify the part.
- Any QCP(s) used to verify the part.

## Usage / update triggers

WI documents are **narrative** documents (prose sections like
Purpose/Scope) — compile with `dilon-document-compiler`, not
`dilon-document-form-compiler`.

No special reissue trigger: every change to a WI item follows the standard
revision-bump behavior above.

## Known gaps

- **Untested**: whether omitting `new_revision_number` on a production
  release that follows a run of prototype iterations correctly
  auto-assigns the matching plain numeric, or drifts/errors. Until tested,
  always pass the value explicitly (above).
- No convention yet defined for what happens if a prototype sequence is
  abandoned entirely before reaching production release.
- Doesn't cover file *content* editing (markup, corrections, check-out/
  check-in) — only naming and revision-numbering.
