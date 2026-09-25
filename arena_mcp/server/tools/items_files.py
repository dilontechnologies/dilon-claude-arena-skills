from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _request_bytes, _arena_post_multipart

__all__ = [
    "get_item_files",
    "get_item_file",
    "get_item_file_watermark_content",
    "add_existing_file_to_item",
    "upload_item_file_content",
    "update_item_file_association",
    "remove_file_from_item",
]


@mcp.tool()
def get_item_files(guid: str) -> dict[str, Any]:
    """List files associated with an item (by item GUID).

    Returns the file-association records — each links a file to one of
    the item's "views" (BOM, Files, Sourcing, Specs). Use get_file_summary
    or get_file_content with the inner file.guid to drill in.
    """
    return _arena_get(f"/items/{guid}/files")

@mcp.tool()
def get_item_file(item_guid: str, file_assoc_guid: str) -> dict[str, Any]:
    """Get a single item ↔ file association by GUID.

    Use after get_item_files to drill into one file association's
    full attributes (primary flag, category, association timestamp).
    """
    return _arena_get(f"/items/{item_guid}/files/{file_assoc_guid}")

@mcp.tool()
def get_item_file_watermark_content(
    item_guid: str, file_assoc_guid: str
) -> dict[str, Any]:
    """Download an item-file with the workspace watermark applied.

    Returns base64-encoded bytes. Watermark may include item number/rev
    in addition to the workspace defaults.
    Spec endpoint: GET /items/{guid}/files/{guid}/watermarkcontent
    """
    return _request_bytes(
        f"/items/{item_guid}/files/{file_assoc_guid}/watermarkcontent"
    )

@mcp.tool()
def add_existing_file_to_item(
    item_guid: str,
    file_guid: str,
    latest_edition_association: bool = True,
    primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Attach an EXISTING file to an item's Files view.

    POST /items/<GUID>/files. Use upload_new_file_to_item for a new upload.
    """
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/items/{item_guid}/files", "body": body}
    return _arena_post(f"/items/{item_guid}/files", body=body)

@mcp.tool()
def upload_item_file_content(
    item_guid: str,
    file_assoc_guid: str,
    local_path: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /items/<GUID>/files/<GUID>/content — upload new file content
    for an item-file association (creates a new edition).

    local_path is on the machine running this MCP.
    """
    if dry_run:
        return {"dry_run": True, "would_upload": f"/items/{item_guid}/files/{file_assoc_guid}/content",
                "local_path": local_path}
    return _arena_post_multipart(
        f"/items/{item_guid}/files/{file_assoc_guid}/content", local_path
    )

@mcp.tool()
def update_item_file_association(
    item_guid: str,
    file_assoc_guid: str,
    latest_edition_association: Optional[bool] = None,
    primary: Optional[bool] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /items/<GUID>/files/<GUID> — change association flags."""
    body: dict[str, Any] = {}
    if latest_edition_association is not None:
        body["latestEditionAssociation"] = latest_edition_association
    if primary is not None:
        body["primary"] = primary
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/items/{item_guid}/files/{file_assoc_guid}"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def remove_file_from_item(
    item_guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /items/<GUID>/files/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{item_guid}/files/{file_assoc_guid}"}
    return _arena_delete(f"/items/{item_guid}/files/{file_assoc_guid}")

