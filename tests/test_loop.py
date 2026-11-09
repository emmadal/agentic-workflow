from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from agent import Budget, run_agent
from agent.tools import ToolError, read_file


def text(t):
    return NS(type="text", text=t)


def tool_use(id_, name, **inp):
    return NS(type="tool_use", id=id_, name=name, input=inp)


class FakeClient:
    def __init__(self, responses):
        self._responses = iter(responses)
        self.messages = self

    def create(self, **_):
        return next(self._responses)


def resp(content, stop):
    return NS(content=content, stop_reason=stop, usage=NS(output_tokens=10))


def test_finishes_without_tools(tmp_path):
    client = FakeClient([resp([text("done")], "end_turn")])
    result = run_agent(client, "hi", tmp_path)
    assert result.stopped_by == "done"
    assert result.text == "done"


def test_tool_call_then_done(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    client = FakeClient(
        [
            resp([tool_use("1", "read_file", path="a.txt")], "tool_use"),
            resp([text("ok")], "end_turn"),
        ]
    )
    result = run_agent(client, "read a.txt", tmp_path)
    assert result.steps == 2
    tool_result = result.messages[2]["content"][0]
    assert tool_result["content"] == "hello"
    assert not tool_result["is_error"]


def test_max_steps_stops_loop(tmp_path):
    loop = [resp([tool_use(str(i), "list_dir")], "tool_use") for i in range(5)]
    result = run_agent(FakeClient(loop), "x", tmp_path, budget=Budget(max_steps=3))
    assert result.stopped_by == "max_steps"


def test_disallowed_tool_is_rejected(tmp_path):
    client = FakeClient(
        [
            resp([tool_use("1", "write_file", path="x", content="y")], "tool_use"),
            resp([text("ok")], "end_turn"),
        ]
    )
    result = run_agent(client, "x", tmp_path, tools=("read_file",))
    assert result.messages[2]["content"][0]["is_error"]
    assert not (tmp_path / "x").exists()


def test_path_escape_blocked(tmp_path):
    with pytest.raises(ToolError):
        read_file(Path(tmp_path), "../../etc/passwd")
