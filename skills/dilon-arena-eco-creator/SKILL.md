---
name: dilon-arena-eco-creator
description: Create and populate an Engineering Change Order (ECO), Deviation, or Admin Correction in Arena, including affected items, file attachment (new documents and revisions), and submission for routing — per Dilon's Change Creation work instruction (SOP-00004). Use when asked to create an ECO, build a change record, or release/revise a controlled document in Arena.
---

# Dilon Arena ECO Creator

Drives the Arena MCP server to build a complete, submission-ready change
record, following `Change Creation Draft.docx` (WI supporting SOP-00004
Change Management). Every GUID is resolved live via MCP calls — never
hardcode a category, phase, or attribute GUID in this skill.

Compiling documents from Dilon markdown source (step 1a) is not this
skill's job — the relevant `dilon-arena-document-standard-<type>` skill
names which compiler skill applies for that document's type; step 1a
defers to it rather than choosing one itself. If that compiler skill isn't
installed, invoking it will prompt for that.

## 1. Gather inputs

Ask the user for:
- The affected item number(s) (or GUIDs, if already known).
- The reason/trigger for the change: a CAPA/complaint/NCMR/audit/ECO
  reference, or the actual driving reason if none apply (e.g. "new product
  development").
- Whether this is an **Engineering Change Order** (permanent), **Deviation**
  (temporary, needs an expiration date), or **Admin Correction** (clerical
  only, no revision advance).
- Local paths to each affected item's expected file formats (typically
  clean docx and pdf — see step 8's Expected file formats deferral for the
  authoritative per-type list), and — if this is a revision of an
  already-released document — the redlined version too. If these don't
  exist yet and the source is Dilon-formatted markdown, see step 1a.

## 1a. Compile documents from Dilon markdown source (if applicable)

Skip this step if the user already has clean files in hand for each of the
item's expected formats.

- Check the relevant `dilon-arena-document-standard-<type>` skill's Usage
  section for that document's type (e.g. `dilon-arena-document-standard-fo`
  for an FO) — it names which compiler skill (`dilon-document-compiler` or
  `dilon-document-form-compiler`) applies for that type. If no
  `dilon-arena-document-standard-<type>` skill exists yet for this
  document's type, invoke `dilon-arena-document-standard-definer` before
  continuing, rather than guessing. Don't assume which compiler applies by
  doc-number prefix — PL (narrative despite being a "Plan") and RE (form
  despite being a "Report") are exceptions to the naive mapping, which is
  exactly why this is the type skill's call, not a rule restated here.
- Before invoking the compiler, check the front matter's `revisions` list:
  the entry matching `current_revision` should have its `eco_date` set to
  today's date, in `MM-DD-YYYY` — update it if it's stale. The date a
  revision is compiled (and then uploaded to Arena on this change) is the
  date that belongs on it, not whatever date was typed in when the
  revision was drafted.
- Invoke whichever compiler skill that section named to produce the docx —
  don't reproduce its internal steps (dependency checks, scripts, exact
  invocation) here; that's those skills' concern and can change
  independently of this one.
- Convert docx -> pdf via `scripts/convert_docx_to_pdf.ps1` (Word COM
  automation — no CLI converter is reliably available cross-environment).
  Pass every docx in the batch as `-InputPaths` in one call; it reuses a
  single Word instance across all of them and verifies each output PDF
  actually exists and is non-empty rather than assuming `SaveAs`
  succeeded.

## 2. Resolve GUIDs live

Every `list_*`/`match by name` lookup below should go through
`scripts/resolve_guid.py` (results list + target name in, one exact
case-insensitive match out, or a loud error listing available names) —
removes the chance of silently accepting a close-but-wrong entry from a
long results list.

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
  - The Affected Items multiselect picklist attribute — for each affected
    item, resolve its picklist value from the relevant
    `dilon-arena-document-standard-<type>` skill's Item connections
    section (e.g. `"Form (FO)"` for FO, `"Test Plan (TP)"` for PL). QCP
    and FTP's values are flagged unconfirmed in their own skills — resolve
    live against `possibleValues` before trusting either one. If the item's
    document type has no `dilon-arena-document-standard-<type>` skill yet,
    invoke `dilon-arena-document-standard-definer` rather than defaulting
    to "Other Document(s)".
  - **Check each attribute's `multiSelect` flag** (`list_change_category_attributes(...,
    include_possible_values=True)`) before deciding the value shape for
    step 6: a `FIXED_DROP_DOWN` attribute with `multiSelect: true` (e.g.
    Affected Items above, or "If \"Yes\", Nationally Recognized Testing
    Laboratory (NRTL) Update::") rejects a bare string from its own
    `possibleValues` list — `{"code": 2026, "message": "The specified
    value \"Other Document(s)\" is not a valid option for multi
    additional attribute..."}` — even though it's a real listed option.
    **Wrap it in a single-element array** (`["Other Document(s)"]`)
    instead. Single-select `FIXED_DROP_DOWN` fields (`multiSelect: false`,
    e.g. "Is Training Required?") take a plain string, no array.
    `scripts/additional_attributes.py` builds step 6's payload from this
    response plus the desired field values, applying this wrapping rule
    automatically instead of it being re-derived by hand each time.
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
- `get_item_files` on each affected item, regardless of whether it's a new
  item or a revision — step 8 decides per expected file format (per the
  relevant `dilon-arena-document-standard-<type>` skill's Expected file
  formats section, typically docx/pdf) whether one is already attached,
  not per item, so this needs checking every time. Note the existing
  file's GUID and item-file association GUID for any format that's
  already attached.

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
- **Never mention losing or recreating the Markdown authoring source** (a
  computer crash, a recovery effort, re-transcribing from an archived
  scan/copy) in the description. That's internal documentation-tooling
  mechanics, not a quality-system event — the released document itself
  wasn't lost, only its editable source, so it doesn't belong in a
  permanent, official QMS record. Confirmed by direct user correction: a
  drafted description that said a document's Markdown source "was lost in
  a data loss event and is being recreated from scanned archive copies"
  was rejected outright, even though it was true — the same change instead
  read purely in terms of the reissue rule and the standard
  business-justification category driving it (here, new product
  development). **This is narrower than "no internal narrative" —** a real
  CAPA/NCMR/complaint/audit-finding reference is exactly what the `Ref:`
  line is for and should be documented there whenever one genuinely
  applies; don't suppress a legitimate quality-record reference by
  over-applying this rule.
- The 6-question block is step 5's screening questions verbatim, each with
  a plain `YES`/`NO` on the line directly under it (not inline) — this is
  where that screening result actually gets recorded; Arena has no
  dedicated structured fields for these 6 questions.
- Even when "Regulatory Review Number Generated?" (step 2) is `No`, still
  fill the free-text "Regulatory Review Number" field with explanatory
  text (e.g. `"No regulatory review required."`) rather than leaving it
  blank.

Run the drafted description through `scripts/lint_description.py` before
step 6 — checks the structure above (Released-to/Obsoleted lines, `Ref:`
line, all 6 questions each followed by a plain YES/NO) and fails loud on
anything missing, rather than a format slip only surfacing after the
change is already live in Arena.

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
`additional_attributes` covering every field resolved in step 2 — built
via `scripts/additional_attributes.py` (step 2), not assembled by hand.
Use "No effect" text for any free-text assessment field with nothing to
report — never leave one blank.

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

Run `scripts/phase_transitions.py` (current/target stage+name in,
`REACHABLE`/`BLOCKED`/`UNKNOWN` out) before every `add_items_to_change`
call instead of eyeballing the list above from memory — an `UNKNOWN`
verdict means test it in sandbox first, not "probably fine."

**Obsolete vs. Abandoned are not interchangeable.** Obsolete is for a
document that *was* released and is now retired/superseded. Abandoned is
for a document that *never* properly released. Since Unreleased ->
Abandoned isn't directly reachable, retiring a never-released item needs
**two sequential ECOs**: one moving it Unreleased -> In Design (or another
reachable `DESIGN`-stage phase), a second moving that to Abandoned. This
can't be collapsed into one ECO.

**What string to pass as `new_revision_number` — including the
Prototype-Release lettered/hyphenated scheme — is the relevant
`dilon-arena-document-standard-<type>` skill's concern, not this skill's.**
See that skill (e.g. `dilon-arena-document-standard-pl` for a PL item) for
the full baseline/prototype/production convention (e.g. `"02-A"`, not a
bare `"A"`), any type-specific exception (PL/RE's reissue-as-new-item
rule), and the current recommendation to always pass `new_revision_number`
explicitly rather than omit it. `scripts/revision_numbers.py` computes
the actual string — `mode: "standard"` (current revision + target phase
family in, next revision string out) for the baseline/prototype/
production scheme every type shares, `mode: "reissue"` (item number +
existing `<root>-*` numbers in, next `<root>-NN` out) for PL/RE's
exception — rather than the numeric/letter arithmetic being redone by
hand each time.

**Do not use `add_items_to_change`'s `affected_item_revision_guid`
parameter.** It's a confirmed dead end — Arena rejects it outright
(`"affectedItemRevision" is not creatable`; it's a system-computed,
response-only field describing pre-change state, not something you can set).

## 8. Attach documents

Item name (this step, for a new item): descriptive only, no type prefix.
File `name`/`title` conventions and the revision-number string are the
relevant `dilon-arena-document-standard-<type>` skill's concern — see that
skill (matched by this file's document type) before naming or renaming a
local copy of the file to upload. If the document type has no matching
skill yet, invoke `dilon-arena-document-standard-definer` first.

**Exception: revising a Test Plan (PL) or Test Report (RE) item.** Before
following the normal per-file sequence below on a PL/RE item, check
`dilon-arena-document-standard-pl`'s or `dilon-arena-document-standard-re`'s
Usage section — once a completed report already exists against the
relevant plan, PL/RE revisions don't bump the item's revision at all; they
create a new item under a `<original number>-<NN>` number instead. That
section's own steps replace this section's for that item, not supplement
it.

**Which formats to expect, and which is primary, is the relevant
`dilon-arena-document-standard-<type>` skill's Expected file formats
section's concern, not this skill's** — check it (matched by this item's
document type) rather than assuming docx+pdf/pdf-primary universally. If
the document type has no matching skill yet, invoke
`dilon-arena-document-standard-definer` first. Everything below refers to
"the primary format" and "the non-primary format(s)" per that section's
designation — typically pdf and docx respectively, but not necessarily.

**Decide per file, not per item.** Don't assume "new item -> all expected
formats are new" or "revision -> all expected formats already exist" —
call `get_item_files(item_guid)` (step 2) and check each of the type's
expected formats independently; it's possible for an existing,
previously-released item to be picking up one of its expected formats for
the first time, or vice versa.

For each of the type's expected formats, in the order that section lists,
follow this exact sequence. **The check in step 1 must happen before
calling either `create_file` or `create_file_edition`, never after** —
creating a new file record for a format that already has one produces an
orphaned duplicate that then has to be unwound (see "Correcting a wrong
create_file call" below; this is not a hypothetical, it happened on
ECO-000262).

`scripts/file_attach_decision.py` makes step 1-2's decision itself —
fresh `get_item_files` output + target format + this item's current
revision status in, one of `CREATE_FILE`/`UPLOAD_CONTENT`/
`BLOCKED_NEEDS_EDITION` out, with the existing file/association GUIDs
already extracted when relevant. Run it instead of re-deriving the
branch by reading the JSON by eye — this exact decision (specifically,
skipping the check and calling `create_file` blind) is what produced the
ECO-000262 orphaned-duplicate-file incident below.

1. **Check**: is a file of this format currently attached to this item?
   Query `get_item_files(item_guid)` **fresh** right before this file's
   sequence — don't reuse step 2's snapshot, since it can go stale the
   moment any content gets replaced for this item earlier in the same run.
2. **If yes (already attached) — decide by the file's own `locked` flag,
   not the item's revision status (the item can be `WORKING` under this
   change while its file is still `locked: true` — the two are
   independent; check the file directly):**
   a. Use that file's current GUID and item-file association GUID from the
      fresh `get_item_files` call in step 1 — it carries the file's
      `locked` flag inline, no separate call needed.
   b. Check `locked` on that file record:
      - **`false`:** replace the file's content in place:
        `upload_file_content(file_guid, local_path=<new local path>)`. No
        edition bump, no new GUID. Use this same path whether it's the
        first time this change has touched the file's content or a later
        correction to what was already uploaded — an unlocked file's
        content can simply be overwritten.

        **Exception, confirmed by direct user correction:** if the
        `unlocked` file is the *dormant* carried-forward edition sitting on
        an item's working revision — last touched by some earlier,
        already-completed change (or never touched by any change at all),
        not something *this* change has already edited — bump a genuine
        new edition instead (`create_file_edition`, same as the `locked`
        branch below), even though the file itself reports `locked:
        false`. This came up revising two items for a real ECO: both
        items' working revisions already carried an unlocked docx+pdf
        pair left over from an earlier, already-released change, and the
        user directed a new edition rather than overwriting that content
        in place. The `locked` flag only tracks whether the file is
        mid-edit *right now* — it says nothing about whether the content
        sitting there belongs to a prior, already-closed change. Use
        `get_file_changes(file_guid)` to check: if it comes back empty or
        only shows already-completed changes, prefer a new edition over an
        in-place overwrite for that file under this change.
      - **`true`:** this needs a genuine new edition:
        `create_file_edition(file_guid, edition=<next edition number>,
        local_path=<new local path>)`. Confirmed working 2026-09-03 — see
        `docs/requirements/dilon-arena-eco-creator/core.md`'s "Fixed for
        real 2026-09-03" section if this ever regresses. This returns a
        **new file GUID** for the new edition; use it (not the old one)
        for step 2c/2d below and for `update_file_summary`.
   c. Regardless of which path above: for the format(s) the type skill
      marks primary, `update_item_file_association(item_guid,
      file_assoc_guid, primary=True)` to confirm it stays primary — a
      carried-forward association can silently lose its primary flag
      across a revision.
   d. Regardless of which path above: `add_file_to_change(change_guid,
      file_guid)`. **Required, not optional**, even when the GUID didn't
      change (content-only replace) — relying on the item's
      `files_view=True` (step 7) alone leaves updated files invisible in
      the change's own Files tab in Arena's Web UI.
   e. If content was replaced via `upload_file_content`, separately call
      `update_file_summary` (step 8a) for any metadata that needs
      refreshing — `upload_file_content` only takes `file_guid`/
      `local_path`, no metadata parameters, so it doesn't touch
      category/author/format on its own.
3. **If no (nothing of this format attached yet):**
   a. `create_file(title="<Number> <Item Name>", storage_method="FILE",
      edition="1", local_path=<local path>)` — a single multipart call that
      creates the file record and uploads its content together. `edition`
      is required; Arena rejects the call without it.
   b. `add_existing_file_to_item(item_guid, file_guid, primary=True for
      whichever format(s) the type skill marks primary, primary=False for
      the rest)`.
   c. `add_file_to_change(change_guid, file_guid)` — item association alone
      doesn't also put it in the change's Files view.

Either way, the redline is traceability evidence for the *change*, not the
controlled item record — attach it with
`add_file_to_change(change_guid, redline_file_guid)`, not to the item.

(Arena's UI enforces updating a file "through the ECO's affected-item Files
view, not from the file record" — a UI-only distinction between which
screen you click "Update Edition" from; the REST API has one mechanism
regardless, `create_file_edition`. This has no bearing on step 2d above —
`add_file_to_change` is needed either way, regardless of which UI screen a
human would have used to produce the same edition.)

## Correcting a wrong `create_file` call

If step 8's check is skipped, or answered wrong — a new `create_file` gets
called for a format that already had an attached edition — don't just
delete the stray file and move on; unwinding it correctly takes a specific
order, and deletion itself may not even be possible:

1. `remove_file_from_item(item_guid, file_assoc_guid)` to detach it from
   the item.
2. `remove_file_from_change(change_guid, file_assoc_guid)` to detach it
   from the change.
3. `delete_file(file_guid)` — attempt it, but don't be surprised if it
   fails: this API credential lacks delete privileges on `/files` entirely
   (`403`, code 3024), even once fully
   unattached. If it fails, the file becomes a harmless orphan — unattached,
   invisible from any item/change/ECO — not a blocker. Tell the user it
   exists and that removing it requires either a human with delete rights
   in Arena's Web UI, or an Arena admin granting this API credential
   delete privileges; don't keep retrying the call or treat it as
   something this skill needs to work around.
4. Redo step 8's "already attached" branch (step 2 above) against the
   *original* file's GUID, not the stray one, with `create_file_edition`.

## Correcting a wrong edition bump

If `create_file_edition` ends up called more than once for the same
item+format (e.g. a retry after a transient error), the file ends up with an
extra, unintended edition. There's no `delete_file_edition` tool (only
whole-file `delete_file`, and per the section above that's usually blocked
by credential permissions anyway), so don't try to remove the stray
edition. Correct forward instead:

1. `get_item_files(item_guid)` fresh to find the file's actual current
   (latest) GUID.
2. `upload_file_content(<current file guid>, local_path=<intended final
   content>)` to make the current edition's content the intended one.
3. Leave the extra edition in that file's edition history — it's a
   harmless, if redundant, audit-trail entry, the same way an orphaned file
   from a wrong `create_file` call is harmless once unattached (above); it
   doesn't affect the item's revision number, the file's `name`/`title`, or
   which edition is "current" going forward.

## 8a. Set file metadata (category, author, format)

Do this after step 8's create/attach calls, for every new file (every one
of the type's expected formats, per its Expected file formats section):

- **Category**: `list_file_categories` -> match by name per the relevant
  `dilon-arena-document-standard-<type>` skill's Item connections section
  (e.g. "Form" for FO, "Work Instructions" for WI, "Manufacturing
  Procedure" for FTP, "Plan" for PL, "Report" for RE — check QCP's own
  skill independently rather than assuming it shares FTP's category) ->
  `update_file_summary(guid,
  category_guid=...)`. Never hardcode the GUID — resolve it live per
  workspace, same as every other GUID in this skill.
- **Author**: `update_file_summary(guid, author_full_name=...)`. Always
  the document's own stated preparer — the author named in the document
  itself (e.g. its front matter/signature block) — never the person
  running this compile-and-upload workflow. Read it from the document
  rather than asking the user.
- **Format**: `update_file_summary(guid, format="DOCX")` /
  `format="PDF")`. `list_file_attributes` reports `format` as a
  `DROP_DOWN` field, but Arena accepts new string values on write with no
  separate picklist-management step required.

## 8b. Item connections

For each affected document item, after step 8's attach and step 8a's
metadata, determine the item-to-item references the relevant
`dilon-arena-document-standard-<type>` skill's Suggested connections
section calls for — one `create_item_reference(from_item_guid=<this
item's guid>, to_item_guid=<target item's guid>)` per target it lists.

- **Get user approval before creating any of them.** List the proposed
  connections (this item -> each target, by item number) and get explicit
  confirmation before calling `create_item_reference` — same pattern as
  step 10's submission confirmation, not a silent background action. A
  target the user declines or corrects doesn't get created; adjust the
  list to what's approved before proceeding. This applies every time step
  8b runs, not just the first time an item is touched.
- **Check before creating.** `get_item_references` is bidirectional —
  querying either item in a link returns it — so before creating a given
  target's link, call `get_item_references` on this item and skip that
  target if the pair is already linked. This avoids a duplicate reference
  record when two documents on each other's connections list (e.g. a WI
  and its Traveler) both run step 8b during the same or a later ECO.
  `scripts/sync_item_connections.py` performs both this check and the
  actual `create_item_reference` calls — each target must carry
  `"approved": true` (set only after the approval step above) or it's
  skipped (`SKIPPED_NOT_APPROVED`) without ever being queried or created,
  so the approval gate can't be bypassed by calling the script directly.
- **Resolving target GUIDs.** If the target item is already one of this
  ECO's own affected items, its GUID is already known from step 2.
  Otherwise resolve it via `search_items` by number; if the number itself
  isn't known (e.g. which WI a QCP/FTP is actually used in, or a plan's
  fixture number), ask the user rather than guessing.
- **Unrecognized document type.** If either this item's or a target's
  document type has no `dilon-arena-document-standard-<type>` skill yet,
  invoke `dilon-arena-document-standard-definer` before continuing rather
  than guessing its connections. This includes emerging types like TF
  (workflow/flow diagrams) — not yet defined in this repo, but Dilon's
  convention is that a TF should reference whatever document(s),
  part(s), subassembly(ies), or fixture(s) it depicts, once a proper
  skill exists for it.
- **Effect.** Like the PL/RE reissue exception's own links, these are
  immediate and unconditional — visible in Arena as soon as they're
  created, not gated on the carrying ECO's approval, and not removed if
  that ECO is later canceled.

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
- Documents attached per the type's expected formats with the correct
  format marked primary (step 8), redline attached for a revision,
  category/author/format populated on each file (step 8a).
  **Exception, confirmed by direct user correction: a Prototype Release
  doesn't need a redline.** Redline-as-traceability-evidence is a
  production-release expectation; for a change whose target lifecycle
  phase is Prototype Release (step 7), skip the redline entirely rather
  than treating its absence as an open gap. Run
  `scripts/verify_documents.py` against every attached document's local
  .docx before telling the user the ECO is ready — it reads the
  compiled document's own header, footer, signature, and revision-history
  content directly (no markdown source needed, since one isn't always
  available). Pass `is_form: true` for each document whose type compiles
  via `dilon-document-form-compiler` (FO, RE — per that type's Expected
  file formats section, already resolved at step 1a) — form documents
  have no signature or revision-history table at all, so the script skips
  those two checks entirely for them and only runs the header/footer
  check:
  - **Blocking**: header Title/Number/Rev and footer doc-number/Rev/ECO
    #/Revision Date each match the actual item name, item number,
    `new_revision_number` (step 7), and this ECO's real number — and the
    item number appears in both the header and footer; the Revision Date
    matches today's date; for narrative documents (`is_form: false`),
    every signer in the signature table is a real reviewer on this ECO
    (`get_change_history`).
  - **Warning only**: for narrative documents, the revision-history
    table's latest DATE doesn't match the document's latest Arena upload
    timestamp, or an ECO reviewer is missing from one document's
    signature table.
  - Does **not** check narrative/body content, or the other cross-checks
    listed as open questions in `script-document-verification.md` — those
    remain unbuilt.
  - **A blocking failure can be overridden with user approval** — this
    check can't cover every document shape (e.g. legacy documents it
    can't parse at all), so it isn't a hard gate the skill enforces
    unconditionally. Show the exact failure(s) reported and don't proceed
    past them silently; the user's explicit approval is what allows
    continuing despite a failure.
- Item connections created per each affected document's Suggested
  connections section (step 8b).
- Training set (step 2's "Is Training Required?" field) and routed if
  required. **Exception, confirmed by direct user correction: a Prototype
  Release doesn't require retraining** — this applies both to the
  change-level "Is Training Required?" attribute and to an individual
  affected item's own per-item retraining flag (surfaced in
  `add_items_to_change`'s response as `retraining`/`retrainingRequired`,
  and editable via the item's "Views To Modify" on the change). Treat
  "No"/"No Retrain" as correct for a Prototype Release target phase,
  not as a gap to flag — retraining is a production-release expectation.
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

`scripts/submit_change.py` drives the sequence below — it refuses to run
at all unless the input JSON includes `"confirmed": true`, which must
only be set after the confirmation step above, not asked for by the
script itself. Prefer it over calling `route_change` by hand: it enforces
the exact call shapes described next and reads back `lifecycleStatus`
after the second call automatically.

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

## Known Limitations

### Reviewers/approvers cannot be added via the API

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
follow the same pattern as `env/environment.example.json` — a checked-in
example plus gitignored real-value files under `environments.local/` or a
sibling directory), this skill should read a recommended reviewer list from
there and present it to the user as a suggestion for step 9, rather than
asking from scratch each time. That settings mechanism doesn't exist yet.

### Cost changes have no API surface at all

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

#### costingView is not API-editable (narrower, separate issue)

Like `filesView` (step 7), an affected item's BOM/Source/Cost views also
need to be flagged `includedInThisChange` for the corresponding changes to
actually take effect on release. `bomView` and `sourcingView` can be set via
`update_change_affected_item`, but Arena's REST API rejects any write to
`costingView` on document-category items (WI/PL/RE/Traveler/FO) with
`{"code": 3032, "message": "The attribute \"costingView\" is not editable."}`
— even though the identical request body works for the other views, and
even though the same checkbox can be set with no error through Arena's web
UI.

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
