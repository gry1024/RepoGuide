# RepoGuide 安装指南

## 在 Claude Code 中安装

```bash
# 将 repoguide/ 目录复制到 Claude Code 的 skills 目录
# Windows:
xcopy /E /I repoguide "%USERPROFILE%\.claude\skills\repoguide"

# macOS/Linux:
cp -r repoguide ~/.claude/skills/
```

或者直接在当前项目中使用：`repoguide/SKILL.md` 会被 Claude Code 自动发现（如果该文件在项目根目录的 `.claude/skills/` 下）。

## 在 Codex 中安装

```bash
# Windows:
xcopy /E /I repoguide "%USERPROFILE%\.codex\skills\repoguide"

# macOS/Linux:
cp -r repoguide ~/.codex/skills/
```

## 在 Kimi Code 中安装

```bash
# Windows:
xcopy /E /I repoguide "%USERPROFILE%\.kimi\skills\repoguide"

# macOS/Linux:
cp -r repoguide ~/.kimi/skills/
```

## 依赖（PDF 生成可选）

- **必装**：
  - Python 3.10+ （detect-stack.py 用）
  - Git （clone GitHub URL 用）
  - Bash （执行 .sh 脚本用）
- **可选**（至少装一个才能生成 PDF）：
  - `pandoc` （推荐，配合 xelatex）
  - `weasyprint` （`pip install weasyprint`）
  - `markdown-pdf` （`pip install markdown-pdf`）

如果都不装，RepoGuide 仍能生成 Markdown 报告，PDF 步骤会优雅跳过并在对话中提示。

## 验证安装

```bash
# 测试 detect-stack 工具
python ~/.claude/skills/repoguide/scripts/detect-stack.py /path/to/any/repo

# 应输出 JSON
```

## 卸载

```bash
rm -rf ~/.claude/skills/repoguide
```
