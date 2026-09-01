---
name: dilon-arena-document-standard-definer
description: Interview the user to define a new dilon-arena-document-standard-<type> skill (naming, revision, item connections, usage/update triggers) for a Dilon document type with no standard yet, and generate a submission file to send to the developer for inclusion in the main repo. Use when dilon-arena-eco-creator encounters a document type with no matching dilon-arena-document-standard-<type> skill, or when directly asked to define a new document type's standard.
---

# Dilon Document Standard Definer

Produces a new `dilon-arena-document-standard-<type>` skill by asking the
user the same questions every existing type skill already answers, then
writes it locally and prepares a submission file for the developer —
because a fresh document type showing up mid-ECO shouldn't dead-end at
"Other Document(s)" with no real rule behind it.

## When this fires

- `dilon-arena-eco-creator` hits a document type with no matching
  `dilon-arena-document-standard-<type>` skill (its step 1a/step 2/step 8).
- A user directly asks to define the standard for a new document type,
  independent of any ECO in progress.

## 1. Interview

Ask the user, covering each of these four areas (the same shape every
existing `dilon-arena-document-standard-<type>` skill uses — see
`dilon-arena-document-standard-fo` for a worked example of the target
shape):

1. **Naming**: does this type follow the standard `<Item Number> Rev
   <Revision Number>.<ext>` file `name` / `<Item Number> <Item Name>` file
   `title` convention every other type uses, or does it differ? If it
   differs, get the exact convention.
2. **Revision**: does this type follow the standard baseline/prototype/
   production scheme (`"00"`, `"01"`, ...; `"<next>-<letter>"` for
   prototype), or does it have its own scheme or an exception like PL/RE's
   reissue-as-new-item rule? If an exception, get its exact trigger
   condition and mechanism.
3. **Item connections**: what Arena file category does this type map to
   (`list_file_categories`, confirm live rather than guess), and what
   value does it take in the change category's Affected-Items multiselect
   picklist (`list_change_category_attributes`, confirm live against
   `possibleValues` rather than guess)?
4. **Usage / update triggers**: is this type a narrative document
   (`dilon-document-compiler`) or a fillable form
   (`dilon-document-form-compiler`)? Is there any special trigger for a new
   item vs. a revision beyond the standard revision-bump behavior?

Ask these one at a time or batched, per the user's stated preference for
this session; don't guess an answer and mark it resolved — if the user
doesn't know one, record it as an open question in the new skill's Known
gaps section instead of inventing a default.

## 2. Write the new skill locally

Once the interview is complete, write:
- `skills/dilon-arena-document-standard-<type>/SKILL.md`, following the
  same four-section shape (Naming, Revision, Item connections, Usage /
  update triggers) and frontmatter style as the existing six skills (see
  `dilon-arena-document-standard-fo` for the template).
- `docs/requirements/dilon-arena-document-standard-<type>/core.md`,
  following the same requirements-doc shape (Purpose, resolved facts,
  Known gaps) as the existing six.

Also update, the same way `dilon-arena-document-standard-fo` through `-re`
are indexed:
- `docs/requirements/README.md`'s "Skills" list — add the new entry.
- `CLAUDE.md`'s Skills section — add the new `###` entry.

Do this regardless of whether the current working directory is this
source repo or an installed plugin copy — always write the files.

## 3. Generate the submission file and prompt to send it

Generate one self-contained file,
`docs/requirements/dilon-arena-document-standard-<type>/submission.md`,
combining the new `SKILL.md`'s full content and `core.md`'s full content
under clear headers, formatted so it can be pasted directly into a GitHub
issue body.

**Always** tell the user, regardless of context:

> "I've written the new skill locally. Please send
> `docs/requirements/dilon-arena-document-standard-<type>/submission.md`
> to the developer (bchaloux@dilon.com) so it can be reviewed and added to
> the main repo."

This skill's responsibility stops here — it does not call `gh` or open a
GitHub issue itself; the developer creates the issue from the received
file on their own.

## Known limitations

- Doesn't validate the interview answers against a live Arena workspace
  itself (e.g. doesn't call `list_file_categories` to confirm the category
  name the user gave actually exists) — it records what the user says,
  flagging anything the user is unsure of as an open question, the same
  as every other skill in this repo does for unconfirmed facts.
- No mechanism to detect or merge a duplicate submission if two people
  independently define the same undeclared type before either reaches the
  developer — a manual review problem for the developer to catch when
  processing submissions, not something this skill resolves.
