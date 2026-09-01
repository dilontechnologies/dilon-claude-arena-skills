# dilon-claude-arena-skills — Claude Guide

## Project Context

Arena PLM MCP server (`arena_mcp/arena_mcp_server.py` entrypoint over the
`arena_mcp/server/` package, originally copied from `~/arena-mcp`) plus
Dilon-specific Claude Code skills that drive it. `server/` is split by
Arena domain (`server/tools/items_core.py`, `changes_core.py`, etc.) —
see `server/__init__.py` for the full module manifest. The server is raw
REST integration with no Dilon policy; each skill encodes one real Dilon
process on top of it.

**Plugin Details:**
- Plugin name: `dilon-arena-skills` (version tracked in both `VERSION.txt`
  and `.claude-plugin/plugin.json` — keep them in sync, enforced by
  `tests/test_version_sync.py` and CI; see `RELEASING.md`).
- Marketplace: `dilon-claude-arena-skills`, defined in
  `.claude-plugin/marketplace.json` (this repo is its own marketplace).

**Distribution Workflow:**
- Skills install via Claude Code's plugin marketplace commands:
  `/plugin marketplace add dilontechnologies/dilon-claude-arena-skills` then
  `/plugin install dilon-arena-skills@dilon-claude-arena-skills`. Updates:
  `/plugin marketplace update dilon-claude-arena-skills` then
  `/plugin update dilon-arena-skills@dilon-claude-arena-skills`.
- The MCP server installs separately via `installer/Install-ArenaMCP.ps1`
  (Windows, PowerShell) — copies to `%USERPROFILE%\arena-mcp`, sets up a
  venv, prompts for Arena credentials, registers with Claude Desktop.
  Re-run it after pulling a new tag to update an existing install.

## Skills

Deciding whether a new Arena/Dilon rule is a new skill, an amendment to an
existing skill, or just a core update — and how amendments are named and
cross-linked — is covered in
`docs/requirements/README.md`. Once an amendment skill exists, list it
as a nested sub-bullet under its base skill's entry below rather than as
its own top-level entry.

### `dilon-arena-eco-creator`
**Location:** `skills/dilon-arena-eco-creator/SKILL.md`

Creates and populates an ECO/Deviation/Admin Correction: title/description
conventions, change-level screening, the required assessment fields,
affected items with lifecycle phase transitions, file attachment (new
documents and Update-Edition revisions), and submission/routing to the
Change Administrator. Resolves every Arena GUID live via MCP calls — no
hardcoded category/phase/attribute GUIDs. See the skill file itself for the
full step sequence. Defers to the relevant
`dilon-arena-document-standard-<type>` skill (FO/WI/QCP/FTP/PL/RE) for
that document's naming, revision, item-connection, and usage rules rather
than duplicating them; invokes `dilon-arena-document-standard-definer` for
an undeclared type.

### `dilon-arena-eco-canceler`
**Location:** `skills/dilon-arena-eco-canceler/SKILL.md`

Teardown counterpart to `dilon-arena-eco-creator`: cancels, deletes, or
withdraws an ECO/Deviation/Admin Correction that shouldn't proceed, picking
the right Arena API call based on the change's current lifecycle status.
Documents that deleting a draft change does not cascade-delete the
items/files created for it, and the manual cleanup that requires.

### `dilon-arena-document-standard-fo`
**Location:** `skills/dilon-arena-document-standard-fo/SKILL.md`

Naming, revision, item-connection, and usage rules for Form (FO) controlled
documents. `dilon-arena-eco-creator` points here for FO items instead of
repeating these rules.

### `dilon-arena-document-standard-wi`
**Location:** `skills/dilon-arena-document-standard-wi/SKILL.md`

Naming, revision, item-connection, and usage rules for Work Instruction
(WI) controlled documents.

### `dilon-arena-document-standard-qcp`
**Location:** `skills/dilon-arena-document-standard-qcp/SKILL.md`

Naming, revision, item-connection, and usage rules for QCP controlled
documents. Flags the change Affected-Items picklist value as unconfirmed.

### `dilon-arena-document-standard-ftp`
**Location:** `skills/dilon-arena-document-standard-ftp/SKILL.md`

Naming, revision, item-connection, and usage rules for FTP controlled
documents. Flags the change Affected-Items picklist value as unconfirmed.

### `dilon-arena-document-standard-pl`
**Location:** `skills/dilon-arena-document-standard-pl/SKILL.md`

Naming, revision, item-connection, and usage rules for Test Plan (PL)
controlled documents, including the reissue-as-new-item exception once a
completed report already exists against the plan.

### `dilon-arena-document-standard-re`
**Location:** `skills/dilon-arena-document-standard-re/SKILL.md`

Naming, revision, item-connection, and usage rules for Test Report (RE)
controlled documents, including the same reissue-as-new-item exception as
`dilon-arena-document-standard-pl`.

### `dilon-arena-document-standard-definer`
**Location:** `skills/dilon-arena-document-standard-definer/SKILL.md`

Interviews the user into a new `dilon-arena-document-standard-<type>` skill
when `dilon-arena-eco-creator` (or a direct request) hits a document type
with no standard yet. Always generates a submission file and prompts the
user to send it to the developer for review and inclusion in the main
repo.

## Testing

`tests/` uses `pytest` + `respx` to mock Arena's REST API — no live Arena
access needed. Two coverage tiers:
- Every read-only tool (`get_*`/`list_*`/`search_*`/`whoami`) — discovered
  via introspection in `tests/test_read_tools.py`, not hand-enumerated.
- Write tools, scoped to what a skill actually calls —
  `tests/test_change_writes.py` (`dilon-arena-eco-creator` and
  `dilon-arena-eco-canceler`'s change-status tools), `tests/test_file_writes.py`
  (`dilon-arena-eco-creator`), and `tests/test_item_writes.py`
  (`dilon-arena-eco-canceler`'s `delete_item`).

When a test proves a real bug in `arena_mcp_server.py`, fix it there — the
server is a copy, not a frozen artifact. When adding a new skill, extend
the write-tool tier with that skill's tools; the read-tool tier already
covers whatever it reads.

## Before Making Changes

See `.claude/branching-strategy.md` for the branch model
(`DEV/<name>/<description>` for features, `BUG/<name>/<description>` for
fixes, both PR'd against the current `REL/v*.*.*` branch; never commit
directly to `master`).
