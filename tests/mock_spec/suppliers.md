# Mock Spec: Suppliers

Supplier CRUD plus addresses/phones/files/quality associations — everything `server/tools/suppliers.py` implements.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `add_file_to_supplier` | — | not started |
| `add_supplier_address` | — | not started |
| `add_supplier_phone` | — | not started |
| `create_supplier` | — | not started |
| `delete_supplier` | — | not started |
| `delete_supplier_address` | — | not started |
| `delete_supplier_phone` | — | not started |
| `get_supplier` | — | not started |
| `get_supplier_address` | — | not started |
| `get_supplier_addresses` | — | not started |
| `get_supplier_file` | — | not started |
| `get_supplier_files` | — | not started |
| `get_supplier_phone_number` | — | not started |
| `get_supplier_phone_numbers` | — | not started |
| `get_supplier_quality_process` | — | not started |
| `get_supplier_quality_processes` | — | not started |
| `list_supplier_approval_statuses` | — | not started |
| `list_supplier_attributes` | — | not started |
| `remove_file_from_supplier` | — | not started |
| `search_suppliers` | — | not started |
| `update_supplier` | — | not started |
| `update_supplier_address` | — | not started |
| `update_supplier_phone` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
