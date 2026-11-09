"""Minimal agent loop: plan, act, observe, repeat, with hard budgets."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .tools import REGISTRY, ToolError

log = logging.getLogger("agent")

DEFAULT_MODEL = "claude-sonnet-5-5"
DEFAULT_SYSTEM = (
    "You are a careful software engineer. Use tools, verify with tests, stop when done."
)


@dataclass
class Budget:
    max_steps: int = 20
    max_output_tokens: int = 200_000


@dataclass
class Result:
    text: str
    steps: int
    stopped_by: str  # "done" | "max_steps" | "max_tokens"
    messages: list[dict[str, Any]] = field(default_factory=list)


def run_agent(
    client: Any,
    goal: str,
    workdir: Path,
    system: str = DEFAULT_SYSTEM,
    tools: tuple[str, ...] = tuple(REGISTRY),
    budget: Budget | None = None,
    model: str = DEFAULT_MODEL,
) -> Result:
    budget = budget or Budget()
    schemas = [REGISTRY[name][1] for name in tools]
    messages: list[dict[str, Any]] = [{"role": "user", "content": goal}]
    used_tokens = 0

    for step in range(1, budget.max_steps + 1):
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            tools=schemas,
            messages=messages,
        )
        used_tokens += resp.usage.output_tokens
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return Result(text, step, "done", messages)

        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            log.info("step=%d tool=%s input=%s", step, block.name, block.input)
            results.append(_run_tool(block, workdir, tools))
        messages.append({"role": "user", "content": results})

        if used_tokens >= budget.max_output_tokens:
            return Result("", step, "max_tokens", messages)

    return Result("", budget.max_steps, "max_steps", messages)


def _run_tool(block: Any, workdir: Path, allowed: tuple[str, ...]) -> dict[str, Any]:
    if block.name not in allowed:
        return _tool_result(block.id, f"tool not allowed: {block.name}", error=True)
    fn = REGISTRY[block.name][0]
    try:
        return _tool_result(block.id, fn(workdir, **block.input))
    except (ToolError, OSError, TypeError) as exc:
        return _tool_result(block.id, f"error: {exc}", error=True)


def _tool_result(tool_use_id: str, content: str, error: bool = False) -> dict[str, Any]:
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "is_error": error,
    }
