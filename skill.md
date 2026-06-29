---
name: repoguide
description: 分析代码仓库并生成 Markdown / PDF 仓库手册。用户发送 GitHub 地址或本地路径；论文链接可选，未提供时会扫描仓库元文件自动发现 arXiv 或本地论文文件。本地路径和当前目录无需克隆，GitHub 仓库默认浅克隆到工作目录。本 skill 支持两种触发方式：1) agent 自行下载本仓库后读取 skill.md；2) 用户在 RepoGuide 仓库目录下启动 agent 并直接对话。
version: 2.0.0
---

# RepoGuide · 仓库手册生成 Skill

## 使用方式

直接告诉 AI：

```
下载 https://github.com/gry1024/RepoGuide 并执行这个 skill
分析 https://github.com/owner/repo
```

或带上论文：

```
分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
```

或分析当前目录：

```
分析这个仓库
```

### 分析细致度

执行前 AI 会询问细致度，共 2 档，**不默认推荐任何一档**：

| 档位 | 仓库分析 | 论文分析 | 适用场景 |
|------|----------|----------|----------|
| **标准 (standard)** | 核心模块、注释化目录树、1 张 graphviz 架构总览图、关键文件详解、核心数据流叙述 | 主要章节、公式、算法、术语 | 日常仓库手册 |
| **深度 (deep)** | 所有文件、每个类/函数详解、完整注释化目录树、1 张 graphviz 架构总览图、完整数据流叙述 + 流转表 | 逐章映射、实验-脚本对应、按区域裁剪论文原图 | 论文复现、技术报告 |

指定方式：

```
标准分析 https://github.com/owner/repo
深度分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
```

无论用户是否写明"标准/深度"，Phase 0 都**必须询问细致度**，列出两档并等待用户明确确认后再继续；不得静默默认任何档位。

## 执行架构

```
Phase 0: 输入归一化（主 agent）
Phase 1: 仓库画像（profiler agent）
Phase 2: 并行深度分析（architect + code-analyst agents）
Phase 2.5: 图片处理（image-handler agent，可选）
Phase 3: 论文解析与映射（paper-analyst + paper-code-mapper，可选）
Phase 4: 手册组装（writer agent）
Phase 5: LaTeX PDF 渲染（renderer agent）
Phase 6: 输出到用户工作目录（主 agent）
```

## 环境检测

引用: `sub-skills/runtime/_detect.md`

自动检测当前 AI 环境（Claude Code / Codex / Kimi / Fallback），选择正确的 Agent Team 执行方式。

## 任务详情

引用: `sub-skills/tasks/_index.md`

任务已按 Phase 拆分为多个子任务文件，便于 agent 按部就班执行：

| Phase | 文件 |
|-------|------|
| 任务总览 | `sub-skills/tasks/_index.md` |
| 0: 输入归一化 | `sub-skills/tasks/phase-0-normalize.md` |
| 1: 仓库画像 | `sub-skills/tasks/phase-1-profiler.md` |
| 2a: 架构与数据流 | `sub-skills/tasks/phase-2-architect.md` |
| 2b: 代码详解 | `sub-skills/tasks/phase-2-code-analyst.md` |
| 2.5: 图片处理 | `sub-skills/tasks/phase-2-5-image-handler.md` |
| 3: 论文解析与映射 | `sub-skills/tasks/phase-3-paper.md` |
| 4: 手册组装 | `sub-skills/tasks/phase-4-writer.md` |
| 5: PDF 渲染 | `sub-skills/tasks/phase-5-renderer.md` |
| 6: 输出到用户目录 | `sub-skills/tasks/phase-6-output.md` |

包含完整的输入解析、Agent Team 分工、JSON 输出格式、手册结构、错误处理。

## 工具与模板索引

| 用途 | 文件 |
|------|------|
| 运行时检测 | `sub-skills/runtime/_detect.md` |
| 统一 Agent 创建 | `sub-skills/runtime/create-agent.md` |
| Claude Team | `sub-skills/runtime/claude-team.md` |
| Codex Subagent | `sub-skills/runtime/codex-subagent.md` |
| Kimi Team | `sub-skills/runtime/kimi-team.md` |
| 仓库归一化 | `sub-skills/tools/repo-normalizer.md` |
| 技术栈识别 | `sub-skills/tools/detect-stack.md` |
| 代码分析策略 | `sub-skills/tools/code-analyzer.md` |
| PDF 读取 | `sub-skills/tools/pdf-reader.md` |
| 论文获取 | `sub-skills/tools/paper-fetcher.md` |
| LaTeX 渲染 | `sub-skills/tools/latex-renderer.md` |
| 图像处理 | `sub-skills/tools/image-handler.md` |
| 手册质量验收 | `sub-skills/tools/manual-quality-checker.md` |
| 手册模板 | `references/manual-template.md` |
| 智能分层规则 | `references/depth-rules.md` |
| 语言特征表 | `references/language-profiles.md` |
| LaTeX 模板 | `references/latex-template/main.tex` |

## 输出

假设仓库名为 `<repo_name>`，最终产物为：

- `<cwd>/<repo_name>-manual.pdf`（需要 xelatex）
- `<cwd>/<repo_name>-manual.html`（xelatex 不可用时降级输出）
- `<cwd>/<repo_name>-manual.md`
- `<cwd>/_repoguide/`（中间产物目录，默认保留）

## 核心原则

1. **全中文面向人**: 手册中面向读者的叙述必须为简体中文；代码标识符、命令、专有名词可保留原文。
2. **必须确认细致度**: Phase 0 必须询问 standard / deep，不得静默默认。
3. **论文自动发现**: 未显式提供论文时，先扫描 README、CITATION、docs、paper(s) 等元文件；发现后进入论文-代码联合分析。
4. **注释化目录树优先**: 仓库结构以每行带用途注释的目录树展示；不用树状 mermaid 依赖图。
5. **结构化代码详解**: 类与函数输出签名、职责、参数、返回值和关键逻辑片段。
6. **LaTeX 渲染**: 使用 xelatex 生成中文 PDF；不可用时保留 Markdown 并降级 HTML。
7. **隔离产物**: 中间产物写入 `_repoguide/`，不写入被分析仓库。
