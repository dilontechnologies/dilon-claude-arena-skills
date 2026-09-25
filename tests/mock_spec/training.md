# Mock Spec: Training

Training plan CRUD plus item/user/file/quality-process associations — everything `server/tools/training.py` implements.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `add_file_to_training_plan` | — | not started |
| `add_item_to_training_plan` | — | not started |
| `add_quality_process_to_training_plan` | — | not started |
| `add_users_to_training_plan` | — | not started |
| `create_training_plan` | — | not started |
| `delete_training_plan` | — | not started |
| `get_training_plan` | — | not started |
| `get_training_plan_file` | — | not started |
| `get_training_plan_files` | — | not started |
| `get_training_plan_item` | — | not started |
| `get_training_plan_items` | — | not started |
| `get_training_plan_quality_process` | — | not started |
| `get_training_plan_quality_processes` | — | not started |
| `get_training_plan_record` | — | not started |
| `get_training_plan_records` | — | not started |
| `get_training_plan_user` | — | not started |
| `get_training_plan_users` | — | not started |
| `list_training_managers` | — | not started |
| `remove_file_from_training_plan` | — | not started |
| `remove_item_from_training_plan` | — | not started |
| `remove_quality_process_from_training_plan` | — | not started |
| `remove_user_from_training_plan` | — | not started |
| `search_training_plans` | — | not started |
| `transition_training_plan_status` | — | not started |
| `update_training_plan` | — | not started |
| `update_training_plan_user` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
