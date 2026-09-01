# Requirements notes

Running notes on the intended behavior of each skill in this repo — what it's
supposed to do, why, and open questions about edge cases. These are informal
notes, not a formal spec: the goal is to have one place where "what should
this tool actually do" gets written down as it comes up, instead of living
only in `SKILL.md` prose or someone's memory.

## How to use this

- One folder per core skill, named after it (e.g. `dilon-arena-eco-creator/`).
  That folder holds the core skill's own requirements doc as `core.md`,
  plus the requirements docs for anything nested under it — amendments and
  sub-components alike — named without the repeated base-skill prefix
  (e.g. `script-document-verification.md`, `amendment-pl-re-item-numbering.md`).
  This keeps the top level of this directory from filling up one file per
  skill as amendments accumulate. A `script-` prefix flags a sub-component
  backed by actual testable code (under the parent skill's `scripts/`),
  not just `SKILL.md` prose — see `script-document-verification.md` for the
  worked example.
- Start a new folder when a new core skill is added; add a file to an
  existing folder when a sub-component or amendment is added to that skill.
- Write informally — bullet points, open questions, "we decided X because Y"
  notes. Prose over structure.
- When a note here changes a skill's actual behavior, update the skill's
  `SKILL.md` too. This directory records *why* and *what's still open*;
  `SKILL.md` is the source of truth for *what Claude actually does*.
- Flag unresolved questions explicitly (e.g. "OPEN QUESTION: ...") rather
  than guessing at an answer and writing it down as settled.

## Deciding where a new rule goes

As more Arena/Dilon rules come in, use this test to decide where a given
rule belongs — so it lands in a discoverable place instead of getting
buried inside a skill it doesn't quite fit, or silently duplicated across
two skills.

Ask, in order:

1. **Could this be invoked on its own**, independent of any other skill's
   workflow (e.g. "create a training plan")? -> It's a **new skill**. See
   "New skill vs. sub-component" below for whether it needs its own
   `skills/` directory or stays a sub-component.
2. **Does it only change what an existing skill would otherwise do, and
   only under specific, checkable conditions** (a document type, item
   category, prior state, workspace setting)? -> It's an **amendment**. See
   "Amendment skills" below.
3. **Otherwise** — it's unconditional new detail, a correction, or a fix to
   how an existing skill already behaves. -> A **core update**: add it to
   that skill's requirements doc first, then fold into `SKILL.md` once
   settled (see "How to use this" above).

This is orthogonal to **known limitations** (platform/API gaps, not Dilon
rules — e.g. `costingView` not being API-editable in
`dilon-arena-eco-creator`). Those aren't business rules at all, so they
don't go through this test — keep documenting them inline as a "Known
limitation: ..." section in whichever skill hit the gap, same as today.

### New skill vs. sub-component

A capability gets its own `skills/<name>/SKILL.md` only if it's
independently invokable — test 1 above. If it only ever runs as a step
nested inside exactly one parent skill's flow, with no standalone trigger
of its own, it stays a **sub-component**: its own requirements doc in the
parent's folder here (open questions, data sources, decisions), but no
`skills/` directory, referenced from the parent's `SKILL.md` at the point
it applies.

Worked example: `dilon-arena-document-verification` (format/consistency
checks run before `dilon-arena-eco-creator` lets a change go to
submission) is a sub-component — it has no reason to exist except as a
pre-submit step inside the ECO flow, so it gets a requirements doc
(`dilon-arena-eco-creator/script-document-verification.md`) and a pointer from
`dilon-arena-eco-creator`'s `SKILL.md`, not its own skill directory.

### Amendment skills

An amendment is a **conditional override** of a rule owned by another
skill — narrow enough that it shouldn't live independently invokable, and
targeted enough that Claude should surface it automatically the moment its
condition applies, rather than relying on a human (or Claude) to notice a
buried exception while reading the base skill's `SKILL.md`.

Making each amendment its own skill, rather than a subsection of the base
skill, is what makes that automatic: Claude Code triggers on a skill's
`description` frontmatter, so an amendment's description should name its
trigger condition precisely (e.g. "Use when revising a Test Plan (PL) or
Test Report (RE) item that already has a completed report against it").

- **Skill directory:** flat under `skills/`, named
  `<base-skill>-amendment-<condition-slug>` (e.g.
  `dilon-arena-file-revision-amendment-pl-re-item-numbering`) — flat
  because skills in this repo are flat, and nested `SKILL.md` discovery
  under a plugin's `skills/` tree isn't confirmed to work.
- **Requirements doc:** lives in the base skill's folder *here*, named
  without the repeated base-skill prefix (e.g.
  `dilon-arena-file-revision/amendment-pl-re-item-numbering.md`) — this is
  the one place naming diverges from the skill's own directory name, since
  the folder already supplies that context.
- **Two-way link:** the amendment's `SKILL.md` states which base skill and
  section it overrides and the exact condition that triggers it. The base
  skill gets **one pointer sentence** at the relevant point ("Exception:
  ... — see `<amendment-name>`, not this section") instead of inlining the
  exception — keeps the base skill's normal-path prose from bloating with
  every special case.
- **Index:** list amendments as a nested sub-bullet under their base
  skill's entry in `CLAUDE.md`'s Skills section, so the index stays a
  legible tree as amendments accumulate instead of a flat list mixing
  independent skills with narrow overrides.

**An amendment doesn't require its base skill to be fully specified
first.** The base skill only needs to exist as the thing that *owns* the
default rule being overridden — it can still have open questions or
"Known gaps" of its own. Waiting for a base skill to be "finished" before
writing down a known exception to it just means the exception has nowhere
to live in the meantime. If, while building an amendment, it turns out the
base skill's own scope is muddled (see the file-naming/file-revision split
below — the base skill was doing two unrelated things under one name),
fixing that is worth doing as part of the same pass, but that's a
consequence of the amendment surfacing the problem, not a precondition for
writing the amendment down.

**Worked case:** `dilon-arena-file-revision-amendment-pl-re-item-numbering`.
Dilon wants PL/RE (Test Plan/Test Report) items to keep a pure revision
history — instead of bumping the item's revision on a re-issue, once a
completed report already exists against a plan, the next issue becomes a
**new Basic Item** under a defined number (plan base + `-NN` sequence, e.g.
`PL-00004` -> `PL-00004-01`; `RE-00023` -> `RE-00023-02`), incrementing
regardless of which plan a report refers back to. This only applies to
PL/RE and only once a completed report exists — everything else still
follows `dilon-arena-file-revision`'s standard revision-bump rule. That
combination (conditional + overriding another skill's default) is exactly
what makes it an amendment rather than a core update to
`dilon-arena-file-revision` itself. Working out this amendment is also what
surfaced that the former `dilon-arena-file-editing` skill was bundling two
unrelated concerns (file naming, and revision numbering) under one name —
it was split into `dilon-arena-file-naming` and `dilon-arena-file-revision`
so the amendment has a single, correctly-scoped base skill to attach to.

**Update (2026-09-01):** this worked case's own base skill,
`dilon-arena-file-revision`, has since retired — the PL/RE exception
described above is now PL's and RE's own rule, stated directly in
`dilon-arena-document-standard-pl`/`-re` rather than as a cross-cutting
amendment (see "Document-type standard skills" below). The general
amendment mechanism above still applies to a future conditional override
that isn't type-based — e.g. one conditioned on a workspace setting or
prior item state that cuts across multiple document types — just not to
this specific case anymore.

### Document-type standard skills

A capability that's really "the rule set for one Dilon document type" gets
its own flat skill, named `dilon-arena-document-standard-<type>` (e.g.
`dilon-arena-document-standard-pl`), rather than a shared skill trying to
state one rule for every type. This is the pattern
`dilon-arena-file-naming`/`dilon-arena-file-revision` were split into on
2026-09-01, once the PL/RE amendment made clear that what looked like a
universal rule was really just "what's been confirmed for the types
touched so far."

Each `dilon-arena-document-standard-<type>` skill covers five sections,
consistently:
1. **Naming** — file `name`/`title` convention for this type.
2. **Revision** — this type's revision-numbering scheme, including any
   type-specific exception (e.g. PL/RE's reissue-as-new-item rule).
3. **Expected file formats** — which file formats this type expects
   attached and which one is primary (default: docx non-primary + pdf
   primary, unless a type-specific exception is confirmed).
4. **Item connections** — item/file category and the change's
   Affected-Items picklist value this type maps to.
5. **Usage / update triggers** — narrative vs. form classification, and
   what event triggers a new item vs. a revision.

Content that's genuinely identical across types today (e.g. the baseline/
prototype/production revision scheme, before PL/RE's exception) is
restated in each type's skill rather than factored into a shared one —
deliberately, so a future divergence for one type doesn't require
unbundling a skill other types still depend on. Where one type's skill
holds the original empirical verification record for content another type
shares (e.g. `dilon-arena-document-standard-fo` for the revision scheme),
other skills cross-reference it in their requirements doc rather than
duplicate the investigation narrative — but the *operative* `SKILL.md`
rule itself is still fully restated in each, not just linked.

When an undeclared document type is encountered,
`dilon-arena-document-standard-definer` interviews the user into a new
skill following this same shape, rather than falling back to a guessed
default.

## Skills

- `dilon-arena-eco-creator/`
  - [`core.md`](dilon-arena-eco-creator/core.md) — Engineering Change Order
    / Deviation / Admin Correction creation in Arena.
  - [`script-document-verification.md`](dilon-arena-eco-creator/script-document-verification.md)
    — sub-component: pre-submit format/consistency checks, no standalone
    skill.
- `dilon-arena-eco-canceler/`
  - [`core.md`](dilon-arena-eco-canceler/core.md) — cancel/delete/withdraw
    an ECO/Deviation/Admin Correction; the teardown counterpart to
    `dilon-arena-eco-creator`.
- `dilon-arena-document-standard-fo/`
  - [`core.md`](dilon-arena-document-standard-fo/core.md) — Form (FO)
    naming, revision, item-connection, and usage rules; holds the shared
    naming/revision scheme's empirical verification record.
- `dilon-arena-document-standard-wi/`
  - [`core.md`](dilon-arena-document-standard-wi/core.md) — Work
    Instruction (WI) naming, revision, item-connection, and usage rules.
- `dilon-arena-document-standard-qcp/`
  - [`core.md`](dilon-arena-document-standard-qcp/core.md) — QCP naming,
    revision, item-connection, and usage rules; Affected-Items picklist
    value flagged unconfirmed.
- `dilon-arena-document-standard-ftp/`
  - [`core.md`](dilon-arena-document-standard-ftp/core.md) — FTP naming,
    revision, item-connection, and usage rules; Affected-Items picklist
    value flagged unconfirmed.
- `dilon-arena-document-standard-pl/`
  - [`core.md`](dilon-arena-document-standard-pl/core.md) — Test Plan (PL)
    naming, revision, item-connection, and usage rules, including the
    reissue-as-new-item exception once a completed report exists.
- `dilon-arena-document-standard-re/`
  - [`core.md`](dilon-arena-document-standard-re/core.md) — Test Report
    (RE) naming, revision, item-connection, and usage rules, including the
    same reissue-as-new-item exception as PL.
- `dilon-arena-document-standard-definer/`
  - [`core.md`](dilon-arena-document-standard-definer/core.md) —
    interviews the user into a new `dilon-arena-document-standard-<type>`
    skill when `dilon-arena-eco-creator` (or a direct request) hits a
    document type with no standard yet.
