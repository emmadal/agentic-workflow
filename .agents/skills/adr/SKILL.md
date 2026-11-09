---
name: adr
description: "Use when choosing a framework, data model, API shape, architecture pattern or any decision that is expensive to reverse, or when asked to document why something was designed a certain way. Records an architecture decision record in docs/adr. Do not use for routine implementation choices."
---
# ADR

Act as a principal engineer. Decisions without recorded reasoning get relitigated or forgotten.

1. Copy `docs/adr/0000-template.md` to `docs/adr/NNNN-<slug>.md` using the next free number.
2. Fill in:
   - **Context**: the problem and the constraints that force a decision.
   - **Options**: at least two, each with honest pros and cons.
   - **Decision**: the choice and the deciding reason.
   - **Consequences**: what gets easier, what gets harder, what to monitor, how to reverse.
3. Set status `proposed`. A human changes it to `accepted`.
4. Never edit an accepted ADR. Add a new one that supersedes it and link both.
