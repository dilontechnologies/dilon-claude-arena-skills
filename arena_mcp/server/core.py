from __future__ import annotations

import time
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

from . import config

mcp = FastMCP("arena-plm")

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}
_name_guid_cache: dict[tuple[str, str], Optional[str]] = {}


def reset_connection() -> None:
    """Force the next _get_access_token call to fetch a fresh token."""
    _token_cache["access_token"] = None
    _token_cache["expires_at"] = 0.0


def _get_access_token(force_refresh: bool = False) -> str:
    now = time.time()
    if (
        not force_refresh
        and _token_cache["access_token"]
        and _token_cache["expires_at"] - now > 60
    ):
        return _token_cache["access_token"]

    resp = httpx.post(
        config.ARENA_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": config.ARENA_CLIENT_ID,
            "client_secret": config.ARENA_CLIENT_SECRET,
            "workspace_id": config.ARENA_WORKSPACE_ID,
            "arena-usage-reason": config.ARENA_USAGE_REASON,
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
    url = f"{config.ARENA_API_BASE}/{path.lstrip('/')}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}

    for attempt in (1, 2):
        token = _get_access_token(force_refresh=(attempt == 2))
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Arena-Usage-Reason": config.ARENA_USAGE_REASON,
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

    url = f"{config.ARENA_API_BASE}/{path.lstrip('/')}"
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}

    for attempt in (1, 2):
        token = _get_access_token(force_refresh=(attempt == 2))
        headers = {
            "Authorization": f"Bearer {token}",
            "Arena-Usage-Reason": config.ARENA_USAGE_REASON,
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
            "Arena-Usage-Reason": config.ARENA_USAGE_REASON,
        }
        url = f"{config.ARENA_API_BASE}/{path.lstrip('/')}"
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
