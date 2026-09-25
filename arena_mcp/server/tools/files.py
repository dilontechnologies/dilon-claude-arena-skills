from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _wildcard, _paginate_get, _request_bytes, _arena_post_multipart, _write_snapshot

__all__ = [
    "list_file_categories",
    "search_files",
    "get_file_summary",
    "get_file_editions",
    "get_file_content",
    "get_file_items",
    "get_file_changes",
    "get_file_change_implementations",
    "get_file_quality_processes",
    "get_file_requests",
    "get_file_suppliers",
    "get_file_supplier_items",
    "get_file_training_plans",
    "get_file_corrections",
    "get_file_markups",
    "get_file_markup_content",
    "list_file_attributes",
    "get_file_watermark_content",
    "create_file",
    "update_file_summary",
    "upload_file_content",
    "create_file_edition",
    "correct_file",
    "check_out_file",
    "check_in_file",
    "cancel_file_check_out",
    "delete_file",
    "create_file_markup",
    "update_file_markup",
    "delete_file_markup",
]


@mcp.tool()
def list_file_categories() -> dict[str, Any]:
    """List file categories defined in the workspace.

    Returns category GUIDs you'll use when uploading files (Wave 2.1).
    """
    return _arena_get("/settings/files/categories")

@mcp.tool()
def search_files(
    query: Optional[str] = None,
    name: Optional[str] = None,
    number: Optional[str] = None,
    title: Optional[str] = None,
    category_guid: Optional[str] = None,
    format: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena files. Wildcards (*) supported on string filters.

    Per Arena's GET /files searchable-attribute spec, the only valid
    filters are: any, title, number, category.guid, format, name. Other
    fields visible on the File object (author, storageMethodName, etc.)
    are NOT searchable — Arena returns 400 code 3019 if you try.

    Pagination:
      - Default limit is 100, max single-page is 400 (Arena's cap).
      - Set fetch_all=True for automatic pagination through ALL results
        (up to ~20,000). Ignores limit/offset when True.

    Args:
        query: Free-text search (Arena's 'any', UI-bar equivalent).
        name: File name (e.g. 'Assy Instructions'), auto-wildcarded.
        number: File number (e.g. 'FILE-000998'), auto-wildcarded.
        title: File title, auto-wildcarded.
        category_guid: Filter by file category (see list_file_categories).
        format: File format/extension, e.g. 'pdf', 'docx', 'xlsx'.
        limit: Single-page size (1-400). Ignored if fetch_all=True.
        offset: Pagination offset. Ignored if fetch_all=True.
        fetch_all: True to paginate through all results automatically.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query
    if name: base_params["name"] = _wildcard(name)
    if number: base_params["number"] = _wildcard(number)
    if title: base_params["title"] = _wildcard(title)
    if category_guid: base_params["category.guid"] = category_guid
    if format: base_params["format"] = format

    if fetch_all:
        return _paginate_get("/files", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/files", params=base_params)

@mcp.tool()
def get_file_summary(guid: str) -> dict[str, Any]:
    """Get metadata for a single file by GUID.

    Returns name, title, number, category, edition, format, mimeType, size,
    author, storage method, lock/markup status, etc. Does NOT download content
    — use get_file_content for that.
    """
    return _arena_get(f"/files/{guid}")

@mcp.tool()
def get_file_editions(guid: str) -> dict[str, Any]:
    """List the edition (revision) history of a file.

    Each edition has its own GUID, edition label, creation date, and
    storage info. The latest edition's content is what you'd download
    via get_file_content; older editions may have separate content URLs.
    """
    return _arena_get(f"/files/{guid}/editions")

@mcp.tool()
def get_file_content(
    guid: str,
    max_size_bytes: int = 10 * 1024 * 1024,
) -> dict[str, Any]:
    """Download a file's content (latest edition) as base64-encoded bytes.

    Default size cap is 10 MB. For larger files, pass max_size_bytes
    explicitly — but be aware the base64 payload travels through the
    conversation, so very large files will blow up context. For a 100 MB
    file you'd be looking at ~133 MB of base64 in the response.

    Returns:
        {size_bytes, content_type, content_disposition, content_base64}
        or {error: True, reason: "file_too_large", ...} if over cap.

    Decode with: base64.b64decode(result["content_base64"]).
    """
    return _request_bytes(f"/files/{guid}/content", max_size_bytes=max_size_bytes)

@mcp.tool()
def get_file_items(guid: str) -> dict[str, Any]:
    """List items this file is attached to (reverse of get_item_files).

    Each entry is a file-view-association record showing which item the
    file is attached to and in which item view (Files, Specs, etc.).
    Useful for answering "where else is this document used?"
    """
    return _arena_get(f"/files/{guid}/items")

@mcp.tool()
def get_file_changes(guid: str) -> dict[str, Any]:
    """List changes that reference this file (changereferences view).

    These are changes where the file is attached as a reference in the
    Files view of the change. Each entry includes change.guid and
    change.number (e.g. ECO-000023). Useful for "which ECOs touched
    this doc?"

    Distinct from get_file_change_implementations — that's for
    changes that *implemented* a new edition of this file.
    """
    return _arena_get(f"/files/{guid}/changereferences")

@mcp.tool()
def get_file_change_implementations(guid: str) -> dict[str, Any]:
    """List changes whose implementation tasks produced an edition of this file.

    Different from get_file_changes (reference vs. implementation):
      - changereferences: changes that simply *attached* this file
      - changeimplementations: changes whose implementation tasks
        produced new editions of this file (the audit trail of who
        edited it under change control)
    """
    return _arena_get(f"/files/{guid}/changeimplementations")

@mcp.tool()
def get_file_quality_processes(guid: str) -> dict[str, Any]:
    """List quality processes this file is attached to.

    Each QP entry includes the QP's guid and number. Useful for
    answering "is this file currently being used as evidence in any
    open CAPA / NCMR / audit?"
    """
    return _arena_get(f"/files/{guid}/qualityprocesses")

@mcp.tool()
def get_file_requests(guid: str) -> dict[str, Any]:
    """List requests / tickets that reference this file.

    Returns request entries with their guid and number. Useful for
    tracing "which complaint or design request first surfaced this
    file?"
    """
    return _arena_get(f"/files/{guid}/requests")

@mcp.tool()
def get_file_suppliers(guid: str) -> dict[str, Any]:
    """List suppliers this file is attached to.

    Each entry includes the supplier's guid and name. Files attached
    to a supplier are typically certificates, audit reports, agreements,
    quality manuals, etc.
    """
    return _arena_get(f"/files/{guid}/suppliers")

@mcp.tool()
def get_file_supplier_items(guid: str) -> dict[str, Any]:
    """List supplier items this file is attached to.

    Returns supplier-item file-view associations. Supplier-item files
    are typically datasheets, CoCs, declarations of conformity, etc.
    """
    return _arena_get(f"/files/{guid}/supplieritems")

@mcp.tool()
def get_file_training_plans(guid: str) -> dict[str, Any]:
    """List training plans that reference this file.

    Critical for QMS audits: "is anyone trained on this WI/SOP?" can be
    chained through training plan → users to answer "have all required
    employees completed training on the current edition of this doc?"
    """
    return _arena_get(f"/files/{guid}/trainingplans")

@mcp.tool()
def get_file_corrections(guid: str) -> dict[str, Any]:
    """List corrections (errata) applied to editions of this file.

    File corrections are post-effective fixes to specific editions —
    they don't create a new edition but flag that an edition had errors.
    Less common than full editions; used for minor textual / formatting
    errors caught after release.
    """
    return _arena_get(f"/files/{guid}/corrections")

@mcp.tool()
def get_file_markups(guid: str) -> dict[str, Any]:
    """List markups (redlines / annotations) attached to the file.

    Markups are overlay edits — e.g. redlined PDFs showing proposed
    changes during a change-order review. Each entry includes the
    markup's guid; pass it to get_file_markup_content to download
    the redlined version.
    """
    return _arena_get(f"/files/{guid}/markups")

@mcp.tool()
def get_file_markup_content(
    file_guid: str,
    markup_guid: str,
    max_size_bytes: int = 10 * 1024 * 1024,
) -> dict[str, Any]:
    """Download a markup's content as base64-encoded bytes.

    Returns the redlined / annotated file (typically a PDF with
    annotations overlaid). Same size constraints as get_file_content
    apply — keep under ~750 KB for the MCP transport.

    Args:
        file_guid: GUID of the parent file.
        markup_guid: GUID of the markup (from get_file_markups).
        max_size_bytes: Reject downloads larger than this. Default 10 MB.
    """
    return _request_bytes(
        f"/files/{file_guid}/markups/{markup_guid}/content",
        max_size_bytes=max_size_bytes,
    )

@mcp.tool()
def list_file_attributes() -> dict[str, Any]:
    """List workspace-wide custom attribute definitions for files."""
    return _arena_get("/settings/files/attributes")

@mcp.tool()
def get_file_watermark_content(guid: str) -> dict[str, Any]:
    """Download a file with the workspace watermark applied.

    Returns base64-encoded bytes. The watermark is applied server-side
    (e.g., "CONFIDENTIAL", item rev label, downloaded-by-user) per
    workspace configuration. Use this instead of get_file_content when
    delivering files outside Arena for audit purposes.
    Spec endpoint: GET /files/{guid}/watermarkcontent
    """
    return _request_bytes(f"/files/{guid}/watermarkcontent")

@mcp.tool()
def create_file(
    title: str,
    category_guid: Optional[str] = None,
    description: Optional[str] = None,
    edition: Optional[str] = None,
    format: Optional[str] = None,
    author_full_name: Optional[str] = None,
    storage_method: str = "PLACE_HOLDER",
    location: Optional[str] = None,
    local_path: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a file record.

    Per Arena's OpenAPI spec, plain JSON POST /files (FileCreateVo) only
    accepts storageMethodName in {FTP, WEB, PLACE_HOLDER} — 'FILE' is
    rejected there with code 3003. Content-bearing files (storage_method=
    'FILE') must instead be created via multipart POST /files (FileCreate),
    which requires local_path to supply the binary content in the same call.

    For FTP/WEB/PLACE_HOLDER: POSTs JSON to /files/json (no content).
    For FILE: pass local_path; POSTs multipart/form-data to /files with
    the file content and metadata together (single call, no separate
    upload_file_content needed).
    """
    if storage_method == "FILE":
        if not local_path:
            return {"error": True, "message": "local_path required for storage_method='FILE'."}
        fields: dict[str, Any] = {"title": title, "storageMethodName": "FILE"}
        if category_guid:
            fields["category.guid"] = category_guid
        if description is not None:
            fields["description"] = description
        if edition is not None:
            fields["edition"] = edition
        if format is not None:
            fields["format"] = format
        if author_full_name is not None:
            fields["author.fullName"] = author_full_name
        if dry_run:
            return {"dry_run": True, "would_post_multipart_to": "/files",
                     "fields": fields, "local_path": local_path}
        return _arena_post_multipart("/files", local_path, extra_fields=fields)

    body: dict[str, Any] = {"title": title, "storageMethodName": storage_method}
    if category_guid:
        body["category"] = {"guid": category_guid}
    if description is not None:
        body["description"] = description
    if edition is not None:
        body["edition"] = edition
    if format is not None:
        body["format"] = format
    if author_full_name is not None:
        body["author"] = {"fullName": author_full_name}
    if location is not None:
        body["location"] = location
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/files/json", "body": body}
    return _arena_post("/files/json", body=body)

@mcp.tool()
def update_file_summary(
    guid: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    edition: Optional[str] = None,
    format: Optional[str] = None,
    author_full_name: Optional[str] = None,
    location: Optional[str] = None,
    category_guid: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False,
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /files/<GUID>. Metadata-only update; content changes go through
    upload_file_content / create_file_edition."""
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if category_guid is not None:
        body["category"] = {"guid": category_guid}
    if edition is not None:
        body["edition"] = edition
    if format is not None:
        body["format"] = format
    if author_full_name is not None:
        body["author"] = {"fullName": author_full_name}
    if location is not None:
        body["location"] = location
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/files/{guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    snap: dict[str, Any] = {}
    if snapshot_first:
        cur = _arena_get(f"/files/{guid}")
        if isinstance(cur, dict) and not cur.get("error"):
            snap = _write_snapshot(
                label=f"pre-update file {cur.get('number', guid)}",
                kind="file_update",
                captures=[{"endpoint": f"/files/{guid}", "data": cur}],
            )
    r = _arena_put(path, body=body)
    return {"snapshot": snap, "result": r} if snap else r

@mcp.tool()
def upload_file_content(
    file_guid: str, local_path: str, dry_run: bool = False
) -> dict[str, Any]:
    """POST /files/<GUID>/content — replace the latest edition's content.

    Reads local_path from the machine running this MCP and uploads as
    multipart/form-data. Arena returns 201 on success.
    """
    if dry_run:
        return {"dry_run": True, "would_upload": f"/files/{file_guid}/content",
                "local_path": local_path}
    return _arena_post_multipart(f"/files/{file_guid}/content", local_path)

@mcp.tool()
def create_file_edition(
    file_guid: str,
    edition: str,
    local_path: Optional[str] = None,
    storage_method: str = "FILE",
    location: Optional[str] = None,
    author_full_name: Optional[str] = None,
    description: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /files/<GUID>/editions — create a new edition.

    For FILE storage: pass local_path and the tool uploads via multipart.
    For WEB or FTP storage: pass location and skip local_path.

    Per this endpoint's FileCreateNested schema (confirmed against Arena's
    live OpenAPI spec, https://api.arenasolutions.com/v1/v3/api-docs/RestAPIv1
    — see docs/requirements/dilon-arena-eco-creator/core.md), every
    multipart field on the FILE-storage branch is `file.`-prefixed,
    *including the binary content part itself* (`file.content`, not
    `filecontent`) — that inconsistency (prefixed metadata, unprefixed
    content part) is what made every prior request to this endpoint fail.
    """
    if storage_method == "FILE":
        if not local_path:
            return {"error": True, "message": "local_path required for FILE storage."}
        fields: dict[str, Any] = {
            "file.edition": edition,
            "file.storageMethodName": storage_method,
        }
        if author_full_name is not None:
            fields["file.author.fullName"] = author_full_name
        if description is not None:
            fields["file.description"] = description
        if dry_run:
            return {"dry_run": True, "would_multipart_upload_to": f"/files/{file_guid}/editions",
                    "local_path": local_path, "fields": fields,
                    "content_field_name": "file.content"}
        return _arena_post_multipart(
            f"/files/{file_guid}/editions", local_path, extra_fields=fields,
            content_field_name="file.content",
        )
    else:
        # WEB / FTP / PLACE_HOLDER / etc. — metadata-only edition, no content
        # upload. Per the live OpenAPI spec this is a *separate* endpoint
        # from the multipart one above (/editions/json, not /editions) and
        # takes a plain (non-`file.`-prefixed) FileEditionVo nested under
        # "file".
        file_fields: dict[str, Any] = {
            "edition": edition,
            "storageMethodName": storage_method,
        }
        if location is not None:
            file_fields["location"] = location
        if author_full_name is not None:
            file_fields["author"] = {"fullName": author_full_name}
        if description is not None:
            file_fields["description"] = description
        body = {"file": file_fields}
        if dry_run:
            return {"dry_run": True, "would_post_to": f"/files/{file_guid}/editions/json",
                    "body": body}
        return _arena_post(f"/files/{file_guid}/editions/json", body=body)

@mcp.tool()
def correct_file(
    file_guid: str, correction_notes: str, dry_run: bool = False
) -> dict[str, Any]:
    """POST /files/<GUID>/corrections — record an errata correction on the
    current edition without incrementing the edition."""
    body = {"notes": correction_notes}
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/files/{file_guid}/corrections", "body": body}
    return _arena_post(f"/files/{file_guid}/corrections", body=body)

@mcp.tool()
def check_out_file(file_guid: str, dry_run: bool = False) -> dict[str, Any]:
    """POST /files/checkoutstatuschanges — reserve for exclusive edit."""
    body = {"file": {"guid": file_guid}, "checkedOut": True}
    if dry_run:
        return {"dry_run": True, "would_post_to": "/files/checkoutstatuschanges", "body": body}
    return _arena_post("/files/checkoutstatuschanges", body=body)

@mcp.tool()
def check_in_file(file_guid: str, dry_run: bool = False) -> dict[str, Any]:
    """POST /files/checkoutstatuschanges — release the exclusive edit lock."""
    body = {"file": {"guid": file_guid}, "checkedOut": False}
    if dry_run:
        return {"dry_run": True, "would_post_to": "/files/checkoutstatuschanges", "body": body}
    return _arena_post("/files/checkoutstatuschanges", body=body)

@mcp.tool()
def cancel_file_check_out(file_guid: str, dry_run: bool = False) -> dict[str, Any]:
    """POST /files/checkoutstatuschanges with cancel flag — releases the
    lock without committing changes."""
    body = {"file": {"guid": file_guid}, "checkedOut": False, "cancel": True}
    if dry_run:
        return {"dry_run": True, "would_post_to": "/files/checkoutstatuschanges", "body": body}
    return _arena_post("/files/checkoutstatuschanges", body=body)

@mcp.tool()
def delete_file(file_guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /files/<GUID>. Arena refuses if the file is attached to items,
    changes, or QPs."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/files/{file_guid}"}
    return _arena_delete(f"/files/{file_guid}")

@mcp.tool()
def create_file_markup(
    file_guid: str,
    title: str,
    local_path: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /files/<GUID>/markups — attach a markup (redline) file."""
    fields = {"title": title}
    if local_path:
        if dry_run:
            return {"dry_run": True, "would_upload": f"/files/{file_guid}/markups",
                    "local_path": local_path, "fields": fields}
        return _arena_post_multipart(f"/files/{file_guid}/markups", local_path, extra_fields=fields)
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/files/{file_guid}/markups", "body": fields}
    return _arena_post(f"/files/{file_guid}/markups", body=fields)

@mcp.tool()
def update_file_markup(
    file_guid: str, markup_guid: str, title: Optional[str] = None,
    setnull: bool = False, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /files/<GUID>/markups/<GUID>."""
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    path = f"/files/{file_guid}/markups/{markup_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_file_markup(
    file_guid: str, markup_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /files/<GUID>/markups/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/files/{file_guid}/markups/{markup_guid}"}
    return _arena_delete(f"/files/{file_guid}/markups/{markup_guid}")

