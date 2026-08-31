# `dilon-arena-eco-creator` — requirements notes

Source of truth for current behavior: `skills/dilon-arena-eco-creator/SKILL.md`.
Business process it encodes: SOP-00004 Change Management, per the
`Change Creation Draft.docx` work instruction. Step numbers below refer to
`SKILL.md`'s numbered sections.

## Purpose

Create and populate an ECO / Deviation / Admin Correction in Arena end to
end: create the change record, add affected items, attach documents (new or
revised), and submit for routing — without hardcoding any Dilon-specific
Arena GUIDs into the skill.

## Change types

- **Engineering Change Order** — permanent.
- **Deviation** — temporary, needs an expiration date.
- **Admin Correction** — clerical only, no revision advance.

OPEN QUESTION: the skill asks which of the three this is (step 1) but has
no step that actually captures or sets an expiration date for a Deviation.
Need to check whether Arena has a dedicated field for this and add an
explicit step if so.

## GUID resolution (no hardcoding)

Category, category attributes, lifecycle phases, routings/administrators,
item + working-revision GUIDs, and existing file GUIDs are all resolved
live via MCP calls (step 2) — never hardcoded in the skill. This is a hard
constraint, not just a convenience: it's what lets one skill file work
across different Arena categories/workspaces without editing.

## Screening / change level

Binary screening question -> **Minor** if "No", **Major** + regulatory
review required if any follow-up is "Yes" (step 5).

RESOLVED (2026-08-31): the WI text itself doesn't enumerate the follow-up
questions, but a representative released ECO in the workspace does — it's
the workspace's golden-standard example and spells out the concrete
6-question Yes/No block used for the Major/Minor follow-up:

```
Does this change meet any of the following criteria? (Yes / No)

1. Could reasonably affect device safety or effectiveness
2. Materially affects intended purpose, design, clinical performance, or benefit-risk profile
3. Results in a change to QMS scope
4. Introduces a new intended purpose, patient population, or clinical indication
5. Major design change affecting performance, safety, operating principles, or clinical function
6. Adds a product or process not covered by the current ISO certification
```

This block gets written directly into the change's **Description** field
(see Description format below), not stored as a separate structured
field — Arena has no dedicated fields for these 6 questions. Caveat: this
is confirmed by example, not by the WI's own text, so if a future WI
revision enumerates them explicitly, that becomes the authoritative
source instead.

## Description format (golden-standard, from a representative released ECO)

The skill's step 4 ("what/why/reference") is correct as a summary but
under-specifies the actual structure real ECOs use. The representative ECO
above establishes this shape — reproduce it rather than free-form prose:

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

Each `Released to <phase>:`/`Obsoleted:` line lists the *exact* doc
numbers going to that phase — don't collapse multiple phases into one
list. The 6-question block's answers are plain `YES`/`NO` on the line
directly under each numbered question, not inline.

**Regulatory Review Number field convention**: even when "Regulatory
Review Number Generated?" is `No`, the representative ECO still fills the
free-text "Regulatory Review Number" field with explanatory text (e.g.
`"No regulatory review required."`) rather than leaving it blank. Match
this — don't leave the field empty just because it's not `required: true`.

**Title nuance**: Dilon's actual usage extends step 3's pattern to
include the item's descriptive name, not just its number — e.g. `Update
Manufacturing Documents for 820-00006 Detector Head`, not just `...for
820-00006`. Worth doing for any title built from a subassembly/parent
item number.

## Naming conventions

- **Title**: verb-first (Create/Import/Release/Update/Obsolete) + item/doc
  number + short description (step 3).
- **Description**: what's changing, why, and the reference (step 4).
- **File naming**: file name `[Number] Rev [nn].[ext]`, item name
  descriptive with no type prefix, file title `[Number] [Item Name]`
  without the revision (step 8).

## Required assessment fields

~12 fields, resolved from `list_change_category_attributes` by exact
display name (step 2). Any free-text field with nothing to report gets
"No effect" — never left blank (step 6).

OPEN QUESTION: what happens if a category's attribute set doesn't include
one of the expected fields — e.g., does Admin Correction carry the same
attribute set as ECO/Deviation, or a lighter one? The skill doesn't
currently branch on this.

## Affected items

- `files_view=True` is required on `add_items_to_change` — this is what
  resolves the WI's "yellow dot" warning (step 7).
- Needs the item's **working revision** GUID, not the item GUID itself.

CORRECTION (2026-08-31): step 2 currently says to find the working
revision "in `get_item`'s response alongside the effective revision" —
**this is wrong and needs fixing in `SKILL.md`.** Tested extensively
against both the sandbox and production workspaces: `get_item` never
surfaces a working revision, even when one exists. The correct call is
`get_item_revisions(<any revision guid of the item>)`, which returns the
item's full revision chain; find the entry with `"status": 0`
(`revisionStatus: "WORKING"`) and use *that* entry's `guid` as
`add_items_to_change`'s `new_item_revision_guid`. Every item has this
dormant working-revision entry available, including RELEASED items that
have never been revised since release — it just isn't visible through
`get_item`. See "Lifecycle phase transitions" below for the full recipe
this feeds into.

**Affected Items picklist — full confirmed value list** (workspace-wide
multiselect FIXED_DROP_DOWN, fetched via
`list_change_category_attributes(category_guid, include_possible_values=True)`):
`ASSETs`, `Bill of Materials (BOM)`, `Components / Items`, `Customer
Materials`, `Design Items`, `Engineering Drawing (PCBA, SCH, DWG)`, `Form
(FO)`, `Labels / Artwork (AR)`, `Manual (MA)`, `Material / Purchase
Specification`, `Other Document(s)`, `Parts List`, `Standard Operating
Procedure (SOP)`, `Technical Bulletin`, `Test Plan (TP)`, `Test Report
(TR)`, `Work Instruction (WI)`. No entries exist for FTP or QCP
specifically — `SKILL.md`'s mapping to `Other Document(s)` for those is
correct and is the best available fit, not a placeholder.

## Lifecycle phase transitions (major addition, 2026-08-31)

This is the biggest gap in the current skill — it has no guidance at all
on *which* phase transitions are actually reachable, and the naive
approach (pick the phase by name, use the item's current guid) fails in
several non-obvious ways. All of this was worked out empirically against
a disposable sandbox workspace (see "Sandbox testing practice" below)
before being applied to production.

**Same-named phases can be different objects with different GUIDs.**
Arena scopes lifecycle phases by `stage` (`PRELIMINARY`, `DESIGN`,
`PRODUCTION`, etc.), and a workspace can have two phases with the
identical display name — e.g. this workspace has a "Prototype Release"
phase in `DESIGN` stage *and* a separate "Prototype Release" phase in
`PRODUCTION` stage, different GUIDs. `list_item_lifecycle_phases` returns
both; matching by name alone is ambiguous. Always disambiguate by
`stage`/`type` as well as `name`.

**Not every same-stage transition is supported, and not every
cross-stage transition is blocked.** There's no simple rule
("same-stage = allowed, cross-stage = blocked") — don't build one.
Confirmed by direct testing (`add_items_to_change` returns
`"Lifecycle transition from X to Y is not supported"`, error code 3063,
when a pair isn't configured):
- `Unreleased -> RELEASED` (`PRELIMINARY` -> `PRODUCTION`): **works**.
- `Unreleased -> Obsolete` (`PRELIMINARY` -> `PRODUCTION`): **fails**.
- `Unreleased -> Abandoned` (`PRELIMINARY` -> `DESIGN`): **fails**, even
  though Abandoned is nominally the same stage family Unreleased items
  usually move into.
- `Unreleased -> In Design` (`PRELIMINARY` -> `DESIGN`): **works**.
- `In Design -> Abandoned` (`DESIGN` -> `DESIGN`): **works**.
- `RELEASED -> Prototype Release [DESIGN stage]` (`PRODUCTION` ->
  `DESIGN`): **fails**.
- `RELEASED -> Prototype Release [PRODUCTION stage]` (`PRODUCTION` ->
  `PRODUCTION`): **works**.
- `RELEASED -> RELEASED` with a new revision, i.e. releasing updated
  content (`PRODUCTION` -> same `PRODUCTION` phase): **works**.

Practical implication: don't assume a target phase is reachable from an
item's current phase just because it "sounds like" a valid next step or
matches a stage-compatibility heuristic. If a transition is rejected with
error 3063, the fix is usually routing through an intermediate phase
(see the Obsolete/Abandoned case below), not retrying with different
parameters.

**Obsolete vs. Abandoned — these are not interchangeable, and the WI is
explicit about which applies:** "Obsolete" is for a document that *was*
released and is now retired/superseded. "Abandoned" is for a document
that *never properly released*. Using the wrong one on a never-released
item both fails the API call (per above) and would be a WI compliance
error even if it somehow succeeded. A never-released item being retired
needs a target of Abandoned, and — since `Unreleased -> Abandoned` isn't
directly reachable — needs **two sequential ECOs**: one moving it
`Unreleased -> In Design` (or another reachable `DESIGN`-stage phase),
a second moving it `In Design -> Abandoned`. This can't be collapsed into
one ECO/one `add_items_to_change` call.

**Revision numbering scheme depends on the target phase family, and must
be passed explicitly.** Arena won't infer it correctly on its own for
these phase-change scenarios:
- Moving into a Prototype-Release-type phase: revisions are **lettered**
  (`"A"`, `"B"`, ...).
- Moving into/within a RELEASED-type phase: revisions are **numeric**
  (`"00"`, `"01"`, ...), continuing the item's existing numeric sequence.
- Always pass `new_revision_number` explicitly on `add_items_to_change`
  rather than omitting it and hoping Arena infers the right scheme.

**The general recipe** (supersedes the "Affected items" section's old
guidance above) for adding *any* non-Unreleased item to a change,
regardless of target phase:
1. `get_item_revisions(item_guid)` -> find the `status: 0` (`WORKING`)
   entry -> note its `guid`. (For an item still Unreleased/WORKING that's
   never been touched by any change, the item's own guid already *is*
   its working revision — this lookup is only needed once an item has an
   effective/released revision.)
2. `add_items_to_change(change_guid, items=[{"new_item_revision_guid":
   "<step 1 guid>", "new_lifecycle_phase_guid": "<target, disambiguated
   by stage>", "new_revision_number": "<letter or next numeric, per the
   target phase family>"}])`.

**Confirmed dead end:** the MCP server exposes an experimental
`affected_item_revision_guid` field on `add_items_to_change` (maps to
Arena's `affectedItemRevision` request field) as an attempt to pass the
item's *effective* revision explicitly. Arena rejects it outright:
`"The attribute \"affectedItemRevision\" is not creatable"` — it's a
system-computed, read-only field in Arena's actual data model (visible
only in *responses*, describing the pre-change state). This field should
probably be removed from `add_items_to_change`'s exposed parameters, or
at minimum the docstring should say plainly "do not use this" rather
than "experimental."

## Document preparation from Dilon markdown source (added 2026-08-31)

Step 1's "local paths to the clean docx and pdf" assumes those files
already exist. When the actual source is Dilon-formatted markdown (e.g. a
Nav3-style docs repo under `Documentation/Process/Subassemblies`), a new
step 1a compiles them first:

- Doc type (narrative vs. fillable form) is determined by checking the
  markdown body for `@@@FORM_FIELD@@@` markers, not by doc-number prefix —
  PL (a "Plan") is narrative, RE (a "Report") is a form, both exceptions
  to the naive prefix mapping.
- Narrative -> `dilon-document-compiler`'s `generate_dilon_doc.py`. Form ->
  `dilon-document-form-compiler`'s `generate_dilon_form.py`. Both need
  `check_deps.py` to pass first.
- docx -> pdf has no reliable cross-environment CLI converter; drive Word
  directly via COM automation (PowerShell, `SaveAs` format code `17` =
  `wdFormatPDF`). Confirmed working end-to-end on ECO-000262 (six
  documents compiled and converted in one batch, one shared Word
  instance).

## File attachment

Two distinct flows (step 8):
- **New item/document**: `create_file(storage_method="FILE", edition="1",
  local_path=...)` (single call, creates + uploads content together) +
  `add_existing_file_to_item` + `add_file_to_change` (item association
  alone does not also put the file in the change's Files view — both
  calls are needed).
- **Revision of an existing document**: `create_file_edition` +
  `update_item_file_association`.

Redlines attach to the **change**, not the item — they're traceability
evidence for the change, not part of the controlled item record.

Known/accepted limitation: Arena's UI distinguishes "update through the
ECO's Files view" vs. "update from the file record," but the REST API has
one mechanism (`create_file_edition`) regardless. The skill relies on
`files_view=True` (step 7) to get the functionally equivalent result. This
is documented in `SKILL.md` as an accepted gap, not an open question.

**Fixed 2026-08-31 — `create_file` couldn't actually create a
content-bearing file.** It always JSON-POSTed `storageMethodName: "FILE"`
to `/files`, but Arena's JSON endpoint (`FileCreateVo` schema) only
accepts `FTP`/`WEB`/`PLACE_HOLDER` there — `FILE` requires
multipart/form-data with the content attached in the same request
(`FileCreate` schema, a different endpoint variant of the same URL).
Confirmed against Arena's live OpenAPI spec
(`https://api.arenasolutions.com/v1/v3/api-docs/RestAPIv1`). Fix: added a
`local_path` param; `storage_method="FILE"` now posts multipart to
`/files` with content, everything else posts JSON to `/files/json`
(previously `/files`, also wrong per the same schema split). Default
`storage_method` changed from `"FILE"` to `"PLACE_HOLDER"` since the old
default silently produced a broken call.

Caution for anyone maintaining this server: a sibling, more-generic copy
of this codebase lives at
`C:\Users\bchaloux\Local_Documents\Local_Repos\dilon-claude-arena-skills\arena_mcp\arena_mcp_server.py`
(this file's own path, if you're reading it from there) vs. the actual
Dilon-configured live server at `C:\Users\bchaloux\arena-mcp\arena_mcp_server.py`
(workspace-switching support, Dilon-specific wording). They can drift —
always verify which one `.claude.json`'s `mcpServers.arena.args` actually
points to before editing, and apply fixes to both if they're meant to
stay in sync.

## File metadata: category, author, format (added 2026-08-31)

New step 8a, run after step 8's create/attach calls, for both the docx
and pdf of every new file:

- **Category**: resolved live via `list_file_categories` (never
  hardcoded), matched to the doc type — "Form" for travelers, "Work
  Instructions" for WIs, "Quality Procedure" for QCP/FTP, "Plan" for PL,
  "Report" for RE.
- **Author**: `update_file_summary`'s `author_full_name`. OPEN QUESTION
  resolved ad hoc, not yet a settled convention: whether this should be
  the document's original/front-matter author or the person running the
  compile-and-upload workflow. Ask the user each time until a default is
  agreed.
- **Format**: `update_file_summary`'s `format` (`"DOCX"`/`"PDF"`).
  `list_file_attributes` reports this as a `DROP_DOWN` field type, but
  Arena accepted both values on write directly — no picklist-management
  step was needed, at least for these two common values.

**Fixed 2026-08-31 — `update_file_summary` had no way to set category.**
The tool exposed `title`/`description`/`edition`/`format`/`author_full_name`/
`location` but not `category_guid`, even though `PUT /files/<guid>`
accepts `category: {guid}` per `FileDetailVo` (same shape `create_file`
already used for creation). Added the missing parameter.

## Pre-submit checklist / approvers

Quality + Regulatory approve every ECO/Deviation, at least 2 independent
approvers, creator/owner is never the sole approver (step 9).

OPEN QUESTION: does Admin Correction have lighter approval requirements
than ECO/Deviation? The current checklist doesn't branch by change type.

## Submission

`route_change` is the one hard-to-reverse, visible-to-others step in the
skill. Explicit user confirmation is required before calling it (step 10),
even if every earlier step succeeded cleanly.

**Submission is a two-call sequence, not one.** `route_change(guid,
status="SUBMITTED", administrator_guids=[...])` first moves the change to
`SUBMITTED_FOR_ROUTING`; a **second** call with `status="SUBMITTED"` and
**no** `administrator_guids` (Arena rejects the second call if
administrators are included — error 4995) advances it further. In a
workspace with no approval routing groups configured for the category,
this second call goes straight to `EFFECTIVE` — no separate approval
step. In a workspace with routing configured, expect it to land on
`SUBMITTED_FOR_APPROVAL` instead, requiring an actual approval action
(see below). Don't assume either behavior — check the returned
`lifecycleStatus`/`status` after the second call.

**Submitting requires a valid, pre-existing Change Administrator.**
`route_change`'s `administrator_guids` must reference a user already
configured as a change administrator for that category
(`list_change_administrators(category_guid)`); an arbitrary valid user
GUID is rejected (`"Invalid change administrator guid"`, error 4991). If
the category has none configured yet, that's an Arena admin-settings gap
outside this MCP server's write surface — ask a human to add one via the
Arena UI (Settings -> Change Administrators) before submission can
proceed at all.

**Force-approve, for testing only:** `force_approve_change` /
`force_reject_change` post `status: "APPROVED"` / `"REJECTED"`
respectively (not `"FORCE_APPROVED"`/`"FORCE_REJECTED"` — an earlier
version of this MCP server had that wrong; already fixed in this repo's
copy) to `/changes/statuschanges`, and only work when the change is
already `SUBMITTED_FOR_APPROVAL`. An `APPROVED` change auto-advances
straight to `EFFECTIVE` as part of the same call — Arena doesn't leave it
in an intermediate "approved but not yet effective" state. This bypasses
real approval routing and should only ever be used in the sandbox
workspace, never against production — this skill's step 10 should never
call it.

## Adjacent Arena MCP nuances (not ECO-specific, but hit while building/using this skill)

**Shared multi-prefix number formats.** Many item categories (Traveler,
Work Instructions, FTP, Plan, Report, and others) don't each have their
own dedicated Arena number format — they share one format object (in
this workspace, named "Document") that has a picklist field selecting
the prefix (`FO`, `WI`, `FTP`, `PL`, `RE`, ...). `create_item` needs
`number_format_guid` (the shared format's guid) plus
`number_format_fields: [{"guid": <picklist field guid>, "value": "FO"}]`
— not a simple prefix string. Get both guids via
`list_item_number_formats` / `get_item_number_format`, or by inspecting
an existing item's category via `list_item_categories` (categories that
share a format expose the same `numberFormat.guid`).

**New item categories aren't creatable via this MCP server.** Creating a
brand-new item category (e.g. a new document type like QCP) requires
Arena admin settings (Settings -> Item Categories) — there's no
`create_item_category` tool, and this is intentional per the server's
"explicitly deferred" admin surface. Flag it as a manual prerequisite,
don't try to work around it.

**Reference docs for the real Arena REST API.** No official public docs
site is reachable from this environment. An unofficial but accurate
mirror exists at `github.com/aptenodytes-forsteri/arena-restapi-doc` —
verified against this workspace's actual error codes/messages multiple
times this session (not a PTC/Arena-owned repo, but trustworthy: use
`raw.githubusercontent.com/aptenodytes-forsteri/arena-restapi-doc/main/<path>`
to fetch specific endpoint docs, and note paths contain spaces that need
URL-encoding when hitting the GitHub API directly).

**Sandbox testing practice.** Dilon has a second Arena workspace,
"Dilon Technologies Validation," purpose-built as a disposable sandbox —
same OAuth client credentials work for both, only `ARENA_WORKSPACE_ID`
differs. Before trying an unfamiliar or destructive-sounding write
operation (lifecycle transitions, force-approve, anything that might
create orphaned records) against production, reproduce it in the sandbox
first. This is how every finding in the "Lifecycle phase transitions"
section above was worked out — none of it was guessed against production
data.

## Known gaps / not yet covered

- Deviation expiration date handling (see Change types above).
- Category-specific attribute variation (see Required assessment fields).
- Admin Correction approval rules (see Pre-submit checklist).
- No handling yet for rejection/rework loops after submission, or for
  cancelling a change mid-flow.
- No per-skill acceptance-criteria convention has been defined yet — right
  now `CLAUDE.md`'s Testing section just says "extend the write-tool tier
  with that skill's tools." As more skills are added, this doc should grow
  a convention for what "done" means per skill (which write tools need
  coverage, what the pre-submit checklist should assert, etc.).
- **`SKILL.md` still needs syncing with most of this doc's 2026-08-31
  additions** — written here first per this repo's own convention
  (`README.md`: "when a note here changes a skill's actual behavior,
  update the skill's `SKILL.md` too"). The document-preparation (step 1a)
  and file-metadata (step 8a) additions above, plus the `create_file`/
  `update_file_summary` fixes, are already folded into `SKILL.md`. Still
  outstanding: step 2's working-revision guidance is known wrong (see
  "Affected items" correction above) and needs replacing with the
  `get_item_revisions` recipe; step 7 needs the full "Lifecycle phase
  transitions" section folded in (phase disambiguation by stage, the
  non-transitive reachability table, the Obsolete-vs-Abandoned two-ECO
  case, explicit revision-number-scheme selection); step 4 needs the
  golden-standard description structure; step 10 needs the two-call
  submission sequence and Change Administrator prerequisite.
- Whether `add_items_to_change`'s `affected_item_revision_guid` parameter
  should be removed entirely, now that it's confirmed non-functional
  (Arena: `"affectedItemRevision" is not creatable`) — currently just
  dead weight in the tool's surface.
- Whether the reachable-phase-pairs discovered so far (see "Lifecycle
  phase transitions") are a complete map or just the subset this session
  happened to need — no attempt was made to enumerate *every* pair in the
  workspace's configured workflow. Treat the documented pairs as
  confirmed, everything else as unknown until tested.
