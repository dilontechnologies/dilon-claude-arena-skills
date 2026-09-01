---
name: dilon-arena-file-revision
description: Determine Dilon's baseline/prototype/production revision-number string for an Arena item, and which Arena API parameter it maps to (`new_revision_number` on `add_items_to_change`/`update_change_affected_item`). Use when creating or revising a controlled item/document in Arena, when an ECO/Deviation/Admin Correction needs a revision value, or when `dilon-arena-file-naming` needs the current revision string to build a file name.
---

# Dilon Arena Revision Numbering

Single source of truth for Dilon's baseline/prototype/production
revision-numbering scheme and the literal string it produces for Arena's
API. `dilon-arena-eco-creator` defers to this skill rather than duplicating
these rules; `dilon-arena-file-naming` consumes this skill's output when it
needs the revision string to build a file's `name` field.

**Before applying the scheme below, check whether an amendment overrides
it for this item.** Currently:
- **Test Plan (PL) / Test Report (RE) items with a completed report
  already against them** don't get a revision bump at all — see
  `dilon-arena-file-revision-amendment-pl-re-item-numbering`, not this
  skill.

## Revision-number scheme

Applies to `add_items_to_change`'s and `update_change_affected_item`'s
`new_revision_number` parameter — this is not just a naming/documentation
convention, it's the literal string Arena stores as the item's revision.

- **Baseline / production revision**: two-digit numeric, `"00"`, `"01"`,
  `"02"`, ... incrementing by one on each production release. A
  never-released item's baseline is `"00"` — its first production release
  is also `"00"` (confirmed against Arena's own auto-numbering default and
  against a real item's history in the sandbox workspace; there is no
  released `"01"` without a `"00"` before it).
- **Prototype Release ahead of the next production release**: revision is
  `"<next-numeric>-<letter>"`, where `<next-numeric>` is the numeric value
  that production release will carry when it happens (current baseline for
  a never-released item, or current-released + 1 for an already-released
  one). E.g.:
  - Never-released item, first prototype iteration: `"00-A"`, second
    iteration before that same first production release: `"00-B"`.
  - Item currently released at `"01"`, first prototype iteration ahead of
    its next release: `"02-A"`, second iteration: `"02-B"`.
- **Promotion to actual production release**: the revision condenses back
  down to the plain numeric (`"02"`), dropping the letter suffix entirely.
  The document's own revision-history table (compiled from its markdown
  front matter) gets **one row** for that production revision,
  summarizing/consolidating the notes from every prototype iteration that
  preceded it (`02-A`, `02-B`, ...) — not one row per prototype iteration.

**Recommendation: always pass `new_revision_number` explicitly**, for
every transition (baseline, prototype, and production release alike),
rather than omitting it and relying on Arena's auto-assignment. A plain
first-ever production release (`"00"`, omitted) is confirmed compatible
with Arena's own default (see "Empirical verification" below) and with
`dilon-arena-eco-creator`'s existing documented omit-for-RELEASED-phase
behavior. But whether Arena's auto-assignment correctly computes the right
numeric when a production release is reached *after* a run of
letter-suffixed prototype revisions (e.g. `02-A`, `02-B` → does omitting
still yield `"02"`, not `"03"` or an error?) has **not** been tested — see
Known gaps below. Passing the exact value explicitly sidesteps needing to
trust that inference at all, and Dilon's scheme already determines the
exact value deterministically at every step, so there's no upside to
omitting it.

## Empirical confirmation (2026-08-31)

**RESOLVED — real (non-dry-run) write confirmed, not just dry-run
validation.** Tested in the sandbox workspace ("Dilon Technologies
Validation", workspace ID `901596215`) via a disposable test change
(`ECO-000195`):

- `add_items_to_change` on `FO-00001` (working rev, target phase Prototype
  Release [`PRODUCTION` stage]) with `new_revision_number="02-A"` was
  accepted and returned `newRevisionNumber: "02-A"` in the response.
- `add_items_to_change` on `FO-00161` (working rev, same target phase —
  the item was already sitting in Prototype Release at legacy revision
  `"A"` from earlier testing) with `new_revision_number="01-B"` was
  accepted, and — critically — `get_item_revisions` afterward confirmed it
  as genuinely **persisted**, not just echoed: the item's `WORKING`
  revision entry shows `"number": "01-B"`, `"revisionStatus": "WORKING"`.
- The same-phase transition (Prototype Release → Prototype Release, i.e. a
  second prototype iteration ahead of the same production release) also
  succeeded with no error 3063.

This supersedes `dilon-arena-eco-creator`'s old text describing prototype
revisions as bare letters (`"A"`, `"B"`) with no numeric prefix — that
description is incomplete/wrong; the confirmed scheme is above.

FO-00001 was subsequently removed from `ECO-000195` (it was only there for
this test). `ECO-000195` and FO-00161's pending `"01-B"` working revision
were intentionally left in place afterward for further testing — not yet
cleaned up as of this writing.

## Cross-repo dependency (informational only — not implemented here)

The document compiler in the separate `dilon-claude-tools` repo
(`skills/dilon-document-compiler` and `skills/dilon-document-form-compiler`,
scripts `generate_dilon_doc.py` / `generate_dilon_form.py`) renders each
document's markdown front-matter `revisions:` list into the revision-history
table in the compiled docx. That table's "Rev" column is sized for short
values (`"00"`, `"A"`) and needs widening to fit `"02-A"`-style strings —
being handled directly in that repo, not here. This skill's job stops at
determining *what string* goes in Arena and in that front-matter list; how
it's rendered into a table is out of scope.

## Amendments

- `dilon-arena-file-revision-amendment-pl-re-item-numbering` — Test Plan
  (PL) / Test Report (RE) items with a completed report already against
  them get a new Basic Item under a `<base>-<NN>` number instead of a
  revision bump on the existing item. Applies only to PL/RE, only once a
  completed report exists.

## Known gaps / not yet covered

- **Untested**: whether omitting `new_revision_number` on a production
  release that follows a run of prototype iterations (`02-A`, `02-B`, ...)
  correctly auto-assigns the matching plain numeric (`"02"`), or whether it
  drifts/errors. Not yet tested because doing so requires completing/
  routing a change (not just adding items to a Working one), which wasn't
  covered by this session's scope. Until tested, follow the recommendation
  above to always pass the value explicitly.
- **Untested**: whether the revision-number scheme interacts with sorting
  or any lifecycle-phase-transition rule beyond the one same-phase pair
  confirmed above. `dilon-arena-eco-creator`'s "Lifecycle phase
  transitions" section owns the general phase-reachability map; this skill
  only adds the one new same-phase (Prototype → Prototype) data point.
- No convention yet defined for what happens if a prototype sequence is
  abandoned entirely (never reaches production release) — does the
  document's revision history need any entry for `02-A`/`02-B` at all in
  that case, or only once/if `02` actually ships?
- `ARENA_ENVIRONMENT`/`environments.local.json` switching on the installed
  copy (`~/arena-mcp`) is unverified/possibly broken — see
  `docs/requirements/dilon-arena-file-revision/core.md` →
  "Environment-switching
  friction." The repo copy pointed at directly via a hardcoded
  `ARENA_WORKSPACE_ID` is the known-working pattern for now.
  **Resolved 2026-09-01**: `ARENA_ENVIRONMENT`/`environments.local.json`
  were retired in favor of the `list_environments`/`switch_environment`/
  `set_environment` MCP tools, which mutate the already-running process
  directly — no subprocess restart involved, so the failure mode
  described above no longer applies. See
  `docs/superpowers/specs/2026-09-01-arena-mcp-server-split-design.md`.
