from __future__ import annotations

import shutil
import unittest
from datetime import datetime, timezone
from pathlib import Path

from lifecycle_extension import decay, ranking
from lifecycle_extension.fields import (
    ARCHIVE_THRESHOLD,
    CANON_ARCHIVED,
    CANON_CANON,
    FIELD_ARCHIVED_AT,
    FIELD_CANON_STATUS,
    FIELD_LAST_HIT,
    FIELD_WEIGHT,
)
from lifecycle_extension.frontmatter_io import split_frontmatter, write_frontmatter
from lifecycle_extension.review_queue import ReviewQueue

# Sandbox forbids tempfile's chmod; use a plain workspace-local scratch dir.
_SCRATCH = Path(__file__).resolve().parents[2] / ".test-tmp"


def fresh_dir(name: str) -> Path:
    p = _SCRATCH / name
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
    p.mkdir(parents=True, exist_ok=True)
    return p


NOTE = """---
title: 林砚
type: Entity
entity_type: Person
weight: 1.2
base_weight: 2.5
canon_status: canon
last_hit: 2026-01-01T00:00:00Z
---

# 林砚

## 自述
我承认我嫉妒沈知微。

## 观察
- [identity] 林砚是长女
"""


class FrontmatterIOTest(unittest.TestCase):
    def test_update_preserves_body(self):
        p = fresh_dir("fm") / "lin.md"
        p.write_text(NOTE, encoding="utf-8")
        write_frontmatter(p, {FIELD_WEIGHT: "2.000"})
        meta, body = split_frontmatter(p.read_text(encoding="utf-8"))
        self.assertEqual(meta[FIELD_WEIGHT], "2.000")
        self.assertIn("## 自述", body)
        self.assertIn("我承认我嫉妒沈知微。", body)


class DecayTest(unittest.TestCase):
    def test_decay_after_interval_and_archive(self):
        p = fresh_dir("decay_archive") / "lin.md"
        p.write_text(NOTE, encoding="utf-8")
        now = datetime(2026, 1, 20, tzinfo=timezone.utc)  # 19 days -> 6 steps -> 1.2-0.6=0.6
        result = decay.decay_note(p, now=now)
        self.assertIsNotNone(result)
        meta, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        self.assertLess(float(meta[FIELD_WEIGHT]), ARCHIVE_THRESHOLD)
        self.assertEqual(meta[FIELD_CANON_STATUS], CANON_ARCHIVED)
        self.assertIn(FIELD_ARCHIVED_AT, meta)

    def test_no_decay_before_interval(self):
        p = fresh_dir("decay_noop") / "lin.md"
        p.write_text(NOTE, encoding="utf-8")
        now = datetime(2026, 1, 2, tzinfo=timezone.utc)  # 1 day
        self.assertIsNone(decay.decay_note(p, now=now))

    def test_no_double_decay_on_rerun(self):
        """Regression: a second run on the same day must not decay again."""
        p = fresh_dir("decay_rerun") / "lin.md"
        # High weight so a 6-step decay stays above the archive threshold.
        high = NOTE.replace("weight: 1.2", "weight: 3.0").replace("base_weight: 2.5", "base_weight: 3.0")
        p.write_text(high, encoding="utf-8")
        t0 = datetime(2026, 1, 20, tzinfo=timezone.utc)
        first = decay.decay_note(p, now=t0)
        self.assertIsNotNone(first)
        self.assertFalse(first.archived)
        second = decay.decay_note(p, now=t0)
        self.assertIsNone(second)
        meta, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        self.assertAlmostEqual(float(meta[FIELD_WEIGHT]), first.new_weight)
        # A run 3 days later decays exactly one more interval.
        third = decay.decay_note(p, now=datetime(2026, 1, 23, tzinfo=timezone.utc))
        self.assertIsNotNone(third)
        self.assertAlmostEqual(third.old_weight, first.new_weight)


class RankingTest(unittest.TestCase):
    def test_weight_and_status_rerank(self):
        results = [
            {"title": "archived", "score": 0.9, "metadata": {FIELD_WEIGHT: "3", FIELD_CANON_STATUS: CANON_ARCHIVED}},
            {"title": "canon-heavy", "score": 0.7, "entity_metadata": {FIELD_WEIGHT: "3", FIELD_CANON_STATUS: CANON_CANON}},
            {"title": "draft", "score": 0.95, "frontmatter": {FIELD_WEIGHT: "1.3", FIELD_CANON_STATUS: "draft"}},
        ]
        ordered = ranking.rerank(results)
        self.assertEqual(ordered[0]["title"], "canon-heavy")
        self.assertEqual(ordered[-1]["title"], "archived")
        self.assertIn("_lifecycle_score", ordered[0])


class ReviewQueueTest(unittest.TestCase):
    def test_propose_decide_apply(self):
        q = ReviewQueue(fresh_dir("queue") / "queue.json")
        added = q.propose([{
            "entity_permalink": "memory://lin-yan",
            "operation": "update",
            "payload": {"field": "attitude", "value": "changed"},
            "reason": "scene 3",
        }])
        self.assertEqual(len(added), 1)
        pid = added[0].id

        again = q.propose([{
            "entity_permalink": "memory://lin-yan",
            "operation": "update",
            "payload": {"field": "attitude", "value": "changed"},
            "reason": "scene 3",
        }])
        self.assertEqual(len(again), 0)
        self.assertEqual(len(q.list_pending()), 1)

        def forbidden(_proposal):
            raise AssertionError("should not apply before approval")

        self.assertFalse(q.apply(pid, forbidden)["ok"])
        q.decide(pid, True)
        applied = q.apply(pid, lambda p: f"applied:{p.entity_permalink}")
        self.assertTrue(applied["ok"])
        self.assertEqual(len(q.list_pending()), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
