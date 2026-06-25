---
name: repoguide-task-phase-2-code-analyst
description: RepoGuide Phase 2b：代码详解。按卡片式 schema 详尽分析核心文件，类/函数须有中文职责、参数表与关键逻辑片段。
---

# Phase 2b: 代码详解（卡片式）

## 执行方式

创建 **code-analyst** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_code.json
```

## 设计理念（重要）

代码详解的读者是人，**禁止密密麻麻的文字堆砌**。每个核心文件一张"卡片"：一句话职责 → 类清单表 → 函数卡片（签名 + 中文职责 + 参数表 + 关键逻辑片段）。所有"职责/用途/说明"必须中文，不得直接复制英文 docstring。

## 任务

1. 读取 `profile.json`（注意 `depth`、`core_files_seed`、`module_candidates`）。
2. 按 `references/depth-rules.md` 判定核心文件与周边文件。
3. 对每个核心文件完整 Read，提取：
   - `one_liner`：一句话中文作用（≤ 30 字）
   - `classes`：类清单（见 schema）
   - `functions`：函数卡片（见 schema）
   - `dependencies`：该文件 import 的其他文件/模块
4. 对周边文件生成简略清单。
5. 输出 `directory_tree`（与 architect 的 annotated_tree 一致风格，本 Phase 可省略，由 architect 统一产出）。

## 卡片式 schema

### classes 元素

```json
{
  "name": "类名",
  "line": 12,
  "signature": "class Foo(Base):",
  "purpose": "中文一句话职责，不得为空"
}
```

### functions 元素（核心）

```json
{
  "name": "函数名",
  "line": 34,
  "signature": "def foo(x: Tensor, mask: bool) -> Tensor:",
  "purpose": "中文一句话职责，不得为空，不得输出空字符串",
  "params": [
    {"name": "x", "meaning": "输入特征张量"},
    {"name": "mask", "meaning": "是否屏蔽无效位置"}
  ],
  "returns": "处理后特征张量",
  "key_logic": "def foo(x, mask):\n    # 关键 3-12 行代码片段（保留原代码，勿翻译）\n    ...\n    return y"
}
```

**字段硬约束**：
- `purpose` 不得为空字符串，必须中文。
- `key_logic` 为原代码片段（保留英文代码本身），≤ 12 行；超长则截断并末尾加 `# ...（略）`。
- `params` 的 `meaning` 必须中文。
- 说明来源优先级：docstring > 上方注释 > 从签名/首行推断；推断也要写成中文。

## 按 depth 调整范围

### standard

- 读取**核心模块文件**（按 `references/depth-rules.md` 得分 ≥ 5）。
- 解析关键类/函数，不必覆盖每个小函数。
- 简略清单覆盖仓库 80% 的非忽略文件路径。

### deep

- **核心文件面面俱到**：核心文件至少包括：
  - 主包模块（如 `src/alpha_gfn/`、`src/alphagen/`、`src/alphagen_qlib/`）
  - 入口训练脚本（`train_gfn.py`、`train_ppo.py`、`train_qcm.py`、`train_AFF.py`、`train_GP.py`）
  - 评估/组合脚本（`run_adaptive_combination.py`、`combine_AFF.py`）
  - **训练/实验入口脚本（`train_*.py`、`run_*.py`）一律视为核心文件，不得仅放入 scripts 清单**。
- **每个类/函数都带中文一句话说明**（`purpose` 不得为空）。
- **不遗漏非核心文件**：遍历所有非忽略文件，分类处理：
  - 测试文件：简略清单 + `test_strategy` 概括。
  - 配置文件（`*.json/yaml/yaml/toml`）：`config_files` 清单。
  - 脚本（`scripts/`、Makefile、CI 等）：`scripts` 清单。
  - 资源文件：`resources` 清单。
- 任何无法静态分析的动态特性写入 `limitation_notes`。

## 规模自适应（大仓库分片）

当 `profile.json.file_count_total > 500` 且 `depth == "deep"` 时，按顶层目录分片并行，合并规则同前（见仓库历史）。每个 shard 输出 `analysis_code_shard_<name>.json`，主 agent 合并为 `analysis_code.json`。

## 输出 JSON

```json
{
  "core_files": [
    {
      "path": "src/alpha_gfn/gflownet.py",
      "one_liner": "GFlowNet 主模型定义",
      "classes": [
        {"name": "GFlowNet", "line": 12, "signature": "class GFlowNet(nn.Module):", "purpose": "GFlowNet 生成器，前向 + 采样"}
      ],
      "functions": [
        {
          "name": "forward",
          "line": 34,
          "signature": "def forward(self, x: Tensor) -> Tensor:",
          "purpose": "前向计算返回 logits",
          "params": [{"name": "x", "meaning": "输入特征"}],
          "returns": "logits 张量",
          "key_logic": "def forward(self, x):\n    h = self.encoder(x)\n    return self.head(h)"
        }
      ],
      "dependencies": ["torch", "src.alphagen.models"]
    }
  ],
  "peripheral_files": [
    {"path": "...", "importance": "high|medium|low", "one_liner": "中文一句话"}
  ],
  "config_files": [{"path": "...", "purpose": "中文用途"}],
  "scripts": [{"path": "...", "purpose": "中文用途"}],
  "resources": [{"path": "...", "purpose": "中文用途"}],
  "test_strategy": "中文一句话概括",
  "limitation_notes": []
}
```

## 输出校验

使用 `_index.md` 中的 `validate_json` 校验 `$WORK_DIR/analysis_code.json`：

```python
validate_json(
    "$WORK_DIR/analysis_code.json",
    required_fields=["core_files", "peripheral_files", "limitation_notes"],
    nullable_fields=["config_files", "scripts", "resources", "test_strategy"],
)
```

附加检查：每个 `core_files[*].functions[*].purpose` 不得为空字符串；`train_*.py` / `run_*.py` 必须出现在 `core_files` 而非 `scripts`。

## 下一 Phase

本 Phase 与 [phase-2-architect.md](phase-2-architect.md) 并行执行。
