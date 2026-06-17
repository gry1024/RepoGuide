# RepoGuide

一个帮你快速理解任意代码仓库并自动生成分析报告的 Skill。给它一个本地路径或 GitHub URL，它会产出一份自顶向下的 Markdown 报告；如果仓库里放了论文 PDF（或 README 里贴了 arXiv 链接），还会自动加上论文与代码的映射章节。

## 安装

把本仓库内容复制到对应 agent 的 skills 目录：

```bash
# Kimi Code
xcopy /E /I . %USERPROFILE%\.kimi\skills\repoguide

# Claude Code
xcopy /E /I . %USERPROFILE%\.claude\skills\repoguide

# Codex
xcopy /E /I . %USERPROFILE%\.codex\skills\repoguide
```

依赖：Python 3.10+、Git、Bash。PDF 需要 pandoc/weasyprint/markdown-pdf 之一，不装则只出 Markdown。

## 使用

在目标仓库目录下说：

```
使用 RepoGuide skill 帮我分析仓库结构
```

或显式指定路径 / URL：

```
使用 RepoGuide skill 分析 /path/to/repo
使用 RepoGuide skill 分析 https://github.com/owner/repo
```

输出产物：

- `<当前目录>/repoguide-report.md`
- `<当前目录>/repoguide-report.pdf`（如果装了 PDF 工具）

## 报告结构

0. 元信息（语言、文件数、论文检测）
1. 一句话总括 + 快速上手
2. 技术栈与依赖
3. 架构与数据流
4. 核心代码详解
5. 论文-代码映射（检测到论文时自动出现）

## 仓库结构

```
├── SKILL.md              # Claude Code 主版本
├── SKILL.codex.md        # Codex 适配
├── SKILL.kimi.md         # Kimi Code 适配
├── INSTALL.md            # 安装细节
├── references/           # 语言特征、分层规则、报告模板
└── scripts/              # detect-stack、clone-if-url、generate-pdf
```

## License

MIT
