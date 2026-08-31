# dilon-claude-arena-skills — Claude Guide

## Project Context

Arena PLM MCP server (`arena_mcp/arena_mcp_server.py`, copied from
`~/arena-mcp`) plus Dilon-specific Claude Code skills that drive it. The
server is raw REST integration with no Dilon policy; each skill encodes one
real Dilon process on top of it.

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

### `dilon-arena-eco-creator`
**Location:** `skills/dilon-arena-eco-creator/SKILL.md`

Creates and populates an ECO/Deviation/Admin Correction: title/description
conventions, change-level screening, the required assessment fields,
affected items with lifecycle phase transitions, file attachment (new
documents and Update-Edition revisions), and submission/routing to the
Change Administrator. Resolves every Arena GUID live via MCP calls — no
hardcoded category/phase/attribute GUIDs. See the skill file itself for the
full step sequence.

## Testing

`tests/` uses `pytest` + `respx` to mock Arena's REST API — no live Arena
access needed. Two coverage tiers:
- Every read-only tool (`get_*`/`list_*`/`search_*`/`whoami`) — discovered
  via introspection in `tests/test_read_tools.py`, not hand-enumerated.
- Write tools, scoped to what a skill actually calls (currently
  `dilon-arena-eco-creator`'s tool set) — `tests/test_change_writes.py` and
  `tests/test_file_writes.py`.

When a test proves a real bug in `arena_mcp_server.py`, fix it there — the
server is a copy, not a frozen artifact. When adding a new skill, extend
the write-tool tier with that skill's tools; the read-tool tier already
covers whatever it reads.

## Before Making Changes

See `.claude/branching-strategy.md` for the branch model
(`DEV/<name>/<description>` for features, `BUG/<name>/<description>` for
fixes, both PR'd against the current `REL/v*.*.*` branch; never commit
directly to `master`).
