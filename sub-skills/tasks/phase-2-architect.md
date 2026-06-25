---
name: repoguide-task-phase-2-architect
description: RepoGuide Phase 2a：架构与数据流分析。以注释化目录树为明星产物，graphviz 生成单张高质量架构总览图，产出数据流叙述与流转表。
---

# Phase 2a: 架构与数据流分析

## 执行方式

创建 **architect** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_arch.json
```

## 设计理念（重要）

仓库结构的**首要展示方式是"注释化目录树"**——每一行带中文用途注释，让人一眼看懂仓库布局。**废弃一切树状的 mermaid 依赖/数据流图**（它们既像树又难懂）。架构总览改用 **graphviz 生成单张分层着色、横向流转的 PNG**，由 Phase 2.5 渲染。

## 任务

1. 读取 `profile.json`（注意 `depth` 字段与 `module_candidates`）。
2. 生成 **`annotated_tree`**：注释化目录树字符串（见下方规范），这是本 Phase 的明星产物。
3. 生成 **`architecture_overview_dot`**：一张 graphviz DOT 源码（见下方规范），描述分层架构与数据流转。
4. 撰写 **`data_flow_narrative`**：3-6 句中文叙述，讲清数据从输入到输出的主要流转。
5. 生成 **`data_flow_table`**：数据流转表，每行 `{step, input, module, output, file}`。
6. 识别 **`key_state_points`**：配置加载、初始化、训练循环、IO 边界、评估切换等关键状态点。
7. 推断 **`design_decisions`**：3-5 个关键设计决策（含证据与理由）。

## annotated_tree 规范（明星产物）

- 使用 `tree` 命令风格缩进：`├──`、`└──`、`│`、空格。
- **每一行末尾必须带 ` # 中文用途注释`**（`#` 前一个空格，注释 ≤ 30 字）。无注释的行不得出现。
- 忽略 `.git/`、`__pycache__/`、`node_modules/`、`.venv/`、`dist/`、`build/` 等。
- 目录与文件都要注释；目录注释说明该目录整体职责。
- 深度建议不超过 5 层；过深的叶子目录可折叠为 `... (N 个文件) # 用途`。

示例：

```text
AlphaSAGE/                      # 项目根：基于 GFlowNet 的 alpha 因子挖掘框架
├── src/                        # 核心源码
│   ├── alpha_gfn/              # GFlowNet 生成器与训练逻辑
│   │   ├── gflownet.py         # GFlowNet 主模型定义
│   │   └── trainer.py          # GFlowNet 训练循环
│   ├── alphagen/               # 通用工具与 RL 基线
│   └── gplearn/                # 遗传规划基线
├── train_gfn.py                # GFlowNet 训练入口脚本
├── run_adaptive_combination.py # 自适应组合评估入口
├── pyproject.toml              # PDM 依赖与项目元信息
└── README.md                   # 项目说明
```

### standard vs deep

- **standard**：保留到核心模块层级，核心文件带注释，周边目录可折叠。
- **deep**：完整树，每个目录与主要文件都带注释，深度 ≤ 5。

## architecture_overview_dot 规范

生成 **一张** graphviz DOT 源码字符串，要求：

- `digraph`，`rankdir=LR`（横向流转，不是树）。
- 用 `subgraph cluster_*` 分层着色：如"输入层/数据"、"模型层"、"训练层"、"评估/输出层"，每层一个 cluster，配 `style=filled, color=浅色, label=中文层名`。
- 节点为模块/关键文件，边标注数据/调用方向（中文标签）。
- 节点形状用 `box, style="rounded,filled"`，配色协调。
- 字体设 `fontname="Microsoft YaHei"`（Windows）/`PingFang SC`（macOS）/`Noto Sans CJK SC`（Linux），DOT 中写 `node [fontname="Microsoft YaHei"]`。
- 图尺寸适中（节点 ≤ 25 个），过于细节的文件不进图。

DOT 示例骨架：

```dot
digraph arch {
  rankdir=LR;
  graph [fontname="Microsoft YaHei", bgcolor="white"];
  node [shape=box, style="rounded,filled", fontname="Microsoft YaHei", fontsize=11];
  edge [fontname="Microsoft YaHei", fontsize=9, color="#555555"];

  subgraph cluster_data { label="数据层"; style=filled; color="#E8F0FE";
    qlib [label="Qlib 行情数据", fillcolor="#FFFFFF"]; }
  subgraph cluster_model { label="模型层"; style=filled; color="#FCE8E6";
    rgcn [label="RGCN 结构感知编码器", fillcolor="#FFFFFF"];
    gfn [label="GFlowNet 生成器", fillcolor="#FFFFFF"]; }
  ...
  qlib -> rgcn [label="特征"];
  rgcn -> gfn [label="嵌入"];
}
```

## 按 depth 调整范围

### standard

- 注释化目录树为核心目录层级。
- 架构总览图覆盖主要模块。
- 数据流叙述 3-4 句，流转表 3-5 行。
- 状态点覆盖主要入口与关键切换。

### deep

- 完整注释化目录树，每个主要文件带注释。
- 架构总览图覆盖所有主要模块与关键文件。
- 数据流叙述 5-6 句，流转表覆盖完整链路。
- 状态点覆盖配置、初始化、训练循环、IO、错误处理、评估、生命周期。

## 输出 JSON

```json
{
  "annotated_tree": "字符串，每行带 # 中文注释",
  "architecture_overview_dot": "digraph 字符串，rankdir=LR，分层着色",
  "data_flow_narrative": "3-6 句中文叙述",
  "data_flow_table": [
    {"step": "1", "input": "...", "module": "...", "output": "...", "file": "..."}
  ],
  "key_state_points": [
    {"name": "...", "description": "...", "file": "...", "line": 0}
  ],
  "design_decisions": [
    {"decision": "...", "evidence": "file:line", "reasoning": "..."}
  ],
  "limitation_notes": []
}
```

## 输出校验

使用 `_index.md` 中的 `validate_json` 校验 `$WORK_DIR/analysis_arch.json`：

```python
validate_json(
    "$WORK_DIR/analysis_arch.json",
    required_fields=["annotated_tree", "architecture_overview_dot",
                     "data_flow_narrative", "data_flow_table",
                     "key_state_points", "design_decisions", "limitation_notes"],
)
```

附加检查：`annotated_tree` 中非空行 ≥ 80% 须含 ` # ` 注释；`architecture_overview_dot` 须含 `rankdir=LR` 与至少一个 `cluster_`。

## 下一 Phase

本 Phase 与 [phase-2-code-analyst.md](phase-2-code-analyst.md) 并行执行。
