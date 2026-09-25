# dilon-claude-arena-skills

Arena PLM MCP server + Dilon-specific Claude Code skills that drive it.

## What's here

- `arena_mcp/arena_mcp_server.py` — a copy of Dilon's Arena PLM MCP server
  (raw REST integration, no Dilon policy baked in).
- `installer/Install-ArenaMCP.ps1` — the one-step Windows installer.
- `env/` — the server's runtime (`requirements.txt`, `.env.example`) and dev
  (`requirements-dev.txt`) dependency files.
- `docs/installation/` — teammate-facing setup docs (`SETUP-GUIDE.md`,
  `QUICKSTART-for-teammate.md`, `HELP-paste-to-Claude.md`).
- `skills/dilon-arena-eco-creator/` — a Claude Code skill that uses the MCP
  server to create, populate, attach files to, and submit an Engineering
  Change Order per SOP-00004.
- `tests/` — a pytest suite that mocks Arena's REST API (via `respx`), so
  the whole suite runs offline. Covers every read-only MCP tool and the
  write tools the ECO skill calls.

## Installing the MCP server

Clone this repo, then run `installer/Install-ArenaMCP.ps1` (right-click ->
"Run with PowerShell", or `.\Install-ArenaMCP.ps1` from an open PowerShell
prompt in the `installer/` folder). It copies the server to
`%USERPROFILE%\arena-mcp`, sets up a venv, prompts for your three Arena
credential values, and registers the server with Claude Desktop. See
`docs/installation/SETUP-GUIDE.md` and
`docs/installation/QUICKSTART-for-teammate.md` for details.

To update an existing install: pull the latest tag from this repo and
re-run `installer/Install-ArenaMCP.ps1` — it overwrites the local install
in place.

## Installing the skills

```
/plugin marketplace add dilontechnologies/dilon-claude-arena-skills
/plugin install dilon-arena-skills@dilon-claude-arena-skills
```

For local testing before relying on the marketplace:
`/plugin marketplace add ./dilon-claude-arena-skills` (run from the parent
directory of a clone).

## Running the tests

```
python -m venv .venv
.venv/Scripts/pip install -r env/requirements-dev.txt
.venv/Scripts/pytest tests/ -v
```

No Arena account or network access is required — the suite mocks Arena's
REST API entirely.

## Contributing

See `RELEASING.md` and `.claude/branching-strategy.md` for the branch model
(`DEV/**`/`BUG/**` -> `REL/**` -> `master`) and release process.
