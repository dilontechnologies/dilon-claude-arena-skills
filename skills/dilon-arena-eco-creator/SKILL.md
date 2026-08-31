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
  already-released document — the redlined version too. If these don't
  exist yet and the source is Dilon-formatted markdown, see step 1a.

## 1a. Compile documents from Dilon markdown source (if applicable)

Skip this step if the user already has clean docx/pdf files in hand.

- Determine whether each document is a **narrative** document (prose
  sections like Purpose/Scope — WI, FTP, QCP, and PL all fall in this
  bucket, PL included despite being a "Plan") or a **fillable form**
  (`@@@FORM_FIELD:FieldGrid@@@` / `Form_Section_Header` markers — FO
  travelers, and RE reports despite being a "Report"). Check the markdown
  body for form markers rather than assuming by doc-number prefix; PL and
  RE are exceptions to the naive prefix->type mapping.
- Run `check_deps.py` for the relevant compiler skill first (pandoc,
  `python-docx`, `docxcompose`, `yaml`, `jinja2`).
- Compile to docx:
  - Narrative -> `dilon-document-compiler/scripts/generate_dilon_doc.py
    <input.md> <output.docx>`.
  - Form -> `dilon-document-form-compiler/scripts/generate_dilon_form.py
    <input.md> <output.docx>`.
- Convert docx -> pdf via Word COM automation (no CLI converter is
  reliably available cross-environment): PowerShell `New-Object
  -ComObject Word.Application`, `Documents.Open($inPath, $false, $true)`,
  `.SaveAs([ref]$outPath, [ref]17)` (`17` = `wdFormatPDF`), `.Close($false)`.
  Confirm Word is installed first via `Get-ItemProperty
  HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WINWORD.EXE`.
  Reuse one Word instance across all files in the batch rather than
  relaunching per file, and `$word.Quit()` at the end.

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
- `list_change_administrators` -> resolve the administrator GUID(s) needed
  for step 10's `route_change` call. (`list_change_routings` returns
  admin-defined approval routing templates; this workspace has none
  configured, so it isn't used in this flow — see the known limitation
  below on adding reviewers.)
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
  1. `create_file(title="<Number> <Item Name>", storage_method="FILE",
     edition="1", local_path=<pdf path>)` — a single multipart call that
     creates the file record and uploads its content together. `edition`
     is required; Arena rejects the call without it.
  2. `add_existing_file_to_item(item_guid, file_guid, primary=True)`.
  3. Repeat 1-2 for the docx with `primary=False`.
  4. Also attach both to the change itself:
     `add_file_to_change(change_guid, file_guid)` for each — item
     association alone doesn't put them in the change's Files view.
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

**Fixed 2026-08-31:** `create_file` used to always JSON-POST
`storageMethodName: "FILE"` to `/files`, which Arena rejects outright
(its JSON endpoint only accepts `FTP`/`WEB`/`PLACE_HOLDER`) — this broke
the New-item/document flow above every time. It now routes `storage_method=
"FILE"` calls through a multipart POST to `/files` (uploading content in
the same request) and routes `FTP`/`WEB`/`PLACE_HOLDER` calls to
`/files/json` instead. The default `storage_method` also changed from
`"FILE"` to `"PLACE_HOLDER"` — always pass `storage_method="FILE"`
explicitly for the flow above.

## 8a. Set file metadata (category, author, format)

Do this after step 8's create/attach calls, for every new file (docx and
pdf both):

- **Category**: `list_file_categories` -> match by name (e.g. "Form" for
  travelers, "Work Instructions" for WIs, "Quality Procedure" for QCP/FTP,
  "Plan" for PL, "Report" for RE) -> `update_file_summary(guid,
  category_guid=...)`. Never hardcode the GUID — resolve it live per
  workspace, same as every other GUID in this skill.
- **Author**: `update_file_summary(guid, author_full_name=...)`. Ask the
  user whether this should be the document's original/front-matter author
  or the person actually performing this compile-and-upload run — don't
  silently default to either.
- **Format**: `update_file_summary(guid, format="DOCX")` /
  `format="PDF")`. `list_file_attributes` reports `format` as a
  `DROP_DOWN` field, but Arena accepts new string values on write with no
  separate picklist-management step required — confirmed passing `"DOCX"`
  and `"PDF"` directly.

**Fixed 2026-08-31:** `update_file_summary` had no `category_guid`
parameter at all — added it (`PUT /files/<guid>` accepts `category:
{guid}` per Arena's `FileDetailVo` schema, the same shape `create_file`
already used).

## 9. Pre-submit checklist

Before step 10, restate this checklist to the user and get confirmation each
item is true:
- Title and description follow the standard (steps 3-4).
- Screening complete, change level set; for Major, regulatory review is
  complete (step 5).
- Affected items added with Files view included, no unresolved yellow dots
  (step 7).
- Documents attached, pdf primary, redline attached for a revision (step 8),
  category/author/format populated on each file (step 8a).
- Training set (step 2's "Is Training Required?" field) and routed if
  required.
- Required approvers present: Quality + Regulatory approve every
  ECO/Deviation, at least 2 independent approvers, and the creator/owner is
  not the sole approver. **This skill cannot add reviewers via the API** (see
  known limitation below) — tell the user which reviewers this checklist
  requires and have them add each one in Arena's Web UI before or during
  routing.

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

## Known limitation: reviewers/approvers cannot be added via the API

Arena has no API to add ad-hoc reviewers to a specific change. The only
mechanism the REST API exposes is admin-defined approval routing: a routing
template (`list_change_routings`, applied at creation via `create_change`'s
`routing_guids`) that carries its own preconfigured reviewer list. This
workspace has no routing templates configured, so that mechanism isn't
available either — there is currently no way to reach the "add these named
people as reviewers on this ECO" outcome through the API.

Reviewer assignment therefore has to be a manual step in Arena's Web UI,
performed by the user. Step 9's checklist should tell the user exactly which
reviewers/approvers are required (Quality, Regulatory, etc. per that step's
rules) so they know what to add; this skill cannot verify or set them itself.

**TODO:** once a set of saved per-user/workspace settings exists (planned to
follow the same pattern as `env/environments.example.json` — a checked-in
example plus a gitignored `*.local.*` file with real values), this skill
should read a recommended reviewer list from there and present it to the
user as a suggestion for step 9, rather than asking from scratch each time.
That settings mechanism doesn't exist yet.

## Known limitation: costingView is not API-editable

Like `filesView` (step 7), an affected item's BOM/Source/Cost views also
need to be flagged `includedInThisChange` for the corresponding changes to
actually take effect on release. `bomView` and `sourcingView` can be set via
`update_change_affected_item`, but Arena's REST API rejects any write to
`costingView` on document-category items (WI/PL/RE/Traveler/FO) with
`{"code": 3032, "message": "The attribute \"costingView\" is not editable."}`
— even though the identical request body works for the other views, and
even though the same checkbox can be set with no error through Arena's web
UI. Confirmed 2026-08-31 on ECO-000262 (820-00006 Detector Head).

This isn't a request-shape bug (verified against Arena's own
`endpoint_change_update_item.md` doc and error-code reference) — it's Arena
either gating that specific attribute behind different permissions for the
REST API vs. the UI's internal client, or never having exposed it on this
endpoint at all for these item categories. **TODO:** look into whether
Arena support/admin settings can grant the API client the same access the
UI has. Until resolved, this skill cannot fully automate Cost-view
inclusion for document items — flag it to the user as a manual UI step
rather than silently skipping it.
