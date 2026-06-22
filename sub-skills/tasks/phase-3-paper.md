---
name: repoguide-task-phase-3
description: RepoGuide Phase 3：论文解析与映射。创建 paper-analyst 和 paper-code-mapper agents，仅当 profile.json.paper_found == true 时执行。
---

# Phase 3: 论文解析与映射

## 执行方式

仅当 `profile.json.paper_found == true` 时执行。

引用 `sub-skills/tools/pdf-reader.md`。

并行创建两个 agents：
- **paper-analyst**
- **paper-code-mapper**（依赖 paper-analyst 的输出，可在 paper-analyst 完成后执行）

## paper-analyst

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_paper.json
```

### 任务

1. 读取 `paper_path`（PDF 或 .tex）。
2. 提取标题、作者、摘要、核心贡献。
3. 提取章节结构（最多 5 级）。
4. 提取关键公式（LaTeX）和算法伪代码。
5. 提取关键术语表。

### 输出 JSON

```json
{
  "title": "...",
  "authors": [...],
  "abstract": "...",
  "core_contributions": [...],
  "section_tree": [
    {"level": 1, "title": "..."}
  ],
  "key_formulas": [
    {"latex": "...", "meaning": "..."}
  ],
  "key_algorithms": [
    {"name": "...", "pseudocode": "..."}
  ],
  "glossary": [
    {"term": "...", "description": "..."}
  ],
  "limitation_notes": []
}
```

## paper-code-mapper

```
输入: $WORK_DIR/analysis_paper.json + analysis_code.json
输出: $WORK_DIR/analysis_map.json
```

### 任务

1. 读取论文解析结果和代码分析结果。
2. 生成三层映射：
   - 层级 1: 论文章节 ↔ 代码模块
   - 层级 2: 论文公式/算法 ↔ 代码函数/类
   - 层级 3: 论文实验/表格 ↔ 评估脚本
3. 标注置信度。

### 输出 JSON

```json
{
  "layer1_section_to_module": [
    {"section": "...", "module": "...", "confidence": "high|medium|low"}
  ],
  "layer2_formula_to_function": [
    {"formula": "...", "function": "...", "file": "...", "line": 0, "confidence": "..."}
  ],
  "layer3_experiment_to_script": [
    {"experiment": "...", "script": "...", "file": "..."}
  ],
  "glossary_mapping": [
    {"term": "...", "code_identifier": "..."}
  ],
  "limitation_notes": []
}
```

## 下一 Phase

完成后进入 [phase-4-writer.md](phase-4-writer.md)。
