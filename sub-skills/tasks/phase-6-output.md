---
name: repoguide-task-phase-6
description: RepoGuide Phase 6：输出到用户工作目录。主 agent 串行执行，将产物复制到 <cwd> 并输出摘要。
---

# Phase 6: 输出到用户工作目录

## 执行方式

主 agent **串行**执行本 Phase 所有步骤。

## 步骤

1. 将 `$WORK_DIR/manual.md` 复制到 `<cwd>/<repo_name>-manual.md`。
2. 如果 PDF 生成成功，复制到 `<cwd>/<repo_name>-manual.pdf`。
3. 如果 PDF 未生成但 HTML 已生成，复制到 `<cwd>/<repo_name>-manual.html`。
4. 输出摘要（参考 `_index.md` 中的输出模板）。

## 输出摘要

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

## 结束状态

- 成功：产物已复制到用户工作目录，`_repoguide/` 中间目录默认保留。
- 失败：根据错误类型输出错误信息（参考 `_index.md` 错误处理表）。
