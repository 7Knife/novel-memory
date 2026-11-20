---
title: Skill - 实体审查
type: Skill
tags: [skill, review]
permalink: skill-entity-review
---

# 实体审查 Skill

## 何时用
场景写完、章定稿、用户说设定改了、用户主动要求。

## 范围
只审查当前场景实际出场或引用的实体。不要全局扫描。

## 步骤
1. 从场景卡或正文提取实体集合。
2. 对每个实体用 `bm_search` / `bm_read` 查现有笔记。
3. 根据正文证据生成建议：
   - `new`：长期价值实体不存在 → 创建 draft 建议；
   - `update`：字段变化 → 完整替换值 + superseded 旧值；
   - `status_progression`：draft/pending → canon，或 canon → obsolete。
4. 每条建议必须附段落与原文引用。
5. 重复建议累计 hits，不重复建条目。
6. 用户确认后才写入 Basic Memory。
