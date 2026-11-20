# 验证记录

时间：2026-11-20（Asia/Shanghai）

## 已执行

```bash
node --version
# v22.14.0

node --check dsh-plugin/index.js
node --check dsh-plugin/lib/review-store.js
node tests/review-store.test.js
```

结果：

- 插件主入口与纯函数模块语法检查通过。
- `review-store` 的 4 个测试全部通过：
  - 建议必须有 evidence；
  - dedup key 忽略中英文空白差异；
  - 重复建议合并并累加 hits；
  - decide 后 pending 列表正确更新。

## 受环境限制的验证

```bash
node --test tests/*.test.js
```

失败：`spawn EPERM`。原因是当前沙箱禁止 `node --test` 为测试文件创建带 stdio 管道的子进程；已按限制改为直接运行测试文件，测试逻辑本身通过。

## 未执行

- 未安装 DSH 插件到 profile：用户要求只创建本地项目；插件安装会修改 DSH profile。
- 未安装 `dsh-mcp-bundle`：同上；需要用户选择本地 stdio 或 Cloud HTTP 并确认端点。
- 未执行 Basic Memory 的完整 Python 测试套件：本项目的改动没有修改 Basic Memory 核心代码。
- 未连接 Basic Memory Cloud：需要用户账号、项目名和 API key。
