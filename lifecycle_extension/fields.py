"""Lifecycle frontmatter fields and default weights.

External extension for Basic Memory. Does not modify Basic Memory source.
Basic Memory already stores arbitrary frontmatter keys in ``entity_metadata``
(markdown/utils.py:74-75, entity_parser.py:349), so these fields need no
parser change.
"""

from __future__ import annotations

# --- Frontmatter keys (kept in one place so every module agrees on names) ---
FIELD_WEIGHT = "weight"
FIELD_CANON_STATUS = "canon_status"
FIELD_LAST_HIT = "last_hit"
FIELD_LAST_DECAY = "last_decay_at"
FIELD_BASE_WEIGHT = "base_weight"
FIELD_ARCHIVED_AT = "archived_at"
FIELD_SUPERSEDED = "superseded"

CANON_DRAFT = "draft"
CANON_PENDING = "pending"
CANON_CANON = "canon"
CANON_ARCHIVED = "archived"
CANON_OBSOLETE = "obsolete"
CANON_STATUSES = (
    CANON_DRAFT, CANON_PENDING, CANON_CANON, CANON_ARCHIVED, CANON_OBSOLETE
)

# --- Decay constants (aligned with dsh-self-memory weight rules) ---
DECAY_PER_DAY = 0.1
DECAY_INTERVAL_DAYS = 3
HIT_BONUS = 0.5
HIT_CAP_FACTOR = 1.5
ARCHIVE_THRESHOLD = 1.0
MAX_WEIGHT = 3.0

# Default weight by observation/category, from dsh-self-memory:
# identity/agreement/emotion 3.0, preference 2.5, meme 1.6, misc 1.3
DEFAULT_WEIGHTS: dict[str, float] = {
    "identity": 3.0,
    "agreement": 3.0,
    "emotion": 3.0,
    "preference": 2.5,
    "meme": 1.6,
    "misc": 1.3,
    # Novel-writing categories map onto the same scale.
    "decision": 3.0,
    "canon": 3.0,
    "character": 3.0,
    "relationship": 2.5,
    "location": 1.6,
    "observation": 1.3,
}
FALLBACK_WEIGHT = DEFAULT_WEIGHTS["misc"]


def default_weight(category: str | None) -> float:
    """Return the starting weight for a category."""
    if not category:
        return FALLBACK_WEIGHT
    return DEFAULT_WEIGHTS.get(str(category).strip().lower(), FALLBACK_WEIGHT)


def clamp(value: float, low: float = 0.0, high: float = MAX_WEIGHT) -> float:
    return max(low, min(high, value))
