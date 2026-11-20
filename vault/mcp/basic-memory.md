---
title: MCP - Basic Memory Tools
type: MCPDoc
tags: [mcp, basic-memory]
permalink: mcp-basic-memory
---

# Basic Memory MCP 速查

工具清单以 Basic Memory 的 `src/basic_memory/mcp/tools/__init__.py` 注册表为准。

## 读取

- `bm_search(query="entity:林夏")`：搜索实体/观察/关系。
- `bm_read(identifier="vault/notes/entities/lin-xia.md", section="观察")`：只读相关段落。
- `bm_context(...)`：构建一组相关笔记上下文。
- `bm_find`：按路径查找。
- `bm_list`：列目录。

## 写入

- `bm_write`：新建/覆盖笔记；创建实体笔记用。
- `bm_edit`：局部修改；更新实体字段或 frontmatter 用。

## 安全边界

- 统一使用 `expected_checksum`（由 `bm_read` 获取）避免覆盖别人刚改过的笔记。
- 实体审查建议默认不写库；用户确认后写。
- 覆盖更新时，旧值不删除，转为 superseded 记录。
