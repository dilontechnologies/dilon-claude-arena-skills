# `dilon-arena-document-standard-tf` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-document-standard-tf/SKILL.md`. Defined 2026-09-02 via
`dilon-arena-document-standard-definer`, triggered by adding a
"Suggested connections" step (8b) to `dilon-arena-eco-creator` and
realizing TF (the Detector Head's workflow/flow diagram, `TF-00008`) had
no standard yet.

## Purpose

Answer, for a TF controlled document: what goes in its file `name`/
`title`, what revision-number string Arena needs, which file category and
Affected-Items picklist value it maps to, how it's produced (since it
isn't compiled from Dilon markdown like every other type), and what it
should connect to.

## Naming and revision — RESOLVED (inherited, not independently tested)

Same convention and scheme as `dilon-arena-document-standard-fo` — see
that skill's `core.md` for the empirical verification record. Confirmed
consistent with real data: `TF-00008 Rev 00-A.pdf`/`.drawio` in the
Detector Head folder matches the standard `<Item Number> Rev <Revision
Number>.<ext>` pattern, at the expected `"00-A"` prototype-revision shape.

## Expected file formats — RESOLVED, non-standard (no fixed non-primary format)

**Primary is pdf**, consistent with every other type. Unlike every other
type, TF has **no single fixed non-primary/source format** — per the
user, "source can differ, it can be a visio or something else." `.drawio`
is the one confirmed example (`TF-00008`). This is a genuine type-specific
exception to the shared docx+pdf default every other
`dilon-arena-document-standard-<type>` skill states.

## Item connections — file category RESOLVED, Affected-Items OPEN QUESTION

**File category = "Technical File"** — per the user ("TF stands for
Technical File"), and confirmed to exist in the sandbox workspace's
`list_file_categories` response (`File \ Document File \ Technical
File`).

**Affected-Items picklist value: OPEN QUESTION**, same treatment as
QCP/FTP — no dedicated TF entry exists in the confirmed value list (see
`dilon-arena-eco-creator/core.md`'s "Affected Items picklist — full
confirmed value list"). Defaulting to `"Other Document(s)"`, flagged
unconfirmed until resolved live against a real TF change.

## Suggested connections — RESOLVED, self-referential (not a fixed list)

Per the user: a TF should reference "any document/part/subassembly/
fixture it references" — i.e. whatever the diagram actually depicts, not
a fixed per-type target list like every other type's Suggested
connections section. `dilon-arena-eco-creator`'s step 8b should ask the
user which items a given TF covers rather than trying to infer it.

## Usage — RESOLVED, no Dilon-markdown compile path; diagram export UNCONFIRMED

TF is **not produced from Dilon markdown source** — confirmed by the real
data: no markdown source file exists for `TF-00008`, only the `.drawio`
source and its `.pdf` export. Neither `dilon-document-compiler` nor
`dilon-document-form-compiler` applies, so `dilon-arena-eco-creator` step
1a's compiler-selection logic doesn't apply to TF at all.

Per the user, a `.drawio` source can be exported to pdf on the command
line — draw.io desktop's documented CLI export flags
(`--export --format pdf --output <out> <in>`) are the likely mechanism,
analogous to step 1a's Word COM automation for docx-sourced types, but
**this hasn't been tested in this environment** — needs the actual
installed executable path/flag syntax confirmed (see Known gaps) before
`dilon-arena-eco-creator` can drive it the way it drives Word today.
Conversion for a non-`.drawio` source (e.g. Visio) is undefined — the
user only said "it can differ."

No PL/RE-style reissue exception mentioned or expected for TF — assumed
to follow the standard revision-bump behavior, same as WI/QCP/FTP, until
told otherwise.

## Known gaps / not yet covered

- Affected-Items picklist value (above) — unconfirmed.
- draw.io CLI export syntax/executable path (above) — unconfirmed, not
  tested in this environment.
- Conversion method for a non-`.drawio` diagram source (e.g. Visio) to
  pdf — undefined.
- Same revision-scheme gaps as `dilon-arena-document-standard-fo` —
  inherited (untested auto-assignment on production release following a
  prototype run; no convention for an abandoned prototype sequence).
- Doesn't cover file *content* editing — only naming and revision-numbering.
- Not yet tested end-to-end inside `dilon-arena-eco-creator`'s actual
  step 1a/8/8b flow on a real TF item — this skill and step 8b's TF
  handling were both written from the interview above, not from a live
  run.
