# agentic-workflow

agentic-workflow turns Claude Code (and Codex, Gemini CLI, OpenCode and Cursor) into a senior engineering team that works the way good teams do: a product thinker who asks the right questions, a spec writer, a planner, a test-first implementer, platform specialists for web, backend, iOS, Android, Kotlin Multiplatform, Flutter and React Native, a reviewer who never edits, a QA lead who tests the running app and fixes what breaks, and a release engineer who ships. 45 skills and 11 role agents, plain Markdown, written once and generated for every tool.

Built and maintained by [Emmanuel Dalougou](https://github.com/emmadal). It is the workflow I use every day to ship web and mobile products with AI agents, packaged so you can install it in a minute.

**Who this is for:**
- **Solo builders and founders** who want a disciplined process instead of a blank prompt
- **Mobile teams** shipping SwiftUI, Jetpack Compose, Kotlin Multiplatform, Flutter, React Native or Expo apps
- **Tech leads** who want spec-first work, small reviewed slices and evidence on every change

## What agentic-workflow is for

- **Spec before code.** Every change starts from written acceptance criteria and a small, ordered plan.
- **Proof, not promises.** Tests fail first, bugs are reproduced before they are fixed, and "it works" means it ran.
- **Current platform practices.** Each platform skill follows its vendor's guidance today: Apple for Swift, Google for Compose and Android, JetBrains for KMP, the Flutter team for Flutter.
- **Cheap to keep loaded.** About 70 tokens per skill sit in context; the detail loads only when a task needs it.
- **One source, every tool.** Claude Code, Codex, Gemini CLI, OpenCode and Cursor read the same skills.

## Quick start

1. Install it (two commands in Claude Code, see below).
2. Describe a feature and ask for `/spec`. You get goals, non-goals and testable acceptance criteria to approve.
3. Run `/code-review` on any branch with changes. You get ranked findings and a verdict.
4. Run `/qa` with your local or staging URL. It opens a real browser, reproduces bugs, fixes each one with a regression test and reports a health score.

Stop there. You will know if this is for you. When you want the whole loop, follow [the workflow](#the-workflow) from `/discover` to `/release`.

## Install

Requirements: one of the supported tools and Git. The repository tooling needs Python 3.11+; the scripts inside skills run on Python 3.9+ with no extra packages.

### Claude Code (recommended)

Open Claude Code and run:

```
/plugin marketplace add emmadal/agentic-workflow
/plugin install agentic-workflow@agentic-workflow
```

Skills appear namespaced, for example `/agentic-workflow:spec`, and the 11 agents are available to delegate to. Update later with `/plugin marketplace update agentic-workflow`, then `/plugin update agentic-workflow`. Current version: **1.0.0**.

Prefer plain files in one project instead of a plugin? From a clone, run `python -m scripts.install_skills /path/to/project --tool claude`. To try a local checkout without installing: `claude --plugin-dir /path/to/agentic-workflow`.

### Codex

The repository is a Codex plugin marketplace:

```bash
codex plugin marketplace add emmadal/agentic-workflow
codex plugin add agentic-workflow@agentic-workflow
```

Skills load as `agentic-workflow:<name>`. Update with `codex plugin marketplace upgrade`. Codex plugins carry skills only, so add the agents to a project with `python -m scripts.install_skills /path/to/project --tool codex` (writes `.codex/agents/*.toml`).

### Gemini CLI

The repository is a Gemini CLI extension with the skills, the sub-agents and a short `GEMINI.md` context:

```bash
gemini extensions install https://github.com/emmadal/agentic-workflow
gemini extensions update agentic-workflow      # later
```

Answer `y` when Gemini asks you to confirm. To install a single skill instead: `gemini skills install https://github.com/emmadal/agentic-workflow --path skills/make-pdf`.

### OpenCode

OpenCode reads the shared `.agents/skills/` folder and its own `.opencode/agents/`:

```bash
git clone https://github.com/emmadal/agentic-workflow && cd agentic-workflow
python -m scripts.install_skills /path/to/project --tool opencode
```

Ask "use the spec skill" and OpenCode loads it through its `skill` tool.

### Cursor

```bash
python -m scripts.install_skills /path/to/project --tool cursor
```

Skills go to `.agents/skills/`, agents to `.cursor/agents/`. Type `/spec` in Agent chat.

### Every tool at once, and other agents

```bash
python -m scripts.install_skills /path/to/project --tool all     # Claude Code, Codex, Gemini CLI, OpenCode, Cursor
python -m scripts.install_skills /path/to/project --dry-run      # preview without writing
```

Existing files are kept unless you pass `--force`; your `AGENTS.md`, `CLAUDE.md` and settings are never touched. Any other agent that follows the [Agent Skills](https://agentskills.io) standard can read the `skills/` folder directly, or use the community CLI: `npx skills add emmadal/agentic-workflow`.

| Tool | How to install | Skills | Agents | First invocation | Install verified |
|------|----------------|--------|--------|------------------|------------------|
| Claude Code | plugin (recommended) or `--tool claude` | plugin `skills/`, or `.claude/skills/` | `.claude/agents/` | `/agentic-workflow:spec` | yes |
| Codex | plugin marketplace; agents with `--tool codex` | plugin `skills/`, or `.agents/skills/` | `.codex/agents/*.toml` | ask for `agentic-workflow:spec` | yes, Codex CLI 0.167 |
| Gemini CLI | extension or `--tool gemini` | extension `skills/`, or `.agents/skills/` | extension `agents/`, or `.gemini/agents/` | "use the spec skill" | yes, Gemini CLI 0.68 |
| OpenCode | `--tool opencode` | `.agents/skills/` | `.opencode/agents/` | "use the spec skill" | yes |
| Cursor | `--tool cursor` | `.agents/skills/` | `.cursor/agents/` | `/spec` | follows Cursor's docs |

Check an install with `claude -p "list project skills"`, `gemini extensions list`, `codex plugin list` or `opencode debug agents`.

## See it work

An example session, abbreviated:

```
You:    I want users to export their invoices as PDF.
You:    /spec
Claude: [asks who exports, how many invoices, whether it must work offline]
        Goals: export one or many invoices as PDF from the invoice list.
        Non-goals: email delivery, custom templates.
        7 acceptance criteria. Edge cases: empty list, 500 invoices,
        unicode names, access revoked mid-export. Approve?

You:    Approved. /plan
Claude: 5 tasks, each with a test and a verification command.
        Risk: large exports block the request; task 3 moves them to a job.

You:    Build task 1.
Claude: [writes the failing test, watches it fail, implements, test green]
        [commits feat(export): render one invoice to PDF]

You:    /code-review
Claude: [reviewer agent, fresh context, no edits]
        HIGH: the invoice id from the URL is not checked against the user (IDOR).
        Verdict: fix before merge.

You:    Fix it, then /qa http://localhost:3000
Claude: QA found 3 issues, fixed 3, health 71 to 96.
        ISSUE-002: the export button stays enabled while running (double export).
        Regression test added, committed fix(qa): ISSUE-002.

You:    /ship
Claude: lint, types, tests, coverage and security scan green.
        PR opened with Summary, Changes, Testing. Waiting for your review.
```

Every step leaves evidence the next one reads: the spec feeds the plan, the plan feeds the tasks, review and QA findings become tests, and `/ship` refuses to open a pull request while a gate is red.

## The workflow

agentic-workflow is a process, not a pile of prompts. The skills run in the order good teams work:

**Discover → Spec → Plan → Build → Review → Test → Ship → Release**

| Skill | Your specialist | What it does |
|-------|-----------------|--------------|
| `/discover` | **Product Partner** | Start here when the idea is fuzzy. Asks a few targeted questions, states assumptions, proposes two or three options with trade-offs. |
| `/spec` | **Spec Author** | Goals, non-goals, testable acceptance criteria, edge cases, rollout and open questions. You approve it before any code. |
| `/plan` | **Tech Lead** | Splits the approved spec into small ordered tasks, each with a verification step, dependencies and risks. Waits for approval. |
| `/incremental-implementation` | **Senior Engineer** | Builds in thin vertical slices, verifies and commits each one, uses a feature flag for risky rollout. |
| `/test-driven-development` | **Test-First Engineer** | Red, green, refactor. Bug fixes start with a test that reproduces the bug. |
| `/debugging` | **Incident Engineer** | Reproduce, isolate, fix the root cause, prove it. For failing tests, crashes, regressions and flaky behavior. |
| `/code-review` | **Staff Reviewer** | Reviews the diff for correctness, tests, security, design, performance and scope. Ranked findings and a verdict. Never edits. |
| `/qa` | **QA Lead** | Tests the running web app, API or CLI, reproduces each bug, fixes it with a regression test and one commit per fix, and reports a health score before and after. |
| `/ship` | **Release Engineer** | Runs every check, gets an independent review, commits, pushes the branch and opens a short pull request. Never merges. |
| `/release` | **Launch Manager** | Pre-launch checklist, staged rollout, monitoring, rollback plan, post-launch review, for the web and the app stores. |
| `/context-save`, `/context-restore` | **Chief of Staff** | Saves a checkpoint (goal, decisions, remaining work, git state) and resumes exactly where you stopped, even in a new session. |

### Mobile

Start every mobile task with `/mobile-engineering`. It sets the cross-platform rules (offline first, old app versions, secrets, lifecycle, accessibility) and routes to the platform skill.

| Skill | Your specialist | What it covers |
|-------|-----------------|----------------|
| `/swift-ios` | **Apple Platform Engineer** | Swift 6 and 6.2 concurrency (default `MainActor` isolation, `@concurrent`), Observation, `NavigationStack`, SwiftData, Swift Testing, XCUITest accessibility audits, iOS 26 Liquid Glass. |
| `/kotlin-android` | **Android Engineer** | Google's app architecture, coroutines and Flow, Hilt with KSP, Room, DataStore, Keystore and Tink, Credential Manager and passkeys, 16 KB pages, WorkManager. |
| `/android-compose` | **Compose Engineer** | androidx Compose API guidelines, the Now in Android screen pattern, stability and strong skipping, Navigation 3, adaptive layouts, edge-to-edge, screenshot tests. |
| `/kotlin-multiplatform` | **KMP Engineer** | JetBrains' recommended structure, the Android-KMP library plugin, Ktor, Room KMP or SQLDelight, `@Throws` and SKIE for Swift, Swift Package Manager distribution. |
| `/flutter` | **Flutter Engineer** | The Flutter team's architecture: MVVM with `ChangeNotifier`, commands and `Result`, repositories and services, go_router, Pigeon, widget, golden and integration tests. |
| `/react-native` | **React Native Engineer** | New Architecture only, the React Compiler, FlashList v2, Reanimated 4, Expo Modules or Turbo Modules, Jest and Maestro. |
| `/expo` | **Expo Engineer** | Expo SDK 58, Expo Router, Expo UI, EAS Build, Submit, Update and Observe, config plugins and development builds. |
| `/mobile-device-testing` | **Device Lab** | Simulators, emulators and real devices: xcodebuild, Gradle Managed Devices, Maestro, screenshots, logs and crashes. |
| `/ios-qa` | **iOS QA Lead** | Drives the running iPhone or iPad app screen by screen: Dynamic Type, dark mode, VoiceOver labels, permissions, deep links, push, crash logs. Fixes come with XCUITest regressions. |
| `/android-qa` | **Android QA Lead** | Drives the running Android app over adb: tap by label, font scale, rotation, process death, TalkBack labels, ANRs, cold start and jank numbers. Fixes come with tests. |

### Web, backend and platform

| Skill | Your specialist | What it covers |
|-------|-----------------|----------------|
| `/frontend-engineering` | **Frontend Engineer** | Accessible components (WCAG 2.2 AA), every UI state, Core Web Vitals budgets, React 19 actions and the React Compiler, platform-first HTML and CSS. |
| `/nextjs-app-router` | **Next.js Engineer** | Next.js 16 App Router: server components, server actions, cache components, streaming, deployment on Vercel or self-hosted. |
| `/backend-engineering` | **Backend Engineer** | Layers, constraints and transactions, expand-migrate-contract migrations, object-level authorization, idempotency, resilience. |
| `/api-design` | **API Designer** | Contract first (OpenAPI 3.1+, Protobuf), RFC 9457 error responses, cursor pagination, idempotency keys, versioning and deprecation. |
| `/security-hardening` | **Security Engineer** | Threat model, input validation, passkeys and OAuth 2.1 with PKCE, secrets, SBOM and provenance, OWASP Top 10, MASVS and LLM risks. |
| `/observability` | **SRE** | OpenTelemetry logs, metrics and traces, SLOs and burn-rate alerts, mobile crash and ANR reporting. |
| `/performance-optimization` | **Performance Engineer** | Budget, measure, change one thing, prove the gain: queries, backend, Web Vitals, app startup and jank. |
| `/ci-cd` | **Build Engineer** | Fast gates, least-privilege workflows, SHA-pinned actions, OIDC, build provenance, staged deploys with rollback. |
| `/browser-testing` | **Web Test Engineer** | Playwright with role locators and web-first assertions, axe, traces, visual comparisons. |
| `/migration` | **Migration Lead** | Inventory consumers, migrate in steps, expand-migrate-contract, then delete the old path. |
| `/adr` | **Architect** | Records decisions that are costly to reverse, with the options and consequences. |

### Quality, documents and personal

| Skill | Your specialist | What it does |
|-------|-----------------|--------------|
| `/qa-testing` | **Test Strategist** | Test pyramid, flaky test fixes, coverage gaps and release readiness for any stack. |
| `/test-plan` | **QA Planner** | A risk-based test plan before release: levels, cases, devices and OS versions, exit criteria. |
| `/make-pdf` | **Publisher** | Markdown to a print-ready PDF through headless Chrome: cover, clickable contents, page numbers, running header, DRAFT watermark, offline by default. |
| `/make-docx` | **Document Editor** | Markdown to a native Word file with real styles, numbered lists, tables, images, contents and page numbers, using only the Python standard library. |
| `/git-workflow` | **Repository Steward** | Short-lived branches, atomic conventional commits, safe undo, reviewable pull requests. |
| `/code-simplification` | **Refactoring Partner** | Less nesting, duplication and indirection, with behavior pinned by tests. |
| `/source-verified-coding` | **Docs Checker** | Reads the current official docs before using a library, cites them and flags anything unverified. |
| `/context-engineering` | **Context Manager** | Keeps the session small: what to read, what to delegate, when to reset. |
| `/accountability` | **Accountability Coach** | Turns goals into dated commitments with proof, and runs check-ins and weekly reviews. |
| `/secretary` | **Executive Assistant** | Meeting minutes, email drafts, day and week plans. Drafts only; it never sends anything. |
| `/swe-interview` | **Interview Coach** | Mock coding, system design and behavioral interviews with rubric scores and targeted drills. |

### Which testing skill should I use?

| You want to... | Use |
|----------------|-----|
| Decide what to test and how much | `/qa-testing` (strategy) or `/test-plan` (a written plan for a release) |
| Write tests while building | `/test-driven-development` |
| Test a running website, API or CLI and fix what breaks | `/qa` |
| Test a running iOS or Android app and fix what breaks | `/ios-qa` or `/android-qa` |
| Automate browser end-to-end tests | `/browser-testing` |
| Run test suites on simulators, emulators or devices | `/mobile-device-testing` |

## The 11 agents

Skills tell the model how to work; agents are role-scoped helpers it can delegate to. The writer and the reviewer are always different agents. No sub-agents in your tool? The skills tell the model to follow the same rules inline.

| Agent | Access | Use for |
|-------|--------|---------|
| `planner` | read-only | Turn an approved spec into ordered tasks with risks |
| `explorer` | read-only | Find where something lives and how it works, with file and line references |
| `architect` | read-only | Compare design options and draft ADRs |
| `reviewer` | inspect, no edits | Fresh-context diff review with ranked findings |
| `security-auditor` | inspect, no edits | Vulnerability audit of a change |
| `implementer` | write | One planned task, test first |
| `backend-engineer` | write | Services, APIs, data, migrations, jobs |
| `frontend-engineer` | write | Web UI, accessibility, performance |
| `mobile-engineer` | write | iOS, Android, KMP, Flutter, React Native and Expo, on simulators and devices |
| `test-engineer` | write | Unit, integration and regression tests |
| `qa-engineer` | write | Test plans, edge cases, exploratory QA, release readiness |

Access maps to each tool's permission model: `read-only` has no shell and no edits, `inspect` has a shell but no edits, `write` has both. On Codex, read-only agents disable the shell tool.

## How it works

```
.agents/skills/<name>/SKILL.md     each skill, written once (plus references/ and scripts/)
.agents/agents/<name>.md           each agent, written once (name, description, access)
.agents/manifest.json              name and version for every plugin
          │
          ▼  python -m scripts.sync_agents
.claude/  .codex/  .gemini/  .opencode/  .cursor/      per-tool skills and agents
skills/  agents/                                       plugin and extension root
.claude-plugin/  .codex-plugin/  .agents/plugins/  gemini-extension.json
```

- **Descriptions are triggers.** Each skill has one line that starts with "Use when ...", so the model picks the right skill without reading the others.
- **Bodies are short.** A `SKILL.md` body is 400 words or less. Depth lives in `references/` and loads only when the task needs it. Helper scripts live in `scripts/`.
- **Routing is tested.** 140 prompts run on every pull request: 97.9% pick the right skill first, 100% within the top three, and 47 of 47 negative prompts go elsewhere.
- **The cost is measured.** All descriptions plus `AGENTS.md` come to about 3,100 tokens for 45 skills; loading one skill averages about 440 tokens. Method and comparison in [`docs/benchmarks.md`](docs/benchmarks.md).
- **CI keeps it honest.** Lint, the skill validator, a drift check on every generated file, the routing eval, tests with a coverage floor, `pip-audit` and `bandit`.

## Platform notes

- **macOS and Linux** run everything the scripts need. On Windows, use WSL.
- **`/make-pdf`** prints with Chrome, Chromium, Edge or Brave in headless mode. Install one, or set `CHROME_PATH`. In containers that run as root it adds `--no-sandbox` automatically. On Linux, install `fonts-liberation` and `fonts-noto-color-emoji` for good typography.
- **`/qa`** uses the Playwright already in your project for its page probe (`npm i -D playwright`), and falls back to your installed Chrome when Playwright's own browser is missing.
- **`/ios-qa`** needs macOS and Xcode. simctl handles app and device state; tapping and the accessibility tree need one of AXe (`brew install cameroncooke/axe/axe`), idb or Maestro.
- **`/android-qa`** needs the Android SDK platform tools (`adb`) and, for emulators, the Android emulator.
- **Other skill packs:** if you also install gstack as user-level skills, its `/qa`, `/ios-qa` and `/make-pdf` share names with these when both are plain files. Plugin installs are namespaced (`agentic-workflow:qa`) and never clash.

## Docs

| Doc | What it covers |
|-----|----------------|
| [Workflow](docs/workflow.md) | Each stage, its owner, its output and its gate |
| [SDLC](docs/sdlc.md) | Models, budgets and how the agent loop runs |
| [Engineering standards](docs/engineering-standards.md) | The code, test and review standards every skill assumes |
| [Tool compatibility](docs/compatibility.md) | What each tool reads, plugin packaging, authoring rules, how each install was verified |
| [Benchmarks](docs/benchmarks.md) | Token cost, routing accuracy and behavioral evals against a no-skill baseline |
| [Architecture decisions](docs/adr/) | Why the defaults are what they are |

## Develop and contribute

```bash
git clone https://github.com/emmadal/agentic-workflow && cd agentic-workflow
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

1. Edit only the sources: `.agents/skills/<name>/SKILL.md` (with optional `references/` and `scripts/`), `.agents/agents/<name>.md`, and the version in `.agents/manifest.json`. Everything else is generated.
2. Follow the authoring rules: the folder name equals the frontmatter `name`; the description is one line of 280 characters or less starting with "Use when"; the body is 400 words or less; skill text stays tool-neutral.
3. Add at least three positive routing prompts and one negative prompt for a new skill in `evals/routing.json`.
4. Regenerate and run the gates:

```bash
python -m scripts.validate_skills
python -m scripts.sync_agents
python -m scripts.route_eval --min-rank1 95
python -m scripts.token_report
pytest -q --cov=agent --cov=scripts --cov-fail-under=80
ruff check . && ruff format --check .
```

5. Open a short pull request with conventional commits and a Summary, Changes, Testing description. A reviewer approves; nobody pushes to `main` directly.

`agent/` also holds a small tool-using loop on the Anthropic SDK with step and token budgets (`python -m agent.cli "explain the repo layout" --workdir .`). It is optional and does not load the skills.

## Troubleshooting

**Skills do not show up.** Restart the tool after installing. In Claude Code, plugin skills are namespaced (`/agentic-workflow:spec`); run `/plugin` to check the plugin is enabled. For Gemini CLI, `gemini extensions list` must show `agentic-workflow`; for Codex, `codex plugin list` must show it installed.

**The wrong skill loads.** Name the skill in your request ("use the qa skill"). If a description misroutes, add the prompt to `evals/routing.json` and tighten the description; the routing eval tells you when it is fixed.

**The Gemini install seems stuck.** It is waiting for confirmation: answer `y`.

**`make_pdf.py` exits with code 4.** No browser was found. Install Chrome or Chromium, set `CHROME_PATH`, or produce a self-contained HTML file with `--to html`.

**`ios-qa.sh tap` says a driver is missing.** Install AXe, idb or Maestro. Without one you can still take screenshots, change device state and open deep links.

**Generated files drift in CI.** Run `python -m scripts.sync_agents` and commit the result; never edit generated folders by hand.

## License

No license file has been added yet, so the code is published for reading and evaluation; reuse rights will come with a license.
