# Sandbox test checklist — `dilon-arena-eco-creator` (mixed affected-item scenario)

Grades a live subagent run of `dilon-arena-eco-creator` against the
"Dilon Technologies Validation" sandbox workspace (`ARENA_WORKSPACE_ID`
`901596215`). Not a mocked/scripted trace — no mocks exist yet for this
skill.

## Scenario — confirmed against real sandbox state (2026-09-02)

One Engineering Change Order with **four** affected items, deliberately
spanning FTP/WI/PL/RE to exercise every distinct path in `SKILL.md` step 8
plus the PL/RE reissue-as-new-item exception:

| Item | Number | Sandbox GUID | Current state |
|------|--------|--------------|----------------|
| A | `FTP-00001` | `L3N6BYPWCK3BU701NQFV` | Unreleased, `WORKING`, never touched by any change |
| B | `WI-00077` | `HZJ27ULS8GZ7Q3WXJPTO` | `RELEASED`, rev `00` |
| C | `PL-00004` | `2K4NSF6DT1KSBOHI4FHM` | `RELEASED`, rev `00` |
| D | `RE-00019` | `R9TCH4V2IQ9H0D67TX1T` | `RELEASED`, rev `00`, tests `PL-00004` |

**Deliberately blind, grader-only note — do not surface this to the
subagent under test:** items C and D are chosen specifically because
`get_item_references` on both returns `count: 0` in sandbox (confirmed
2026-09-02) — no reissue has happened there yet, and no plan/report link
is recorded. `dilon-arena-document-standard-pl`/`-re` document a reissue-
as-new-item exception that should apply once a completed report exists
against a plan (which is true here — see the "Blind task brief" section
below for what the subagent is actually told). The point of this run is
to see whether the subagent discovers and correctly executes that
exception on its own, by actually reading those two skills during step 8,
rather than being told about it in advance. Section "8-PL"/"8-RE" below
is the answer key for grading afterward, not instructions to hand the
subagent.

## Blind task brief — give the subagent this, and only this, for items C/D

Don't mention "reissue," "new item," or the PL/RE exception. Neutral
framing, same as you'd give any real request:

> Also update `PL-00004` (the Detector Head qualification plan) and
> `RE-00019` (its qualification report) as part of this ECO — content is
> at `Markdown_Source\pl-00004-01-....md` and
> `Markdown_Source\re-00019-01-....md` respectively. Handle each per the
> relevant document-standard skill for its type.

If the subagent asks whether a completed report already exists against
`PL-00004`, or which plan `RE-00019` tests, answer truthfully (yes;
`PL-00004`) — that's the skill's own documented step working correctly,
not a hint. Only intervene if it doesn't ask and simply proceeds as if
this were a normal revision.

Local file sources (all under
`C:\Users\bchaloux\Local_Documents\Local_Repos\Nav3\Documentation\Process\Subassemblies\Detector_Head_820_00006`):
- Item A: `Archive\FTP-00001 NAV 3 Detector Head Assembly Functional Test Procedure Rev00.docx`,
  or compile fresh from `Markdown_Source\ftp-00001-nav-3-detector-head-assembly-functional-test-procedure.md`
  (step 1a; FTP is narrative -> `dilon-document-compiler`).
- Item B: `Archive\WI-00077 N3 Detector Head Assembly.docx`, or compile from
  `Markdown_Source\wi-00077-nav-3-detector-head-assembly-instructions.md`
  (WI is narrative -> `dilon-document-compiler`).
- Item C's new `PL-00004-01`: compile from
  `Markdown_Source\pl-00004-01-nav-3-detector-head-assembly-and-alignment-fixture-qualification-plan.md`
  (PL is narrative despite the name -> `dilon-document-compiler`). A
  production reference copy already exists at `PL-00004-01 Rev 00.pdf` in
  the folder root — **do not treat this as sandbox ground truth**, it's
  from a prior *production* reissue; useful only as a sanity comparison
  for content, not for GUIDs/sandbox state.
- Item D's new `RE-00019-01`: compile from
  `Markdown_Source\re-00019-01-nav-3-detector-head-assembly-and-alignment-fixture-qualification-report.md`
  (RE is a form despite the name -> `dilon-document-form-compiler`).
  Reference copy: `RE-00019-01 Rev 00.pdf` (production, same caveat as
  above).
- No redline provided in this scenario — mark redline-attach checks N/A
  rather than fail.

The fact that production already went through this exact PL-00004 ->
PL-00004-01 / RE-00019 -> RE-00019-01 reissue (markdown source and
reference PDFs already exist for both) makes this a strong parity check:
does the skill reproduce the same shape of result in sandbox that already
happened for real in production?

## How to grade

Watch the subagent's tool calls (not just its final claim) and check off
each item against what actually got called/returned. A "fail" on any
`MUST` item is a skill bug — file it back against `SKILL.md`. A `SHOULD`
item failing may be a legitimate gap already tracked in `core.md`'s Known
gaps — check there before treating it as new.

## 1–1a. Inputs / document compile

- [ ] Asked for affected items, change reason, and ECO/Deviation/Admin
      Correction before proceeding (MUST). Use **Engineering Change
      Order** for this run.
- [ ] For each item compiled from markdown (step 1a): correctly deferred
      to the matching `dilon-arena-document-standard-<type>` skill to pick
      `dilon-document-compiler` (FTP, WI, PL) vs.
      `dilon-document-form-compiler` (RE) — not guessed from the doc-number
      prefix, given RE is explicitly the form-despite-the-name exception
      (MUST).

## 2. GUID resolution

- [ ] `list_change_categories` called; category matched by name to
      "Engineering Change Order," not hardcoded (MUST).
- [ ] `list_change_category_attributes(category_guid, include_possible_values=True)`
      called and inspected for `multiSelect` before step 6 (MUST).
- [ ] Affected Items picklist values resolved per item: `["Form (FO)"]`
      N/A this run; `["Work Instruction (WI)"]` for Item B, `["Test Plan
      (TP)"]` for Item C's new item, `["Test Report (TR)"]` for Item D's
      new item — each wrapped in a single-element array (MUST).
- [ ] For Item A (FTP): does **not** trust `"Other Document(s)"` blindly —
      checks `possibleValues` live and/or asks the user, per FTP's Known
      gaps (MUST, this is FTP's documented unconfirmed case).
- [ ] `list_item_lifecycle_phases` called; target phase for every item
      matched by **both** name and `stage` (MUST).
- [ ] `list_change_administrators` called and a valid admin GUID resolved
      before step 10 (SHOULD).
- [ ] Item A: item's own GUID (`L3N6BYPWCK3BU701NQFV`) used directly as
      its working revision — no `get_item_revisions` detour attempted, or
      if attempted, correctly recognized as unnecessary (SHOULD).
- [ ] Items B/C/D: `get_item_revisions` called for each; the `status: 0` /
      `WORKING` entry's `guid` used as `new_item_revision_guid` — not the
      item's top-level GUID (MUST).
- [ ] `get_item_files` called fresh for each item before step 8 decisions
      (MUST).

## 3–4. Title / description

- [ ] Title is verb-first + item number(s) **and descriptive name** + what
      changed (MUST).
- [ ] Description reproduces the golden-standard structure: opening
      sentence, `Released to <phase>:` / `Released:` / `Obsoleted:` lines
      with exact doc numbers per phase, `Ref:` line, then the 6-question
      Yes/No block, each answer on its own line (MUST).
- [ ] "Regulatory Review Number" free-text field filled even if "...
      Generated?" is No (MUST).

## 5. Screening

- [ ] Gating question asked before the 6 follow-ups (MUST).
- [ ] Change level set consistently with the answers (MUST).

## 6. Create the change

- [ ] `create_change` includes every field step 2 resolved (MUST).
- [ ] Blank-eligible free-text fields get "No effect" text (MUST).
- [ ] Multi-select fields as arrays, single-select as plain strings (MUST).

## 7. Add affected items

- [ ] `add_items_to_change` called once per item (four calls) with the
      correct working-revision GUID per item (MUST).
- [ ] `specs_view=True` on all four (MUST).
- [ ] `files_view=True` on all four — every item has a file change here
      (MUST).
- [ ] `bom_view`/`sourcing_view` left `False` for all four (SHOULD — none
      of these items have BOM/sourcing changes in this scenario).
- [ ] `new_revision_number` passed explicitly for every item, matching the
      revision scheme for its target phase (MUST).
- [ ] `affected_item_revision_guid` never used (MUST).
- [ ] Items C and D end up added via `add_items_to_change`'s **new-item**
      path (computed `PL-00004-01`/`RE-00019-01` numbers), not as a
      revision of the original `PL-00004`/`RE-00019` GUIDs (MUST — grading
      criterion only; not something the subagent was told in advance).

## 8. Attach documents — Item A (FTP-00001, never released)

- [ ] "If no" branch followed: `create_file(storage_method="FILE",
      edition="1", local_path=...)` per format, not `create_file_edition`
      (MUST).
- [ ] File `name` is `FTP-00001 Rev <rev>.<ext>`; `title` is `<Item
      Number> <Item Name>`, no revision in title (MUST).
- [ ] `add_existing_file_to_item` + `add_file_to_change` both called per
      format (MUST).

## 8. Attach documents — Item B (WI-00077, RELEASED)

- [ ] `get_item_files` (fresh) checked before deciding the branch (MUST).
- [ ] Correctly identifies the revision is `RELEASED` (not yet `WORKING`
      under this change) and takes the `create_file_edition` path, not
      `upload_file_content` (MUST).
- [ ] Since `create_file_edition` is a confirmed Known limitation: stops
      and reports the blocker rather than guessing a workaround (MUST —
      **expected to block; a clear report of the blocker is a pass**).

## 8-PL. Item C (PL-00004) — answer key, not shown to the subagent

**First, before checking any of these:** did the subagent, unprompted,
recognize that `PL-00004` needed something other than a plain revision
bump — by actually consulting `dilon-arena-document-standard-pl` during
step 8, not because it was told? If it just bumped the revision and
never opened that skill's Usage section, that's the finding — record it
and stop grading the rest of this section as a straightforward fail
rather than checking off the sub-steps below.

If it did engage with the exception:
- [ ] Step 1 (does the exception apply?): calls `get_item_references` on
      `PL-00004`'s guid, gets an empty result, and — because this is the
      documented first-time case — **asks the user** whether a completed
      report already exists, rather than concluding "no exception" from
      the empty query (MUST). Tester answers: yes, `RE-00019` is a
      completed/RELEASED report against this plan.
- [ ] Step 2 (compute new number): roots to `PL-00004` (no existing
      suffix), calls `search_items(number="PL-00004-*")`, finds no
      existing suffix in sandbox, computes `NN = "01"` -> `PL-00004-01`
      (MUST).
- [ ] Step 3 (create item): uses Arena's "Basic Item Number" format (not
      the shared "Document" format), category stays "Plan," resolves any
      `required: true` Plan-category attributes live rather than assuming
      a fixed list (MUST).
- [ ] New item added to the change via the **new-item** path (no prior
      working-revision GUID) (MUST — cross-check with step 7 above).
- [ ] docx/pdf attached following step 8's "new item" branch, using this
      skill's own Naming/Revision conventions for the new item, starting
      fresh (e.g. rev `"00"`), independent of the `-01` item-number suffix
      (MUST).
- [ ] Step 4 (traceability link): `create_item_reference(from_item_guid=
      <PL-00004-01's new guid>, to_item_guid=<PL-00004's guid>)` created
      (MUST).

## 8-RE. Item D (RE-00019) — answer key, not shown to the subagent

**First, same check as Item C:** did the subagent independently recognize
`RE-00019` needed more than a plain revision bump, by consulting
`dilon-arena-document-standard-re`'s Usage section on its own? If not,
record that as the finding and treat the rest of this section as a fail
rather than a partial pass.

If it did engage with the exception:
- [ ] Step 1 (which plan does this report test?): calls
      `get_item_references` on `RE-00019`'s guid, gets an empty result,
      and asks the user which plan this report tests rather than guessing
      from the item name (MUST). Tester answers: `PL-00004`.
- [ ] Then checks whether a completed report already exists for that plan
      — same mechanism as Item C's step 1, reusing the same
      already-obtained answer rather than asking twice for the same fact
      (SHOULD).
- [ ] Step 2: roots to `RE-00019`, computes `RE-00019-01` (independent
      suffix counter from PL's) (MUST).
- [ ] Step 3: same mechanism as PL's step 3, category "Report" (MUST).
- [ ] Step 4 (two links, not one): `create_item_reference(from_item_guid=
      <RE-00019-01's new guid>, to_item_guid=<RE-00019's guid>)` **and**
      `create_item_reference(from_item_guid=<RE-00019-01's new guid>,
      to_item_guid=<PL-00004's guid>)` — the second re-establishes the
      report-tests-plan link on the new report item (MUST — a single link
      is an incomplete implementation of this step).

## 8b. Item connections (all four items)

- [ ] Before any `create_item_reference` call, the subagent lists the
      proposed connections (this item -> each target, by item number) and
      gets explicit user confirmation — not created silently in the
      background (MUST, per SKILL.md step 8b's approval gate).
- [ ] Only targets the user actually approved get created. If you decline
      or correct one target during the run, confirm it does **not** end
      up as a `create_item_reference` call, and any others you approved
      still do (MUST).
- [ ] `get_item_references` checked fresh before each approved target's
      create call, skipping any pair already linked — verify by
      requesting one connection you know is already covered by another
      item's own step 8b run earlier in this same ECO (e.g. Item B's link
      to Item A, if Item A's step 8b already created the reverse) and
      confirming no duplicate reference record results (MUST).
- [ ] Item A (FTP) -> WI(s) it's used in + Traveler with the pieces it
      fills; Item B (WI) -> Traveler, part/subassembly, PL, RE, FTP(s),
      QCP(s) used; Item C's new PL-00004-01 -> WI, thing qualified; Item
      D's new RE-00019-01 -> only the PL it tests (SHOULD — exact targets
      depend on what you approve during the run, per the point above).

## 8a. File metadata (all four items)

- [ ] Category resolved live and matched: "Quality Procedure" (Item A,
      shared with QCP), "Work Instructions" (Item B), "Plan" (Item C),
      "Report" (Item D) (MUST, never hardcoded).
- [ ] Author read from each document's own stated preparer (front
      matter/signature block), not asked of the user and not defaulted to
      whoever is running the workflow (MUST).
- [ ] Format set per file (SHOULD).

## 9. Pre-submit checklist

- [ ] Restated to the user with explicit confirmation per item (MUST).
- [ ] Item B's blocked file update flagged as an open item, not silently
      dropped (MUST).
- [ ] Reviewer requirements (Quality, Regulatory, 2 independent approvers,
      creator not sole approver) stated as manual Arena UI steps (MUST).
- [ ] Cost view not raised — N/A for this scenario (SHOULD).

## 10. Submit / route

- [ ] Explicit user confirmation obtained before the first `route_change`
      call (MUST).
- [ ] Two-call sequence: first with `administrator_guids`, second without
      (MUST).
- [ ] `force_approve_change`/`force_reject_change` never called (MUST).
- [ ] Final `lifecycleStatus`/`status` from the second call read and
      reported, not assumed (MUST).

## Cross-cutting

- [ ] No Arena category/phase/attribute/file-category/number-format GUID
      hardcoded anywhere in the transcript (MUST).
- [ ] Every deferral to the matching `dilon-arena-document-standard-<type>`
      skill actually happened for all four items (MUST).
- [ ] Any Arena error surfaced (3063, 4991, 2026, 4074, etc.) reported
      with its actual code/message, not swallowed (SHOULD).
- [ ] Environment stayed on `sandbox` for the entire run — no accidental
      `switch_environment("production")` mid-run (MUST).

## Outcome log (fill in after the run)

| Item | Result | Notes |
|------|--------|-------|
| A — FTP-00001 (new-path) | | |
| B — WI-00077 (revision, RELEASED-file blocker) | | |
| C — PL-00004 -> PL-00004-01 (reissue) | | |
| D — RE-00019 -> RE-00019-01 (reissue) | | |
| 8b — Item connections (approval gate) | | |
| Submission (step 10) | | |
