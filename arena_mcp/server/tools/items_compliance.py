from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete

__all__ = [
    "get_item_compliance",
    "get_item_sourcing",
    "get_item_references",
    "get_item_compliance_requirement",
    "get_item_source",
    "get_item_reference",
    "add_item_compliance_declaration",
    "update_item_compliance",
    "delete_item_compliance",
    "create_item_source",
    "update_item_source",
    "delete_item_source",
    "create_item_reference",
    "update_item_reference",
    "delete_item_reference",
]


@mcp.tool()
def get_item_compliance(guid: str) -> dict[str, Any]:
    """List compliance requirements/declarations for this item.

    Returns compliance records for regulatory regimes the item is
    flagged against (RoHS, REACH, conflict minerals, etc.). Each entry
    includes the compliance regime, declared status (compliant /
    non-compliant / exempt), and supporting documentation.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/compliance")

@mcp.tool()
def get_item_sourcing(guid: str) -> dict[str, Any]:
    """List sourcing relationships (suppliers/manufacturers) for this item.

    Returns source-relationship records linking this item to the
    supplier items / supplier manufacturers it can be purchased from.
    For a multi-source part, you'll get one row per supplier item.

    Each entry includes the supplier-item ref (guid + number),
    supplier name, manufacturer part number, status (preferred /
    alternate / disapproved), and pricing if available.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/sourcing")

@mcp.tool()
def get_item_references(guid: str) -> dict[str, Any]:
    """List item-to-item references (cross-references) for this item.

    Item references are non-BOM relationships between items — e.g.
    "this WI references this Form" or "this SOP supersedes this older
    SOP". Different from BOM (parts that go into the assembly) and
    where-used (assemblies this part is in).

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/items")

@mcp.tool()
def get_item_compliance_requirement(
    item_guid: str,
    requirement_guid: str,
) -> dict[str, Any]:
    """Get a single item compliance record by GUID.

    Use after get_item_compliance to drill into one requirement's full
    detail (declared status, evidence, exemption notes).
    """
    return _arena_get(f"/items/{item_guid}/compliance/{requirement_guid}")

@mcp.tool()
def get_item_source(item_guid: str, source_guid: str) -> dict[str, Any]:
    """Get a single item ↔ supplier-item source relationship by GUID.

    Source-relationship GUID is identical to that returned by
    get_supplier_item_sourcing — they're two sides of the same edge.
    """
    return _arena_get(f"/items/{item_guid}/sourcing/{source_guid}")

@mcp.tool()
def get_item_reference(item_guid: str, ref_guid: str) -> dict[str, Any]:
    """Get a single item-to-item cross-reference by GUID."""
    return _arena_get(f"/items/{item_guid}/items/{ref_guid}")

@mcp.tool()
def add_item_compliance_declaration(
    item_guid: str,
    requirement_guid: str,
    status: str,
    evidence_type: Optional[str] = None,
    mark: Optional[str] = None,
    rationale: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /items/<GUID>/compliance — add a compliance declaration.

    status: COMPLIANT, NONCOMPLIANT, EXEMPT, INDETERMINATE, etc.
    evidence_type: AML_AND_FILES, FILES, INDIRECT, etc.
    """
    body: dict[str, Any] = {
        "requirement": {"guid": requirement_guid},
        "status": status,
    }
    if evidence_type is not None:
        body["evidenceType"] = evidence_type
    if mark is not None:
        body["mark"] = mark
    if rationale is not None:
        body["rationale"] = rationale
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/items/{item_guid}/compliance", "body": body}
    return _arena_post(f"/items/{item_guid}/compliance", body=body)

@mcp.tool()
def update_item_compliance(
    item_guid: str,
    compliance_guid: str,
    status: Optional[str] = None,
    evidence_type: Optional[str] = None,
    mark: Optional[str] = None,
    rationale: Optional[str] = None,
    setnull: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /items/<GUID>/compliance/<GUID>."""
    body: dict[str, Any] = {}
    if status is not None:
        body["status"] = status
    if evidence_type is not None:
        body["evidenceType"] = evidence_type
    if mark is not None:
        body["mark"] = mark
    if rationale is not None:
        body["rationale"] = rationale
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/items/{item_guid}/compliance/{compliance_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_item_compliance(
    item_guid: str, compliance_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /items/<GUID>/compliance/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{item_guid}/compliance/{compliance_guid}"}
    return _arena_delete(f"/items/{item_guid}/compliance/{compliance_guid}")

@mcp.tool()
def create_item_source(
    item_guid: str,
    supplier_item_guid: str,
    approved: bool = True,
    active_production: bool = False,
    active_prototype: bool = False,
    aml_rank: Optional[int] = None,
    notes: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /items/<GUID>/sourcing — link a supplier item to this item."""
    body: dict[str, Any] = {
        "supplierItem": {"guid": supplier_item_guid},
        "approved": approved,
        "activeProduction": active_production,
        "activePrototype": active_prototype,
    }
    if aml_rank is not None:
        body["amlRank"] = aml_rank
    if notes is not None:
        body["notes"] = notes
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/items/{item_guid}/sourcing", "body": body}
    return _arena_post(f"/items/{item_guid}/sourcing", body=body)

@mcp.tool()
def update_item_source(
    item_guid: str,
    source_guid: str,
    approved: Optional[bool] = None,
    active_production: Optional[bool] = None,
    active_prototype: Optional[bool] = None,
    aml_rank: Optional[int] = None,
    notes: Optional[str] = None,
    setnull: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /items/<GUID>/sourcing/<GUID>."""
    body: dict[str, Any] = {}
    if approved is not None:
        body["approved"] = approved
    if active_production is not None:
        body["activeProduction"] = active_production
    if active_prototype is not None:
        body["activePrototype"] = active_prototype
    if aml_rank is not None:
        body["amlRank"] = aml_rank
    if notes is not None:
        body["notes"] = notes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/items/{item_guid}/sourcing/{source_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_item_source(
    item_guid: str, source_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /items/<GUID>/sourcing/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{item_guid}/sourcing/{source_guid}"}
    return _arena_delete(f"/items/{item_guid}/sourcing/{source_guid}")

@mcp.tool()
def create_item_reference(
    from_item_guid: str,
    to_item_guid: str,
    reference_type: Optional[str] = None,
    notes: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /items/<GUID>/items — create a cross-reference from one item to another."""
    body: dict[str, Any] = {"item": {"guid": to_item_guid}}
    if reference_type:
        body["referenceType"] = reference_type
    if notes:
        body["note"] = notes
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/items/{from_item_guid}/items", "body": body}
    return _arena_post(f"/items/{from_item_guid}/items", body=body)

@mcp.tool()
def update_item_reference(
    from_item_guid: str,
    reference_guid: str,
    reference_type: Optional[str] = None,
    notes: Optional[str] = None,
    setnull: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /items/<GUID>/items/<GUID>."""
    body: dict[str, Any] = {}
    if reference_type is not None:
        body["referenceType"] = reference_type
    if notes is not None:
        body["note"] = notes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/items/{from_item_guid}/items/{reference_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_item_reference(
    from_item_guid: str, reference_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /items/<GUID>/items/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{from_item_guid}/items/{reference_guid}"}
    return _arena_delete(f"/items/{from_item_guid}/items/{reference_guid}")

