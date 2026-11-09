"""CLI: python -m agent.cli "<goal>" --workdir . [--read-only]"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import anthropic

from .loop import Budget, run_agent
from .tools import READ_ONLY, REGISTRY


def main() -> int:
    parser = argparse.ArgumentParser(prog="agent")
    parser.add_argument("goal")
    parser.add_argument("--workdir", type=Path, default=Path("."))
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument(
        "--allow-write",
        action="store_true",
        help="enable write_file and run_tests (code execution; use in a sandbox)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    tools = tuple(REGISTRY) if args.allow_write else READ_ONLY
    result = run_agent(
        anthropic.Anthropic(),
        args.goal,
        args.workdir.resolve(),
        tools=tools,
        budget=Budget(max_steps=args.max_steps),
    )
    print(result.text or f"stopped: {result.stopped_by}")
    return 0 if result.stopped_by == "done" else 1


if __name__ == "__main__":
    raise SystemExit(main())
