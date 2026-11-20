"""Optional standalone MCP server exposing review/confirm tools.

This is a THIN wrapper over review_queue, meant to be mounted as a separate MCP
server. It does not import Basic Memory and does not register tools into BM.
The actual write-back is delegated to Basic Memory's public tools by the agent
after apply_review approves a proposal.
"""

from __future__ import annotations

import os
from pathlib import Path

from .review_queue import ReviewQueue

DEFAULT_QUEUE = Path(
    os.environ.get(
        "NOVEL_MEMORY_REVIEW_QUEUE",
        str(Path.home() / ".basic-memory" / "novel-review-queue.json"),
    )
)

_queue = ReviewQueue(DEFAULT_QUEUE)


def review_memory(scope: str = "all", since: str | None = None, action: str = "list") -> dict:
    """List or scan pending review proposals. No writes to notes."""
    rows = _queue.list_pending()
    if scope != "all":
        rows = [r for r in rows if scope in r.entity_permalink]
    return {"action": action, "scope": scope, "since": since, "pending": [r.__dict__ for r in rows]}


def propose_memory(proposals: list[dict]) -> dict:
    """Queue change proposals (new/update/status_progression/archive). No note writes."""
    added = _queue.propose(proposals)
    return {"queued": len(added), "ids": [p.id for p in added]}


def apply_review(proposal_id: str, approve: bool = True) -> dict:
    """Approve/reject a proposal. Approval returns the proposal for the agent to apply via BM tools."""
    updated = _queue.decide(proposal_id, approve)
    if updated is None:
        return {"ok": False, "message": "proposal not found"}
    return {"ok": True, "proposal": updated.__dict__,
            "next": "call Basic Memory bm_write/bm_edit to apply, then mark applied"}


def review_status() -> dict:
    """Quick health/status of the review queue."""
    return {"queue_path": str(DEFAULT_QUEUE), "pending_count": len(_queue.list_pending())}
