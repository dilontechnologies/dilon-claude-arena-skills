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
  wants each affected item to move to. **Match by `stage` (`PRELIMINARY`,
  `DESIGN`, `PRODUCTION`, etc.) as well as name** — a workspace can have
  two phases with the identical display name in different stages (e.g.
  "Prototype Release" exists in both `DESIGN` and `PRODUCTION`), and
  they're different GUIDs with different reachability. See step 7 for
  which transitions between phases are actually possible.
- `list_change_administrators` -> resolve the administrator GUID(s) needed
  for step 10's `route_change` call. (`list_change_routings` returns
  admin-defined approval routing templates; this workspace has none
  configured, so it isn't used in this flow — see the known limitation
  below on adding reviewers.)
- `search_items` / `get_item` -> for each affected item number, resolve the
  item GUID. Do **not** use `get_item`'s response to find the working
  revision — it never surfaces one, even when one exists. Instead call
  `get_item_revisions(<any revision guid of the item>)` and find the entry
  with `"status": 0` (`revisionStatus: "WORKING"`); that entry's `guid` is
  what `add_items_to_change` needs as `new_item_revision_guid`. Every item
  has this dormant working-revision entry, including a RELEASED item never
  revised since release. Skip this lookup only for an item still
  Unreleased/WORKING that no change has ever touched — there, the item's
  own GUID already is its working revision.
- If this is a revision of an already-released document: `get_item_files`
  on that item to find the existing file's GUID and item-file association
  GUID.

## 3. Title

Verb-first: Create / Import / Release / Update / Obsolete, then the item or
document number **and its descriptive name**, then a few words on what
changed. Example: "Update Manufacturing Documents for 820-00006 Detector
Head" (not just "...for 820-00006").

## 4. Description

Reproduce this structure — confirmed against a representative released ECO
in the workspace, not free-form prose:

```
<Opening sentence: what's changing and why>

Released to Prototype Release: <doc numbers, comma-separated>.
Released: <doc numbers going straight to a released phase, if any>.
Obsoleted: <doc numbers, if any, with a short reason>.

Ref: <the CAPA/complaint/NCMR/audit/ECO reference, or the driving reason
if none apply>.

Does this change meet any of the following criteria? (Yes / No)

1. Could reasonably affect device safety or effectiveness
NO
2. Materially affects intended purpose, design, clinical performance, or benefit-risk profile
NO
...
```

- Each `Released to <phase>:`/`Obsoleted:` line lists the *exact* doc
  numbers going to that phase — don't collapse multiple phases into one
  list.
- The 6-question block is step 5's screening questions verbatim, each with
  a plain `YES`/`NO` on the line directly under it (not inline) — this is
  where that screening result actually gets recorded; Arena has no
  dedicated structured fields for these 6 questions.
- Even when "Regulatory Review Number Generated?" (step 2) is `No`, still
  fill the free-text "Regulatory Review Number" field with explanatory
  text (e.g. `"No regulatory review required."`) rather than leaving it
  blank.

## 5. Change-level screening

Ask: does this change apply to a device commercialized, CE-marked, or
licensed in any jurisdiction?
- **No** -> Minor. No regulatory review required.
- **Yes** -> ask these 6 follow-up questions (Yes/No each); any "Yes" ->
  Major, regulatory review required before routing (step 10). All "No" ->
  Minor.
  1. Could reasonably affect device safety or effectiveness
  2. Materially affects intended purpose, design, clinical performance, or
     benefit-risk profile
  3. Results in a change to QMS scope
  4. Introduces a new intended purpose, patient population, or clinical
     indication
  5. Major design change affecting performance, safety, operating
     principles, or clinical function
  6. Adds a product or process not covered by the current ISO
     certification

These are the same 6 questions step 4's Description block records with
YES/NO answers — confirmed by example from a representative released ECO,
not from the WI's own text. If a future WI revision enumerates the
follow-up questions explicitly, that becomes the authoritative source
instead.

## 6. Create the change

Call `create_change` with the title (step 3), category GUID (step 2), and
`additional_attributes` covering every field resolved in step 2. Use "No
effect" text for any free-text assessment field with nothing to report —
never leave one blank.

## 7. Add affected items

For each affected item, call `add_items_to_change` with its working
revision GUID (step 2), target lifecycle phase GUID (step 2, disambiguated
by stage), and the view flags below. If an item was already added with the
wrong flags, fix it afterward with `update_change_affected_item(views={...})`.

**View flags are not a blanket `files_view=True` — ask the user, per
affected item, which of these apply:**
- **Specs view (`specs_view`)**: always `True`, every item, no need to ask.
- **Files view (`files_view`)**: `True` if that item's attached
  files/documents are being added or revised by this change. This is what
  resolves the WI's "yellow dot" warning — Arena won't include a pending
  file change in the release unless Files view is marked included.
- **BOM view (`bom_view`)**: `True` if this change modifies that item's
  bill of materials (structure/line changes on an assembly). **The view
  flag doesn't perform or link the edit** — there's no
  `add_bom_line_to_change`-style call. Make the actual BOM edits with
  `create_bom_line`/`update_bom_line`/`delete_bom_line`, passing the
  item's **working revision GUID** (step 2) as `parent_item_guid` — BOM
  is per-revision data. Setting `bom_view=True` only declares that this
  revision's BOM differs from what's currently effective.
- **Sourcing view (`sourcing_view`)**: `True` if this change modifies that
  item's approved sources. Same pattern as BOM: make the edits with
  `create_item_source`/`update_item_source`/`delete_item_source` against
  the item's working revision GUID, then set the flag as a declaration,
  not a link.
- **Cost view (`costingView`)**: if this change affects that item's cost
  structure, tell the user to enable Cost view manually in Arena's UI for
  that specific item, and record on the pre-submit checklist (step 9)
  that it's still owed. This gap is deeper than just the view flag being
  API-blocked (known limitation below) — Arena represents item cost via
  Quote Line / Purchase records on Supplier Items
  (`/supplieritems/<guid>/quotes/<guid>`, `/supplieritems/<guid>/purchases/
  <guid>`), and this MCP server has no tools at all for either endpoint,
  not even read. There is currently no way for this skill, or a future
  verification script, to confirm a cost change actually happened — only
  that the user said one did.

**Lifecycle phase transitions are not fully general — verify before
assuming a target is reachable.** There's no rule like "same-stage =
allowed, cross-stage = blocked"; some same-stage transitions fail and some
cross-stage ones succeed. Confirmed reachable/blocked pairs (`PRELIMINARY`,
`DESIGN`, `PRODUCTION` stages):
- Unreleased -> RELEASED (`PRELIMINARY` -> `PRODUCTION`): works.
- Unreleased -> In Design (`PRELIMINARY` -> `DESIGN`): works.
- In Design -> Abandoned (`DESIGN` -> `DESIGN`): works.
- RELEASED -> RELEASED with a new revision (`PRODUCTION` -> same phase):
  works.
- RELEASED -> Prototype Release [`PRODUCTION` stage] (`PRODUCTION` ->
  `PRODUCTION`): works.
- Unreleased -> Obsolete (`PRELIMINARY` -> `PRODUCTION`): fails.
- Unreleased -> Abandoned (`PRELIMINARY` -> `DESIGN`): fails, despite
  looking same-stage-family.
- RELEASED -> Prototype Release [`DESIGN` stage] (`PRODUCTION` ->
  `DESIGN`): fails.

This list is confirmed, not exhaustive — treat any pair not listed here as
unknown, and test it in the sandbox workspace ("Dilon Technologies
Validation," same credentials, different `ARENA_WORKSPACE_ID`) before
trying it against production. A rejected transition returns error 3063
("Lifecycle transition from X to Y is not supported"); the fix is
routing through an intermediate phase, not retrying with different
parameters.

**Obsolete vs. Abandoned are not interchangeable.** Obsolete is for a
document that *was* released and is now retired/superseded. Abandoned is
for a document that *never* properly released. Since Unreleased ->
Abandoned isn't directly reachable, retiring a never-released item needs
**two sequential ECOs**: one moving it Unreleased -> In Design (or another
reachable `DESIGN`-stage phase), a second moving that to Abandoned. This
can't be collapsed into one ECO.

**Only pass `new_revision_number` explicitly when moving into a
Prototype-Release-type phase** — those use a lettered scheme (`"A"`,
`"B"`, ...) that Arena won't infer on its own. For any transition into or
within a RELEASED-type phase, **omit** `new_revision_number` — Arena
assigns the next numeric revision (`"00"`, `"01"`, ...) automatically, and
passing one explicitly there isn't necessary.

**Do not use `add_items_to_change`'s `affected_item_revision_guid`
parameter.** It's a confirmed dead end — Arena rejects it outright
(`"affectedItemRevision" is not creatable`; it's a system-computed,
response-only field describing pre-change state, not something you can set).

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
- Affected items added with the correct view flags per step 7 (Specs
  always; Files/BOM/Sourcing only where that item actually changed in that
  way), no unresolved yellow dots. For any item where Cost view applies,
  confirm the user actually enabled it manually in Arena's UI — this
  skill can't set or verify `costingView` itself (see known limitation
  below).
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
and get explicit confirmation before calling `route_change` at all.

Submission is a **two-call sequence**, not one:
1. `route_change(guid, status="SUBMITTED", comment=..., administrator_guids=[...])`
   moves the change to `SUBMITTED_FOR_ROUTING`. `administrator_guids` must
   reference a user already configured as a change administrator for that
   category (step 2's `list_change_administrators`) — an arbitrary valid
   user GUID is rejected (`"Invalid change administrator guid"`, error
   4991). If the category has none configured, that's an Arena
   admin-settings gap outside this skill's write surface — ask a human to
   add one via Arena's UI (Settings -> Change Administrators) before
   submission can proceed at all.
2. A **second** call with `status="SUBMITTED"` and **no**
   `administrator_guids` (Arena rejects the second call if administrators
   are included, error 4995) advances it further. In a workspace with no
   approval routing configured for the category — as is currently the case
   here — this lands on `EFFECTIVE` directly, no separate approval step. A
   workspace with routing configured would instead land on
   `SUBMITTED_FOR_APPROVAL`, requiring an actual approval action. Don't
   assume either outcome — check the returned `lifecycleStatus`/`status`
   after the second call.

**Never call `force_approve_change`/`force_reject_change` from this
skill.** They bypass real approval routing and only work when a change is
already `SUBMITTED_FOR_APPROVAL`; they exist for sandbox testing only, and
an `APPROVED` change auto-advances straight to `EFFECTIVE` in the same
call with no intermediate state to catch a mistake in.

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

## Known limitation: cost changes have no API surface at all

The `costingView` flag being API-blocked (below) is the smaller of two
problems. The bigger one: Arena represents item cost via Quote Line and
Purchase records on Supplier Items (`/supplieritems/<guid>/quotes/<guid>`,
`/supplieritems/<guid>/purchases/<guid>`), and this MCP server has no read
or write tools for either endpoint. Unlike BOM/Sourcing — which this skill
*can* drive directly against the item's working revision (step 7) — there
is no way to make, or even read back, a cost change through this server at
all. Cost changes are entirely a manual Arena UI process today, and
neither this skill nor a future verification script can confirm one
actually happened, only that the user reported one.

**TODO:** if Dilon's process needs this automated later, it requires new
MCP tools for the quotes/purchases endpoints first — this isn't fixable
by changing this skill alone.

### costingView is not API-editable (narrower, separate issue)

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
UI has, and whether `costingView` is actually API-writable on non-document
categories (Assembly/Part) where it hasn't been tested yet. Until either
is resolved, step 7 treats Cost view as a manual UI step for every item
category, not just documents — flag it to the user rather than silently
skipping it or assuming it works elsewhere untested.
