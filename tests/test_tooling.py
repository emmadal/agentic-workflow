import re
import shutil
import tomllib
from pathlib import Path

import pytest

from scripts import sync_agents, validate_skills
from scripts.frontmatter import FrontmatterError, parse, quote

ROOT = Path(__file__).resolve().parent.parent

MOBILE_SKILLS = {
    "mobile-engineering",
    "swift-ios",
    "kotlin-android",
    "android-compose",
    "kotlin-multiplatform",
    "react-native",
    "expo",
    "mobile-device-testing",
}


def make_repo(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / ".agents", tmp_path / ".agents")
    return tmp_path


# --- frontmatter ---


def test_parse_quoted_and_plain():
    doc = parse('---\nname: x\ndescription: "a: b"\n---\nbody\n')
    assert doc.meta == {"name": "x", "description": "a: b"}
    assert doc.body == "body\n"


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter",
        "---\nname: x\n",
        "---\ndescription: Use when: colon\n---\n",
        "---\nname: a\nname: b\n---\n",
        "---\ndescription: 'single'\n---\n",
        "---\nbad line\n---\n",
    ],
)
def test_parse_rejects_invalid(text):
    with pytest.raises(FrontmatterError):
        parse(text)


def test_quote_roundtrip():
    value = 'say "hi": ok'
    assert parse(f"---\ndescription: {quote(value)}\n---\n").meta["description"] == value


# --- the real repository ---


def test_repo_skills_and_agents_are_valid():
    assert validate_skills.validate_skills(ROOT) == []
    assert validate_skills.validate_agents(ROOT) == []


def test_generated_files_are_in_sync():
    assert sync_agents.check(ROOT) == []


def test_mobile_skills_exist():
    names = {p.name for p in (ROOT / ".agents/skills").iterdir() if p.is_dir()}
    assert MOBILE_SKILLS <= names


def test_agents_md_only_references_real_skills():
    skills = {p.name for p in (ROOT / ".agents/skills").iterdir() if p.is_dir()}
    agents = {p.stem for p in (ROOT / ".agents/agents").glob("*.md")}
    text = (ROOT / "AGENTS.md").read_text()
    routing = [line for line in text.splitlines() if line.startswith(("Flow:", "Mobile:"))]
    names = {n for line in routing for n in re.findall(r"`([a-z][a-z0-9-]+)`", line)}
    assert names and names <= skills
    listed = re.findall(
        r"`([a-z][a-z0-9-]+)`", next(ln for ln in text.splitlines() if ln.startswith("Agents:"))
    )
    assert set(listed) == agents


def test_senior_persona_is_declared_once_not_per_skill():
    assert "senior engineer (10+ years)" in (ROOT / "AGENTS.md").read_text()
    for path in (ROOT / ".agents/agents").glob("*.md"):
        assert re.search(r"\b(senior|staff|principal)\b", path.read_text(), re.I), path.name


def test_helper_scripts_are_executable():
    for script in (ROOT / ".agents/skills/mobile-device-testing/scripts").glob("*.sh"):
        assert script.stat().st_mode & 0o111, f"{script.name} is not executable"


def test_codex_outputs_are_valid_toml():
    for path in (ROOT / ".codex/agents").glob("*.toml"):
        data = tomllib.loads(path.read_text())
        assert {"name", "description", "developer_instructions"} <= set(data)
        assert data["name"] == path.stem


def test_claude_agents_pin_opus():
    for path in (ROOT / ".claude/agents").glob("*.md"):
        assert parse(path.read_text()).meta["model"] == "opus"


def test_opencode_config_default_model():
    import json

    cfg = json.loads((ROOT / "opencode.json").read_text())
    assert cfg["model"] == "anthropic/claude-opus-5-5"


# --- access mapping ---


@pytest.mark.parametrize("access", ["read-only", "inspect", "write"])
def test_access_mapping(access):
    args = ("n", "d", access, "body\n")
    claude = sync_agents.render_claude(*args)
    assert f"tools: {sync_agents.CLAUDE_TOOLS[access]}" in claude
    has_edit = "Edit" in claude
    assert has_edit == (access == "write")
    assert ("edit: allow" in sync_agents.render_opencode(*args)) == (access == "write")
    assert ("readonly: true" in sync_agents.render_cursor(*args)) == (access != "write")
    gemini = sync_agents.render_gemini(*args)
    assert ("write_file" in gemini) == (access == "write")
    assert ("run_shell_command" in gemini) == (access != "read-only")


# --- validator failure modes ---


def write_skill(root: Path, name: str, front: str, body: str = "# t\nSenior.\n") -> None:
    d = root / ".agents/skills" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\n{front}\n---\n{body}")


def errors_for(tmp_path, name, front, body="# t\n"):
    repo = make_repo(tmp_path)
    write_skill(repo, name, front, body)
    return validate_skills.validate_skills(repo)


def test_name_must_match_directory(tmp_path):
    errs = errors_for(tmp_path, "bad-skill", 'name: other\ndescription: "Use when x."')
    assert any("must equal directory name" in e for e in errs)


def test_description_needs_trigger(tmp_path):
    errs = errors_for(tmp_path, "bad-skill", 'name: bad-skill\ndescription: "Does things."')
    assert any("Use when" in e for e in errs)


def test_description_length_limit(tmp_path):
    long = "Use when " + "x" * 600
    errs = errors_for(tmp_path, "bad-skill", f'name: bad-skill\ndescription: "{long}"')
    assert any("max 280" in e for e in errs)


def test_unquoted_colon_description_rejected(tmp_path):
    errs = errors_for(tmp_path, "bad-skill", "name: bad-skill\ndescription: Use when: x")
    assert any("double quotes" in e for e in errs)


def test_unknown_key_rejected(tmp_path):
    front = 'name: bad-skill\ndescription: "Use when x."\nallowed-tools: Bash'
    assert any("unsupported" in e for e in errors_for(tmp_path, "bad-skill", front))


def test_missing_reference_detected(tmp_path):
    front = 'name: bad-skill\ndescription: "Use when x."'
    errs = errors_for(tmp_path, "bad-skill", front, "# t\nSee `references/none.md`.\n")
    assert any("referenced file not found" in e for e in errs)


def test_agent_with_unknown_skill_detected(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".agents/agents/ghost.md").write_text(
        '---\nname: ghost\ndescription: "d"\naccess: write\n---\nLoad the `nope` skill.\n'
    )
    assert any("unknown skill 'nope'" in e for e in validate_skills.validate_agents(repo))


def test_agent_bad_access_detected(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".agents/agents/ghost.md").write_text(
        '---\nname: ghost\ndescription: "d"\naccess: root\n---\nbody\n'
    )
    assert any("access must be" in e for e in validate_skills.validate_agents(repo))


# --- sync behavior ---


def test_sync_creates_then_detects_drift(tmp_path):
    repo = make_repo(tmp_path)
    assert sync_agents.check(repo)  # nothing generated yet
    sync_agents.sync(repo)
    assert sync_agents.check(repo) == []

    (repo / ".claude/agents/reviewer.md").write_text("tampered")
    (repo / ".claude/skills/extra.txt").write_text("stale")
    problems = sync_agents.check(repo)
    assert any("out of date: .claude/agents/reviewer.md" in p for p in problems)
    assert any("stale: .claude/skills/extra.txt" in p for p in problems)

    sync_agents.sync(repo)
    assert sync_agents.check(repo) == []


def test_main_check_exit_codes(tmp_path):
    repo = make_repo(tmp_path)
    assert sync_agents.main(["sync", "--check", str(repo)]) == 1
    assert sync_agents.main(["sync", str(repo)]) == 0
    assert sync_agents.main(["sync", "--check", str(repo)]) == 0


def test_validate_main_exit_codes(tmp_path):
    assert validate_skills.main(["v", str(ROOT)]) == 0
    repo = make_repo(tmp_path)
    write_skill(repo, "bad-skill", "name: nope\ndescription: x")
    assert validate_skills.main(["v", str(repo)]) == 1


def test_codex_read_only_disables_shell_tool():
    read_only = tomllib.loads(sync_agents.render_codex("n", "d", "read-only", "b\n"))
    assert read_only["features"]["shell_tool"] is False
    for access in ("inspect", "write"):
        assert "features" not in tomllib.loads(sync_agents.render_codex("n", "d", access, "b\n"))


# --- hardening ---


def test_symlinks_in_skills_are_rejected(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".agents/skills/spec/leak.md").symlink_to("/etc/hosts")
    assert any("symlinks are not allowed" in e for e in validate_skills.validate_skills(repo))
    with pytest.raises(sync_agents.SyncError):
        sync_agents.sync(repo)


def test_sync_refuses_invalid_sources(tmp_path):
    repo = make_repo(tmp_path)
    (repo / ".agents/agents/evil.md").write_text(
        '---\nname: "../../escape"\ndescription: "d"\naccess: write\n---\nbody\n'
    )
    with pytest.raises(sync_agents.SyncError):
        sync_agents.sync(repo)
    assert not (tmp_path.parent / "escape.md").exists()
    assert sync_agents.main(["sync", "--check", str(repo)]) == 2


def test_inspect_permissions_use_exact_git_commands():
    rendered = sync_agents.render_opencode("n", "d", "inspect", "b\n")
    assert "*" not in rendered.replace('"*": ask', "")
    assert '"git diff": allow' in rendered
    assert "git diff*" not in rendered


# --- token budgets and routing eval ---

from scripts import route_eval, token_report  # noqa: E402


def test_repo_meets_routing_floor():
    result = route_eval.evaluate(ROOT, max_overlap=0.55)
    assert result["problems"] == []
    assert result["rank1"] / result["positives"] >= 0.95
    assert result["negatives_ok"] == result["negatives"]


def test_repo_stays_within_token_budgets():
    cat = token_report.measure("t", ROOT / ".agents/skills", ROOT / "AGENTS.md")
    assert cat.skills >= 30
    assert cat.always_on < 3000
    assert cat.body_avg < 450
    assert cat.body_max < 800


def test_stemmer_folds_silent_e():
    assert route_eval.stem("replace") == route_eval.stem("replacing")
    assert route_eval.tokenize("The tests are failing") == ["test", "fail"]


def test_route_eval_flags_unknown_and_uncovered_skills(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "evals").mkdir()
    cases = [
        {"skill": "ghost", "positive": ["x"], "negative": []},
        {"skill": "spec", "positive": ["write a spec with acceptance criteria"], "negative": []},
    ]
    import json

    (repo / "evals/routing.json").write_text(json.dumps(cases))
    problems = route_eval.evaluate(repo, 0.55)["problems"]
    assert any("unknown skill: ghost" in p for p in problems)
    assert any("no routing cases for skill: debugging" in p for p in problems)


def test_route_eval_main_exit_codes(tmp_path):
    assert route_eval.main(["r", "--min-rank1", "95", str(ROOT)]) == 0
    repo = make_repo(tmp_path)
    (repo / "evals").mkdir()
    (repo / "evals/routing.json").write_text("[]")
    assert route_eval.main(["r", str(repo)]) == 1


def test_token_report_compares_two_catalogs(capsys):
    assert token_report.main(["t", "--compare", str(ROOT / ".agents"), str(ROOT)]) == 0
    out = capsys.readouterr().out
    assert "this repo" in out and "Always-loaded tokens" in out


def test_validator_enforces_budgets(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "AGENTS.md").write_text("word " * 500)
    body = "# t\n" + "word " * 450
    write_skill(repo, "fat-skill", 'name: fat-skill\ndescription: "Use when x."', body)
    errs = validate_skills.validate_skills(repo)
    assert any("AGENTS.md exceeds" in e for e in errs)
    assert any("body is" in e and "max 400" in e for e in errs)


def test_validator_enforces_total_description_budget(tmp_path):
    repo = make_repo(tmp_path)
    desc = "Use when " + "y" * 250
    for i in range(30):
        write_skill(repo, f"extra-{i}", f'name: extra-{i}\ndescription: "{desc}"')
    assert any("descriptions total" in e for e in validate_skills.validate_skills(repo))
