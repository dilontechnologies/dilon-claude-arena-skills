"""
Arena PLM MCP Server (Wave 3.2 — Full write parity with Arena UI)

REST API reference (endpoint request/response shapes, error codes):
  https://api.arenasolutions.com/v1/swagger-ui/index.html
  (Arena's own live Swagger UI — authoritative, current spec, OAS 3.1).
  Raw OpenAPI JSON: https://api.arenasolutions.com/v1/v3/api-docs/RestAPIv1
  Prefer this over the unofficial aptenodytes-forsteri/arena-restapi-doc
  GitHub mirror, which is stale/incomplete in places — e.g. it doesn't
  document at all that Change reviewers/approvers ("Additional Reviewer")
  have no REST endpoint, confirmed 2026-08-31 by checking every Change-
  related path and schema in the real spec.

Full read + write access equivalent to the underlying Arena OAuth user's
own permissions in the workspace. Every non-admin write endpoint documented
in the spec is now exposed.

Changes from Wave 3.1a-3:
  Items (8 tools): create_item, update_item, delete_item,
    create_item_thumbnail_from_files_view, delete_item_thumbnail,
    change_item_lifecycle_phase, reserve_item_number,
    cancel_item_number_reservation
  BOM (7 tools): create/update/delete bom_line + settings + substitute
    create/update/delete
  Item Files (4 tools): add_existing_file_to_item, upload_item_file_content
    (multipart), update_item_file_association, remove_file_from_item
  Item Compliance (3): add/update/delete compliance declarations
  Item Sourcing (3): create/update/delete item_source
  Item References (3): create/update/delete item_reference
  Files top-level (12 tools): create/update_summary/upload_content/edition/
    correct/check_out/check_in/cancel_check_out/delete/markup CRUD
  Change writes (17 tools): all statuschanges variants, delete_change,
    update_change_affected_item, add/remove file to change + implementation,
    implementation task CRUD + notes + files, change file markup
  QP extras (5 tools): delete_quality_process, update/remove step affected,
    add_signoff_step_decision_makers, make_signoff_step_decision
  Training Plans (13 tools): full CRUD + items/users/files/quality assoc
  Suppliers (10 tools): CRUD + addresses/phones/files
  Supplier Items (7 tools): CRUD + files
  Multipart upload helper for file-content endpoints

Explicitly deferred (add on request):
  - Admin surface: employees, machine users, user groups, access policies
  - Tickets + Requests + Evaluation Issues (not commonly used, kept out of scope)
  - Exports/Extracts run + Imports run/commit (batch operations)
  - Outbound event reconcile endpoints

Changes from Wave 3.1a-2:
  - complete_quality_process_step, reopen_quality_process_step

Changes from Wave 3.1a-1:

Full read + write access equivalent to the underlying Arena OAuth user's
own permissions in the workspace. No tool-side policy gating: whatever
the user can do in the Arena UI, this MCP can do via the API.

Safety knobs (per-tool, opt-in — not policy):
- dry_run=False by default on all writes (call with dry_run=True to
  preview the request body before sending).
- snapshot_first=True by default on writes that mutate an existing
  record. Snapshots go to snapshots/ and can be inspected via
  list_snapshots / get_snapshot / restored via restore_from_snapshot.
- Arena's own permission model + workflow rules are the source of
  truth for what's allowed (e.g., a COMPLETE step will 400 on a PUT).
  The MCP does not second-guess Arena.

Wave 3.1a additions (writes area):
  - update_quality_process_step (Wave 3.1a-1):
    PUT /qualityprocesses/<GUID>/steps/<GUID>[?setnull=true]
    Writes step attribute values, assignees, dueDateTime. Body field
    is `attributes` (NOT `additionalAttributes` as the QP-level PUT
    uses — spec-verified pages 685/690/694).
  - list_quality_process_step_attributes enhanced with
    include_possible_values=True to reveal FIXED_DROP_DOWN option
    strings.

Not yet built (spec-verified, deferred by workload not by policy):
  - Item working-revision creation: not needed. Arena working revs
    exist implicitly on every item; add_items_to_change already
    handles the reference.
  - File edition + item file attach: 3-step spec-verified path
    (POST /files → POST /files/<G>/editions multipart → POST
    /items/<G>/files). Requires multipart/form-data helper. Add
    when the ECO document-revision workflow becomes a priority.

Changes from Wave 2.2j-3:
  - 2 new audit-pack macros: audit_pack_item, audit_pack_training_plan
  - Wave 2.2k (Imports, 6 tools): import definitions, runs, result/error content
  - Wave 2.2l (Integrations/Events/Activity, 14 tools): outbound integrations,
    triggers, outbound events + triggers, integration administrators,
    recent activity (user access, exports, report runs, file access),
    API usage
  - Wave 2.2m (BOM substitutes + watermarks, 4 tools): BOM substitute list +
    single, file watermark content, item file watermark content
  - Total new in this wave: 26 tools (2 macros + 24 endpoints)

Changes from Wave 2.2j-2:
  - Went back to the official spec (Quality Affected schema, page 1298,
    plus POST samples at line 31020) to verify affected-type handling.
  - Added missing REQUEST type resolution (per /requests/{guid}).
  - Added missing URL type handling (inline link/display/description,
    no resolution call needed).
  - Confirmed and documented the QUALITY type semantics: top-level guid
    is the parent QP guid; nested step.guid points to a specific step
    within that QP.
  - Spec-confirmed: valid affected types per the POST endpoint sample
    bodies are ITEM, REQUEST, CHANGE, SUPPLIER, SUPPLIER ITEM, FILE,
    QUALITY, URL. All 8 now handled in audit_pack_capa.

Changes from Wave 2.2j-1:
  - Fixed audit_pack_capa: it was silently returning 0 affected items/files/
    changes/quality on CAPAs that had real affected attachments. The
    /steps/<GUID>/affected endpoint returns only {type, guid} for each
    affected — not nested item/file/change objects. The macro now does a
    resolution pass that fetches the parent record (get_item / get_file /
    get_change / get_quality_process) per unique (type, guid) and caches
    the result so repeated references across steps cost one fetch each.

(HISTORICAL NOTE: earlier waves ran under a "reads only" policy where
write tools existed in source but were considered deferred. That policy
was lifted 2026-07-16 — see top-of-file wave note. Left here for context
on why certain design decisions look defensive; those defaults are safety
knobs, not policy locks.)

Changes from Wave 2.2g-h-i:
  - Removed buggy `get_quality_process_step_file` (targeted a non-existent
    endpoint; correct path is via get_quality_process_step_affected_record).
  - Added 3 audit-pack macro tools that compose existing read primitives
    into FDA-ready audit workflows:
      - audit_pack_change(change_number): full change lifecycle in one call
      - audit_pack_capa(capa_number): CAPA workflow + signatures + affecteds
      - audit_pack_supplier_impact(supplier_name): full supplier impact map

Changes from Wave 2.2e (Wave 2.2f tickets/requests and 2.2j exports
deliberately deferred per scope direction — not commonly used, kept out
of scope):

  Section B — Change Implementation + History + item-side completers (17):
    Change implementation:
      - get_change_implementation_files / get_change_implementation_file
      - get_change_implementation_tasks / get_change_implementation_task
      - get_change_implementation_task_notes / ...note (single)
      - get_change_implementation_task_files / ...file (single)
      - get_change_history (audit log of all property changes)
    Item-side single-getters (drill into one entry of an existing list):
      - get_item_compliance_requirement (single)
      - get_item_file (single file association)
      - get_item_source (single source relationship)
      - get_item_reference (single item-to-item ref)
      - get_item_training_plan (single TP ref)
      - get_item_training_record (single record)
      - get_item_bom_line (single BOM line, optionally with substitutes)
      - get_item_bom_settings (BOM view config)

  Section C — QP Step Decisions + step-level single-getters (5):
      - get_quality_process_step (single workflow step)
      - get_quality_process_step_affected_record (single affected obj)
      - get_quality_process_step_file (single step file)
      - get_quality_process_step_decisions (list approval sign-offs)
      - get_quality_process_step_decision (single sign-off)

  Section D — Workspace settings round-out (26):
    Items: list_item_attributes / get_item_attribute, list_item_attribute_groups,
      list_item_bom_attributes, list_item_category_attributes, get_item_category,
      list_item_number_reservations, get_item_number_format,
      list_item_requirements / get_item_requirement
    Changes: list_change_attributes, list_change_item_attributes,
      list_change_category_attributes, list_change_number_sequence_prefixes,
      get_change_category, list_change_implementation_statuses,
      list_change_implementation_task_templates / single getter
    Files: list_file_attributes
    Quality Processes: list_quality_process_attributes,
      list_quality_process_step_attributes,
      list_quality_process_template_attributes, get_quality_process_template,
      get_quality_process_number_format
    Workspace: get_arena_settings, list_export_attributes

  Deliberately deferred for later waves: ticket-domain endpoints, request /
  evaluation issue endpoints, exports/extracts, imports, integrations,
  outbound events, recent activity, BOM substitutes, file watermarks/redlines,
  user/access-control plumbing.

Changes from Wave 2.2d:

  New tools — Suppliers + Supplier Items domain (24 total):

    Suppliers (top-level + sub-collections, 10 tools):
      - search_suppliers: GET /suppliers (with pagination)
      - get_supplier: profile by GUID
      - get_supplier_addresses / get_supplier_address: addresses (list / one)
      - get_supplier_phone_numbers / get_supplier_phone_number
      - get_supplier_files / get_supplier_file: attached files
      - get_supplier_quality_processes / get_supplier_quality_process:
            SCAR, supplier audits, supplier-related CAPAs

    Supplier Items (top-level + sub-collections, 11 tools):
      - search_supplier_items: GET /supplieritems (with pagination)
      - get_supplier_item: profile by GUID (includes spec attributes)
      - get_supplier_item_thumbnail: image content (binary)
      - get_supplier_item_compliance / get_supplier_item_compliance_record
      - get_supplier_item_files / get_supplier_item_file: attached files
      - get_supplier_item_file_content: download a supplier-item file
      - get_supplier_item_quality_processes / get_supplier_item_quality_process
      - get_supplier_item_sourcing / get_supplier_item_source: which Arena
            items does this supplier item source (reverse of get_item_sourcing)

    Workspace settings (4 tools):
      - list_supplier_attributes: supplier custom attribute schema
      - list_supplier_item_attributes: supplier-item custom attribute schema
      - list_supplier_approval_statuses: Unrated/Approved/Disapproved/etc.
      - list_supplier_item_compliance_requirements: RoHS/REACH/etc. regimes

  Note: GET Supplier Item "Specs" in the spec is just /supplieritems/<GUID>
  (the regular profile), not a separate sub-endpoint. The Specs tab in the
  UI is rendered from custom attributes returned by the profile call.

Changes from Wave 2.2c:

  New tools — Training Plans domain (13 total):
    Cross-cutting:
      - search_training_plans: GET /trainingplans (with pagination)
      - list_training_managers: GET /settings/trainingplans/managers

    Plan-level (single by GUID):
      - get_training_plan: GET /trainingplans/<GUID>

    Plan sub-collections (list all):
      - get_training_plan_items: items in a TP (SOPs/WIs trained on)
      - get_training_plan_files: files attached to a TP
      - get_training_plan_users: trainees enrolled in a TP
      - get_training_plan_records: completion audit trail
      - get_training_plan_quality_processes: QPs referencing this TP

    Plan sub-records (single by GUID — full read coverage):
      - get_training_plan_item
      - get_training_plan_file
      - get_training_plan_user
      - get_training_plan_record
      - get_training_plan_quality_process

  This wave closes the QMS audit-readiness gap. With these tools you can
  answer: "who's trained on SOP-XXX Rev N?" — call get_item_training_plans
  to find the TP(s), then get_training_plan_records on each to see
  completions, and get_training_plan_users to see the roster. Diff the
  two to find overdue trainees.

Changes from Wave 2.2b:

  Search-tool pagination:
    All four search tools (search_items, search_changes, search_files,
    search_quality_processes) now support automatic pagination via
    `fetch_all=True`. When set, the tool walks all pages (using Arena's
    max page size of 400) and merges results. Safety cap at 50 pages
    (~20,000 items) to avoid runaway loops.
    Defaults bumped: limit default now 100, max single-page 400.

  New tools — item-side reverse-lookups (8 total):
    These mirror the tabs you see on an item page in the Arena UI.
    Results are returned RAW with no deduplication (e.g. a CAPA that
    references an item on two steps shows up twice in get_item_quality_processes).

    - get_item_quality_processes: QPs referencing this item (Quality tab)
    - get_item_training_plans: training plans this item is in (Training tab)
    - get_item_training_records: training records for this item
    - get_item_tickets: tickets/requests referencing this item (Tickets tab)
    - get_item_compliance: compliance records for this item (Compliance tab)
    - get_item_sourcing: sourcing relationships (Sourcing tab)
    - get_item_references: item-to-item refs (cross-refs, not BOM)
    - get_item_thumbnail: download item's thumbnail image (base64)

  Docstring updates:
    - search_changes docstring now documents common change-number
      prefixes: ECO (Engineering Change Order), AC (Admin Change — does
      NOT bump rev number, supersedes silently), DEV (Deviation —
      TEMPORARY), ECR (Engineering Change Request).

Changes from Wave 2.2a:

  Search behavior: auto-wildcard
    Arena's REST API requires an explicit trailing '*' for prefix matches,
    but the Arena web UI silently appends one. This wave makes the MCP
    tools behave like the UI by auto-appending '*' to string filters that
    don't already contain a wildcard. Applied to:
      - search_items: number, name, description, owner_full_name,
            creator_full_name
      - search_changes: number, title
      - search_files: number, name, title
      - search_quality_processes: number, name, description,
            owner_full_name, creator_full_name
    NOT applied to: GUIDs (exact match required), free-text 'any' / query
    (Arena ignores wildcards there), revisionNumber (would over-match —
    "16*" would catch 16, 160, 1600), enum/boolean/date fields.
    Pass an explicit '*' anywhere in the string to opt out of auto-wildcard.

  New tools — file reverse-lookups (11 total):
    - get_file_items: items this file is attached to
    - get_file_changes: changes referencing this file (changereferences)
    - get_file_change_implementations: changes that produced editions of
        this file under change-order control
    - get_file_quality_processes: QPs this file is attached to
    - get_file_requests: requests / tickets referencing this file
    - get_file_suppliers: suppliers this file is attached to
    - get_file_supplier_items: supplier items this file is attached to
    - get_file_training_plans: training plans that reference this file
    - get_file_corrections: errata corrections to this file's editions
    - get_file_markups: list redline / annotation overlays on the file
    - get_file_markup_content: download a specific markup's content

Changes from Wave 2.1a.3:

  Search-tool audit (cross-referenced against the official Arena REST API
  Developer Guide v2.94, July 2025):

    Bug fixes (params that were silently failing with API error code 3019):
      - search_items: lifecyclePhase.name → resolved internally to
            lifecyclePhase.guid via /settings/items/lifecyclephases.
      - search_quality_processes: template.name → resolved internally to
            template.guid via /settings/qualityprocesses/templates.
      - search_files: dropped author.fullName and storageMethodName
            params (neither is in Arena's searchable-attribute spec).

    Missing searchable attributes added:
      - search_items: + assembly_type, creator_full_name, creator_guid,
            description, revision_number, in_assembly, effective_from,
            effective_to, modified_bom, modified_files, modified_sourcing,
            modified_specs (12 total).
      - search_changes: + expiration_from, expiration_to.
      - search_files: + format (filter pdf / docx / xlsx).
      - search_quality_processes: + name, description, type, owner_guid,
            creator_full_name, creator_guid.

    New name→guid resolver helpers (_resolve_lifecycle_phase_guid,
    _resolve_quality_template_guid) with process-wide memoization.

  New tools for item revision history:
    - get_item_revisions: GET /items/<GUID>/revisions — returns the
        full revision chain with the effecting change embedded per rev.
        This is THE endpoint for reproducing Arena's "»18 - ECO-000011"
        revision dropdown.
    - get_item_history: GET /items/<GUID>/history — item audit log
        (property changes, who/when/from-value/to-value).
    - get_item_future_changes: GET /items/<GUID>/futurechanges — pending
        changes that haven't gone effective yet.

Changes from Wave 2.1a.2:
  Wave 2.1a.2's get_quality_process_files and get_quality_process_step_files
  read the affected type from r["type"] (top level), but Arena nests it at
  r["affected"]["type"]. Result: filter never matched, returned 0 files for
  every QP even when files existed.

  Fixes:
    - get_quality_process_step_files: read (r.get("affected") or {}).get("type")
    - get_quality_process_files: same, plus added a `quality` bucket to
        related_affected for QUALITY-type cross-referenced QPs (e.g., the
        CEC auto-linked to a CAPA).

Changes from Wave 2.1a:
  Wave 2.1a's get_quality_process_files used /qualityprocesses/{guid}/files,
  which does not exist (404). The real model: files attach to a QP STEP as
  an affected object of type=FILE, retrieved via
  GET /qualityprocesses/{guid}/steps/{step}/affected. Affected-object types
  are ITEM, REQUEST, CHANGE, SUPPLIER, SUPPLIER ITEM, FILE, QUALITY, URL.

  Tools changed:
    - get_quality_process_files: rewritten as an aggregator. Walks
        /qualityprocesses/{guid}/steps, then for each step fetches
        /steps/{step}/affected and filters to type=FILE. Also surfaces
        ITEM- and CHANGE-type affecteds in a `related_affected` field so
        callers can chain into get_item_files / get_change_files. Errors
        per step go into a `step_errors` list — does NOT silently swallow
        them the way Wave 2.1a.1 did (the prior attempt's try/except over
        _request() was dead code; _request returns error dicts, doesn't
        raise — fixed here with explicit `isinstance(resp, dict) and
        resp.get("error")` checks).

  Tools added:
    - get_quality_process_steps        GET /qualityprocesses/{guid}/steps
    - get_quality_process_step_affected GET .../steps/{step}/affected
    - get_quality_process_step_files   wraps step_affected, filters FILE

Changes from Wave 2.0.1 (kept from Wave 2.1a):
  Adds 7 file read tools. The big one is get_file_content which downloads
  raw file bytes from Arena and returns them base64-encoded so they can
  travel through JSON-RPC. Claude can then decode and parse PDFs, Word
  docs, etc. on its side.

  Default size cap is 10 MB to keep responses sane; pass max_size_bytes
  to override.

  New tools:
    - search_files               GET /files
    - get_file_summary           GET /files/{guid}
    - get_file_editions          GET /files/{guid}/editions
    - get_file_content           GET /files/{guid}/content  (binary)
    - get_item_files             GET /items/{guid}/files
    - get_change_files           GET /changes/{guid}/files

  New helper:
    - _request_bytes() returns raw response bytes for binary downloads.

Changes from Wave 2.0 (kept):
  Adds 11 read-only Settings-catalog tools that resolve GUIDs needed by
  the other tools (e.g. list_users gives you the creator_guid for
  search_changes; list_quality_process_number_formats gives you the
  prefix GUID for create_quality_process). All hit /settings/* and
  return catalogs without pagination (except list_users which Arena
  explicitly paginates).

  New tools:
    - list_users, get_user             /settings/users
    - list_user_groups                 /settings/usergroups
    - list_item_categories             /settings/items/categories
    - list_item_lifecycle_phases       /settings/items/lifecyclephases
    - list_item_number_formats         /settings/items/numberformats
    - list_change_administrators       /settings/changes/administrators
    - list_change_number_prefixes      /settings/changes/numberprefixes
    - list_quality_process_owners      /settings/qualityprocesses/owners
    - list_quality_process_number_formats
                                       /settings/qualityprocesses/numberformats
    - list_file_categories             /settings/files/categories

Changes from Wave 1.2 (kept from 1.3):
  - list_change_categories: dropped 'limit' param. Arena's
        /settings/changes/categories endpoint rejects 'limit' as a
        not-searchable attribute (error 3019). It returns all categories
        in one response — no pagination needed.
  - list_quality_templates: dropped 'limit' param.
  - search_changes: docstring corrected. The '!' negation operator does
        NOT work on /changes lifecycleStatus.type. The '!' operator is
        only valid on /qualityprocesses?status=.

Changes from Wave 1.1 (kept from 1.2):
  - search_changes: status_name → lifecycle_status, mapped to
        lifecycleStatus.type. owner_full_name removed (not searchable
        on /changes). Added implementation_status, effective_from,
        effective_to filters.
  - search_quality_processes: status_name → status.

Changes from Wave 1.0 (kept from 1.1):
  - list_change_categories: /categories/change → /settings/changes/categories
  - list_workflow_states renamed to list_change_routings:
        /categories/change/<guid>/workflow → /settings/changes/categories/<guid>/routings
  - list_quality_templates: /categories/qualityprocess → /settings/qualityprocesses/templates
  - get_change_workflow_status: no separate /workflow/nextstates endpoint;
        now derives status from the change object's lifecycleStatus
  - route_change, cancel_change → /changes/statuschanges
  - route_quality_process, close_quality_process → /qualityprocesses/statuschanges
  - add_quality_comment: REMOVED (no standalone endpoint)
  - create_change: now uses "title" (was "name"); supports routings + numberSequencePrefix
  - create_quality_process: uses "name"; supports template.numberFormat.prefix
  - add_items_to_change: corrected body shape (newItemRevision.guid + view flags)
  - add_items_to_quality_process: REPLACED with add_affected_to_quality_step

Auth and other plumbing unchanged.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
#
# Multiple named environments (e.g. a production workspace and a disposable
# sandbox) can be configured for one installation without putting any real
# workspace ID or credentials in a tracked file:
#
#   1. Create environments.local.json next to this file (never committed —
#      matched by .gitignore's `*.local.*` pattern). See
#      env/environments.example.json in the repo for the shape.
#   2. Set ARENA_ENVIRONMENT=<name> in .env to select one of its entries.
#      Each entry may override any of ARENA_CLIENT_ID/CLIENT_SECRET/
#      WORKSPACE_ID/TOKEN_URL/API_BASE/USAGE_REASON; anything it doesn't
#      override falls through to the plain env vars below.
#      Reconnect the MCP server after changing ARENA_ENVIRONMENT.
#
# If ARENA_ENVIRONMENT is unset (or environments.local.json doesn't exist),
# behavior is unchanged: plain ARENA_WORKSPACE_ID etc. from .env are used
# directly — this is the default, single-environment setup.

load_dotenv()


def _load_environment_overrides() -> dict[str, str]:
    env_name = os.environ.get("ARENA_ENVIRONMENT", "").strip()
    if not env_name:
        return {}
    envs_path = Path(__file__).parent / "environments.local.json"
    if not envs_path.exists():
        raise SystemExit(
            f"ARENA_ENVIRONMENT={env_name!r} is set but {envs_path} doesn't "
            "exist. Create it (see env/environments.example.json) or unset "
            "ARENA_ENVIRONMENT to use plain ARENA_WORKSPACE_ID from .env."
        )
    data = json.loads(envs_path.read_text(encoding="utf-8"))
    envs = data.get("environments", {})
    if env_name not in envs:
        raise SystemExit(
            f"ARENA_ENVIRONMENT={env_name!r} is not defined in {envs_path}. "
            f"Known environments: {sorted(envs)}."
        )
    return envs[env_name]


_ENV_OVERRIDES = _load_environment_overrides()


def _configured(key: str, env_var: str, default: str = "") -> str:
    return str(_ENV_OVERRIDES.get(key, os.environ.get(env_var, default))).strip()


ARENA_CLIENT_ID = _configured("client_id", "ARENA_CLIENT_ID")
ARENA_CLIENT_SECRET = _configured("client_secret", "ARENA_CLIENT_SECRET")
ARENA_WORKSPACE_ID = _configured("workspace_id", "ARENA_WORKSPACE_ID")

ARENA_TOKEN_URL = _configured(
    "token_url", "ARENA_TOKEN_URL", "https://oauth.bom.com/oauth2/token"
)
ARENA_API_BASE = _configured(
    "api_base", "ARENA_API_BASE", "https://api.arenasolutions.com/v1"
).rstrip("/")
ARENA_USAGE_REASON = _configured(
    "usage_reason", "ARENA_USAGE_REASON", "Claude / Arena MCP tooling"
)

SNAPSHOT_DIR = Path(
    os.environ.get("ARENA_SNAPSHOT_DIR") or Path(__file__).parent / "snapshots"
).expanduser().resolve()
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

_MISSING = [
    name for name, val in [
        ("ARENA_CLIENT_ID", ARENA_CLIENT_ID),
        ("ARENA_CLIENT_SECRET", ARENA_CLIENT_SECRET),
        ("ARENA_WORKSPACE_ID", ARENA_WORKSPACE_ID),
    ] if not val
]
if _MISSING:
    raise SystemExit(
        f"Missing required env var(s): {', '.join(_MISSING)}.\n"
        "Copy .env.example to .env and fill in your Arena Client Credentials."
    )

# ---------------------------------------------------------------------------
# Token cache
# ---------------------------------------------------------------------------

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


def _get_access_token(force_refresh: bool = False) -> str:
    now = time.time()
    if (
        not force_refresh
        and _token_cache["access_token"]
        and _token_cache["expires_at"] - now > 60
    ):
        return _token_cache["access_token"]

    resp = httpx.post(
        ARENA_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": ARENA_CLIENT_ID,
            "client_secret": ARENA_CLIENT_SECRET,
            "workspace_id": ARENA_WORKSPACE_ID,
            "arena-usage-reason": ARENA_USAGE_REASON,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"OAuth token request failed ({resp.status_code}): {resp.text}"
        )
    payload = resp.json()
    _token_cache["access_token"] = payload["access_token"]
    _token_cache["expires_at"] = now + int(payload.get("expires_in", 5399))
    return _token_cache["access_token"]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return resp.text[:2000]


def _request(
    method: str,
    path: str,
    params: Optional[dict[str, Any]] = None,
    body: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    url = f"{ARENA_API_BASE}/{path.lstrip('/')}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}

    for attempt in (1, 2):
        token = _get_access_token(force_refresh=(attempt == 2))
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Arena-Usage-Reason": ARENA_USAGE_REASON,
        }
        try:
            resp = httpx.request(
                method, url, params=clean_params, json=body, headers=headers, timeout=60.0,
            )
        except httpx.HTTPError as exc:
            return {"error": True, "exception": str(exc), "url": url}

        if resp.status_code == 401 and attempt == 1:
            continue

        if resp.status_code == 204 or not resp.content:
            return {"ok": True, "status_code": resp.status_code}

        if resp.status_code >= 400:
            return {
                "error": True,
                "status_code": resp.status_code,
                "url": str(resp.request.url),
                "method": method,
                "body": _safe_json(resp),
            }
        ct = resp.headers.get("content-type", "")
        return resp.json() if ct.startswith("application/json") else {"ok": True, "raw": resp.text[:2000]}
    return {"error": True, "message": "exhausted retries"}


def _arena_get(path, params=None): return _request("GET", path, params=params)
def _arena_post(path, body=None): return _request("POST", path, body=body)
def _arena_put(path, body=None): return _request("PUT", path, body=body)
def _arena_delete(path, params=None): return _request("DELETE", path, params=params)


# =============================================================================
# Name → GUID resolution helpers
# =============================================================================
#
# Several Arena search endpoints accept *.guid filters but NOT *.name filters.
# E.g., search_items accepts lifecyclePhase.guid but not lifecyclePhase.name;
# search_quality_processes accepts template.guid but not template.name. Passing
# the .name form silently returns unfiltered results (in some cases) or 400s
# with code 3019. To keep the tool surface friendly, these resolvers let
# callers pass human-readable names; we look up the matching GUID from the
# relevant /settings/* lookup endpoint and substitute it transparently.
#
# Cache is process-local and lives for the lifetime of the MCP server. Settings
# rarely change; if a phase or template is renamed, restart the server.

_name_guid_cache: dict[tuple[str, str], Optional[str]] = {}


def _resolve_name_to_guid(
    domain: str,
    name: str,
    settings_path: str,
    settings_params: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    """Look up the GUID for a named entity from a /settings/* endpoint.

    Returns the GUID on case-insensitive name match, or None if no match
    (in which case callers should typically drop the filter rather than
    pass an invalid GUID).

    Memoized per (domain, name.lower()).
    """
    key = (domain, name.lower())
    if key in _name_guid_cache:
        return _name_guid_cache[key]

    resp = _arena_get(settings_path, params=settings_params)
    guid: Optional[str] = None
    if isinstance(resp, dict) and not resp.get("error"):
        for entry in resp.get("results", []) or []:
            if (entry.get("name") or "").lower() == name.lower():
                guid = entry.get("guid")
                break
    _name_guid_cache[key] = guid
    return guid


def _resolve_lifecycle_phase_guid(name: str) -> Optional[str]:
    """Resolve an item lifecycle phase name (e.g. 'RELEASED', 'In Design')
    to its GUID via /settings/items/lifecyclephases."""
    return _resolve_name_to_guid(
        "lifecyclephase",
        name,
        "/settings/items/lifecyclephases",
    )


def _resolve_quality_template_guid(name: str) -> Optional[str]:
    """Resolve a quality process template name (e.g. 'CAPA', 'NCMR')
    to its GUID via /settings/qualityprocesses/templates."""
    return _resolve_name_to_guid(
        "qualitytemplate",
        name,
        "/settings/qualityprocesses/templates",
        settings_params=None,  # templates endpoint rejects limit per Wave 1 findings
    )


def _wildcard(value: Optional[str]) -> Optional[str]:
    """Append a trailing '*' to make string filters behave like Arena's UI.

    Arena's REST API only does prefix matches when an explicit '*' is at
    the end of the search term, but the Arena web UI silently appends one
    for every query. This helper bridges that gap so users typing "WI" via
    these tools get the same results they'd get from the UI search box.

    Rules:
      - None or empty stays untouched.
      - If the value already contains '*' anywhere, leave it alone — the
        caller has expressed intent.
      - Otherwise append a single '*' to the end.

    Apply ONLY to fields that the Arena spec marks as string match (number,
    name, title, description, *.fullName). Do NOT apply to:
      - GUIDs (exact-match required)
      - 'any' / free-text search (Arena ignores '*' here)
      - revisionNumber (auto-wildcard would mix "16" with "160", "1600")
      - enum/boolean/date fields
    """
    if not value:
        return value
    if "*" in value:
        return value
    return value + "*"


def _paginate_get(
    path: str,
    base_params: dict[str, Any],
    page_size: int = 400,
    max_pages: int = 50,
) -> dict[str, Any]:
    """Walk all pages of a search endpoint and merge results.

    Arena search endpoints accept `limit` (max 400) and `offset` for
    pagination. This helper requests pages of `page_size` until either:
      - a page comes back with fewer than page_size results (the last page),
      - or max_pages have been fetched (safety cap, default 20,000 items),
      - or an error is encountered.

    Returns a dict with the same shape as a single page but with the
    combined results array and a `paginated: True` marker plus
    `pages_fetched` count.

    Caller's base_params will have its `limit` and `offset` overridden.
    """
    all_results: list[Any] = []
    offset = 0
    pages = 0
    while pages < max_pages:
        page_params = {**base_params, "limit": page_size, "offset": offset}
        resp = _arena_get(path, params=page_params)
        if not isinstance(resp, dict) or resp.get("error"):
            # Propagate error but attach what we've collected so far
            if isinstance(resp, dict):
                resp["partial_results"] = all_results
                resp["pages_fetched_before_error"] = pages
            return resp
        page = resp.get("results") or []
        all_results.extend(page)
        pages += 1
        if len(page) < page_size:
            break
        offset += page_size
    return {
        "count": len(all_results),
        "results": all_results,
        "paginated": True,
        "pages_fetched": pages,
        "page_size": page_size,
        "truncated_at_max_pages": pages >= max_pages,
    }


def _request_bytes(
    path: str,
    params: Optional[dict[str, Any]] = None,
    max_size_bytes: int = 10 * 1024 * 1024,  # 10 MB default cap
) -> dict[str, Any]:
    """Binary GET. Returns raw response bytes (base64-encoded in JSON envelope)
    rather than parsing as JSON. Used for file content downloads where the
    payload is the actual file bytes (PDF, DOCX, image, etc.).

    Refuses downloads larger than max_size_bytes to avoid blowing up the
    MCP/JSON-RPC channel. Caller can override per-call.
    """
    import base64

    url = f"{ARENA_API_BASE}/{path.lstrip('/')}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}

    for attempt in (1, 2):
        token = _get_access_token(force_refresh=(attempt == 2))
        headers = {
            "Authorization": f"Bearer {token}",
            "Arena-Usage-Reason": ARENA_USAGE_REASON,
        }
        try:
            resp = httpx.request(
                "GET", url, params=clean_params, headers=headers, timeout=120.0,
            )
        except httpx.HTTPError as exc:
            return {"error": True, "exception": str(exc), "url": url}

        if resp.status_code == 401 and attempt == 1:
            continue

        if resp.status_code >= 400:
            return {
                "error": True,
                "status_code": resp.status_code,
                "url": str(resp.request.url),
                "method": "GET",
                "body": _safe_json(resp),
            }

        content = resp.content
        size = len(content)
        if size > max_size_bytes:
            return {
                "error": True,
                "reason": "file_too_large",
                "size_bytes": size,
                "max_size_bytes": max_size_bytes,
                "hint": (
                    "Increase max_size_bytes to download this file. "
                    "Be aware large payloads may blow up the conversation."
                ),
                "headers": {
                    "content-type": resp.headers.get("content-type"),
                    "content-disposition": resp.headers.get("content-disposition"),
                },
            }

        return {
            "size_bytes": size,
            "content_type": resp.headers.get("content-type"),
            "content_disposition": resp.headers.get("content-disposition"),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }
    return {"error": True, "message": "exhausted retries"}


# ---------------------------------------------------------------------------
# Snapshot helper
# ---------------------------------------------------------------------------


def _write_snapshot(label: str, kind: str, captures: list[dict[str, Any]]) -> dict[str, Any]:
    snap_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    snap = {
        "id": snap_id,
        "label": label,
        "kind": kind,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "workspace_id": ARENA_WORKSPACE_ID,
        "captures": captures,
    }
    path = SNAPSHOT_DIR / f"{snap_id}.json"
    path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return {"snapshot_id": snap_id, "path": str(path), "items_captured": len(captures)}


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("arena-plm")


# =============================================================================
# Diagnostic
# =============================================================================


@mcp.tool()
def whoami() -> dict[str, Any]:
    """Verify auth is working and report Arena workspace context."""
    settings = _arena_get("/settings/arena")
    return {
        "auth": "ok" if not (isinstance(settings, dict) and settings.get("error")) else "failed",
        "workspace_id": ARENA_WORKSPACE_ID,
        "arena_version": settings.get("arenaVersionId") if isinstance(settings, dict) else None,
        "api_base": ARENA_API_BASE,
        "snapshot_dir": str(SNAPSHOT_DIR),
        "raw": settings,
    }


# =============================================================================
# Workspace Settings (lookups)
# =============================================================================
#
# Read-only catalogs that resolve workspace GUIDs for the other tools.
# All paths hit /settings/*. Most settings endpoints return everything
# in one response — only /settings/users explicitly paginates.


@mcp.tool()
def list_users(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    user_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """Search workspace users — the primary way to resolve a person's GUID
    for creator_guid / owner_guid filters on other tools.

    Args:
        first_name: First name; wildcards (*) supported.
        last_name: Last name; wildcards supported.
        full_name: Full name "First Last"; wildcards supported.
        email: Email address.
        user_type: EMPLOYEE | PARTNER | BASIC_SUPPLIER | ADVANCED_SUPPLIER | INTEGRATION.
        enabled: True for active users, False for disabled.
        limit: Max results, default 25, max 400.
        offset: Pagination offset.
    """
    params: dict[str, Any] = {"limit": min(max(limit, 1), 400), "offset": max(offset, 0)}
    if first_name: params["firstName"] = first_name
    if last_name: params["lastName"] = last_name
    if full_name: params["fullName"] = full_name
    if email: params["email"] = email
    if user_type: params["type"] = user_type
    if enabled is not None: params["enabled"] = "true" if enabled else "false"
    return _arena_get("/settings/users", params=params)


@mcp.tool()
def get_user(guid: str) -> dict[str, Any]:
    """Get a single workspace user by GUID."""
    return _arena_get(f"/settings/users/{guid}")


@mcp.tool()
def list_user_groups() -> dict[str, Any]:
    """List all user groups in the workspace.

    Returns groups with their assignability scopes (ACCESS_POLICIES,
    CHANGES, QUALITY, etc.). Only available in Access Policies–enabled
    workspaces.
    """
    return _arena_get("/settings/usergroups")


@mcp.tool()
def list_item_categories(
    path: Optional[str] = None,
    include_deleted: bool = False,
) -> dict[str, Any]:
    """List item categories.

    Args:
        path: Optional path filter (e.g. r"Item\\Assembly" returns all
            categories under Assembly). Wildcards supported.
        include_deleted: If True, also includes soft-deleted categories.
    """
    params: dict[str, Any] = {}
    if path: params["path"] = path
    if include_deleted: params["includeDeleted"] = "true"
    return _arena_get("/settings/items/categories",
                      params=params if params else None)


@mcp.tool()
def list_item_lifecycle_phases() -> dict[str, Any]:
    """List item lifecycle phases (In Design, In Production, Obsolete, etc.).

    Returns phase GUIDs to use with new_lifecycle_phase_guid in
    add_items_to_change for lifecycle transitions.
    """
    return _arena_get("/settings/items/lifecyclephases")


@mcp.tool()
def list_item_number_formats() -> dict[str, Any]:
    """List item number formats (auto-numbering schemes for new items)."""
    return _arena_get("/settings/items/numberformats")


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
def list_file_categories() -> dict[str, Any]:
    """List file categories defined in the workspace.

    Returns category GUIDs you'll use when uploading files (Wave 2.1).
    """
    return _arena_get("/settings/files/categories")


# =============================================================================
# Files (read-only)
# =============================================================================
#
# Search files, fetch metadata, walk file editions, download file content
# (returned base64-encoded), and list files associated with items, changes,
# and quality processes. Writes (upload, new edition) will come in Wave 2.1b.


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


# -----------------------------------------------------------------------------
# Wave 2.2b — File reverse-lookups
# -----------------------------------------------------------------------------
# Given a file GUID, find everything that references it: items, changes,
# quality processes, requests, suppliers, supplier items, training plans.
# Plus file-internal lookups: corrections (errata) and markups (redlines).

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
def get_item_files(guid: str) -> dict[str, Any]:
    """List files associated with an item (by item GUID).

    Returns the file-association records — each links a file to one of
    the item's "views" (BOM, Files, Sourcing, Specs). Use get_file_summary
    or get_file_content with the inner file.guid to drill in.
    """
    return _arena_get(f"/items/{guid}/files")


@mcp.tool()
def get_change_files(guid: str) -> dict[str, Any]:
    """List files associated with a change (ECO/DEV/etc. by change GUID).

    Returns file-view-association records — each entry shows which file
    is attached and in which "view" (Files-only attach vs. attach + edit
    target). Use the inner file.guid with get_file_summary / get_file_content.
    """
    return _arena_get(f"/changes/{guid}/files")


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


# =============================================================================
# Items / BOMs (read-only)
# =============================================================================


@mcp.tool()
def search_items(
    query: Optional[str] = None,
    number: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    owner_full_name: Optional[str] = None,
    creator_full_name: Optional[str] = None,
    creator_guid: Optional[str] = None,
    category_guid: Optional[str] = None,
    lifecycle_phase_name: Optional[str] = None,
    revision_number: Optional[str] = None,
    assembly_type: Optional[str] = None,
    in_assembly: Optional[bool] = None,
    effective_from: Optional[str] = None,
    effective_to: Optional[str] = None,
    modified_bom: Optional[bool] = None,
    modified_files: Optional[bool] = None,
    modified_sourcing: Optional[bool] = None,
    modified_specs: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena items. Wildcards (*) supported on string filters.

    Per Arena's GET /items spec, searchable attributes accepted are:
    any, number, name, description, owner.fullName, creator.fullName,
    creator.guid, category.guid, lifecyclePhase.guid, revisionNumber,
    assemblyType, inAssembly, effectiveDateTimeFrom/To, modifiedBom/Files/
    Sourcing/Specs.

    Pagination:
      - Default limit is 100, max single-page is 400 (Arena's cap).
      - Set fetch_all=True to paginate through ALL matching items
        automatically (up to ~20,000 — the safety cap). When fetch_all
        is True, `limit` and `offset` are ignored.

    Note: Arena's API does NOT accept lifecyclePhase.name as a search
    attribute (only .guid). To keep this tool friendly, lifecycle_phase_name
    is resolved to a GUID internally via /settings/items/lifecyclephases.
    The lookup is cached process-wide.

    Args:
        query: Free-text search (Arena's 'any'). This is what the UI's
            main search bar uses — pass plain text without wildcards.
        number: Item number, wildcards supported (e.g. 'WI-*'). The number
            field is auto-wildcarded if you don't include '*' yourself.
        name: Item name (auto-wildcarded).
        description: Item description (auto-wildcarded).
        owner_full_name: Item owner's full name (auto-wildcarded).
        creator_full_name: Item creator's full name (auto-wildcarded).
        creator_guid: Item creator's user GUID.
        category_guid: Filter by item category.
        lifecycle_phase_name: Human-readable phase name (e.g. 'RELEASED',
            'In Design'). Resolved to GUID internally.
        revision_number: Exact revision (e.g. '16', 'B').
        assembly_type: TOP_LEVEL_ASSEMBLY | ASSEMBLY | NOT_AN_ASSEMBLY.
        in_assembly: True returns only items that appear on at least one BOM.
        effective_from: ISO-8601 Zulu, items effective on/after this date.
        effective_to: ISO-8601 Zulu, items effective on/before this date.
        modified_bom / modified_files / modified_sourcing / modified_specs:
            True returns items with working-revision changes in that view.
        limit: Single-page result size (1-400). Ignored if fetch_all=True.
        offset: Starting offset for pagination. Ignored if fetch_all=True.
        fetch_all: If True, paginate through all results and return them
            combined. Bypasses limit/offset.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query  # 'any' ignores wildcards per spec
    if number: base_params["number"] = _wildcard(number)
    if name: base_params["name"] = _wildcard(name)
    if description: base_params["description"] = _wildcard(description)
    if owner_full_name: base_params["owner.fullName"] = _wildcard(owner_full_name)
    if creator_full_name: base_params["creator.fullName"] = _wildcard(creator_full_name)
    if creator_guid: base_params["creator.guid"] = creator_guid
    if category_guid: base_params["category.guid"] = category_guid
    if revision_number: base_params["revisionNumber"] = revision_number  # exact match, no wildcard
    if assembly_type: base_params["assemblyType"] = assembly_type
    if in_assembly is not None: base_params["inAssembly"] = str(in_assembly).lower()
    if effective_from: base_params["effectiveDateTimeFrom"] = effective_from
    if effective_to: base_params["effectiveDateTimeTo"] = effective_to
    if modified_bom is not None: base_params["modifiedBom"] = str(modified_bom).lower()
    if modified_files is not None: base_params["modifiedFiles"] = str(modified_files).lower()
    if modified_sourcing is not None: base_params["modifiedSourcing"] = str(modified_sourcing).lower()
    if modified_specs is not None: base_params["modifiedSpecs"] = str(modified_specs).lower()

    # Resolve lifecycle phase name → guid (Arena rejects lifecyclePhase.name)
    if lifecycle_phase_name:
        phase_guid = _resolve_lifecycle_phase_guid(lifecycle_phase_name)
        if phase_guid:
            base_params["lifecyclePhase.guid"] = phase_guid
        else:
            return {
                "error": True,
                "reason": "unknown_lifecycle_phase",
                "message": (
                    f"No item lifecycle phase named {lifecycle_phase_name!r} "
                    f"in /settings/items/lifecyclephases. Use list_item_lifecycle_phases "
                    f"to see valid names."
                ),
            }

    if fetch_all:
        return _paginate_get("/items", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/items", params=base_params)


@mcp.tool()
def get_item(guid: str) -> dict[str, Any]:
    """Get full details of a single Arena item by GUID."""
    return _arena_get(f"/items/{guid}", params={"includeEmptyAdditionalAttributes": "true"})


@mcp.tool()
def get_item_bom(guid: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """Get the Bill of Materials (BOM) for an Arena item."""
    return _arena_get(f"/items/{guid}/bom",
                      params={"limit": min(max(limit, 1), 200), "offset": max(offset, 0)})


@mcp.tool()
def get_item_where_used(guid: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """Get the parent assemblies that contain this item (where-used)."""
    return _arena_get(f"/items/{guid}/whereused",
                      params={"limit": min(max(limit, 1), 200), "offset": max(offset, 0)})


@mcp.tool()
def get_item_revisions(guid: str) -> dict[str, Any]:
    """List ALL revisions of an item with the effecting change embedded per rev.

    This is THE endpoint for reproducing Arena's revision-history dropdown
    (the "»18 - ECO-000011" display). Each entry in results includes:

      - guid:            GUID of THAT specific revision (different per rev,
                         so each rev is essentially a different Arena object).
                         Pass this guid to get_item_files / get_item_bom /
                         get_item to inspect that historical revision's state.
      - number:          Revision string ('16', '01', 'B', etc.)
      - status:          0=WORKING, 1=EFFECTIVE, 2=SUPERSEDED. Use this to
                         identify the current canonical rev (status=1).
      - change:          { number, effectiveDateTime, creationDateTime }
                         The change order (ECO/DEV/etc.) that released
                         this rev. For the WORKING rev (status=0) this may
                         be sparsely populated since it isn't bound to a
                         change yet.
      - lifecyclePhase:  { guid, name } as of this revision.
      - supersededDateTime: When this rev was superseded by a newer one,
                            or null if it's the current effective rev.

    Note: pass ANY of the item's revision GUIDs as input — Arena returns
    the full revision chain regardless of which specific rev you pass.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/revisions")


@mcp.tool()
def get_item_history(guid: str) -> dict[str, Any]:
    """Return the audit history of an item (Items > History > General subview).

    Each entry includes: action, date, user, property, originalValue,
    newValue, and the revision the change applied to.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(
        f"/items/{guid}/history",
        params={"includeEmptyAdditionalAttributes": "true"},
    )


@mcp.tool()
def get_item_future_changes(guid: str) -> dict[str, Any]:
    """List pending (future) changes that may affect this item.

    These are changes (typically OPEN/SUBMITTED) that have the item as
    an affected object but aren't yet effective. Useful for spotting
    "this SOP has an ECO in flight" without manually searching changes.

    Each entry includes change.guid, change.number, change.title,
    change.creationDateTime, change.effectivityType.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/futurechanges")


# -----------------------------------------------------------------------------
# Wave 2.2c — Item-side reverse-lookups
# -----------------------------------------------------------------------------
# These mirror what the Arena UI tabs show on each item page (Quality,
# Training, Tickets, Compliance, Sourcing, Item References, Image).
# The UI returns records RAW with no deduplication — e.g. if a CAPA
# references an item on two different steps, it shows up twice in the
# item's Quality tab. These tools preserve that behavior so output
# matches what users see in the application.

@mcp.tool()
def get_item_quality_processes(guid: str) -> dict[str, Any]:
    """List quality processes that reference this item (item's Quality tab).

    Returns one row per attachment, NOT per unique QP. If a CAPA
    references the item on multiple steps, you'll see multiple rows for
    the same CAPA — same as the Arena UI's Quality tab.

    Each entry includes the QP's guid, number, name, template,
    owner, status, and dates. To dedupe by QP, group results by guid
    client-side.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/quality")


@mcp.tool()
def get_item_training_plans(guid: str) -> dict[str, Any]:
    """List training plans that include this item (item's Training tab).

    Critical for QMS audits — answers "who needs to be trained on this
    SOP/WI?" Each entry includes training plan guid, number, name,
    training manager, and status.

    Training is commonly attached at the ITEM level (e.g. a document
    number + rev), NOT at the file level. So if you want "training plans for
    this document", use this tool on the item GUID, not on the file GUID.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/trainingplans")


@mcp.tool()
def get_item_training_records(guid: str) -> dict[str, Any]:
    """List training records associated with this item.

    Training records track individual user completions for a given
    training plan. Use this to answer "has anyone completed training
    on this item?" — though typically training records are queried
    via the training plan, not via the item directly.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/trainingrecords")


@mcp.tool()
def get_item_tickets(guid: str) -> dict[str, Any]:
    """List tickets / requests that reference this item.

    Tickets (also called Requests in Arena) are typically complaints,
    feedback, or design requests. They're often the entry point into
    a CAPA chain. Use this to trace "what complaint surfaced this part?"

    Each entry includes the ticket/request guid, number, title, status,
    creator, etc.

    Args:
        guid: GUID of any revision of the item.
    """
    return _arena_get(f"/items/{guid}/tickets")


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
def get_item_thumbnail(
    guid: str,
    max_size_bytes: int = 5 * 1024 * 1024,
) -> dict[str, Any]:
    """Download an item's thumbnail image as base64-encoded bytes.

    Items can have a thumbnail image (typically a small JPG/PNG of the
    part). Returns the image bytes the same way get_file_content does
    — base64-encoded in a JSON envelope so the MCP transport can carry it.

    Returns an empty error if the item has no thumbnail.

    Args:
        guid: GUID of any revision of the item.
        max_size_bytes: Reject downloads larger than this. Default 5 MB.
    """
    return _request_bytes(
        f"/items/{guid}/image/content",
        max_size_bytes=max_size_bytes,
    )


# =============================================================================
# Changes — reads + lookups
# =============================================================================


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


# =============================================================================
# Changes — writes
# =============================================================================


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


# =============================================================================
# Quality processes — reads + lookups
# =============================================================================


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


# =============================================================================
# Quality processes — writes
# =============================================================================


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


# =============================================================================
# Wave 2.2d — Training Plans (standalone domain)
# =============================================================================
# Training plans (TPs) hold the items, files, and users that constitute a
# training program (typically tied to SOPs/WIs). Records capture per-user
# completion. This domain is essential for QMS audit readiness — answering
# "who is trained on SOP-XXX Rev N?" and "what's overdue?"
#
# Training is commonly attached at the ITEM level. To go from a document
# to a training plan use get_item_training_plans(item_guid); then drill in
# here with the training-plan GUID for completion data.


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


# =============================================================================
# Wave 2.2e — Suppliers + Supplier Items + Sourcing
# =============================================================================
# Two parallel object types in Arena's supply-chain model:
#   - SUPPLIER: a vendor/manufacturer profile (Adaptive Circuit Boards, etc.)
#   - SUPPLIER ITEM: a specific catalog SKU offered by a supplier — the
#     part-number-as-quoted, the distributor's listing, the manufacturer's
#     P/N. Multiple supplier items can source the same internal item.
# Sourcing relationships are the link between Arena items and supplier items
# (preferred vs alternate, pricing, supplier-status). Same source-relationship
# GUID appears in both /items/<GUID>/sourcing and
# /supplieritems/<GUID>/sourcing — they're two views of the same edge.


# -----------------------------------------------------------------------------
# Suppliers
# -----------------------------------------------------------------------------

@mcp.tool()
def search_suppliers(
    query: Optional[str] = None,
    name: Optional[str] = None,
    supplier_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena suppliers (vendor / manufacturer profiles).

    Per Arena's GET /suppliers spec, only `any`, `name`, and `supplierId`
    are searchable filters (besides custom attributes by GUID). Other
    visible fields (approvalStatus, description, etc.) are NOT searchable.

    Pagination:
      - Default limit 100, max single-page 400.
      - Set fetch_all=True to paginate through all suppliers.

    Args:
        query: Free-text search (Arena's 'any', UI-bar equivalent).
        name: Supplier name, auto-wildcarded if no '*' present.
        supplier_id: Short ID (e.g. 'Adaptive'), auto-wildcarded.
        limit: Single-page size (1-400). Ignored if fetch_all=True.
        offset: Pagination offset. Ignored if fetch_all=True.
        fetch_all: True to paginate through all results automatically.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query
    if name: base_params["name"] = _wildcard(name)
    if supplier_id: base_params["supplierId"] = _wildcard(supplier_id)

    if fetch_all:
        return _paginate_get("/suppliers", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/suppliers", params=base_params)


@mcp.tool()
def get_supplier(guid: str) -> dict[str, Any]:
    """Get full profile of a single supplier by GUID.

    Returns name, supplierId, approvalStatus, description, accountNumber,
    website, creator, and custom attributes. Sub-collections (addresses,
    phone numbers, files, items, quality processes) require separate calls.
    """
    return _arena_get(f"/suppliers/{guid}")


@mcp.tool()
def get_supplier_addresses(guid: str) -> dict[str, Any]:
    """List all addresses on file for a supplier.

    Each entry includes address lines, city, region, postal code, country,
    and the address type (billing, shipping, etc.) if set.
    """
    return _arena_get(f"/suppliers/{guid}/addresses")


@mcp.tool()
def get_supplier_address(supplier_guid: str, address_guid: str) -> dict[str, Any]:
    """Get a single supplier address by GUID."""
    return _arena_get(f"/suppliers/{supplier_guid}/addresses/{address_guid}")


@mcp.tool()
def get_supplier_phone_numbers(guid: str) -> dict[str, Any]:
    """List all phone numbers on file for a supplier."""
    return _arena_get(f"/suppliers/{guid}/phonenumbers")


@mcp.tool()
def get_supplier_phone_number(supplier_guid: str, phone_guid: str) -> dict[str, Any]:
    """Get a single supplier phone number by GUID."""
    return _arena_get(f"/suppliers/{supplier_guid}/phonenumbers/{phone_guid}")


@mcp.tool()
def get_supplier_files(guid: str) -> dict[str, Any]:
    """List files attached to a supplier.

    Files attached at the supplier level are typically certificates of
    insurance, ISO certifications, audit reports, master agreements,
    quality manuals. NOT the same as files attached to specific supplier
    items (datasheets / CoCs) — use get_supplier_item_files for those.
    """
    return _arena_get(f"/suppliers/{guid}/files")


@mcp.tool()
def get_supplier_file(supplier_guid: str, file_assoc_guid: str) -> dict[str, Any]:
    """Get a single supplier ↔ file association by GUID."""
    return _arena_get(f"/suppliers/{supplier_guid}/files/{file_assoc_guid}")


@mcp.tool()
def get_supplier_quality_processes(guid: str) -> dict[str, Any]:
    """List quality processes that reference this supplier.

    Examples: SCAR (Supplier Corrective Action Request), supplier audits,
    re-qualification CAPAs. Each entry has the QP's guid, number, name.
    """
    return _arena_get(f"/suppliers/{guid}/quality")


@mcp.tool()
def get_supplier_quality_process(supplier_guid: str, qp_ref_guid: str) -> dict[str, Any]:
    """Get a single supplier ↔ quality-process reference by GUID."""
    return _arena_get(f"/suppliers/{supplier_guid}/quality/{qp_ref_guid}")


# -----------------------------------------------------------------------------
# Supplier Items
# -----------------------------------------------------------------------------

@mcp.tool()
def search_supplier_items(
    query: Optional[str] = None,
    name: Optional[str] = None,
    number: Optional[str] = None,
    supplier_name: Optional[str] = None,
    supplier_guid: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """Search Arena supplier items (vendor-side catalog SKUs).

    A supplier item is a specific listing — e.g. "Digi-Key part number
    296-1382-1-ND, an SN74HC04N" — distinct from your internal item.
    Multiple supplier items can source the same Arena item (multi-sourcing).

    Per Arena's GET /supplieritems spec, searchable filters: any, name,
    number, supplier.name, supplier.guid (plus custom attributes by GUID).

    Pagination:
      - Default limit 100, max single-page 400.
      - Set fetch_all=True to paginate through all supplier items.

    Args:
        query: Free-text search (Arena's 'any', UI-bar equivalent).
        name: Supplier item name (auto-wildcarded).
        number: Supplier item number / part number (auto-wildcarded).
        supplier_name: Supplier name (auto-wildcarded), filters items
            offered by suppliers whose name matches.
        supplier_guid: Filter by exact supplier GUID.
        limit: Single-page size (1-400). Ignored if fetch_all=True.
        offset: Pagination offset. Ignored if fetch_all=True.
        fetch_all: True to paginate through all results automatically.
    """
    base_params: dict[str, Any] = {}
    if query: base_params["any"] = query
    if name: base_params["name"] = _wildcard(name)
    if number: base_params["number"] = _wildcard(number)
    if supplier_name: base_params["supplier.name"] = _wildcard(supplier_name)
    if supplier_guid: base_params["supplier.guid"] = supplier_guid

    if fetch_all:
        return _paginate_get("/supplieritems", base_params)
    base_params["limit"] = min(max(limit, 1), 400)
    base_params["offset"] = max(offset, 0)
    return _arena_get("/supplieritems", params=base_params)


@mcp.tool()
def get_supplier_item(guid: str) -> dict[str, Any]:
    """Get full profile of a single supplier item by GUID.

    Returns name, number, supplier (guid + name), description, lifecycle
    phase if applicable, and all custom attributes (the "specs" you'd see
    in the UI's Specs tab — Arena exposes them on the main object rather
    than a separate /specs endpoint).
    """
    return _arena_get(f"/supplieritems/{guid}")


@mcp.tool()
def get_supplier_item_thumbnail(
    guid: str,
    max_size_bytes: int = 5 * 1024 * 1024,
) -> dict[str, Any]:
    """Download a supplier item's thumbnail image as base64-encoded bytes.

    Same pattern as get_item_thumbnail / get_file_content — base64-encoded
    in a JSON envelope. Returns an error if the supplier item has no
    thumbnail.

    Args:
        guid: Supplier item GUID.
        max_size_bytes: Reject downloads larger than this. Default 5 MB.
    """
    return _request_bytes(
        f"/supplieritems/{guid}/image/content",
        max_size_bytes=max_size_bytes,
    )


@mcp.tool()
def get_supplier_item_compliance(guid: str) -> dict[str, Any]:
    """List compliance declarations for a supplier item.

    Returns the supplier-item-level compliance records (RoHS, REACH,
    California Prop 65, etc.) with declared status and supporting
    documentation. Each entry has the requirement guid, name, declared
    status, and supporting file references.
    """
    return _arena_get(f"/supplieritems/{guid}/compliance")


@mcp.tool()
def get_supplier_item_compliance_record(
    supplier_item_guid: str,
    compliance_guid: str,
) -> dict[str, Any]:
    """Get a single supplier-item compliance record by GUID."""
    return _arena_get(
        f"/supplieritems/{supplier_item_guid}/compliance/{compliance_guid}"
    )


@mcp.tool()
def get_supplier_item_files(guid: str) -> dict[str, Any]:
    """List files attached to a supplier item.

    Typical attachments: manufacturer datasheets, certificates of
    conformity (CoCs), declarations of conformity, RoHS/REACH
    declarations, drawings.
    """
    return _arena_get(f"/supplieritems/{guid}/files")


@mcp.tool()
def get_supplier_item_file(
    supplier_item_guid: str,
    file_assoc_guid: str,
) -> dict[str, Any]:
    """Get a single supplier-item ↔ file association by GUID."""
    return _arena_get(
        f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}"
    )


@mcp.tool()
def get_supplier_item_file_content(
    supplier_item_guid: str,
    file_assoc_guid: str,
    max_size_bytes: int = 10 * 1024 * 1024,
) -> dict[str, Any]:
    """Download the content of a file attached to a supplier item.

    Returns base64-encoded bytes in a JSON envelope, same pattern as
    get_file_content. Watch the size cap for MCP transport (~750 KB
    safe).

    Args:
        supplier_item_guid: Supplier item GUID.
        file_assoc_guid: GUID of the file-association record (from
            get_supplier_item_files).
        max_size_bytes: Reject downloads larger than this. Default 10 MB.
    """
    return _request_bytes(
        f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}/content",
        max_size_bytes=max_size_bytes,
    )


@mcp.tool()
def get_supplier_item_quality_processes(guid: str) -> dict[str, Any]:
    """List quality processes that reference this supplier item.

    Typically SCARs, supplier-quality NCMRs, audits, or supplier
    requalification CAPAs.
    """
    return _arena_get(f"/supplieritems/{guid}/quality")


@mcp.tool()
def get_supplier_item_quality_process(
    supplier_item_guid: str,
    qp_ref_guid: str,
) -> dict[str, Any]:
    """Get a single supplier-item ↔ quality-process reference by GUID."""
    return _arena_get(
        f"/supplieritems/{supplier_item_guid}/quality/{qp_ref_guid}"
    )


@mcp.tool()
def get_supplier_item_sourcing(guid: str) -> dict[str, Any]:
    """List source relationships from a supplier item to Arena items.

    Reverse direction of get_item_sourcing — instead of "what supplier
    items source this Arena item?" this is "which Arena items does this
    supplier item source?" Useful for impact analysis on a supplier item
    (e.g. when a vendor discontinues a part: which of our items will be
    affected?).

    Source-relationship GUIDs returned here are the SAME as those
    returned by get_item_sourcing for the matching items — they're two
    sides of the same edge.
    """
    return _arena_get(f"/supplieritems/{guid}/sourcing")


@mcp.tool()
def get_supplier_item_source(
    supplier_item_guid: str,
    source_guid: str,
) -> dict[str, Any]:
    """Get a single supplier-item ↔ item source relationship by GUID."""
    return _arena_get(
        f"/supplieritems/{supplier_item_guid}/sourcing/{source_guid}"
    )


# -----------------------------------------------------------------------------
# Supplier-domain workspace settings
# -----------------------------------------------------------------------------

@mcp.tool()
def list_supplier_attributes() -> dict[str, Any]:
    """List the supplier object's custom attributes in the workspace.

    Returns the attribute schema for suppliers — names, GUIDs, field
    types, dropdown options. Use the attribute GUIDs to pass custom
    filters to search_suppliers.
    """
    return _arena_get("/settings/suppliers/attributes")


@mcp.tool()
def list_supplier_item_attributes() -> dict[str, Any]:
    """List the supplier-item object's custom attributes in the workspace.

    Returns the attribute schema for supplier items.
    """
    return _arena_get("/settings/supplieritems/attributes")


@mcp.tool()
def list_supplier_approval_statuses() -> dict[str, Any]:
    """List the supplier approval statuses configured in the workspace.

    Typical values: Unrated, Approved, Conditionally Approved, Disapproved,
    Discontinued. Each entry has guid and name. Used as the approvalStatus
    field on suppliers.
    """
    return _arena_get("/settings/suppliers/approvalstatuses")


@mcp.tool()
def list_supplier_item_compliance_requirements() -> dict[str, Any]:
    """List the compliance requirements available for supplier items.

    Workspace-level list of regulatory regimes (RoHS, REACH, California
    Prop 65, conflict minerals, etc.). Each requirement gets associated
    with individual supplier items via get_supplier_item_compliance.
    """
    return _arena_get("/settings/supplieritems/requirements")


# =============================================================================
# Wave 2.2g-h-i — Change Impl/History + Item completers + QP step decisions
#                 + Workspace settings round-out
# =============================================================================
# Three groups merged into one wave for deploy efficiency:
#   - Section B: Change implementation tasks/notes/files, change history,
#                item-side single-getters missed in earlier waves
#   - Section C: QP step decisions + step-level single-getters
#   - Section D: Workspace settings completion (skipping tickets and
#                user/access-control plumbing per scope direction)


# -----------------------------------------------------------------------------
# Section B — Change Implementation + History + item-side completers
# -----------------------------------------------------------------------------

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


# Item-side single-getter completers — fill in the missing single-record
# endpoints for sub-collections where we already have list-getters.

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
def get_item_file(item_guid: str, file_assoc_guid: str) -> dict[str, Any]:
    """Get a single item ↔ file association by GUID.

    Use after get_item_files to drill into one file association's
    full attributes (primary flag, category, association timestamp).
    """
    return _arena_get(f"/items/{item_guid}/files/{file_assoc_guid}")


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
def get_item_training_plan(
    item_guid: str,
    tp_ref_guid: str,
) -> dict[str, Any]:
    """Get a single item ↔ training plan reference by GUID."""
    return _arena_get(f"/items/{item_guid}/trainingplans/{tp_ref_guid}")


@mcp.tool()
def get_item_training_record(
    item_guid: str,
    record_guid: str,
) -> dict[str, Any]:
    """Get a single training record associated with an item.

    Training records on items show which users completed training on
    which specific revision of the item.
    """
    return _arena_get(f"/items/{item_guid}/trainingrecords/{record_guid}")


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


# -----------------------------------------------------------------------------
# Section C — QP Step Decisions + step-level single-getters
# -----------------------------------------------------------------------------

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


# NOTE: get_quality_process_step_file removed in Wave 2.2j-1 patch.
# The endpoint /qualityprocesses/<GUID>/steps/<GUID>/files/<GUID> does not exist
# in the Arena spec. Files on a QP step are affected objects with type=FILE; use
# get_quality_process_step_files (aggregator) to list them, then
# get_quality_process_step_affected_record(qp_guid, step_guid, affected_guid)
# for single-file detail. The affected_guid is the entry's guid from the list.


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


# -----------------------------------------------------------------------------
# Section D — Workspace settings round-out
# -----------------------------------------------------------------------------

# ---- Items domain settings ----

@mcp.tool()
def list_item_attributes() -> dict[str, Any]:
    """List all item-level custom attribute definitions in the workspace.

    Returns the workspace-wide schema for item custom attributes —
    field names, GUIDs, field types, dropdown options. Use these
    attribute GUIDs as search filters in search_items.
    """
    return _arena_get("/settings/items/attributes")


@mcp.tool()
def get_item_attribute(attribute_guid: str) -> dict[str, Any]:
    """Get a single item attribute definition by GUID."""
    return _arena_get(f"/settings/items/attributes/{attribute_guid}")


@mcp.tool()
def list_item_attribute_groups() -> dict[str, Any]:
    """List item attribute groups (visual groupings of attributes in the UI).

    Attribute groups organize the Item edit form into named sections
    (e.g. "Electrical", "Mechanical", "Compliance"). Each group
    contains an ordered list of attribute GUIDs.
    """
    return _arena_get("/settings/items/attributegroups")


@mcp.tool()
def list_item_bom_attributes() -> dict[str, Any]:
    """List BOM-line custom attribute definitions.

    These are attributes attached to BOM lines (the parent-child
    relationship), distinct from item attributes attached to the
    items themselves. Examples: "Optional", "Ref Des", "DNI".
    """
    return _arena_get("/settings/items/bom/attributes")


@mcp.tool()
def list_item_category_attributes(category_guid: str) -> dict[str, Any]:
    """List custom attributes for a specific item category.

    Item categories (Standard Operating Procedure, Drawing, Assembly,
    PCBA, etc.) can have their own category-specific attribute schemas
    on top of the workspace-wide attribute list.

    Args:
        category_guid: Item category GUID (from list_item_categories).
    """
    return _arena_get(f"/settings/items/categories/{category_guid}/attributes")


@mcp.tool()
def get_item_category(category_guid: str) -> dict[str, Any]:
    """Get full details of a single item category."""
    return _arena_get(f"/settings/items/categories/{category_guid}")


@mcp.tool()
def list_item_number_reservations() -> dict[str, Any]:
    """List reserved item number ranges in the workspace.

    Some workspaces reserve number ranges for specific product lines
    or specific users (e.g. "100-00000 through 199-99999 reserved for
    R&D, auto-assigned"). Returns the reservation records.
    """
    return _arena_get("/settings/items/numberreservations")


@mcp.tool()
def get_item_number_format(format_guid: str) -> dict[str, Any]:
    """Get a single item number format by GUID.

    Returns format pattern, prefix, sequence counter, and which item
    categories use this format.
    """
    return _arena_get(f"/settings/items/numberformats/{format_guid}")


@mcp.tool()
def list_item_requirements() -> dict[str, Any]:
    """List compliance requirements available for items at the workspace level.

    Workspace-level list of regulatory regimes (RoHS, REACH, Prop 65,
    etc.). Each item can declare compliance status against any of these
    via get_item_compliance.
    """
    return _arena_get("/settings/items/requirements")


@mcp.tool()
def get_item_requirement(requirement_guid: str) -> dict[str, Any]:
    """Get a single item compliance requirement definition by GUID."""
    return _arena_get(f"/settings/items/requirements/{requirement_guid}")


# ---- Changes domain settings ----

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


# ---- Files domain settings ----

@mcp.tool()
def list_file_attributes() -> dict[str, Any]:
    """List workspace-wide custom attribute definitions for files."""
    return _arena_get("/settings/files/attributes")


# ---- Quality Processes domain settings ----

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


# ---- Workspace-level settings ----

@mcp.tool()
def get_arena_settings() -> dict[str, Any]:
    """Get top-level workspace settings.

    Returns workspace-level configuration: company info, license
    details, enabled features, default time zone, etc.
    """
    return _arena_get("/settings/arena")


@mcp.tool()
def list_export_attributes() -> dict[str, Any]:
    """List custom attributes available on export definitions.

    Even though we've scoped out the Exports / Extracts read tooling,
    knowing which attributes exist on export definitions is useful
    for understanding workspace configuration.
    """
    return _arena_get("/settings/export/attributes")


# =============================================================================
# Wave 2.2j-1 — Audit-pack macros (composed workflows over read primitives)
# =============================================================================
# These tools compose the 147 read primitives into one-shot audit workflows
# that match how QMS / FDA / MDR auditors actually consume the data.
#
# Design principles:
#   - One macro = one bounded story (a change, a CAPA, a supplier-impact)
#   - Return structured sections, not raw nested payloads
#   - Summarize where possible to stay under MCP transport limits (~1 MB)
#   - Fail soft: one missing sub-fetch doesn't kill the whole pack;
#     errors are collected in an `errors` section at the response root
#   - All inputs are user-facing identifiers (numbers, names) — the macros
#     resolve to GUIDs internally
#   - Set `verbose=True` to include full per-item details; default is summary


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


# =============================================================================
# Wave 2.2k — Imports (read-only)
# =============================================================================
# Surfaces bulk import job definitions and run history. Adding POST endpoints
# to trigger new import runs would go here if/when needed.


@mcp.tool()
def search_import_definitions(
    query: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Search Arena import definitions.

    Returns a list of import-job templates (e.g., bulk-item-import,
    bulk-BOM-import).
    """
    params: dict[str, Any] = {"limit": min(max(limit, 1), 400), "offset": max(offset, 0)}
    if query:
        params["any"] = query
    if name:
        params["name"] = name if "*" in name else f"{name}*"
    return _arena_get("/imports", params=params)


@mcp.tool()
def get_import_definition(guid: str) -> dict[str, Any]:
    """Get a single import definition by GUID."""
    return _arena_get(f"/imports/{guid}")


@mcp.tool()
def get_import_runs(guid: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """List runs (executions) of an import definition."""
    return _arena_get(
        f"/imports/{guid}/runs",
        params={"limit": min(max(limit, 1), 400), "offset": max(offset, 0)},
    )


@mcp.tool()
def get_import_run(import_guid: str, run_guid: str) -> dict[str, Any]:
    """Get a single import run by GUID (status, dates, file refs)."""
    return _arena_get(f"/imports/{import_guid}/runs/{run_guid}")


@mcp.tool()
def get_import_run_result_content(import_guid: str, run_guid: str) -> dict[str, Any]:
    """Download the result-content file of an import run (typically a CSV
    summarizing what was imported). Returned as base64-encoded bytes."""
    return _request_bytes(
        f"/imports/{import_guid}/runs/{run_guid}/resultContent"
    )


@mcp.tool()
def get_import_run_error_content(import_guid: str, run_guid: str) -> dict[str, Any]:
    """Download the error-content file of an import run (errors encountered
    during the run). Returned as base64-encoded bytes."""
    return _request_bytes(
        f"/imports/{import_guid}/runs/{run_guid}/errorContent"
    )


# =============================================================================
# Wave 2.2l — Integrations, Outbound Events, Triggers, Recent Activity, API Usage
# =============================================================================


@mcp.tool()
def search_integrations(
    query: Optional[str] = None,
    name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Search outbound integrations configured in the workspace.

    Spec endpoint: GET /outboundintegrations
    """
    params: dict[str, Any] = {"limit": min(max(limit, 1), 400), "offset": max(offset, 0)}
    if query:
        params["any"] = query
    if name:
        params["name"] = name if "*" in name else f"{name}*"
    return _arena_get("/outboundintegrations", params=params)


@mcp.tool()
def get_integration(guid: str) -> dict[str, Any]:
    """Get a single outbound integration by GUID."""
    return _arena_get(f"/outboundintegrations/{guid}")


@mcp.tool()
def get_integration_administrators(guid: str) -> dict[str, Any]:
    """List administrators (users) who can manage an integration."""
    return _arena_get(f"/outboundintegrations/{guid}/administrators")


@mcp.tool()
def list_triggers() -> dict[str, Any]:
    """List ALL triggers in the workspace.

    Triggers fire integration events when specified conditions are met.
    Spec endpoint: GET /settings/integrations/triggers
    """
    return _arena_get("/settings/integrations/triggers")


@mcp.tool()
def get_trigger(guid: str) -> dict[str, Any]:
    """Get a single trigger by GUID."""
    return _arena_get(f"/settings/integrations/triggers/{guid}")


@mcp.tool()
def search_outbound_event_integrations(
    query: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Search outbound-event integrations.

    Distinct from generic integrations — these are integrations that fire
    events outbound (webhooks-style) on workspace activity.
    Spec endpoint: GET /outboundevents
    """
    params: dict[str, Any] = {"limit": min(max(limit, 1), 400), "offset": max(offset, 0)}
    if query:
        params["any"] = query
    return _arena_get("/outboundevents", params=params)


@mcp.tool()
def get_outbound_event_integration(guid: str) -> dict[str, Any]:
    """Get a single outbound-event integration by GUID."""
    return _arena_get(f"/outboundevents/{guid}")


@mcp.tool()
def get_outbound_event_integration_triggers(guid: str) -> dict[str, Any]:
    """List triggers attached to an outbound-event integration."""
    return _arena_get(f"/outboundevents/{guid}/triggers")


@mcp.tool()
def get_outbound_event_integration_trigger(
    integration_guid: str, trigger_guid: str
) -> dict[str, Any]:
    """Get a single trigger attached to an outbound-event integration."""
    return _arena_get(
        f"/outboundevents/{integration_guid}/triggers/{trigger_guid}"
    )


@mcp.tool()
def get_outbound_event_integration_administrators(guid: str) -> dict[str, Any]:
    """List administrators of an outbound-event integration."""
    return _arena_get(f"/outboundevents/{guid}/administrators")


@mcp.tool()
def get_recent_activity_user_access() -> dict[str, Any]:
    """List recent user-access activity in the workspace (logins, etc.).

    Spec endpoint: GET /settings/recentactivities/useraccesses
    """
    return _arena_get("/settings/recentactivities/useraccesses")


@mcp.tool()
def get_recent_activity_exports() -> dict[str, Any]:
    """List recent export-run activity in the workspace.

    Spec endpoint: GET /settings/recentactivities/exports
    """
    return _arena_get("/settings/recentactivities/exports")


@mcp.tool()
def get_recent_activity_report_runs() -> dict[str, Any]:
    """List recent report-run activity in the workspace.

    Spec endpoint: GET /settings/recentactivities/reportruns
    """
    return _arena_get("/settings/recentactivities/reportruns")


@mcp.tool()
def get_recent_activity_file_access() -> dict[str, Any]:
    """List recent file-access activity (file downloads, content fetches).

    Spec endpoint: GET /settings/recentactivities/fileaccesses
    """
    return _arena_get("/settings/recentactivities/fileaccesses")


@mcp.tool()
def get_api_usage() -> dict[str, Any]:
    """Return every API call recorded in the workspace.

    Useful for monitoring this MCP server's own footprint against the
    workspace's API quota.
    Spec endpoint: GET /settings/recentactivities/apiusages
    """
    return _arena_get("/settings/recentactivities/apiusages")


# =============================================================================
# Wave 2.2m — BOM substitutes + file watermarks (read-only)
# =============================================================================


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


# =============================================================================
# Wave 3.2 — Full write parity with Arena UI
# =============================================================================
# Every write endpoint documented in the spec exposed as a thin tool. Each
# accepts optional dry_run and (where mutation is involved) snapshot_first.
# Body shapes were spec-verified where samples were available; endpoints
# without clear sample bodies were coded following Arena's documented
# patterns (nested {guid} references, additionalAttributes lists, etc.).
# If any tool returns a 400 with an unexpected error code, the response
# body carries Arena's own explanation.
#
# Scope note: multipart file-content uploads (POST /files/<G>/content,
# POST /files/<G>/editions with content, POST /items/<G>/files/<G>/content,
# POST /supplieritems/<G>/files/<G>/content) accept a local_path argument
# and stream the file to Arena as multipart/form-data.
#
# Explicitly not in this wave: admin surface (machine users, employees,
# user groups, access policies) and outbound event reconcile endpoints.
# Add on demand.


# ---- Helper: multipart file upload -------------------------------------


def _arena_post_multipart(
    path: str, local_path: str, extra_fields: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """POST to Arena with multipart/form-data — for file content uploads.

    Reads the file at local_path (must be readable from the process running
    this MCP) and uploads it as `filecontent` field, along with any extra
    form fields. Arena returns no JSON body on multipart uploads — a 201
    status is success, 400 is failure.
    """
    import os
    if not os.path.isfile(local_path):
        return {"error": True, "message": f"File not found: {local_path}"}
    for attempt in (1, 2):
        token = _get_access_token(force_refresh=(attempt == 2))
        headers = {
            "Authorization": f"Bearer {token}",
            "Arena-Usage-Reason": ARENA_USAGE_REASON,
        }
        url = f"{ARENA_API_BASE}/{path.lstrip('/')}"
        try:
            with open(local_path, "rb") as fh:
                files = {"filecontent": (os.path.basename(local_path), fh)}
                data = extra_fields or {}
                resp = httpx.post(
                    url, headers=headers, files=files, data=data, timeout=300.0,
                )
        except httpx.HTTPError as exc:
            return {"error": True, "exception": str(exc), "url": url}
        if resp.status_code == 401 and attempt == 1:
            continue
        if resp.status_code in (200, 201, 204):
            return {"ok": True, "status_code": resp.status_code,
                    "body": _safe_json(resp) if resp.content else None}
        return {"error": True, "status_code": resp.status_code,
                "url": url, "body": _safe_json(resp)}
    return {"error": True, "message": "exhausted retries"}


# ---- Items --------------------------------------------------------------


@mcp.tool()
def create_item(
    name: str,
    category_guid: str,
    number_format_guid: Optional[str] = None,
    number_format_fields: Optional[list[dict[str, Any]]] = None,
    description: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new Arena item.

    POST /items. category_guid drives numbering + attributes; if the category
    has a single default number sequence, number_format_guid/fields can be
    omitted. Otherwise (e.g. a shared multi-prefix format like "Document",
    which covers FO/WI/FTP/PL/RE/etc. off one picklist) you must pass:
      number_format_guid: the numberFormat's own guid (see
        list_item_number_formats / get_item_number_format).
      number_format_fields: [{"guid": <picklist field guid>, "value": "FO"}]
        for each field the format requires (e.g. the prefix code field).
    Per Arena's REST API docs, this nests as body.numberFormat =
    {"guid": ..., "fields": [...]}. Note: "numberSequencePrefix" is NOT a
    valid field on /items (that belongs to /changes and
    /settings/items/numberreservations, not this endpoint).
    """
    body: dict[str, Any] = {"name": name, "category": {"guid": category_guid}}
    if number_format_guid:
        body["numberFormat"] = {
            "guid": number_format_guid,
            "fields": number_format_fields or [],
        }
    if description is not None:
        body["description"] = description
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/items", "body": body}
    return _arena_post("/items", body=body)


@mcp.tool()
def update_item(
    guid: str,
    description: Optional[str] = None,
    owner_full_name: Optional[str] = None,
    owner_guid: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False,
    snapshot_first: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update an item's scalar fields + additionalAttributes.

    PUT /items/<GUID>. Rev-controlled fields (BOM, files, etc.) update
    through their own endpoints. setnull=True appends ?setnull=true.
    """
    body: dict[str, Any] = {}
    if description is not None:
        body["description"] = description
    if owner_full_name is not None:
        body["owner"] = {"fullName": owner_full_name}
    elif owner_guid is not None:
        body["owner"] = {"guid": owner_guid}
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if not body:
        return {"error": True, "message": "No fields provided to update."}
    path = f"/items/{guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    snap: dict[str, Any] = {}
    if snapshot_first:
        cur = _arena_get(f"/items/{guid}")
        if isinstance(cur, dict) and not cur.get("error"):
            snap = _write_snapshot(
                label=f"pre-update item {cur.get('number', guid)}",
                kind="item_update",
                captures=[{"endpoint": f"/items/{guid}", "data": cur}],
            )
    r = _arena_put(path, body=body)
    return {"snapshot": snap, "result": r} if snap else r


@mcp.tool()
def delete_item(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /items/<GUID>. Arena refuses if the item is referenced anywhere."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{guid}"}
    return _arena_delete(f"/items/{guid}")


@mcp.tool()
def create_item_thumbnail_from_files_view(
    guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """Set item thumbnail from a file already in the item's Files view.

    POST /items/<GUID>/image with body {file: {guid}}.
    """
    body = {"file": {"guid": file_assoc_guid}}
    if dry_run:
        return {"dry_run": True, "would_post_to": f"/items/{guid}/image", "body": body}
    return _arena_post(f"/items/{guid}/image", body=body)


@mcp.tool()
def delete_item_thumbnail(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /items/<GUID>/image — remove the item's thumbnail."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/items/{guid}/image"}
    return _arena_delete(f"/items/{guid}/image")


@mcp.tool()
def change_item_lifecycle_phase(
    item_guid: str,
    to_lifecycle_phase_guid: str,
    revision_number: Optional[str] = None,
    proceed_on_notice: bool = True,
    notes: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Move an item to a different lifecycle phase without a change order.

    POST /items/lifecyclephasechanges. Requires appropriate permissions;
    normal-flow phase changes should go through an ECO instead.
    """
    body: dict[str, Any] = {
        "item": {"guid": item_guid},
        "toLifecyclePhase": {"guid": to_lifecycle_phase_guid},
        "proceedOnNotice": proceed_on_notice,
    }
    if revision_number:
        body["revisionNumber"] = revision_number
    if notes:
        body["notes"] = notes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/items/lifecyclephasechanges", "body": body}
    return _arena_post("/items/lifecyclephasechanges", body=body)


@mcp.tool()
def reserve_item_number(
    number_sequence_prefix: str, quantity: int = 1, dry_run: bool = False
) -> dict[str, Any]:
    """Reserve N item numbers on a sequence prefix (e.g. "830-").

    POST /settings/items/numberreservations.
    """
    body = {
        "numberSequencePrefix": {"value": number_sequence_prefix},
        "quantity": quantity,
    }
    if dry_run:
        return {"dry_run": True, "would_post_to": "/settings/items/numberreservations", "body": body}
    return _arena_post("/settings/items/numberreservations", body=body)


@mcp.tool()
def cancel_item_number_reservation(
    reservation_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /settings/items/numberreservations/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/settings/items/numberreservations/{reservation_guid}"}
    return _arena_delete(f"/settings/items/numberreservations/{reservation_guid}")


# ---- BOM ----------------------------------------------------------------


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


# ---- Item Files ---------------------------------------------------------


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


# ---- Files (top-level) --------------------------------------------------


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
            fields["categoryGuid"] = category_guid
        if description is not None:
            fields["description"] = description
        if edition is not None:
            fields["edition"] = edition
        if format is not None:
            fields["format"] = format
        if author_full_name is not None:
            fields["authorFullName"] = author_full_name
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
    """
    fields: dict[str, Any] = {
        "edition": edition,
        "storageMethodName": storage_method,
    }
    if location is not None:
        fields["location"] = location
    if author_full_name is not None:
        fields["author.fullName"] = author_full_name
    if description is not None:
        fields["description"] = description

    if storage_method == "FILE":
        if not local_path:
            return {"error": True, "message": "local_path required for FILE storage."}
        if dry_run:
            return {"dry_run": True, "would_multipart_upload_to": f"/files/{file_guid}/editions",
                    "local_path": local_path, "fields": fields}
        return _arena_post_multipart(
            f"/files/{file_guid}/editions", local_path, extra_fields=fields
        )
    else:
        # WEB / FTP — JSON body
        body = {"file": fields}
        if dry_run:
            return {"dry_run": True, "would_post_to": f"/files/{file_guid}/editions",
                    "body": body}
        return _arena_post(f"/files/{file_guid}/editions", body=body)


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


# ---- Item Compliance / Sourcing / References ---------------------------


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
        body["notes"] = notes
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
        body["notes"] = notes
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


# ---- Changes: status transitions + missing writes ----------------------


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


# ---- Quality process extras --------------------------------------------


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


# ---- Training Plans -----------------------------------------------------


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


# ---- Suppliers ----------------------------------------------------------


@mcp.tool()
def create_supplier(
    name: str, supplier_id: Optional[str] = None,
    description: Optional[str] = None, website: Optional[str] = None,
    approval_status: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /suppliers."""
    body: dict[str, Any] = {"name": name}
    if supplier_id is not None:
        body["supplierId"] = supplier_id
    if description is not None:
        body["description"] = description
    if website is not None:
        body["website"] = website
    if approval_status is not None:
        body["approvalStatus"] = approval_status
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/suppliers", "body": body}
    return _arena_post("/suppliers", body=body)


@mcp.tool()
def update_supplier(
    guid: str, name: Optional[str] = None, supplier_id: Optional[str] = None,
    description: Optional[str] = None, website: Optional[str] = None,
    approval_status: Optional[str] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False, snapshot_first: bool = True, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /suppliers/<GUID>."""
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if supplier_id is not None:
        body["supplierId"] = supplier_id
    if description is not None:
        body["description"] = description
    if website is not None:
        body["website"] = website
    if approval_status is not None:
        body["approvalStatus"] = approval_status
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/suppliers/{guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    snap: dict[str, Any] = {}
    if snapshot_first:
        cur = _arena_get(f"/suppliers/{guid}")
        if isinstance(cur, dict) and not cur.get("error"):
            snap = _write_snapshot(
                label=f"pre-update supplier {cur.get('name', guid)}",
                kind="supplier_update",
                captures=[{"endpoint": f"/suppliers/{guid}", "data": cur}],
            )
    r = _arena_put(path, body=body)
    return {"snapshot": snap, "result": r} if snap else r


@mcp.tool()
def delete_supplier(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /suppliers/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/suppliers/{guid}"}
    return _arena_delete(f"/suppliers/{guid}")


@mcp.tool()
def add_supplier_address(
    supplier_guid: str, address_body: dict[str, Any], primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /suppliers/<GUID>/addresses.

    address_body is the "address" sub-object per spec: {label, address1,
    address2, city, state, "Country/Region", province, postalCode}.
    """
    body = {"address": address_body, "primary": primary}
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/suppliers/{supplier_guid}/addresses", "body": body}
    return _arena_post(f"/suppliers/{supplier_guid}/addresses", body=body)


@mcp.tool()
def update_supplier_address(
    supplier_guid: str, address_guid: str, address_body: dict[str, Any],
    primary: Optional[bool] = None, setnull: bool = False, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /suppliers/<GUID>/addresses/<GUID>."""
    body: dict[str, Any] = {"address": address_body}
    if primary is not None:
        body["primary"] = primary
    path = f"/suppliers/{supplier_guid}/addresses/{address_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)


@mcp.tool()
def delete_supplier_address(
    supplier_guid: str, address_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /suppliers/<GUID>/addresses/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/suppliers/{supplier_guid}/addresses/{address_guid}"}
    return _arena_delete(f"/suppliers/{supplier_guid}/addresses/{address_guid}")


@mcp.tool()
def add_supplier_phone(
    supplier_guid: str, phone_body: dict[str, Any], primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /suppliers/<GUID>/phonenumbers."""
    body = {"phoneNumber": phone_body, "primary": primary}
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/suppliers/{supplier_guid}/phonenumbers", "body": body}
    return _arena_post(f"/suppliers/{supplier_guid}/phonenumbers", body=body)


@mcp.tool()
def update_supplier_phone(
    supplier_guid: str, phone_guid: str, phone_body: dict[str, Any],
    primary: Optional[bool] = None, setnull: bool = False, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /suppliers/<GUID>/phonenumbers/<GUID>."""
    body: dict[str, Any] = {"phoneNumber": phone_body}
    if primary is not None:
        body["primary"] = primary
    path = f"/suppliers/{supplier_guid}/phonenumbers/{phone_guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)


@mcp.tool()
def delete_supplier_phone(
    supplier_guid: str, phone_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /suppliers/<GUID>/phonenumbers/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/suppliers/{supplier_guid}/phonenumbers/{phone_guid}"}
    return _arena_delete(f"/suppliers/{supplier_guid}/phonenumbers/{phone_guid}")


@mcp.tool()
def add_file_to_supplier(
    supplier_guid: str, file_guid: str,
    latest_edition_association: bool = True, primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /suppliers/<GUID>/files."""
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/suppliers/{supplier_guid}/files", "body": body}
    return _arena_post(f"/suppliers/{supplier_guid}/files", body=body)


@mcp.tool()
def remove_file_from_supplier(
    supplier_guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /suppliers/<GUID>/files/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/suppliers/{supplier_guid}/files/{file_assoc_guid}"}
    return _arena_delete(f"/suppliers/{supplier_guid}/files/{file_assoc_guid}")


# ---- Supplier Items -----------------------------------------------------


@mcp.tool()
def create_supplier_item(
    name: str, number: str, supplier_guid: str,
    description: Optional[str] = None, off_the_shelf: Optional[bool] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /supplieritems."""
    body: dict[str, Any] = {
        "name": name, "number": number, "supplier": {"guid": supplier_guid},
    }
    if description is not None:
        body["description"] = description
    if off_the_shelf is not None:
        body["offTheShelf"] = off_the_shelf
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if dry_run:
        return {"dry_run": True, "would_post_to": "/supplieritems", "body": body}
    return _arena_post("/supplieritems", body=body)


@mcp.tool()
def update_supplier_item(
    guid: str, name: Optional[str] = None, number: Optional[str] = None,
    description: Optional[str] = None, off_the_shelf: Optional[bool] = None,
    additional_attributes: Optional[list[dict[str, Any]]] = None,
    setnull: bool = False, snapshot_first: bool = True, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /supplieritems/<GUID>."""
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if number is not None:
        body["number"] = number
    if description is not None:
        body["description"] = description
    if off_the_shelf is not None:
        body["offTheShelf"] = off_the_shelf
    if additional_attributes:
        body["additionalAttributes"] = additional_attributes
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/supplieritems/{guid}"
    if setnull:
        path += "?setnull=true"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    snap: dict[str, Any] = {}
    if snapshot_first:
        cur = _arena_get(f"/supplieritems/{guid}")
        if isinstance(cur, dict) and not cur.get("error"):
            snap = _write_snapshot(
                label=f"pre-update supplier item {cur.get('number', guid)}",
                kind="supplier_item_update",
                captures=[{"endpoint": f"/supplieritems/{guid}", "data": cur}],
            )
    r = _arena_put(path, body=body)
    return {"snapshot": snap, "result": r} if snap else r


@mcp.tool()
def delete_supplier_item(guid: str, dry_run: bool = False) -> dict[str, Any]:
    """DELETE /supplieritems/<GUID>."""
    if dry_run:
        return {"dry_run": True, "would_delete": f"/supplieritems/{guid}"}
    return _arena_delete(f"/supplieritems/{guid}")


@mcp.tool()
def add_existing_file_to_supplier_item(
    supplier_item_guid: str, file_guid: str,
    latest_edition_association: bool = True, primary: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /supplieritems/<GUID>/files (add existing)."""
    body = {
        "file": {"guid": file_guid},
        "latestEditionAssociation": latest_edition_association,
        "primary": primary,
    }
    if dry_run:
        return {"dry_run": True,
                "would_post_to": f"/supplieritems/{supplier_item_guid}/files", "body": body}
    return _arena_post(f"/supplieritems/{supplier_item_guid}/files", body=body)


@mcp.tool()
def upload_supplier_item_file_content(
    supplier_item_guid: str, file_assoc_guid: str, local_path: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """POST /supplieritems/<GUID>/files/<GUID>/content — upload new content."""
    if dry_run:
        return {
            "dry_run": True,
            "would_upload": f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}/content",
            "local_path": local_path,
        }
    return _arena_post_multipart(
        f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}/content", local_path
    )


@mcp.tool()
def update_supplier_item_file_association(
    supplier_item_guid: str, file_assoc_guid: str,
    latest_edition_association: Optional[bool] = None,
    primary: Optional[bool] = None, dry_run: bool = False,
) -> dict[str, Any]:
    """PUT /supplieritems/<GUID>/files/<GUID>."""
    body: dict[str, Any] = {}
    if latest_edition_association is not None:
        body["latestEditionAssociation"] = latest_edition_association
    if primary is not None:
        body["primary"] = primary
    if not body:
        return {"error": True, "message": "Nothing to update."}
    path = f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}"
    if dry_run:
        return {"dry_run": True, "would_put_to": path, "body": body}
    return _arena_put(path, body=body)


@mcp.tool()
def remove_file_from_supplier_item(
    supplier_item_guid: str, file_assoc_guid: str, dry_run: bool = False
) -> dict[str, Any]:
    """DELETE /supplieritems/<GUID>/files/<GUID>."""
    if dry_run:
        return {"dry_run": True,
                "would_delete": f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}"}
    return _arena_delete(f"/supplieritems/{supplier_item_guid}/files/{file_assoc_guid}")


# =============================================================================
# Snapshot / restore safety net
# =============================================================================


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
    files = sorted(SNAPSHOT_DIR.glob("*.json"), reverse=True)[:limit]
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
    path = SNAPSHOT_DIR / f"{snapshot_id}.json"
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
    path = SNAPSHOT_DIR / f"{snapshot_id}.json"
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
