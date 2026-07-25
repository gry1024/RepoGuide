---
name: repoguide-task-phase-2c-concept-extractor
description: RepoGuide Phase 2c 概念抽取器。从架构、代码、论文分析结果中识别核心概念，生成概念级关系图与教学顺序，解决"代码解析平铺臃肿"问题。
---

# RepoGuide · Phase 2c：概念抽取器

## 触发条件

Phase 2a 与 Phase 2b 均完成（`analysis_arch.json` + `analysis_code.json` 存在且可解析）。与 Phase 2.5 并行执行，不阻塞图片处理。

## 目标

解决"代码详解平铺直叙、把所有文件所有类函数一一列出导致臃肿"的体验问题。从文件级平铺升级为**概念驱动**：先识别 5-12 个核心概念，每个概念关联文件/函数/公式，并给出类比与教学顺序，让读者先建立直觉再深入代码。

## 输入

- `$WORK_DIR/analysis_arch.json`（架构、目录树、数据流、设计决策）
- `$WORK_DIR/analysis_code.json`（核心文件、函数卡片）
- `$WORK_DIR/profile.json`（depth、repo_name）
- `$WORK_DIR/analysis_paper.json`（可选；若 paper_found=true，用于关联公式与算法）

## 输出

`$WORK_DIR/analysis_concepts.json`，schema：

```json
{
  "repo_name": "AlphaSAGE",
  "depth": "deep",
  "concepts": [
    {
      "id": "C1",
      "name": "GFlowNet 生成框架",
      "analogy": "像一个多路探索者，同时派出许多条路径去采样不同的 alpha 公式，而不是只走一条最优路。",
      "summary": "100 字以内中文职责说明，讲清这个概念是什么、解决什么问题。",
      "related_files": ["src/alpha_gfn/gflownet.py", "train_gfn.py"],
      "star_functions": [
        {"function": "EntropyTBGFlowNet.loss", "file": "src/alpha_gfn/gflownet.py", "line": 81, "why_star": "TB 损失核心，直接对应论文公式 L_TB"}
      ],
      "related_formulas": ["L_{TB}(\\tau) = ..."],
      "teaching_order": 3,
      "layer": "core"
    }
  ],
  "concept_relations": [
    {"from": "C1", "to": "C2", "label": "采样状态送入编码", "confidence": "high"}
  ],
  "concept_map_dot": "digraph G { rankdir=LR; ... }",
  "reading_path": ["C3", "C1", "C2", "C4"],
  "limitation_notes": []
}
```

### 字段硬约束

1. `name`：中文名，≤ 12 字，不得含英文整句。
2. `analogy`：一句中文类比，以"像……"开头，≤ 60 字。不得为空。
3. `summary`：100 字以内中文，讲清"是什么 + 解决什么"。
4. `related_files`：≥ 1 个，来自 `analysis_code.json.core_files[*].path`。
5. `star_functions`：每个概念 1-3 个，必须是真正关键的"明星函数"，从 `analysis_code.json` 的 functions 中挑选，附 `why_star` 中文说明（≤ 30 字）。**不得把概念下所有函数都列为明星函数**——明星函数是"读者必须看 key_logic 的少数函数"。
6. `related_formulas`：若有论文，从 `analysis_paper.json.key_formulas` 挑选 LaTeX；无论文则为空数组。
7. `teaching_order`：整数，从 1 开始，由浅入深。数据/配置类概念排前，核心算法居中，评估/输出排后。
8. `layer`：`data`（数据与配置）/ `core`（核心算法与模型）/ `io`（训练入口与评估输出）。
9. `concept_relations`：≥ 概念数-1 条（保证连通），`label` 中文 ≤ 8 字，`confidence` ∈ high/medium/low。
10. `concept_map_dot`：graphviz DOT，rankdir=LR，节点用概念 id+name，边带 label，**不得用 mermaid**。
11. `reading_path`：概念 id 的有序列表，按推荐阅读顺序排列（通常等于 teaching_order 排序，但允许手动调整）。

## 概念数量档位

引用 `references/depth-rules.md`：

| 档位 | 概念数量 | 明星函数总数上限 |
|------|----------|------------------|
| standard | 5-8 | ≤ 16 |
| deep | 8-12 | ≤ 30 |

## 执行步骤

### 步骤 1：读取输入

读取 `analysis_arch.json`、`analysis_code.json`、`profile.json`，若 `profile.paper_found == true` 则读取 `analysis_paper.json`。

### 步骤 2：识别候选概念

从以下来源归纳概念（去重合并）：

1. `analysis_arch.json.design_decisions` 的 `decision` 字段 → 每个设计决策往往对应一个概念。
2. `analysis_code.json.core_files` 的 `one_liner` 聚类 → 职责相近的文件归为一个概念。
3. 若有论文：`analysis_paper.json.core_contributions` → 每条核心贡献通常对应一个概念。
4. `analysis_arch.json.data_flow_table` 的 `module` 列 → 数据流经的模块即概念。

合并规则：名称相近、文件重叠 > 50% 的候选合并为一个概念。

### 步骤 3：挑选明星函数

对每个概念，从其 `related_files` 的 `functions` 中挑选 1-3 个"明星函数"：

- 优先选：论文公式直接对应的函数、训练主循环、损失计算、核心前向传播。
- 排除：纯工具函数（如 `__repr__`、`save`、`load`）、简单 getter/setter。
- `why_star` 必须中文说明"为什么这个函数值得读者看 key_logic"。

### 步骤 4：生成概念关系图 DOT

```dot
digraph G {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fontname="Microsoft YaHei"];
  C1 [label="C1\nGFlowNet 生成框架", fillcolor="#e8f4f8"];
  C2 [label="C2\nRGCN 编码器", fillcolor="#e8f4f8"];
  C1 -> C2 [label="采样状态送入编码"];
}
```

节点 fillcolor 按 layer 分色：data=#fff3e0、core=#e8f4f8、io=#f1f8e9。

### 步骤 5：排序教学顺序

按 layer 优先级（data < core < io）+ 概念间依赖关系排序，写入 `teaching_order`。`reading_path` 通常等于 teaching_order 升序，但若存在"先看核心再看数据"的特殊情况可手动调整。

### 步骤 6：写入与校验

写入 `$WORK_DIR/analysis_concepts.json`，执行校验：

```python
import json
from pathlib import Path
d = json.loads(Path("$WORK_DIR/analysis_concepts.json").read_text(encoding="utf-8"))
assert "concepts" in d and "concept_relations" in d and "concept_map_dot" in d
assert "reading_path" in d
n = len(d["concepts"])
depth = d.get("depth", "standard")
lo, hi = (5, 8) if depth == "standard" else (8, 12)
assert lo <= n <= hi, f"概念数 {n} 不在 {lo}-{hi}"
for c in d["concepts"]:
    assert c.get("analogy"), f"概念 {c.get('name')} 缺少类比"
    assert 1 <= len(c.get("star_functions", [])) <= 3
    assert c.get("teaching_order") and isinstance(c["teaching_order"], int)

# P2-8：id 唯一性
all_ids = [c["id"] for c in d["concepts"]]
assert len(all_ids) == len(set(all_ids)), f"概念 id 重复：{all_ids}"

# P2-8：teaching_order 连续（1..N）
orders = sorted([c["teaching_order"] for c in d["concepts"]])
assert orders == list(range(1, n + 1)), f"teaching_order 不连续：{orders}"

# P2-8：明星函数 file:line 必须在 analysis_code.json 中存在
code = json.loads(Path("$WORK_DIR/analysis_code.json").read_text(encoding="utf-8"))
valid_locs = set()
for cf in code.get("core_files", []):
    for fn in cf.get("functions", []):
        valid_locs.add((cf["path"], fn.get("line", 0)))
    for cls in cf.get("classes", []):
        for m in cls.get("methods", []):
            valid_locs.add((cf["path"], m.get("line", 0)))
for c in d["concepts"]:
    for sf in c.get("star_functions", []):
        loc = (sf.get("file", ""), sf.get("line", 0))
        assert loc in valid_locs, f"明星函数 {sf.get('function','')} 位置 {loc} 不在 analysis_code.json"

# P1-6：关系图连通性收紧——每个概念至少出现在一条关系里（0 个孤立）
ids = {c["id"] for c in d["concepts"]}
involved = set()
for r in d["concept_relations"]:
    involved.add(r["from"]); involved.add(r["to"])
assert ids == involved, f"存在孤立概念：{ids - involved}"

print(f"OK: {n} concepts, {len(d['concept_relations'])} relations, 0 isolated")
```

## 与下游 Phase 的契约

- **Phase 2.5 image-handler**：读取 `concept_map_dot`，渲染 `images/concept_map.png`。
- **Phase 4 writer**：读取 `analysis_concepts.json`，按概念分组重组代码详解（概念导览 → 文件速览表 → 明星函数深入 → 其余函数折叠）。
- **Phase 5 renderer**：HTML 渲染时，deep 模式按概念分页，侧边导航按 `reading_path` 排序。

## 失败降级

- 概念抽取失败：writer 回退到原"按文件平铺"模式，在 `limitation_notes` 记录"概念层缺失，代码详解按文件平铺"。
- 概念数不足下限：放宽至 3 个，记录 limitation。
- `concept_map_dot` 渲染失败（graphviz 不可用）：writer 用关系表格替代图片。
