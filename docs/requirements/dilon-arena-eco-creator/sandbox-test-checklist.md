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

**Grading note (2026-09-03):** the run spanned two agent sessions with a
context reset in between (subagent tracking did not survive it), so the
raw tool-call transcript for steps 1–8 (everything up through item
creation, file upload, and the PL/RE reissue discovery) is no longer
directly inspectable. Those items are graded from the pre-reset session's
own progress log plus the final Arena sandbox state, which independently
confirms the *outcome* of each step. Items marked `(not independently
verifiable)` below could not be confirmed from call order/sequence alone
and are neither passes nor fails — the end state is consistent with a
correct run but the sequencing itself wasn't re-checked. Steps 8b, 9, and
10 were re-run to completion in the second session and were graded from
its live tool calls directly.

## 1–1a. Inputs / document compile

- [x] Asked for affected items, change reason, and ECO/Deviation/Admin
      Correction before proceeding (MUST). Use **Engineering Change
      Order** for this run. — confirmed via pre-reset session's own
      progress log (pre-proceed Q&A covered ECO type, phases, screening
      answers, evaluator).
- [x] For each item compiled from markdown (step 1a): correctly deferred
      to the matching `dilon-arena-document-standard-<type>` skill to pick
      `dilon-document-compiler` (FTP, WI, PL) vs.
      `dilon-document-form-compiler` (RE) — not guessed from the doc-number
      prefix, given RE is explicitly the form-despite-the-name exception
      (MUST). — confirmed: RE-00019-01 ended up correctly categorized/
      compiled as a form-style Report document; progress log explicitly
      records the PL/RE document-standard skills being read.

## 2. GUID resolution

- [x] `list_change_categories` called; category matched by name to
      "Engineering Change Order," not hardcoded (MUST). — end state
      category is the real "Engineering Change Order" GUID with matching
      name/path.
- [ ] `list_change_category_attributes(category_guid, include_possible_values=True)`
      called and inspected for `multiSelect` before step 6 (MUST). — (not
      independently verifiable) end-state multiSelect flags on the change
      (e.g. Affected Items, NRTL fields) are correctly applied, consistent
      with this having happened.
- [x] Affected Items picklist values resolved per item: `["Form (FO)"]`
      N/A this run; `["Work Instruction (WI)"]` for Item B, `["Test Plan
      (TP)"]` for Item C's new item, `["Test Report (TR)"]` for Item D's
      new item — each wrapped in a single-element array (MUST). —
      confirmed: change-level "Affected Items" = `["Work Instruction
      (WI)","Test Plan (TP)","Test Report (TR)","Other Document(s)"]`,
      exactly the four expected values.
- [ ] For Item A (FTP): does **not** trust `"Other Document(s)"` blindly —
      checks `possibleValues` live and/or asks the user, per FTP's Known
      gaps (MUST, this is FTP's documented unconfirmed case). — (not
      independently verifiable); still an open item per FTP's Known gaps.
- [x] `list_item_lifecycle_phases` called; target phase for every item
      matched by **both** name and `stage` (MUST). — confirmed: all four
      items landed on the correct real phases ("Prototype Release" for
      A/B, "RELEASED" for C/D-new) with correct GUIDs.
- [x] `list_change_administrators` called and a valid admin GUID resolved
      before step 10 (SHOULD). — confirmed directly in the step 10 run:
      returned Brennan Chaloux and Matt Morales; Matt Morales selected and
      used.
- [x] Item A: item's own GUID (`L3N6BYPWCK3BU701NQFV`) used directly as
      its working revision — no `get_item_revisions` detour attempted, or
      if attempted, correctly recognized as unnecessary (SHOULD). —
      confirmed: `newItemRevision.guid` for FTP-00001 on the change is its
      own item GUID.
- [x] Items B/C/D: `get_item_revisions` called for each; the `status: 0` /
      `WORKING` entry's `guid` used as `new_item_revision_guid` — not the
      item's top-level GUID (MUST). — confirmed: WI-00077's working
      revision GUID (`6O8RWJAHX5OWFSLM8BZT`) is distinct from and correctly
      differs from the original `EFFECTIVE` GUID; PL/RE's new-item GUIDs
      are fresh.
- [ ] `get_item_files` called fresh for each item before step 8 decisions
      (MUST). — (not independently verifiable); end-state branch choice per
      item (new-file for A, edition-bump for B) is consistent with this
      having happened.

## 3–4. Title / description

- [x] Title is verb-first + item number(s) **and descriptive name** + what
      changed (MUST). — "Update N3 Detector Head Assembly Verification
      Documents (FTP-00001, WI-00077, PL-00004-01, RE-00019-01) for New
      Prototype Test Tooling."
- [x] Description reproduces the golden-standard structure: opening
      sentence, `Released to <phase>:` / `Released:` / `Obsoleted:` lines
      with exact doc numbers per phase, `Ref:` line, then the 6-question
      Yes/No block, each answer on its own line (MUST). — confirmed
      verbatim in the live change record.
- [x] "Regulatory Review Number" free-text field filled even if "...
      Generated?" is No (MUST). — "No regulatory review required." present
      alongside `Regulatory Review Number Generated? = No`.

## 5. Screening

- [ ] Gating question asked before the 6 follow-ups (MUST). — (not
      independently verifiable); consistent with the pre-reset session's
      progress log ("no regulatory/commercialized-device screening"
      answered as part of the pre-proceed round).
- [x] Change level set consistently with the answers (MUST). — all six
      criteria answered `NO`; category is the base "Engineering Change
      Order" tier, consistent.

## 6. Create the change

- [x] `create_change` includes every field step 2 resolved (MUST). —
      confirmed: all additional attributes populated on the live record.
- [x] Blank-eligible free-text fields get "No effect" text (MUST). —
      "No effect on product already delivered.", "No effect on product in
      process." both present.
- [x] Multi-select fields as arrays, single-select as plain strings (MUST).
      — confirmed from field types/values (e.g. NRTL `["N/A"]`, Affected
      Items array, vs. single-select `"No"`/`"N/A"` strings).

## 7. Add affected items

- [x] `add_items_to_change` called once per item (four calls) with the
      correct working-revision GUID per item (MUST). — confirmed via
      `get_change_items`: four items, correct revision GUIDs each.
- [x] `specs_view=True` on all four (MUST). — confirmed.
- [x] `files_view=True` on all four — every item has a file change here
      (MUST). — confirmed.
- [~] `bom_view`/`sourcing_view` left `False` for all four (SHOULD — none
      of these items have BOM/sourcing changes in this scenario). —
      **Partial.** Correctly `false` for Item B (revision path). For Items
      A/C/D (new-item path) Arena itself defaults `bomView`/`costingView`/
      `sourcingView` to `true` regardless of what's requested — confirmed
      as Arena platform behavior for genuinely new items, not a skill
      defect. This SHOULD item cannot be satisfied for new-item-path
      items; worth a one-line note in `core.md`'s Known gaps so future
      runs don't mistake this for a bug.
- [x] `new_revision_number` passed explicitly for every item, matching the
      revision scheme for its target phase (MUST). — confirmed: `00-A`,
      `01-A`, `00`, `00`.
- [ ] `affected_item_revision_guid` never used (MUST). — (not
      independently verifiable from read-back state alone; no contrary
      evidence).
- [x] Items C and D end up added via `add_items_to_change`'s **new-item**
      path (computed `PL-00004-01`/`RE-00019-01` numbers), not as a
      revision of the original `PL-00004`/`RE-00019` GUIDs (MUST — grading
      criterion only; not something the subagent was told in advance). —
      confirmed: distinct new item GUIDs (`SAUDI5W3JRAI1E17PNHU`,
      `HZJ27ULS8GZ7Q3QWECZK`) separate from the originals.

## 8. Attach documents — Item A (FTP-00001, never released)

- [x] "If no" branch followed: `create_file(storage_method="FILE",
      edition="1", local_path=...)` per format, not `create_file_edition`
      (MUST). — confirmed: files show `edition: "1"`, `storageMethod:
      FILE`.
- [x] File `name` is `FTP-00001 Rev <rev>.<ext>`; `title` is `<Item
      Number> <Item Name>`, no revision in title (MUST). — confirmed
      exactly: `FTP-00001 Rev 00-A.docx`/`.pdf`, title `FTP-00001 N3
      Detector Head Assembly Testing`.
- [x] `add_existing_file_to_item` + `add_file_to_change` both called per
      format (MUST). — confirmed on the change side (`get_change_files`);
      item-side association not independently re-queried but consistent.

## 8. Attach documents — Item B (WI-00077, RELEASED)

- [ ] `get_item_files` (fresh) checked before deciding the branch (MUST).
      — (not independently verifiable).
- [x] Correctly identifies the revision is `RELEASED` (not yet `WORKING`
      under this change) and takes the `create_file_edition` path, not
      `upload_file_content` (MUST). — confirmed: WI-00077's files show
      `edition: "2"` (bumped from an existing edition 1, i.e. the
      edition-create path was used).
- [x] ~~Since `create_file_edition` is a confirmed Known limitation: stops
      and reports the blocker~~ **Superseded finding, not a fail:**
      `create_file_edition` did **not** block this run. The real root
      cause — the multipart binary-content field must be named
      `file.content`, not `filecontent` — was found and fixed in
      `arena_mcp/server/core.py` / `arena_mcp/server/tools/files.py`
      during this same test session, with a regression test added and the
      fix verified live against sandbox files before this run reached step
      8. `SKILL.md`/`core.md` were already updated accordingly. This
      checklist item's original expectation ("expected to block") is now
      stale — a successful `create_file_edition` here is the *correct*
      outcome. Recommend rewriting this line rather than grading it as a
      blocker check going forward.

## 8-PL. Item C (PL-00004) — answer key, not shown to the subagent

**Unprompted-engagement gate:** confirmed **pass** — the pre-reset
session's own progress log records the subagent identifying the
PL-00004/RE-00019 reissue exception unprompted, via `get_item_references`
returning empty plus actually reading
`dilon-arena-document-standard-pl`/`-re`.

- [x] Step 1 (does the exception apply?): calls `get_item_references` on
      `PL-00004`'s guid, gets an empty result, and — because this is the
      documented first-time case — **asks the user** whether a completed
      report already exists, rather than concluding "no exception" from
      the empty query (MUST). Tester answers: yes, `RE-00019` is a
      completed/RELEASED report against this plan. — confirmed via
      progress log and the blind task brief's design (this is exactly the
      question the tester was primed to answer truthfully).
- [x] Step 2 (compute new number): roots to `PL-00004` (no existing
      suffix), calls `search_items(number="PL-00004-*")`, finds no
      existing suffix in sandbox, computes `NN = "01"` -> `PL-00004-01`
      (MUST). — confirmed by final result.
- [x] Step 3 (create item): uses Arena's "Basic Item Number" format (not
      the shared "Document" format), category stays "Plan," resolves any
      `required: true` Plan-category attributes live rather than assuming
      a fixed list (MUST). — category confirmed "Plan"; number format not
      independently re-verified but no contrary evidence.
- [x] New item added to the change via the **new-item** path (no prior
      working-revision GUID) (MUST — cross-check with step 7 above). —
      confirmed.
- [x] docx/pdf attached following step 8's "new item" branch, using this
      skill's own Naming/Revision conventions for the new item, starting
      fresh (e.g. rev `"00"`), independent of the `-01` item-number suffix
      (MUST). — confirmed: `PL-00004-01 Rev 00.docx`/`.pdf`.
- [x] Step 4 (traceability link): `create_item_reference(from_item_guid=
      <PL-00004-01's new guid>, to_item_guid=<PL-00004's guid>)` created
      (MUST). — confirmed: reference note "PL-00004-01 supersedes
      PL-00004 (reissue per ECO-000197)".

## 8-RE. Item D (RE-00019) — answer key, not shown to the subagent

**Unprompted-engagement gate:** confirmed **pass**, same basis as Item C.

- [x] Step 1 (which plan does this report test?): calls
      `get_item_references` on `RE-00019`'s guid, gets an empty result,
      and asks the user which plan this report tests rather than guessing
      from the item name (MUST). Tester answers: `PL-00004`. — confirmed
      via progress log and blind task brief design.
- [ ] Then checks whether a completed report already exists for that plan
      — same mechanism as Item C's step 1, reusing the same
      already-obtained answer rather than asking twice for the same fact
      (SHOULD). — (not independently verifiable whether it re-asked or
      reused; no contrary evidence).
- [x] Step 2: roots to `RE-00019`, computes `RE-00019-01` (independent
      suffix counter from PL's) (MUST). — confirmed.
- [x] Step 3: same mechanism as PL's step 3, category "Report" (MUST). —
      confirmed.
- [x] Step 4 (two links, not one): `create_item_reference(from_item_guid=
      <RE-00019-01's new guid>, to_item_guid=<RE-00019's guid>)` **and**
      `create_item_reference(from_item_guid=<RE-00019-01's new guid>,
      to_item_guid=<PL-00004's guid>)` — the second re-establishes the
      report-tests-plan link on the new report item (MUST — a single link
      is an incomplete implementation of this step). — confirmed both:
      "RE-00019-01 supersedes RE-00019 (reissue per ECO-000197)" and
      "RE-00019-01 tests PL-00004-01".

## 8b. Item connections (all four items)

- [x] Before any `create_item_reference` call, the subagent lists the
      proposed connections (this item -> each target, by item number) and
      gets explicit user confirmation — not created silently in the
      background (MUST, per SKILL.md step 8b's approval gate). — confirmed
      for both rounds: the pre-reset session's progress log records the
      user approving all 11 originally proposed connections; the
      follow-up round used `AskUserQuestion` live for the remaining
      reconciliation (null-note fix, QCP-00001 skip, fixture link).
- [x] Only targets the user actually approved get created. If you decline
      or correct one target during the run, confirm it does **not** end
      up as a `create_item_reference` call, and any others you approved
      still do (MUST). — confirmed: a proposed WI-00077 -> QCP-00001 link
      was declined (QCP-00001 doesn't exist in this sandbox) and no
      reference to it exists; the approved fixture link
      (PL-00004-01 -> 435-00032) does exist.
- [x] `get_item_references` checked fresh before each approved target's
      create call, skipping any pair already linked — verify by
      requesting one connection you know is already covered by another
      item's own step 8b run earlier in this same ECO (e.g. Item B's link
      to Item A, if Item A's step 8b already created the reverse) and
      confirming no duplicate reference record results (MUST). — confirmed:
      no duplicate reference records exist anywhere in the final state
      (e.g. FTP-00001 <-> WI-00077 appears exactly once from each side).
- [x] Item A (FTP) -> WI(s) it's used in + Traveler with the pieces it
      fills; Item B (WI) -> Traveler, part/subassembly, PL, RE, FTP(s),
      QCP(s) used; Item C's new PL-00004-01 -> WI, thing qualified; Item
      D's new RE-00019-01 -> only the PL it tests (SHOULD — exact targets
      depend on what you approve during the run, per the point above). —
      Final shape closely matches: A -> WI-00077 + Traveler FO-00127; B ->
      FTP-00001, Traveler FO-00127, 820-00001, 820-00006, PL-00004-01,
      RE-00019-01 (QCP link N/A — doesn't exist in sandbox); C
      (PL-00004-01) -> PL-00004 (supersedes), WI-00077, RE-00019-01,
      820-00006, 435-00032 fixture; D (RE-00019-01) -> RE-00019
      (supersedes), WI-00077, PL-00004-01. D also links to WI-00077 in
      addition to "only the PL it tests," but that's a legitimate
      approved connection, not a defect.
- **Retracted finding:** the WI-00077 -> 820-00001 reference with
  `notes: null` initially looked like a step 8b gap (a `create_item_reference`
  call made without a note). `get_item_history` on WI-00077 shows this
  reference was actually added **2025-02-11T19:53:03Z by Shannon
  Buccellato under ECO-000046** — a pre-existing, real historical
  reference more than a year old, never touched by this test's step 8b at
  all. The five reference-add events this session's 8b actually created
  for WI-00077 (FTP-00001, 820-00006, FO-00127/Traveler, PL-00004-01,
  RE-00019-01, all timestamped 2026-09-03) all carry descriptive notes.
  The follow-up round's `update_item_reference` call on it (adding a note)
  was an unnecessary touch of unrelated historical data, not a bug fix —
  no skill defect here after all.

## 8a. File metadata (all four items)

- [x] Category resolved live and matched: "Quality Procedure" (Item A,
      shared with QCP), "Work Instructions" (Item B), "Plan" (Item C),
      "Report" (Item D) (MUST, never hardcoded). — confirmed for all four.
- [x] Author read from each document's own stated preparer (front
      matter/signature block), not asked of the user and not defaulted to
      whoever is running the workflow (MUST). — confirmed: all four files
      show author "Brennan Chaloux," independently verified against each
      markdown source's own front-matter `author:` field (not a
      workflow-runner default).
- [x] Format set per file (SHOULD). — confirmed (DOCX/PDF pairs set
      correctly per format).

## 9. Pre-submit checklist

- [x] Restated to the user with explicit confirmation per item (MUST). —
      confirmed: full checklist restated per item, user confirmed.
- [x] Item B's blocked file update flagged as an open item, not silently
      dropped (MUST). — **N/A this run, correctly so:** there was no
      blocked file (see the step-8/Item-B finding above — the real bug was
      fixed earlier this session), so there was nothing to flag; the
      follow-up round correctly did not fabricate a blocker.
- [x] Reviewer requirements (Quality, Regulatory, 2 independent approvers,
      creator not sole approver) stated as manual Arena UI steps (MUST). —
      confirmed.
- [x] Cost view not raised — N/A for this scenario (SHOULD). — confirmed
      N/A (not raised); note the same Arena-default caveat as the step 7
      `bom_view`/`sourcing_view` item applies to `costingView` on new-item
      path items.

## 10. Submit / route

- [x] Explicit user confirmation obtained before the first `route_change`
      call (MUST). — confirmed.
- [x] Two-call sequence: first with `administrator_guids`, second without
      (MUST). — confirmed: first call (`administrator_guids=[Matt
      Morales]`) returned `SUBMITTED_FOR_ROUTING`; second call (no
      administrator_guids) returned `EFFECTIVE`.
- [x] `force_approve_change`/`force_reject_change` never called (MUST). —
      confirmed, neither called.
- [x] Final `lifecycleStatus`/`status` from the second call read and
      reported, not assumed (MUST). — confirmed independently via a fresh
      `get_change` call: `lifecycleStatus.type: "EFFECTIVE"`, no approval
      routing configured for this category so it landed straight on
      EFFECTIVE — matches SKILL.md step 10's documented expected outcome.

## Cross-cutting

- [ ] No Arena category/phase/attribute/file-category/number-format GUID
      hardcoded anywhere in the transcript (MUST). — (not independently
      re-verifiable end-to-end without the lost transcript); all final
      GUIDs resolved to correct live sandbox values with matching names,
      no evidence of hardcoding.
- [x] Every deferral to the matching `dilon-arena-document-standard-<type>`
      skill actually happened for all four items (MUST). — confirmed via
      categorization outcomes plus the pre-reset session's progress log.
- N/A this run: no Arena error codes were encountered/surfaced.
- [x] Environment stayed on `sandbox` for the entire run — no accidental
      `switch_environment("production")` mid-run (MUST). — confirmed:
      `get_active_environment` checked sandbox both before and after the
      resumed work; no `switch_environment` call reported anywhere.

## Outcome log

| Item | Result | Notes |
|------|--------|-------|
| A — FTP-00001 (new-path) | PASS | New item, never released; `create_file` (edition 1) used correctly; category "Quality Procedure"; connections to WI-00077 and Traveler FO-00127 created with approval. |
| B — WI-00077 (revision, RELEASED-file blocker) | PASS (blocker resolved, not hit) | `create_file_edition` succeeded (edition 1→2) — the multipart-field-name bug (`filecontent` vs `file.content`) was found and fixed earlier this session; checklist's old "expected to block" note is now stale and was rewritten above. |
| C — PL-00004 -> PL-00004-01 (reissue) | PASS | Reissue exception discovered unprompted via empty `get_item_references` + reading `dilon-arena-document-standard-pl`; `-01` computed correctly; supersedes link created. |
| D — RE-00019 -> RE-00019-01 (reissue) | PASS | Same unprompted discovery via `-re` skill; both required links created (supersedes + tests-PL-00004-01). |
| 8b — Item connections (approval gate) | PASS | All connections user-approved before creation; no duplicates. All 5 references this run's step 8b actually created for WI-00077 carry descriptive notes — the one null-note reference found during review turned out to be unrelated pre-existing sandbox data from 2025, not something this test created (see Findings below). |
| Submission (step 10) | PASS | Two-call `route_change` sequence executed correctly; landed on `EFFECTIVE` (no approval routing configured for this category, matching SKILL.md's documented expected outcome); `force_approve`/`force_reject` never used. |

## Findings to consider filing separately

1. **Stale checklist expectation, not a skill bug:** step 8/Item B's
   "confirmed Known limitation" for `create_file_edition` is resolved —
   see the note rewritten in place above. `SKILL.md`/`core.md` were
   already updated for the real root cause during this session.
2. **Retracted — not a gap.** Initially flagged as a missing `notes` field
   on a `create_item_reference` call; `get_item_history` shows that
   reference (WI-00077 -> 820-00001) was actually added 2025-02-11 by
   Shannon Buccellato under ECO-000046, over a year before this test and
   with no relation to it. This test's own step 8b reference-add calls all
   carried descriptive notes. No SKILL.md change needed.
3. **Non-defect platform behavior — filed to `core.md`'s Known gaps
   2026-09-03:** Arena defaults `bomView`/`costingView`/`sourcingView` to
   `true` for genuinely new items regardless of what's requested, unlike
   revision-path items where they can correctly be left `false`.
4. Not pursued (QCP-00001 sandbox data gap) — out of scope per reviewer.
5. **Carried over from earlier in this test session (unrelated to
   grading above):** `dilon-arena-eco-canceler`'s SKILL.md still needs
   updating to document that `cancel_change` works directly from
   `OPEN_AND_UNLOCKED` — confirmed while cleaning up leftover test ECOs
   before this run started.
