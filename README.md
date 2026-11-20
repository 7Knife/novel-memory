# Novel Memory

以 **Basic Memory** 为主结构、融合 **dsh-self-memory** 的按需记忆调用方法，并只借鉴 **dsh-memory-evolve** 的“实体级自我审查 / 建议 → 确认”触发思路的本地项目骨架，面向长篇小说创作。

> 这是一套配置与工作流工程，不 Fork Basic Memory 核心代码。Basic Memory 继续负责 Markdown 笔记、知识图谱、MCP 工具与云端同步；本项目只增加小说创作所需的实体规范、按需检索规则和一个轻量的 DSH Host 插件。

## 来源与合并原则

| 来源 | 保留方式 | 删除/不移植 |
|---|---|---|
| `basic-memory/` | 作为主项目基础：Markdown 文件为唯一事实源，实体/观察/关系模型，MCP 工具，Basic Memory Cloud | 不改核心代码 |
| `dsh-self-memory/` | 保留其“记忆不常驻、需要时调用”的思路；参考其工具定义形态和 systemPrompt 注入边界 | 删除重复的四层存储、独立检索、L2 权重/衰减、全局 selfNote、全局审查、加密同步、设备网、会话同步、插件自动补装 |
| `dsh-memory-evolve/` | 只提取触发思路：写作边界事件 → 限定实体范围 → 每条建议附依据 → 用户确认 | 不安装插件主体；不移植全局记忆、WebUI、待办、技能自动创建、COI 调度、外部 CLI、会话广播、审查员模型 |

## 核心决策

1. **全局不使用自我认知**：不向主 agent 每轮注入“我是谁/关于我自己”的提示词。
2. **实体级下放自我认知**：人物、地点、组织、体系等具体实体，各自在笔记里拥有“自我认知”段落（人物可直接写内心自述；地点/组织写“内在逻辑/自洽性”），只有当前场景引用到该实体时才按需读取。
3. **提示词极简**：主提示词只说明触发规则；大量提示词模板、skill 说明、MCP 使用手册放在云端/Basic Memory 笔记库，agent 不知道时通过检索工具取回。
4. **云端记忆库**：使用 Basic Memory Cloud（本地可通过 `basic-memory project set-cloud` / cloud api-key 配置），按需调用 `bm_search`、`bm_read`、`bm_context`，而非全局注入。
5. **实体级审查**：在“场景写完 / 章定稿 / 用户说这个设定改了 / 主动触发”时，只审查当前场景实际出场或被引用的实体，建议三类：新建、更新、状态推进。所有建议默认 `draft`/`pending`，用户确认后写入正式笔记。

## 目录

```text
novel-memory/
├── README.md                     # 本文件
├── docs/
│   ├── ARCHITECTURE.md           # 合并架构与目录职责
│   ├── WORKFLOW.md               # 小说创作工作流
│   ├── ENTITY-REVIEW.md          # 实体级审查规则
│   ├── CLOUD-MEMORY.md           # Basic Memory Cloud 配置与检索策略
│   ├── PROMPT-MINIMAL.md         # 极简主提示词模板
│   ├── MERGE-MAP.md              # 三仓库逐项合并映射
│   └── VERIFICATION.md           # 验证记录
├── schemas/
│   ├── entity.schema.json        # 实体 frontmatter / canon_status / superseded
│   └── review-suggestion.schema.json
├── vault/
│   ├── notes/
│   │   ├── entities/             # 人物、地点、组织、物品、体系
│   │   ├── scenes/               # 场景正文与场景卡
│   │   ├── chapters/             # 章节大纲/定稿记录
│   │   └── index/                # 地图/索引笔记
│   ├── prompts/                  # 云端按需提示词模板
│   ├── skills/                   # 云端按需 skill 说明
│   ├── mcp/                      # 云端 MCP 使用说明
│   └── reviews/
│       ├── pending/              # 待确认建议（JSONL）
│       └── history/              # 已确认/已拒绝历史
├── dsh-plugin/                   # 轻量 DSH Host 插件：实体审查与确认
├── dsh-mcp-bundle/               # DSH → Basic Memory MCP 连接模板（本地/cloud 二选一）
└── tests/                        # 本地验证
```

## 快速开始

1. 参考 `docs/CLOUD-MEMORY.md` 配置 Basic Memory 项目与 Cloud。
2. 把主 agent 提示词替换为 `docs/PROMPT-MINIMAL.md` 的极简版本。
3. 写作时按 `docs/WORKFLOW.md` 产出场景/章节。
4. 在写作边界触发实体审查，按 `docs/ENTITY-REVIEW.md` 生成建议。
5. 通过 `/novel-review` 或插件工具确认建议；未确认的实体一律 `draft`/`pending`，不得当作 canon。

## 审查类型速览

| 类型 | 触发条件 | 动作 |
|---|---|---|
| `new` | 正文出现地图/索引中不存在、但有长期价值的实体 | 建议新建笔记，`entity_type` + `canon_status: draft` + 一句摘要 |
| `update` | 现有实体字段变化（领袖更替、地点被毁、规则新层面） | 建议修改字段；旧值不删除，标 `superseded` 并保留变更理由 |
| `status_progression` | draft/pending 实体在正文中反复使用且用户确认 | 建议推进 `canon_status` 到 `canon`，或标记 `obsolete` |

每条建议都必须包含证据：`source_note`、`paragraph`、`quote`、`trigger`（场景写完/章定稿/设定变更/主动触发）。

## 验证

```bash
node --check dsh-plugin/index.js
node --check dsh-plugin/lib/review-store.js
node tests/review-store.test.js
```

当前插件不修改 DSH profile；安装与启用由用户自行决定。

## License

MIT. See `LICENSE`.

See `THIRD_PARTY_NOTICES.md` for the copyright assessment of the three upstream reference repositories.

## 说明

工作区中 `basic-memory/`、`dsh-self-memory/`、`dsh-memory-evolve/` 是三个上游仓库的克隆，仅作来源对照；实际合并成果在 `novel-memory/` 目录。这些克隆目录通过 `.gitignore` 排除，不会上传到本仓库。
