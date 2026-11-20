# 三仓库合并映射

## Basic Memory（主）

| 内容 | 处理 |
|---|---|
| Markdown note / observation / relation / frontmatter | 保留为事实源与实体表达 |
| `bm_read` / `bm_write` / `bm_edit` / `bm_search` / `bm_context` | 保留为读写/检索工具 |
| Basic Memory Cloud | 保留为云端记忆库 |
| Skills/plugins 机制 | 保留；本项目新增 DSH plugin 与 vault skills |
| 核心 Python 代码 | 不改、不复制 |

## dsh-self-memory（方法来源，去重）

| 原内容 | 处理 |
|---|---|
| L0 原文库 events JSONL | 删除；使用 Basic Memory 场景/章节笔记 |
| L2 事实库 facts.jsonl + 权重衰减 | 删除；使用 Basic Memory 实体笔记/搜索 |
| L3 中文 bigram 检索 | 删除；使用 bm_search / Basic Memory semantic/hybrid search |
| L4 全局 selfNote | 删除全局层；下放到实体笔记内 |
| `self_memory_recall` | 保留方法：不知道就检索；工具由 bm_search/bm_read 承担 |
| `self_memory_review` 全局审查 | 替换为实体级审查，仅写作边界触发 |
| systemPrompt.section 注入全局记忆 | 只保留“极简路由提示词”，不注入全局事实/自我认知 |
| 加密同步 / GitHub vault | 删除；Basic Memory Cloud 负责 |
| 设备网 / 远程派活 | 删除，与小说创作无关 |
| 会话同步 | 删除；如需可由用户自行选用，不进入本项目 |
| 插件注册/工具定义形态 | 参考，用于 novel-memory DSH plugin |

## dsh-memory-evolve（仅参考思路）

| 原内容 | 处理 |
|---|---|
| 实体级自我审查思路 | 借鉴并改写为“设定该不该新建/更新/过期” |
| 建议 → 用户确认队列 | 借鉴；实现为 `vault/reviews/pending` + 插件命令 |
| 重复建议 hits 累计 | 借鉴 |
| 每条建议附 reason | 强化为 paragraph + quote 证据 |
| 触发节奏 `agent/turn-stopping` 每 N 回合 | 不采用；改为写作边界事件 |
| advisor 独立模型评审 | 不采用；避免复杂模型路由与额外 token |
| WebUI / 待办 / COI / 外部 CLI / 会话广播 | 不采用 |
| 全局记忆审查/自我进化 | 不采用；与“全局不使用自我认知”冲突 |
