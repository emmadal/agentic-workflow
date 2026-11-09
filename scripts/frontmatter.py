"""Strict parser for the flat YAML frontmatter used by skills and agents.

Supports `key: value` where value is a double-quoted JSON string or a plain scalar.
Plain scalars containing ': ' or ' #' are rejected because YAML parsers disagree on them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s+(.*))?$")


class FrontmatterError(ValueError):
    pass


@dataclass
class Document:
    meta: dict[str, str]
    body: str


def parse(text: str) -> Document:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("file must start with '---'")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise FrontmatterError("frontmatter is not closed with '---'") from exc

    meta: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = KEY_RE.match(raw)
        if not match:
            raise FrontmatterError(f"unsupported frontmatter line: {raw!r}")
        key, value = match.group(1), (match.group(2) or "").strip()
        if key in meta:
            raise FrontmatterError(f"duplicate key: {key}")
        meta[key] = _scalar(key, value)
    return Document(meta, "\n".join(lines[end + 1 :]).lstrip("\n"))


def _scalar(key: str, value: str) -> str:
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise FrontmatterError(f"{key}: invalid double-quoted string") from exc
        if not isinstance(parsed, str):
            raise FrontmatterError(f"{key}: expected a string")
        return parsed
    if value.startswith(("'", "|", ">", "[", "{")):
        raise FrontmatterError(f"{key}: use a double-quoted string")
    if ": " in value or " #" in value:
        raise FrontmatterError(
            f"{key}: plain value contains ': ' or ' #'; wrap it in double quotes"
        )
    return value


def quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
