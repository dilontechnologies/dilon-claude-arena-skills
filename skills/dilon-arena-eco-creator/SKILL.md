---
name: dilon-arena-eco-creator
description: Create and populate an Engineering Change Order (ECO), Deviation, or Admin Correction in Arena, including affected items, file attachment (new documents and revisions), and submission for routing — per Dilon's Change Creation work instruction (SOP-00004). Use when asked to create an ECO, build a change record, or release/revise a controlled document in Arena.
---

# Dilon Arena ECO Creator

Drives the Arena MCP server to build a complete, submission-ready change
record, following `Change Creation Draft.docx` (WI supporting SOP-00004
Change Management). Every GUID is resolved live via MCP calls — never
hardcode a category, phase, or attribute GUID in this skill.

## 1. Gather inputs

Ask the user for:
- The affected item number(s) (or GUIDs, if already known).
- The reason/trigger for the change: a CAPA/complaint/NCMR/audit/ECO
  reference, or the actual driving reason if none apply (e.g. "new product
  development").
- Whether this is an **Engineering Change Order** (permanent), **Deviation**
  (temporary, needs an expiration date), or **Admin Correction** (clerical
  only, no revision advance).
- Local paths to the clean docx and pdf, and — if this is a revision of an
  already-released document — the redlined version too.

## 2. Resolve GUIDs live

- `list_change_categories` -> match the category name the user selected in
  step 1.
- `list_change_category_attributes(category_guid)` -> match these fields by
  display name, exactly as Arena shows them:
  - "Effect on Product Already Delivered (Describe)"
  - "Effect on Product in Process (Describe)"
  - "Evaluation of Constituent Parts"
  - "Evaluation of Change of Risk Management Inputs / Outputs Conducted"
  - "Evaluation of Product Realization Process (Describe)"
  - "Evaluation Performed By"
  - "Product Change?"
  - "Is Training Required?" and "Required Person(s) for Training"
  - "Parts Become Effective"
  - "Regulatory Review Number Generated?" and "Regulatory Review Number"
  - The Affected Items multiselect picklist attribute (no exact FTP/QCP
    entries — map FO->"Form (FO)", WI->"Work Instruction (WI)",
    PL->"Test Plan (TP)", RE->"Test Report (TR)", anything else->"Other
    Document(s)")
- `list_item_lifecycle_phases` -> match the target phase name(s) the user
  wants each affected item to move to.
- `list_change_routings(category_guid)` and `list_change_administrators` ->
  resolve routing/administrator GUIDs needed for step 8's `route_change` call.
- `search_items` / `get_item` -> for each affected item number, resolve the
  item GUID and its **working revision** GUID (`add_items_to_change` needs
  the working revision GUID, not the item GUID — check `get_item`'s response
  for the working revision alongside the effective revision).
- If this is a revision of an already-released document: `get_item_files`
  on that item to find the existing file's GUID and item-file association
  GUID.

## 3. Title

Verb-first: Create / Import / Release / Update / Obsolete, then the item or
document number, then a few words on what changed. Example: "Update
Manufacturing Documents for 820-00006."

## 4. Description

State what's changing (with the item/doc number), why (the reason/trigger
from step 1), and the reference (linked CAPA/complaint/NCMR/audit/ECO), or
the driving reason if none apply.

## 5. Change-level screening

Ask: does this change apply to a device commercialized, CE-marked, or
licensed in any jurisdiction?
- **No** -> Minor. No regulatory review required.
- **Yes** -> ask the follow-up questions. Any "Yes" -> Major, regulatory
  review required before routing (see step 8). All "No" -> Minor.

## 6. Create the change

Call `create_change` with the title (step 3), category GUID (step 2), and
`additional_attributes` covering every field resolved in step 2. Use "No
effect" text for any free-text assessment field with nothing to report —
never leave one blank.

## 7. Add affected items

For each affected item, call `add_items_to_change` with its working
revision GUID, target lifecycle phase GUID, and **`files_view=True`**. This
is what resolves the WI's "yellow dot" warning — Arena won't include a
pending file change in the release unless the Files view is marked included.
If an item was already added without this flag, fix it afterward with
`update_change_affected_item(views={"filesView": {"includedInThisChange": True}})`.

## 8. Attach documents

Naming, per the WI: file name `[Number] Rev [nn].[ext]`, item name
descriptive only with no type prefix, file title `[Number] [Item Name]`
without the revision. Before uploading, rename a local temp copy of the
source file to match if it isn't already named per convention.

- **New item/document** (no existing controlled file):
  1. `create_file(title="<Number> <Item Name>")` for the pdf.
  2. `upload_file_content(file_guid, local_path)` to add its initial content.
  3. `add_existing_file_to_item(item_guid, file_guid, primary=True)`.
  4. Repeat 1-3 for the docx with `primary=False`.
- **Revision of an already-released document:**
  1. Use the file GUID found in step 2's `get_item_files` call.
  2. `create_file_edition(file_guid, edition="<next rev>", local_path=<new pdf>)`.
  3. `update_item_file_association(item_guid, file_assoc_guid, primary=True)`
     to confirm the pdf stays primary.
  4. Repeat step 2 for the docx.
  5. The redline is traceability evidence for the *change*, not the
     controlled item record — attach it with
     `add_file_to_change(change_guid, redline_file_guid)`, not to the item.

(Arena's UI enforces updating a file "through the ECO's affected-item Files
view, not from the file record" — a UI-only distinction between which screen
you click "Update Edition" from. The REST API has one mechanism for adding
an edition regardless: `create_file_edition`. Step 7's `files_view=True`
flag is what gets the functionally equivalent result.)

## 9. Pre-submit checklist

Before step 10, restate this checklist to the user and get confirmation each
item is true:
- Title and description follow the standard (steps 3-4).
- Screening complete, change level set; for Major, regulatory review is
  complete (step 5).
- Affected items added with Files view included, no unresolved yellow dots
  (step 7).
- Documents attached, pdf primary, redline attached for a revision (step 8).
- Training set (step 2's "Is Training Required?" field) and routed if
  required.
- Required approvers present: Quality + Regulatory approve every
  ECO/Deviation, at least 2 independent approvers, and the creator/owner is
  not the sole approver.

## 10. Submit / route

This is the one hard-to-reverse, visible-to-others step in this skill.
Show the user the fully-populated change (title, description, screening
result, all assessment field values, affected items, attached documents)
and get explicit confirmation before calling `route_change`. Once confirmed,
call `route_change(guid, status="SUBMITTED", comment=..., administrator_guids=...)`
to submit to the Change Administrator per step 9's approver rules.

Steps 6-8 are cheap to redo — the change stays in a Working state and is
deletable, and file editions can be corrected. Do not skip the confirmation
in this step even if every earlier step succeeded without issue.
