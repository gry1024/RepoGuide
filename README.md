# RepoGuide

一个 Kimi / Claude / Codex 通用的 Skill：给它一个本地仓库路径或 GitHub URL，自动生成一份自顶向下的代码分析报告（Markdown + 可选 PDF）。

报告分五层：元信息、快速上手、技术栈、架构与数据流、核心代码详解；如果仓库里有论文 PDF，还会加上论文-代码映射。

## 安装

复制 `repoguide/` 到对应 agent 的 skills 目录：

```bash
# Kimi Code（当前环境）
mkdir -p ~/.kimi/skills
xcopy /E /I repoguide %USERPROFILE%\.kimi\skills\repoguide

# Claude Code
xcopy /E /I repoguide %USERPROFILE%\.claude\skills\repoguide

# Codex
xcopy /E /I repoguide %USERPROFILE%\.codex\skills\repoguide
```

依赖：Python 3.10+、Git、Bash。PDF 需要 pandoc/weasyprint/markdown-pdf 之一，不装则只出 Markdown。

## 使用

在任意仓库目录下说：

```
使用 RepoGuide skill 帮我分析仓库结构
```

或显式给路径 / URL：

```
使用 RepoGuide skill 分析 /path/to/repo
使用 RepoGuide skill 分析 https://github.com/owner/repo
```

输出产物：

- `<当前目录>/repoguide-report.md`
- `<当前目录>/repoguide-report.pdf`（如果装了 PDF 工具）

## 测试

```bash
# 单元测试
python -m pytest tests/unit/test_detect_stack.py -v
bash tests/unit/test_clone_if_url.sh
bash tests/unit/test_generate_pdf.sh

# 集成测试
bash tests/integration/test_e2e.sh
```

## 结构

```
repoguide/
├── SKILL.md              # Claude Code 主版本
├── SKILL.codex.md        # Codex 适配
├── SKILL.kimi.md         # Kimi Code 适配
├── references/           # 语言特征、分层规则、报告模板
└── scripts/              # detect-stack、clone-if-url、generate-pdf
```

## License

MIT
