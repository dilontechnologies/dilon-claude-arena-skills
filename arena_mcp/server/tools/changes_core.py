from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _wildcard, _paginate_get
from .. import config

__all__ = [
    "list_change_administrators",
    "list_change_number_prefixes",
    "get_change_files",
    "search_changes",
    "get_change",
    "get_change_items",
    "get_change_workflow_status",
    "list_change_categories",
    "list_change_routings",
    "create_change",
    "update_change",
    "add_items_to_change",
    "remove_items_from_change",
    "route_change",
    "cancel_change",
    "get_change_history",
    "list_change_attributes",
    "list_change_item_attributes",
    "list_change_category_attributes",
    "list_change_number_sequence_prefixes",
    "get_change_category",
    "transition_change_status",
    "complete_change",
    "reopen_change",
    "force_reject_change",
    "force_approve_change",
    "withdraw_change",
    "uncomplete_change",
    "delete_change",
    "update_change_affected_item",
    "add_file_to_change",
    "remove_file_from_change",
]


@mcp.tool()
def list_change_administrators(category_guid: Optional[str] = None) -> dict[str, Any]:
    """List change administrators in the workspace.

    Args:
        category_guid: Optional category to filter administrators by
            scope (some workspaces scope admins per category).
    """
    params: dict[str, Any] = {}
    if category_guid: params["category.guid"] = category_guid
    return _arena_get("/settings/changes/administrators",
                      params=params if params else None)

@mcp.tool()
def list_change_number_prefixes() -> dict[str, Any]:
    """List change number prefixes (e.g. ECO-, DCO-, MCO-, DEV-).

    Returns prefix GUIDs to use with number_sequence_prefix on create_change.
    Endpoint is /settings/changes/numbersequenceprefixes — Arena spells it
    out fully, matching the numberSequencePrefix field on /changes.
    """
    return _arena_get("/settings/changes/numbersequenceprefixes")

@mcp.tool()
def get_change_files(guid: str) -> dict[str, Any]:
    """List files associated with a change (ECO/DEV/etc. by change GUID).

    Returns file-view-association records — each entry shows which file
    is attached and in which "view" (Files-only attach vs. attach + edit
    target). Use the inner file.guid with get_file_summary / get_file_content.
    """
    return _arena_get(f"/changes/{guid}/files")

@mcp.tool()
def search_changes(
    query: Optional[str] = None,
    number: Optional[str] = None,
    title: Optional[str] = None,
    lifecycle_status: Optional[str] = None,
    creator_guid: Optional[str] = None,
    category_guid: Optional[str] = None,
    implementation_status: Optional[str] = None,
    effective_from: Optional[str] = None,
    effective_to: Optional[str] = None,
    expiration_from: Optional[str] = None,
    expiration_to: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena changes (ECOs, ECRs, ACs, DEVs, etc.).

    Common change-number prefixes include:
      - ECO: Engineering Change Order (standard release of new revs)
      - AC:  Admin Change (post-release administrative fixup,
             does NOT bump the rev number — supersedes silently)
      - DEV: Deviation (TEMPORARY effectivity)
      - ECR: Engineering Change Request

    Per Arena's GET /changes searchable-attribute spec, only the params
    below are valid filters. `lifecycle_status` maps to lifecycleStatus.type.
    NOTE: Arena's /changes endpoint does NOT support '!' negation on
    lifecycleStatus.type (the '!' operator only works on /qualityprocesses
    ?status=). For "all non-COMPLETED" changes, run multiple queries with
    positive values and union client-side.

    Valid lifecycle_status values: OPEN_AND_UNLOCKED, OPEN_AND_LOCKED,
    SUBMITTED_FOR_ROUTING, SUBMITTED_FOR_APPROVAL, REJECTED, CANCELED,
    APPROVED, EFFECTIVE, COMPLETED, EXPIRED. Filtering by owner is NOT
    supported by Arena on /changes — use creator_guid (the user GUID)
    instead.

    Pagination:
      - Default limit is 100, max single-page is 400 (Arena's cap).
      - Set fetch_all=True for automatic pagination through all results
        (up to ~20,000). When fetch_all is True, limit and offset are
        ignored.

    Args:
        query: Free-text search (Arena's 'any', UI-bar equivalent).
        number: Change number, auto-wildcarded if no '*' present.
        title: Change title, auto-wildcarded if no '*' present.
        lifecycle_status: One of the lifecycle states above (positive
            value only — no negation).
        creator_guid: Filter by creating user's GUID.
        category_guid: Filter by change category GUID (use
            list_change_categories to discover).
        implementation_status: NOT_STARTED | IN_PROGRESS | NEEDS_ATTENTION | DONE.
        effective_from: ISO-8601 Zulu datetime, lower bound on effectivity.
        effective_to: ISO-8601 Zulu datetime, upper bound on effectivity.
        expiration_from: ISO-8601 Zulu datetime, lower bound on expiration
            (TEMPORARY changes only).
        expiration_to: ISO-8601 Zulu datetime, upper bound on expiration.
        limit: Single-page size (1-400). Ignored if fetch_all=True.
        offset: Pagination offset. Ignored if fetch_all=True.
        fetch_all: True to paginate through all results automatically.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query
    if number: base_params["number"] = _wildcard(number)
    if title: base_params["title"] = _wildcard(title)
    if lifecycle_status: base_params["lifecycleStatus.type"] = lifecycle_status
    if creator_guid: base_params["creator.guid"] = creator_guid
    if category_guid: base_params["category.guid"] = category_guid
    if implementation_status: base_params["implementationStatus"] = implementation_status
    if effective_from: base_params["effectiveDateTimeFrom"] = effective_from
    if effective_to: base_params["effectiveDateTimeTo"] = effective_to
    if expiration_from: base_params["expirationDateTimeFrom"] = expiration_from
    if expiration_to: base_params["expirationDateTimeTo"] = expiration_to

    if fetch_all:
        return _paginate_get("/changes", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/changes", params=base_params)

@mcp.tool()
def get_change(guid: str) -> dict[str, Any]:
    """Get full details of a single change by GUID."""
    return _arena_get(f"/changes/{guid}")

@mcp.tool()
def get_change_items(guid: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """List items affected by a change."""
    return _arena_get(f"/changes/{guid}/items",
                      params={"limit": min(max(limit, 1), 200), "offset": max(offset, 0)})

@mcp.tool()
def get_change_workflow_status(guid: str) -> dict[str, Any]:
    """Report current lifecycle status of a change.

    Arena doesn't expose a "next states" endpoint; valid transitions are
    determined by Arena workflow constants. Common status values seen in
    Arena: OPEN_AND_UNLOCKED, OPEN_AND_LOCKED, SUBMITTED, SUBMITTED_FOR_ROUTING,
    APPROVED, EFFECTIVE, COMPLETED, CANCELED. Exact set depends on category.
    """
    change = _arena_get(f"/changes/{guid}")
    if isinstance(change, dict) and change.get("error"):
        return change
    cur = change if isinstance(change, dict) else {}
    return {
        "guid": guid,
        "number": cur.get("number"),
        "title": cur.get("title"),
        "lifecycle_status": cur.get("lifecycleStatus"),
        "category": cur.get("category"),
        "routings": cur.get("routings"),
        "submission_datetime": cur.get("submissionDateTime"),
        "effective_datetime": cur.get("effectiveDateTime"),
        "note": (
            "Use route_change with the appropriate Arena status string. "
            "Common values: OPEN_AND_LOCKED, OPEN_AND_UNLOCKED, SUBMITTED, "
            "CANCELED. Exact set depends on the category and routing config."
        ),
    }

@mcp.tool()
def list_change_categories() -> dict[str, Any]:
    """List all change categories in the workspace.

    Returns category GUIDs to use as category_guid when creating changes.
    Arena's /settings/changes/categories endpoint does not paginate —
    it rejects 'limit' as a not-searchable attribute and returns all
    categories in one response.
    """
    return _arena_get("/settings/changes/categories")

@mcp.tool()
def list_change_routings(category_guid: str) -> dict[str, Any]:
    """List approval routings configured for a change category.

    Use these routing GUIDs in create_change's routings parameter.
    """
    return _arena_get(f"/settings/changes/categories/{category_guid}/routings")

@mcp.tool()
def create_change(
    title: str,
    category_guid: str,
    number_sequence_prefix: Optional[str] = None,
    description: Optional[str] = None,
    routing_guids: Optional[list[str]] = None,
    effectivity_type: str = "PERMANENT_ON_APPROVAL",
    approval_deadline_datetime: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new change (ECO/ECR/etc.).

    Args:
        title: Title of the change (NOT 'name' — Arena calls this 'title').
        category_guid: GUID from list_change_categories.
        number_sequence_prefix: e.g. "ECO-". Arena may default this from
            the category; if so you can omit.
        description: Description body.
        routing_guids: Approval routing GUIDs from list_change_routings.
        effectivity_type: One of PERMANENT_ON_APPROVAL (default),
            PERMANENT_ON_DATE, TEMPORARY.
        approval_deadline_datetime: ISO 8601 (e.g. "2026-06-15T00:00:00Z").
        additional_attributes: List of {"guid": "<attr-guid>", "value": ...}
            for custom attributes on this category.
        dry_run: Preview body without sending.
    """
    body: dict[str, Any] = {
        "title": title,
        "category": {"guid": category_guid},
        "effectivityType": effectivity_type,
    }
    if number_sequence_prefix:
        body["numberSequencePrefix"] = {"value": number_sequence_prefix}
    if description is not None:
        body["description"] = description
    if routing_guids:
        body["routings"] = [{"guid": g} for g in routing_guids]
    if approval_deadline_datetime:
        body["approvalDeadlineDateTime"] = approval_deadline_datetime
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes", "body": body}
    return _arena_post("/changes", body=body)

@mcp.tool()
def update_change(
    guid: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    approval_deadline_datetime: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update attributes on an existing change.

    Only the fields you pass are modified. Arena requires the change to be
    in OPEN_AND_UNLOCKED status for edits; if it's locked, this will 4xx.
    """
    body: dict[str, Any] = {}
    if title is not None: body["title"] = title
    if description is not None: body["description"] = description
    if approval_deadline_datetime is not None:
        body["approvalDeadlineDateTime"] = approval_deadline_datetime
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes

    if not body:
        return {"error": True, "message": "No fields provided to update."}

    if dry_run:
        return {"dry_run": True, "would_put_to": f"/changes/{guid}", "body": body}

    snap_info: dict[str, Any] = {}
    if snapshot_first:
        current = _arena_get(f"/changes/{guid}")
        if isinstance(current, dict) and not current.get("error"):
            snap_info = _write_snapshot(
                label=f"pre-update change {current.get('number', guid)}",
                kind="change_update",
                captures=[{"endpoint": f"/changes/{guid}", "data": current}],
            )
    result = _arena_put(f"/changes/{guid}", body=body)
    if snap_info:
        result = {"snapshot": snap_info, "result": result}
    return result

@mcp.tool()
def add_items_to_change(
    change_guid: str,
    items: list[dict[str, Any]],
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add one or more items as affected by a change.

    Each entry in `items` is a dict describing one affected item. At minimum:
        {"new_item_revision_guid": "<working-rev-guid>"}

    Optional per-item fields:
        new_revision_number: e.g. "B"
        bom_view, files_view, sourcing_view, specs_view: booleans (whether
            that view is included in the change)
        new_lifecycle_phase_guid: GUID of target lifecycle phase
        notes_bom, notes_files, notes_sourcing, notes_specs: per-view notes
        affected_item_revision_guid: GUID of the item's current EFFECTIVE
            revision, for advancing a RELEASED item that has no working
            revision yet. Per Arena's REST API docs this is a distinct
            field from newItemRevision (experimental — added 2026-08-31
            to test whether Arena auto-creates the working revision when
            this is supplied alongside newItemRevision).

    IMPORTANT: `new_item_revision_guid` is the WORKING revision GUID, not
    the item GUID itself. You can find it via get_item — the working revision
    is shown alongside the effective revision.

    Args:
        change_guid: GUID of the target change.
        items: List of per-item dicts as above.
        snapshot_first: Snapshot affected-items list before modifying.
        dry_run: Preview without sending.
    """

    def _build_body(it: dict[str, Any]) -> dict[str, Any]:
        body: dict[str, Any] = {
            "newItemRevision": {"guid": it["new_item_revision_guid"]},
        }
        if "affected_item_revision_guid" in it:
            body["affectedItemRevision"] = {"guid": it["affected_item_revision_guid"]}
        if "new_revision_number" in it:
            body["newRevisionNumber"] = it["new_revision_number"]
        if "new_lifecycle_phase_guid" in it:
            body["newLifecyclePhase"] = {"guid": it["new_lifecycle_phase_guid"]}
        for view_field, api_key in [
            ("bom_view", "bomView"),
            ("files_view", "filesView"),
            ("sourcing_view", "sourcingView"),
            ("specs_view", "specsView"),
        ]:
            if view_field in it:
                view = {"includedInThisChange": bool(it[view_field])}
                notes_key = f"notes_{view_field.replace('_view', '')}"
                if it[view_field] and notes_key in it:
                    view["notes"] = it[notes_key]
                body[api_key] = view
        return body

    if dry_run:
        return {
            "dry_run": True,
            "would_post_to": f"/changes/{change_guid}/items",
            "bodies": [_build_body(it) for it in items],
        }

    snap_info: dict[str, Any] = {}
    if snapshot_first:
        current_items = _arena_get(f"/changes/{change_guid}/items", params={"limit": 200})
        if isinstance(current_items, dict) and not current_items.get("error"):
            snap_info = _write_snapshot(
                label=f"pre-add-items to change {change_guid}",
                kind="change_items",
                captures=[{"endpoint": f"/changes/{change_guid}/items", "data": current_items}],
            )

    results = []
    for it in items:
        r = _arena_post(f"/changes/{change_guid}/items", body=_build_body(it))
        results.append({"item": it, "result": r})
    out: dict[str, Any] = {"added": len(results), "results": results}
    if snap_info:
        out["snapshot"] = snap_info
    return out

@mcp.tool()
def remove_items_from_change(
    change_guid: str,
    affected_item_association_guids: list[str],
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Remove affected items from a change.

    IMPORTANT: Pass the change-item ASSOCIATION GUIDs (from get_change_items),
    not the item GUIDs themselves. The association GUID is returned when an
    item is added to the change.
    """
    if dry_run:
        return {
            "dry_run": True,
            "would_delete": [
                f"/changes/{change_guid}/items/{g}" for g in affected_item_association_guids
            ],
        }

    snap_info: dict[str, Any] = {}
    if snapshot_first:
        current_items = _arena_get(f"/changes/{change_guid}/items", params={"limit": 200})
        if isinstance(current_items, dict) and not current_items.get("error"):
            snap_info = _write_snapshot(
                label=f"pre-remove-items from change {change_guid}",
                kind="change_items",
                captures=[{"endpoint": f"/changes/{change_guid}/items", "data": current_items}],
            )

    results = []
    for assoc_guid in affected_item_association_guids:
        r = _arena_delete(f"/changes/{change_guid}/items/{assoc_guid}")
        results.append({"association_guid": assoc_guid, "result": r})
    out: dict[str, Any] = {"removed": len(results), "results": results}
    if snap_info:
        out["snapshot"] = snap_info
    return out

@mcp.tool()
def route_change(
    guid: str,
    status: str,
    comment: Optional[str] = None,
    administrator_guids: Optional[list[str]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Advance/transition a change to a new status via POST /changes/statuschanges.

    Args:
        guid: GUID of the change.
        status: Arena status string. Common values:
            OPEN_AND_LOCKED, OPEN_AND_UNLOCKED, SUBMITTED, CANCELED.
            For admin-defined routing: SUBMITTED triggers SUBMITTED_FOR_ROUTING
            on the first call and then SUBMITTED on the second.
        comment: Optional comment (recommended; some transitions require it).
        administrator_guids: Required only for admin-defined routings.
        dry_run: Preview without sending.
    """
    body: dict[str, Any] = {"change": {"guid": guid}, "status": status}
    if comment:
        body["comment"] = comment
    if administrator_guids:
        body["administrators"] = [{"guid": g} for g in administrator_guids]
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes/statuschanges", "body": body}
    return _arena_post("/changes/statuschanges", body=body)

@mcp.tool()
def cancel_change(
    guid: str,
    comment: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Cancel a change (status=CANCELED).

    Uses the /changes/statuschanges endpoint (same as route_change).
    """
    body: dict[str, Any] = {"change": {"guid": guid}, "status": "CANCELED"}
    if comment:
        body["comment"] = comment

    if dry_run:
        current = _arena_get(f"/changes/{guid}")
        cur = current if isinstance(current, dict) else {}
        return {
            "dry_run": True,
            "would_post_to": "/changes/statuschanges",
            "body": body,
            "current_state": {
                "number": cur.get("number"),
                "title": cur.get("title"),
                "lifecycle_status": cur.get("lifecycleStatus"),
            },
            "to_actually_cancel": "Re-call with dry_run=False",
        }

    current = _arena_get(f"/changes/{guid}")
    cur = current if isinstance(current, dict) else {}
    snap_info = _write_snapshot(
        label=f"pre-cancel change {cur.get('number', guid)}",
        kind="change_cancel",
        captures=[{"endpoint": f"/changes/{guid}", "data": current}],
    )
    result = _arena_post("/changes/statuschanges", body=body)
    return {"snapshot": snap_info, "result": result}

@mcp.tool()
def get_change_history(guid: str) -> dict[str, Any]:
    """Return the audit history of a change.

    Equivalent to the Change ▶ History ▶ General subview in the UI.
    Returns a chronological list of every property change, status
    transition, approval signoff, and modification — each with the
    user, timestamp, property name, original value, and new value.

    This is the audit trail an FDA/MDR inspector would ask for to
    verify change-control compliance.
    """
    return _arena_get(f"/changes/{guid}/history")

@mcp.tool()
def list_change_attributes(include_possible_values: bool = False) -> dict[str, Any]:
    """List workspace-wide custom attribute definitions for changes.

    Args:
        include_possible_values: If True, returns each FIXED_DROP_DOWN
            attribute's full options list under `possibleValues`. Required
            for validating dropdown values before write. Default False
            for smaller responses on schema-only queries.

    Spec: GET /settings/changes/attributes[?includePossibleValues=true]
    """
    params: dict[str, Any] = {}
    if include_possible_values:
        params["includePossibleValues"] = "true"
    return _arena_get("/settings/changes/attributes", params=params)

@mcp.tool()
def list_change_item_attributes() -> dict[str, Any]:
    """List custom attribute definitions for change-affected-items.

    These are attributes attached to the "affected items" rows on a
    change (e.g. "From rev", "To rev", "Disposition for in-stock").
    Distinct from item-level or change-level attributes.
    """
    return _arena_get("/settings/changes/items/attributes")

@mcp.tool()
def list_change_category_attributes(
    category_guid: str, include_possible_values: bool = False
) -> dict[str, Any]:
    """List custom attributes for a specific change category.

    Args:
        category_guid: Change category GUID (e.g. ECO, AC, DEV).
        include_possible_values: If True, returns each FIXED_DROP_DOWN
            attribute's full options list under `possibleValues`. Required
            for validating dropdown values before write. Default False
            for smaller responses on schema-only queries.

    Spec: GET /settings/changes/categories/<GUID>/attributes
          [?includePossibleValues=true]
    """
    params: dict[str, Any] = {}
    if include_possible_values:
        params["includePossibleValues"] = "true"
    return _arena_get(
        f"/settings/changes/categories/{category_guid}/attributes", params=params
    )

@mcp.tool()
def list_change_number_sequence_prefixes() -> dict[str, Any]:
    """List number sequence prefixes for changes (e.g. ECO, AC, DEV, ECR).

    Returns each prefix and the change category it belongs to. Use
    this to enumerate this workspace's change prefix conventions.
    """
    return _arena_get("/settings/changes/numbersequenceprefixes")

@mcp.tool()
def get_change_category(category_guid: str) -> dict[str, Any]:
    """Get full details of a single change category by GUID."""
    return _arena_get(f"/settings/changes/categories/{category_guid}")

@mcp.tool()
def transition_change_status(
    change_guid: str,
    status: str,
    comment: Optional[str] = None,
    routings: Optional[list[dict[str, Any]]] = None,
    administrators: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generic change-status transition endpoint.

    POST /changes/statuschanges. `status` values (per spec pages 563–591):
      OPEN_AND_LOCKED, OPEN_AND_UNLOCKED (lock/unlock)
      SUBMITTED (submitting — auto-routing or admin-defined depending on
                 category config; add administrators=[{guid}] for admin-defined)
      COMPLETED (complete)
      CANCELED (also via cancel_change wrapper)
      APPROVED / REJECTED (admin force-approve/force-reject override —
        only valid when the change is SUBMITTED_FOR_APPROVAL; an APPROVED
        change auto-advances straight to EFFECTIVE)
      WITHDRAWN, REOPENED
    """
    body: dict[str, Any] = {"change": {"guid": change_guid}, "status": status}
    if comment:
        body["comment"] = comment
    if routings:
        body["routings"] = routings
    if administrators:
        body["administrators"] = administrators
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes/statuschanges", "body": body}
    return _arena_post("/changes/statuschanges", body=body)

@mcp.tool()
def complete_change(
    change_guid: str,
    comment: Optional[str] = None,
    implementation_status: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /changes/statuschanges — mark change COMPLETED.

    Optional implementation_status for the "Complete With Implementation
    Status" spec variant (page 579).
    """
    body: dict[str, Any] = {"change": {"guid": change_guid}, "status": "COMPLETED"}
    if comment:
        body["comment"] = comment
    if implementation_status:
        body["implementationStatus"] = implementation_status
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes/statuschanges", "body": body}
    return _arena_post("/changes/statuschanges", body=body)

@mcp.tool()
def reopen_change(
    change_guid: str, comment: Optional[str] = None, dry_run: bool = False
) -> dict[str, Any]:
    """POST /changes/statuschanges — REOPEN a completed change."""
    body: dict[str, Any] = {"change": {"guid": change_guid}, "status": "REOPENED"}
    if comment:
        body["comment"] = comment
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes/statuschanges", "body": body}
    return _arena_post("/changes/statuschanges", body=body)

@mcp.tool()
def force_reject_change(
    change_guid: str, comment: Optional[str] = None, dry_run: bool = False
) -> dict[str, Any]:
    """POST /changes/statuschanges — admin FORCE_REJECT the change.

    Only valid when the change is SUBMITTED_FOR_APPROVAL. Per Arena's REST
    API docs the status value is "REJECTED", not "FORCE_REJECTED".
    """
    body: dict[str, Any] = {"change": {"guid": change_guid}, "status": "REJECTED"}
    if comment:
        body["comment"] = comment
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes/statuschanges", "body": body}
    return _arena_post("/changes/statuschanges", body=body)

@mcp.tool()
def force_approve_change(
    change_guid: str, comment: Optional[str] = None, dry_run: bool = False
) -> dict[str, Any]:
    """POST /changes/statuschanges — admin FORCE_APPROVE the change.

    Only valid when the change is SUBMITTED_FOR_APPROVAL (submit it first).
    Per Arena's REST API docs the status value is "APPROVED", not
    "FORCE_APPROVED" — Arena auto-advances an APPROVED change straight to
    EFFECTIVE as part of this same call.
    """
    body: dict[str, Any] = {"change": {"guid": change_guid}, "status": "APPROVED"}
    if comment:
        body["comment"] = comment
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes/statuschanges", "body": body}
    return _arena_post("/changes/statuschanges", body=body)

@mcp.tool()
def withdraw_change(
    change_guid: str, comment: Optional[str] = None, dry_run: bool = False
) -> dict[str, Any]:
    """POST /changes/statuschanges — withdraw the change (WITHDRAWN)."""
    body: dict[str, Any] = {"change": {"guid": change_guid}, "status": "WITHDRAWN"}
    if comment:
        body["comment"] = comment
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes/statuschanges", "body": body}
    return _arena_post("/changes/statuschanges", body=body)

@mcp.tool()
def uncomplete_change(
    change_guid: str, comment: Optional[str] = None, dry_run: bool = False
) -> dict[str, Any]:
    """POST /changes/statuschanges — unmark as complete (page 582)."""
    body: dict[str, Any] = {"change": {"guid": change_guid}, "status": "OPEN_AND_UNLOCKED"}
    if comment:
        body["comment"] = comment
    if dry_run:
        return {"dry_run": True, "would_post_to": "/changes/statuschanges", "body": body}
    return _arena_post("/changes/statuschanges", body=body)

@mcp.tool()
def delete_change(change_guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /changes/<GUID>. Only works for changes in draft."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/changes/{change_guid}"}
    return _arena_delete(f"/changes/{change_guid}")

@mcp.tool()
def update_change_affected_item(
    change_guid: str,
    association_guid: str,
    new_revision_number: Optional[str] = None,
    new_lifecycle_phase_guid: Optional[str] = None,
    views: Optional[dict[str, Any]] = None,
    disposition_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /changes/<GUID>/items/<GUID> — edit an affected-item association.

    views is an optional dict e.g. {"filesView": {"includedInThisChange": true,
    "notes": "…"}, "bomView": {...}}. Only pass the views you want to change.
    """
    body: dict[str, Any] = {}
    if new_revision_number is not None:
        body["newRevisionNumber"] = new_revision_number
    if new_lifecycle_phase_guid is not None:
        body["newLifecyclePhase"] = {"guid": new_lifecycle_phase_guid}
    if views:
        body.update(views)
    if disposition_attributes:
        body["dispositionAttributes"] = disposition_attributes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/changes/{change_guid}/items/{association_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def add_file_to_change(
    change_guid: str, file_guid: str,
    latest_edition_association: bool = True, primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /changes/<GUID>/files — attach existing file to change's Files view."""
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/changes/{change_guid}/files", "body": body}
    return _arena_post(f"/changes/{change_guid}/files", body=body)

@mcp.tool()
def remove_file_from_change(
    change_guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /changes/<GUID>/files/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/changes/{change_guid}/files/{file_assoc_guid}"}
    return _arena_delete(f"/changes/{change_guid}/files/{file_assoc_guid}")

