# Requirements notes

Running notes on the intended behavior of each skill in this repo — what it's
supposed to do, why, and open questions about edge cases. These are informal
notes, not a formal spec: the goal is to have one place where "what should
this tool actually do" gets written down as it comes up, instead of living
only in `SKILL.md` prose or someone's memory.

Unlike `docs/superpowers/` (gitignored, session-scoped planning artifacts),
this directory is tracked and committed — it's meant to persist and grow
across sessions as requirements expand.

## How to use this

- One file per skill/capability. Start a new file when a new skill is added.
- Write informally — bullet points, open questions, "we decided X because Y"
  notes. Prose over structure.
- When a note here changes a skill's actual behavior, update the skill's
  `SKILL.md` too. This directory records *why* and *what's still open*;
  `SKILL.md` is the source of truth for *what Claude actually does*.
- Flag unresolved questions explicitly (e.g. "OPEN QUESTION: ...") rather
  than guessing at an answer and writing it down as settled.

## Skills

- [`dilon-arena-eco-creator.md`](dilon-arena-eco-creator.md) — Engineering
  Change Order / Deviation / Admin Correction creation in Arena.
