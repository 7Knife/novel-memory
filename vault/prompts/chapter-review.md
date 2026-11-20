---
title: Prompt - 章末实体审查
type: Prompt
tags: [prompt, review]
permalink: prompt-chapter-review
---

# 章末实体审查

1. 列出本章实际出场/引用的实体。
2. 对每个实体判断是否需要 `new` / `update` / `status_progression`。
3. 每条建议附 `source_note`、`paragraph`、`quote`、`trigger`。
4. 输出符合 `schemas/review-suggestion.schema.json` 的 JSON。
5. 不直接修改笔记，只把建议放入待确认队列。
