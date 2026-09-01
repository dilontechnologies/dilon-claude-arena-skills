from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _wildcard, _paginate_get

__all__ = [
    "search_training_plans",
    "get_training_plan",
    "get_training_plan_items",
    "get_training_plan_item",
    "get_training_plan_files",
    "get_training_plan_file",
    "get_training_plan_users",
    "get_training_plan_user",
    "get_training_plan_records",
    "get_training_plan_record",
    "get_training_plan_quality_processes",
    "get_training_plan_quality_process",
    "list_training_managers",
    "create_training_plan",
    "update_training_plan",
    "delete_training_plan",
    "transition_training_plan_status",
    "add_item_to_training_plan",
    "remove_item_from_training_plan",
    "add_users_to_training_plan",
    "update_training_plan_user",
    "remove_user_from_training_plan",
    "add_file_to_training_plan",
    "remove_file_from_training_plan",
    "add_quality_process_to_training_plan",
    "remove_quality_process_from_training_plan",
]


@mcp.tool()
def search_training_plans(
    query: Optional[str] = None,
    number: Optional[str] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    manager_full_name: Optional[str] = None,
    manager_guid: Optional[str] = None,
    user_guid: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena training plans.

    Per Arena's GET /trainingplans spec, searchable attributes are:
    any, number, name, status, manager.guid, manager.fullName, user.guid.
    Valid status values: OPEN, CLOSED.

    Pagination:
      - Default limit 100, max single-page 400.
      - Set fetch_all=True to paginate through all training plans.

    Args:
        query: Free-text search (Arena's 'any', UI-bar equivalent).
        number: Training plan number, auto-wildcarded (e.g. 'TRP-*').
        name: Training plan name, auto-wildcarded.
        status: OPEN | CLOSED.
        manager_full_name: Training manager's name, auto-wildcarded.
        manager_guid: Training manager's user GUID.
        user_guid: Filter to plans that include this user as a trainee.
        limit: Single-page size (1-400). Ignored if fetch_all=True.
        offset: Pagination offset. Ignored if fetch_all=True.
        fetch_all: True to paginate through all results automatically.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query
    if number: base_params["number"] = _wildcard(number)
    if name: base_params["name"] = _wildcard(name)
    if status: base_params["status"] = status
    if manager_full_name: base_params["manager.fullName"] = _wildcard(manager_full_name)
    if manager_guid: base_params["manager.guid"] = manager_guid
    if user_guid: base_params["user.guid"] = user_guid

    if fetch_all:
        return _paginate_get("/trainingplans", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/trainingplans", params=base_params)

@mcp.tool()
def get_training_plan(guid: str) -> dict[str, Any]:
    """Get full details of a single training plan by GUID.

    Returns name, number, description, status, manager, creation date,
    due dates, and other top-level attributes. To list trainees / items /
    files / records, use the dedicated sub-endpoints.

    Args:
        guid: Training plan GUID.
    """
    return _arena_get(f"/trainingplans/{guid}")

@mcp.tool()
def get_training_plan_items(guid: str) -> dict[str, Any]:
    """List items included in a training plan.

    Items are the SOPs / WIs / forms users need to be trained on. Each
    entry includes the item's guid, number, name, and revision info.

    Args:
        guid: Training plan GUID.
    """
    return _arena_get(f"/trainingplans/{guid}/items")

@mcp.tool()
def get_training_plan_item(plan_guid: str, item_guid: str) -> dict[str, Any]:
    """Get a specific training plan ↔ item association.

    Args:
        plan_guid: Training plan GUID.
        item_guid: GUID of the item-association record (NOT the item's own
            GUID — get this from get_training_plan_items).
    """
    return _arena_get(f"/trainingplans/{plan_guid}/items/{item_guid}")

@mcp.tool()
def get_training_plan_files(guid: str) -> dict[str, Any]:
    """List files included in a training plan.

    Files attached directly to a TP (separate from files attached to items
    in the plan). Each entry includes the file's guid, number, name,
    edition, etc.

    Args:
        guid: Training plan GUID.
    """
    return _arena_get(f"/trainingplans/{guid}/files")

@mcp.tool()
def get_training_plan_file(plan_guid: str, file_guid: str) -> dict[str, Any]:
    """Get a specific training plan ↔ file association.

    Args:
        plan_guid: Training plan GUID.
        file_guid: GUID of the file-association record from get_training_plan_files.
    """
    return _arena_get(f"/trainingplans/{plan_guid}/files/{file_guid}")

@mcp.tool()
def get_training_plan_users(guid: str) -> dict[str, Any]:
    """List users (trainees) enrolled in a training plan.

    Each entry includes the user's guid, email, fullName, and the
    user's due-date for the training (null if no per-user due date set).
    This is the roster — use get_training_plan_records to see who has
    actually completed it.

    Args:
        guid: Training plan GUID.
    """
    return _arena_get(f"/trainingplans/{guid}/users")

@mcp.tool()
def get_training_plan_user(plan_guid: str, user_guid: str) -> dict[str, Any]:
    """Get a specific training plan ↔ user enrollment record.

    Args:
        plan_guid: Training plan GUID.
        user_guid: GUID of the user-enrollment record from get_training_plan_users.
    """
    return _arena_get(f"/trainingplans/{plan_guid}/users/{user_guid}")

@mcp.tool()
def get_training_plan_records(guid: str) -> dict[str, Any]:
    """List training records (completions) for a training plan.

    These are the audit-trail records — who completed the training, when,
    quiz results if applicable. Compare against get_training_plan_users to
    identify trainees who haven't yet completed required training.

    Args:
        guid: Training plan GUID.
    """
    return _arena_get(f"/trainingplans/{guid}/records")

@mcp.tool()
def get_training_plan_record(plan_guid: str, record_guid: str) -> dict[str, Any]:
    """Get full detail of a single training completion record.

    May contain more detail than the list version (quiz scores,
    signatures, completion timestamps, etc.).

    Args:
        plan_guid: Training plan GUID.
        record_guid: Training record GUID from get_training_plan_records.
    """
    return _arena_get(f"/trainingplans/{plan_guid}/records/{record_guid}")

@mcp.tool()
def get_training_plan_quality_processes(guid: str) -> dict[str, Any]:
    """List quality processes that reference this training plan.

    Useful for tracing "what CAPA / NCMR drove the creation or update of
    this training plan?"

    Args:
        guid: Training plan GUID.
    """
    return _arena_get(f"/trainingplans/{guid}/quality")

@mcp.tool()
def get_training_plan_quality_process(plan_guid: str, qp_ref_guid: str) -> dict[str, Any]:
    """Get a specific training plan ↔ quality process reference.

    Args:
        plan_guid: Training plan GUID.
        qp_ref_guid: GUID of the QP-reference record from
            get_training_plan_quality_processes (not the QP's own GUID).
    """
    return _arena_get(f"/trainingplans/{plan_guid}/quality/{qp_ref_guid}")

@mcp.tool()
def list_training_managers() -> dict[str, Any]:
    """List all designated training plan managers in the workspace.

    Returns one entry per user who can be assigned as the manager of a
    training plan. Each entry has guid, fullName, email.
    """
    return _arena_get("/settings/trainingplans/managers")

@mcp.tool()
def create_training_plan(
    name: str,
    description: Optional[str] = None,
    days_to_complete: Optional[int] = None,
    manager_guid: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /trainingplans."""
    body: dict[str, Any] = {"name": name}
    if description is not None:
        body["description"] = description
    if days_to_complete is not None:
        body["daysToComplete"] = days_to_complete
    if manager_guid is not None:
        body["manager"] = {"guid": manager_guid}
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/trainingplans", "body": body}
    return _arena_post("/trainingplans", body=body)

@mcp.tool()
def update_training_plan(
    guid: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    days_to_complete: Optional[int] = None,
    manager_guid: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False, snapshot_first: bool = True, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /trainingplans/<GUID>."""
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if days_to_complete is not None:
        body["daysToComplete"] = days_to_complete
    if manager_guid is not None:
        body["manager"] = {"guid": manager_guid}
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/trainingplans/{guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    snap: dict[str, Any] = {}
    if snapshot_first:
        cur = _arena_get(f"/trainingplans/{guid}")
        if isinstance(cur, dict) and not cur.get("error"):
            snap = _write_snapshot(
                label=f"pre-update TP {cur.get('number', guid)}",
                kind="training_plan_update",
                captures=[{"endpoint": f"/trainingplans/{guid}", "data": cur}],
            )
    r = _arena_put(path, body=body)
    return {"snapshot": snap, "result": r} if snap else r

@mcp.tool()
def delete_training_plan(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /trainingplans/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/trainingplans/{guid}"}
    return _arena_delete(f"/trainingplans/{guid}")

@mcp.tool()
def transition_training_plan_status(
    guid: str, status: str, comment: Optional[str] = None, dry_run: bool = False
) -> dict[str, Any]:
    """POST /trainingplans/statuschanges.

    status values (per spec): OPEN, CLOSED, ARCHIVED, etc.
    """
    body: dict[str, Any] = {"trainingPlan": {"guid": guid}, "status": status}
    if comment:
        body["comment"] = comment
    if dry_run:
        return {"dry_run": True, "would_post_to": "/trainingplans/statuschanges", "body": body}
    return _arena_post("/trainingplans/statuschanges", body=body)

@mcp.tool()
def add_item_to_training_plan(
    plan_guid: str, item_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """POST /trainingplans/<GUID>/items."""
    body = {"item": {"guid": item_guid}}
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/trainingplans/{plan_guid}/items", "body": body}
    return _arena_post(f"/trainingplans/{plan_guid}/items", body=body)

@mcp.tool()
def remove_item_from_training_plan(
    plan_guid: str, item_association_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /trainingplans/<GUID>/items/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/trainingplans/{plan_guid}/items/{item_association_guid}"}
    return _arena_delete(f"/trainingplans/{plan_guid}/items/{item_association_guid}")

@mcp.tool()
def add_users_to_training_plan(
    plan_guid: str, user_guids: list[str],
    due_date: Optional[str] = None, dry_run: bool = False,
) -> dict[str, Any]:
    """POST /trainingplans/<GUID>/users — enroll one or more users."""
    body: dict[str, Any] = {"users": [{"guid": g} for g in user_guids]}
    if due_date:
        body["dueDate"] = due_date
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/trainingplans/{plan_guid}/users", "body": body}
    return _arena_post(f"/trainingplans/{plan_guid}/users", body=body)

@mcp.tool()
def update_training_plan_user(
    plan_guid: str, user_association_guid: str,
    due_date: Optional[str] = None, setnull: bool = False, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /trainingplans/<GUID>/users/<GUID> — update a trainee's assignment."""
    body: dict[str, Any] = {}
    if due_date is not None:
        body["dueDate"] = due_date
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/trainingplans/{plan_guid}/users/{user_association_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def remove_user_from_training_plan(
    plan_guid: str, user_association_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /trainingplans/<GUID>/users/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/trainingplans/{plan_guid}/users/{user_association_guid}"}
    return _arena_delete(f"/trainingplans/{plan_guid}/users/{user_association_guid}")

@mcp.tool()
def add_file_to_training_plan(
    plan_guid: str, file_guid: str,
    latest_edition_association: bool = True, primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /trainingplans/<GUID>/files."""
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/trainingplans/{plan_guid}/files", "body": body}
    return _arena_post(f"/trainingplans/{plan_guid}/files", body=body)

@mcp.tool()
def remove_file_from_training_plan(
    plan_guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /trainingplans/<GUID>/files/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/trainingplans/{plan_guid}/files/{file_assoc_guid}"}
    return _arena_delete(f"/trainingplans/{plan_guid}/files/{file_assoc_guid}")

@mcp.tool()
def add_quality_process_to_training_plan(
    plan_guid: str, quality_process_guid: str, step_guid: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /trainingplans/<GUID>/quality — link the plan to a QP (and step)."""
    body: dict[str, Any] = {"quality": {"guid": quality_process_guid}}
    if step_guid:
        body["quality"]["step"] = {"guid": step_guid}
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/trainingplans/{plan_guid}/quality", "body": body}
    return _arena_post(f"/trainingplans/{plan_guid}/quality", body=body)

@mcp.tool()
def remove_quality_process_from_training_plan(
    plan_guid: str, quality_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /trainingplans/<GUID>/quality/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/trainingplans/{plan_guid}/quality/{quality_assoc_guid}"}
    return _arena_delete(f"/trainingplans/{plan_guid}/quality/{quality_assoc_guid}")

