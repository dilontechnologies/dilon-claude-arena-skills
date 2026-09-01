# `dilon-arena-document-standard-ftp` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-document-standard-ftp/SKILL.md`. Split out of the
former `dilon-arena-file-naming`/`dilon-arena-file-revision` pair
(2026-09-01) — see `../README.md` for why, and
`../dilon-arena-document-standard-fo/core.md` for the shared naming/
revision scheme's original empirical verification record.

## Purpose

Answer, for an FTP controlled document: what goes in its file `name`/
`title`, what revision-number string Arena needs, which file category and
Affected-Items picklist value it maps to, and how it's compiled.

## Naming and revision — RESOLVED (inherited, not independently tested)

Same convention and scheme as `dilon-arena-document-standard-fo` — see
that skill's `core.md` for the empirical verification record.

## Item connections — file category RESOLVED, Affected-Items OPEN QUESTION

File category "Quality Procedure" is confirmed —
`dilon-arena-eco-creator`'s step 8a named it explicitly for QCP/FTP prior
to this split. The change category's Affected-Items picklist value for
FTP was never confirmed the same way: the same skill's step 2 mapping only
named FO/WI/PL/RE explicitly and defaulted everything else to
`"Other Document(s)"`. **OPEN QUESTION**: is `"Other Document(s)"` actually
correct for FTP, or does the picklist have an FTP-specific entry that was
simply never checked? Resolve via `list_change_category_attributes` against
a real FTP change, or ask the user, before relying on either answer.

## Usage — RESOLVED (narrative), reissue behavior UNCONFIRMED

`dilon-arena-eco-creator`'s step 1a named FTP as narrative (alongside WI,
QCP, PL) prior to this split. Whether FTP has any PL/RE-style reissue
exception has never been asked — assumed no or same as WI (that is, none)
until confirmed otherwise.

## Known gaps / not yet covered

- Affected-Items picklist value (above) — unconfirmed.
- Same revision-scheme gaps as `dilon-arena-document-standard-fo` — inherited.
- Doesn't cover file *content* editing — only naming and revision-numbering.
