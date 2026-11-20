# Lifecycle extension (external, opt-in)

混合方案的外挂实现：**Basic Memory 源码零改动**，全部新逻辑在本目录；其中排序加权是最小扩展层，包装 `bm_search` 结果，不进入 Basic Memory 核心。

## 已核实的基本事实（避免改错地方）

- Basic Memory 已把任意自定义 frontmatter 字段归一化后存入 `entity_metadata`（`markdown/utils.py:74-75`、`markdown/entity_parser.py:349`）。所以 `weight` / `base_weight` / `last_hit` / `canon_status` **无需改解析器**。
- Basic Memory 的搜索排序在 `services/search_reader.py` 的 fusion/rerank 阶段；本扩展不碰它，改在 DSH/调用方对 `bm_search` 结果做二次排序。
- Basic Memory 的 MCP 工具注册表是 `mcp/tools/__init__.py`；本扩展的审查工具是**独立可选的 MCP server**，不注册进去。

## 四个模块

| 模块 | 作用 | 回滚 |
|---|---|---|
| `fields.py` | 统一的字段名 + 默认权重（identity 3.0 / preference 2.5 / misc 1.3…） | 不导入即可 |
| `frontmatter_io.py` | 只改 YAML frontmatter，正文逐字保留，原子写 | 不用即可 |
| `decay.py` | 批量衰减 + 归档，不常驻；可 DSH 定时任务每天/每周跑 | 不跑脚本即可 |
| `ranking.py` | 对 bm_search 结果按 `weight × status` 二次排序 | 不调用 rerank 即恢复原生排序 |
| `review_queue.py` + `mcp_tools.py` | 单个 JSON 队列 + review_memory/propose_memory/apply_review 确认工具 | 不挂载该 MCP server 即可 |
| `SELF_NARRATIVE.md` | `## 自述` 段落规范（实体级人格，按需加载） | 删段落即可 |

## 使用

### 1. 权重衰减（手动/定时）

```bash
python -m lifecycle_extension.decay --root <vault/notes> --dry-run
python -m lifecycle_extension.decay --root <vault/notes>
```

它只改带 `weight` 或 `last_hit` frontmatter 的笔记；按 3 天一档衰减，低于 1.0 标 `archived`（不删除）。写回后由 Basic Memory 既有 watcher / 下次索引把 SQLite 收敛，脚本**不碰 SQLite**。

### 2. 审查队列

```python
from lifecycle_extension.review_queue import ReviewQueue
q = ReviewQueue(Path.home() / ".basic-memory" / "novel-review-queue.json")
q.propose([{
    "entity_permalink": "memory://lin-yan",
    "operation": "update",
    "payload": {"field": "attitude", "value": "..."},
    "reason": "场景 3 中态度变化",
    "evidence": [{"source_note": "ch03-s05.md", "quote": "..."}],
}])
pending = q.list_pending()
q.decide(pending[0].id, True)
q.apply(pending[0].id, lambda p: bm_write(...))  # 回调里调用 Basic Memory 公共工具
```

`mcp_tools.py` 提供同名的薄封装（review_memory / propose_memory / apply_review / review_status），可作为独立 MCP server 挂载。

### 3. 加权排序

```python
from lifecycle_extension.ranking import rerank
results = rerank(bm_search_results)  # 结果里带 metadata/entity_metadata/frontmatter 即可
```

`weight` 归一化 `min(weight/3, 1)`，`canon_status=draft` ×0.6、`archived` ×0.2、canon ×1.0。archived 被降权而非隐藏，仍可显式查到。

### 4. 实体自我认知

在人物笔记写 `## 自述` 段落；按 `AGENTS-md-addition.md` 的规则让 agent 只在当前场景引用该实体时读取。删除段落即回滚。

## 安全边界

- 不修改 Basic Memory 的 SQLite 表、解析器、Markdown 渲染核心、MCP 工具注册表。
- 所有写回走 Markdown frontmatter/Basic Memory 公共 API；不直接写索引。
- `weight` 只是检索信号，不决定 canon；`draft → canon` 仍需用户确认。
- 默认关闭：不跑脚本、不挂 MCP、不调用 rerank，就退回原生 Basic Memory 行为。

## 测试

```bash
python -m unittest discover -s lifecycle_extension/tests -t . -v
```

5 个测试覆盖：frontmatter 保真、3 天衰减、归档阈值、间隔内不衰减、加权排序、审查队列去重与确认门禁。
