---
name: repoguide-tool-code-analyzer
description: RepoGuide 的代码分析策略：如何读取文件、提取类/函数/依赖、判断核心文件与周边文件。
---

# RepoGuide · 代码分析策略

## 读取原则

- 核心文件必须完整 Read。
- 周边文件至少 Read 开头 50 行判断作用。
- 忽略 `tests/`、`node_modules/`、`vendor/`、`dist/`、`build/`、`.git/` 等。

## 核心文件判定

引用 `references/depth-rules.md`。核心得分规则：

| 规则 | 权重 |
|------|------|
| 入口链追溯 | +10 |
| 配置显式声明 | +10 |
| 模块入口命名 | +5 |
| 论文伪代码对应 | +5 |
| 启发式补充 | +3 |

得分 ≥ 5 为核心文件。

## 提取内容（结构化 schema）

对每个核心文件输出。**`purpose` 不得为空、不得输出空字符串，必须中文**；`key_logic` 为 3-12 行原代码片段：

```json
{
  "path": "src/foo.py",
  "one_liner": "一句话作用（中文）",
  "classes": [{"name": "Foo", "line": 10, "signature": "class Foo:", "purpose": "中文职责，不得为空"}],
  "functions": [{"name": "bar", "line": 20, "signature": "def bar(self, x):", "purpose": "中文职责，不得输出空字符串", "params": [{"name": "x", "meaning": "中文含义"}], "returns": "中文说明", "key_logic": "def bar(self, x):\n    return x+1"}],
  "dependencies": ["src/baz.py"]
}
```

## 周边文件清单

| 路径 | 一句话作用 | 重要度 |
|------|-----------|--------|
| `src/utils.py` | 工具函数集 | 中 |

重要度：高（被广泛引用）/ 中（被 2-5 个引用）/ 低（叶子节点）。

## 规模自适应

| 总文件数 | 策略 |
|----------|------|
| < 50 | 所有非忽略文件按核心分析 |
| 50-500 | 按规则筛核心 |
| > 500 | 核心文件上限 30 个 |
