---
name: repoguide-task-phase-1
description: RepoGuide Phase 1：仓库画像。创建 profiler agent，扫描仓库基础信息并生成 profile.json。
---

# Phase 1: 仓库画像

## 执行方式

创建 **profiler** agent 执行本 Phase。

```
输入: $REPO_PATH
输出: $WORK_DIR/profile.json
```

## 任务

1. 按 `sub-skills/tools/detect-stack.md` 中的方法执行，生成基础画像。
2. 扫描 README、LICENSE、顶层目录结构。
3. 如果仓库内有 PDF/.tex 或 README 含 arxiv 链接，设置 `paper_found=true`。
4. 将完整画像写入 `profile.json`。

## profile.json 必填字段

```json
{
  "repo_path": "...",
  "work_dir": "...",
  "repo_name": "...",
  "primary_language": "...",
  "all_languages": [...],
  "package_managers": [...],
  "entry_points": [...],
  "paper_found": false,
  "paper_path": "..." | null,
  "depth": "standard|deep",
  "file_count_total": 0,
  "file_count_by_ext": {...},
  "module_candidates": [...],
  "core_files_seed": [...]
}
```

## 注意事项

- `depth` 必须来自 Phase 0 的用户确认结果，禁止默认填充。
- `file_count_total` 统计仓库根下所有非忽略文件（不含 `.git/`、依赖目录、构建产物等）。
- `core_files_seed` 为后续 code-analyst 的初始候选集，包含入口文件、配置声明文件、模块入口文件等。

## 下一 Phase

完成后并行进入：
- [phase-2-architect.md](phase-2-architect.md)
- [phase-2-code-analyst.md](phase-2-code-analyst.md)
