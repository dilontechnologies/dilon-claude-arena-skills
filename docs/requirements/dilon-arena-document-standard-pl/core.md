# `dilon-arena-document-standard-pl` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-document-standard-pl/SKILL.md`. Folds together what
was previously split across `dilon-arena-file-naming`,
`dilon-arena-file-revision`, and
`dilon-arena-file-revision-amendment-pl-re-item-numbering` (2026-09-01) —
see `../README.md` for why those retired in favor of one skill per
document type, and
`../dilon-arena-document-standard-fo/core.md` for the base naming/revision
scheme's original empirical verification record.

## Purpose

Answer, for a PL (Test Plan) controlled document: what goes in its file
`name`/`title`, what revision-number string Arena needs (or, once a
completed report exists, what new-item number instead), which file
category and Affected-Items picklist value it maps to, and how it's
compiled.

## Naming and base revision — RESOLVED (inherited, not independently tested)

Same convention and scheme as `dilon-arena-document-standard-fo` — see
that skill's `core.md` for the empirical verification record. Applies to
PL up until the reissue exception below fires.

## Expected file formats — RESOLVED (inherited, not independently tested)

Same default as `dilon-arena-document-standard-fo`: docx + pdf, pdf
primary — applies to a normal revision and to the new item created under
the reissue exception below alike. See that skill's `core.md` for the one
confirmed data point behind the default. No PL-specific testing done
separately.

## Reissue-instead-of-revision exception — RESOLVED mechanism, open questions remain

Confirmed with the user (2026-09-01):
- **Suffix counter is independent per root number.** `PL-00004`'s
  reissues (`-01`, `-02`, ...) and a linked report's reissues are separate
  counters — a report's suffix has nothing to do with which plan it's
  currently testing.
- **"Completed report exists" detection should use Item References**,
  created going forward (report -> plan), rather than inferred from
  naming/description text or asked fresh every single time.
- **New items get an explicit traceability link back to what they
  supersede**, via Item Reference, since Arena's own revision history
  won't show any relationship between e.g. `PL-00004` and `PL-00004-01` —
  they're different items now, not revisions of one item.
- **Fires inside `dilon-arena-eco-creator`'s flow** (step 8, attaching
  documents).

### Empirical investigation (2026-09-01, sandbox workspace 901596215)

All of the below used disposable test items, created and deleted in the
same session — no lasting changes to the sandbox.

**Number-format mechanism**: `list_item_number_formats` shows 7 formats in
this workspace, including `"Basic Item Number"` (guid
`O6Q9E1SZFN6FYHXYILPF`) — a single `FREE_TEXT` field, no auto-sequencing.
The Plan (`CUEX2PGN3BU4N6INXRKH`) and Report (`XFZINA18OWFP8R38IC6T`)
categories both normally use the shared "Document" format
(`P7RAF2T0GO7GZIYZJMQF`): `<prefix picklist>-<DELIMITER "-">-<5-digit
zero-padded AUTO_SEQUENCE>`.
- `create_item(category_guid=Plan, number_format_guid=Document,
  number_format_fields=[{prefix field: "PL"}, {Number/AUTO_SEQUENCE field:
  "00004-01"}])` — the manual override of the AUTO_SEQUENCE field was
  **silently ignored**; Arena returned its own real next value, not the
  requested string.
- `create_item(category_guid=Plan, number_format_guid=<Basic Item
  Number's guid>, number_format_fields=[{its one field's guid:
  "PL-00004-01"}])` — accepted, returned `"number": "PL-00004-01"`
  exactly. Category stayed `"Plan"` — item behaves as a completely normal
  Plan-category item, only its number-assignment mechanism at creation
  differs. No new Arena item category needs to exist or be created.
- Both Plan and Report categories require one custom attribute on
  creation in the **sandbox** workspace only (`"Next review Date?"`,
  `DATE` type) — confirmed **absent** on the real production Plan/Report
  categories. `create_item` for `PL-00004-01` succeeded in production with
  no `additional_attributes` needed. The fix is to always check
  `list_item_category_attributes` live per-workspace, not carry a fixed
  field list forward.

**Item Reference mechanism**: `get_item_references` on a real, released
item (`PL-00004`) returned zero results — no pre-existing Arena-native
link between any existing Plan and its Report(s) in this workspace; no
backfill for already-released pairs.
- Directionality test: created disposable test Plan and Report items,
  `create_item_reference(from=report, to=plan)`, then queried
  `get_item_references` on **both** items — both returned one result. The
  query is **bidirectional**, not filtered to outgoing-only.
- **Reference links are immediate/global, not ECO-scoped.** A created
  reference has no revision/change/effectivity field at all — visible in
  Arena the instant it's created, unconditionally. Canceling the ECO the
  referencing item was an affected item on does **not** remove the
  reference. Deleting the referencing item **does** cascade-delete the
  reference (contradicts `delete_item`'s own tool description about
  Arena refusing to delete a referenced item — that description is wrong
  at least for this relationship type).
- **Bug found and fixed**: `create_item_reference`'s (and
  `update_item_reference`'s) `notes` parameter always posted
  `body["notes"] = notes`; Arena's actual field (confirmed by the
  `"note": null` response shape) is `note`, singular. Fixed both tools in
  `arena_mcp/arena_mcp_server.py` to post `body["note"]`.

## Known gaps / not yet covered

- **"Completed report" definition**: working assumption is `RELEASED`
  lifecycle phase / `EFFECTIVE` revision status on the linked Report. Not
  yet confirmed with the user.
- **Suffix zero-padding width**: examples given were always 2 digits
  (`-01`, `-02`); unspecified what happens past `-99`.
- **End-to-end test — partially confirmed in production 2026-09-01.**
  `PL-00004-01` was created successfully in production via the documented
  mechanism and behaves as a normal Plan-category item;
  `create_item_reference` from the new item back to `PL-00004` also
  confirmed working in production the same way as sandbox. **Still not
  completed**: `add_items_to_change` to attach `PL-00004-01` onto an ECO
  as an affected item, and attaching its compiled docx/pdf to both the
  item and the change, following `dilon-arena-eco-creator`'s step 8 attach
  flow — ran out of session time before finishing.
- **Naming for the new item**: same descriptive name convention as the
  original item, not yet tested whether Dilon wants any indication in the
  item `name` itself that this is a reissue.
- No backfill plan for existing released PL/RE pairs that predate this
  rule, beyond "ask the user the first time."
