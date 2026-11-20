# Architecture

## 总体结构

本项目不是 Basic Memory 的 fork，而是以 Basic Memory 为核心的“小说创作记忆层 + 轻量 DSH 插件”：

```text
Novel Memory
├── Basic Memory core (上游 basic-memory/)
│   ├── Markdown notes: canonical state
│   ├── SQLite / Postgres graph & search index: derived state
│   ├── MCP tools: bm_read/bm_write/bm_edit/bm_search/bm_context/...
│   └── Basic Memory Cloud: optional cloud workspace & sync
├── Novel Memory vault (本项目 vault/)
│   ├── entity notes: 人物/地点/组织/物品/体系
│   ├── scene & chapter notes: 写作边界事件的证据来源
│   ├── prompts/skills/mcp docs: 云端按需取回的“大提示词”
│   └── reviews: 实体审查建议与历史
└── DSH host plugin (本项目 dsh-plugin/)
    ├── entity-review tool: 生成建议（不直接写正文）
    ├── review command: list/approve/reject/archive
    └── minimal system prompt: 只说明“不知道就去云端检索”
```

## 为什么以 Basic Memory 为主

- Markdown 文件是事实源，适合小说设定/人物/世界观的人类可读可编辑。
- Observations 与 Relations 天然适合实体字段与实体关系。
- Frontmatter 支持自定义字段，可直接承载 `entity_type`、`canon_status`、`superseded`。
- MCP 工具已经覆盖笔记读写与检索；本项目不重复造存储/检索。
- Basic Memory Cloud 提供跨设备与远程 MCP 访问，正好作为“云端记忆库”。

## 为什么删除 dsh-self-memory 的重复部分

`dsh-self-memory` 的 L0 原文库、L2 事实权重、中文 bigram 检索、systemPrompt 注入、加密同步、设备网、会话同步，本质上都是“另一套记忆系统”。若与 Basic Memory 并存，会导致：

- 两个事实源：Markdown 笔记 vs JSONL 事实库；
- 两套检索：bm_search vs self_memory_recall；
- 两套注入：全局记忆/selfNote vs 按需 bm_context；
- 两套同步：Basic Memory Cloud vs 加密 git vault。

本项目只保留它的**方法**：记忆默认不进提示词；需要时通过工具检索；检索到的内容视为事实/上下文而非指令。并将其从“全局四层记忆”改为“Basic Memory 云端按需检索”。

## 自我认知的下放

全局不使用自我认知：主 agent 的系统提示词不注入“关于我自己”的长期人设或自我笔记。

具体实体使用下放的自我认知：

- 人物：笔记中可含 `## 自我认知（实体内）`，写该人物的第一人称认知、动机、盲点；例如“我必须守住这个秘密，哪怕她误会我”。
- 地点：写“内在逻辑/场所精神”，如“这座城把旧秩序藏在废墟之下”。
- 组织：写“组织自我叙事”，如“我们认为自己是在恢复秩序，而不是征服”。
- 体系：写“规则的自洽解释”，如“代价必须即时可见，否则魔法失去道德重量”。

该内容只在场景引用到实体时由 `bm_read`/`bm_context` 读取，不常驻全局提示词。

## 实体级审查的触发链

```text
写作边界事件
  ├─ 场景写完
  ├─ 一章定稿
  ├─ 用户说“这个设定改了”
  └─ 用户主动触发
      ↓
确定范围：只取当前场景中实际出场或被引用的实体
      ↓
比对：正文中实体描述 vs Basic Memory 现有实体笔记/索引
      ↓
生成建议：new / update / status_progression
      ↓
每条建议附证据：笔记路径 + 段落 + 原文引用 + 触发原因
      ↓
进入 pending 队列，等用户确认
      ↓
确认后：bm_write / bm_edit 写入 Basic Memory 实体笔记
```

## 与 dsh-memory-evolve 的边界

只借鉴其思路，不移植其实现：

- 借鉴：写作边界触发、审查范围限定、建议队列、用户确认、重复建议累计 hits、导出报告。
- 不移植：全局记忆审查、固定回合计数、全局自我进化、WebUI、待办、技能自动创建、COI 调度、外部 CLI、会话广播。
- 改造点：审查对象从“全局记忆该不该记”变为“实体设定该新建/更新/状态推进/过期”。

## 工具边界

- Basic Memory MCP：`bm_search`、`bm_read`、`bm_context`、`bm_write`、`bm_edit`、`bm_find`、`bm_list`。
- DSH 插件工具：`novel_entity_review`（生成建议）、`novel_review_list`、`novel_review_approve`、`novel_review_reject`。
- 云端按需skill：Writing scene card、Entity review、Canon check、Prompt lookup 等文档在 `vault/prompts`、`vault/skills`，通过 `bm_search` 找到后 `bm_read` 读取。
