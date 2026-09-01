from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _wildcard, _paginate_get, _request_bytes, _arena_post_multipart

__all__ = [
    "search_supplier_items",
    "get_supplier_item",
    "get_supplier_item_thumbnail",
    "get_supplier_item_compliance",
    "get_supplier_item_compliance_record",
    "get_supplier_item_files",
    "get_supplier_item_file",
    "get_supplier_item_file_content",
    "get_supplier_item_quality_processes",
    "get_supplier_item_quality_process",
    "get_supplier_item_sourcing",
    "get_supplier_item_source",
    "list_supplier_item_attributes",
    "list_supplier_item_compliance_requirements",
    "create_supplier_item",
    "update_supplier_item",
    "delete_supplier_item",
    "add_existing_file_to_supplier_item",
    "upload_supplier_item_file_content",
    "update_supplier_item_file_association",
    "remove_file_from_supplier_item",
]


@mcp.tool()
def search_supplier_items(
    query: Optional[str] = None,
    name: Optional[str] = None,
    number: Optional[str] = None,
    supplier_name: Optional[str] = None,
    supplier_guid: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena supplier items (vendor-side catalog SKUs).

    A supplier item is a specific listing — e.g. "Digi-Key part number
    296-1382-1-ND, an SN74HC04N" — distinct from your internal item.
    Multiple supplier items can source the same Arena item (multi-sourcing).

    Per Arena's GET /supplieritems spec, searchable filters: any, name,
    number, supplier.name, supplier.guid (plus custom attributes by GUID).

    Pagination:
      - Default limit 100, max single-page 400.
      - Set fetch_all=True to paginate through all supplier items.

    Args:
        query: Free-text search (Arena's 'any', UI-bar equivalent).
        name: Supplier item name (auto-wildcarded).
        number: Supplier item number / part number (auto-wildcarded).
        supplier_name: Supplier name (auto-wildcarded), filters items
            offered by suppliers whose name matches.
        supplier_guid: Filter by exact supplier GUID.
        limit: Single-page size (1-400). Ignored if fetch_all=True.
        offset: Pagination offset. Ignored if fetch_all=True.
        fetch_all: True to paginate through all results automatically.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query
    if name: base_params["name"] = _wildcard(name)
    if number: base_params["number"] = _wildcard(number)
    if supplier_name: base_params["supplier.name"] = _wildcard(supplier_name)
    if supplier_guid: base_params["supplier.guid"] = supplier_guid

    if fetch_all:
        return _paginate_get("/supplieritems", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/supplieritems", params=base_params)

@mcp.tool()
def get_supplier_item(guid: str) -> dict[str, Any]:
    """Get full profile of a single supplier item by GUID.

    Returns name, number, supplier (guid + name), description, lifecycle
    phase if applicable, and all custom attributes (the "specs" you'd see
    in the UI's Specs tab — Arena exposes them on the main object rather
    than a separate /specs endpoint).
    """
    return _arena_get(f"/supplieritems/{guid}")

@mcp.tool()
def get_supplier_item_thumbnail(
    guid: str,
    max_size_bytes: int = 5 * 1024 * 1024,
) -> dict[str, Any]:
    """Download a supplier item's thumbnail image as base64-encoded bytes.

    Same pattern as get_item_thumbnail / get_file_content — base64-encoded
    in a JSON envelope. Returns an error if the supplier item has no
    thumbnail.

    Args:
        guid: Supplier item GUID.
        max_size_bytes: Reject downloads larger than this. Default 5 MB.
    """
    return _request_bytes(
        f"/supplieritems/{guid}/image/content",
        max_size_bytes=max_size_bytes,
    )

@mcp.tool()
def get_supplier_item_compliance(guid: str) -> dict[str, Any]:
    """List compliance declarations for a supplier item.

    Returns the supplier-item-level compliance records (RoHS, REACH,
    California Prop 65, etc.) with declared status and supporting
    documentation. Each entry has the requirement guid, name, declared
    status, and supporting file references.
    """
    return _arena_get(f"/supplieritems/{guid}/compliance")

@mcp.tool()
def get_supplier_item_compliance_record(
    supplier_item_guid: str,
    compliance_guid: str,
) -> dict[str, Any]:
    """Get a single supplier-item compliance record by GUID."""
    return _arena_get(
        f"/supplieritems/{supplier_item_guid}/compliance/{compliance_guid}"
    )

@mcp.tool()
def get_supplier_item_files(guid: str) -> dict[str, Any]:
    """List files attached to a supplier item.

    Typical attachments: manufacturer datasheets, certificates of
    conformity (CoCs), declarations of conformity, RoHS/REACH
    declarations, drawings.
    """
    return _arena_get(f"/supplieritems/{guid}/files")

@mcp.tool()
def get_supplier_item_file(
    supplier_item_guid: str,
    file_assoc_guid: str,
) -> dict[str, Any]:
    """Get a single supplier-item ↔ file association by GUID."""
    return _arena_get(
        f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}"
    )

@mcp.tool()
def get_supplier_item_file_content(
    supplier_item_guid: str,
    file_assoc_guid: str,
    max_size_bytes: int = 10 * 1024 * 1024,
) -> dict[str, Any]:
    """Download the content of a file attached to a supplier item.

    Returns base64-encoded bytes in a JSON envelope, same pattern as
    get_file_content. Watch the size cap for MCP transport (~750 KB
    safe).

    Args:
        supplier_item_guid: Supplier item GUID.
        file_assoc_guid: GUID of the file-association record (from
            get_supplier_item_files).
        max_size_bytes: Reject downloads larger than this. Default 10 MB.
    """
    return _request_bytes(
        f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}/content",
        max_size_bytes=max_size_bytes,
    )

@mcp.tool()
def get_supplier_item_quality_processes(guid: str) -> dict[str, Any]:
    """List quality processes that reference this supplier item.

    Typically SCARs, supplier-quality NCMRs, audits, or supplier
    requalification CAPAs.
    """
    return _arena_get(f"/supplieritems/{guid}/quality")

@mcp.tool()
def get_supplier_item_quality_process(
    supplier_item_guid: str,
    qp_ref_guid: str,
) -> dict[str, Any]:
    """Get a single supplier-item ↔ quality-process reference by GUID."""
    return _arena_get(
        f"/supplieritems/{supplier_item_guid}/quality/{qp_ref_guid}"
    )

@mcp.tool()
def get_supplier_item_sourcing(guid: str) -> dict[str, Any]:
    """List source relationships from a supplier item to Arena items.

    Reverse direction of get_item_sourcing — instead of "what supplier
    items source this Arena item?" this is "which Arena items does this
    supplier item source?" Useful for impact analysis on a supplier item
    (e.g. when a vendor discontinues a part: which of our items will be
    affected?).

    Source-relationship GUIDs returned here are the SAME as those
    returned by get_item_sourcing for the matching items — they're two
    sides of the same edge.
    """
    return _arena_get(f"/supplieritems/{guid}/sourcing")

@mcp.tool()
def get_supplier_item_source(
    supplier_item_guid: str,
    source_guid: str,
) -> dict[str, Any]:
    """Get a single supplier-item ↔ item source relationship by GUID."""
    return _arena_get(
        f"/supplieritems/{supplier_item_guid}/sourcing/{source_guid}"
    )

@mcp.tool()
def list_supplier_item_attributes() -> dict[str, Any]:
    """List the supplier-item object's custom attributes in the workspace.

    Returns the attribute schema for supplier items.
    """
    return _arena_get("/settings/supplieritems/attributes")

@mcp.tool()
def list_supplier_item_compliance_requirements() -> dict[str, Any]:
    """List the compliance requirements available for supplier items.

    Workspace-level list of regulatory regimes (RoHS, REACH, California
    Prop 65, conflict minerals, etc.). Each requirement gets associated
    with individual supplier items via get_supplier_item_compliance.
    """
    return _arena_get("/settings/supplieritems/requirements")

@mcp.tool()
def create_supplier_item(
    name: str, number: str, supplier_guid: str,
    description: Optional[str] = None, off_the_shelf: Optional[bool] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /supplieritems."""
    body: dict[str, Any] = {
        "name": name, "number": number, "supplier": {"guid": supplier_guid},
    }
    if description is not None:
        body["description"] = description
    if off_the_shelf is not None:
        body["offTheShelf"] = off_the_shelf
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/supplieritems", "body": body}
    return _arena_post("/supplieritems", body=body)

@mcp.tool()
def update_supplier_item(
    guid: str, name: Optional[str] = None, number: Optional[str] = None,
    description: Optional[str] = None, off_the_shelf: Optional[bool] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False, snapshot_first: bool = True, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /supplieritems/<GUID>."""
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if number is not None:
        body["number"] = number
    if description is not None:
        body["description"] = description
    if off_the_shelf is not None:
        body["offTheShelf"] = off_the_shelf
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/supplieritems/{guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    snap: dict[str, Any] = {}
    if snapshot_first:
        cur = _arena_get(f"/supplieritems/{guid}")
        if isinstance(cur, dict) and not cur.get("error"):
            snap = _write_snapshot(
                label=f"pre-update supplier item {cur.get('number', guid)}",
                kind="supplier_item_update",
                captures=[{"endpoint": f"/supplieritems/{guid}", "data": cur}],
            )
    r = _arena_put(path, body=body)
    return {"snapshot": snap, "result": r} if snap else r

@mcp.tool()
def delete_supplier_item(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /supplieritems/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/supplieritems/{guid}"}
    return _arena_delete(f"/supplieritems/{guid}")

@mcp.tool()
def add_existing_file_to_supplier_item(
    supplier_item_guid: str, file_guid: str,
    latest_edition_association: bool = True, primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /supplieritems/<GUID>/files (add existing)."""
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/supplieritems/{supplier_item_guid}/files", "body": body}
    return _arena_post(f"/supplieritems/{supplier_item_guid}/files", body=body)

@mcp.tool()
def upload_supplier_item_file_content(
    supplier_item_guid: str, file_assoc_guid: str, local_path: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /supplieritems/<GUID>/files/<GUID>/content — upload new content."""
    if dry_run:
        return {
            "dry_run": True,
            "would_upload": f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}/content",
            "local_path": local_path,
        }
    return _arena_post_multipart(
        f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}/content", local_path
    )

@mcp.tool()
def update_supplier_item_file_association(
    supplier_item_guid: str, file_assoc_guid: str,
    latest_edition_association: Optional[bool] = None,
    primary: Optional[bool] = None, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /supplieritems/<GUID>/files/<GUID>."""
    body: dict[str, Any] = {}
    if latest_edition_association is not None:
        body["latestEditionAssociation"] = latest_edition_association
    if primary is not None:
        body["primary"] = primary
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def remove_file_from_supplier_item(
    supplier_item_guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /supplieritems/<GUID>/files/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}"}
    return _arena_delete(f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}")

