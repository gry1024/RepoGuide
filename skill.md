---
name: repoguide
description: 端到端分析代码仓库并生成精美 PDF 仓库手册指南。用户只需发送 GitHub 地址和可选 arXiv 论文链接，AI 自动完成仓库获取、分析、论文解析、代码映射、LaTeX 渲染全流程。本地路径和当前目录无需克隆，GitHub 仓库默认浅克隆到工作目录。在 cc/codex/kimi 中说"分析 https://github.com/owner/repo"或"分析这个仓库"即可触发。
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

执行前 AI 会询问细致度，共 3 档：

| 档位 | 仓库分析 | 论文分析 | 适用场景 |
|------|----------|----------|----------|
| **快速 (fast)** | 仅 README、顶层结构、入口文件 | 仅摘要与核心贡献 | 快速了解项目概貌 |
| **标准 (standard)** | 核心模块、架构图、关键文件 | 主要章节、公式、算法、术语 | 日常仓库手册（默认） |
| **深度 (deep)** | 全量核心代码、依赖链、目录树 | 逐章映射、实验-脚本对应、图片提取 | 论文复现、技术报告 |

指定方式：

```
快速分析 https://github.com/owner/repo
深度分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
```

未指定时默认使用 **标准** 档位。

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

引用: `sub-skills/tasks/analyze-repo.md`

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

1. **零学习成本**: 用户只需发送仓库地址，AI 完成所有步骤。
2. **Agent Team**: 多 agent 并行分析，提升质量与速度。
3. **自然语言驱动**: 不使用 CLI，全部通过对话触发。
4. **LaTeX 渲染**: 使用 xelatex 生成美观的中文 PDF 仓库手册。
5. **优雅降级**: 任一环节失败不影响最终手册产出。
