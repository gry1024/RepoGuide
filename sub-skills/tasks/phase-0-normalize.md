---
name: repoguide-task-phase-0
description: RepoGuide Phase 0：输入归一化。主 agent 串行执行，确定仓库、论文、工作目录，并完成仓库克隆/归一化。
---

# Phase 0: 输入归一化

## 执行方式

主 agent **串行**执行本 Phase 所有步骤。

## 步骤

1. 检测 RUNTIME（引用 `sub-skills/runtime/_detect.md`）。
2. 解析用户输入，确定仓库引用和论文引用：**不要先克隆仓库**。
3. **先询问细致度**：列出两档（standard / deep），等待用户明确回复。将结果写入环境变量或临时记录。
4. 确定工作目录：`$WORK_DIR = <cwd>/_repoguide/`，并创建该目录。
5. 调用 `sub-skills/tools/repo-normalizer.md` 归一化仓库路径 → `$REPO_PATH`。
   - 本地路径 / 当前目录：直接使用，不克隆。
   - GitHub URL：默认浅克隆到 `$WORK_DIR/repo/`。
   - 远程模式：使用 GitHub API 读取，写入 `$WORK_DIR/repo/` 和 `$WORK_DIR/github-tree.json`。
6. 如果用户提供了 arXiv 链接，调用 `sub-skills/tools/paper-fetcher.md` 下载论文 → `$WORK_DIR/paper.pdf`。

## 输出

- `$WORK_DIR` 目录已创建。
- `$REPO_PATH` 已确定（本地路径或克隆后的路径）。
- `$WORK_DIR/paper.pdf`（可选）。
- 临时记录中的 `depth` 值（standard 或 deep），将在 Phase 1 写入 `profile.json`。

## 下一 Phase

完成后进入 [phase-1-profiler.md](phase-1-profiler.md)。
