# Benchmarks

Compared against [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) v0.6.15, read from a local plugin install on 2026-11-09. Same method applied to both catalogs.

| Metric | this repo | agent-skills 0.6.15 |
|---|---:|---:|
| Skills | 33 | 25 |
| Always-loaded tokens (descriptions + instructions) | 2349 | 3804 |
| Always-loaded tokens per skill | 71 | 152 |
| Tokens to load one average skill | 347 | 3314 |
| Tokens to load the largest skill | 524 (mobile-device-testing) | 5307 (constraint-driven-development) |
| All skill bodies | 11469 | 82873 |
| On-demand references (not loaded by default) | 6978 | 16222 |

Reproduce:

```bash
python -m scripts.token_report --compare <path to agent-skills checkout or plugin dir>
python -m scripts.route_eval --min-rank1 95
```

Routing eval on this repo: 99 prompts across 33 skills, rank-1 99%, top-3 100%, 33/33 negative prompts routed away.

## What we kept from upstream

Skill structure that works: a "Use when" trigger description, red flags and rationalization tables for discipline skills, a verification checklist, a deterministic routing eval run in CI. The coverage list matches upstream (spec, plan, incremental implementation, TDD, code review, simplification, debugging, API design, security, performance, observability, git, CI/CD, migration, release, ADRs, context engineering, source-verified coding, browser testing, discovery).

## Where this repo differs

| Area | Upstream | This repo |
|---|---|---|
| Skill size | about 2,100 words each, everything inline | 400 words max, depth in `references/` loaded on demand |
| Always-loaded cost | every description plus a meta-skill | shorter descriptions, 450-word `AGENTS.md`, no meta-skill (routing comes from descriptions) |
| Budgets | line limit | enforced words, description length and catalog total, in CI |
| Mobile | none | Swift, Kotlin, Compose, KMP, React Native, Expo, device and emulator testing |
| Tools | Claude plus per-tool folders | one source in `.agents/`, generated for Claude, OpenCode, Cursor, Codex, Gemini, drift checked in CI |
| Agent permissions | prompt-level | `access` level mapped to each tool's permission model |

## Caveats

- Tokens are estimated as characters / 4. The estimate is identical for both catalogs but is not a tokenizer count.
- The routing eval is a lexical approximation (stemmed TF-IDF). Its prompts were written by this repo's author and the descriptions were tuned against them, so 99% overstates real-world accuracy. It catches missing vocabulary and overlapping descriptions; it does not judge semantics.
- No behavioral eval (does the agent do better with the skill) has been run. Fewer tokens and good routing are measured here; better outcomes are the goal, not a measured result.
- Upstream content was read, not copied. Skills here are written independently.
