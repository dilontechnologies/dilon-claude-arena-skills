# Arena Mock Spec

This directory documents Arena's wire-level behavior — per-endpoint
request/response/error/state-transition shape — as a foundation for a
future stateful Arena mock that can replace ad hoc per-test `respx` route
mocking. A stateful mock is useful for testing multi-call sequences a
skill actually performs end-to-end (e.g. `dilon-arena-eco-creator`
creating a change, adding items, attaching a file, and routing it) rather
than one call mocked in isolation, which is what `tests/test_*.py`
currently does via `respx`.

**Status:** structure only. No endpoint has been documented yet, and no
mock implementation exists yet — this is scaffolding for both, to be
filled in incrementally as tests are written for the tool calls each
skill actually uses (see "Coverage priority" below).

## Layout

One file per Arena domain, matching `arena_mcp/server/tools/`'s domain
grouping at the domain level (not its finer per-file split — e.g. one
`items.md` covers everything `items_core.py`/`items_bom.py`/
`items_files.py`/`items_compliance.py` implement):

- `users.md`, `items.md`, `changes.md`, `quality.md`, `training.md`,
  `suppliers.md`, `supplier_items.md`, `files.md`,
  `imports_integrations.md`, `activity.md`, `audit_packs.md`,
  `snapshots.md`, `environments.md`

Each file has a coverage table (at-a-glance progress) and a set of
per-endpoint entries using the template in "Entry template" below.

## Coverage priority

Documenting all ~290 tools before any of this is useful isn't the goal —
coverage is prioritized by what a shipped skill actually calls. Each
entry's "Used by skills" field tracks this. An endpoint no skill calls
yet stays `not started` indefinitely without blocking anything.

## Conventions every domain file relies on (documented once, here)

**OAuth flow:** client_credentials grant against `ARENA_TOKEN_URL`. The
access token is cached in-process (`server/core.py::_token_cache`) and
reused until it's within 60 seconds of `expires_in`. A `401` on any API
call triggers exactly one retry with `force_refresh=True` before giving
up — see `tests/test_change_writes.py::test_401_then_200_retries_once_and_succeeds`
for the existing test that exercises this path against a single endpoint;
a stateful mock needs to support returning `401` once, then `200`, per
route.

**Pagination shape:** list/search responses return `{"results": [...],
"totalResults": <int>}`; `limit`/`offset` query params control the page.

**Arena's raw HTTP error shape:** (distinct from this codebase's own tool
return shape below) — TODO once the first real error response is
captured from Arena and documented in a domain file.

**This codebase's tool return shape:** every tool function returns a
plain `dict`. On success, that's Arena's raw parsed JSON body (mostly
passed through unchanged). On a handled failure, it's `{"error": True,
"message": "..."}` — this is this codebase's own wrapper, not something
Arena itself returns.

**`dry_run`/`snapshot_first`:** most write tools accept `dry_run: bool =
False` — when `True`, the tool returns a preview without making any
network call at all. A mock never needs to model the `dry_run=True` path;
there's nothing to mock.

**GUID resolution:** several tools accept a human-readable name and
resolve it to a GUID via an internal search call before making their
"real" request (`server/core.py::_resolve_name_to_guid` and friends). A
domain entry for such a tool should note this under "Depends on / GUID
resolution" so a stateful mock knows to expect two calls, not one.

**Multipart upload:** file content upload is a two-step
`create_file`/`create_item` (JSON) → `upload_*_content` (multipart/
form-data) pattern, not a single call.

## Entry template

```markdown
### `<tool_function_name>`

- **Used by skills:** [none yet | dilon-arena-eco-creator | ...]
- **Arena endpoint:** `<METHOD> <path>`
- **Request:** path/query params; body shape (fields, types, required/optional)
- **Response (success):** status code; body shape + example
- **Response (error cases):** status code → condition → body shape
- **State effects:** what this call changes in Arena's model that a stateful mock must track (e.g. creates a Change record, transitions workflow status) — "none" for pure reads
- **Depends on / GUID resolution:** any prior lookup calls this tool makes internally
- **Mock status:** `not started` | `fixture-only` | `stateful-mock implemented`
- **Notes:** quirks, spec-verified callouts, Dilon-specific wrinkles
```

`audit_packs.md` uses a variant entry — its five tools are read-only
composites over other domains' endpoints, with no Arena calls of their
own. List which other domains' entries they compose instead of a
Request/Response shape:

```markdown
### `<audit_pack_tool_name>`

- **Used by skills:** [none yet | ...]
- **Composes:** `items.md#get_item`, `items.md#get_item_bom`, ... (list every tool it calls)
- **State effects:** none (read-only aggregation)
- **Mock status:** `not started` | `fixture-only` | `stateful-mock implemented`
- **Notes:**
```
