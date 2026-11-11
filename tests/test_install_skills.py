from pathlib import Path

import pytest

from scripts import install_skills

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(p.name for p in (ROOT / ".agents" / "skills").iterdir())
AGENTS = sorted(p.stem for p in (ROOT / ".agents" / "agents").glob("*.md"))


def test_claude_install_has_all_skills_and_agents(tmp_path):
    assert install_skills.main([str(tmp_path)]) == 0
    for name in SKILLS:
        assert (tmp_path / ".claude" / "skills" / name / "SKILL.md").is_file()
    for name in AGENTS:
        assert (tmp_path / ".claude" / "agents" / f"{name}.md").is_file()
    assert not (tmp_path / ".agents").exists()


def test_other_tools_read_agents_skills(tmp_path):
    assert install_skills.main([str(tmp_path), "--tool", "codex"]) == 0
    assert (tmp_path / ".agents" / "skills" / SKILLS[0] / "SKILL.md").is_file()
    assert (tmp_path / ".codex" / "agents" / f"{AGENTS[0]}.toml").is_file()
    assert not (tmp_path / ".claude").exists()


def test_all_tools(tmp_path):
    assert install_skills.main([str(tmp_path), "--tool", "all"]) == 0
    for d in (".claude", ".opencode", ".cursor", ".codex", ".gemini"):
        assert (tmp_path / d / "agents").is_dir()


def test_existing_files_kept_unless_force(tmp_path):
    target = tmp_path / ".claude" / "skills" / "spec" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("mine")
    install_skills.main([str(tmp_path)])
    assert target.read_text() == "mine"
    install_skills.main([str(tmp_path), "--force"])
    assert target.read_text() != "mine"


def test_dry_run_writes_nothing(tmp_path, capsys):
    install_skills.main([str(tmp_path), "--dry-run"])
    assert list(tmp_path.iterdir()) == []
    assert "would write" in capsys.readouterr().out


def test_helper_scripts_stay_executable(tmp_path):
    install_skills.main([str(tmp_path)])
    for src in (ROOT / ".agents" / "skills").rglob("*.sh"):
        dest = tmp_path / ".claude" / "skills" / src.relative_to(ROOT / ".agents" / "skills")
        assert dest.stat().st_mode & 0o111


def test_rejects_missing_target_and_source_repo(tmp_path, capsys):
    assert install_skills.main([str(tmp_path / "nope")]) == 2
    assert install_skills.main([str(ROOT)]) == 2
    assert "error:" in capsys.readouterr().err


def test_rejects_unknown_tool(tmp_path):
    with pytest.raises(SystemExit):
        install_skills.main([str(tmp_path), "--tool", "vim"])


# --- plugin manifests and context helper ---

import json  # noqa: E402
import subprocess  # noqa: E402


def test_plugin_manifest_matches_generated_agents():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    listed = sorted(Path(a).name for a in plugin["agents"])
    assert listed == sorted(p.name for p in (ROOT / ".claude" / "agents").glob("*.md"))
    assert "skills" not in plugin  # loads the default skills/ directory (see test_plugins.py)
    assert (ROOT / "skills").is_dir()
    assert market["plugins"][0]["name"] == plugin["name"]
    assert market["plugins"][0]["version"] == plugin["version"]


def test_context_skills_exist():
    assert "context-save" in SKILLS and "context-restore" in SKILLS


def test_context_script_state_and_path(tmp_path):
    script = ROOT / ".agents" / "skills" / "context-save" / "scripts" / "context.sh"
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    state = subprocess.run(
        [str(script), "state"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout
    assert state.startswith("branch:")
    first = subprocess.run(
        [str(script), "path", "Fix Login: OAuth!"], cwd=tmp_path, capture_output=True, text=True
    ).stdout.strip()
    assert first.endswith("-fix-login-oauth.md")
    assert Path(first).parent == tmp_path / ".context" / "checkpoints"
    Path(first).write_text("x")
    second = subprocess.run(
        [str(script), "path", "Fix Login: OAuth!"], cwd=tmp_path, capture_output=True, text=True
    ).stdout.strip()
    assert second != first
    assert ".context/" in (tmp_path / ".git" / "info" / "exclude").read_text()


def test_context_script_rejects_unknown_command(tmp_path):
    script = ROOT / ".agents" / "skills" / "context-save" / "scripts" / "context.sh"
    result = subprocess.run([str(script), "nope"], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2
