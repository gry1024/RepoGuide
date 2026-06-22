---
name: repoguide-task-phase-2-architect
description: RepoGuide Phase 2a：架构与数据流分析。创建 architect agent，生成模块依赖图、数据流图、状态点、设计决策和目录树。
---

# Phase 2a: 架构与数据流分析

## 执行方式

创建 **architect** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json
输出: $WORK_DIR/analysis_arch.json
```

## 任务

1. 读取 `profile.json`（注意 `depth` 字段）。
2. 从 `entry_points` 出发，沿 import/include 反向追溯模块依赖。
3. 生成 **mermaid 模块依赖图**（`graph TD` 或 `graph LR`）。
4. 跟踪主要函数调用链，生成 **mermaid 数据流图**。
5. 识别关键状态点（配置加载、初始化、事件触发、IO 边界等）。
6. 推断 3-5 个关键设计决策。
7. 输出 `directory_tree`（见下方格式）。

## 按 depth 调整范围

### standard

- 分析**核心模块依赖**与**主要调用链**。
- 输出**核心目录**的 tree 风格目录树。
- 包含**核心数据流图**（至少 1 张 mermaid 图）。
- 状态点覆盖主要入口和关键状态切换。

### deep

- **面面俱到**：完整模块依赖、完整数据流、完整目录树。
- **所有关键状态点**：配置加载、初始化、事件、IO、错误处理、生命周期节点。
- **每个类/函数的职责与调用关系**：从入口到叶节点的调用链都要覆盖。
- **必须生成以下图表**：
  - 模块依赖图（全量模块/包级别）
  - 数据流图（请求/数据在模块间的完整流转）
  - 调用链图（核心入口到每个关键函数的调用路径）
  - 状态/生命周期图（如适用）
- 目录树为**完整 tree**，每个核心目录/文件附带一句话注释。

## 输出 JSON

```json
{
  "module_dependency_graph": "mermaid string",
  "data_flow_graph": "mermaid string",
  "call_chain_graph": "mermaid string (deep 必填，standard 可选)",
  "state_lifecycle_graph": "mermaid string (如适用)",
  "key_state_points": [
    {"name": "...", "description": "...", "file": "...", "line": 0}
  ],
  "design_decisions": [
    {"decision": "...", "evidence": "file:line", "reasoning": "..."}
  ],
  "directory_tree": "字符串形式的目录树，deep 必填，standard 为核心目录",
  "limitation_notes": []
}
```

## 图表质量要求

- 所有 mermaid 图必须语法正确，可被 `image-handler` 渲染。
- 节点命名清晰，边标注说明数据/调用方向。
- deep 模式下，图应覆盖所有主要模块和关键函数，避免只画"A -> B"的粗粒度图。

## 下一 Phase

本 Phase 与 [phase-2-code-analyst.md](phase-2-code-analyst.md) 并行执行。
