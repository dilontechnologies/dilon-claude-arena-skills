# `dilon-arena-document-standard-wi` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-document-standard-wi/SKILL.md`. Split out of the
former `dilon-arena-file-naming`/`dilon-arena-file-revision` pair
(2026-09-01) when those were retired in favor of one skill per document
type — see `../README.md` for why, and
`../dilon-arena-document-standard-fo/core.md` for the shared naming/
revision scheme's original empirical verification record (tested via
FO-prefixed items; applies identically here).

## Purpose

Answer, for a WI (Work Instruction) controlled document: what goes in its
file `name`/`title`, what revision-number string Arena needs, which file
category and Affected-Items picklist value it maps to, and how it's
compiled.

## Naming and revision — RESOLVED

Same convention and scheme as `dilon-arena-document-standard-fo` — see
that skill's `core.md` for the empirical verification record. No WI-
specific naming/revision testing has been done separately; this doc
exists to hold WI-specific facts if/when they diverge from FO's.

## Item connections and usage — RESOLVED

File category "Work Instructions", Affected-Items value
`"Work Instruction (WI)"`, narrative document type — all confirmed by
`dilon-arena-eco-creator`'s existing production use prior to this split
(step 2's Affected-Items mapping and step 8a's category mapping named WI
explicitly).

## Known gaps / not yet covered

- Same revision-scheme gaps as `dilon-arena-document-standard-fo` (untested
  auto-assignment after a prototype run, no abandoned-sequence
  convention) — inherited, not independently re-tested for WI.
- Doesn't cover file *content* editing — only naming and revision-numbering.
