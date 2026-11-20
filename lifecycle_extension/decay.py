"""decay.py -- external, batch lifecycle pass over Basic Memory Markdown notes.

Run manually or from a daily/weekly DSH scheduled task. It does NOT run as a
daemon and does NOT import Basic Memory. It only edits frontmatter keys that
this extension owns, and writes files atomically.

Basic Memory's file watcher / next index pass converges the SQLite index; we do
not touch SQLite directly, preserving the canonical-Markdown model.

Settlement rule: elapsed days are measured from max(last_hit, last_decay_at).
After a decay, last_decay_at is advanced to ``now`` so repeated runs on the same
day cannot compound the weight loss. ``last_hit`` is never modified here.

Usage:
    python -m lifecycle_extension.decay --root <vault/notes> [--dry-run] [--force]
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .fields import (
    ARCHIVE_THRESHOLD,
    CANON_ARCHIVED,
    CANON_STATUSES,
    DECAY_INTERVAL_DAYS,
    DECAY_PER_DAY,
    FIELD_ARCHIVED_AT,
    FIELD_BASE_WEIGHT,
    FIELD_CANON_STATUS,
    FIELD_LAST_DECAY,
    FIELD_LAST_HIT,
    FIELD_WEIGHT,
    FALLBACK_WEIGHT,
    clamp,
)
from .frontmatter_io import split_frontmatter, write_frontmatter


@dataclass
class DecayResult:
    path: Path
    old_weight: float
    new_weight: float
    archived: bool


def _parse_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_dt(value: object) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _isodate(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def _settlement_start(meta: dict[str, Any]) -> datetime | None:
    """Later of last_hit and last_decay_at -- the point decay was last credited."""
    candidates = [
        dt for dt in (_parse_dt(meta.get(FIELD_LAST_HIT)), _parse_dt(meta.get(FIELD_LAST_DECAY)))
        if dt is not None
    ]
    return max(candidates) if candidates else None


def _compute(meta: dict[str, Any], now: datetime, force: bool) -> tuple[float, float, bool] | None:
    """Return (old_weight, new_weight, archived) or None when no decay is due."""
    weight = _parse_float(meta.get(FIELD_WEIGHT), FALLBACK_WEIGHT)
    start = _settlement_start(meta)
    if start is None:
        days = float(DECAY_INTERVAL_DAYS)
    else:
        days = max(0.0, (now - start).total_seconds() / 86400.0)

    if force:
        loss = DECAY_PER_DAY
    else:
        steps = int(days // DECAY_INTERVAL_DAYS)
        if steps < 1:
            return None
        loss = DECAY_PER_DAY * DECAY_INTERVAL_DAYS * steps

    new_weight = clamp(weight - loss)
    return weight, new_weight, new_weight < ARCHIVE_THRESHOLD


def decay_note(path: Path, now: datetime | None = None, force: bool = False) -> DecayResult | None:
    """Apply one decay step to a single note. Returns None when unchanged."""
    now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    if not meta:
        return None

    status = str(meta.get(FIELD_CANON_STATUS, "")).strip()
    if status and status not in CANON_STATUSES:
        return None
    if status == CANON_ARCHIVED:
        return None

    computed = _compute(meta, now, force)
    if computed is None:
        return None
    old_weight, new_weight, archived = computed

    updates: dict[str, object] = {
        FIELD_WEIGHT: f"{new_weight:.3f}",
        FIELD_LAST_DECAY: _isodate(now),
    }
    if archived:
        updates[FIELD_CANON_STATUS] = CANON_ARCHIVED
        updates[FIELD_ARCHIVED_AT] = _isodate(now)
    if not meta.get(FIELD_BASE_WEIGHT):
        updates[FIELD_BASE_WEIGHT] = f"{_parse_float(meta.get(FIELD_WEIGHT), old_weight):.3f}"
    write_frontmatter(path, updates)
    return DecayResult(path, old_weight, new_weight, archived)


def run(root: Path, dry_run: bool = False, force: bool = False, now: datetime | None = None) -> list[DecayResult]:
    now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    results: list[DecayResult] = []
    for path in sorted(root.rglob("*.md")):
        meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        # Only touch notes that opt into lifecycle management.
        if FIELD_WEIGHT not in meta and FIELD_LAST_HIT not in meta:
            continue
        status = str(meta.get(FIELD_CANON_STATUS, "")).strip()
        if status and status not in CANON_STATUSES:
            continue
        if status == CANON_ARCHIVED:
            continue

        computed = _compute(meta, now, force)
        if computed is None:
            continue
        old_weight, new_weight, archived = computed

        if not dry_run:
            updates: dict[str, object] = {
                FIELD_WEIGHT: f"{new_weight:.3f}",
                FIELD_LAST_DECAY: _isodate(now),
            }
            if archived:
                updates[FIELD_CANON_STATUS] = CANON_ARCHIVED
                updates[FIELD_ARCHIVED_AT] = _isodate(now)
            if not meta.get(FIELD_BASE_WEIGHT):
                updates[FIELD_BASE_WEIGHT] = f"{_parse_float(meta.get(FIELD_WEIGHT), old_weight):.3f}"
            write_frontmatter(path, updates)

        results.append(DecayResult(path, old_weight, new_weight, archived))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Decay lifecycle weights in Basic Memory notes")
    parser.add_argument("--root", required=True, type=Path, help="vault notes root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="apply one step even if interval not elapsed")
    args = parser.parse_args()
    results = run(args.root, dry_run=args.dry_run, force=args.force)
    for r in results:
        action = "ARCHIVE" if r.archived else "decay"
        print(f"{action}: {r.path} {r.old_weight:.2f} -> {r.new_weight:.2f}")
    print(f"Processed {len(results)} note(s)")


if __name__ == "__main__":
    main()
