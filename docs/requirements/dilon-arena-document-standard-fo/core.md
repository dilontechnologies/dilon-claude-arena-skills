# `dilon-arena-document-standard-fo` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-document-standard-fo/SKILL.md`. This doc records the
empirical work and decisions behind FO's naming/revision rules. Split out
of the former `dilon-arena-file-naming`/`dilon-arena-file-revision` pair
(2026-09-01) when those were retired in favor of one skill per document
type — see `../README.md` for why.

## Purpose

Answer, for an FO (Form/Traveler) controlled document: what goes in its
file `name`/`title`, what revision-number string Arena needs, which file
category and Affected-Items picklist value it maps to, and how it's
compiled.

## Naming — RESOLVED

Convention: `<Item Number> Rev <Revision Number>.<ext>` for `name`,
`<Item Number> <Item Name>` for `title` (no revision). Confirmed via
`create_file`/`create_file_edition`/`update_file_summary` exposing no
`name` parameter, and a real attached file (`FO-00004`'s pdf/docx pair)
showing `name` tracks the uploaded filename exactly. `title` kept
descriptive by precedent — `dilon-arena-eco-creator`'s file-attach step has
called `create_file(title="<Number> <Item Name>", ...)` in real production
use since before this split (confirmed working on ECO-000262).

## Revision-numbering scheme — RESOLVED

Confirmed with the user (2026-08-31):

> First release to production is 00. We can still have prototype releases
> before the first official release, and that will be released as 00-A.

Final scheme: baseline/production `"00"`, `"01"`, `"02"`, ...; prototype
`"<next-numeric>-<letter>"`; production release condenses back to the
plain numeric. Full description in `SKILL.md`.

## Expected file formats — RESOLVED (one confirmed data point)

docx + pdf, pdf primary. Confirmed via `FO-00004`'s attached pdf/docx pair
(see Naming above) — the same evidence backing the naming convention also
shows both formats attached side-by-side, pdf marked primary. Not
independently re-confirmed for every FO item; the default is treated as
the norm going forward, per `dilon-arena-eco-creator`'s general
docx+pdf/pdf-primary practice (see that skill's step 8, and its
ECO-000262 production confirmation of a 5-document docx+pdf batch).

## Empirical verification — RESOLVED (real call, not just dry-run)

Tested in the sandbox workspace ("Dilon Technologies Validation", workspace
ID `901596215`) via a disposable test change (`ECO-000195`, category
Engineering Change Order):

- `add_items_to_change(FO-00001's working rev, target phase Prototype
  Release [PRODUCTION stage], new_revision_number="02-A")` → accepted,
  `newRevisionNumber: "02-A"` in the response.
- `add_items_to_change(FO-00161's working rev, same target phase — item
  was already at Prototype Release, legacy revision "A" —
  new_revision_number="01-B")` → accepted. Re-queried via
  `get_item_revisions`: the item's `WORKING` revision entry shows
  `"number": "01-B"`, confirming genuine persistence, not just an echoed
  request value.
- The same-phase transition this required (Prototype Release → Prototype
  Release, for a second prototype iteration ahead of the same production
  release) also succeeded — no error 3063. This is one confirmed data
  point in `dilon-arena-eco-creator`'s general lifecycle-phase reachability
  map (that skill's own section owns the map; this is just the one data
  point).

`FO-00001` was removed from `ECO-000195` afterward (only added for this
test). `ECO-000195` and `FO-00161`'s pending `"01-B"` working revision were
left in place at the user's request, for possible further testing — not
yet cleaned up as of this writing.

## Known gaps / not yet covered

- **Untested**: whether omitting `new_revision_number` on a production
  release that follows a run of prototype iterations correctly
  auto-assigns the matching plain numeric, or drifts/errors. Testing this
  requires completing/routing a change (not just adding items to a
  Working one) — out of scope so far. Current guidance: always pass the
  value explicitly.
- Whether the revision-number scheme needs any special handling if a
  prototype sequence is abandoned before reaching production release.
- Doesn't cover file *content* editing (markup, corrections, check-out/
  check-in) — only the naming/revision-number convention.
