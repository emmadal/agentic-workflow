@AGENTS.md

## Claude Code specifics
- Default model: `claude-opus-5-5` (`.claude/settings.json`); generated sub-agents use `model: opus`.
- Skills load from `.claude/skills/` (generated from `.agents/skills/`). Invoke with `/<skill-name>`.
- Sub-agents load from `.claude/agents/` (generated from `.agents/agents/`).
- After editing anything in `.agents/`, run `python -m scripts.sync_agents`.
