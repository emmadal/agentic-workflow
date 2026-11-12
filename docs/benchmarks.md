# Benchmarks

Compared against [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) v0.6.15, read from a local plugin install on 2026-11-09. Same method applied to both catalogs.

| Metric | this repo | agent-skills 0.6.15 |
|---|---:|---:|
| Skills | 51 | 25 |
| Always-loaded tokens (descriptions + instructions) | 3139 | 3804 |
| Always-loaded tokens per skill | 61 | 152 |
| Tokens to load one average skill | 440 | 3314 |
| Tokens to load the largest skill | 747 (android-compose) | 5307 (constraint-driven-development) |
| All skill bodies | 22482 | 82873 |
| On-demand references (not loaded by default) | 41683 | 16222 |

Reproduce:

```bash
python -m scripts.token_report --compare <path to agent-skills checkout or plugin dir>
python -m scripts.route_eval --min-rank1 95
```

Routing eval on this repo: 160 prompts across 51 skills, rank-1 100%, top-3 100%, 55/55 negative prompts routed away. Regenerated on 2026-11-12 after adding `angular`, `vue`, `svelte`, `solidjs` and `vanilla-js` and tightening 22 existing descriptions to stay under the 9,000-character catalog budget; the agent-skills column is unchanged from 2026-11-09. The behavioral results below predate `flutter`, `qa`, `ios-qa`, `android-qa`, `make-pdf`, `make-docx`, `figma-to-expo` and the five web framework skills; they were not re-run.

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

### 2026-11-10 (evening): `scope_tests` and `vague` re-run after skill tightening (10 reps, Sonnet)

`incremental-implementation` now states an existing test suite is not an exemption (extend the nearest test file; a slice with no new test is not done), and `discover` now requires the first reply to be questions, not a plan. Both changes came from the failure analysis of the morning run.

| Task | no skill | this repo | agent-skills 0.6.15 |
|---|---:|---:|---:|
| scope_tests, perfect runs | 0/10 | **10/10** (was 7/10) | 0/10 |
| vague, perfect runs | 4/6 valid (4 empty replies) | **10/10** (was 9/10) | 1/10 |

- Files: `results-scope-tests-venv-n10.json` (valid) and `results-scope-vague-n10.json` (its `vague` rows are valid; its `scope_tests` rows are **invalid** — the first attempt ran with a system Python without `pytest`, so `suite_passes` graded false in every arm; the venv re-run above replaces them).
- The 4 empty `vague` baseline replies match the 6-turn-limit failure mode documented on Haiku; kept as imperfect rather than dropped.
- Combined with the unchanged `tdd` arm (10/10): **30/30 perfect runs (100%)** for this repo on Sonnet across `tdd`, `scope_tests` and `vague`.

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

## Personal skills (accountability, secretary, swe-interview)

Harness: `evals/behavioral/personal.py`. Headless `claude -p` on Sonnet, no tools, empty directory, project-only settings; arm "skill" appends the skill body to the system prompt. 5 runs per cell, 0 failed calls (`results-personal.json`). Graders are regexes and counts (7 checks per task, e.g. unknown owner flagged, absolute dates, 3 commitments or fewer with proof, no solution leaked); no model judges another model.

| Task | no skill, perfect runs | skill, perfect runs | no skill, mean score | skill, mean score | cost per run (no skill / skill) |
|---|---:|---:|---:|---:|---:|
| secretary: minutes from messy notes | 0/5 | 5/5 | 0.86 | 1.00 | $0.015 / $0.021 |
| accountability: vague goals | 0/5 | 3/5 | 0.46 | 0.77 | $0.027 / $0.016 |
| swe-interview: start a mock design interview | 3/5 | 5/5 | 0.91 | 1.00 | $0.015 / $0.016 |

Limits: n=5 per cell is small and no significance test was run; checks are mine and reward the skill's own rules (for example flagging unknown owners); one model. A first 1-run smoke test found `accountability` still lists more than 6 items on a two-goal request in some runs. The swe-interview grader was rewritten after reading a first run, so the single-turn numbers above are not comparable to the earlier smoke run.

### Multi-turn: accountability and swe-interview, 2 turns, 5 reps (`results-personal-multi.json`)

Harness: `evals/behavioral/personal_multi.py`. Same headless `claude -p` setup as above; turn 2 is a scripted user reply sent with `--resume`, and the grader checks the turn-2 reply only. Accountability checks commitment proof, the given deadline, an if-then for tiredness and a dated check-in; swe-interview checks question count, no solution leaked, no early scoring, no fluff.

Run of 2026-11-10 after the `swe-interview` mock-loop change (third run of the day, see below):

| Task | Arm | Perfect runs | Mean score | Mean cost per run | Failed runs |
|---|---|---:|---:|---:|---:|
| accountability | no skill | 0/3 | 0.62 | $0.041 | 2 |
| accountability | skill | 1/5 | 0.89 | $0.054 | 0 |
| swe-interview | no skill | 0/5 | 0.43 | $0.034 | 0 |
| swe-interview | skill | 5/5 | 1.00 | $0.036 | 0 |

History of the skill arm across the three runs (5 reps each, same grader):

| Run | swe-interview skill | accountability skill | What changed |
|---|---|---|---|
| 1 | 0/5 perfect, 0.80 | 4/5 perfect, 0.97 | baseline |
| 2 | 1/5 perfect, 0.70 | 3/5 perfect, 0.86 | swe-interview: one probe per turn, written as a question |
| 3 | 5/5 perfect, 1.00 | 1/5 perfect, 0.89 | swe-interview: "done" with open gaps is not done, probe again |

- **Swe-interview**: in run 1 the miss was `asks_at_most_two_questions` (4/5). Reading the replies showed 3 of those 4 asked zero questions (the probe was an imperative, "Walk me through ..."), and one asked three. Run 2 fixed the phrasing but 3/5 replies scored at once, because the scripted "I think I'm done" matched the skill's "when they finish, stop and score". Run 3 resolved that conflict in the skill and all 5 replies ask one question about the lost indices.
- **Accountability**: the skill was not edited, yet its perfect runs moved 4/5, 3/5, 1/5. The unstable check is `names_next_checkin` (fails 1/5, 2/5, 4/5). Treat run-to-run differences of this size as noise at n=5, and the dated check-in as not reliable yet.
- **Overfitting risk**: the swe-interview wording was changed twice against this single scripted scenario and the same grader, so 5/5 shows the two rules are followed here, not that the skill generalizes. The no-skill arm also moved 0.57 to 0.43 with no change.
- **Grader rewrite**: the swe-interview grader was rewritten after reading a first run (before run 1), so no earlier multi-turn numbers exist for comparison; neither grader was changed between runs 1 and 3. Only run 3 is kept in `results-personal-multi.json`; runs 1 and 2 are in git history and this table.

Limits: n=5 per cell, one model, self-written checks, two turns only. Reproduce: `python evals/behavioral/personal_multi.py --reps 5` (spends tokens, not part of CI).
