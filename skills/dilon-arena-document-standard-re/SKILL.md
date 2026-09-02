---
name: dilon-arena-document-standard-re
description: Dilon's document standard for Test Report (RE) controlled documents in Arena — file name/title convention, revision-numbering scheme (including the reissue-as-new-item exception once a completed report exists against the plan it tests), file-category and change Affected-Items picklist mapping, and narrative-vs-form classification. Use when creating, naming, or revising an RE-prefixed item/file, or when dilon-arena-eco-creator needs RE's naming/revision/item-connection rules.
---

# Dilon Document Standard — RE (Test Report)

Single source of truth for Dilon's rules on RE-prefixed controlled
documents. `dilon-arena-eco-creator` defers to this skill for RE items
rather than duplicating this guidance.

## Naming

**File `name`** — no direct Arena API field; set via the uploaded
filename. Convention: `<Item Number> Rev <Revision Number>.<ext>` (e.g.
`RE-00023 Rev 01.docx`) for a normal revision, or, once the reissue
exception below applies, the new item's own number in the same pattern
(e.g. `RE-00023-02 Rev 00.docx`). This MCP server's `create_file`/
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
completed report already exists against the plan this report tests — see
the Usage section below for that exception, which replaces revision-
bumping with a new item instead.**

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
verification record; it applies identically to RE up until the reissue
exception fires.

## Expected file formats

Default: **docx** (non-primary) + **pdf** (primary) — same default every
`dilon-arena-document-standard-<type>` skill in this repo states, no
known exception for this type specifically, including for the new item
created under the reissue exception above (it gets its own fresh docx+pdf
pair, same as any other new item). `dilon-arena-eco-creator`'s step 8
iterates whichever formats and primary designation this section lists
rather than assuming docx+pdf on its own; if this type is ever confirmed
to need a different set, update this section — that skill's step 8 loop
stays generic. See `dilon-arena-document-standard-fo`'s requirements doc
for the one confirmed data point behind this default (`FO-00004`'s
pdf/docx pair).

## Item connections

- **File category**: "Report" (`list_file_categories`, match by name —
  never hardcode the GUID).
- **Change Affected-Items picklist value**: `"Test Report (TR)"` (the
  multiselect picklist attribute on the change category,
  `list_change_category_attributes` — wrap it in a single-element array,
  e.g. `["Test Report (TR)"]`, since this attribute is `multiSelect: true`).

## Suggested connections

Via `create_item_reference` (`dilon-arena-eco-creator` step 8b) — check
`get_item_references` first and skip a target that's already linked:
- The Plan (PL) this report tests. This generalizes the report-tests-plan
  link the reissue exception below already creates for a reissued report
  — step 8b creates/confirms it for every RE, not just at reissue time.

## Usage / update triggers

RE documents are **forms** despite being a "Report"
(`@@@FORM_FIELD:FieldGrid@@@` / `Form_Section_Header` markers) — compile
with `dilon-document-form-compiler`, not `dilon-document-compiler`. Check
the markdown body for form markers rather than assuming by doc-number
prefix if this is ever in doubt.

**Exception to the standard revision-bump behavior above: once a completed
report already exists against the plan this report tests, a further
change to that report becomes a new item, not a revision.** Same
rationale and mechanism as `dilon-arena-document-standard-pl`'s exception
— a tested/completed record's content shouldn't change in place.

1. **Does the exception apply?** First resolve which Plan this report
   tests: `get_item_references(report_item_guid)` (bidirectional —
   querying either side of a reference returns it). If no reference exists
   yet (first time this report/plan pair is tracked), ask the user which
   Plan this report tests — don't guess. Then check whether a completed
   report already exists for that Plan, exactly as
   `dilon-arena-document-standard-pl`'s Usage section step 1 describes
   (same "completed" definition, same fallback-to-asking-the-user for a
   pair with no existing Item References yet).
   - If no completed report exists for that plan yet: the exception
     doesn't apply — follow the standard revision-bump behavior above.
   - If one does: continue below instead of bumping the revision.
2. **Compute the new item number** — identical mechanism to
   `dilon-arena-document-standard-pl`'s Usage section step 2, applied to
   this report's own root number (e.g. `RE-00023` -> `RE-00023-02`). The
   suffix counter is independent per root number — a report's suffix
   sequence has nothing to do with which plan it's currently testing, or
   that plan's own sequence.
3. **Create the new item** — identical mechanism to
   `dilon-arena-document-standard-pl`'s Usage section step 3, with
   category "Report" instead of "Plan".
4. **Link for traceability.** Always create
   `create_item_reference(from_item_guid=<new report item's guid>,
   to_item_guid=<the report it supersedes>)`. Also (re-)establish the
   report-tests-plan link on the **new** report item:
   `create_item_reference(from_item_guid=<new report item's guid>,
   to_item_guid=<the plan item's guid>)` — this is also what step 1's
   "completed report" check relies on for every pair going forward. These
   links are immediate and unconditional — visible in Arena the instant
   they're created, not gated on the carrying ECO's approval, and not
   removed if that ECO is later canceled.

## Known gaps

- **Unconfirmed with the user**: the "completed" definition used in step 1
  above (`RELEASED`/`EFFECTIVE` assumed) — same open question as
  `dilon-arena-document-standard-pl`.
- **Unconfirmed**: whether the `-NN` suffix needs to grow past 2 digits.
- **Not yet tested end-to-end** inside `dilon-arena-eco-creator`'s actual
  step 8 attach flow on a real report reissue — only the underlying
  item-creation/numbering-override and item-reference mechanics were
  confirmed standalone, against disposable test items in the sandbox
  workspace.
- No backfill plan for existing released PL/RE pairs that predate this
  rule, beyond "ask the user the first time" (step 1 above).
- **Untested** (inherited from the base revision scheme, applies before
  any completed report exists against the plan this report tests):
  whether omitting `new_revision_number` on a production release that
  follows a run of prototype iterations correctly auto-assigns the
  matching plain numeric. Always pass the value explicitly.
- Naming for the new item: same descriptive name convention as the
  original item — not yet tested whether Dilon wants any indication in the
  item `name` itself that this is a reissue.
