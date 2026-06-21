---
name: repoguide-runtime-create-agent
description: RepoGuide 统一的跨平台 Agent 创建接口，根据检测到的运行时环境自动选择 Claude/Codex/Kimi/串行执行方式。
---

# RepoGuide · 统一 Agent 创建接口

## 接口语义

所有需要并行或派生 subagent 的地方，都按以下语义描述：

```
为以下每个任务创建专属 agent 并行执行：
- 任务 1: ...
- 任务 2: ...

Agent 模板：
"""
你是 <角色>，负责 <任务>。
输入：...
输出：...
要求：...
"""
```

具体语法由运行时环境决定。

## Claude Code

```python
for task in task_list:
    Agent({
        "name": task["name"],
        "prompt": task["prompt"],
        "description": task.get("description", ""),
    })
```

- Agent 之间通过 `SendMessage()` 通信。
- 多个 Agent 必须在同一条消息里并行派发。

## Kimi Code CLI

```python
for task in task_list:
    Agent({
        "description": task.get("description", ""),
        "prompt": task["prompt"],
        "subagent_type": task.get("subagent_type", "coder"),
    })
```

- Agent 结果直接返回给父代理，无需 `SendMessage()`。
- 多个 Agent 可以并行派发。

## Codex

使用自然语言向 Codex 描述并行 subagent 任务：

```
请为以下任务并行创建 subagents：

1. <任务1描述>
2. <任务2描述>

每个 subagent 使用对应的 prompt 模板执行。
```

## Fallback

如果环境不支持 Agent 工具，主 agent 串行执行每个任务：

```
按顺序完成任务 1 → 任务 2 → ...
每个任务使用同样的 prompt 模板，但由主 agent 自己执行。
```

## 注意事项

1. 不要直接调用本接口，而是在 task skill 中通过自然语言引用。
2. 每个 agent 的 prompt 必须包含：输入路径、输出路径、任务要求、输出格式。
3. 所有 agent 的产物必须写到约定的 `_repoguide/` 工作目录下，方便主 agent 汇总。
