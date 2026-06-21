---
name: repoguide-runtime-codex-subagent
description: Codex 环境下 RepoGuide 使用 native subagents 的语法和协作模式。
---

# RepoGuide · Codex Subagent

## 工具映射

| Claude Code | Codex |
|-------------|-------|
| Bash | shell |
| Read | view |
| Write | write |
| Edit | edit |
| Glob | list_files |
| Grep | grep_files |
| Agent | dispatch_agent |

## 派发方式

Codex 没有独立的 `SendMessage()` 工具，subagent 结果通过返回直接汇报。

向 Codex 发出如下自然语言指令：

```
请并行创建 N 个 subagents 完成以下任务：

1. profiler: 归一化仓库并生成 profile.json
   - 输入：仓库 URL 或路径
   - 输出：$WORK_DIR/profile.json

2. architect: 分析架构与数据流
   - 输入：$WORK_DIR/profile.json
   - 输出：$WORK_DIR/analysis_arch.json

...（其余角色）

每个 subagent 必须独立完成，产物写入指定 JSON 文件。
```

## 约束

- Codex 全自动运行，不向用户提问。
- 所有产物必须落盘到 `$WORK_DIR`（即 `<cwd>/_repoguide/`）。
- 主 agent 负责最后的汇总和 PDF 渲染。
