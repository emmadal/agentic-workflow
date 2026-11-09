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
| inspect | + Bash | edit deny, bash ask (git read commands allowed) | `readonly: true` | + run_shell_command |
| write | + Edit, Write | edit allow, bash ask | writable | + write_file, replace |

Codex custom agents inherit the parent's permissions and cannot override them, so read-only intent is stated in the instructions and enforced by your Codex sandbox and approval settings.

## Known limits

- Model pinning only applies to Claude Code and OpenCode. Other tools use their own model; pick the strongest available.
- Cursor `readonly` and Gemini tool names follow their current docs; if a tool rejects a field, remove it in `scripts/sync_agents.py`.
- Hooks (`.claude/settings.json`) are Claude Code only. CI enforces the same gates for every tool.
