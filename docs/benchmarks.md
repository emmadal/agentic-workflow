# Benchmarks

Compared against [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) v0.6.15, read from a local plugin install on 2026-11-09. Same method applied to both catalogs.

| Metric | this repo | agent-skills 0.6.15 |
|---|---:|---:|
| Skills | 33 | 25 |
| Always-loaded tokens (descriptions + instructions) | 2351 | 3804 |
| Always-loaded tokens per skill | 71 | 152 |
| Tokens to load one average skill | 365 | 3314 |
| Tokens to load the largest skill | 524 (mobile-device-testing) | 5307 (constraint-driven-development) |
| All skill bodies | 12069 | 82873 |
| On-demand references (not loaded by default) | 6978 | 16222 |

Reproduce:

```bash
python -m scripts.token_report --compare <path to agent-skills checkout or plugin dir>
python -m scripts.route_eval --min-rank1 95
```

Routing eval on this repo: 99 prompts across 33 skills, rank-1 99%, top-3 100%, 33/33 negative prompts routed away. The table above was regenerated after the last skill edits (355 tokens per average skill).

## Behavioral eval (does the skill change the agent's output?)

Harness: `evals/behavioral/run.py`. Each run is a headless `claude -p` call on Sonnet in a throwaway directory with no user plugins, hooks, MCP servers or skills, and the skill text appended to the system prompt. Three arms: no skill, this repo's skills, upstream's closest skills. Graders are objective (tests run, files checked, question marks counted); no model judges another model.

### Main result: 90 runs, 10 per cell, 0 failed calls (`results-n10.json`)

| Arm | Perfect runs (every check passed) | Mean normalized score | Mean cost per run |
|---|---:|---:|---:|
| no skill | 7/30 | 0.617 | $0.021 |
| this repo | 26/30 | 0.963 | $0.030 |
| agent-skills 0.6.15 | 14/30 | 0.823 | $0.050 |

Fisher exact test on perfect runs: this repo vs no skill p < 0.001; this repo vs upstream p = 0.002.

| Task | no skill | this repo | upstream | ours vs upstream (p) |
|---|---:|---:|---:|---:|
| tdd: fix a bug (regression test, fails on old code, fix, suite green), perfect runs | 0/10 | 10/10 | 10/10 | 1.00 |
| scope_tests: add a flag in a repo that already has tests, with a new test, perfect runs | 0/10 | 7/10 | 1/10 | 0.020 |
| vague: "Build me a food delivery app" (asks questions, builds nothing), perfect runs | 7/10 | 9/10 | 3/10 | 0.020 |

- **Bug fixes:** without a skill the agent fixes the code and writes no regression test. Either skill fixes that, every time.
- **Adding a test with a feature:** only this repo's incremental-implementation skill ("every slice ships with a test for its new behavior") reliably does it: 7/10 vs 1/10 upstream and 0/10 with no skill.
- **Vague requests:** this repo's `discover` skill asks questions 9/10 times. Upstream's `interview-me` made the agent ask less than no skill at all (3/10 vs 7/10).
- **Cost:** about 40% lower per run than upstream, at 365 tokens per skill vs about 3,300.

### Second model: Haiku, 8 reps per cell (`results-haiku-n8.json`)

| Task | no skill | this repo | upstream |
|---|---:|---:|---:|
| tdd, perfect runs | 0/8 | 8/8 | 8/8 |
| scope_tests, perfect runs | 7/8 | 8/8 | 8/8 |
| vague | 16 of 24 calls failed (baseline and ours), not interpretable | | 1/8 asked questions |

- **Replicates:** a skill turns "fix the bug" into "write a failing regression test, then fix it" on Haiku too (0/8 to 8/8, p < 0.001). This repo and upstream tie.
- **Does not replicate:** this repo's lead over upstream on `scope_tests` and `vague`. On Haiku the baseline already adds the test 7/8 times, so there is nothing to improve.
- **`vague` on Haiku is not valid.** Every failed call was a baseline or this-repo run with an empty reply, most likely the agent hitting the 6-turn limit while building the app instead of asking questions. Dropping failed runs would be survivorship bias, so no pooled score is reported for this model.
- Tokens: the skill text here costs about 365 tokens, upstream's about 3,300, so cost per run is lower for this repo on both models.

So the supported claim is: skills clearly beat no skill on discipline tasks on two models; this repo matches upstream on the bug-fix task on both models, and beats it on two other tasks on Sonnet only.

### Earlier 5-task matrix, 3 reps (`results.json`, `results-after-port.json`)

On review tasks (6 planted vulnerabilities, 7 planted Compose issues) Sonnet already finds nearly everything without a skill (5.67/6 and 7/7), and both skill sets match it, so skills add little for capability-bound tasks.

### Limits of this evidence

- One model (Sonnet), 10 reps per cell, three tasks. The tasks were chosen after an earlier run showed where skills made a difference, and the `incremental-implementation` test rule was added after the first scope result. That is some tuning toward the benchmark. The `scope_tests` fixture is new and was not used for tuning, but treat the p-values as optimistic.
- Graders are objective but crude: question marks, file existence, test results.
- The upstream arm gets its closest skills as plain text, so upstream's routing is not exercised, only its content. Upstream may suit a different prompt style or tool setup.
- Perfect-run rate pools tasks the authors picked, not a random sample of engineering work.
- Not shown: results on real projects, other models, long multi-step work.

### Security boundary of the harness

The harness executes model-written code (`pytest`, `python cli.py`) as the current user. Scrubbed environments and narrow tool grants reduce risk but are not isolation. Run it on a disposable machine, VM or container, preferably with `--isolated-home` and a dedicated low-budget API key, and pin and review any upstream checkout you point it at. It has not been run inside a container.

Reproduce (spends tokens, not part of CI):

```bash
python evals/behavioral/run.py --upstream <agent-skills checkout or plugin dir> --reps 10 --tasks tdd,vague,scope_tests
python evals/behavioral/report.py evals/behavioral/results-n10.json
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
- Outcome quality is measured only by the behavioral eval above, not by real-world projects.
- Upstream content was read, not copied. Skills here are written independently.
