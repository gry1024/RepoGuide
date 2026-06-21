---
name: repoguide-runtime-claude-team
description: Claude Code 环境下 RepoGuide Agent Team 的具体语法和协作模式。
---

# RepoGuide · Claude Code Agent Team

## Agent 创建

```python
Agent({
    "name": "<agent-name>",
    "prompt": """你是 RepoGuide 的 <角色>。

输入: <路径>
输出: <路径>

任务：
1. ...
2. ...

要求：
- 所有产物写入指定路径
- 不要向用户提问
- 遇到困难在 JSON 的 limitation_notes 中说明
""",
    "description": "<一句话描述>",
})
```

## Agent 间通信

```python
SendMessage({
    "to": "<agent-name>",
    "message": "...",
})
```

## 典型团队

```
coordinator (主 agent)
├── profiler        → $WORK_DIR/profile.json
├── architect       → $WORK_DIR/analysis_arch.json
├── code-analyst    → $WORK_DIR/analysis_code.json
├── paper-analyst   → $WORK_DIR/analysis_paper.json  (可选)
├── paper-mapper    → $WORK_DIR/analysis_map.json    (可选)
├── image-handler   → $WORK_DIR/images/ + $WORK_DIR/image-manifest.json  (可选)
├── writer          → $WORK_DIR/manual.md
└── renderer        → $WORK_DIR/repoguide-manual.pdf (或 .html 降级)
```

所有子 agent 并行创建，各自写产物；coordinator 在最后读取产物、汇总、输出摘要。
