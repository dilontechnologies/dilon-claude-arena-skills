# Document verification — requirements notes

Source of truth for current behavior:
`skills/dilon-arena-eco-creator/scripts/verify_documents.py` (built
2026-09-02, sections 1, 2a, and 2b — see "Build status" below) and
step 9 of `skills/dilon-arena-eco-creator/SKILL.md`. This is a
sub-component of `dilon-arena-eco-creator`, not a separate skill — split
into its own requirements doc because the check has enough open questions
and its own data sources (document front matter, compiled document, and
change history) to track separately from the rest of the ECO flow.

## Handoff status (2026-09-02, end of session)

**Read this first if picking this up in a fresh session.** Everything in
this doc and in `SKILL.md` describes the *intended* design — that part is
settled and shouldn't need re-litigating. Code status is more mixed:

- **Not yet reflected in code: 2a and 2b must be skipped for form
  documents.** Confirmed against the actual compiler code
  (`generate_dilon_form.py`, `dilon-tools` plugin): form documents (FO,
  RE) are built from the base template with **no body tables at all** —
  no signature-approval table and no revision-history table, only the
  running header/footer. `_extract_signers`/`_extract_current_revision`
  in `verify_documents.py` currently report "table not found" as a
  **blocking error** unconditionally, which means every form submitted
  today would fail verification for a structural reason that isn't
  actually a defect. See "2a"/"2b" applicability notes below for the
  resolved fix (caller-supplied `is_form` flag) — not yet implemented.

- `verify_documents.py` has code for all three sections (1, 2a, 2b)
  described below, including the section 1 (header/footer) rewrite.
- `tests/eco_creator_scripts/test_verify_documents.py` has been rewritten
  to match (a `_build_docx` fixture that now also builds header/footer
  tables, plus `get_item`/`get_change` mocks) — **but this rewritten test
  file has not actually been run.** The session was interrupted
  mid-test-run when the user redirected to finishing this requirements
  doc instead. Before trusting any of section 1's behavior, run:
  `./.venv/Scripts/python.exe -m pytest tests/eco_creator_scripts -q`
  and fix whatever fails — treat the header/footer extraction logic
  (`_extract_header_footer`, `_check_header_footer` in
  `verify_documents.py`) as unverified until that's green.
- Everything else touched this session (the other 9 scripts under
  `skills/dilon-arena-eco-creator/scripts/`, the step 8b approval gate in
  `sync_item_connections.py`, and all `SKILL.md` wiring for steps other
  than step 9's document verification) **was** fully tested and green
  (55/55, then re-confirmed against the full repo suite) before this
  final round of changes — only the section-1 addition and its tests are
  in an unverified state.
- `env/requirements.txt` already has `python-docx>=1.1.0` added and
  installed in `.venv`; no environment setup should be needed.

## Build status (2026-09-02)

- **Source of truth changed from markdown front matter to the compiled
  .docx itself (2026-09-02, before the first build).** A markdown source
  isn't always available — TF documents never have one (see
  `dilon-arena-document-standard-tf`), and documents that predate the
  markdown-authoring pipeline don't either. Every document is guaranteed
  to have the compiled/uploaded .docx, so the script reads the signature
  and revision-history tables `dilon-document-compiler`/
  `dilon-document-form-compiler` always produce directly out of the local
  .docx file (via python-docx), located by header row text, not table
  index. See "2a"/"2b" below for the exact table shapes. This
  incidentally also resolves 2a's open question about `department_head`
  (see below) and confirms step 8a's Author resolution (the Preparer row
  IS the document's own stated preparer).
- **Section 1 (Format compliance): built (2026-09-02, second pass) —
  header/footer only.** The original three candidates (front-matter
  completeness, markdown styling-guide conformance, compiled-docx
  structural elements) were superseded by a concrete spec direct from the
  user: header Title/Number/Rev and footer doc-number/Rev/ECO #/Revision
  Date must each match the actual item name/number, the item's
  `new_revision_number` for this ECO, this ECO's real number, and today's
  date — plus the item number must appear generally in both the header
  and footer text. All **blocking**. See "1. Format compliance" below for
  the exact header/footer shape this reads.
- **2a (signature table vs. ECO reviewers): built.** Mismatch policy
  resolved: a signer who isn't a real ECO reviewer **blocks** progression
  to "ready to submit" (the reverse direction — an ECO reviewer missing
  from one document's signature block — is a warning only, not blocking;
  see the 2a section below for why).
- **2b (current-revision date vs. latest Arena upload): built.**
  Mismatch is a **warning**, not blocking (the docx-vs-pdf timestamp and
  timezone handling are both approximations — see 2b below — not
  confident enough to gate submission on).
- **Section 2c (other consistency checks): not built.** Still open, not
  decided which of the three candidates (if any) to include.
- **Override policy (resolved 2026-09-02):** this check cannot cover
  every document shape (legacy documents it can't even parse, for
  example), so a blocking failure is not an unconditional hard gate —
  `dilon-arena-eco-creator` step 9 may proceed past a reported failure
  with the user's approval. This is a workflow-level policy in
  `SKILL.md`, not something built into the script itself — the script
  always reports failures faithfully and never softens its own verdict.

## Purpose

Before `dilon-arena-eco-creator` tells the user an ECO is ready to submit
(step 9/10), verify the documents being uploaded on two dimensions:

1. **Format compliance** — each document matches Dilon's prescribed
   document format/template.
2. **Information consistency** — information recorded inside each document
   is consistent with what's recorded on the ECO itself (e.g. a document's
   signature table names the same people the ECO actually has as
   reviewers).

## Form

`skills/dilon-arena-eco-creator/scripts/verify_documents.py` — a
standalone script (not just `SKILL.md` prose), same as this repo's
convention for anything with deterministic parsing/comparison behavior.
Has a pytest test (`tests/eco_creator_scripts/test_verify_documents.py`,
direct-import + respx, not a subprocess CLI test — respx patches httpx
within the test process, which a subprocess would defeat).

## 1. Format compliance

**Built (2026-09-02), scoped to header/footer only.** The original three
candidates (front-matter completeness, markdown styling-guide
conformance, general compiled-docx structural elements) were superseded
by a concrete spec given directly by the user, checking the running
header/footer against the actual submission rather than the document's
internal structure generally.

**Confirmed inputs:** `dilon_docx_common.py`'s `populate_header()`/
`populate_footer()` — shared by both compilers, so this applies to every
narrative and form document alike:
- **Header** (4-column table, 1 row): logo | two paragraphs ("Title:
  `<title>`", "Number: `<doc_number>`") | "Rev `<current_revision>`" |
  page N of M (a live field, not read by this script).
- **Footer** (3-column table, row 0 of 2): "`<doc_number>` Rev
  `<current_revision>`" | "`<eco_number>`" | "Revision Date:
  `<eco_date>`" (row 1 is the confidentiality notice, not read).

**Checks, all blocking:**
- Header Title == the item's actual Arena `name` (`get_item`).
- Header Number == the item's actual Arena `number`, **and** the item
  number appears anywhere in the header's full text (a looser, redundant
  backstop independent of the exact-field parse — this is the literal
  "item number must appear in the header" requirement, checked twice: an
  exact-field match and a general-text match).
- Header Rev == `expected_revision` (the `new_revision_number` this item
  is actually getting on this ECO — passed in by the caller from step 7,
  not re-derived here).
- Footer's leading `<doc_number> Rev <current_revision>` ==
  `"<item_number> Rev <expected_revision>"`, and the item number appears
  anywhere in the footer's full text (same double-check as the header).
- Footer ECO # == the actual change's `number` (`get_change`).
- Footer Revision Date == **today's date (UTC)** — not an Arena upload
  timestamp (that's 2b, a different, non-blocking check of internal
  document/Arena consistency; this one checks the document was actually
  finalized today).

**Resolved:** override policy — see "Build status" above. A blocking
failure here is not an unconditional hard gate; the skill may proceed
with the user's approval.

**Still open:**
- No document body/content check (table of contents, required sections,
  placeholder leftovers) — the header/footer spec above doesn't cover
  this; still genuinely unscoped, same as before.
- Today's date is compared in UTC, same documented timezone
  approximation as 2b below — a late-night compile could land on a
  different calendar date once converted to Dilon's actual local
  timezone.

## 2. Information consistency: document vs. ECO

### 2a. Signature table vs. ECO reviewers

**Applicability (resolved 2026-09-02): narrative documents only.** Form
documents (FO, RE — see `dilon-arena-document-standard-fo`/`-re`) are
compiled with `dilon-document-form-compiler`, which produces **no
signature-approval table at all** (confirmed in
`generate_dilon_form.py`'s docstring: "no signature page... no
signature-approval table"). 2a cannot run against a document that
structurally has no signature table, so it must not even attempt to.
Since `verify_documents.py` deliberately doesn't read the markdown source
(that's the whole point of the compiled-docx redesign — TF and legacy
documents don't have one), it can't reliably infer form-vs-narrative
itself: doc-number prefix isn't safe (the PL and RE document-standard
skills explicitly warn not to assume by prefix), and inferring from table
absence would break the existing legacy-document detection (a missing
table on a *narrative* document is deliberately reported as an error —
see Known gaps — inferring "must be a form" from the same signal would
mask that case). Resolved: the caller passes an explicit per-document
`is_form` boolean in the JSON input (`dilon-arena-eco-creator` already
knows this per document — it's resolved at step 1a from the type's
Expected file formats section). When `is_form` is true, the script skips
signature-table extraction and 2a entirely for that document — no
error, no warning, nothing added to either list.

**Confirmed inputs:**
- **Document side (redesigned 2026-09-02):** the compiled .docx's own
  signature table, read via python-docx, located by its header row text
  (`"Group" / "Preparer" / "Signature"`), not by table index —
  `generate_dilon_doc.py`'s `create_signature_table()` is the generator
  this shape is confirmed against. Layout: header row, a Preparer row
  (department + author name — this is step 8a's Author field, confirmed:
  the document's own stated preparer), a second header row (`"Department"
  / "Name" / "Signature"`), a department-head row, then zero or more
  additional-approver rows (one per markdown source's original
  `signature_fields` entry, if the document came from the Dilon markdown
  pipeline at all — but the script doesn't need or read the markdown
  itself). Every row from the department-head row onward is checked
  against ECO reviewers; the Preparer row is not (preparing and reviewing
  are different roles). If the document wasn't produced by either
  compiler, this table won't be found by header text and the document is
  reported as an error, not guessed around — see Known gaps.
- **ECO side:** `get_change_history(change_guid)`, filtered to
  `action == "Add Additional Reviewer"` (property `"Change Approver
  Record"`). Reviewer name is the `newValue` string with its trailing
  qualifier stripped — confirmed format `"<Name> (Approval Required)"` on
  a real completed ECO (ECO-000162: "Kevin Lint (Approval Required)",
  "Pedro Cruz (Approval Required)"). This is the only way to read
  reviewers — Arena has no dedicated reviewers endpoint (confirmed by
  checking the full official spec), but the history feed carries it, so
  the MCP server header comment claiming reviewers are unreadable is
  wrong and should be corrected to say "no dedicated endpoint" instead of
  implying they can't be read at all.

**Confirmed constraint: matching is name-only, not department.**
`get_user`/`list_users` expose no department field on Arena's user object
at all, and this API credential's `list_users` only ever returns 3 users
regardless of filter (looks like an integration-scope limit, not a query
bug) — confirmed 2026-09-01 querying by full name, last name, wildcard,
and email for known users who returned zero results. There is no way to
derive "this person = Manufacturing/Quality/Regulatory" from Arena. The
`department` half of each `signature_fields` entry is a label the
document's author chose and cannot be cross-checked against Arena — the
tool can only confirm the `name` half is a real reviewer on the ECO.

**Resolved:**
- Mismatch policy: signer not a real reviewer -> **block**. Reviewer not
  in this document's table -> **warn** only.
- `department_head` **is** checked against ECO reviewers — resolved by
  the docx redesign itself: once read from the actual compiled table
  there's no structural distinction between the department-head row and
  an additional-approver row, so treating them differently would be
  arbitrary.
- Name matching: `re.sub(r"\s+", " ", name).strip().casefold()` — handles
  the observed whitespace quirks (`"Phillip  Gray"` double space,
  `"Shannon Buccellato "` trailing space) and is case-insensitive.
- Which documents get checked, and independently or as a union: the
  script checks exactly whatever document list `dilon-arena-eco-creator`
  passes it (see SKILL.md step 9) — each document independently against
  the same ECO reviewer set, no combined/union requirement. The skill,
  not the script, decides which documents to include (in practice: every
  document step 8 attached/revised this run).

**Still open:**
- Are there reviewer qualifier suffixes besides `"(Approval Required)"`
  (e.g. an optional/FYI reviewer type) that need including or excluding
  from the comparison set? The stripping regex (`\s*\([^)]*\)\s*$`) is
  generic — it removes any trailing parenthetical, not just that one
  literal string — but only one real qualifier has actually been observed
  (ECO-000162).

### 2b. Current-revision date vs. most recent Arena upload

**Applicability (resolved 2026-09-02): narrative documents only, same
reasoning as 2a.** Form documents have no revision-history table either
(same base template, no body tables at all) — the only revision
information a form carries is the header/footer "Rev `<n>`" fields, which
Section 1 already checks. 2b uses the same caller-supplied `is_form` flag
as 2a: when true, the script skips revision-table extraction and 2b
entirely for that document.

**Document side (redesigned 2026-09-02):** the compiled .docx's own
revision-history table, read via python-docx, located by its header row
text (`"REV #" / "DESCRIPTION OF CHANGE" / "ECO #" / "DATE"`) —
`generate_dilon_doc.py`'s `create_revision_table()` is the generator this
shape is confirmed against. The table is append-only in practice, so the
**last data row** is treated as the current revision; its `DATE` column
is what gets compared. That date must reflect **when the document was
most recently pushed to Arena for this ECO**, not just the day the ECO
was originally created or drafted — a single ECO can span multiple
document re-uploads (review feedback -> author revises -> new edition),
and the last row's DATE needs to track the latest one, not the first.

**Confirmed mechanism (verified 2026-09-01 against production, read-only):**
- Both `get_item_files(item_guid)` and `get_file_editions(file_guid)`
  return each file/edition with its own `creationDateTime` and
  `lastModifiedDateTime` — no extra call needed beyond what step 2 of
  `dilon-arena-eco-creator` already fetches. `get_item_files`'s per-file
  entry with `"latest": true` is the current edition.
- Confirmed accurate against a real re-upload event: `FO-00096`'s docx
  file (`HZJ27ULS8GZFYH4Z1CPH`) has edition `"1"` created
  `2024-10-18T15:20:49Z` and edition `"2"` (`latest: true`) created
  `2025-02-13T20:04:37Z`. That second edition's timestamp matches
  `AC-000008` ("Reupload of FO-00096"), submitted the same day
  (`2025-02-13T20:05:17Z`) — confirms edition `creationDateTime` tracks
  the actual push-to-Arena event, not some other unrelated timestamp.

**Resolved:**
- The docx and pdf editions of the same document can have different
  `creationDateTime`s (seconds apart, but still different) — the script
  takes whichever is later (`max()` of both), not per-file independent
  comparison.

**Still open:**
- Date-only comparison (the DATE column is `"YYYY-MM-DD"`) vs. Arena's
  UTC timestamp — a late-night UTC upload could land on a different
  calendar date once converted to Dilon's local timezone. The script
  currently compares against the plain UTC calendar date (no timezone
  conversion) as a documented approximation — this is exactly why a 2b
  mismatch is a warning, not a block. Which timezone Dilon actually wants
  here is still unanswered.
- This check can only run *after* step 8 uploads the file (the edition
  has to exist in Arena to have a timestamp) — if it then finds a
  mismatch, fixing it means recompiling and re-uploading, which creates
  yet another edition with a newer timestamp, requiring the check to
  re-run. Worth confirming this convergence loop terminates in practice
  rather than assuming it.

### 2c. Other consistency checks — not yet scoped

OPEN QUESTION: what other document fields should be cross-checked against
the ECO? Candidates worth considering, none decided yet. Written before
the 2026-09-02 docx redesign — restated against the docx tables where
the same idea still applies; not otherwise re-evaluated:
- Revision-history table's last row's `ECO #` column matches this ECO's
  actual number.
- Revision-history table's last row's `REV #` column matches the
  `new_revision_number` passed to `add_items_to_change`/
  `update_change_affected_item` (the relevant
  `dilon-arena-document-standard-<type>` skill's revision scheme).
- Front matter's `doc_number` matches the Arena item number the document
  is attached to.

## Known gaps

- **TF documents are a third, unaddressed case.** TF isn't compiled by
  either `dilon-document-compiler` or `dilon-document-form-compiler` (no
  markdown source at all — see `dilon-arena-document-standard-tf`),
  so it's not just missing signature/revision tables like a form; it may
  not even have a `populate_header`/`populate_footer` running header/
  footer in the same shape, or a .docx at all (primary format is pdf).
  Whether/how `verify_documents.py` should handle TF documents is a
  genuinely open question, separate from the form/narrative distinction
  above — not decided yet, found during the 2026-09-02 requirements
  review.
- **Legacy/non-Dilon-compiled documents**: if a document wasn't produced
  by `dilon-document-compiler` or `dilon-document-form-compiler`, it
  likely doesn't have a signature table with the exact "Group / Preparer
  / Signature" header or a revision table with the exact "REV # /
  DESCRIPTION OF CHANGE / ECO # / DATE" header — the script reports this
  as an error for that document (table not found) rather than attempting
  to parse an unknown table shape. Not yet tested against a real legacy
  document to confirm this is actually how it fails in practice.
- **Not yet tested end-to-end** inside `dilon-arena-eco-creator`'s actual
  step 9 flow on a real ECO with real compiled documents — only unit
  tests against hand-built minimal .docx fixtures matching the
  generator's table shape (`tests/eco_creator_scripts/test_verify_documents.py`).
