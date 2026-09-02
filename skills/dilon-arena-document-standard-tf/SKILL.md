---
name: dilon-arena-document-standard-tf
description: Dilon's document standard for TF (Technical File) controlled documents in Arena — file name/title convention, revision-numbering scheme, file-category mapping ("Technical File"), and diagram-source export (drawio/Visio/etc.) in place of the standard Dilon-markdown compile pipeline. Flags the change Affected-Items picklist value as unconfirmed. Use when creating, naming, or revising a TF-prefixed item/file, or when dilon-arena-eco-creator needs TF's naming/revision/item-connection rules.
---

# Dilon Document Standard — TF (Technical File)

Single source of truth for Dilon's rules on TF-prefixed controlled
documents. `dilon-arena-eco-creator` defers to this skill for TF items
rather than duplicating this guidance.

## Naming

Same convention as every other type. **File `name`** — no direct Arena
API field; set via the uploaded filename. Convention: `<Item Number> Rev
<Revision Number>.<ext>` (e.g. `TF-00008 Rev 00-A.pdf`, confirmed against
a real Detector Head TF item). This MCP server's `create_file`/
`create_file_edition`/`update_file_summary` tools expose no `name`
parameter — Arena populates a file's `name` from the uploaded file's own
filename on a multipart (`storage_method="FILE"`) upload. Rename a local
temp copy of the source file to this convention *before* calling
`create_file`/`create_file_edition` — there's no way to set `name` after
the fact.

**File `title`** — stays descriptive, never carries the revision.
Convention: `<Item Number> <Item Name>`, no revision number in it ever.

## Revision

Same baseline/prototype/production scheme as every other type. Applies to
`add_items_to_change`'s and `update_change_affected_item`'s
`new_revision_number` parameter.

- **Baseline / production revision**: two-digit numeric, `"00"`, `"01"`,
  `"02"`, ... incrementing by one on each production release. A
  never-released item's first production release is `"00"`.
- **Prototype Release ahead of the next production release**: revision is
  `"<next-numeric>-<letter>"`. E.g. never-released item, first prototype
  iteration: `"00-A"`, second: `"00-B"`. The real Detector Head TF item,
  `TF-00008`, currently sits at `"00-A"`.
- **Promotion to actual production release**: the revision condenses back
  down to the plain numeric (`"02"`); the document's revision-history table
  gets one consolidated row for it, not one per prototype iteration.

**Always pass `new_revision_number` explicitly**, same as every other
type.

Empirical confirmation of this base scheme against real, non-dry-run Arena
writes was done via FO-prefixed items — see
`dilon-arena-document-standard-fo`'s requirements doc for the full
verification record.

## Expected file formats

**Primary: pdf**, same as every other type. **Non-primary/source format
varies by TF** — unlike every other type, there's no single fixed
non-primary format. `.drawio` is one confirmed example (`TF-00008` has a
`.drawio` source alongside its `.pdf`), but a diagram may be authored in a
different tool instead (e.g. Visio `.vsdx`). Check what source format the
user actually has before assuming `.drawio`.

## Item connections

- **File category**: "Technical File" (`list_file_categories`, match by
  name — never hardcode the GUID; confirmed to exist in this workspace as
  `File \ Document File \ Technical File`).
- **Change Affected-Items picklist value**: **unconfirmed.** No dedicated
  entry for TF exists in the confirmed Affected-Items value list (see
  `dilon-arena-eco-creator`'s requirements doc for the full confirmed
  list) — closest fit is `"Other Document(s)"`, same treatment as
  QCP/FTP. Resolve live against `possibleValues` before trusting it.
  Remember this attribute is `multiSelect: true` — wrap the value in a
  single-element array (`["Other Document(s)"]`).

## Suggested connections

Via `create_item_reference` (`dilon-arena-eco-creator` step 8b) — check
`get_item_references` first and skip a target that's already linked.
Unlike every other type's fixed target list, a TF's connections are
**self-referential**: link it to whatever document(s), part(s),
subassembly(ies), or fixture(s) it actually depicts. Ask the user which
items the diagram covers — don't guess from its name or description.

## Usage / update triggers

TF documents are **not compiled from Dilon markdown source** — unlike
every other type, neither `dilon-document-compiler` nor
`dilon-document-form-compiler` applies, and `dilon-arena-eco-creator`
step 1a's markdown-source deferral is skipped entirely for TF. The user
always supplies the diagram source directly.

**Diagram source -> pdf export.** When the source is a `.drawio` file,
draw.io's desktop app exposes a command-line export (`--export --format
pdf --output <out.pdf> <in.drawio>`, via the installed `draw.io`/
`draw.io.exe` executable on Windows) that can produce the primary pdf
without manual UI interaction — the same role Word COM automation plays
for docx-sourced types in step 1a. **Not yet confirmed working in this
environment** — verify the exact executable path and flag syntax locally
before relying on it; see Known gaps. For a non-`.drawio` source (e.g.
Visio), no export method is defined yet — ask the user for a
pre-exported pdf rather than guessing a conversion.

No special reissue trigger known: every change to a TF item is assumed to
follow the standard revision-bump behavior above, same as WI/QCP/FTP. Not
separately confirmed with the user.

## Known gaps

- **Unconfirmed**: the Affected-Items picklist value for TF (Item
  connections above) — resolve live against a real change category before
  trusting `"Other Document(s)"`.
- **Unconfirmed**: the draw.io CLI export syntax/executable path (Usage
  above) — not tested in this environment yet.
- **Undefined**: conversion method for a non-`.drawio` diagram source
  (e.g. Visio `.vsdx`) to pdf.
- **Untested**: whether omitting `new_revision_number` on a production
  release that follows a run of prototype iterations correctly
  auto-assigns the matching plain numeric, or drifts/errors. Until
  tested, always pass the value explicitly.
- No convention yet defined for what happens if a prototype sequence is
  abandoned entirely before reaching production release.
- Doesn't cover file *content* editing — only naming and revision-numbering.
