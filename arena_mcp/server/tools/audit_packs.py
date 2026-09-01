from __future__ import annotations

from typing import Any, Optional

from ..core import mcp, _arena_get

__all__ = [
    "audit_pack_change",
    "audit_pack_capa",
    "audit_pack_supplier_impact",
    "audit_pack_item",
    "audit_pack_training_plan",
]


def _safe_call(label: str, fn, *args, errors: list, **kwargs):
    """Call a sub-primitive and capture any exception into `errors`."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        errors.append({"step": label, "error": str(e)[:300]})
        return None

@mcp.tool()
def audit_pack_change(
    change_number: str,
    verbose: bool = False,
) -> dict[str, Any]:
    """FDA-ready audit summary for one change.

    Composes search_changes → get_change → get_change_history →
    get_change_items → get_change_files → get_change_implementation_tasks
    (+ notes per task) into a single structured payload.

    Args:
        change_number: e.g. "ECO-000023" or "AC-000005".
        verbose: True returns full per-item / per-task detail. Default
            False returns summary counts and identifiers only.

    Returns a dict with sections: change, history, affected_items,
    implementation_tasks, files, errors. Each section is independently
    populated — partial results are returned if any sub-call fails.
    """
    errors: list = []

    # Resolve change number → GUID
    search_result = _safe_call(
        "search_changes",
        _arena_get, "/changes",
        params={"number": change_number, "limit": 5},
        errors=errors,
    )
    if not search_result or not search_result.get("results"):
        return {
            "change_number": change_number,
            "found": False,
            "errors": errors + [{"step": "resolve", "error": "no change matched"}],
        }
    change_summary = search_result["results"][0]
    change_guid = change_summary["guid"]

    # Full change record
    full_change = _safe_call(
        "get_change",
        _arena_get, f"/changes/{change_guid}",
        errors=errors,
    ) or {}

    # History (audit log)
    history_raw = _safe_call(
        "get_change_history",
        _arena_get, f"/changes/{change_guid}/history",
        errors=errors,
    ) or {}
    history_entries = history_raw.get("results", []) or []

    # Affected items
    items_raw = _safe_call(
        "get_change_items",
        _arena_get, f"/changes/{change_guid}/items",
        params={"limit": 400},
        errors=errors,
    ) or {}
    affected_items_raw = items_raw.get("results", []) or []

    # Files attached at change level
    files_raw = _safe_call(
        "get_change_files",
        _arena_get, f"/changes/{change_guid}/files",
        errors=errors,
    ) or {}

    # Implementation tasks + notes per task
    impl_tasks_raw = _safe_call(
        "get_change_implementation_tasks",
        _arena_get, f"/changes/{change_guid}/implementationtasks",
        errors=errors,
    ) or {}
    tasks_with_notes = []
    for task in (impl_tasks_raw.get("results", []) or []):
        task_guid = task.get("guid")
        if not task_guid:
            continue
        notes_raw = _safe_call(
            f"task_notes[{task.get('name','?')}]",
            _arena_get,
            f"/changes/{change_guid}/implementationtasks/{task_guid}/notes",
            errors=errors,
        ) or {}
        entry = {
            "guid": task_guid,
            "name": task.get("name"),
            "status": task.get("status"),
            "assignee": (task.get("assignee") or {}).get("fullName"),
            "dueDate": task.get("dueDate"),
            "completeDate": task.get("completeDate"),
            "notes_count": notes_raw.get("count", 0),
        }
        if verbose:
            entry["notes"] = notes_raw.get("results", []) or []
        tasks_with_notes.append(entry)

    # Summarize history into status transitions + approval signatures
    status_transitions = [
        {"date": e.get("date"), "from": e.get("originalValue"),
         "to": e.get("newValue"), "user": e.get("user")}
        for e in history_entries
        if e.get("property") == "Status History Id"
    ]
    approval_signatures = [
        {"date": e.get("date"), "decision": e.get("newValue"),
         "user": e.get("user")}
        for e in history_entries
        if "Change Decision Approve" in str(e.get("property") or "")
    ]
    approval_comments = [
        {"date": e.get("date"), "comment": e.get("newValue"),
         "user": e.get("user")}
        for e in history_entries
        if e.get("property") == "Change Decision Comments"
        or "Change Decision Comments:" in str(e.get("property") or "")
    ]

    # Summarize affected items
    affected_summary = []
    for it in affected_items_raw:
        new_rev = it.get("newItemRevision") or {}
        old_rev = it.get("affectedItemRevision") or {}
        affected_summary.append({
            "number": new_rev.get("number") or old_rev.get("number"),
            "name": new_rev.get("name") or old_rev.get("name"),
            "before_rev": old_rev.get("revisionNumber"),
            "after_rev": new_rev.get("revisionNumber"),
            "target_lifecycle": (it.get("newLifecyclePhase") or {}).get("name"),
            "views_modified": [
                v for v, key in [("bom","bomView"),("files","filesView"),
                                 ("sourcing","sourcingView"),("specs","specsView")]
                if (it.get(key) or {}).get("modifiedOnWorkingRev")
            ],
        })

    pack = {
        "change_number": change_number,
        "found": True,
        "change": {
            "guid": change_guid,
            "number": full_change.get("number"),
            "title": full_change.get("title"),
            "category": (full_change.get("category") or {}).get("name"),
            "status": (full_change.get("lifecycleStatus") or {}).get("type"),
            "creator": (full_change.get("creator") or {}).get("fullName"),
            "creationDateTime": full_change.get("creationDateTime"),
            "effectiveDateTime": full_change.get("effectiveDateTime"),
            "implementationStatus": full_change.get("implementationStatus"),
        },
        "audit_summary": {
            "history_entries": len(history_entries),
            "status_transitions": status_transitions,
            "approval_signatures": approval_signatures,
            "approval_comments": approval_comments,
        },
        "affected_items": {
            "count": len(affected_summary),
            "items": affected_summary,
        },
        "implementation_tasks": {
            "count": len(tasks_with_notes),
            "tasks": tasks_with_notes,
        },
        "files_at_change_level": {
            "count": files_raw.get("count", 0),
            "note": (
                "Per common QMS convention, files attach to ITEMS not changes. "
                "Use get_item_files on each affected item for actual file content."
            ),
        },
        "errors": errors,
    }
    if verbose:
        pack["raw_history"] = history_entries
    return pack

@mcp.tool()
def audit_pack_capa(
    capa_number: str,
    verbose: bool = False,
) -> dict[str, Any]:
    """FDA-ready audit summary for one CAPA / quality process.

    Composes search_quality_processes → get_quality_process →
    get_quality_process_steps → (per step) get_quality_process_step_decisions
    + get_quality_process_step_affected into a single structured payload.

    Surfaces electronic signatures explicitly, including the
    OVERRIDE_APPROVED case which produces no decision record (and is
    therefore an audit-relevant signal that admin override was used).

    Args:
        capa_number: e.g. "CAPA-000001" or any QP number.
        verbose: True returns full step-attribute detail. Default
            False returns workflow summary only.

    Returns a dict with sections: capa, workflow, affected,
    related_changes, errors.
    """
    errors: list = []

    # Resolve QP number → GUID
    search_result = _safe_call(
        "search_quality_processes",
        _arena_get, "/qualityprocesses",
        params={"number": capa_number, "limit": 5},
        errors=errors,
    )
    if not search_result or not search_result.get("results"):
        return {
            "capa_number": capa_number,
            "found": False,
            "errors": errors + [{"step": "resolve", "error": "no QP matched"}],
        }
    qp_summary = search_result["results"][0]
    qp_guid = qp_summary["guid"]

    # Full QP record
    full_qp = _safe_call(
        "get_quality_process",
        _arena_get, f"/qualityprocesses/{qp_guid}",
        errors=errors,
    ) or {}

    # Steps
    steps_raw = _safe_call(
        "get_quality_process_steps",
        _arena_get, f"/qualityprocesses/{qp_guid}/steps",
        errors=errors,
    ) or {}
    steps_list = steps_raw.get("results", []) or []

    # Per-step: decisions + affected
    workflow_steps = []
    all_affected_items: list = []
    all_affected_files: list = []
    all_affected_changes: list = []
    all_affected_quality: list = []
    signoff_with_signatures = []
    signoff_overrides = []
    collected_raw_affecteds: list = []  # raw entries before resolution

    for step in steps_list:
        step_guid = step.get("guid")
        step_name = step.get("name")
        step_type = step.get("type")
        step_status = step.get("status")
        step_decision = step.get("decision")

        decisions = []
        if step_type == "SIGNOFF":
            decisions_raw = _safe_call(
                f"decisions[{step_name}]",
                _arena_get,
                f"/qualityprocesses/{qp_guid}/steps/{step_guid}/decisions",
                errors=errors,
            ) or {}
            decisions = decisions_raw.get("results", []) or []

            if step_decision == "OVERRIDE_APPROVED":
                signoff_overrides.append({
                    "step_name": step_name,
                    "step_order": step.get("order"),
                    "complete_user": (step.get("completeUser") or {}).get("fullName"),
                    "complete_dateTime": step.get("completeDateTime"),
                    "note": "Admin override — no decision record captured",
                })
            elif decisions:
                signoff_with_signatures.append({
                    "step_name": step_name,
                    "step_order": step.get("order"),
                    "signers": [
                        {
                            "user": (d.get("user") or {}).get("fullName"),
                            "decision": d.get("decision"),
                            "decisionType": d.get("decisionType"),
                            "decisionDateTime": d.get("decisionDateTime"),
                            "comments": d.get("comments"),
                        }
                        for d in decisions
                    ],
                })

        # Affected objects on this step.
        # IMPORTANT: /qualityprocesses/<GUID>/steps/<GUID>/affected returns
        # entries shaped like:
        #   {affected: {type: "ITEM", guid: "<inner_guid>", specificRevision: bool},
        #    guid: "<assoc_guid>", addedBy: {...}, addedDateTime: ..., notes: ...}
        # NOTE the inner object only has type+guid (no nested name/number).
        # To get readable identifiers we must resolve each inner GUID by type.
        # We collect raw entries here; resolution happens in a single pass
        # after all steps are walked, with a cache to avoid duplicate fetches.
        affected_raw = _safe_call(
            f"affected[{step_name}]",
            _arena_get,
            f"/qualityprocesses/{qp_guid}/steps/{step_guid}/affected",
            errors=errors,
        ) or {}
        for a in (affected_raw.get("results", []) or []):
            inner = a.get("affected") or {}
            atype = inner.get("type")
            # URL type doesn't have a guid; the data is inline.
            # For all other types, the guid is present and we'll resolve it
            # in the second pass.
            inner_guid = inner.get("guid")
            if not atype:
                continue
            if atype != "URL" and not inner_guid:
                continue
            collected_raw_affecteds.append({
                "step_name": step_name,
                "step_order": step.get("order"),
                "atype": atype,
                "inner_guid": inner_guid,
                "specificRevision": inner.get("specificRevision"),
                "assoc_guid": a.get("guid"),
                "addedBy": (a.get("addedBy") or {}).get("fullName"),
                "addedDateTime": a.get("addedDateTime"),
                "notes": a.get("notes"),
                "qp_step_ref": (inner.get("step") or {}).get("guid"),  # QUALITY type only
                "url_link": inner.get("link"),         # URL type only
                "url_display": inner.get("display"),   # URL type only
                "url_description": inner.get("description"),  # URL type only
            })

        step_entry = {
            "order": step.get("order"),
            "name": step_name,
            "type": step_type,
            "status": step_status,
            "decision": step_decision,
            "completeDateTime": step.get("completeDateTime"),
            "completeUser": (step.get("completeUser") or {}).get("fullName"),
            "decisions_count": len(decisions),
        }
        if verbose:
            step_entry["attributes"] = step.get("attributes")
            step_entry["assignees"] = step.get("assignees")
            step_entry["decisions"] = decisions
        workflow_steps.append(step_entry)

    # ---- Resolution pass: turn (type, guid) into readable identifiers ----
    # Per spec (Quality Affected, page 1298): valid types are ITEM, REQUEST,
    # CHANGE, SUPPLIER, SUPPLIER ITEM, FILE, QUALITY, or URL.
    # For URL, the affected payload is inline (link, display, description) —
    # no resolution call needed. For all other types, fetch the parent record
    # to get readable number/name.
    # Cache keyed by (type, guid) so each unique reference is fetched once
    # even if referenced from multiple steps.
    resolution_cache: dict = {}
    for raw in collected_raw_affecteds:
        key = (raw["atype"], raw["inner_guid"])
        if key in resolution_cache:
            continue
        atype, ig = key
        resolved: dict = {}
        try:
            if atype == "ITEM":
                data = _arena_get(f"/items/{ig}") or {}
                resolved = {
                    "number": data.get("number"),
                    "name": data.get("name"),
                    "revisionNumber": data.get("revisionNumber"),
                    "revisionStatus": data.get("revisionStatus"),
                }
            elif atype == "FILE":
                data = _arena_get(f"/files/{ig}") or {}
                resolved = {
                    "number": data.get("number"),
                    "name": data.get("name"),
                    "title": data.get("title"),
                }
            elif atype == "CHANGE":
                data = _arena_get(f"/changes/{ig}") or {}
                resolved = {
                    "number": data.get("number"),
                    "title": data.get("title"),
                    "status": (data.get("lifecycleStatus") or {}).get("type"),
                }
            elif atype == "QUALITY":
                # Per spec, top-level guid is the parent QP guid; the nested
                # step.guid (captured separately) is a step within that QP.
                data = _arena_get(f"/qualityprocesses/{ig}") or {}
                resolved = {
                    "number": data.get("number"),
                    "name": data.get("name"),
                    "status": data.get("status"),
                }
            elif atype == "REQUEST":
                # REQUEST affected items aren't commonly used but the spec
                # lists REQUEST as a valid affected type. Resolve to /requests/{guid}.
                data = _arena_get(f"/requests/{ig}") or {}
                resolved = {
                    "number": data.get("number"),
                    "title": data.get("title"),
                    "status": (data.get("status") or {}).get("value"),
                }
            elif atype == "SUPPLIER":
                data = _arena_get(f"/suppliers/{ig}") or {}
                resolved = {
                    "name": data.get("name"),
                    "supplierId": data.get("supplierId"),
                }
            elif atype == "SUPPLIER ITEM":
                data = _arena_get(f"/supplieritems/{ig}") or {}
                resolved = {
                    "number": data.get("number"),
                    "name": data.get("name"),
                    "supplier_name": (data.get("supplier") or {}).get("name"),
                }
            # URL type is handled inline below (no resolution call).
        except Exception as e:
            errors.append({"step": f"resolve[{atype}:{ig[:12]}]",
                           "error": str(e)[:200]})
            resolved = {"_resolution_failed": True}
        resolution_cache[key] = resolved

    # ---- Build categorized output from resolved data ----
    all_affected_requests: list = []
    all_affected_urls: list = []
    for raw in collected_raw_affecteds:
        atype = raw["atype"]
        entry = {
            "step": raw["step_name"],
            "step_order": raw["step_order"],
            "added_by": raw["addedBy"],
            "added_dateTime": raw["addedDateTime"],
            "notes": raw["notes"],
        }
        # URL handled specially: data is inline on the raw record, not via
        # resolution.
        if atype == "URL":
            entry.update({
                "link": raw.get("url_link"),
                "display": raw.get("url_display"),
                "description": raw.get("url_description"),
            })
            all_affected_urls.append(entry)
            continue

        # All non-URL types: merge resolved data
        key = (atype, raw["inner_guid"])
        resolved = resolution_cache.get(key) or {}
        entry["inner_guid"] = raw["inner_guid"]
        entry.update(resolved)
        if raw["specificRevision"] is not None:
            entry["specificRevision"] = raw["specificRevision"]
        if atype == "ITEM":
            all_affected_items.append(entry)
        elif atype == "FILE":
            all_affected_files.append(entry)
        elif atype == "CHANGE":
            all_affected_changes.append(entry)
        elif atype == "QUALITY":
            entry["referenced_step_guid"] = raw["qp_step_ref"]
            all_affected_quality.append(entry)
        elif atype == "REQUEST":
            all_affected_requests.append(entry)
        elif atype == "SUPPLIER":
            all_affected_items.append(entry)  # fold into items for now
        elif atype == "SUPPLIER ITEM":
            all_affected_items.append(entry)  # fold into items for now

    pack = {
        "capa_number": capa_number,
        "found": True,
        "capa": {
            "guid": qp_guid,
            "number": full_qp.get("number"),
            "name": full_qp.get("name"),
            "template": (full_qp.get("template") or {}).get("name"),
            "status": full_qp.get("status"),
            "creator": (full_qp.get("creator") or {}).get("fullName"),
            "creationDateTime": full_qp.get("creationDateTime"),
        },
        "workflow": {
            "step_count": len(workflow_steps),
            "complete_steps": sum(1 for s in workflow_steps if s.get("status") == "COMPLETE"),
            "open_steps": sum(1 for s in workflow_steps if s.get("status") != "COMPLETE"),
            "signoff_steps_count": sum(1 for s in workflow_steps if s.get("type") == "SIGNOFF"),
            "signoff_with_signatures": signoff_with_signatures,
            "signoff_overrides": signoff_overrides,
            "steps": workflow_steps,
        },
        "affected": {
            "items": {"count": len(all_affected_items), "list": all_affected_items},
            "files": {"count": len(all_affected_files), "list": all_affected_files},
            "changes": {"count": len(all_affected_changes), "list": all_affected_changes},
            "related_quality_processes": {
                "count": len(all_affected_quality),
                "list": all_affected_quality,
            },
            "requests": {
                "count": len(all_affected_requests),
                "list": all_affected_requests,
            },
            "urls": {
                "count": len(all_affected_urls),
                "list": all_affected_urls,
            },
        },
        "errors": errors,
    }
    return pack

@mcp.tool()
def audit_pack_supplier_impact(
    supplier_name: str,
    include_where_used: bool = True,
    verbose: bool = False,
) -> dict[str, Any]:
    """Answers "if this supplier disappears, what breaks?"

    Composes search_suppliers → get_supplier → search_supplier_items →
    (per supplier item) get_supplier_item_sourcing → (per sourced Arena
    item, optionally) get_item_where_used → get_supplier_quality_processes
    into a structured impact map.

    Args:
        supplier_name: Supplier name (auto-wildcarded). Returns first
            match if multiple suppliers share a name prefix.
        include_where_used: If True, walks each sourced Arena item up
            to its parent assemblies. Slower but more complete impact map.
            Default True.
        verbose: True returns full per-record detail. Default summary.

    Returns a dict with sections: supplier, supplier_items, sourced_arena_items,
    parent_assemblies (if include_where_used), quality_processes,
    impact_summary, errors.
    """
    errors: list = []

    # Resolve supplier
    name_param = supplier_name if "*" in supplier_name else f"{supplier_name}*"
    search_result = _safe_call(
        "search_suppliers",
        _arena_get, "/suppliers",
        params={"name": name_param, "limit": 5},
        errors=errors,
    )
    if not search_result or not search_result.get("results"):
        return {
            "supplier_name": supplier_name,
            "found": False,
            "errors": errors + [{"step": "resolve", "error": "no supplier matched"}],
        }
    sup_summary = search_result["results"][0]
    sup_guid = sup_summary["guid"]

    # Full supplier
    full_supplier = _safe_call(
        "get_supplier",
        _arena_get, f"/suppliers/{sup_guid}",
        errors=errors,
    ) or {}

    # Supplier items they offer
    items_raw = _safe_call(
        "search_supplier_items",
        _arena_get, "/supplieritems",
        params={"supplier.guid": sup_guid, "limit": 400},
        errors=errors,
    ) or {}
    supplier_items_list = items_raw.get("results", []) or []

    # For each supplier item, get the Arena items it sources
    sourced_arena_items = []
    parent_assemblies: list = []
    for si in supplier_items_list:
        si_guid = si.get("guid")
        if not si_guid:
            continue
        sourcing = _safe_call(
            f"sourcing[{si.get('number')}]",
            _arena_get, f"/supplieritems/{si_guid}/sourcing",
            errors=errors,
        ) or {}
        for src in (sourcing.get("results", []) or []):
            arena_item = src.get("item") or {}
            entry = {
                "supplier_item_number": si.get("number"),
                "supplier_item_name": si.get("name"),
                "arena_item_number": arena_item.get("number"),
                "arena_item_name": arena_item.get("name"),
                "arena_item_rev": arena_item.get("revisionNumber"),
                "arena_item_status": arena_item.get("revisionStatus"),
                "approved": src.get("approved"),
                "active_production": src.get("activeProduction"),
                "active_prototype": src.get("activePrototype"),
            }
            sourced_arena_items.append(entry)

            if include_where_used and arena_item.get("guid"):
                wu = _safe_call(
                    f"where_used[{arena_item.get('number')}]",
                    _arena_get, f"/items/{arena_item['guid']}/whereused",
                    params={"limit": 200},
                    errors=errors,
                ) or {}
                for parent in (wu.get("results", []) or []):
                    pitem = parent.get("item") or {}
                    parent_assemblies.append({
                        "sourced_item": arena_item.get("number"),
                        "parent_number": pitem.get("number"),
                        "parent_name": pitem.get("name"),
                        "parent_rev": pitem.get("revisionNumber"),
                        "parent_status": pitem.get("revisionStatus"),
                    })

    # Quality processes referencing this supplier (SCARs etc.)
    quality_raw = _safe_call(
        "supplier_quality",
        _arena_get, f"/suppliers/{sup_guid}/quality",
        errors=errors,
    ) or {}
    quality_list = quality_raw.get("results", []) or []

    # Custom attribute extraction (criticality, rating, etc.)
    custom_attrs = {}
    for attr in (full_supplier.get("additionalAttributes") or []):
        custom_attrs[attr.get("name")] = attr.get("value")

    pack = {
        "supplier_name": supplier_name,
        "found": True,
        "supplier": {
            "guid": sup_guid,
            "name": full_supplier.get("name"),
            "supplierId": full_supplier.get("supplierId"),
            "description": full_supplier.get("description"),
            "approvalStatus": full_supplier.get("approvalStatus"),
            "website": full_supplier.get("website"),
            "category": custom_attrs.get("Supplier Catagory"),
            "rating": custom_attrs.get("Supplier Rating"),
            "iso_cert_expiry": custom_attrs.get(
                "Supplier ISO or Other Quality Certificate Expiry Date"
            ),
            "last_evaluation": custom_attrs.get("Supplier Evaluation Approval Date"),
        },
        "supplier_items": {
            "count": len(supplier_items_list),
            "list": [
                {"number": si.get("number"), "name": si.get("name"),
                 "type": si.get("type")}
                for si in supplier_items_list
            ] if not verbose else supplier_items_list,
        },
        "sourced_arena_items": {
            "count": len(sourced_arena_items),
            "list": sourced_arena_items,
        },
        "parent_assemblies": (
            {"count": len(parent_assemblies), "list": parent_assemblies}
            if include_where_used else
            {"skipped": True, "note": "Pass include_where_used=True for parent rollup"}
        ),
        "quality_processes": {
            "count": len(quality_list),
            "list": [
                {"number": (q.get("quality") or {}).get("number"),
                 "name": (q.get("quality") or {}).get("name")}
                for q in quality_list
            ],
        },
        "impact_summary": {
            "supplier_items_offered": len(supplier_items_list),
            "arena_items_sourced": len(sourced_arena_items),
            "parent_assemblies_affected": len(parent_assemblies) if include_where_used else None,
            "open_quality_issues": len(quality_list),
        },
        "errors": errors,
    }
    return pack

@mcp.tool()
def audit_pack_item(
    item_number: str,
    include_bom: bool = True,
    include_where_used: bool = True,
    include_history: bool = True,
    verbose: bool = False,
) -> dict[str, Any]:
    """FDA-ready audit summary for one item.

    Returns: current effective revision details, full revision history with
    effecting changes, file attachments, BOM, where-used assemblies, quality
    processes referencing it, training plans, future changes.

    Spec-verified response shapes (all per spec p1273+):
      - /items/{guid}: full item record (number, name, revisionNumber, lifecycle)
      - /items/{guid}/revisions: list with effecting-change embedded per rev
      - /items/{guid}/files: nested file objects fully populated (no resolution
        pass needed — different shape from QP affected endpoint)
      - /items/{guid}/whereused: nested item objects in `item` field
      - /items/{guid}/quality: nested quality process objects
      - /items/{guid}/trainingplans: SUPERSET of plans referencing the item
        (per memory rule — auditors should use plan-side for canonical list)

    Args:
        item_number: e.g. "SOP-00040" or "FO-00099".
        include_bom: walk BOM lines (only meaningful for assemblies).
        include_where_used: walk parent assemblies.
        include_history: include full revision history + change history.
        verbose: True returns full per-record detail.
    """
    errors: list = []

    # Resolve item number → GUID (effective revision preferred)
    search_result = _safe_call(
        "search_items",
        _arena_get, "/items",
        params={"number": item_number, "limit": 5},
        errors=errors,
    )
    if not search_result or not search_result.get("results"):
        return {
            "item_number": item_number,
            "found": False,
            "errors": errors + [{"step": "resolve", "error": "no item matched"}],
        }
    # Prefer the EFFECTIVE revision if multiple match
    results = search_result["results"]
    effective_match = next(
        (r for r in results if r.get("revisionStatus") == "EFFECTIVE"), None
    )
    item_summary = effective_match or results[0]
    item_guid = item_summary["guid"]

    # Full item record
    full_item = _safe_call(
        "get_item",
        _arena_get, f"/items/{item_guid}",
        params={"includeEmptyAdditionalAttributes": "true"},
        errors=errors,
    ) or {}

    # File attachments — nested file objects are pre-populated
    files_raw = _safe_call(
        "get_item_files",
        _arena_get, f"/items/{item_guid}/files",
        errors=errors,
    ) or {}
    files_summary = []
    for f in (files_raw.get("results", []) or []):
        file_obj = f.get("file") or {}
        files_summary.append({
            "number": file_obj.get("number"),
            "name": file_obj.get("name"),
            "title": file_obj.get("title"),
            "category": (file_obj.get("category") or {}).get("name"),
            "view": (f.get("view") or {}).get("name"),
        })

    # Revision history with effecting changes
    revisions_summary = []
    if include_history:
        revs_raw = _safe_call(
            "get_item_revisions",
            _arena_get, f"/items/{item_guid}/revisions",
            errors=errors,
        ) or {}
        for r in (revs_raw.get("results", []) or []):
            # Per spec p251: nested object is `change` (not effectingChange);
            # top-level fields are `number` (rev letter) and `status` (int),
            # NOT revisionNumber/revisionStatus. lifecyclePhase.name is the
            # readable phase name.
            change = r.get("change") or {}
            revisions_summary.append({
                "revisionNumber": r.get("number"),
                "status_code": r.get("status"),
                "lifecyclePhase": (r.get("lifecyclePhase") or {}).get("name"),
                "effectiveDateTime": change.get("effectiveDateTime"),
                "supersededDateTime": r.get("supersededDateTime"),
                "effecting_change_number": change.get("number"),
                "effecting_change_guid": change.get("guid"),
                "deviated": change.get("deviated"),
                "notes": r.get("notes"),
            })

    # BOM (skipped for non-assemblies — Arena returns empty)
    bom_summary = None
    if include_bom:
        bom_raw = _safe_call(
            "get_item_bom",
            _arena_get, f"/items/{item_guid}/bom",
            params={"limit": 200},
            errors=errors,
        ) or {}
        bom_lines = bom_raw.get("results", []) or []
        bom_summary = {
            "count": len(bom_lines),
            "lines": [
                {
                    "child_number": (b.get("item") or {}).get("number"),
                    "child_name": (b.get("item") or {}).get("name"),
                    "child_rev": (b.get("item") or {}).get("revisionNumber"),
                    "child_status": (b.get("item") or {}).get("revisionStatus"),
                    "quantity": b.get("quantity"),
                    "lineNumber": b.get("lineNumber"),
                    "refDes": b.get("refDes"),  # spec p193 field is refDes
                    "notes": b.get("notes"),
                }
                for b in bom_lines
            ] if not verbose else bom_lines,
        }

    # Where-used (parent assemblies)
    where_used_summary = None
    if include_where_used:
        wu_raw = _safe_call(
            "get_item_where_used",
            _arena_get, f"/items/{item_guid}/whereused",
            params={"limit": 200},
            errors=errors,
        ) or {}
        parents = wu_raw.get("results", []) or []
        where_used_summary = {
            "count": len(parents),
            "parents": [
                {
                    "number": (p.get("item") or {}).get("number"),
                    "name": (p.get("item") or {}).get("name"),
                    "revisionNumber": (p.get("item") or {}).get("revisionNumber"),
                    "revisionStatus": (p.get("item") or {}).get("revisionStatus"),
                    "quantity": p.get("quantity"),
                }
                for p in parents
            ],
        }

    # Quality processes referencing this item (CAPAs, NCMRs, etc.)
    # Spec p249: response uses `qualityProcess` field, NOT `quality`.
    # Response includes notes, qualityProcess.{guid, name, number, step, type}.
    quality_raw = _safe_call(
        "get_item_quality_processes",
        _arena_get, f"/items/{item_guid}/quality",
        errors=errors,
    ) or {}
    quality_summary = [
        {
            "number": (q.get("qualityProcess") or {}).get("number"),
            "name": (q.get("qualityProcess") or {}).get("name"),
            "type": (q.get("qualityProcess") or {}).get("type"),
            "step": ((q.get("qualityProcess") or {}).get("step") or {}).get("name"),
            "notes": q.get("notes"),
        }
        for q in (quality_raw.get("results", []) or [])
    ]

    # Training plans (SUPERSET per memory rule). Spec p274: nested field is
    # `trainingplan` (all-lowercase), and only contains `number` + `guid` —
    # no name or status. Use audit_pack_training_plan for full plan detail.
    training_raw = _safe_call(
        "get_item_training_plans",
        _arena_get, f"/items/{item_guid}/trainingplans",
        errors=errors,
    ) or {}
    training_summary = [
        {
            "number": (t.get("trainingplan") or {}).get("number"),
            "guid": (t.get("trainingplan") or {}).get("guid"),
        }
        for t in (training_raw.get("results", []) or [])
    ]

    # Future / pending changes affecting this item
    future_raw = _safe_call(
        "get_item_future_changes",
        _arena_get, f"/items/{item_guid}/futurechanges",
        errors=errors,
    ) or {}
    future_changes_summary = [
        {
            "number": (c.get("change") or {}).get("number"),
            "title": (c.get("change") or {}).get("title"),
            "category": (c.get("change") or {}).get("category", {}).get("name") if isinstance(c.get("change", {}).get("category"), dict) else None,
            "effectivityType": (c.get("change") or {}).get("effectivityType"),
        }
        for c in (future_raw.get("results", []) or [])
    ]

    pack = {
        "item_number": item_number,
        "found": True,
        "item": {
            "guid": item_guid,
            "number": full_item.get("number"),
            "name": full_item.get("name"),
            "description": full_item.get("description"),
            "revisionNumber": full_item.get("revisionNumber"),
            "revisionStatus": full_item.get("revisionStatus"),
            "lifecyclePhase": (full_item.get("lifecyclePhase") or {}).get("name"),
            "category": (full_item.get("category") or {}).get("name"),
            "creator": (full_item.get("creator") or {}).get("fullName"),
            "owner": (full_item.get("owner") or {}).get("fullName"),
            "effectiveDateTime": full_item.get("effectiveDateTime"),
        },
        "files": {
            "count": len(files_summary),
            "list": files_summary,
        },
        "revision_history": {
            "count": len(revisions_summary),
            "revisions": revisions_summary,
        } if include_history else {"skipped": True},
        "bom": bom_summary if include_bom else {"skipped": True},
        "where_used": where_used_summary if include_where_used else {"skipped": True},
        "quality_processes": {
            "count": len(quality_summary),
            "list": quality_summary,
            "note": "QPs (CAPAs, NCMRs, etc.) that reference this item as an affected object.",
        },
        "training_plans": {
            "count": len(training_summary),
            "list": training_summary,
            "note": "SUPERSET: includes plans referencing item indirectly. Use audit_pack_training_plan for canonical enrollment list.",
        },
        "future_changes": {
            "count": len(future_changes_summary),
            "list": future_changes_summary,
            "note": "Pending changes (typically OPEN/SUBMITTED) affecting this item.",
        },
        "errors": errors,
    }
    return pack

@mcp.tool()
def audit_pack_training_plan(
    plan_number: str,
    include_records: bool = True,
    verbose: bool = False,
) -> dict[str, Any]:
    """FDA-ready audit summary for one training plan.

    Returns: plan record, canonical items list (direct enrollment), enrolled
    users, completion records with dates, quality processes that reference
    the plan, files attached to the plan.

    Spec-verified response shapes:
      - /trainingplans/{guid}: full plan record
      - /trainingplans/{guid}/items: items DIRECTLY enrolled in the plan
        (canonical, not the superset that item-side query returns)
      - /trainingplans/{guid}/users: users enrolled (the trainees)
      - /trainingplans/{guid}/records: completion records per user/item pair
      - /trainingplans/{guid}/quality: QPs referencing this plan
      - /trainingplans/{guid}/files: files attached at plan level

    Args:
        plan_number: e.g. "DEP TRP-000009" or "TRP-000001".
        include_records: True to fetch completion records (can be large).
        verbose: True returns full per-record detail.
    """
    errors: list = []

    # Resolve plan number → GUID
    search_result = _safe_call(
        "search_training_plans",
        _arena_get, "/trainingplans",
        params={"number": plan_number, "limit": 5},
        errors=errors,
    )
    if not search_result or not search_result.get("results"):
        return {
            "plan_number": plan_number,
            "found": False,
            "errors": errors + [{"step": "resolve", "error": "no training plan matched"}],
        }
    plan_summary = search_result["results"][0]
    plan_guid = plan_summary["guid"]

    # Full plan record
    full_plan = _safe_call(
        "get_training_plan",
        _arena_get, f"/trainingplans/{plan_guid}",
        errors=errors,
    ) or {}

    # Items directly enrolled (canonical)
    items_raw = _safe_call(
        "get_training_plan_items",
        _arena_get, f"/trainingplans/{plan_guid}/items",
        params={"limit": 400},
        errors=errors,
    ) or {}
    items_summary = [
        {
            "number": (i.get("item") or {}).get("number"),
            "name": (i.get("item") or {}).get("name"),
            "revisionNumber": (i.get("item") or {}).get("revisionNumber"),
            "revisionStatus": (i.get("item") or {}).get("revisionStatus"),
        }
        for i in (items_raw.get("results", []) or [])
    ]

    # Enrolled users (trainees). Spec p732: response has {user:{fullName,
    # email, guid}, dueDate, guid}. NO `status` or `enrollmentDateTime` field.
    users_raw = _safe_call(
        "get_training_plan_users",
        _arena_get, f"/trainingplans/{plan_guid}/users",
        params={"limit": 400},
        errors=errors,
    ) or {}
    users_summary = [
        {
            "fullName": (u.get("user") or {}).get("fullName"),
            "email": (u.get("user") or {}).get("email"),
            "dueDate": u.get("dueDate"),
        }
        for u in (users_raw.get("results", []) or [])
    ]

    # Completion records. Spec p707: response has {user:{...}, item:{...},
    # dueDate, signedDateTime, guid}. NO `status` or `completionDateTime`
    # field. We derive a synthetic completion_state from signed/due dates.
    records_summary: list = []
    records_count = 0
    if include_records:
        records_raw = _safe_call(
            "get_training_plan_records",
            _arena_get, f"/trainingplans/{plan_guid}/records",
            params={"limit": 400},
            errors=errors,
        ) or {}
        records_list = records_raw.get("results", []) or []
        records_count = len(records_list)
        # Derive completion state from signedDateTime + dueDate
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for r in records_list:
            signed = r.get("signedDateTime")
            due = r.get("dueDate")
            # Synthetic state
            if signed:
                state = "COMPLETE"
            elif due:
                try:
                    due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                    state = "OVERDUE" if due_dt < now else "IN_PROGRESS"
                except Exception:
                    state = "IN_PROGRESS"
            else:
                state = "IN_PROGRESS"
            records_summary.append({
                "user": (r.get("user") or {}).get("fullName"),
                "item_number": (r.get("item") or {}).get("number"),
                "item_name": (r.get("item") or {}).get("name"),
                "item_rev": (r.get("item") or {}).get("revisionNumber"),
                "signedDateTime": signed,
                "dueDate": due,
                "completion_state": state,  # synthetic, not from API
            })

    # Quality processes referencing this plan. Spec p714: response has
    # {quality: {guid, number, step:{guid, name}}, guid}. NO name or status.
    quality_raw = _safe_call(
        "get_training_plan_quality_processes",
        _arena_get, f"/trainingplans/{plan_guid}/quality",
        errors=errors,
    ) or {}
    quality_summary = [
        {
            "number": (q.get("quality") or {}).get("number"),
            "step": ((q.get("quality") or {}).get("step") or {}).get("name"),
        }
        for q in (quality_raw.get("results", []) or [])
    ]

    # Files attached at plan level
    files_raw = _safe_call(
        "get_training_plan_files",
        _arena_get, f"/trainingplans/{plan_guid}/files",
        errors=errors,
    ) or {}
    files_summary = [
        {
            "number": (f.get("file") or {}).get("number"),
            "name": (f.get("file") or {}).get("name"),
            "title": (f.get("file") or {}).get("title"),
        }
        for f in (files_raw.get("results", []) or [])
    ]

    # Compliance metrics (derived from synthetic completion_state)
    completion_stats: dict = {}
    if include_records and records_summary:
        completed = sum(1 for r in records_summary if r["completion_state"] == "COMPLETE")
        overdue = sum(1 for r in records_summary if r["completion_state"] == "OVERDUE")
        in_progress = sum(1 for r in records_summary if r["completion_state"] == "IN_PROGRESS")
        completion_stats = {
            "completed": completed,
            "overdue": overdue,
            "in_progress": in_progress,
            "completion_rate_pct": round(completed / max(records_count, 1) * 100, 1),
            "_note": "Completion state derived locally from signedDateTime + dueDate; not from a status field.",
        }

    pack = {
        "plan_number": plan_number,
        "found": True,
        "plan": {
            "guid": plan_guid,
            "number": full_plan.get("number"),
            "name": full_plan.get("name"),
            "description": full_plan.get("description"),
            "status": full_plan.get("status"),
            "manager": (full_plan.get("manager") or {}).get("fullName"),
            "daysToComplete": full_plan.get("daysToComplete"),
            "creationDateTime": full_plan.get("creationDateTime"),
        },
        "enrolled_items": {
            "count": len(items_summary),
            "list": items_summary,
            "note": "Canonical direct-enrollment list (different from item-side superset).",
        },
        "trainees": {
            "count": len(users_summary),
            "list": users_summary,
        },
        "training_records": {
            "count": records_count,
            "stats": completion_stats,
            "records": records_summary if verbose else records_summary[:50],
            "_truncated": records_count > 50 and not verbose,
        } if include_records else {"skipped": True},
        "related_quality_processes": {
            "count": len(quality_summary),
            "list": quality_summary,
        },
        "files": {
            "count": len(files_summary),
            "list": files_summary,
        },
        "errors": errors,
    }
    return pack

