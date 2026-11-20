# 实体级审查规则

## 原则

审查对象不是全局记忆，而是**当前场景中实际出场或被引用的实体**。审查产出不是结论，而是**建议 + 证据**，由用户确认。

核心转向：

> 从「这条记忆该不该记」转向「这个设定该新建、更新、过期，还是保持原状」。

## 触发时机

仅在写作边界触发：

1. `scene_end`：一个场景写完；
2. `chapter_final`：一章定稿；
3. `canon_change`：用户明确说“这个设定改了”“某某不再/现在是……”；
4. `manual`：用户主动要求审查。

不应触发：

- 每 N 个普通用户回合；
- 每轮自动审查；
- 对整本小说所有设定做全量扫描；
- 未在当前场景出场或引用的实体。

## 审查输入

最少输入：

```json
{
  "trigger": "scene_end",
  "source_note": "vault/notes/scenes/ch01-s03.md",
  "excerpt": "……正文片段……",
  "entities": ["林夏", "雨夜旧城区", "黑鸦会"]
}
```

推荐由场景卡的“出场实体/引用实体”提供实体范围。若没有场景卡，agent 必须先从当前正文中识别实体，再限制在这个集合内审查。

## 三类建议

### 1. 新建（`new`）

触发：正文出现地图/索引中不存在，但有长期价值的实体。

例子：

- 新地点：废弃的第七码头；
- 新组织：白塔监察院；
- 新体系：以记忆为货币的契约法；
- 重要物品：会自己改写主人名字的钥匙。

动作：

```markdown
---
title: 白塔监察院
type: Organization
entity_type: Organization
canon_status: draft
tags: [faction, draft]
permalink: bai-ta-jian-cha-yuan
---

# 白塔监察院

## 摘要
（一句摘要）

## 观察
- [goal] （目标）
- [rule] （规则）

## 自我认知（实体内）
（组织如何解释自身行为的自洽叙事）

## 关系
- controls [[白塔]]
```

不建议为随手提及、没有长期价值的名词创建实体。

### 2. 更新（`update`）

触发：现有实体字段发生变化。

例子：

- 势力领袖换了；
- 地点被摧毁；
- 体系规则被揭示新层面；
- 人物目标发生实质改变。

动作：

```markdown
## 观察
- [leader] 现任领袖：苏晴 (source: ch03-s05)
- [former_leader] 前任领袖：陈默 (superseded_at: ch03-s05, reason: 在雨夜政变中被罢免)
```

旧值不删除；标记为 `superseded`，保留变更理由和来源。

### 3. 状态推进（`status_progression`）

触发：

- draft/pending 的设定在正文中被反复使用；
- 用户明确确认其为正式事实；
- 用户说“这个设定改了”“现在正式算 canon”。

动作：

- `draft` → `canon`：确认正式事实；
- `pending` → `canon`：确认待审变更；
- `canon` → `obsolete`：设定作废，但笔记保留；
- `pending` → `obsolete`：拒绝/废弃候选设定。

## 证据要求

每条建议必须附：

```json
{
  "source_note": "vault/notes/scenes/ch03-s05.md",
  "paragraph": 7,
  "quote": "白塔的旗号从城门上降下，换成监察院的黑纹旗。",
  "trigger": "canon_change",
  "reason": "场景正文显示白塔监察院取代原守城队控制城门"
}
```

没有证据的建议不进入待确认队列。

## 重复建议

同一实体、同一类型、同一内容重复出现时：

- 不重复创建多条；
- 已有建议 `hits += 1`；
- 更新 `last_seen`；
- 合并证据列表，但保留去重后的最多 5 条。

hits 高的建议表示反复被正文触发，用户应优先处理。

## 用户确认

未确认的建议不得直接修改实体笔记。确认后：

- `new`：用 `bm_write` 创建实体笔记；
- `update`：用 `bm_edit` 追加/替换观察，旧值改为 superseded；
- `status_progression`：用 `bm_edit set_metadata` 更新 frontmatter。

## 全局禁用自我认知

审查结果不写入全局 system prompt。人物的自我认知只存在于人物实体笔记内；地点/组织/体系的自我认知只作为笔记段落存在，按需读取。
