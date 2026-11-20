"""Review queue and confirmation tools -- external 'confirmation buffer' layer.

Stores proposals in a single JSON file (not JSONL, not a new DB). The agent side
(review_memory/propose) only writes proposals; the user side (apply_review)
applies them via a caller-provided apply callback -- which should be Basic
Memory's public write/edit API. Nothing here imports or modifies Basic Memory.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .fields import CANON_DRAFT


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Proposal:
    id: str
    entity_permalink: str
    operation: str  # new | update | status_progression | archive
    payload: dict[str, Any]
    reason: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    status: str = "pending"  # pending | approved | rejected | applied
    created_at: str = field(default_factory=_now)
    decided_at: str | None = None
    hits: int = 1


class ReviewQueue:
    def __init__(self, path: Path):
        self.path = path

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, rows: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def propose(self, proposals: list[dict[str, Any]]) -> list[Proposal]:
        rows = self._load()
        existing = {row.get("id") for row in rows}
        added: list[Proposal] = []
        for item in proposals:
            if not item.get("entity_permalink") or not item.get("operation"):
                continue
            # Dedup: same entity + operation + payload while pending.
            duplicate = next(
                (
                    row for row in rows
                    if row.get("status") == "pending"
                    and row.get("entity_permalink") == item.get("entity_permalink")
                    and row.get("operation") == item.get("operation")
                    and row.get("payload") == item.get("payload")
                ),
                None,
            )
            if duplicate is not None:
                duplicate["hits"] = int(duplicate.get("hits", 1)) + 1
                continue
            pid = str(uuid.uuid4()) if item.get("id") in (None, "") or item.get("id") in existing else str(item["id"])
            proposal = Proposal(
                id=pid,
                entity_permalink=str(item["entity_permalink"]),
                operation=str(item["operation"]),
                payload=dict(item.get("payload") or {}),
                reason=str(item.get("reason") or ""),
                evidence=list(item.get("evidence") or []),
                status=CANON_DRAFT if item.get("status") == CANON_DRAFT else "pending",
            )
            rows.append(asdict(proposal))
            added.append(proposal)
        self._save(rows)
        return added

    def list_pending(self) -> list[Proposal]:
        return [Proposal(**row) for row in self._load() if row.get("status") in ("pending", CANON_DRAFT)]

    def decide(self, proposal_id: str, approve: bool) -> Proposal | None:
        rows = self._load()
        for row in rows:
            if row.get("id") == proposal_id:
                row["status"] = "approved" if approve else "rejected"
                row["decided_at"] = _now()
                self._save(rows)
                return Proposal(**row)
        return None

    def apply(
        self,
        proposal_id: str,
        apply_callback: Callable[[Proposal], Any],
    ) -> Any:
        """Apply ONE approved proposal through a caller-provided callback.

        The callback should call Basic Memory's public write/edit API. If the
        proposal is not approved, nothing is applied.
        """
        rows = self._load()
        target = next((row for row in rows if row.get("id") == proposal_id), None)
        if target is None:
            return {"ok": False, "message": "proposal not found"}
        if target.get("status") != "approved":
            return {"ok": False, "message": "proposal is not approved"}
        proposal = Proposal(**target)
        result = apply_callback(proposal)
        target["status"] = "applied"
        target["decided_at"] = _now()
        self._save(rows)
        return {"ok": True, "result": result}
