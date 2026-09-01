from __future__ import annotations

from typing import Any, Optional
import json
import uuid
from datetime import datetime, timezone

from ..core import mcp, _arena_get, _arena_put
from .. import config

__all__ = [
    "snapshot_state",
    "list_snapshots",
    "get_snapshot",
    "restore_from_snapshot",
]


def _write_snapshot(label: str, kind: str, captures: list[dict[str, Any]]) -> dict[str, Any]:
    snap_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    snap = {
        "id": snap_id,
        "label": label,
        "kind": kind,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "workspace_id": config.ARENA_WORKSPACE_ID,
        "captures": captures,
    }
    path = config.SNAPSHOT_DIR / f"{snap_id}.json"
    path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return {"snapshot_id": snap_id, "path": str(path), "items_captured": len(captures)}

@mcp.tool()
def snapshot_state(
    label: str,
    object_type: str,
    object_guids: list[str],
) -> dict[str, Any]:
    """Manually capture current state of Arena objects to a local snapshot.

    Use BEFORE a bulk write you want to be able to undo.

    Args:
        label: Human-readable description.
        object_type: One of: "item", "change", "quality_process".
        object_guids: List of GUIDs to capture.
    """
    endpoint_map = {
        "item": "items",
        "change": "changes",
        "quality_process": "qualityprocesses",
    }
    if object_type not in endpoint_map:
        return {"error": True, "message": f"object_type must be one of {list(endpoint_map.keys())}"}
    captures = []
    for guid in object_guids:
        data = _arena_get(f"/{endpoint_map[object_type]}/{guid}")
        captures.append({"endpoint": f"/{endpoint_map[object_type]}/{guid}", "data": data})
    return _write_snapshot(label=label, kind=f"manual_{object_type}", captures=captures)

@mcp.tool()
def list_snapshots(limit: int = 25) -> dict[str, Any]:
    """List recent local snapshots (most recent first)."""
    files = sorted(config.SNAPSHOT_DIR.glob("*.json"), reverse=True)[:limit]
    out = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out.append({
                "id": data.get("id"),
                "label": data.get("label"),
                "kind": data.get("kind"),
                "created_at": data.get("created_at"),
                "items_captured": len(data.get("captures", [])),
                "path": str(f),
            })
        except Exception as e:
            out.append({"path": str(f), "error": f"unreadable: {e}"})
    return {"count": len(out), "snapshots": out}

@mcp.tool()
def get_snapshot(snapshot_id: str) -> dict[str, Any]:
    """Read the full contents of a snapshot file."""
    path = config.SNAPSHOT_DIR / f"{snapshot_id}.json"
    if not path.exists():
        return {"error": True, "message": f"Snapshot {snapshot_id} not found."}
    return json.loads(path.read_text(encoding="utf-8"))

@mcp.tool()
def restore_from_snapshot(snapshot_id: str, confirm: bool = False) -> dict[str, Any]:
    """Restore Arena objects to the state in a snapshot.

    Always previews unless confirm=True. Only restores safe scalar fields
    (title/name, description, owner, additionalAttributes) via PUT.
    Workflow status, affected-items lists, and other complex state are
    NOT auto-restored — by design.
    """
    path = config.SNAPSHOT_DIR / f"{snapshot_id}.json"
    if not path.exists():
        return {"error": True, "message": f"Snapshot {snapshot_id} not found."}

    snap = json.loads(path.read_text(encoding="utf-8"))
    SAFE_FIELDS = {
        "title", "name", "description", "owner", "type",
        "additionalAttributes", "approvalDeadlineDateTime",
    }
    plan = []
    for capture in snap.get("captures", []):
        endpoint = capture.get("endpoint", "")
        data = capture.get("data", {})
        if not isinstance(data, dict) or data.get("error"):
            plan.append({"endpoint": endpoint, "skipped": "no usable data in capture"})
            continue
        body = {k: v for k, v in data.items() if k in SAFE_FIELDS}
        plan.append({"endpoint": endpoint, "body": body})

    if not confirm:
        return {
            "preview": True,
            "snapshot_id": snapshot_id,
            "label": snap.get("label"),
            "kind": snap.get("kind"),
            "created_at": snap.get("created_at"),
            "would_restore": plan,
            "to_actually_restore": "Re-call with confirm=True",
        }

    results = []
    for step in plan:
        endpoint = step.get("endpoint", "")
        body = step.get("body")
        if not body:
            results.append({"endpoint": endpoint, "skipped": True})
            continue
        r = _arena_put(endpoint, body=body)
        results.append({"endpoint": endpoint, "result": r})
    return {"snapshot_id": snapshot_id, "restored": True, "results": results}

