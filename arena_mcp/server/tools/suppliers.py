from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _wildcard, _paginate_get

__all__ = [
    "search_suppliers",
    "get_supplier",
    "get_supplier_addresses",
    "get_supplier_address",
    "get_supplier_phone_numbers",
    "get_supplier_phone_number",
    "get_supplier_files",
    "get_supplier_file",
    "get_supplier_quality_processes",
    "get_supplier_quality_process",
    "list_supplier_attributes",
    "list_supplier_approval_statuses",
    "create_supplier",
    "update_supplier",
    "delete_supplier",
    "add_supplier_address",
    "update_supplier_address",
    "delete_supplier_address",
    "add_supplier_phone",
    "update_supplier_phone",
    "delete_supplier_phone",
    "add_file_to_supplier",
    "remove_file_from_supplier",
]


@mcp.tool()
def search_suppliers(
    query: Optional[str] = None,
    name: Optional[str] = None,
    supplier_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena suppliers (vendor / manufacturer profiles).

    Per Arena's GET /suppliers spec, only `any`, `name`, and `supplierId`
    are searchable filters (besides custom attributes by GUID). Other
    visible fields (approvalStatus, description, etc.) are NOT searchable.

    Pagination:
      - Default limit 100, max single-page 400.
      - Set fetch_all=True to paginate through all suppliers.

    Args:
        query: Free-text search (Arena's 'any', UI-bar equivalent).
        name: Supplier name, auto-wildcarded if no '*' present.
        supplier_id: Short ID (e.g. 'Adaptive'), auto-wildcarded.
        limit: Single-page size (1-400). Ignored if fetch_all=True.
        offset: Pagination offset. Ignored if fetch_all=True.
        fetch_all: True to paginate through all results automatically.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query
    if name: base_params["name"] = _wildcard(name)
    if supplier_id: base_params["supplierId"] = _wildcard(supplier_id)

    if fetch_all:
        return _paginate_get("/suppliers", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/suppliers", params=base_params)

@mcp.tool()
def get_supplier(guid: str) -> dict[str, Any]:
    """Get full profile of a single supplier by GUID.

    Returns name, supplierId, approvalStatus, description, accountNumber,
    website, creator, and custom attributes. Sub-collections (addresses,
    phone numbers, files, items, quality processes) require separate calls.
    """
    return _arena_get(f"/suppliers/{guid}")

@mcp.tool()
def get_supplier_addresses(guid: str) -> dict[str, Any]:
    """List all addresses on file for a supplier.

    Each entry includes address lines, city, region, postal code, country,
    and the address type (billing, shipping, etc.) if set.
    """
    return _arena_get(f"/suppliers/{guid}/addresses")

@mcp.tool()
def get_supplier_address(supplier_guid: str, address_guid: str) -> dict[str, Any]:
    """Get a single supplier address by GUID."""
    return _arena_get(f"/suppliers/{supplier_guid}/addresses/{address_guid}")

@mcp.tool()
def get_supplier_phone_numbers(guid: str) -> dict[str, Any]:
    """List all phone numbers on file for a supplier."""
    return _arena_get(f"/suppliers/{guid}/phonenumbers")

@mcp.tool()
def get_supplier_phone_number(supplier_guid: str, phone_guid: str) -> dict[str, Any]:
    """Get a single supplier phone number by GUID."""
    return _arena_get(f"/suppliers/{supplier_guid}/phonenumbers/{phone_guid}")

@mcp.tool()
def get_supplier_files(guid: str) -> dict[str, Any]:
    """List files attached to a supplier.

    Files attached at the supplier level are typically certificates of
    insurance, ISO certifications, audit reports, master agreements,
    quality manuals. NOT the same as files attached to specific supplier
    items (datasheets / CoCs) — use get_supplier_item_files for those.
    """
    return _arena_get(f"/suppliers/{guid}/files")

@mcp.tool()
def get_supplier_file(supplier_guid: str, file_assoc_guid: str) -> dict[str, Any]:
    """Get a single supplier ↔ file association by GUID."""
    return _arena_get(f"/suppliers/{supplier_guid}/files/{file_assoc_guid}")

@mcp.tool()
def get_supplier_quality_processes(guid: str) -> dict[str, Any]:
    """List quality processes that reference this supplier.

    Examples: SCAR (Supplier Corrective Action Request), supplier audits,
    re-qualification CAPAs. Each entry has the QP's guid, number, name.
    """
    return _arena_get(f"/suppliers/{guid}/quality")

@mcp.tool()
def get_supplier_quality_process(supplier_guid: str, qp_ref_guid: str) -> dict[str, Any]:
    """Get a single supplier ↔ quality-process reference by GUID."""
    return _arena_get(f"/suppliers/{supplier_guid}/quality/{qp_ref_guid}")

@mcp.tool()
def list_supplier_attributes() -> dict[str, Any]:
    """List the supplier object's custom attributes in the workspace.

    Returns the attribute schema for suppliers — names, GUIDs, field
    types, dropdown options. Use the attribute GUIDs to pass custom
    filters to search_suppliers.
    """
    return _arena_get("/settings/suppliers/attributes")

@mcp.tool()
def list_supplier_approval_statuses() -> dict[str, Any]:
    """List the supplier approval statuses configured in the workspace.

    Typical values: Unrated, Approved, Conditionally Approved, Disapproved,
    Discontinued. Each entry has guid and name. Used as the approvalStatus
    field on suppliers.
    """
    return _arena_get("/settings/suppliers/approvalstatuses")

@mcp.tool()
def create_supplier(
    name: str, supplier_id: Optional[str] = None,
    description: Optional[str] = None, website: Optional[str] = None,
    approval_status: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /suppliers."""
    body: dict[str, Any] = {"name": name}
    if supplier_id is not None:
        body["supplierId"] = supplier_id
    if description is not None:
        body["description"] = description
    if website is not None:
        body["website"] = website
    if approval_status is not None:
        body["approvalStatus"] = approval_status
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/suppliers", "body": body}
    return _arena_post("/suppliers", body=body)

@mcp.tool()
def update_supplier(
    guid: str, name: Optional[str] = None, supplier_id: Optional[str] = None,
    description: Optional[str] = None, website: Optional[str] = None,
    approval_status: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False, snapshot_first: bool = True, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /suppliers/<GUID>."""
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if supplier_id is not None:
        body["supplierId"] = supplier_id
    if description is not None:
        body["description"] = description
    if website is not None:
        body["website"] = website
    if approval_status is not None:
        body["approvalStatus"] = approval_status
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/suppliers/{guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    snap: dict[str, Any] = {}
    if snapshot_first:
        cur = _arena_get(f"/suppliers/{guid}")
        if isinstance(cur, dict) and not cur.get("error"):
            snap = _write_snapshot(
                label=f"pre-update supplier {cur.get('name', guid)}",
                kind="supplier_update",
                captures=[{"endpoint": f"/suppliers/{guid}", "data": cur}],
            )
    r = _arena_put(path, body=body)
    return {"snapshot": snap, "result": r} if snap else r

@mcp.tool()
def delete_supplier(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /suppliers/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/suppliers/{guid}"}
    return _arena_delete(f"/suppliers/{guid}")

@mcp.tool()
def add_supplier_address(
    supplier_guid: str, address_body: dict[str, Any], primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /suppliers/<GUID>/addresses.

    address_body is the "address" sub-object per spec: {label, address1,
    address2, city, state, "Country/Region", province, postalCode}.
    """
    body = {"address": address_body, "primary": primary}
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/suppliers/{supplier_guid}/addresses", "body": body}
    return _arena_post(f"/suppliers/{supplier_guid}/addresses", body=body)

@mcp.tool()
def update_supplier_address(
    supplier_guid: str, address_guid: str, address_body: dict[str, Any],
    primary: Optional[bool] = None, setnull: bool = False, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /suppliers/<GUID>/addresses/<GUID>."""
    body: dict[str, Any] = {"address": address_body}
    if primary is not None:
        body["primary"] = primary
    path = f"/suppliers/{supplier_guid}/addresses/{address_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_supplier_address(
    supplier_guid: str, address_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /suppliers/<GUID>/addresses/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/suppliers/{supplier_guid}/addresses/{address_guid}"}
    return _arena_delete(f"/suppliers/{supplier_guid}/addresses/{address_guid}")

@mcp.tool()
def add_supplier_phone(
    supplier_guid: str, phone_body: dict[str, Any], primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /suppliers/<GUID>/phonenumbers."""
    body = {"phoneNumber": phone_body, "primary": primary}
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/suppliers/{supplier_guid}/phonenumbers", "body": body}
    return _arena_post(f"/suppliers/{supplier_guid}/phonenumbers", body=body)

@mcp.tool()
def update_supplier_phone(
    supplier_guid: str, phone_guid: str, phone_body: dict[str, Any],
    primary: Optional[bool] = None, setnull: bool = False, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /suppliers/<GUID>/phonenumbers/<GUID>."""
    body: dict[str, Any] = {"phoneNumber": phone_body}
    if primary is not None:
        body["primary"] = primary
    path = f"/suppliers/{supplier_guid}/phonenumbers/{phone_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_supplier_phone(
    supplier_guid: str, phone_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /suppliers/<GUID>/phonenumbers/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/suppliers/{supplier_guid}/phonenumbers/{phone_guid}"}
    return _arena_delete(f"/suppliers/{supplier_guid}/phonenumbers/{phone_guid}")

@mcp.tool()
def add_file_to_supplier(
    supplier_guid: str, file_guid: str,
    latest_edition_association: bool = True, primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /suppliers/<GUID>/files."""
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/suppliers/{supplier_guid}/files", "body": body}
    return _arena_post(f"/suppliers/{supplier_guid}/files", body=body)

@mcp.tool()
def remove_file_from_supplier(
    supplier_guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /suppliers/<GUID>/files/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/suppliers/{supplier_guid}/files/{file_assoc_guid}"}
    return _arena_delete(f"/suppliers/{supplier_guid}/files/{file_assoc_guid}")

