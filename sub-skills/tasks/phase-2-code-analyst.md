---
name: repoguide-task-phase-2-code-analyst
description: RepoGuide Phase 2b：代码详解。创建 code-analyst agent，按 depth 规则详尽分析核心文件与所有文件。
---

# Phase 2b: 代码详解

## 执行方式

创建 **code-analyst** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_code.json
```

## 任务

1. 读取 `profile.json`（注意 `depth` 字段与 `core_files_seed`）。
2. 按 `references/depth-rules.md` 和 `depth` 判定核心文件与周边文件。
3. 对每个核心文件完整 Read，提取：
   - 一句话作用
   - 类/函数/方法清单（签名 + 行号 + 作用）
   - 关键逻辑（3-10 行/函数）
   - 依赖关系
4. 对周边文件生成简略清单。
5. 输出 `directory_tree`。

## 按 depth 调整范围

### standard

- 读取**核心模块文件**（按 `references/depth-rules.md` 得分 ≥ 5 的核心文件）。
- 输出**核心目录**的 tree 风格目录树。
- 解析关键类/函数，不必覆盖每个小函数。
- 简略清单覆盖仓库 80% 的非忽略文件路径。

### deep

- **核心文件面面俱到**：核心文件详尽分析，每个类/函数都带说明：
  - 类：职责、关键方法、继承/组合关系
  - 函数：签名、行号、参数/返回值/副作用、关键逻辑
- **不遗漏非核心文件**：遍历所有非忽略文件，但按 `references/depth-rules.md` 分类处理：
  - 测试文件（`tests/`、`*_test.go`、`*.test.js|ts` 等）：生成带重要度的简略清单，并在 `test_strategy` 中概括整体测试策略。
  - 配置文件（`*.json/*.yaml/*.yml/*.toml` 等）：生成 `config_files` 清单，说明作用。
  - 脚本（`scripts/`、`Makefile`、CI 脚本等）：生成 `scripts` 清单，说明用途。
  - 资源文件（图片、静态资源等）：生成 `resources` 清单。
- 输出**完整目录树**，每个核心文件/目录带注释。
- 任何无法静态分析的动态特性写入 `limitation_notes`。

## 规模自适应（大仓库分片）

当 `profile.json.file_count_total > 500` 且 `depth == "deep"` 时，单个 agent 可能无法完整处理所有文件。此时采用分片并行策略：

1. 按仓库**顶层目录**将文件划分为若干 shard：
   - 每个一级目录一个 shard（如 `src/`、`tests/`、`docs/`）。
   - 顶层文件单独一个 shard（`root`）。
2. 为每个 shard 创建一个 code-analyst 子 agent 并行执行。
3. 每个 shard 输出 `$WORK_DIR/analysis_code_shard_<shard_name>.json`，结构与 `analysis_code.json` 相同。
4. 主 agent 或一个合并 agent 读取所有 shard，合并为最终的 `$WORK_DIR/analysis_code.json`。

### 分片合并规则

```python
import json
from pathlib import Path

work_dir = Path("$WORK_DIR")
shards = sorted(work_dir.glob("analysis_code_shard_*.json"))

merged = {
    "core_files": [],
    "peripheral_files": [],
    "config_files": [],
    "scripts": [],
    "resources": [],
    "test_strategy": "",
    "directory_tree": "",
    "limitation_notes": [],
}

for shard_path in shards:
    data = json.loads(shard_path.read_text(encoding="utf-8"))
    for key in ["core_files", "peripheral_files", "config_files", "scripts", "resources", "limitation_notes"]:
        merged[key].extend(data.get(key, []))
    if data.get("test_strategy"):
        merged["test_strategy"] = data["test_strategy"]
    if data.get("directory_tree"):
        merged["directory_tree"] += data["directory_tree"] + "\n"

# 去重并排序
merged["core_files"] = sorted(merged["core_files"], key=lambda x: x["path"])
merged["peripheral_files"] = sorted(set((x["path"], x["one_liner"], x["importance"]) for x in merged["peripheral_files"]))
merged["config_files"] = sorted(merged["config_files"], key=lambda x: x["path"])
merged["scripts"] = sorted(merged["scripts"], key=lambda x: x["path"])
merged["resources"] = sorted(merged["resources"], key=lambda x: x["path"])

(work_dir / "analysis_code.json").write_text(
    json.dumps(merged, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
```

## 输出 JSON

```json
{
  "core_files": [
    {
      "path": "...",
      "one_liner": "...",
      "classes": [
        {"name": "...", "line": 0, "signature": "...", "purpose": "..."}
      ],
      "functions": [
        {"name": "...", "line": 0, "signature": "...", "key_logic": "...", "params": [...], "returns": "...", "side_effects": "..."}
      ],
      "dependencies": ["..."]
    }
  ],
  "peripheral_files": [
    {"path": "...", "importance": "high|medium|low", "one_liner": "..."}
  ],
  "config_files": [
    {"path": "...", "purpose": "..."}
  ],
  "scripts": [
    {"path": "...", "purpose": "..."}
  ],
  "resources": [
    {"path": "...", "purpose": "..."}
  ],
  "test_strategy": "一句话概括",
  "directory_tree": "字符串形式的目录树，deep 必填完整树，standard 为核心目录",
  "limitation_notes": []
}
```

## 注意事项

- 严格遵循 `references/depth-rules.md` 中的"永远简略的类别"，不将 node_modules、vendor、构建产物等纳入分析。
- deep 模式下，不得因文件数量多而跳过任何非忽略文件；若因工具限制无法全部读取，写入 `limitation_notes`。
- 行号必须尽量准确，便于 writer 在手册中定位。

## 输出校验

使用 `_index.md` 中的 `validate_json` 校验 `$WORK_DIR/analysis_code.json`：

```python
validate_json(
    "$WORK_DIR/analysis_code.json",
    required_fields=["core_files", "peripheral_files", "directory_tree", "limitation_notes"],
    nullable_fields=["config_files", "scripts", "resources", "test_strategy"],
)
```

每个 `core_files` 元素必须包含 `path`、`one_liner`、`classes`、`functions`、`dependencies`。

## 下一 Phase

本 Phase 与 [phase-2-architect.md](phase-2-architect.md) 并行执行。
