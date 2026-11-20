---
title: Skill - Canon 检查
type: Skill
tags: [skill, canon]
permalink: skill-canon-check
---

# Canon 检查 Skill

## 何时用
不确定某个设定是否正式生效，或需要判断 draft/pending/canon/obsolete 状态时。

## 步骤
1. 用 `bm_search` 搜索 `canon:<实体名>`。
2. 用 `bm_read` 读取实体 frontmatter 的 `canon_status`。
3. 若状态为 draft/pending，不要当作正式事实写正文，除非用户明确要求使用草案。
4. 若状态为 obsolete，检查 `superseded` 字段与新设定。
5. 状态推进必须经过用户确认。
