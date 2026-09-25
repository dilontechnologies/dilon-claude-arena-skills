from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _resolve_lifecycle_phase_guid, _wildcard, _paginate_get, _request_bytes, _write_snapshot

__all__ = [
    "list_item_categories",
    "list_item_lifecycle_phases",
    "list_item_number_formats",
    "search_items",
    "get_item",
    "get_item_where_used",
    "get_item_revisions",
    "get_item_history",
    "get_item_future_changes",
    "get_item_quality_processes",
    "get_item_training_plans",
    "get_item_training_records",
    "get_item_tickets",
    "get_item_thumbnail",
    "get_item_training_plan",
    "get_item_training_record",
    "list_item_attributes",
    "get_item_attribute",
    "list_item_attribute_groups",
    "list_item_category_attributes",
    "get_item_category",
    "list_item_number_reservations",
    "get_item_number_format",
    "list_item_requirements",
    "get_item_requirement",
    "create_item",
    "update_item",
    "delete_item",
    "create_item_thumbnail_from_files_view",
    "delete_item_thumbnail",
    "change_item_lifecycle_phase",
    "reserve_item_number",
    "cancel_item_number_reservation",
]


@mcp.tool()
def list_item_categories(
    path: Optional[str] = None,
    include_deleted: bool = False,
) -> dict[str, Any]:
    """List item categories.

    Args:
        path: Optional path filter (e.g. r"Item\\Assembly" returns all
            categories under Assembly). Wildcards supported.
        include_deleted: If True, also includes soft-deleted categories.
    """
    params: dict[str, Any] = {}
    if path: params["path"] = path
    if include_deleted: params["includeDeleted"] = "true"
    return _arena_get("/settings/items/categories",
                      params=params if params else None)

@mcp.tool()
def list_item_lifecycle_phases() -> dict[str, Any]:
    """List item lifecycle phases (In Design, In Production, Obsolete, etc.).

    Returns phase GUIDs to use with new_lifecycle_phase_guid in
    add_items_to_change for lifecycle transitions.
    """
    return _arena_get("/settings/items/lifecyclephases")

@mcp.tool()
def list_item_number_formats() -> dict[str, Any]:
    """List item number formats (auto-numbering schemes for new items)."""
    return _arena_get("/settings/items/numberformats")

@mcp.tool()
def search_items(
    query: Optional[str] = None,
    number: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    owner_full_name: Optional[str] = None,
    creator_full_name: Optional[str] = None,
    creator_guid: Optional[str] = None,
    category_guid: Optional[str] = None,
    lifecycle_phase_name: Optional[str] = None,
    revision_number: Optional[str] = None,
    assembly_type: Optional[str] = None,
    in_assembly: Optional[bool] = None,
    effective_from: Optional[str] = None,
    effective_to: Optional[str] = None,
    modified_bom: Optional[bool] = None,
    modified_files: Optional[bool] = None,
    modified_sourcing: Optional[bool] = None,
    modified_specs: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena items. Wildcards (*) supported on string filters.

    Per Arena's GET /items spec, searchable attributes accepted are:
    any, number, name, description, owner.fullName, creator.fullName,
    creator.guid, category.guid, lifecyclePhase.guid, revisionNumber,
    assemblyType, inAssembly, effectiveDateTimeFrom/To, modifiedBom/Files/
    Sourcing/Specs.

    Pagination:
      - Default limit is 100, max single-page is 400 (Arena's cap).
      - Set fetch_all=True to paginate through ALL matching items
        automatically (up to ~20,000 — the safety cap). When fetch_all
        is True, `limit` and `offset` are ignored.

    Note: Arena's API does NOT accept lifecyclePhase.name as a search
    attribute (only .guid). To keep this tool friendly, lifecycle_phase_name
    is resolved to a GUID internally via /settings/items/lifecyclephases.
    The lookup is cached process-wide.

    Args:
        query: Free-text search (Arena's 'any'). This is what the UI's
            main search bar uses — pass plain text without wildcards.
        number: Item number, wildcards supported (e.g. 'WI-*'). The number
            field is auto-wildcarded if you don't include '*' yourself.
        name: Item name (auto-wildcarded).
        description: Item description (auto-wildcarded).
        owner_full_name: Item owner's full name (auto-wildcarded).
        creator_full_name: Item creator's full name (auto-wildcarded).
        creator_guid: Item creator's user GUID.
        category_guid: Filter by item category.
        lifecycle_phase_name: Human-readable phase name (e.g. 'RELEASED',
            'In Design'). Resolved to GUID internally.
        revision_number: Exact revision (e.g. '16', 'B').
        assembly_type: TOP_LEVEL_ASSEMBLY | ASSEMBLY | NOT_AN_ASSEMBLY.
        in_assembly: True returns only items that appear on at least one BOM.
        effective_from: ISO-8601 Zulu, items effective on/after this date.
        effective_to: ISO-8601 Zulu, items effective on/before this date.
        modified_bom / modified_files / modified_sourcing / modified_specs:
            True returns items with working-revision changes in that view.
        limit: Single-page result size (1-400). Ignored if fetch_all=True.
        offset: Starting offset for pagination. Ignored if fetch_all=True.
        fetch_all: If True, paginate through all results and return them
            combined. Bypasses limit/offset.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query  # 'any' ignores wildcards per spec
    if number: base_params["number"] = _wildcard(number)
    if name: base_params["name"] = _wildcard(name)
    if description: base_params["description"] = _wildcard(description)
    if owner_full_name: base_params["owner.fullName"] = _wildcard(owner_full_name)
    if creator_full_name: base_params["creator.fullName"] = _wildcard(creator_full_name)
    if creator_guid: base_params["creator.guid"] = creator_guid
    if category_guid: base_params["category.guid"] = category_guid
    if revision_number: base_params["revisionNumber"] = revision_number  # exact match, no wildcard
    if assembly_type: base_params["assemblyType"] = assembly_type
    if in_assembly is not None: base_params["inAssembly"] = str(in_assembly).lower()
    if effective_from: base_params["effectiveDateTimeFrom"] = effective_from
    if effective_to: base_params["effectiveDateTimeTo"] = effective_to
    if modified_bom is not None: base_params["modifiedBom"] = str(modified_bom).lower()
    if modified_files is not None: base_params["modifiedFiles"] = str(modified_files).lower()
    if modified_sourcing is not None: base_params["modifiedSourcing"] = str(modified_sourcing).lower()
    if modified_specs is not None: base_params["modifiedSpecs"] = str(modified_specs).lower()

    # Resolve lifecycle phase name → guid (Arena rejects lifecyclePhase.name)
    if lifecycle_phase_name:
        phase_guid = _resolve_lifecycle_phase_guid(lifecycle_phase_name)
        if phase_guid:
            base_params["lifecyclePhase.guid"] = phase_guid
        else:
            return {
                "error": True,
                "reason": "unknown_lifecycle_phase",
                "message": (
                    f"No item lifecycle phase named {lifecycle_phase_name!r} "
                    f"in /settings/items/lifecyclephases. Use list_item_lifecycle_phases "
                    f"to see valid names."
                ),
            }

    if fetch_all:
        return _paginate_get("/items", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/items", params=base_params)

@mcp.tool()
def get_item(guid: str) -> dict[str, Any]:
    """Get full details of a single Arena item by GUID."""
    return _arena_get(f"/items/{guid}", params={"includeEmptyAdditionalAttributes": "true"})

@mcp.tool()
def get_item_where_used(guid: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """Get the parent assemblies that contain this item (where-used)."""
    return _arena_get(f"/items/{guid}/whereused",
                      params={"limit": min(max(limit, 1), 200), "offset": max(offset, 0)})

@mcp.tool()
def get_item_revisions(guid: str) -> dict[str, Any]:
    """List ALL revisions of an item with the effecting change embedded per rev.

    This is THE endpoint for reproducing Arena's revision-history dropdown
    (the "»18 - ECO-000011" display). Each entry in results includes:

      - guid:            GUID of THAT specific revision (different per rev,
                         so each rev is essentially a different Arena object).
                         Pass this guid to get_item_files / get_item_bom /
                         get_item to inspect that historical revision's state.
      - number:          Revision string ('16', '01', 'B', etc.)
      - status:          0=WORKING, 1=EFFECTIVE, 2=SUPERSEDED. Use this to
                         identify the current canonical rev (status=1).
      - change:          { number, effectiveDateTime, creationDateTime }
                         The change order (ECO/DEV/etc.) that released
                         this rev. For the WORKING rev (status=0) this may
                         be sparsely populated since it isn't bound to a
                         change yet.
      - lifecyclePhase:  { guid, name } as of this revision.
      - supersededDateTime: When this rev was superseded by a newer one,
                            or null if it's the current effective rev.

    Note: pass ANY of the item's revision GUIDs as input — Arena returns
    the full revision chain regardless of which specific rev you pass.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/revisions")

@mcp.tool()
def get_item_history(guid: str) -> dict[str, Any]:
    """Return the audit history of an item (Items > History > General subview).

    Each entry includes: action, date, user, property, originalValue,
    newValue, and the revision the change applied to.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(
        f"/items/{guid}/history",
        params={"includeEmptyAdditionalAttributes": "true"},
    )

@mcp.tool()
def get_item_future_changes(guid: str) -> dict[str, Any]:
    """List pending (future) changes that may affect this item.

    These are changes (typically OPEN/SUBMITTED) that have the item as
    an affected object but aren't yet effective. Useful for spotting
    "this SOP has an ECO in flight" without manually searching changes.

    Each entry includes change.guid, change.number, change.title,
    change.creationDateTime, change.effectivityType.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/futurechanges")

@mcp.tool()
def get_item_quality_processes(guid: str) -> dict[str, Any]:
    """List quality processes that reference this item (item's Quality tab).

    Returns one row per attachment, NOT per unique QP. If a CAPA
    references the item on multiple steps, you'll see multiple rows for
    the same CAPA — same as the Arena UI's Quality tab.

    Each entry includes the QP's guid, number, name, template,
    owner, status, and dates. To dedupe by QP, group results by guid
    client-side.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/quality")

@mcp.tool()
def get_item_training_plans(guid: str) -> dict[str, Any]:
    """List training plans that include this item (item's Training tab).

    Critical for QMS audits — answers "who needs to be trained on this
    SOP/WI?" Each entry includes training plan guid, number, name,
    training manager, and status.

    Training is commonly attached at the ITEM level (e.g. a document
    number + rev), NOT at the file level. So if you want "training plans for
    this document", use this tool on the item GUID, not on the file GUID.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/trainingplans")

@mcp.tool()
def get_item_training_records(guid: str) -> dict[str, Any]:
    """List training records associated with this item.

    Training records track individual user completions for a given
    training plan. Use this to answer "has anyone completed training
    on this item?" — though typically training records are queried
    via the training plan, not via the item directly.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/trainingrecords")

@mcp.tool()
def get_item_tickets(guid: str) -> dict[str, Any]:
    """List tickets / requests that reference this item.

    Tickets (also called Requests in Arena) are typically complaints,
    feedback, or design requests. They're often the entry point into
    a CAPA chain. Use this to trace "what complaint surfaced this part?"

    Each entry includes the ticket/request guid, number, title, status,
    creator, etc.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/tickets")

@mcp.tool()
def get_item_thumbnail(
    guid: str,
    max_size_bytes: int = 5 * 1024 * 1024,
) -> dict[str, Any]:
    """Download an item's thumbnail image as base64-encoded bytes.

    Items can have a thumbnail image (typically a small JPG/PNG of the
    part). Returns the image bytes the same way get_file_content does
    — base64-encoded in a JSON envelope so the MCP transport can carry it.

    Returns an empty error if the item has no thumbnail.

    Args:
        guid: GUID of any revision of the item.
        max_size_bytes: Reject downloads larger than this. Default 5 MB.
    """
    return _request_bytes(
        f"/items/{guid}/image/content",
        max_size_bytes=max_size_bytes,
    )

@mcp.tool()
def get_item_training_plan(
    item_guid: str,
    tp_ref_guid: str,
) -> dict[str, Any]:
    """Get a single item ↔ training plan reference by GUID."""
    return _arena_get(f"/items/{item_guid}/trainingplans/{tp_ref_guid}")

@mcp.tool()
def get_item_training_record(
    item_guid: str,
    record_guid: str,
) -> dict[str, Any]:
    """Get a single training record associated with an item.

    Training records on items show which users completed training on
    which specific revision of the item.
    """
    return _arena_get(f"/items/{item_guid}/trainingrecords/{record_guid}")

@mcp.tool()
def list_item_attributes() -> dict[str, Any]:
    """List all item-level custom attribute definitions in the workspace.

    Returns the workspace-wide schema for item custom attributes —
    field names, GUIDs, field types, dropdown options. Use these
    attribute GUIDs as search filters in search_items.
    """
    return _arena_get("/settings/items/attributes")

@mcp.tool()
def get_item_attribute(attribute_guid: str) -> dict[str, Any]:
    """Get a single item attribute definition by GUID."""
    return _arena_get(f"/settings/items/attributes/{attribute_guid}")

@mcp.tool()
def list_item_attribute_groups() -> dict[str, Any]:
    """List item attribute groups (visual groupings of attributes in the UI).

    Attribute groups organize the Item edit form into named sections
    (e.g. "Electrical", "Mechanical", "Compliance"). Each group
    contains an ordered list of attribute GUIDs.
    """
    return _arena_get("/settings/items/attributegroups")

@mcp.tool()
def list_item_category_attributes(category_guid: str) -> dict[str, Any]:
    """List custom attributes for a specific item category.

    Item categories (Standard Operating Procedure, Drawing, Assembly,
    PCBA, etc.) can have their own category-specific attribute schemas
    on top of the workspace-wide attribute list.

    Args:
        category_guid: Item category GUID (from list_item_categories).
    """
    return _arena_get(f"/settings/items/categories/{category_guid}/attributes")

@mcp.tool()
def get_item_category(category_guid: str) -> dict[str, Any]:
    """Get full details of a single item category."""
    return _arena_get(f"/settings/items/categories/{category_guid}")

@mcp.tool()
def list_item_number_reservations() -> dict[str, Any]:
    """List reserved item number ranges in the workspace.

    Some workspaces reserve number ranges for specific product lines
    or specific users (e.g. "100-00000 through 199-99999 reserved for
    R&D, auto-assigned"). Returns the reservation records.
    """
    return _arena_get("/settings/items/numberreservations")

@mcp.tool()
def get_item_number_format(format_guid: str) -> dict[str, Any]:
    """Get a single item number format by GUID.

    Returns format pattern, prefix, sequence counter, and which item
    categories use this format.
    """
    return _arena_get(f"/settings/items/numberformats/{format_guid}")

@mcp.tool()
def list_item_requirements() -> dict[str, Any]:
    """List compliance requirements available for items at the workspace level.

    Workspace-level list of regulatory regimes (RoHS, REACH, Prop 65,
    etc.). Each item can declare compliance status against any of these
    via get_item_compliance.
    """
    return _arena_get("/settings/items/requirements")

@mcp.tool()
def get_item_requirement(requirement_guid: str) -> dict[str, Any]:
    """Get a single item compliance requirement definition by GUID."""
    return _arena_get(f"/settings/items/requirements/{requirement_guid}")

@mcp.tool()
def create_item(
    name: str,
    category_guid: str,
    number_format_guid: Optional[str] = None,
    number_format_fields: Optional[list[dict[str, Any]]] = None,
    description: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new Arena item.

    POST /items. category_guid drives numbering + attributes; if the category
    has a single default number sequence, number_format_guid/fields can be
    omitted. Otherwise (e.g. a shared multi-prefix format like "Document",
    which covers FO/WI/FTP/PL/RE/etc. off one picklist) you must pass:
      number_format_guid: the numberFormat's own guid (see
        list_item_number_formats / get_item_number_format).
      number_format_fields: [{"guid": <picklist field guid>, "value": "FO"}]
        for each field the format requires (e.g. the prefix code field).
    Per Arena's REST API docs, this nests as body.numberFormat =
    {"guid": ..., "fields": [...]}. Note: "numberSequencePrefix" is NOT a
    valid field on /items (that belongs to /changes and
    /settings/items/numberreservations, not this endpoint).
    """
    body: dict[str, Any] = {"name": name, "category": {"guid": category_guid}}
    if number_format_guid:
        body["numberFormat"] = {
            "guid": number_format_guid,
            "fields": number_format_fields or [],
        }
    if description is not None:
        body["description"] = description
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/items", "body": body}
    return _arena_post("/items", body=body)

@mcp.tool()
def update_item(
    guid: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    owner_full_name: Optional[str] = None,
    owner_guid: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False,
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update an item's scalar fields + additionalAttributes.

    PUT /items/<GUID>. Rev-controlled fields (BOM, files, etc.) update
    through their own endpoints. setnull=True appends ?setnull=true.
    """
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if owner_full_name is not None:
        body["owner"] = {"fullName": owner_full_name}
    elif owner_guid is not None:
        body["owner"] = {"guid": owner_guid}
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if not body:
        return {"error": True, "message": "No fields provided to update."}
    path = f"/items/{guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    snap: dict[str, Any] = {}
    if snapshot_first:
        cur = _arena_get(f"/items/{guid}")
        if isinstance(cur, dict) and not cur.get("error"):
            snap = _write_snapshot(
                label=f"pre-update item {cur.get('number', guid)}",
                kind="item_update",
                captures=[{"endpoint": f"/items/{guid}", "data": cur}],
            )
    r = _arena_put(path, body=body)
    return {"snapshot": snap, "result": r} if snap else r

@mcp.tool()
def delete_item(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /items/<GUID>. Arena refuses if the item is referenced anywhere."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{guid}"}
    return _arena_delete(f"/items/{guid}")

@mcp.tool()
def create_item_thumbnail_from_files_view(
    guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """Set item thumbnail from a file already in the item's Files view.

    POST /items/<GUID>/image with body {file: {guid}}.
    """
    body = {"file": {"guid": file_assoc_guid}}
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/items/{guid}/image", "body": body}
    return _arena_post(f"/items/{guid}/image", body=body)

@mcp.tool()
def delete_item_thumbnail(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /items/<GUID>/image — remove the item's thumbnail."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{guid}/image"}
    return _arena_delete(f"/items/{guid}/image")

@mcp.tool()
def change_item_lifecycle_phase(
    item_guid: str,
    to_lifecycle_phase_guid: str,
    revision_number: Optional[str] = None,
    proceed_on_notice: bool = True,
    notes: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Move an item to a different lifecycle phase without a change order.

    POST /items/lifecyclephasechanges. Requires appropriate permissions;
    normal-flow phase changes should go through an ECO instead.
    """
    body: dict[str, Any] = {
        "item": {"guid": item_guid},
        "toLifecyclePhase": {"guid": to_lifecycle_phase_guid},
        "proceedOnNotice": proceed_on_notice,
    }
    if revision_number:
        body["revisionNumber"] = revision_number
    if notes:
        body["notes"] = notes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/items/lifecyclephasechanges", "body": body}
    return _arena_post("/items/lifecyclephasechanges", body=body)

@mcp.tool()
def reserve_item_number(
    number_sequence_prefix: str, quantity: int = 1, dry_run: bool = False
) -> dict[str, Any]:
    """Reserve N item numbers on a sequence prefix (e.g. "830-").

    POST /settings/items/numberreservations.
    """
    body = {
        "numberSequencePrefix": {"value": number_sequence_prefix},
        "quantity": quantity,
    }
    if dry_run:
        return {"dry_run": True, "would_post_to": "/settings/items/numberreservations", "body": body}
    return _arena_post("/settings/items/numberreservations", body=body)

@mcp.tool()
def cancel_item_number_reservation(
    reservation_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /settings/items/numberreservations/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/settings/items/numberreservations/{reservation_guid}"}
    return _arena_delete(f"/settings/items/numberreservations/{reservation_guid}")

