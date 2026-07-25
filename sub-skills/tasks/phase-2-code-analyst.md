---
name: repoguide-task-phase-2-code-analyst
description: RepoGuide Phase 2b：代码详解。按紧凑结构化 schema 分析核心文件，先讲文件职责和核心流程，再列类、方法、独立函数与 main 步骤。
---

# Phase 2b: 代码详解

## 执行方式

创建 **code-analyst** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_code.json
```

## 设计理念（重要）

代码详解要先回答“这个文件到底负责什么、怎么跑起来”，再解释符号。每个核心文件必须先给出一段可直接读懂的 `file_role_summary`，再给出 `core_flow` 编号步骤，最后紧凑列出类、类下方法、独立函数和 `main_steps`。所有“职责/用途/说明”必须中文，不得直接复制英文 docstring。

示例风格：

```text
GFN 只负责生成候选 alpha；run_adaptive_combination.py 负责在验证/测试阶段每天动态筛 alpha、回归权重，用当天 alpha 值预测股票未来收益，最后计算 IC 与策略收益。

核心流程：
1. 读取 pool_*.json 中的 alpha 表达式
2. 在完整数据区间上计算每个 alpha 的因子值 fct_tensor
3. 计算未来收益标签 tgt_tensor
4. 预先计算每个 alpha 每天的 IC / RankIC
5. 从 validation 第一天开始逐日滚动
6. 每天只用 cur - shift 以前的历史，避免未来信息泄漏
7. 根据历史 RankIC 和 RankICIR 筛选表现好的 alpha
8. 用历史 alpha 值和历史收益做最小二乘回归
9. 得到当天 alpha 组合权重
10. 用当天 alpha 值预测当天股票未来收益
11. 保存每天预测到 pred_list
12. 切成 Validation / Test 分别算指标
13. 保存测试集每日收益 ret_s.npy
```

## 任务

1. 读取 `profile.json`（注意 `depth`、`core_files_seed`、`module_candidates`）。
2. 按 `references/depth-rules.md` 判定核心文件与周边文件。
3. 对每个核心文件完整 Read，提取：
   - `one_liner`：一句话中文作用（≤ 30 字）。
   - `file_role_summary`：3-6 句中文总述，讲清该文件在仓库里的真实职责、输入、输出、与其他入口的关系。
   - `core_flow`：5-14 个中文步骤，按运行顺序写，关键防泄漏/训练/评估/保存逻辑必须出现。
   - `classes`：类清单，每个类含 `methods`，类和方法都要有中文职责。
   - `functions`：不属于类的独立函数条目。
   - `main_steps`：若文件有 `main`、`if __name__ == "__main__"`、CLI 入口或脚本顶层流程，提取 3-12 个中文步骤；没有则为空列表。
   - `dependencies`：该文件 import 的其他文件/模块。
4. 对周边文件生成简略清单。
5. 输出 `directory_tree`（可复用 architect 的 annotated_tree 风格；缺失时给空字符串）。

## 紧凑 schema

### classes 元素

```json
{
  "name": "类名",
  "line": 12,
  "signature": "class Foo(Base):",
  "purpose": "中文一句话职责，不得为空",
  "methods": [
    {
      "name": "fit",
      "line": 34,
      "signature": "def fit(self, x, y):",
      "purpose": "用历史因子和收益拟合组合权重",
      "params": [{"name": "x", "meaning": "历史因子矩阵"}],
      "returns": "回归后的权重或自身",
      "key_logic": "def fit(self, x, y):\n    self.weight = solve(x, y)\n    return self"
    }
  ]
}
```

### functions 元素（独立函数）

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
  "key_logic": "def foo(x, mask):\n    # 关键 3-10 行代码片段（保留原代码，勿翻译）\n    ...\n    return y"
}
```

**字段硬约束**：
- `file_role_summary` 不得复述文件名，必须说明该文件承担的产品/算法职责。
- `core_flow` 必须按执行顺序编号；脚本类文件不少于 8 步，库文件不少于 5 步。
- `purpose` 不得为空字符串，必须中文。
- `key_logic` 为原代码片段（保留英文代码本身），≤ 10 行；超长则截断并末尾加 `# ...（略）`。
- `params` 的 `meaning` 必须中文。
- 说明来源优先级：代码执行流 > docstring > 上方注释 > 从签名/调用点推断；推断也要写成中文。

## 按 depth 调整范围

### standard

- 读取核心模块文件（按 `references/depth-rules.md` 得分 ≥ 5）。
- 每个核心文件必须有 `file_role_summary`、`core_flow`、关键类/函数和必要 `main_steps`。
- 单文件函数条目优先解释入口链和关键算法，不必覆盖每个小工具函数。
- 简略清单覆盖仓库 80% 的非忽略文件路径。

### deep

- 核心文件至少包括：
  - 主包模块（如 `src/alpha_gfn/`、`src/alphagen/`、`src/alphagen_qlib/`）。
  - 入口训练脚本（`train_gfn.py`、`train_ppo.py`、`train_qcm.py`、`train_AFF.py`、`train_GP.py`）。
  - 评估/组合脚本（`run_adaptive_combination.py`、`combine_AFF.py`）。
  - 训练/实验入口脚本（`train_*.py`、`run_*.py`）一律视为核心文件，不得仅放入 scripts 清单。
- 每个类/函数都带中文一句话说明；类下方法放入 `classes[*].methods`，不要与独立函数混在一起。
- 不遗漏非核心文件：遍历所有非忽略文件，分类处理测试、配置、脚本、资源。
- 任何无法静态分析的动态特性写入 `limitation_notes`。

## 规模自适应（大仓库分片）

当 `profile.json.file_count_total > 500` 且 `depth == "deep"` 时，按顶层目录分片并行。每个 shard 输出 `analysis_code_shard_<name>.json`，主 agent 合并为 `analysis_code.json`，合并时保留所有 `file_role_summary` / `core_flow` / `main_steps`。

## 输出 JSON

```json
{
  "core_files": [
    {
      "path": "run_adaptive_combination.py",
      "one_liner": "滚动筛选并组合 alpha",
      "file_role_summary": "GFN 只负责生成候选 alpha；本文件负责在验证/测试阶段每天动态筛 alpha、动态回归权重，并用当天 alpha 值预测股票未来收益，最后计算 IC 和策略收益。",
      "core_flow": [
        "读取 pool_*.json 中的 alpha 表达式",
        "计算每个 alpha 的因子值 fct_tensor",
        "计算未来收益标签 tgt_tensor",
        "预先计算每日 IC / RankIC",
        "逐日滚动并只使用 cur - shift 以前的历史，避免未来信息泄漏",
        "按 RankIC 和 RankICIR 筛选 alpha",
        "最小二乘回归得到当天组合权重",
        "预测当天股票未来收益并保存 pred_list",
        "切分 Validation / Test 并保存 ret_s.npy"
      ],
      "classes": [
        {
          "name": "RollingCombiner",
          "line": 12,
          "signature": "class RollingCombiner:",
          "purpose": "维护滚动筛选、回归和预测状态",
          "methods": [
            {"name": "fit_day", "line": 45, "signature": "def fit_day(self, cur):", "purpose": "用历史窗口拟合当天权重", "params": [{"name": "cur", "meaning": "当前交易日索引"}], "returns": "当天组合权重", "key_logic": "def fit_day(self, cur):\n    hist = slice(0, cur - self.shift)\n    return lstsq(self.x[hist], self.y[hist])"}
          ]
        }
      ],
      "functions": [
        {"name": "main", "line": 180, "signature": "def main():", "purpose": "串起读取、计算、滚动评估和保存", "params": [], "returns": "无显式返回", "key_logic": "def main():\n    load_pool()\n    run_rolling_eval()"}
      ],
      "main_steps": ["解析参数", "读取表达式池", "计算因子与标签", "滚动回归预测", "输出指标与 ret_s.npy"],
      "dependencies": ["numpy", "torch", "src.alphagen_qlib"]
    }
  ],
  "peripheral_files": [
    {"path": "...", "importance": "high|medium|low", "one_liner": "中文一句话"}
  ],
  "directory_tree": "字符串或空字符串",
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
    required_fields=["core_files", "peripheral_files", "directory_tree", "limitation_notes"],
    nullable_fields=["config_files", "scripts", "resources", "test_strategy"],
)
```

附加检查：每个 `core_files[*]` 必须包含非空 `file_role_summary`、`core_flow`；脚本入口文件必须包含 `main_steps`；每个类/函数/方法的 `purpose` 不得为空；`train_*.py` / `run_*.py` 必须出现在 `core_files` 而非 `scripts`。

## 下一 Phase

本 Phase 与 [phase-2-architect.md](phase-2-architect.md) 并行执行。