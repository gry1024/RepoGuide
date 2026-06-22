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

1. 读取 Phase 0 已生成的 `$WORK_DIR/profile.json`（如有），获取 `repo_path`、`work_dir`、`analysis_mode` 和 `depth`。
2. 设置环境变量后执行 `sub-skills/tools/detect-stack.md` 中的代码：
   - `WORK_DIR` = `$WORK_DIR`
   - `REPOGUIDE_DEPTH` = `depth`
3. 扫描 README、LICENSE、顶层目录结构，补充元信息。
4. 如果仓库内有 PDF/.tex 或 README 含 arxiv 链接，设置 `paper_found=true`。
5. **合并 profile**：将 Phase 0 的字段（`repo_path`、`work_dir`、`analysis_mode`）与 detect-stack 输出合并，统一写回 `$WORK_DIR/profile.json`。

## profile.json 必填字段

```json
{
  "repo_path": "...",
  "work_dir": "...",
  "analysis_mode": "local|clone|remote",
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
- `work_dir` 由 Phase 0 确定，profiler 必须沿用，不可自行变更。
- `file_count_total` 统计仓库根下所有非忽略文件（不含 `.git/`、依赖目录、构建产物等）。
- `core_files_seed` 为后续 code-analyst 的初始候选集，包含入口文件、配置声明文件、模块入口文件等。
- 最终 `profile.json` 必须包含 Phase 0 的 `analysis_mode` 字段，供 writer/renderer 参考。

## 输出校验

使用 `_index.md` 中的 `validate_json` 校验 `$WORK_DIR/profile.json`：

```python
validate_json(
    "$WORK_DIR/profile.json",
    required_fields=["repo_path", "work_dir", "analysis_mode", "repo_name",
                     "primary_language", "depth", "file_count_total", "core_files_seed"],
    nullable_fields=["paper_path"],
)
```

校验失败时，把错误追加到 `profile.json` 的 `limitation_notes` 中。

## 下一 Phase

完成后并行进入：
- [phase-2-architect.md](phase-2-architect.md)
- [phase-2-code-analyst.md](phase-2-code-analyst.md)
