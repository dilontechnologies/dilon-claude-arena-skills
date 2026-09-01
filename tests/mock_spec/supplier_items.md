# Mock Spec: Supplier Items

Supplier item CRUD plus files/compliance/sourcing/quality — everything `server/tools/supplier_items.py` implements.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `add_existing_file_to_supplier_item` | — | not started |
| `create_supplier_item` | — | not started |
| `delete_supplier_item` | — | not started |
| `get_supplier_item` | — | not started |
| `get_supplier_item_compliance` | — | not started |
| `get_supplier_item_compliance_record` | — | not started |
| `get_supplier_item_file` | — | not started |
| `get_supplier_item_file_content` | — | not started |
| `get_supplier_item_files` | — | not started |
| `get_supplier_item_quality_process` | — | not started |
| `get_supplier_item_quality_processes` | — | not started |
| `get_supplier_item_source` | — | not started |
| `get_supplier_item_sourcing` | — | not started |
| `get_supplier_item_thumbnail` | — | not started |
| `list_supplier_item_attributes` | — | not started |
| `list_supplier_item_compliance_requirements` | — | not started |
| `remove_file_from_supplier_item` | — | not started |
| `search_supplier_items` | — | not started |
| `update_supplier_item` | — | not started |
| `update_supplier_item_file_association` | — | not started |
| `upload_supplier_item_file_content` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
