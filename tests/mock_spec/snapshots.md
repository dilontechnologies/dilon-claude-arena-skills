# Mock Spec: Snapshots

Local state snapshot/restore (not an Arena endpoint domain — reads/writes files under `SNAPSHOT_DIR`) — everything `server/tools/snapshots.py` implements.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `get_snapshot` | — | not started |
| `list_snapshots` | — | not started |
| `restore_from_snapshot` | — | not started |
| `snapshot_state` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
