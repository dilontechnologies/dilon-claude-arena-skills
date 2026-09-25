from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete

__all__ = [
    "get_item_bom",
    "get_item_bom_line",
    "get_item_bom_settings",
    "list_item_bom_attributes",
    "get_item_bom_substitutes",
    "get_item_bom_substitute",
    "create_bom_line",
    "update_bom_line",
    "delete_bom_line",
    "update_bom_settings",
    "create_bom_substitute",
    "update_bom_substitute",
    "delete_bom_substitute",
]


@mcp.tool()
def get_item_bom(guid: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """Get the Bill of Materials (BOM) for an Arena item."""
    return _arena_get(f"/items/{guid}/bom",
                      params={"limit": min(max(limit, 1), 200), "offset": max(offset, 0)})

@mcp.tool()
def get_item_bom_line(
    item_guid: str,
    bom_line_guid: str,
    include_substitutes: bool = False,
) -> dict[str, Any]:
    """Get a single BOM line of an item by GUID.

    Use after get_item_bom to inspect one BOM line in detail (quantity,
    reference designator, unit of measure, child item revision rules).

    Args:
        item_guid: Parent item GUID.
        bom_line_guid: BOM line GUID from get_item_bom results.
        include_substitutes: If True, include any approved alternate
            parts (BOM substitutes) configured for this line.
    """
    params: dict[str, Any] = {}
    if include_substitutes:
        params["includeBomSubstitutes"] = "true"
    return _arena_get(
        f"/items/{item_guid}/bom/{bom_line_guid}",
        params=params or None,
    )

@mcp.tool()
def get_item_bom_settings(item_guid: str) -> dict[str, Any]:
    """Get an item's BOM view settings.

    Returns BOM display preferences for the item — which columns are
    shown, sort order, and any custom view configuration.
    """
    return _arena_get(f"/items/{item_guid}/bom/settings")

@mcp.tool()
def list_item_bom_attributes() -> dict[str, Any]:
    """List BOM-line custom attribute definitions.

    These are attributes attached to BOM lines (the parent-child
    relationship), distinct from item attributes attached to the
    items themselves. Examples: "Optional", "Ref Des", "DNI".
    """
    return _arena_get("/settings/items/bom/attributes")

@mcp.tool()
def get_item_bom_substitutes(
    item_guid: str, bom_line_guid: str
) -> dict[str, Any]:
    """List substitute parts for a single BOM line.

    Substitutes are alternate items that can replace the primary BOM child
    in manufacturing (e.g., same-spec resistor from a different supplier).
    Spec endpoint: GET /items/{guid}/bom/{guid}/substitutes
    """
    return _arena_get(
        f"/items/{item_guid}/bom/{bom_line_guid}/substitutes"
    )

@mcp.tool()
def get_item_bom_substitute(
    item_guid: str, bom_line_guid: str, substitute_guid: str
) -> dict[str, Any]:
    """Get a single BOM substitute by GUID."""
    return _arena_get(
        f"/items/{item_guid}/bom/{bom_line_guid}/substitutes/{substitute_guid}"
    )

@mcp.tool()
def create_bom_line(
    parent_item_guid: str,
    child_item_guid: str,
    quantity: float,
    ref_des: Optional[str] = None,
    notes: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add a child line to a parent item's BOM.

    POST /items/<parent>/bom.
    """
    body: dict[str, Any] = {
        "item": {"guid": child_item_guid},
        "quantity": quantity,
    }
    if ref_des:
        body["refDes"] = ref_des
    if notes:
        body["notes"] = notes
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/items/{parent_item_guid}/bom", "body": body}
    return _arena_post(f"/items/{parent_item_guid}/bom", body=body)

@mcp.tool()
def update_bom_line(
    parent_item_guid: str,
    bom_line_guid: str,
    quantity: Optional[float] = None,
    ref_des: Optional[str] = None,
    notes: Optional[str] = None,
    setnull: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /items/<parent>/bom/<line>."""
    body: dict[str, Any] = {}
    if quantity is not None:
        body["quantity"] = quantity
    if ref_des is not None:
        body["refDes"] = ref_des
    if notes is not None:
        body["notes"] = notes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/items/{parent_item_guid}/bom/{bom_line_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_bom_line(
    parent_item_guid: str, bom_line_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /items/<parent>/bom/<line>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{parent_item_guid}/bom/{bom_line_guid}"}
    return _arena_delete(f"/items/{parent_item_guid}/bom/{bom_line_guid}")

@mcp.tool()
def update_bom_settings(
    parent_item_guid: str,
    settings_body: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /items/<parent>/bom/settings — set BOM-level configuration.

    Pass settings_body per spec (see GET /items/<G>/bom/settings response
    shape for the fields this endpoint accepts).
    """
    if dry_run:
        return {"dry_run": True, "would_put_to": f"/items/{parent_item_guid}/bom/settings",
                "body": settings_body}
    return _arena_put(f"/items/{parent_item_guid}/bom/settings", body=settings_body)

@mcp.tool()
def create_bom_substitute(
    parent_item_guid: str,
    bom_line_guid: str,
    substitute_item_guid: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /items/<parent>/bom/<line>/substitutes."""
    body = {"item": {"guid": substitute_item_guid}}
    path = f"/items/{parent_item_guid}/bom/{bom_line_guid}/substitutes"
    if dry_run:
        return {"dry_run": True, "would_post_to": path, "body": body}
    return _arena_post(path, body=body)

@mcp.tool()
def update_bom_substitute(
    parent_item_guid: str,
    bom_line_guid: str,
    substitute_guid: str,
    substitute_item_guid: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /items/<parent>/bom/<line>/substitutes/<sub>."""
    body = {"item": {"guid": substitute_item_guid}}
    path = f"/items/{parent_item_guid}/bom/{bom_line_guid}/substitutes/{substitute_guid}"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_bom_substitute(
    parent_item_guid: str,
    bom_line_guid: str,
    substitute_guid: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """DELETE /items/<parent>/bom/<line>/substitutes/<sub>."""
    path = f"/items/{parent_item_guid}/bom/{bom_line_guid}/substitutes/{substitute_guid}"
    if dry_run:
        return {"dry_run": True, "would_delete": path}
    return _arena_delete(path)

