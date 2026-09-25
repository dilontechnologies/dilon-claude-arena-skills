# Mock Spec: Files

Controlled-file CRUD, editions, corrections, markups, check-in/out — everything `server/tools/files.py` implements.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `cancel_file_check_out` | — | not started |
| `check_in_file` | — | not started |
| `check_out_file` | — | not started |
| `correct_file` | — | not started |
| `create_file` | — | not started |
| `create_file_edition` | — | not started |
| `create_file_markup` | — | not started |
| `delete_file` | — | not started |
| `delete_file_markup` | — | not started |
| `get_file_change_implementations` | — | not started |
| `get_file_changes` | — | not started |
| `get_file_content` | — | not started |
| `get_file_corrections` | — | not started |
| `get_file_editions` | — | not started |
| `get_file_items` | — | not started |
| `get_file_markup_content` | — | not started |
| `get_file_markups` | — | not started |
| `get_file_quality_processes` | — | not started |
| `get_file_requests` | — | not started |
| `get_file_summary` | — | not started |
| `get_file_supplier_items` | — | not started |
| `get_file_suppliers` | — | not started |
| `get_file_training_plans` | — | not started |
| `get_file_watermark_content` | — | not started |
| `list_file_attributes` | — | not started |
| `list_file_categories` | — | not started |
| `search_files` | — | not started |
| `update_file_markup` | — | not started |
| `update_file_summary` | — | not started |
| `upload_file_content` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
