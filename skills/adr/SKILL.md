---
name: adr
description: "Use when making a decision that is costly to reverse (framework, data model, API shape, architecture), or documenting why something was designed that way. Not for routine choices."
---
# ADR

1. Copy `docs/adr/0000-template.md` to `docs/adr/NNNN-<slug>.md` with the next number.
2. **Context**: the problem and the constraints that force a choice.
3. **Options**: at least two, honest pros and cons, including "do nothing".
4. **Decision**: the choice and the deciding reason.
5. **Consequences**: easier, harder, what to monitor, how to reverse.
6. Status `proposed`. A human sets `accepted`.
7. Never edit an accepted ADR. Supersede it with a new one and link both.

## Red flags
One option listed · reasons that are only preferences · no reversal path · decision recorded after the code shipped.

## Verify
A new teammate can tell what was decided, what was rejected, and why, without asking anyone.
