---
name: repoguide
description: |
  [Codex 适配] 端到端分析任意代码仓库，产出五层结构 Markdown + PDF 报告。
  使用方式: 引用 `repoguide` skill 后说"分析 <仓库路径或 URL>"。
  本文件是 SKILL.md 在 Codex 平台上的适配版本，行为完全一致。
version: 0.1.0
allowed-tools: shell, view, write, edit, list_files, grep_files, dispatch_agent
---

# RepoGuide (Codex 适配)

> 主版本定义在同目录的 `SKILL.md` 中。本文件仅做平台适配。

## 工具名映射

| Claude Code | Codex | 用途 |
|-------------|-------|------|
| Bash | shell | 执行 shell 命令 |
| Read | view | 读取文件 |
| Write | write | 写文件 |
| Edit | edit | 编辑文件 |
| Glob | list_files | 列出匹配文件 |
| Grep | grep_files | 搜索文件内容 |
| Agent | dispatch_agent | 派 subagent |
| AskUserQuestion | (禁用) | 永远不要派发 |

## 触发条件

参考 SKILL.md "触发条件" 节。本 skill 在 Codex 上**全自动**运行，不向用户追问任何问题（Codex 没有等效的 AskUserQuestion 工具）。

## 行为指令

完全遵循 `SKILL.md` 中 Phase 0/1/2/3 的所有行为。**特别注意**:

- 用 `view` 替代 `Read`
- 用 `shell` 跑命令
- 用 `dispatch_agent` 派 subagent 时使用 `agent_type="general"`（Codex 等价物）
- 派发 4 个 subagent 时**必须在同一条消息中并行派发**

## 错误处理

参考 SKILL.md "错误处理" 节。

## 内置默认策略

参考 SKILL.md "内置默认策略" 节。

## 完成后输出

参考 SKILL.md "完成后输出模板"。
