from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _resolve_quality_template_guid, _wildcard, _paginate_get, _write_snapshot

__all__ = [
    "list_quality_process_owners",
    "list_quality_process_number_formats",
    "get_quality_process_steps",
    "get_quality_process_step_affected",
    "get_quality_process_step_files",
    "get_quality_process_files",
    "search_quality_processes",
    "get_quality_process",
    "list_quality_templates",
    "create_quality_process",
    "update_quality_process",
    "update_quality_process_step",
    "complete_quality_process_step",
    "reopen_quality_process_step",
    "add_affected_to_quality_step",
    "route_quality_process",
    "close_quality_process",
    "get_quality_process_step",
    "get_quality_process_step_affected_record",
    "get_quality_process_step_decisions",
    "get_quality_process_step_decision",
    "list_quality_process_attributes",
    "list_quality_process_step_attributes",
    "list_quality_process_template_attributes",
    "get_quality_process_template",
    "get_quality_process_number_format",
    "delete_quality_process",
    "update_quality_process_step_affected",
    "remove_affected_from_quality_step",
    "add_signoff_step_decision_makers",
    "make_signoff_step_decision",
]


@mcp.tool()
def list_quality_process_owners() -> dict[str, Any]:
    """List users who can own quality processes in this workspace."""
    return _arena_get("/settings/qualityprocesses/owners")

@mcp.tool()
def list_quality_process_number_formats() -> dict[str, Any]:
    """List quality process number formats and their prefixes.

    Returns format/prefix GUIDs needed for number_format_prefix_guid
    on create_quality_process.
    """
    return _arena_get("/settings/qualityprocesses/numberformats")

@mcp.tool()
def get_quality_process_steps(guid: str) -> dict[str, Any]:
    """List the workflow steps of a quality process (CAPA/NCMR/SCAR/etc.).

    Each step can have AFFECTED OBJECTS attached to it — items, changes,
    suppliers, files, etc. Use the returned step.guid with
    get_quality_process_step_affected to list them, or with
    get_quality_process_step_files to filter to FILE-type affecteds only.
    """
    return _arena_get(f"/qualityprocesses/{guid}/steps")

@mcp.tool()
def get_quality_process_step_affected(
    quality_process_guid: str,
    step_guid: str,
) -> dict[str, Any]:
    """List ALL affected objects attached to one step of a quality process.

    Arena's affected-object types: ITEM, REQUEST, CHANGE, SUPPLIER,
    SUPPLIER ITEM, FILE, QUALITY, URL. Each result has a `type` field plus
    a typed inner object — for FILE the `file` field is populated, for
    ITEM the `item` field, etc.
    """
    return _arena_get(
        f"/qualityprocesses/{quality_process_guid}/steps/{step_guid}/affected"
    )

@mcp.tool()
def get_quality_process_step_files(
    quality_process_guid: str,
    step_guid: str,
) -> dict[str, Any]:
    """List files attached to one specific step of a quality process.

    Files in Arena attach to a QP step as an affected object of type=FILE,
    not via a dedicated /files endpoint. This wraps
    GET /qualityprocesses/{qp}/steps/{step}/affected and filters to FILE type.

    Note: the `type` field is nested at result.affected.type, NOT at the top
    level of the record.
    """
    resp = _arena_get(
        f"/qualityprocesses/{quality_process_guid}/steps/{step_guid}/affected"
    )
    if isinstance(resp, dict) and resp.get("error"):
        return resp
    results = resp.get("results", []) if isinstance(resp, dict) else []
    files_only = [
        r for r in results
        if (r.get("affected") or {}).get("type") == "FILE"
    ]
    return {"count": len(files_only), "results": files_only}

@mcp.tool()
def get_quality_process_files(guid: str) -> dict[str, Any]:
    """List ALL files across every step of a quality process (aggregator).

    Arena attaches files to QP STEPS as affected objects of type=FILE, not
    to the QP itself. This walks each step in the QP, fetches its affected
    objects, and pulls out the FILE entries.

    Important: the `type` field is nested at result.affected.type, NOT at
    the top level. Reading r["type"] returns None for every record (the
    silent-empty bug from Wave 2.1a.2). Use (r.get("affected") or {}).get("type").

    Also surfaces ITEM, CHANGE, and QUALITY affecteds in `related_affected`
    so callers can chain into get_item_files / get_change_files / another
    QP for indirect file access.

    Returns:
        {
            count: <files attached directly to steps>,
            results: [<FILE-typed affected>, ...] each tagged with
                `_step: {guid, name}`,
            related_affected: {
                items:    [<ITEM-typed affected with _step>],
                changes:  [<CHANGE-typed affected with _step>],
                quality:  [<QUALITY-typed affected with _step — these are
                           cross-referenced QPs (e.g., the CEC linked to a CAPA)>],
            },
            step_errors: [<error envelopes for any failed step fetches>],
        }
    """
    steps_resp = _arena_get(f"/qualityprocesses/{guid}/steps")
    if isinstance(steps_resp, dict) and steps_resp.get("error"):
        return {
            "error": True,
            "stage": "fetch_steps",
            "detail": steps_resp,
        }

    steps = steps_resp.get("results", []) if isinstance(steps_resp, dict) else []
    files_out: list[dict[str, Any]] = []
    items_out: list[dict[str, Any]] = []
    changes_out: list[dict[str, Any]] = []
    quality_out: list[dict[str, Any]] = []
    step_errors: list[dict[str, Any]] = []

    for step in steps:
        step_guid = step.get("guid")
        step_name = step.get("name")
        if not step_guid:
            continue

        affected_resp = _arena_get(
            f"/qualityprocesses/{guid}/steps/{step_guid}/affected"
        )
        if isinstance(affected_resp, dict) and affected_resp.get("error"):
            step_errors.append({
                "step": {"guid": step_guid, "name": step_name},
                "error": affected_resp,
            })
            continue

        affecteds = (
            affected_resp.get("results", [])
            if isinstance(affected_resp, dict) else []
        )
        for a in affecteds:
            atype = (a.get("affected") or {}).get("type")
            tagged = {**a, "_step": {"guid": step_guid, "name": step_name}}
            if atype == "FILE":
                files_out.append(tagged)
            elif atype == "ITEM":
                items_out.append(tagged)
            elif atype == "CHANGE":
                changes_out.append(tagged)
            elif atype == "QUALITY":
                quality_out.append(tagged)
            # REQUEST, SUPPLIER, SUPPLIER ITEM, URL dropped here —
            # use get_quality_process_step_affected if you need them.

    return {
        "count": len(files_out),
        "results": files_out,
        "related_affected": {
            "items": items_out,
            "changes": changes_out,
            "quality": quality_out,
        },
        "step_errors": step_errors,
    }

@mcp.tool()
def search_quality_processes(
    query: Optional[str] = None,
    number: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    owner_full_name: Optional[str] = None,
    owner_guid: Optional[str] = None,
    creator_full_name: Optional[str] = None,
    creator_guid: Optional[str] = None,
    template_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena quality processes (CAPAs, NCMRs, audits, etc.).

    Per Arena's GET /qualityprocesses spec, valid filters are: any, number,
    name, description, type, status, owner.fullName, owner.guid,
    creator.fullName, creator.guid, template.guid. The `status` param
    supports '!' negation, e.g. status='!COMPLETED'.

    Valid status values per the spec: OPEN, COMPLETED. (The application
    UI shows finer-grained step status; that's the QP attribute
    currentStep, not the searchable status.)

    Note: Arena's API does NOT accept template.name as a search attribute
    (only template.guid). To keep this tool friendly, template_name is
    resolved to a GUID internally via /settings/qualityprocesses/templates.
    Lookup is cached process-wide.

    Pagination:
      - Default limit is 100, max single-page is 400 (Arena's cap).
      - Set fetch_all=True for automatic pagination (up to ~20,000).

    Args:
        query: Free-text search (Arena's 'any', UI-bar equivalent).
        number: QP number, auto-wildcarded (e.g. 'CAPA-*').
        name: QP name, auto-wildcarded.
        description: QP description, auto-wildcarded.
        type: QP type (e.g. 'CAPA', 'NCMR', 'Audit').
        status: OPEN | COMPLETED, optionally prefixed with '!' to negate.
        owner_full_name: Owner's full name, auto-wildcarded.
        owner_guid: Owner's user GUID.
        creator_full_name: Creator's full name, auto-wildcarded.
        creator_guid: Creator's user GUID.
        template_name: Human-readable template name (e.g. 'CAPA Template').
            Resolved to GUID internally.
        limit: Single-page size (1-400). Ignored if fetch_all=True.
        offset: Pagination offset. Ignored if fetch_all=True.
        fetch_all: True to paginate through all results automatically.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query
    if number: base_params["number"] = _wildcard(number)
    if name: base_params["name"] = _wildcard(name)
    if description: base_params["description"] = _wildcard(description)
    if type: base_params["type"] = type
    if status: base_params["status"] = status
    if owner_full_name: base_params["owner.fullName"] = _wildcard(owner_full_name)
    if owner_guid: base_params["owner.guid"] = owner_guid
    if creator_full_name: base_params["creator.fullName"] = _wildcard(creator_full_name)
    if creator_guid: base_params["creator.guid"] = creator_guid

    # Resolve template name → guid (Arena rejects template.name)
    if template_name:
        tpl_guid = _resolve_quality_template_guid(template_name)
        if tpl_guid:
            base_params["template.guid"] = tpl_guid
        else:
            return {
                "error": True,
                "reason": "unknown_quality_template",
                "message": (
                    f"No quality template named {template_name!r} in "
                    f"/settings/qualityprocesses/templates. Use list_quality_templates "
                    f"to see valid names."
                ),
            }

    if fetch_all:
        return _paginate_get("/qualityprocesses", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/qualityprocesses", params=base_params)

@mcp.tool()
def get_quality_process(guid: str) -> dict[str, Any]:
    """Get full details of a single quality process by GUID.

    The 'currentStep' field is important — most write operations (adding
    affected items, completing steps) target a specific step GUID.
    """
    return _arena_get(f"/qualityprocesses/{guid}")

@mcp.tool()
def list_quality_templates(active_only: bool = False) -> dict[str, Any]:
    """List quality process templates (CAPA, NCMR, audit, etc.).

    Returns template GUIDs to use when creating quality processes.
    Arena's /settings/qualityprocesses/templates endpoint does not
    paginate — it returns all templates in one response. Only 'name'
    and 'active' are valid search params.
    """
    params: dict[str, Any] = {}
    if active_only:
        params["active"] = "true"
    return _arena_get("/settings/qualityprocesses/templates",
                      params=params if params else None)

@mcp.tool()
def create_quality_process(
    name: str,
    template_guid: str,
    number_format_prefix_guid: Optional[str] = None,
    description: Optional[str] = None,
    owner_guid: Optional[str] = None,
    type_value: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new quality process.

    Args:
        name: Title (Arena calls this 'name' for QPs, unlike changes).
        template_guid: From list_quality_templates.
        number_format_prefix_guid: GUID of the number-format prefix. Required
            if the template doesn't have a default; check template settings.
        description: Description body.
        owner_guid: Required if template has no default owner.
        type_value: Optional QP type string (template-specific).
        additional_attributes: List of {"guid": "<attr-guid>", "value": ...}.
        dry_run: Preview without sending.
    """
    template: dict[str, Any] = {"guid": template_guid}
    if number_format_prefix_guid:
        template["numberFormat"] = {"prefix": {"guid": number_format_prefix_guid}}
    body: dict[str, Any] = {"name": name, "template": template}
    if description is not None:
        body["description"] = description
    if owner_guid:
        body["owner"] = {"guid": owner_guid}
    if type_value:
        body["type"] = type_value
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/qualityprocesses", "body": body}
    return _arena_post("/qualityprocesses", body=body)

@mcp.tool()
def update_quality_process(
    guid: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    owner_guid: Optional[str] = None,
    type_value: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update attributes on an existing quality process."""
    body: dict[str, Any] = {}
    if name is not None: body["name"] = name
    if description is not None: body["description"] = description
    if owner_guid is not None: body["owner"] = {"guid": owner_guid}
    if type_value is not None: body["type"] = type_value
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes

    if not body:
        return {"error": True, "message": "No fields provided to update."}

    if dry_run:
        return {"dry_run": True, "would_put_to": f"/qualityprocesses/{guid}", "body": body}

    snap_info: dict[str, Any] = {}
    if snapshot_first:
        current = _arena_get(f"/qualityprocesses/{guid}")
        if isinstance(current, dict) and not current.get("error"):
            snap_info = _write_snapshot(
                label=f"pre-update QP {current.get('number', guid)}",
                kind="qp_update",
                captures=[{"endpoint": f"/qualityprocesses/{guid}", "data": current}],
            )

    result = _arena_put(f"/qualityprocesses/{guid}", body=body)
    if snap_info:
        result = {"snapshot": snap_info, "result": result}
    return result

@mcp.tool()
def update_quality_process_step(
    quality_process_guid: str,
    step_guid: str,
    attributes: Optional[list[dict[str, Any]]] = None,
    assignee_user_guids: Optional[list[str]] = None,
    due_date_time: Optional[str] = None,
    setnull: bool = False,
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Set attribute values (and optionally assignee/due date) on a QP step.

    Spec: PUT /qualityprocesses/<GUID>/steps/<GUID> (pages 685/690/694).
    Editable fields per spec: attribute values, assignees, dueDateTime.

    IMPORTANT — spec field-name discrepancy vs the QP-level PUT:
    - update_quality_process (QP body) uses body field "additionalAttributes"
    - update_quality_process_step (step body) uses body field "attributes"
    Different field names for the same concept. This tool handles that.

    Arena itself will reject writes to a COMPLETE / CANCELED step
    (returns 400). This tool does not pre-check step status — it lets
    Arena's own permission model handle it. If you get a 400 back, the
    step's current status is in the response.

    Args:
        quality_process_guid: QP GUID.
        step_guid: Step GUID within that QP.
        attributes: List of {"guid": "<attribute-def-guid>", "value": <value>}
            entries. Value type must match the attribute's fieldType:
              SINGLE_LINE_TEXT / MULTI_LINE_TEXT: string
              FIXED_DROP_DOWN (single-select): the option string, exact match
              FIXED_DROP_DOWN (multiSelect=true): array of option strings
              DATE: ISO-8601 "YYYY-MM-DD"
              DATETIME: ISO-8601 with time+timezone
              NUMBER: numeric
            Attribute-def GUIDs and their possible-values lists are readable
            via list_quality_process_step_attributes(include_possible_values=True)
            or list_quality_process_template_attributes(template_guid).
        assignee_user_guids: Optional list of user GUIDs to reassign the step.
        due_date_time: Optional ISO-8601 datetime (date portion honored;
            time always appears as 23:59:59 local).
        setnull: If True, appends ?setnull=true to the URL. Required when
            passing null in the body to explicitly clear a field. Without
            this, null values in the body are ignored by Arena.
        snapshot_first: If True, capture current step state before writing.
        dry_run: If True, return the request body without sending.

    Returns the full updated step object on success (201) or the error body
    on failure (400). The response includes the complete attribute schema,
    which is useful for discovering the definition GUIDs and names of
    unpopulated attributes on the step.
    """
    body: dict[str, Any] = {}
    if attributes is not None:
        body["attributes"] = attributes
    if assignee_user_guids is not None:
        body["assignees"] = {
            "users": [{"guid": g} for g in assignee_user_guids]
        }
    if due_date_time is not None:
        body["dueDateTime"] = due_date_time

    if not body:
        return {"error": True, "message": "No writable fields provided."}

    path = f"/qualityprocesses/{quality_process_guid}/steps/{step_guid}"
    if setnull:
        path += "?setnull=true"

    if dry_run:
        return {
            "dry_run": True,
            "would_put_to": path,
            "body": body,
        }

    snap_info: dict[str, Any] = {}
    if snapshot_first:
        step_data = _arena_get(
            f"/qualityprocesses/{quality_process_guid}/steps/{step_guid}"
        )
        if isinstance(step_data, dict) and not step_data.get("error"):
            snap_info = _write_snapshot(
                label=(
                    f"pre-update QP step "
                    f"{step_data.get('name', step_guid)} "
                    f"(qp {quality_process_guid[:8]}...)"
                ),
                kind="qp_step_update",
                captures=[{
                    "endpoint": (
                        f"/qualityprocesses/{quality_process_guid}"
                        f"/steps/{step_guid}"
                    ),
                    "data": step_data,
                }],
            )

    result = _arena_put(path, body=body)
    if snap_info:
        result = {"snapshot": snap_info, "result": result}
    return result

@mcp.tool()
def complete_quality_process_step(
    quality_process_guid: str,
    step_guid: str,
    comment: Optional[str] = None,
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Complete (mark done) a REGULAR quality-process step.

    Spec: POST /qualityprocesses/statuschanges (page 701).
    Body shape: {qualityProcess: {guid, step: {guid}}, complete: true, comment}.
    Same endpoint as route_quality_process / close_quality_process but the
    body differentiates the operation (nested step.guid + complete=true).

    Response returns the parent QP with currentStep advanced to the next
    step in the workflow.

    Notes (per spec):
      - REGULAR steps only. SIGNOFF steps must use "make decision" instead
        (not yet exposed as a tool — build when needed).
      - Assigned steps: can be completed by the step assignee OR the QP owner.
      - Unassigned steps: any user with permissions.
      - Cannot complete if the parent QP is already COMPLETED.
      - If the step is already complete, Arena returns 400 code 3089.
      - Access Policies workspaces require the "Quality Edit Details" rule.

    Args:
        quality_process_guid: QP GUID.
        step_guid: Step GUID within that QP.
        comment: Optional comment (recorded in the QP history — recommended
            for audit trail).
        snapshot_first: Capture step state before completing. Default True.
        dry_run: Preview without sending.

    Returns the parent QP payload with currentStep advanced on success, or
    an error body (400 + code) on failure.
    """
    body: dict[str, Any] = {
        "qualityProcess": {
            "guid": quality_process_guid,
            "step": {"guid": step_guid},
        },
        "complete": True,
    }
    if comment:
        body["comment"] = comment

    if dry_run:
        return {
            "dry_run": True,
            "would_post_to": "/qualityprocesses/statuschanges",
            "body": body,
        }

    snap_info: dict[str, Any] = {}
    if snapshot_first:
        step_data = _arena_get(
            f"/qualityprocesses/{quality_process_guid}/steps/{step_guid}"
        )
        if isinstance(step_data, dict) and not step_data.get("error"):
            snap_info = _write_snapshot(
                label=(
                    f"pre-complete QP step "
                    f"{step_data.get('name', step_guid)} "
                    f"(qp {quality_process_guid[:8]}...)"
                ),
                kind="qp_step_complete",
                captures=[{
                    "endpoint": (
                        f"/qualityprocesses/{quality_process_guid}"
                        f"/steps/{step_guid}"
                    ),
                    "data": step_data,
                }],
            )

    result = _arena_post("/qualityprocesses/statuschanges", body=body)
    if snap_info:
        result = {"snapshot": snap_info, "result": result}
    return result

@mcp.tool()
def reopen_quality_process_step(
    quality_process_guid: str,
    step_guid: str,
    comment: Optional[str] = None,
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Reopen a completed REGULAR quality-process step.

    Spec: POST /qualityprocesses/statuschanges (page 703).
    Same endpoint + body shape as complete_quality_process_step, but with
    complete=false. Sensible pair for undo.

    Notes (per spec):
      - REGULAR steps only. Approved SIGNOFF steps cannot be reopened via
        this endpoint (they'd need workflow-level reversal).
      - Assigned steps: reopened by the step assignee OR the QP owner.
      - Unassigned steps: any user with permissions.
      - Cannot reopen if the parent QP is already COMPLETED.
      - Access Policies workspaces require the "Quality Edit Details" rule.

    Args:
        quality_process_guid: QP GUID.
        step_guid: Step GUID to reopen.
        comment: Optional comment (recorded in QP history — recommended for
            audit trail explaining why the step was reopened).
        snapshot_first: Capture step state before reopening. Default True.
        dry_run: Preview without sending.
    """
    body: dict[str, Any] = {
        "qualityProcess": {
            "guid": quality_process_guid,
            "step": {"guid": step_guid},
        },
        "complete": False,
    }
    if comment:
        body["comment"] = comment

    if dry_run:
        return {
            "dry_run": True,
            "would_post_to": "/qualityprocesses/statuschanges",
            "body": body,
        }

    snap_info: dict[str, Any] = {}
    if snapshot_first:
        step_data = _arena_get(
            f"/qualityprocesses/{quality_process_guid}/steps/{step_guid}"
        )
        if isinstance(step_data, dict) and not step_data.get("error"):
            snap_info = _write_snapshot(
                label=(
                    f"pre-reopen QP step "
                    f"{step_data.get('name', step_guid)} "
                    f"(qp {quality_process_guid[:8]}...)"
                ),
                kind="qp_step_reopen",
                captures=[{
                    "endpoint": (
                        f"/qualityprocesses/{quality_process_guid}"
                        f"/steps/{step_guid}"
                    ),
                    "data": step_data,
                }],
            )

    result = _arena_post("/qualityprocesses/statuschanges", body=body)
    if snap_info:
        result = {"snapshot": snap_info, "result": result}
    return result

@mcp.tool()
def add_affected_to_quality_step(
    quality_process_guid: str,
    step_guid: str,
    affected_guid: str,
    notes: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add an affected object (item, change, supplier, etc.) to a quality step.

    Arena attaches affected objects to a STEP within a QP, not the QP itself.
    Find the current step via get_quality_process → currentStep.guid.

    Args:
        quality_process_guid: GUID of the QP.
        step_guid: GUID of the step to attach to.
        affected_guid: GUID of the object being attached (item/change/etc.).
        notes: Optional note about why this is affected.
        dry_run: Preview without sending.
    """
    body: dict[str, Any] = {"affected": {"guid": affected_guid}}
    if notes:
        body["notes"] = notes
    path = f"/qualityprocesses/{quality_process_guid}/steps/{step_guid}/affected"
    if dry_run:
        return {"dry_run": True, "would_post_to": path, "body": body}
    return _arena_post(path, body=body)

@mcp.tool()
def route_quality_process(
    guid: str,
    status: Optional[str] = None,
    complete: bool = False,
    comment: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Advance a quality process via POST /qualityprocesses/statuschanges.

    Two modes:
      - Set status (e.g. OPEN, ON_HOLD) → pass status="..."
      - Complete the QP → pass complete=True (use close_quality_process for
        the safer wrapper).

    Args:
        guid: GUID of the QP.
        status: Optional Arena status string.
        complete: If True, sets complete=true in the request.
        comment: Optional comment (recommended).
        dry_run: Preview without sending.
    """
    body: dict[str, Any] = {"qualityProcess": {"guid": guid}}
    if status:
        body["status"] = status
    if complete:
        body["complete"] = True
    if comment:
        body["comment"] = comment

    if not status and not complete:
        return {"error": True, "message": "Provide either status or complete=True."}

    if dry_run:
        return {"dry_run": True, "would_post_to": "/qualityprocesses/statuschanges", "body": body}
    return _arena_post("/qualityprocesses/statuschanges", body=body)

@mcp.tool()
def close_quality_process(
    guid: str,
    comment: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Close a quality process (complete=true).

    Uses the /qualityprocesses/statuschanges endpoint (same as route_quality_process).
    """
    body: dict[str, Any] = {
        "qualityProcess": {"guid": guid},
        "complete": True,
    }
    if comment:
        body["comment"] = comment

    if dry_run:
        current = _arena_get(f"/qualityprocesses/{guid}")
        cur = current if isinstance(current, dict) else {}
        return {
            "dry_run": True,
            "would_post_to": "/qualityprocesses/statuschanges",
            "body": body,
            "current_state": {
                "number": cur.get("number"),
                "name": cur.get("name"),
                "status": cur.get("status"),
            },
            "to_actually_close": "Re-call with dry_run=False",
        }

    current = _arena_get(f"/qualityprocesses/{guid}")
    cur = current if isinstance(current, dict) else {}
    snap_info = _write_snapshot(
        label=f"pre-close QP {cur.get('number', guid)}",
        kind="qp_close",
        captures=[{"endpoint": f"/qualityprocesses/{guid}", "data": current}],
    )
    result = _arena_post("/qualityprocesses/statuschanges", body=body)
    return {"snapshot": snap_info, "result": result}

@mcp.tool()
def get_quality_process_step(
    qp_guid: str,
    step_guid: str,
) -> dict[str, Any]:
    """Get a single quality-process workflow step by GUID.

    Returns the full step record — name, status, owner, due date,
    completion timestamp, and all step-level attributes. Use after
    get_quality_process_steps to drill into one step.
    """
    return _arena_get(f"/qualityprocesses/{qp_guid}/steps/{step_guid}")

@mcp.tool()
def get_quality_process_step_affected_record(
    qp_guid: str,
    step_guid: str,
    affected_guid: str,
) -> dict[str, Any]:
    """Get a single affected-object attached to a quality-process step.

    Use after get_quality_process_step_affected to inspect one entry's
    full detail (object type, reference notes, attachment metadata).
    """
    return _arena_get(
        f"/qualityprocesses/{qp_guid}/steps/{step_guid}/affected/{affected_guid}"
    )

@mcp.tool()
def get_quality_process_step_decisions(
    qp_guid: str,
    step_guid: str,
) -> dict[str, Any]:
    """List approval/sign-off decisions cast at a quality-process step.

    Each decision is one user's sign-off: who decided, what they
    decided (approved / rejected / abstained), when, and any notes.
    This is the FDA-relevant audit trail showing each approver's
    explicit electronic signature on a CAPA, NCMR, or other quality
    workflow.
    """
    return _arena_get(
        f"/qualityprocesses/{qp_guid}/steps/{step_guid}/decisions"
    )

@mcp.tool()
def get_quality_process_step_decision(
    qp_guid: str,
    step_guid: str,
    decision_guid: str,
) -> dict[str, Any]:
    """Get a single QP step decision (sign-off) by GUID.

    Returns one approver's full decision detail — user, decision type,
    timestamp, sign-off notes.
    """
    return _arena_get(
        f"/qualityprocesses/{qp_guid}/steps/{step_guid}/decisions/{decision_guid}"
    )

@mcp.tool()
def list_quality_process_attributes() -> dict[str, Any]:
    """List workspace-wide custom attribute definitions for quality processes."""
    return _arena_get("/settings/qualityprocesses/attributes")

@mcp.tool()
def list_quality_process_step_attributes(
    include_possible_values: bool = False,
) -> dict[str, Any]:
    """List custom attribute definitions for quality-process steps.

    Attributes that can be configured per workflow step (e.g. "Step
    duration target", "Decision rationale required").

    Args:
        include_possible_values: If True, returns each FIXED_DROP_DOWN
            attribute's full options list under `possibleValues`. Required
            for validating dropdown values before write. Default False
            for smaller responses on schema-only queries.

    Spec: GET /settings/qualityprocesses/steps/attributes
          [?includePossibleValues=true]
    """
    params: dict[str, Any] = {}
    if include_possible_values:
        params["includePossibleValues"] = "true"
    return _arena_get("/settings/qualityprocesses/steps/attributes", params=params)

@mcp.tool()
def list_quality_process_template_attributes(template_guid: str) -> dict[str, Any]:
    """List custom attributes defined on a quality-process template.

    Args:
        template_guid: QP template GUID (e.g. CAPA template, NCMR
            template).
    """
    return _arena_get(
        f"/settings/qualityprocesses/templates/{template_guid}/attributes"
    )

@mcp.tool()
def get_quality_process_template(template_guid: str) -> dict[str, Any]:
    """Get full details of a single quality-process template."""
    return _arena_get(f"/settings/qualityprocesses/templates/{template_guid}")

@mcp.tool()
def get_quality_process_number_format(format_guid: str) -> dict[str, Any]:
    """Get a single QP number format by GUID."""
    return _arena_get(f"/settings/qualityprocesses/numberformats/{format_guid}")

@mcp.tool()
def delete_quality_process(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /qualityprocesses/<GUID>. Refuses if QP is COMPLETED."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/qualityprocesses/{guid}"}
    return _arena_delete(f"/qualityprocesses/{guid}")

@mcp.tool()
def update_quality_process_step_affected(
    quality_process_guid: str, step_guid: str, affected_guid: str,
    notes: Optional[str] = None, setnull: bool = False, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /qualityprocesses/<GUID>/steps/<GUID>/affected/<GUID> — edit an
    affected-object association (typically to update notes)."""
    body: dict[str, Any] = {}
    if notes is not None:
        body["notes"] = notes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = (
        f"/qualityprocesses/{quality_process_guid}"
        f"/steps/{step_guid}/affected/{affected_guid}"
    )
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def remove_affected_from_quality_step(
    quality_process_guid: str, step_guid: str, affected_guid: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """DELETE /qualityprocesses/<GUID>/steps/<GUID>/affected/<GUID>."""
    path = (
        f"/qualityprocesses/{quality_process_guid}"
        f"/steps/{step_guid}/affected/{affected_guid}"
    )
    if dry_run:
        return {"dry_run": True, "would_delete": path}
    return _arena_delete(path)

@mcp.tool()
def add_signoff_step_decision_makers(
    quality_process_guid: str, step_guid: str,
    user_guids: Optional[list[str]] = None,
    user_group_guids: Optional[list[str]] = None,
    decision_type: str = "ALL_REQUIRED",
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /qualityprocesses/<GUID>/steps/<GUID>/decisions — add decision
    makers (approvers) to a SIGNOFF step.

    decision_type: ALL_REQUIRED, ANY_ONE_REQUIRED, N_OF_M_REQUIRED, etc.
    """
    body: dict[str, Any] = {"decisionType": decision_type, "decisionMakers": {}}
    if user_guids:
        body["decisionMakers"]["users"] = [{"guid": g} for g in user_guids]
    if user_group_guids:
        body["decisionMakers"]["userGroups"] = [{"guid": g} for g in user_group_guids]
    path = f"/qualityprocesses/{quality_process_guid}/steps/{step_guid}/decisions"
    if dry_run:
        return {"dry_run": True, "would_post_to": path, "body": body}
    return _arena_post(path, body=body)

@mcp.tool()
def make_signoff_step_decision(
    quality_process_guid: str, step_guid: str, decision_guid: str,
    decision: str, comments: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /qualityprocesses/<GUID>/steps/<GUID>/decisions/<GUID>.

    decision: APPROVED, REJECTED, ABSTAINED, etc.
    comments: recommended for audit trail.
    """
    body: dict[str, Any] = {"decision": decision}
    if comments:
        body["comments"] = comments
    path = (
        f"/qualityprocesses/{quality_process_guid}"
        f"/steps/{step_guid}/decisions/{decision_guid}"
    )
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

