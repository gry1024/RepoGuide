---
name: repoguide-task-phase-3
description: RepoGuide Phase 3：论文解析与映射。仅当 paper_found == true 时执行。公式以 LaTeX 提取，叙述全中文。
---

# Phase 3: 论文解析与映射

## 执行方式

仅当 `profile.json.paper_found == true` 时执行。

引用 `sub-skills/tools/pdf-reader.md`。

并行创建两个 agents：
- **paper-analyst**
- **paper-code-mapper**（依赖 paper-analyst 输出，可在其完成后执行）

## paper-analyst

```
输入: $WORK_DIR/profile.json + $WORK_DIR/paper.pdf
输出: $WORK_DIR/analysis_paper.json
```

### 任务

1. 读取 `paper_path`（PDF 或 .tex）。
2. 提取标题、作者、摘要、核心贡献（**全中文叙述**）。
3. 提取章节结构（最多 5 级）。
4. 提取关键公式：**以原始 LaTeX 写入 `latex` 字段**（不要转义 `$`、`^`、`_`），`meaning` 字段中文解释。
5. 提取关键算法伪代码（中文说明）。
6. 提取关键术语表（`term` 原文，`description` 中文）。

### 输出 JSON

```json
{
  "title": "论文标题（原文）",
  "authors": [...],
  "abstract": "中文摘要",
  "core_contributions": ["中文贡献点"],
  "section_tree": [{"level": 1, "title": "章节标题"}],
  "key_formulas": [
    {"latex": "R_{total}=\\sum_{t} r_t + \\lambda \\cdot novel(s_t)", "meaning": "中文解释"}
  ],
  "key_algorithms": [{"name": "...", "pseudocode": "..."}],
  "glossary": [{"term": "GFlowNet", "description": "生成式流网络"}],
  "limitation_notes": []
}
```

**公式硬约束**：`key_formulas[*].latex` 必须是可被 LaTeX 直接渲染的原始内容（含 `^`、`_`、`\sum` 等），不得把 `\` 转义为 `\\`，不得包裹 `$`。writer 会以 `$$...$$` 包裹。

## paper-code-mapper

```
输入: $WORK_DIR/analysis_paper.json + analysis_code.json
输出: $WORK_DIR/analysis_map.json
```

### 任务

1. 读取论文解析与代码分析结果。
2. 生成三层映射（置信度 high/medium/low）：
   - 层级 1：论文章节 ↔ 代码模块
   - 层级 2：论文公式/算法 ↔ 代码函数/类（含 file:line）
   - 层级 3：论文实验/表格 ↔ 评估脚本
3. 术语-代码标识符对照。

### 输出 JSON

```json
{
  "layer1_section_to_module": [{"section":"...","module":"...","confidence":"high"}],
  "layer2_formula_to_function": [{"formula":"...","function":"...","file":"...","line":0,"confidence":"medium"}],
  "layer3_experiment_to_script": [{"experiment":"...","script":"...","file":"..."}],
  "glossary_mapping": [{"term":"GFlowNet","code_identifier":"GFlowNet"}],
  "limitation_notes": []
}
```

## 输出校验

```python
validate_json("$WORK_DIR/analysis_paper.json",
    required_fields=["title","authors","abstract","core_contributions","section_tree",
                     "key_formulas","key_algorithms","glossary","limitation_notes"])
validate_json("$WORK_DIR/analysis_map.json",
    required_fields=["layer1_section_to_module","layer2_formula_to_function",
                     "layer3_experiment_to_script","glossary_mapping","limitation_notes"])
```

## 下一 Phase

完成后进入 [phase-4-writer.md](phase-4-writer.md)。
