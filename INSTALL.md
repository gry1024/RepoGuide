# RepoGuide 安装指南

## 在 Kimi Code 中安装

```bash
# 把整个仓库内容复制到 Kimi Code skills 目录
# Windows
xcopy /E /I . "%USERPROFILE%\.kimi\skills\repoguide"

# macOS / Linux
cp -r . ~/.kimi/skills/repoguide
```

## 在 Claude Code 中安装

```bash
# Windows
xcopy /E /I . "%USERPROFILE%\.claude\skills\repoguide"

# macOS / Linux
cp -r . ~/.claude/skills/repoguide
```

## 在 Codex 中安装

```bash
# Windows
xcopy /E /I . "%USERPROFILE%\.codex\skills\repoguide"

# macOS / Linux
cp -r . ~/.codex/skills/repoguide
```

## 依赖

- **必装**：Python 3.10+、Git、Bash
- **可选（至少一个才能生成 PDF）**：
  - `pandoc`（推荐，配合 xelatex）
  - `weasyprint`：`pip install weasyprint`
  - `markdown-pdf`：`pip install markdown-pdf`

如果都不装，RepoGuide 仍会生成 Markdown 报告，PDF 步骤会跳过并在对话中提示。

## 验证安装

```bash
python "%USERPROFILE%\.kimi\skills\repoguide\scripts\detect-stack.py" /path/to/any/repo
```

应输出 JSON。
