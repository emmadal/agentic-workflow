# Tool compatibility

One source of truth in `.agents/`, generated into each tool's native location.

| | Claude Code | OpenCode | Cursor | Codex | Gemini CLI |
|---|---|---|---|---|---|
| Instructions | `CLAUDE.md` (imports `AGENTS.md`) | `AGENTS.md` + `opencode.json` | `AGENTS.md` | `AGENTS.md` | `AGENTS.md` via `.gemini/settings.json` |
| Skills | `.claude/skills/` (generated) | `.agents/skills/` | `.agents/skills/` | `.agents/skills/` | `.agents/skills/` |
| Sub-agents | `.claude/agents/*.md` | `.opencode/agents/*.md` | `.cursor/agents/*.md` | `.codex/agents/*.toml` | `.gemini/agents/*.md` |
| Default model | `claude-opus-5-5` | `anthropic/claude-opus-5-5` | tool setting | tool setting | tool setting |

Locations were checked against each tool's documentation in Nov 2026. Tools evolve; re-verify when upgrading.

## Invoking skills

Skills load automatically when the task matches the `description` ("Use when ..."). Explicit invocation:

| Tool | How |
|------|-----|
| Claude Code | `/spec`, `/swift-ios`, or ask naturally |
| OpenCode | the agent calls its `skill` tool; ask "use the swift-ios skill" |
| Cursor | `/swift-ios` in Agent chat |
| Codex | `$swift-ios` or `/skills`; name the skill in the prompt |
| Gemini CLI | the model calls `activate_skill`; ask "use the swift-ios skill" |

Descriptions are written as triggers, single line, 500 characters or fewer, so every tool can decide correctly.

## Authoring rules (enforced by `python -m scripts.validate_skills`)

- Skill folder name equals frontmatter `name` (lowercase, hyphens, max 64 chars).
- Frontmatter has only `name` and `description` (optional `license`, `compatibility`, `metadata`). No tool-specific keys.
- `description` is quoted, one line, contains "Use when", at most 500 characters.
- Body at most 500 lines. Put detail in `references/`, helpers in `scripts/`, and link them as `references/x.md`.
- Agents have `name` (equal to file name), `description`, and `access`:
  - `read-only`: read, search. No shell, no edits.
  - `inspect`: read, search and shell. No edits.
  - `write`: read, search, edit, shell.
- Skill bodies are tool-neutral. Say "delegate to the `reviewer` agent, or follow its rules inline if sub-agents are unavailable".

## Workflow

```bash
# edit .agents/skills/** or .agents/agents/**
python -m scripts.validate_skills
python -m scripts.sync_agents
git add -A
```

CI fails if generated files drift (`python -m scripts.sync_agents --check`).

## What each generator maps

| `access` | Claude `tools` | OpenCode `permission` | Cursor | Gemini `tools` |
|---|---|---|---|---|
| read-only | Read, Grep, Glob | edit deny, bash deny | `readonly: true` | read_file, list_directory, glob, grep_search |
| inspect | + Bash | edit deny, bash ask (exact read-only git commands allowed) | `readonly: true` | + run_shell_command |
| write | + Edit, Write | edit allow, bash ask | writable | + write_file, replace |

Codex custom agents inherit the parent's sandbox and approvals and cannot override them. Read-only agents therefore disable the shell tool (`features.shell_tool = false`) and say so in their instructions; keep your Codex sandbox on `read-only` or `workspace-write` for the rest. `inspect` agents keep the shell on Codex because Codex cannot restrict individual commands per agent; `sandbox_mode` in an agent file is ignored by Codex, so none is emitted.

On Claude Code the `inspect` agents get the full `Bash` tool; project `permissions` in `.claude/settings.json` apply, but review output before trusting a read-only claim.

## Known limits

- Model pinning only applies to Claude Code and OpenCode. Other tools use their own model; pick the strongest available.
- Hooks (`.claude/settings.json`) are Claude Code only. CI enforces the same gates for every tool.

## Verification status

| Item | Status |
|------|--------|
| Cursor `readonly`, subagent fields | Confirmed in Cursor docs |
| Gemini tool names (`read_file`, `list_directory`, `glob`, `grep_search`, `write_file`, `replace`, `run_shell_command`) and `.gemini/agents` format | Confirmed in Gemini CLI docs |
| Codex agent TOML fields and `features.shell_tool` | Confirmed in Codex docs |
| OpenCode | Run locally: `opencode debug agents` lists all 11 agents with the right `edit`/`shell` permissions; `opencode debug config` shows `anthropic/claude-opus-5-5` |
| Claude Code | Run locally: `claude -p` sees all 18 skills and 11 agents and rejects decoy names |
| Cursor, Codex, Gemini CLI skill loading | Not run (tools not installed on the author's machine); paths follow each tool's docs |
| `android-emu.sh` | Run on a Pixel 9 emulator (Android 17): start, launch, shot, log, crash, stop |
| `ios-sim.sh`, `run-maestro.sh` | Syntax-checked; iOS runtimes and Maestro are not installed on the author's machine |
