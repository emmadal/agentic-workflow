import subprocess
import sys
from types import SimpleNamespace as NS

import pytest

from agent import cli, tools
from agent.tools import ToolError


def test_list_dir_hides_blocked_entries(tmp_path):
    (tmp_path / ".env").write_text("SECRET=1")
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "a.py").write_text("")
    assert tools.list_dir(tmp_path).split("\n") == ["a.py", "src/"]


def test_list_dir_rejects_file(tmp_path):
    (tmp_path / "a.py").write_text("")
    with pytest.raises(ToolError):
        tools.list_dir(tmp_path, "a.py")


def test_read_rejects_directory(tmp_path):
    with pytest.raises(ToolError):
        tools.read_file(tmp_path, ".")


def test_write_file_creates_parents(tmp_path):
    tools.write_file(tmp_path, "pkg/mod.py", "x = 1")
    assert (tmp_path / "pkg/mod.py").read_text() == "x = 1"


def test_write_blocks_sensitive_path(tmp_path):
    with pytest.raises(ToolError):
        tools.write_file(tmp_path, "conftest.py", "import os")
    assert not (tmp_path / "conftest.py").exists()


def test_run_tests_uses_scrubbed_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    seen = {}

    def fake_run(cmd, **kw):
        seen.update(kw)
        return NS(stdout="1 passed", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert tools.run_tests(tmp_path) == "1 passed"
    assert "ANTHROPIC_API_KEY" not in seen["env"]
    assert seen["timeout"] == 300


def _run_cli(monkeypatch, argv, stopped_by="done"):
    captured = {}

    def fake_run_agent(client, goal, workdir, tools, budget):
        captured.update(goal=goal, tools=tools, budget=budget)
        return NS(text="answer" if stopped_by == "done" else "", stopped_by=stopped_by)

    monkeypatch.setattr(cli, "run_agent", fake_run_agent)
    monkeypatch.setattr(cli.anthropic, "Anthropic", lambda: object())
    monkeypatch.setattr(sys, "argv", ["agent", *argv])
    return cli.main(), captured


def test_cli_is_read_only_by_default(monkeypatch):
    code, seen = _run_cli(monkeypatch, ["do it"])
    assert code == 0
    assert seen["tools"] == tools.READ_ONLY


def test_cli_allow_write_enables_all_tools(monkeypatch):
    _, seen = _run_cli(monkeypatch, ["do it", "--allow-write", "--max-steps", "5"])
    assert set(seen["tools"]) == set(tools.REGISTRY)
    assert seen["budget"].max_steps == 5


def test_cli_nonzero_when_budget_exhausted(monkeypatch):
    code, _ = _run_cli(monkeypatch, ["do it"], stopped_by="max_steps")
    assert code == 1
