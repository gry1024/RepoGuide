---
name: repoguide-tasks-index
description: RepoGuide 任务总览。定义触发条件、输入解析、细致度档位、工作目录、整体流程、错误处理与输出模板。各 Phase 的具体实现见同目录 phase-*.md。
---

# RepoGuide · 任务总览

## 触发条件

用户输入包含以下任一形式：

```
分析 https://github.com/owner/repo
标准分析 https://github.com/owner/repo
深度分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
分析这个仓库
分析 /path/to/repo
分析 <GitHub URL>，论文 https://arxiv.org/abs/xxxx.xxxxx
```

## 输入解析

1. 提取 GitHub URL（匹配 `https?://github\.[\w.-]+/[\w.-]+`）。
2. 提取 arXiv 链接（匹配 `https?://arxiv\.(?:org|pdf)/[\d.]+` 或本地 PDF/.tex 路径）。
3. 如果没有 URL 但有本地路径，使用本地路径。
4. 如果都没有，使用当前工作目录（必须是 git 仓库根）。
5. 如果无法确定 → 终止并报错，不追问。

## 分析细致度（执行前必须询问）

**主 agent 在 Phase 0 必须先向用户确认细致度，收到明确回复后再继续。** 即使输入含"标准/深度"字样，也应列出两档并让用户确认。

```
检测到仓库 <repo> 与论文 <arxiv>。
请选择分析细致度：
1) 标准 (standard) - 核心模块 + 架构图 + 关键文件 + tree 风格目录树（核心目录） + 核心数据流 + 论文主要章节
2) 深度 (deep)   - 面面俱到：所有文件、每个类/函数、完整目录树、完整数据流（含图）、论文逐章映射、原图提取
```

用户回复档位后，写入 `$WORK_DIR/profile.json` 的 `"depth": "standard|deep"`。

| 档位 | 仓库分析 | 论文分析 | 输出重点 |
|------|----------|----------|----------|
| **standard** | 核心模块、架构图、关键文件、**tree 风格目录树（核心目录）**、核心数据流 | 主要章节、公式、算法、术语 | 有图、有结构、有重点代码 |
| **deep** | **所有文件**、每个类/函数、完整依赖链、**完整 tree 目录树**、完整数据流（模块依赖图 + 数据流图 + 状态/调用链图） | 逐章映射、实验-脚本对应、提取论文原图 | 面面俱到 |

**不默认推荐任何一档**，由用户根据场景自行选择。

## 工作目录

所有中间产物统一写入用户当前工作目录下的 `_repoguide/`，不写入被分析仓库内部：

```
<cwd>/_repoguide/
├── repo/                    (GitHub URL 克隆到此，本地路径时不存在)
├── profile.json
├── analysis_arch.json
├── analysis_code.json
├── analysis_paper.json      (可选)
├── analysis_map.json        (可选)
├── image-manifest.json      (可选)
├── images/                  (可选)
├── paper.pdf                (可选)
├── manual.md
├── <repo_name>-manual.pdf   (如 xelatex 可用)
└── <repo_name>-manual.html  (xelatex 不可用时降级)
```

最终手册复制到用户当前工作目录：

```
<cwd>/<repo_name>-manual.md
<cwd>/<repo_name>-manual.pdf   (如 xelatex 可用)
<cwd>/<repo_name>-manual.html  (xelatex 不可用时降级)
```

## 执行流程

按顺序执行，可并行的 Phase 已在对应文件中说明：

| Phase | 文件 | 负责 agent | 关键产物 |
|-------|------|-----------|----------|
| 0 | [phase-0-normalize.md](phase-0-normalize.md) | 主 agent | `$WORK_DIR`, `$REPO_PATH`, `paper.pdf` |
| 1 | [phase-1-profiler.md](phase-1-profiler.md) | profiler | `profile.json` |
| 2a | [phase-2-architect.md](phase-2-architect.md) | architect | `analysis_arch.json` |
| 2b | [phase-2-code-analyst.md](phase-2-code-analyst.md) | code-analyst | `analysis_code.json` |
| 2.5 | [phase-2-5-image-handler.md](phase-2-5-image-handler.md) | image-handler | `images/`, `image-manifest.json` |
| 3 | [phase-3-paper.md](phase-3-paper.md) | paper-analyst + paper-code-mapper | `analysis_paper.json`, `analysis_map.json` |
| 4 | [phase-4-writer.md](phase-4-writer.md) | writer | `manual.md` |
| 5 | [phase-5-renderer.md](phase-5-renderer.md) | renderer | `<repo_name>-manual.pdf/html` |
| 6 | [phase-6-output.md](phase-6-output.md) | 主 agent | 用户工作目录产物 |

## 进度反馈

- `📋 Phase 0/6: 输入归一化...`
- `🤖 创建 profiler agent...`
- `🤖 并行创建 architect / code-analyst...`
- `🤖 创建 image-handler...` (可选)
- `🤖 创建 paper-analyst / paper-code-mapper...` (可选)
- `🤖 创建 writer agent...`
- `🤖 创建 renderer agent...`
- `✅ Done in <duration>`

## 错误处理

| 错误 | 处理 |
|------|------|
| 仓库 URL 失效 / 为空 | 立即终止，无手册 |
| 单文件分析失败 | 跳过，写入对应 `limitation_notes` |
| 论文 PDF 损坏 / 无法解析 | 跳过第 5 层 |
| xelatex 不可用 | 保留 Markdown 并降级渲染 HTML，提示用户 |
| Agent 工具不可用 | 主 agent 串行执行各 phase |

## 输出模板

```
✅ RepoGuide 仓库手册生成完成

📊 统计:
- 仓库: <repo_name>
- 主语言: <primary_language>
- 文件总数: <file_count_total>
- 论文: <found|not found>
- 执行模式: <claude-team|kimi-team|codex-subagent|serial>
- 总耗时: <duration>

📄 产物文件:
- Markdown: <absolute path>/<repo_name>-manual.md
- PDF: <absolute path>/<repo_name>-manual.pdf (如 xelatex 可用)
- HTML: <absolute path>/<repo_name>-manual.html (xelatex 不可用时降级生成)

🎯 一句话总结: <从第 1 层提取>
```
