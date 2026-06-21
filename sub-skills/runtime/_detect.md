---
name: repoguide-runtime-detect
description: 检测当前运行的 AI 环境（Claude Code / Codex / Kimi / Fallback），为 RepoGuide 选择正确的 Agent Team 执行方式。
---

# RepoGuide · 运行时环境检测

## 检测逻辑

在 skill 执行开始时运行：

```python
import os
import shutil

if os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") or os.environ.get("CLAUDE_CODE") == "1":
    RUNTIME = "claude"
elif os.environ.get("CODEX") == "1":
    RUNTIME = "codex"
elif os.environ.get("KIMI_CODE_CLI") == "1" or os.environ.get("KIMI") == "1" or shutil.which("kimi"):
    RUNTIME = "kimi"
else:
    RUNTIME = "fallback"
```

## 环境特征

| 环境 | 检测方式 | Agent 语法 | 通信方式 |
|------|----------|------------|----------|
| Claude Code | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 或 `CLAUDE_CODE=1` | `Agent({...})` | `SendMessage()` |
| Codex | `CODEX=1` | `dispatch_agent` / native subagent | 自然语言并行描述 |
| Kimi Code CLI | `KIMI_CODE_CLI=1` 或 `which kimi` | `Agent({...})` | Agent 结果直接返回 |
| Fallback | 以上都不满足 | 主 agent 串行执行 | 无 |

## 使用方式

1. 主 skill 先检测 RUNTIME。
2. 后续所有创建 Agent 的地方都引用 `sub-skills/runtime/create-agent.md`。
3. 如果 RUNTIME 是 `fallback`，在主 agent 内部串行完成各 subagent 的任务，并在报告元信息中标注 `执行模式: 串行（环境限制）`。
