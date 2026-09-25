# `dilon-arena-eco-canceler` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-eco-canceler/SKILL.md`. Companion to
[`../dilon-arena-eco-creator/core.md`](../dilon-arena-eco-creator/core.md) —
that skill only builds/advances a change; this one undoes one.

## Purpose

Give Claude a single place to look when asked to reject, cancel, delete,
withdraw, or reopen an Arena change (ECO/Deviation/Admin Correction),
instead of guessing which of Arena's several teardown-shaped API calls
applies. `dilon-arena-eco-creator`'s own "Known gaps" already flagged this
as missing ("No handling yet for rejection/rework loops after submission,
or for cancelling a change mid-flow") — this skill is that gap filled in.

## Why a new skill, not a section in `dilon-arena-eco-creator`

Per this repo's own test (`../README.md` → "Deciding where a new rule
goes"): rejecting/canceling/deleting a change is independently invokable —
a user can ask to kill an ECO that was never touched by this session, with
no dependency on `dilon-arena-eco-creator`'s own flow having just run. That
makes it a new skill, not a core update or amendment.

## Source: ECO-000262 session findings (2026-09-01)

Everything below traces back to
`docs/requirements/2026-09-01-eco-000262-session-findings.md` (item 4),
a handoff doc from a session in the separate `Nav3` docs repo that hit
this gap while trying to unwind a mistaken PL/RE split.

### `delete_change` does not cascade (confirmed, sandbox)

Created a disposable test ECO, created a brand-new item + file, attached
the file to the item, added the item as an affected item (specs+files
view), attached the file to the change's Files view too, then
`delete_change`'d the whole thing. Both the item (`search_items`) and file
(`get_file_summary`) were still fully intact afterward — `delete_change`
only removes the change record and its own affected-item/file
*associations*, never the underlying item/file objects it pointed at.

**Implication:** if a new item created for an ECO (e.g. via the PL/RE
`-01` amendment, or `dilon-arena-eco-creator` step 8's "new item" branch)
turns out to be a mistake and the ECO gets deleted instead of submitted,
the item and any attached files are **not** cleaned up automatically —
needs an explicit `delete_item` call, and the file becomes a harmless
orphan since this API credential can't `delete_file` (same limitation
`dilon-arena-eco-creator`'s "File attachment mistakes are hard to delete,
not just detach" section already documents for a different scenario —
same root cause, credential lacks delete privileges on `/files`).

### Change lifecycle tools available (from `arena_mcp/server/tools/changes_core.py`)

`cancel_change`, `withdraw_change`, `uncomplete_change`, `reopen_change`,
`delete_change`, `force_reject_change`, `force_approve_change`, plus the
generic `transition_change_status`/`route_change`. None of these were
exercised empirically this session beyond `delete_change` above — the
status-transition validity map (which status a change must be in before
each of these is accepted) is inferred from each tool's docstring, not
tested. See `SKILL.md`'s "Known gaps" for the resulting open questions
(`cancel_change` from a draft, `reopen_change` vs. `uncomplete_change`).

### No change-level approve/reject decision tool

`make_signoff_step_decision` exists but targets Quality Process steps
(`/qualityprocesses/<GUID>/steps/<GUID>/decisions`), a different Arena
module from Change approval routing entirely. There is no equivalent
tool for a Change's own `SUBMITTED_FOR_APPROVAL` → `APPROVED`/`REJECTED`
decision other than the admin-override `force_approve_change`/
`force_reject_change` pair, which `dilon-arena-eco-creator` already
excludes from normal use. A real approver's reject/approve decision has
to happen manually in Arena's Web UI — same shape of gap as
`dilon-arena-eco-creator`'s "reviewers/approvers cannot be added via the
API" known limitation.

## Open questions

- Whether `cancel_change` is valid directly from `OPEN_AND_UNLOCKED`
  (draft), or only from an already-submitted state.
- Whether `reopen_change` (status `REOPENED`) or `uncomplete_change`
  (status `OPEN_AND_UNLOCKED`) is the one Dilon's actual workflow expects
  after a change is `COMPLETED` — these produce different resulting
  statuses and haven't been tested against a real category's configured
  workflow.
- Whether Admin Correction / Deviation categories have different
  valid-from-state rules than ECO for any of these transitions.
- No confirmed transition-validity map (analogous to
  `dilon-arena-eco-creator`'s "Lifecycle phase transitions" section for
  item phases) exists yet for change statuses — everything not explicitly
  confirmed above is unknown until tested, ideally in the sandbox
  workspace first.
