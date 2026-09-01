---
name: dilon-arena-document-standard-ftp
description: Dilon's document standard for FTP controlled documents in Arena — file name/title convention, revision-numbering scheme, file-category mapping, and narrative-vs-form classification. Flags the change Affected-Items picklist value as unconfirmed. Use when creating, naming, or revising an FTP-prefixed item/file, or when dilon-arena-eco-creator needs FTP's naming/revision/item-connection rules.
---

# Dilon Document Standard — FTP

Single source of truth for Dilon's rules on FTP-prefixed controlled
documents. `dilon-arena-eco-creator` defers to this skill for FTP items
rather than duplicating this guidance.

## Naming

**File `name`** — no direct Arena API field; set via the uploaded
filename. Convention: `<Item Number> Rev <Revision Number>.<ext>` (e.g.
`FTP-00007 Rev 01.docx`). This MCP server's `create_file`/
`create_file_edition`/`update_file_summary` tools expose no `name`
parameter — Arena populates a file's `name` from the uploaded file's own
filename on a multipart (`storage_method="FILE"`) upload. Rename a local
temp copy of the source file to this convention *before* calling
`create_file`/`create_file_edition` — there's no way to set `name` after
the fact. Resolve `<Revision Number>` per the Revision section below.

**File `title`** — stays descriptive, never carries the revision.
Convention: `<Item Number> <Item Name>`, no revision number in it ever,
even though `name` above does carry one.

## Revision

Baseline/prototype/production revision-numbering scheme. Applies to
`add_items_to_change`'s and `update_change_affected_item`'s
`new_revision_number` parameter.

- **Baseline / production revision**: two-digit numeric, `"00"`, `"01"`,
  `"02"`, ... incrementing by one on each production release. A
  never-released item's first production release is `"00"`.
- **Prototype Release ahead of the next production release**: revision is
  `"<next-numeric>-<letter>"`. E.g. never-released item, first prototype
  iteration: `"00-A"`, second: `"00-B"`. Item currently released at
  `"01"`: first prototype iteration ahead of its next release is
  `"02-A"`, second is `"02-B"`.
- **Promotion to actual production release**: the revision condenses back
  down to the plain numeric (`"02"`); the document's revision-history table
  gets one consolidated row for it, not one per prototype iteration.

**Always pass `new_revision_number` explicitly**, for every transition.

Empirical confirmation of this scheme against real, non-dry-run Arena
writes was done via FO-prefixed items — see
`dilon-arena-document-standard-fo`'s requirements doc for the full
verification record; this scheme applies identically to FTP.

## Item connections

- **File category**: "Quality Procedure" (`list_file_categories`, match by
  name — never hardcode the GUID; shared with
  `dilon-arena-document-standard-qcp` — QCP and FTP file to the same Arena
  file category).
- **Change Affected-Items picklist value**: **unconfirmed.**
  `dilon-arena-eco-creator`'s Affected-Items mapping historically only
  named FO/WI/PL/RE explicitly and defaulted everything else, including
  FTP, to `"Other Document(s)"` — that default was never actually
  confirmed correct for FTP specifically. Before relying on it, check
  `list_change_category_attributes`'s `possibleValues` for the Affected
  Items attribute against a real FTP change, or ask the user. See Known
  gaps.

## Usage / update triggers

FTP documents are **narrative** documents — compile with
`dilon-document-compiler`, not `dilon-document-form-compiler`.

No special reissue trigger known: every change to an FTP item is assumed
to follow the standard revision-bump behavior above, same as WI. Not
separately confirmed with the user — flag if a reissue-style exception
turns out to apply here too.

## Known gaps

- **Unconfirmed**: the Affected-Items picklist value for FTP (Item
  connections above) — resolve live against a real change category before
  trusting `"Other Document(s)"`.
- **Untested**: whether omitting `new_revision_number` on a production
  release that follows a run of prototype iterations correctly
  auto-assigns the matching plain numeric, or drifts/errors. Until tested,
  always pass the value explicitly.
- No convention yet defined for what happens if a prototype sequence is
  abandoned entirely before reaching production release.
- Doesn't cover file *content* editing — only naming and revision-numbering.
