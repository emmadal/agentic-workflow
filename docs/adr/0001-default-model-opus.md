# 0001. Default model is Claude Opus 5.5

- Status: accepted
- Date: 2026-11-09

## Context

Engineering agents plan, edit code and review changes. Errors are costly: wrong plans and
missed review findings cost more than model tokens.

## Options

1. Sonnet 5.5: cheaper and faster, weaker on long multi-step reasoning.
2. Opus 5.5: strongest reasoning, higher cost and latency.

## Decision

Default to `claude-opus-5-5` in `agent/loop.py` and `model: opus` in every sub-agent.
Callers may pass `model=` to use a smaller model for bulk, low-risk work.

## Consequences

Higher cost per run, mitigated by step and token budgets. Revisit when evals show a smaller
model matches pass rate for a given role.
