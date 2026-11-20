# 合并后目录职责补充

基于对三个仓库的最终分析，补充以下实现边界：

## Basic Memory 是唯一事实源

- `vault/notes/entities/*.md`：人物、地点、组织、物品、体系、概念。
- `vault/notes/scenes/*.md`：场景正文与场景卡。
- `vault/notes/chapters/*.md`：章节大纲与定稿记录。
- `vault/reviews/pending/*.jsonl`：仅保存待确认建议，不作为 canon 事实源。
- `vault/reviews/history/*.jsonl`：已确认/拒绝/归档建议历史。

Basic Memory 的 Markdown 文件是 canonical state；数据库、搜索索引和本项目的 review 队列都是派生状态。

## 下放的自我认知放在实体笔记中

实体笔记可以包含如下段落：

```markdown
## 自我认知（实体内）
- [self] 我必须守住这个秘密，哪怕她误会我。
- [blindspot] 我把忠诚误解为不解释。
```

地点/组织/体系可使用：

```markdown
## 内在逻辑
- [logic] 这座城把旧秩序藏在废墟之下。
- [self-narrative] 我们认为自己是在恢复秩序，而不是征服。
```

这些内容只通过 `bm_search entity:<名称>` 和 `bm_read section=...` 按需读取，不进入全局 system prompt。

## 建议队列与写入边界

- `novel_entity_review` 只写 review 队列，不写实体笔记。
- `novel_review_decide approve` 只把建议标为 approved，并返回 JSON；实际写入必须由主 agent 调用 Basic Memory `bm_write`/`bm_edit` 完成。
- 这样设计是为了保证“建议 → 确认 → 写入”三段分离，避免自动污染 canon。

## DSH MCP bundle 说明

`dsh-mcp-bundle/` 是配置模板，不是自定义 MCP server。它使用 DSH 已安装的 `@deepseek-ai/dsh-mcp-client`：

- 默认本地 stdio：`uvx --prerelease=allow basic-memory mcp`。
- Cloud HTTP：替换 `url` 为实际 Basic Memory Cloud MCP 端点。
- 不要提交 API key/JWT；Cloud 凭据用 `basic-memory cloud api-key save` 在本机保存。
