---
name: discover
description: "Use when the request is vague or you have only a rough idea, are not sure what to build, or need options before committing: asks a few targeted questions, states assumptions, proposes 2-3 variants."
---
# Discover

Cheapest time to find a wrong requirement is before any code.

1. Read the repo and docs first. Ask only what they cannot answer.
2. Ask at most 5 questions, one decision each, ordered by how much the answer changes the work. Offer a default per question.
3. State assumptions as a list and ask for correction before proceeding:
   `ASSUMPTIONS: 1. ... 2. ...  Reply to correct, or I proceed.`
4. When the user lacks a concrete idea, give 2-3 variants with trade-offs (scope, cost, risk) and a recommendation.
5. Stop on contradictions. Name the conflict, present the trade-off, wait.
6. Finish with a one-paragraph problem statement. Next step is `spec`.

## Red flags
| Thought | Reality |
|---|---|
| "I'll fill the gap with a sensible guess" | Wrong guesses cost a rewrite. Ask or state the assumption. |
| "Ask everything up front" | A long questionnaire gets skimmed. Lead with the 1-3 that matter. |

## Verify
Every assumption is written down and confirmed or corrected; the user can restate the goal in one sentence.
