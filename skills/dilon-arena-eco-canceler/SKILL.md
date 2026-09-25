---
name: dilon-arena-eco-canceler
description: Cancel, delete, or withdraw an Engineering Change Order, Deviation, or Admin Correction in Arena that shouldn't proceed, including the manual cleanup a deleted draft change leaves behind. Use when asked to reject, cancel, delete, withdraw, reopen, or otherwise undo/unwind a change record — the teardown counterpart to dilon-arena-eco-creator, which only builds and submits changes forward.
---

# Dilon Arena ECO Canceler

Companion to `dilon-arena-eco-creator` for undoing a change instead of
creating or advancing one. Every GUID is resolved live via MCP calls —
never hardcode a category, phase, or attribute GUID in this skill, same
convention as `dilon-arena-eco-creator`.

## 1. Identify the change and its current status

`get_change(guid)` or `get_change_workflow_status(guid)` — the right
teardown action depends entirely on the change's current lifecycle status,
not on what the user calls the action ("reject" and "cancel" mean
different concrete API calls depending on where the change currently
sits). Don't guess the status from what the user describes; check it.

## 2. Pick the right action for the current status

- **`OPEN_AND_UNLOCKED` (draft, never submitted) and it's a pure
  mistake — nothing about it should exist:** `delete_change(guid)`. Only
  works on a draft. **Does not cascade** — see step 3, always required
  reading before using this.
- **`OPEN_AND_UNLOCKED` (draft) but you want a canceled record kept for
  the audit trail instead of removed entirely:** `cancel_change(guid,
  comment=...)` (status `CANCELED`). **OPEN QUESTION**: not confirmed
  whether Arena accepts `CANCELED` directly from a draft, or only from an
  already-submitted state — test in the sandbox workspace first (see
  "Sandbox testing practice" below) before relying on this from a draft.
- **Already submitted (`SUBMITTED_FOR_ROUTING`/`SUBMITTED_FOR_APPROVAL`)
  and the submitter/owner wants to pull it back:** `withdraw_change(guid,
  comment=...)` (status `WITHDRAWN`). This is the "I changed my mind after
  submitting" path — not a peer/approver rejecting it (see Known
  limitation below).
- **`COMPLETED` and it needs to be reopened for more work:**
  `reopen_change(guid, comment=...)` (status `REOPENED`) or
  `uncomplete_change(guid, comment=...)` (status `OPEN_AND_UNLOCKED`
  directly). **OPEN QUESTION**: not empirically distinguished which one
  Dilon's actual configured workflow expects — `uncomplete_change` goes
  straight back to a fully-open working state, `reopen_change` produces a
  distinct `REOPENED` status that may or may not be meaningful for this
  workspace's category configuration. Verify against a real category
  before relying on either without asking the user which behavior they
  actually want.
- **Never call `force_reject_change`/`force_approve_change` from this
  skill.** Same reasoning `dilon-arena-eco-creator` already documents:
  they bypass real approval routing, only work when a change is already
  `SUBMITTED_FOR_APPROVAL`, exist for sandbox testing only, and an
  `APPROVED` change auto-advances straight to `EFFECTIVE` in the same call
  with no intermediate state to catch a mistake in. Point the user at that
  skill's existing warning rather than duplicating the reasoning here.

## 3. Cleaning up after `delete_change` (draft only)

**Confirmed 2026-09-01, sandbox:** `delete_change` only removes the change
record and its own affected-item/file *associations* — never the
underlying item/file objects it pointed at. Tested by creating a draft
ECO, creating a brand-new item + file, attaching the file to the item,
adding the item as an affected item (specs+files view), attaching the file
to the change's Files view too, then `delete_change`-ing the whole thing:
both the item (`search_items`) and file (`get_file_summary`) were still
fully intact afterward.

Before assuming cleanup is needed: only an item/file **newly created for
this specific change** needs unwinding — an item/file that already existed
before this change touched it (a normal revision) is completely unaffected
by the change's own deletion, since only the association gets removed.

For anything genuinely new and now orphaned by the deleted change (e.g. a
new item/file created via `dilon-arena-eco-creator` step 8, or the PL/RE
amendment's new-item path):

- **New item**: `delete_item(item_guid)` — but confirm nothing else now
  legitimately references it first (a deleted item's own outgoing item
  references cascade-delete cleanly per
  `dilon-arena-document-standard-pl`'s core.md findings, but that doesn't
  mean nothing *else* in the workspace depends on the item itself).
- **New file**: this API credential cannot `delete_file` — confirmed
  `403`, code 3024, same limitation as `dilon-arena-eco-creator`'s "File
  attachment mistakes are hard to delete, not just detach" section. The
  file becomes a harmless orphan (unattached, invisible from any
  item/change once the item is gone too) — tell the user it exists and
  that removing it needs either a human with delete rights in Arena's Web
  UI, or an Arena admin granting this API credential delete privileges.
  Don't retry the call or treat this as something to work around.

## Known limitation: no change-level reject/approve decision tool

Unlike Quality Process steps (`make_signoff_step_decision`, which posts to
`/qualityprocesses/<GUID>/steps/<GUID>/decisions` — a different Arena
module entirely), this MCP server has **no tool for a change's own normal
approval-routing reject/approve decision** (the action a human assigned
approver takes on a `SUBMITTED_FOR_APPROVAL` change in Arena's Web UI).
The only change-status tools that touch `APPROVED`/`REJECTED` are
`force_approve_change`/`force_reject_change`, which are the admin-override
bypass excluded above, not a real approver's decision. A genuine
peer-review rejection has to happen as a manual action in Arena's Web UI —
this mirrors `dilon-arena-eco-creator`'s existing "reviewers/approvers
cannot be added via the API" known limitation; tell the user which action
is needed and that it must be done manually, rather than trying to
simulate it with `force_reject_change`.

## Known gaps / not yet covered

- **OPEN QUESTION**: whether `cancel_change` is valid directly from
  `OPEN_AND_UNLOCKED`, or only from an already-submitted state (see step
  2). Not tested this session.
- **OPEN QUESTION**: `reopen_change` vs. `uncomplete_change` — which
  matches Dilon's actual expected post-completion workflow. Not tested.
- Whether Admin Correction / Deviation categories have different
  valid-from-state rules than ECO for any of the transitions above — not
  tested; verify per category the same way `dilon-arena-eco-creator`'s
  "Lifecycle phase transitions" section verifies item-phase transitions
  per category, rather than assuming one map covers every change category.
- No confirmed transition map (which statuses reject a given `status`
  value with error 3063-style "not supported" responses) — treat every
  transition above as the confirmed cases only, everything else unknown
  until tested.

**Sandbox testing practice**: same as `dilon-arena-eco-creator` — test an
unfamiliar or destructive-sounding transition in the "Dilon Technologies
Validation" sandbox workspace (same credentials, different
`ARENA_WORKSPACE_ID`) before trying it against production.
