---
name: dilon-arena-document-standard-pl
description: Dilon's document standard for Test Plan (PL) controlled documents in Arena — file name/title convention, revision-numbering scheme (including the reissue-as-new-item exception once a completed report exists), file-category and change Affected-Items picklist mapping, and narrative-vs-form classification. Use when creating, naming, or revising a PL-prefixed item/file, or when dilon-arena-eco-creator needs PL's naming/revision/item-connection rules.
---

# Dilon Document Standard — PL (Test Plan)

Single source of truth for Dilon's rules on PL-prefixed controlled
documents. `dilon-arena-eco-creator` defers to this skill for PL items
rather than duplicating this guidance.

## Naming

**File `name`** — no direct Arena API field; set via the uploaded
filename. Convention: `<Item Number> Rev <Revision Number>.<ext>` (e.g.
`PL-00004 Rev 01.docx`) for a normal revision, or, once the reissue
exception below applies, the new item's own number in the same pattern
(e.g. `PL-00004-01 Rev 00.docx`). This MCP server's `create_file`/
`create_file_edition`/`update_file_summary` tools expose no `name`
parameter — Arena populates a file's `name` from the uploaded file's own
filename on a multipart (`storage_method="FILE"`) upload. Rename a local
temp copy of the source file to this convention *before* calling
`create_file`/`create_file_edition` — there's no way to set `name` after
the fact.

**File `title`** — stays descriptive, never carries the revision.
Convention: `<Item Number> <Item Name>`, no revision number in it ever.

## Revision

Baseline/prototype/production revision-numbering scheme, **except once a
completed report already exists against this plan — see the Usage section
below for that exception, which replaces revision-bumping with a new item
instead.**

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

**Always pass `new_revision_number` explicitly**, for every transition
this scheme still applies to.

Empirical confirmation of this base scheme against real, non-dry-run Arena
writes was done via FO-prefixed items — see
`dilon-arena-document-standard-fo`'s requirements doc for the full
verification record; it applies identically to PL up until the reissue
exception fires.

## Item connections

- **File category**: "Plan" (`list_file_categories`, match by name — never
  hardcode the GUID).
- **Change Affected-Items picklist value**: `"Test Plan (TP)"` (the
  multiselect picklist attribute on the change category,
  `list_change_category_attributes` — wrap it in a single-element array,
  e.g. `["Test Plan (TP)"]`, since this attribute is `multiSelect: true`).

## Usage / update triggers

PL documents are **narrative** documents despite being a "Plan" — compile
with `dilon-document-compiler`, not `dilon-document-form-compiler`. Check
the markdown body for form markers rather than assuming by doc-number
prefix if this is ever in doubt.

**Exception to the standard revision-bump behavior above: once a completed
report already exists against this plan, a further change becomes a new
item, not a revision.** Dilon wants a plan's and report's history to stay
pure once real testing has happened against it — a revision bump on the
same item would let a tested/completed record's content change in place.

1. **Does the exception apply?** Check whether a completed report already
   exists for this plan: `get_item_references(plan_item_guid)`, filter
   results to items whose category is Report, and check each linked
   report's lifecycle phase/revision status. Working assumption for
   "completed": `RELEASED` lifecycle phase / `EFFECTIVE` revision status —
   **not yet confirmed with the user**, see Known gaps. Pre-existing PL/RE
   items may have **no** Item References at all (nothing backfilled) — the
   first time this check applies to a given plan, ask the user directly
   whether a completed report exists rather than trusting an empty query
   result; only rely on the query once step 4 below has started creating
   the links for that plan.
   - If no completed report exists: the exception doesn't apply — follow
     the standard revision-bump behavior above.
   - If a completed report exists: continue below instead of bumping the
     revision.
2. **Compute the new item number.** Find the root number: this item's own
   number, with any existing `-NN` suffix stripped (e.g. re-revising
   `PL-00004-01` roots to `PL-00004`, not `PL-00004-01`). Find the next
   `NN`: `search_items(number="<root>-*")`, take the highest existing
   suffix, add 1, zero-padded to 2 digits (`"01"`, `"02"`, ...); if none
   exist yet, `NN = "01"`. New number: `<root>-<NN>` (e.g. `PL-00004-01`).
   The suffix counter is independent per root number.
3. **Create the new item.** Category stays "Plan" (no new Arena item
   category needed or should be created). Use Arena's "Basic Item Number"
   format (`list_item_number_formats`, match name exactly), not the
   default "Document" format — the Document format's auto-sequence field
   silently ignores a manually-set value; "Basic Item Number"'s single
   `FREE_TEXT` field accepts the computed number from step 2 directly.
   Resolve any `required: true` custom attributes on the Plan category
   live (`list_item_category_attributes`) — don't assume a fixed field
   list; this has been observed to differ between sandbox and production
   workspaces. `create_item(name=<same descriptive name convention as the
   original item>, category_guid=<Plan category guid>,
   number_format_guid=<Basic Item Number format guid>,
   number_format_fields=[{"guid": <its one field's guid>, "value": "<computed
   number>"}], additional_attributes=[<required attributes resolved
   above>])`. This is a new item, not a revision — add it to the change via
   `add_items_to_change`'s new-item path (no prior working-revision GUID
   needed), then attach its docx/pdf content following
   `dilon-arena-eco-creator` step 8's "new item/document" branch; the new
   item's own file `name`/`title`/revision string still follow this
   skill's Naming/Revision sections above, starting fresh as a brand-new
   item, independent of the `-NN` item-numbering.
4. **Link for traceability.** Arena's own revision history won't show any
   relationship between e.g. `PL-00004` and `PL-00004-01` — they're
   different items now. Always create
   `create_item_reference(from_item_guid=<new item's guid>,
   to_item_guid=<the item it supersedes>)`, regardless of whether this
   plan or its report is being reissued. These links are immediate and
   unconditional — visible in Arena the instant they're created, not gated
   on the carrying ECO's approval, and not removed if that ECO is later
   canceled.

## Known gaps

- **Unconfirmed with the user**: the "completed" definition in step 1
  above (`RELEASED`/`EFFECTIVE` assumed).
- **Unconfirmed**: whether the `-NN` suffix needs to grow past 2 digits
  (zero-padding width beyond `"99"` reissues isn't specified anywhere).
- **Not yet tested end-to-end** inside `dilon-arena-eco-creator`'s actual
  step 8 attach flow on a real PL pair with a real report — only the
  underlying item-creation/numbering-override and item-reference mechanics
  were confirmed standalone, against disposable test items in the sandbox
  workspace.
- No backfill plan for existing released PL/RE pairs that predate this
  rule, beyond "ask the user the first time" (step 1 above).
- **Untested** (inherited from the base revision scheme, applies before
  any completed report exists against a plan): whether omitting
  `new_revision_number` on a production release that follows a run of
  prototype iterations correctly auto-assigns the matching plain numeric.
  Always pass the value explicitly.
- Naming for the new item: same descriptive name convention as the
  original item — not yet tested whether Dilon wants any indication in the
  item `name` itself that this is a reissue, as opposed to relying solely
  on the number suffix and the traceability reference.
