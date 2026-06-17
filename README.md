# RepoGuide

一个帮你快速理解任意代码仓库并自动生成分析报告的 Skill。给它一个本地路径或 GitHub URL，它会产出一份自顶向下的 Markdown 报告；如果仓库里放了论文 PDF（或 README 里贴了 arXiv 链接），还会自动加上论文与代码的映射章节。

## 安装

```bash
git clone https://github.com/gry1024/RepoGuide.git
cd RepoGuide
./install.sh                # 安装到 ~/.claude/skills/repoguide/
```

或安装到其他平台 / 项目本地：

```bash
./install.sh --kimi                    # ~/.kimi/skills/repoguide/
./install.sh --codex                   # ~/.codex/skills/repoguide/
./install.sh --project ~/my-project    # ~/my-project/.claude/skills/repoguide/
./install.sh --kimi --project ~/my-project  # ~/my-project/.kimi/skills/repoguide/
```

也可以直接把仓库地址丢给你的 coding agent，agent 会自动完成上述步骤：

```
请从 https://github.com/gry1024/RepoGuide 安装 RepoGuide skill
```

依赖：Python 3.10+、Git、Bash。PDF 由 skill 自动处理，依赖缺失时会自动尝试安装；实在装不上则只出 Markdown。

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
- `<当前目录>/repoguide-report.pdf`（自动从 Markdown 生成，无需额外安装工具）

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
├── install.sh            # 一键安装脚本
├── README.md             # 本文件
├── references/           # 语言特征、分层规则、报告模板
└── scripts/              # detect-stack、clone-if-url、generate-pdf.py
```

## License

MIT
