"""Minimal frontmatter reader/writer for lifecycle fields.

Only touches the YAML block at the top of a Markdown file, preserves the body
byte-for-byte, and writes atomically. This is deliberately independent of Basic
Memory's parser/markdown_processor so it can be removed without touching core.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FM_DELIM = "---"

_SCALAR_RE = re.compile(r"^([^:\n]+):\s*(.*)$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (metadata, body). If no valid frontmatter, return ({}, text)."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FM_DELIM:
        return {}, text
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == FM_DELIM:
            end = i
            break
    if end is None:
        return {}, text
    meta: dict[str, Any] = {}
    for raw in lines[1:end]:
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _SCALAR_RE.match(line.strip())
        if not m:
            continue
        key, value = m.group(1).strip(), m.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            value = value.strip("'\"")
        meta[key] = value
    body = "".join(lines[end + 1:])
    return meta, body


def _format_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(str(v) for v in value) + "]"
    return str(value)


def write_frontmatter(path: Path, updates: dict[str, Any]) -> dict[str, Any]:
    """Merge updates into a note's frontmatter and write atomically.

    Returns the resulting metadata. Body (including all sections and WikiLinks)
    is preserved exactly.
    """
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)

    # Preserve the original key order for stable diffs.
    merged: dict[str, Any] = dict(meta)
    for key, value in updates.items():
        merged[key] = value

    header_lines = [FM_DELIM]
    for key, value in merged.items():
        header_lines.append(f"{key}: {_format_value(value)}")
    header_lines.append(FM_DELIM)

    new_text = "\n".join(header_lines) + "\n" + body
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(path)
    return merged
