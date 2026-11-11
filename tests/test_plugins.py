"""Plugin and extension packaging: Claude Code, Codex and Gemini CLI install from the repo root."""

import json
import re
from pathlib import Path

import pytest

from scripts import sync_agents

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(p.name for p in (ROOT / ".agents/skills").iterdir() if (p / "SKILL.md").is_file())
AGENTS = sorted(p.stem for p in (ROOT / ".agents/agents").glob("*.md"))


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())


def test_versions_and_names_agree_everywhere():
    meta = load(".agents/manifest.json")
    claude, codex, gemini = (
        load(".claude-plugin/plugin.json"),
        load(".codex-plugin/plugin.json"),
        load("gemini-extension.json"),
    )
    claude_market, codex_market = (
        load(".claude-plugin/marketplace.json"),
        load(".agents/plugins/marketplace.json"),
    )
    for doc in (claude, codex, gemini, claude_market["plugins"][0], codex_market["plugins"][0]):
        assert doc["name"] == meta["name"]
        assert doc["version"] == meta["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+", meta["version"])


def test_descriptions_state_real_counts():
    desc = load("gemini-extension.json")["description"]
    assert desc.startswith(f"{len(SKILLS)} skills and {len(AGENTS)} role agents")


def test_claude_plugin_uses_default_skills_dir_and_claude_agents():
    plugin = load(".claude-plugin/plugin.json")
    # `skills` adds to the default skills/ dir, so declaring it would load every skill twice.
    assert "skills" not in plugin
    listed = sorted(Path(a).stem for a in plugin["agents"])
    assert listed == AGENTS
    for agent in plugin["agents"]:
        assert agent.startswith("./.claude/agents/")
        assert (ROOT / agent).is_file()


def test_codex_plugin_points_at_root_skills():
    plugin = load(".codex-plugin/plugin.json")
    assert plugin["skills"] == "./skills/"
    assert plugin["interface"]["displayName"]
    market = load(".agents/plugins/marketplace.json")
    assert market["plugins"][0]["source"] == "./"


def test_gemini_extension_layout():
    ext = load("gemini-extension.json")
    context = ROOT / ext["contextFileName"]
    assert context.is_file()
    referenced = set(re.findall(r"`([a-z][a-z0-9-]+)`", context.read_text()))
    assert referenced <= set(SKILLS) | set(AGENTS) | {"activate_skill"}
    for name in AGENTS:
        text = (ROOT / "agents" / f"{name}.md").read_text()
        assert "\nkind: local\n" in text and "  - read_file\n" in text  # Gemini format


@pytest.mark.parametrize("name", SKILLS)
def test_root_skills_mirror_source(name):
    src = ROOT / ".agents/skills" / name
    dst = ROOT / "skills" / name
    src_files = sorted(p.relative_to(src) for p in src.rglob("*") if sync_agents.is_source_file(p))
    dst_files = sorted(p.relative_to(dst) for p in dst.rglob("*") if p.is_file())
    assert src_files == dst_files
    for rel in src_files:
        assert (src / rel).read_bytes() == (dst / rel).read_bytes()
        assert (src / rel).stat().st_mode & 0o111 == (dst / rel).stat().st_mode & 0o111


def test_manifest_errors_are_reported(tmp_path):
    (tmp_path / ".agents").mkdir()
    with pytest.raises(sync_agents.SyncError, match="cannot read"):
        sync_agents.load_manifest(tmp_path)
    (tmp_path / ".agents/manifest.json").write_text('{"name": "x"}')
    with pytest.raises(sync_agents.SyncError, match="missing"):
        sync_agents.load_manifest(tmp_path)


def test_bytecode_is_never_copied(tmp_path):
    import shutil

    shutil.copytree(ROOT / ".agents", tmp_path / ".agents")
    cache = tmp_path / ".agents/skills/make-pdf/scripts/__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "mdlite.cpython-312.pyc").write_bytes(b"x")
    files = sync_agents.expected_files(tmp_path)
    assert not [f for f in files if "__pycache__" in f or f.endswith(".pyc")]


def test_check_detects_stale_manifest(tmp_path):
    import shutil

    shutil.copytree(ROOT / ".agents", tmp_path / ".agents")
    sync_agents.sync(tmp_path)
    assert sync_agents.check(tmp_path) == []
    (tmp_path / "gemini-extension.json").write_text("{}")
    assert "out of date: gemini-extension.json" in sync_agents.check(tmp_path)
    (tmp_path / "gemini-extension.json").unlink()
    assert "missing: gemini-extension.json" in sync_agents.check(tmp_path)
