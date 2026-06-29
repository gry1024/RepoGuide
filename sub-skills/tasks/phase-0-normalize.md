---
name: repoguide-task-phase-0
description: RepoGuide Phase 0：输入归一化。主 agent 串行执行，确定仓库、论文、工作目录，并完成仓库克隆/归一化。
---

# Phase 0: 输入归一化

## 执行方式

主 agent **串行**执行本 Phase 所有步骤。

## 步骤

1. 检测 RUNTIME（引用 `sub-skills/runtime/_detect.md`）。
2. 解析用户输入，确定仓库引用和显式论文引用：**不要先克隆仓库**。
3. **先询问细致度**：列出两档（standard / deep），等待用户明确回复。将结果写入环境变量或临时记录。
4. 确定工作目录：`$WORK_DIR = <cwd>/_repoguide/`，并创建该目录。
5. 调用 `sub-skills/tools/repo-normalizer.md` 归一化仓库路径 → `$REPO_PATH`。
   - 本地路径 / 当前目录：直接使用，不克隆。
   - GitHub URL：默认浅克隆到 `$WORK_DIR/repo/`。
   - 远程模式：使用 GitHub API 读取，写入 `$WORK_DIR/repo/` 和 `$WORK_DIR/github-tree.json`。
   - 执行前设置环境变量 `REPO_REF` 为原始仓库引用（URL 或路径），`repo-normalizer` 会从中解析 `repo_name`。
   - 同时把 `repo_path`、`work_dir`、`analysis_mode`、`repo_name` 写入 `$WORK_DIR/profile.json`（初步）。
6. 处理论文输入（调用 `sub-skills/tools/paper-fetcher.md`）：
   - 用户显式提供论文链接 / PDF / .tex：直接获取到 `$WORK_DIR/paper.pdf` 或记录本地 .tex。
   - 用户未显式提供论文：在 `$REPO_PATH` 中扫描 README、CITATION、docs、paper(s) 等元文件；若发现 arXiv 或本地论文文件，同样获取并写入 profile。
   - 未发现论文：在 profile 中写入 `paper_found: false`, `paper_path: null`, `paper_ref: null`。
7. 若获取到论文，在 `$WORK_DIR/profile.json` 写入 `paper_found: true`, `paper_ref`, `paper_path`, `paper_source`，后续 Phase 3 自动进入论文-代码联合分析。

## 输出

- `$WORK_DIR` 目录已创建。
- `$REPO_PATH` 已确定（本地路径或克隆后的路径）。
- `$WORK_DIR/profile.json`（初步，含 `repo_path`、`work_dir`、`analysis_mode`、`repo_name`，供 Phase 1 合并）。
- `$WORK_DIR/paper.pdf` 或本地 `.tex` 路径（可选）。
- 临时记录中的 `depth` 值（standard 或 deep），将在 Phase 1 写入 `profile.json`。

## 下一 Phase

完成后进入 [phase-1-profiler.md](phase-1-profiler.md)。
