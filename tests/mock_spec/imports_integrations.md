# Mock Spec: Imports & Integrations

Import definitions/runs, integrations, triggers, outbound events — everything `server/tools/imports_integrations.py` implements.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `get_import_definition` | — | not started |
| `get_import_run` | — | not started |
| `get_import_run_error_content` | — | not started |
| `get_import_run_result_content` | — | not started |
| `get_import_runs` | — | not started |
| `get_integration` | — | not started |
| `get_integration_administrators` | — | not started |
| `get_outbound_event_integration` | — | not started |
| `get_outbound_event_integration_administrators` | — | not started |
| `get_outbound_event_integration_trigger` | — | not started |
| `get_outbound_event_integration_triggers` | — | not started |
| `get_trigger` | — | not started |
| `list_triggers` | — | not started |
| `search_import_definitions` | — | not started |
| `search_integrations` | — | not started |
| `search_outbound_event_integrations` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
