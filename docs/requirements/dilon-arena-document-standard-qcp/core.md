# `dilon-arena-document-standard-qcp` — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-document-standard-qcp/SKILL.md`. Split out of the
former `dilon-arena-file-naming`/`dilon-arena-file-revision` pair
(2026-09-01) — see `../README.md` for why, and
`../dilon-arena-document-standard-fo/core.md` for the shared naming/
revision scheme's original empirical verification record.

## Purpose

Answer, for a QCP controlled document: what goes in its file `name`/
`title`, what revision-number string Arena needs, which file category and
Affected-Items picklist value it maps to, and how it's compiled.

## Naming and revision — RESOLVED (inherited, not independently tested)

Same convention and scheme as `dilon-arena-document-standard-fo` — see
that skill's `core.md` for the empirical verification record.

## Expected file formats — RESOLVED (inherited, not independently tested)

Same default as `dilon-arena-document-standard-fo`: docx + pdf, pdf
primary. See that skill's `core.md` for the one confirmed data point
behind it. No QCP-specific testing done separately.

## Item connections — file category RESOLVED, Affected-Items OPEN QUESTION

File category "Quality Procedure" is confirmed —
`dilon-arena-eco-creator`'s step 8a named it explicitly for QCP/FTP prior
to this split. The change category's Affected-Items picklist value for
QCP was never confirmed the same way: the same skill's step 2 mapping only
named FO/WI/PL/RE explicitly and defaulted everything else to
`"Other Document(s)"`. **OPEN QUESTION**: is `"Other Document(s)"` actually
correct for QCP, or does the picklist have a QCP-specific entry that was
simply never checked? Resolve via `list_change_category_attributes` against
a real QCP change, or ask the user, before relying on either answer.

## Usage — RESOLVED (narrative), reissue behavior UNCONFIRMED

`dilon-arena-eco-creator`'s step 1a named QCP as narrative (alongside WI,
FTP, PL) prior to this split. Whether QCP has any PL/RE-style reissue
exception has never been asked — assumed no or same as WI (that is, none)
until confirmed otherwise.

## Known gaps / not yet covered

- Affected-Items picklist value (above) — unconfirmed.
- Same revision-scheme gaps as `dilon-arena-document-standard-fo` — inherited.
- Doesn't cover file *content* editing — only naming and revision-numbering.
