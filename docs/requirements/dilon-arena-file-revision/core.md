# `dilon-arena-file-revision` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-file-revision/SKILL.md`. This doc records the
empirical work and decisions behind Dilon's revision-numbering scheme.
Split out from the former `dilon-arena-file-editing` doc/skill pair
(2026-09-01) — see
[`../dilon-arena-file-naming/core.md`](../dilon-arena-file-naming/core.md)
for the file name/title half, and [`../README.md`](../README.md) for the
split rule. This is also the base skill for
[`amendment-pl-re-item-numbering.md`](amendment-pl-re-item-numbering.md),
in this same folder — see that doc for the PL/RE exception to everything
below.

## Purpose

Answer: what literal string does Dilon's baseline/prototype/production
revision-numbering scheme produce for a given item state, and where does
that string get passed in the Arena API?

## Revision-numbering scheme — RESOLVED

**Original open question from the task, since clarified with the user
(2026-08-31):** the task's initial wording ("a never-released item's
baseline is effectively '00', i.e. its first release will be '01'") was
ambiguous/self-contradictory, and conflicted with a real data point found
in the sandbox: `FO-00161`'s actual first production release (`ECO-000190`)
was labeled `"00"`, not `"01"`. Asked the user directly; confirmed:

> First release to production is 00. We can still have prototype releases
> before the first official release, and that will be released as 00-A.

Final scheme:
- Baseline/production revision: `"00"`, `"01"`, `"02"`, ... A never-released
  item's first production release is `"00"` (matches Arena's own
  auto-numbering default).
- Prototype Release ahead of the next production release:
  `"<next-numeric>-<letter>"`. `<next-numeric>` is whatever numeric the
  *next* production release will carry — `"00"` for a never-released item's
  pre-first-release prototypes, `"02"` for prototypes ahead of a release
  that will become `"02"` after a currently-released `"01"`. Successive
  prototype iterations before that same production release increment the
  letter: `"00-A"`, `"00-B"`, ... / `"02-A"`, `"02-B"`, ...
- Promotion to production release condenses back to the plain numeric
  (`"02"`), and the document's revision-history table gets one consolidated
  row for it, not one row per prototype iteration (see "Cross-repo
  dependency" in `SKILL.md` for where that table is actually rendered).
- This is the literal value for `add_items_to_change`'s and
  `update_change_affected_item`'s `new_revision_number` parameter — not
  just a documentation convention.

**Supersedes** `dilon-arena-eco-creator`'s prior text (its step 7), which
described Prototype Release revisions as bare letters (`"A"`, `"B"`) with
no numeric prefix. That was wrong/incomplete and has been corrected there
to point at this doc/skill instead of repeating (now-corrected) details.

**Does not apply to PL/RE items with a completed report already against
them** — see [`amendment-pl-re-item-numbering.md`](amendment-pl-re-item-numbering.md),
in this same folder.

## Empirical verification — RESOLVED (real call, not just dry-run)

The task explicitly required confirming this with a **real** (non-dry-run)
write, not just the dry-run validation that had already passed, before
relying on it for production ECOs. Per this repo's established
sandbox-testing practice (see
`docs/requirements/dilon-arena-eco-creator/core.md`
→ "Sandbox testing practice"), this needed to happen against "Dilon
Technologies Validation" (workspace ID `901596215`), not production.

**Environment-switching friction (2026-08-31, resolved but noted for future
reference):** the installed MCP server at `C:\Users\bchaloux\arena-mcp` had
no multi-environment config yet, and getting a fresh subprocess to pick up
an `ARENA_ENVIRONMENT`/`environments.local.json` change proved unreliable —
neither `/mcp` reconnect nor a full Claude Code relaunch caused a new
subprocess to actually read the updated `.env` (4 stale `python.exe`
processes were found still running against the old config; killing all of
them and reconnecting *still* didn't pick up the change). Root cause not
found. **Workaround used instead**: pointed the `arena` MCP server entry in
`~/.claude.json` at this repo's own copy (`arena_mcp/arena_mcp_server.py`,
repo `.venv`) with a repo-local `arena_mcp/.env` hardcoding
`ARENA_WORKSPACE_ID=901596215` directly (no `ARENA_ENVIRONMENT` indirection)
— this connected cleanly on the next `/mcp` reconnect. **TODO**: root-cause
why the installed copy's environment-switching mechanism didn't take effect
across multiple reconnect/relaunch/process-kill attempts; until then, don't
assume `ARENA_ENVIRONMENT` switching on the installed copy works as
documented in that file's own comments.

**The real-call test itself**, in the sandbox, via a disposable test change
(`ECO-000195`, category Engineering Change Order):
- `add_items_to_change(FO-00001's working rev, target phase Prototype
  Release [PRODUCTION stage], new_revision_number="02-A")` → accepted,
  `newRevisionNumber: "02-A"` in the response.
- `add_items_to_change(FO-00161's working rev, same target phase — item was
  already at Prototype Release, legacy revision "A" — new_revision_number=
  "01-B")` → accepted. Re-queried via `get_item_revisions`: the item's
  `WORKING` revision entry shows `"number": "01-B"`, confirming genuine
  persistence, not just an echoed request value.
- The same-phase transition this required (Prototype Release → Prototype
  Release, for a second prototype iteration ahead of the same production
  release) also succeeded — no error 3063, adding one confirmed pair to
  `dilon-arena-eco-creator`'s phase-transition map (that skill's own section
  owns the general reachability map; this is just the one new data point).

FO-00001 was removed from `ECO-000195` afterward (it was only added for
this test). `ECO-000195` and FO-00161's pending `"01-B"` working revision
were left in place at the user's request, for possible further testing —
not yet cleaned up as of this writing.

## Known gaps / not yet covered

- **Untested**: whether omitting `new_revision_number` on a production
  release that follows a run of prototype iterations (`02-A`, `02-B`, ...)
  correctly auto-assigns the matching plain numeric, or drifts/errors.
  Testing this requires completing/routing a change (not just adding items
  to a Working one) — out of scope for this session. Current guidance:
  always pass the value explicitly rather than rely on this untested
  inference.
- Whether the revision-number scheme needs any special handling if a
  prototype sequence is abandoned before reaching production release.
- `ARENA_ENVIRONMENT`/`environments.local.json` switching on the installed
  copy (`~/arena-mcp`) is unverified/possibly broken — see
  "Environment-switching friction" above. The repo copy pointed at
  directly via a hardcoded `ARENA_WORKSPACE_ID` is the known-working
  pattern for now.
  **Resolved 2026-09-01**: `ARENA_ENVIRONMENT`/`environments.local.json`
  were retired in favor of the `list_environments`/`switch_environment`/
  `set_environment` MCP tools, which mutate the already-running process
  directly — no subprocess restart involved, so the failure mode
  described above no longer applies. See
  `docs/superpowers/specs/2026-09-01-arena-mcp-server-split-design.md`.
- This doc doesn't cover file *content* editing (markup, corrections,
  check-out/check-in) — only the revision-number convention that was in
  scope for this task.
