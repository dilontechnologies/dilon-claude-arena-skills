# Mock Spec: Audit Packs

Read-only composite macros aggregating other domains' endpoints — everything `server/tools/audit_packs.py` implements. Uses the variant entry template from README.md, not the standard one.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `audit_pack_capa` | — | not started |
| `audit_pack_change` | — | not started |
| `audit_pack_item` | — | not started |
| `audit_pack_supplier_impact` | — | not started |
| `audit_pack_training_plan` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
