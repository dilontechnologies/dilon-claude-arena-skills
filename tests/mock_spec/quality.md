# Mock Spec: Quality

Quality process CRUD, steps, decisions, signoff — everything `server/tools/quality.py` implements.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `add_affected_to_quality_step` | — | not started |
| `add_signoff_step_decision_makers` | — | not started |
| `close_quality_process` | — | not started |
| `complete_quality_process_step` | — | not started |
| `create_quality_process` | — | not started |
| `delete_quality_process` | — | not started |
| `get_quality_process` | — | not started |
| `get_quality_process_files` | — | not started |
| `get_quality_process_number_format` | — | not started |
| `get_quality_process_step` | — | not started |
| `get_quality_process_step_affected` | — | not started |
| `get_quality_process_step_affected_record` | — | not started |
| `get_quality_process_step_decision` | — | not started |
| `get_quality_process_step_decisions` | — | not started |
| `get_quality_process_step_files` | — | not started |
| `get_quality_process_steps` | — | not started |
| `get_quality_process_template` | — | not started |
| `list_quality_process_attributes` | — | not started |
| `list_quality_process_number_formats` | — | not started |
| `list_quality_process_owners` | — | not started |
| `list_quality_process_step_attributes` | — | not started |
| `list_quality_process_template_attributes` | — | not started |
| `list_quality_templates` | — | not started |
| `make_signoff_step_decision` | — | not started |
| `remove_affected_from_quality_step` | — | not started |
| `reopen_quality_process_step` | — | not started |
| `route_quality_process` | — | not started |
| `search_quality_processes` | — | not started |
| `update_quality_process` | — | not started |
| `update_quality_process_step` | — | not started |
| `update_quality_process_step_affected` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
