# Mock Spec: Changes

Change (ECO/Deviation/Admin Correction) CRUD, workflow/status transitions, routing, implementation tasks/notes/files, change file markup — everything `server/tools/changes_core.py` and `changes_implementation.py` implement.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `add_file_to_change` | — | not started |
| `add_file_to_change_implementation` | — | not started |
| `add_items_to_change` | — | not started |
| `attach_file_to_change_implementation_task` | — | not started |
| `cancel_change` | — | not started |
| `complete_change` | — | not started |
| `create_change` | — | not started |
| `create_change_file_markup` | — | not started |
| `create_change_implementation_task` | — | not started |
| `create_change_implementation_task_note` | — | not started |
| `delete_change` | — | not started |
| `delete_change_file_markup` | — | not started |
| `delete_change_implementation_task` | — | not started |
| `delete_change_implementation_task_note` | — | not started |
| `force_approve_change` | — | not started |
| `force_reject_change` | — | not started |
| `get_change` | — | not started |
| `get_change_category` | — | not started |
| `get_change_files` | — | not started |
| `get_change_history` | — | not started |
| `get_change_implementation_file` | — | not started |
| `get_change_implementation_files` | — | not started |
| `get_change_implementation_task` | — | not started |
| `get_change_implementation_task_file` | — | not started |
| `get_change_implementation_task_files` | — | not started |
| `get_change_implementation_task_note` | — | not started |
| `get_change_implementation_task_notes` | — | not started |
| `get_change_implementation_task_template` | — | not started |
| `get_change_implementation_tasks` | — | not started |
| `get_change_items` | — | not started |
| `get_change_workflow_status` | — | not started |
| `list_change_administrators` | — | not started |
| `list_change_attributes` | — | not started |
| `list_change_categories` | — | not started |
| `list_change_category_attributes` | — | not started |
| `list_change_implementation_statuses` | — | not started |
| `list_change_implementation_task_templates` | — | not started |
| `list_change_item_attributes` | — | not started |
| `list_change_number_prefixes` | — | not started |
| `list_change_number_sequence_prefixes` | — | not started |
| `list_change_routings` | — | not started |
| `remove_file_from_change` | — | not started |
| `remove_file_from_change_implementation` | — | not started |
| `remove_file_from_change_implementation_task` | — | not started |
| `remove_items_from_change` | — | not started |
| `reopen_change` | — | not started |
| `route_change` | — | not started |
| `search_changes` | — | not started |
| `transition_change_status` | — | not started |
| `uncomplete_change` | — | not started |
| `update_change` | — | not started |
| `update_change_affected_item` | — | not started |
| `update_change_implementation_task` | — | not started |
| `update_change_implementation_task_note` | — | not started |
| `withdraw_change` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
