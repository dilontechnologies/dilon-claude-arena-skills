# Mock Spec: Items

Item CRUD, lifecycle, BOM, item-file associations, compliance/sourcing/references — everything `server/tools/items_core.py`, `items_bom.py`, `items_files.py`, and `items_compliance.py` implement.

See `README.md` in this directory for shared conventions (auth flow,
pagination, error shape, `dry_run` handling, GUID resolution, multipart
upload) and the entry template used below.

## Coverage

| Tool | Used by | Mock status |
|---|---|---|
| `add_existing_file_to_item` | — | not started |
| `add_item_compliance_declaration` | — | not started |
| `cancel_item_number_reservation` | — | not started |
| `change_item_lifecycle_phase` | — | not started |
| `create_bom_line` | — | not started |
| `create_bom_substitute` | — | not started |
| `create_item` | — | not started |
| `create_item_reference` | — | not started |
| `create_item_source` | — | not started |
| `create_item_thumbnail_from_files_view` | — | not started |
| `delete_bom_line` | — | not started |
| `delete_bom_substitute` | — | not started |
| `delete_item` | — | not started |
| `delete_item_compliance` | — | not started |
| `delete_item_reference` | — | not started |
| `delete_item_source` | — | not started |
| `delete_item_thumbnail` | — | not started |
| `get_item` | — | not started |
| `get_item_attribute` | — | not started |
| `get_item_bom` | — | not started |
| `get_item_bom_line` | — | not started |
| `get_item_bom_settings` | — | not started |
| `get_item_bom_substitute` | — | not started |
| `get_item_bom_substitutes` | — | not started |
| `get_item_category` | — | not started |
| `get_item_compliance` | — | not started |
| `get_item_compliance_requirement` | — | not started |
| `get_item_file` | — | not started |
| `get_item_file_watermark_content` | — | not started |
| `get_item_files` | — | not started |
| `get_item_future_changes` | — | not started |
| `get_item_history` | — | not started |
| `get_item_number_format` | — | not started |
| `get_item_quality_processes` | — | not started |
| `get_item_reference` | — | not started |
| `get_item_references` | — | not started |
| `get_item_requirement` | — | not started |
| `get_item_revisions` | — | not started |
| `get_item_source` | — | not started |
| `get_item_sourcing` | — | not started |
| `get_item_thumbnail` | — | not started |
| `get_item_tickets` | — | not started |
| `get_item_training_plan` | — | not started |
| `get_item_training_plans` | — | not started |
| `get_item_training_record` | — | not started |
| `get_item_training_records` | — | not started |
| `get_item_where_used` | — | not started |
| `list_item_attribute_groups` | — | not started |
| `list_item_attributes` | — | not started |
| `list_item_bom_attributes` | — | not started |
| `list_item_categories` | — | not started |
| `list_item_category_attributes` | — | not started |
| `list_item_lifecycle_phases` | — | not started |
| `list_item_number_formats` | — | not started |
| `list_item_number_reservations` | — | not started |
| `list_item_requirements` | — | not started |
| `remove_file_from_item` | — | not started |
| `reserve_item_number` | — | not started |
| `search_items` | — | not started |
| `update_bom_line` | — | not started |
| `update_bom_settings` | — | not started |
| `update_bom_substitute` | — | not started |
| `update_item` | — | not started |
| `update_item_compliance` | — | not started |
| `update_item_file_association` | — | not started |
| `update_item_reference` | — | not started |
| `update_item_source` | — | not started |
| `upload_item_file_content` | — | not started |
<!-- one row per tool in this domain; see arena_mcp/server/tools/ for the
     authoritative current list — this table is a tracking aid, not a
     duplicate source of truth, so don't let it silently drift out of
     sync as tools are added/removed there -->

## Entries

<!-- Copy the entry template from README.md here as each tool gets
     documented. Empty until the first one is written. -->
