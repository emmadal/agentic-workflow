# Benchmarks

Compared against [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) v0.6.15, read from a local plugin install on 2026-11-09. Same method applied to both catalogs.

| Metric | this repo | agent-skills 0.6.15 |
|---|---:|---:|
| Skills | 33 | 25 |
| Always-loaded tokens (descriptions + instructions) | 2349 | 3804 |
| Always-loaded tokens per skill | 71 | 152 |
| Tokens to load one average skill | 355 | 3314 |
| Tokens to load the largest skill | 524 (mobile-device-testing) | 5307 (constraint-driven-development) |
| All skill bodies | 11729 | 82873 |
| On-demand references (not loaded by default) | 6978 | 16222 |

Reproduce:

```bash
python -m scripts.token_report --compare <path to agent-skills checkout or plugin dir>
python -m scripts.route_eval --min-rank1 95
```

Routing eval on this repo: 99 prompts across 33 skills, rank-1 99%, top-3 100%, 33/33 negative prompts routed away. The table above was regenerated after the last skill edits (355 tokens per average skill).

## Behavioral eval (does the skill change the agent's output?)

Harness: `evals/behavioral/run.py`. Each run is a headless `claude -p` call on Sonnet in a throwaway directory with no user plugins, hooks, MCP servers or skills, and the skill text appended to the system prompt. Three arms: no skill, this repo's skills, upstream's closest skills. Graders are objective (tests run, keyword hits, file checks); no model judges another model. 5 tasks, 3 reps per arm, 45 runs, 0 failed calls.

| Arm | Mean normalized score | Mean input tokens | Mean cost per run |
|---|---:|---:|---:|
| no skill | 0.789 | 14,845 | $0.020 |
| this repo | 0.950 | 18,817 | $0.027 |
| agent-skills 0.6.15 | 0.883 | 37,380 | $0.060 |

Per task (mean score, checks passed):

| Task | no skill | this repo | upstream |
|---|---:|---:|---:|
| tdd: fix a bug (regression test, proves it fails on old code, fix, suite green) | 1.00/4 | 4.00/4 | 4.00/4 |
| scope: add a flag without touching unrelated code, with a test | 3.00/4 | 3.00/4 | 3.00/4 |
| security: review a file with 6 planted vulnerabilities | 5.67/6 | 6.00/6 | 6.00/6 |
| compose: review a Compose screen with 7 planted issues | 7.00/7 | 7.00/7 | 7.00/7 |
| vague: "Build me a food delivery app" (asks questions, builds nothing) | 2.00/2 | 2.00/2 | 1.33/2 |

After porting a few upstream ideas into the skills (stop-the-line, change sizing, ask-first boundaries, error-budget gate), the `tdd` and `scope` tasks were rerun (`results-after-port.json`): this repo 4.00/4 and 3.00/4, upstream 3.33/4 and 3.00/4, no skill 1.00/4 and 3.00/4.

What this shows:
- Skills change behavior most on discipline tasks. Bug fixes: without a skill the agent fixes the code and writes no regression test (1/4); with either skill it writes one first and proves it fails on the original code.
- On capability tasks (reviews) Sonnet already finds nearly everything, so skills add little there.
- Our skills match or beat upstream on every task at about half the cost per run, and 2x lower input tokens. Skill text is the difference: about 350 tokens per skill here vs about 3,300 upstream.
- Shared weakness: no arm, upstream included, adds a test when the repo has none (`scope.test_added` 0/3 everywhere). The model says it would be scope creep. An instruction to add one made no difference, so it was removed.

Limits of this evidence:
- 3 reps per cell on one model (Sonnet). Differences between this repo and upstream are small except `vague` (3/3 questions asked vs 1/3) and the `tdd` rerun; they are not statistically significant.
- Tasks are small and the keyword graders are crude. They check for a topic being mentioned, not for quality of explanation.
- The upstream arm gets its closest skills as plain text, so upstream's routing is not exercised, only its content.
- The first matrix ran before the harness was hardened (narrower Bash grants, scrubbed environment, grading in a subprocess); the rerun used the hardened harness. The harness still runs on the host machine in throwaway directories, not in a container.
- Skill edits between the two runs (ported ideas) mean the first matrix is not a rerun of the final skills.

Reproduce (spends tokens, not part of CI):

```bash
python evals/behavioral/run.py --upstream <agent-skills checkout or plugin dir> --reps 3
python evals/behavioral/report.py
```

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
- Outcome quality is measured only by the small behavioral eval above, not by real-world projects.
- Upstream content was read, not copied. Skills here are written independently.
