---
name: RepoGuide
description: 端到端分析代码仓库，产出五层结构报告（md + pdf）。
activation_keyword: repoguide
version: 0.1.0
---

# RepoGuide (Kimi Code 适配)

> 主版本定义在同目录的 `SKILL.md` 中。本文件仅做平台适配。

## 触发方式

用户输入含 `repoguide` 关键词 + "分析仓库/分析代码" 时激活本 skill。

## 工具能力差异

Kimi Code 工具集与 Claude Code 类似但有差异：

- 支持 `Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep` 等基础工具
- **不支持** `Agent` 工具 → 派 subagent 时降级为：主 agent 串行处理 Subagent A/B/C/D 的工作
- **不支持** `AskUserQuestion` → 全自动模式，不追问

## 行为指令

完全遵循 `SKILL.md` 中 Phase 0/1/2/3 的所有行为。**降级策略**:

- Phase 2 不再并行派 subagent，而是主 agent 串行执行 Subagent A → B → C → D 的工作
- 报告元信息标注 "⚠️ 串行执行模式 (Kimi Code 限制)"

## 错误处理

参考 SKILL.md "错误处理" 节。

## 内置默认策略

参考 SKILL.md "内置默认策略" 节。

## 完成后输出

参考 SKILL.md "完成后输出模板"。
