# Mock Spec: Activity

Recent activity, API usage, Arena settings, export attributes — everything `server/tools/activity.py` implements.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `get_api_usage` | — | not started |
| `get_arena_settings` | — | not started |
| `get_recent_activity_exports` | — | not started |
| `get_recent_activity_file_access` | — | not started |
| `get_recent_activity_report_runs` | — | not started |
| `get_recent_activity_user_access` | — | not started |
| `list_export_attributes` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
