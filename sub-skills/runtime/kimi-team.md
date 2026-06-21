---
name: repoguide-runtime-kimi-team
description: Kimi Code CLI 环境下 RepoGuide Agent Team 的具体语法和协作模式。
---

# RepoGuide · Kimi Team

## Agent 创建

```python
Agent({
    "description": "<一句话描述>",
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
    "subagent_type": "coder",
})
```

## 通信方式

Kimi Agent 的结果直接返回给父代理，不需要 `SendMessage()`。

## 典型团队

与 Claude Code 一致：

```
coordinator
├── profiler
├── architect
├── code-analyst
├── paper-analyst (可选)
├── paper-mapper  (可选)
├── writer
└── renderer
```

## 标注

当运行在 Kimi 串行模式时，在报告元信息中标注：`执行模式：串行（Kimi 环境限制）`。
