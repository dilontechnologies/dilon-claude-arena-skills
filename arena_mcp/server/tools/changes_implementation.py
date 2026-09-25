from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get, _arena_post, _arena_put, _arena_delete, _arena_post_multipart

__all__ = [
    "get_change_implementation_files",
    "get_change_implementation_file",
    "get_change_implementation_tasks",
    "get_change_implementation_task",
    "get_change_implementation_task_notes",
    "get_change_implementation_task_note",
    "get_change_implementation_task_files",
    "get_change_implementation_task_file",
    "list_change_implementation_statuses",
    "list_change_implementation_task_templates",
    "get_change_implementation_task_template",
    "add_file_to_change_implementation",
    "remove_file_from_change_implementation",
    "create_change_implementation_task",
    "update_change_implementation_task",
    "delete_change_implementation_task",
    "create_change_implementation_task_note",
    "update_change_implementation_task_note",
    "delete_change_implementation_task_note",
    "attach_file_to_change_implementation_task",
    "remove_file_from_change_implementation_task",
    "create_change_file_markup",
    "delete_change_file_markup",
]


@mcp.tool()
def get_change_implementation_files(guid: str) -> dict[str, Any]:
    """List implementation files attached to a change.

    Implementation files are the working files attached to an Effective
    change as part of the post-release implementation workflow — typically
    revised drawings, updated SOPs, instructions to manufacturing, etc.
    Distinct from get_change_files (which lists the change-package files).
    """
    return _arena_get(f"/changes/{guid}/implementationfiles")

@mcp.tool()
def get_change_implementation_file(
    change_guid: str,
    file_assoc_guid: str,
) -> dict[str, Any]:
    """Get a single change implementation file association by GUID."""
    return _arena_get(f"/changes/{change_guid}/implementationfiles/{file_assoc_guid}")

@mcp.tool()
def get_change_implementation_tasks(guid: str) -> dict[str, Any]:
    """List implementation tasks for a change.

    Implementation tasks are the post-Effective work items spawned by a
    change — e.g. "Update ERP", "Notify Suppliers", "Update Training",
    each with an assignee, status, and due date. Tracks downstream
    follow-through after the change itself has been approved.
    """
    return _arena_get(f"/changes/{guid}/implementationtasks")

@mcp.tool()
def get_change_implementation_task(
    change_guid: str,
    task_guid: str,
) -> dict[str, Any]:
    """Get a single change implementation task by GUID.

    Returns task name, status, assignee, due date, completion timestamp,
    and full task detail.
    """
    return _arena_get(f"/changes/{change_guid}/implementationtasks/{task_guid}")

@mcp.tool()
def get_change_implementation_task_notes(
    change_guid: str,
    task_guid: str,
) -> dict[str, Any]:
    """List notes / comments left on a change implementation task.

    Notes are the audit trail of comments, status updates, and
    discussion the task's owner and reviewers leave during execution.
    """
    return _arena_get(
        f"/changes/{change_guid}/implementationtasks/{task_guid}/notes"
    )

@mcp.tool()
def get_change_implementation_task_note(
    change_guid: str,
    task_guid: str,
    note_guid: str,
) -> dict[str, Any]:
    """Get a single note on a change implementation task."""
    return _arena_get(
        f"/changes/{change_guid}/implementationtasks/{task_guid}/notes/{note_guid}"
    )

@mcp.tool()
def get_change_implementation_task_files(
    change_guid: str,
    task_guid: str,
) -> dict[str, Any]:
    """List files attached to a change implementation task.

    Task-level files are evidence/output attached during task execution
    (e.g. an ERP screenshot proving the SKU was updated, a signed
    notification letter). Distinct from change-level files.
    """
    return _arena_get(
        f"/changes/{change_guid}/implementationtasks/{task_guid}/files"
    )

@mcp.tool()
def get_change_implementation_task_file(
    change_guid: str,
    task_guid: str,
    file_assoc_guid: str,
) -> dict[str, Any]:
    """Get a single file attached to a change implementation task."""
    return _arena_get(
        f"/changes/{change_guid}/implementationtasks/{task_guid}/files/{file_assoc_guid}"
    )

@mcp.tool()
def list_change_implementation_statuses() -> dict[str, Any]:
    """List the change implementation statuses configured in the workspace.

    These are the allowed status values when transitioning a change
    between EFFECTIVE → COMPLETED or COMPLETED → EFFECTIVE. Examples
    might be "Implemented in ERP", "Pending Supplier Update", etc.
    """
    return _arena_get("/settings/changes/implementationstatuses")

@mcp.tool()
def list_change_implementation_task_templates(category_guid: str) -> dict[str, Any]:
    """List implementation task templates for a specific change category.

    Templates are pre-defined tasks that get auto-spawned on every
    change of a given category (e.g. every ECO automatically creates
    "Update ERP" and "Notify Manufacturing" tasks).

    Args:
        category_guid: Change category GUID.
    """
    return _arena_get(
        f"/settings/changes/categories/{category_guid}/implementationtemplates"
    )

@mcp.tool()
def get_change_implementation_task_template(
    category_guid: str,
    template_guid: str,
) -> dict[str, Any]:
    """Get a single change implementation task template by GUID."""
    return _arena_get(
        f"/settings/changes/categories/{category_guid}/implementationtemplates/{template_guid}"
    )

@mcp.tool()
def add_file_to_change_implementation(
    change_guid: str, file_guid: str,
    latest_edition_association: bool = True, primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /changes/<GUID>/implementationfiles — attach file to Implementation view."""
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/changes/{change_guid}/implementationfiles", "body": body}
    return _arena_post(f"/changes/{change_guid}/implementationfiles", body=body)

@mcp.tool()
def remove_file_from_change_implementation(
    change_guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /changes/<GUID>/implementationfiles/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/changes/{change_guid}/implementationfiles/{file_assoc_guid}"}
    return _arena_delete(f"/changes/{change_guid}/implementationfiles/{file_assoc_guid}")

@mcp.tool()
def create_change_implementation_task(
    change_guid: str,
    name: str,
    description: Optional[str] = None,
    assignee_user_guid: Optional[str] = None,
    due_date: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /changes/<GUID>/implementationtasks — add a post-effective task."""
    body: dict[str, Any] = {"name": name}
    if description is not None:
        body["description"] = description
    if assignee_user_guid is not None:
        body["assignee"] = {"guid": assignee_user_guid}
    if due_date is not None:
        body["dueDate"] = due_date
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/changes/{change_guid}/implementationtasks", "body": body}
    return _arena_post(f"/changes/{change_guid}/implementationtasks", body=body)

@mcp.tool()
def update_change_implementation_task(
    change_guid: str,
    task_guid: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    assignee_user_guid: Optional[str] = None,
    due_date: Optional[str] = None,
    status: Optional[str] = None,
    complete_date: Optional[str] = None,
    setnull: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /changes/<GUID>/implementationtasks/<GUID>."""
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if assignee_user_guid is not None:
        body["assignee"] = {"guid": assignee_user_guid}
    if due_date is not None:
        body["dueDate"] = due_date
    if status is not None:
        body["status"] = status
    if complete_date is not None:
        body["completeDate"] = complete_date
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/changes/{change_guid}/implementationtasks/{task_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_change_implementation_task(
    change_guid: str, task_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /changes/<GUID>/implementationtasks/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/changes/{change_guid}/implementationtasks/{task_guid}"}
    return _arena_delete(f"/changes/{change_guid}/implementationtasks/{task_guid}")

@mcp.tool()
def create_change_implementation_task_note(
    change_guid: str, task_guid: str, note_text: str, dry_run: bool = False
) -> dict[str, Any]:
    """POST /changes/<GUID>/implementationtasks/<GUID>/notes."""
    body = {"text": note_text}
    path = f"/changes/{change_guid}/implementationtasks/{task_guid}/notes"
    if dry_run:
        return {"dry_run": True, "would_post_to": path, "body": body}
    return _arena_post(path, body=body)

@mcp.tool()
def update_change_implementation_task_note(
    change_guid: str, task_guid: str, note_guid: str, note_text: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /changes/<GUID>/implementationtasks/<GUID>/notes/<GUID>."""
    body = {"text": note_text}
    path = f"/changes/{change_guid}/implementationtasks/{task_guid}/notes/{note_guid}"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)

@mcp.tool()
def delete_change_implementation_task_note(
    change_guid: str, task_guid: str, note_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /changes/<GUID>/implementationtasks/<GUID>/notes/<GUID>."""
    path = f"/changes/{change_guid}/implementationtasks/{task_guid}/notes/{note_guid}"
    if dry_run:
        return {"dry_run": True, "would_delete": path}
    return _arena_delete(path)

@mcp.tool()
def attach_file_to_change_implementation_task(
    change_guid: str, task_guid: str, file_guid: str,
    latest_edition_association: bool = True, primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /changes/<GUID>/implementationtasks/<GUID>/files — attach existing file."""
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    path = f"/changes/{change_guid}/implementationtasks/{task_guid}/files"
    if dry_run:
        return {"dry_run": True, "would_post_to": path, "body": body}
    return _arena_post(path, body=body)

@mcp.tool()
def remove_file_from_change_implementation_task(
    change_guid: str, task_guid: str, file_assoc_guid: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """DELETE /changes/<GUID>/implementationtasks/<GUID>/files/<GUID>."""
    path = (
        f"/changes/{change_guid}/implementationtasks/{task_guid}"
        f"/files/{file_assoc_guid}"
    )
    if dry_run:
        return {"dry_run": True, "would_delete": path}
    return _arena_delete(path)

@mcp.tool()
def create_change_file_markup(
    change_guid: str, title: str, local_path: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /changes/<GUID>/markupfiles — add a markup (redline) file to the change."""
    fields = {"title": title}
    if local_path:
        if dry_run:
            return {"dry_run": True, "would_upload": f"/changes/{change_guid}/markupfiles",
                    "local_path": local_path, "fields": fields}
        return _arena_post_multipart(f"/changes/{change_guid}/markupfiles", local_path,
                                      extra_fields=fields)
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/changes/{change_guid}/markupfiles",
                "body": fields}
    return _arena_post(f"/changes/{change_guid}/markupfiles", body=fields)

@mcp.tool()
def delete_change_file_markup(
    change_guid: str, markup_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /changes/<GUID>/markupfiles/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/changes/{change_guid}/markupfiles/{markup_guid}"}
    return _arena_delete(f"/changes/{change_guid}/markupfiles/{markup_guid}")

