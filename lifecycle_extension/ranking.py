"""Weight-aware re-ranking of Basic Memory search results.

This is the minimal 'sorting extension layer'. It never edits Basic Memory: the
caller fetches results with bm_search (which already supports filters on
frontmatter metadata), then passes them here for a second sort using the
lifecycle weight and canon_status. Archived/draft items are demoted, not hidden,
so nothing is lost.
"""

from __future__ import annotations

from typing import Any, Iterable

from .fields import (
    CANON_ARCHIVED,
    CANON_DRAFT,
    CANON_PENDING,
    FIELD_CANON_STATUS,
    FIELD_WEIGHT,
    MAX_WEIGHT,
    FALLBACK_WEIGHT,
)


def normalized_weight(meta: dict[str, Any]) -> float:
    try:
        w = float(meta.get(FIELD_WEIGHT, FALLBACK_WEIGHT))
    except (TypeError, ValueError):
        w = FALLBACK_WEIGHT
    return max(0.0, min(w / MAX_WEIGHT, 1.0))


def status_multiplier(meta: dict[str, Any]) -> float:
    status = str(meta.get(FIELD_CANON_STATUS, "")).strip()
    if status == CANON_ARCHIVED:
        return 0.2
    if status == CANON_DRAFT:
        return 0.6
    if status == CANON_PENDING:
        return 0.8
    return 1.0  # canon, obsolete-explicit, or unmarked: unchanged


def rerank(results: Iterable[dict[str, Any]], use_weight: bool = True) -> list[dict[str, Any]]:
    """Return results re-sorted by relevance * weight * status multiplier.

    Each result is expected to have a ``score``/``relevance`` key and either
    ``metadata``/``entity_metadata``/``frontmatter`` carrying lifecycle fields.
    The original score is preserved under ``_base_score``; a computed
    ``_lifecycle_score`` is added. Results lacking metadata pass through with
    multiplier 1.0, so removal of this layer restores native BM ordering.
    """
    items = list(results)
    for item in items:
        meta = {}
        for key in ("metadata", "entity_metadata", "frontmatter"):
            candidate = item.get(key)
            if isinstance(candidate, dict):
                meta.update(candidate)
        base = item.get("score", item.get("relevance", 0.0))
        try:
            base = float(base)
        except (TypeError, ValueError):
            base = 0.0
        item["_base_score"] = base
        factor = normalized_weight(meta) * status_multiplier(meta) if use_weight else 1.0
        item["_lifecycle_score"] = base * factor

    return sorted(items, key=lambda r: r["_lifecycle_score"], reverse=True)
