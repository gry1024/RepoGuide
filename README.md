<p align="center">
  <strong>RepoGuide</strong>
</p>

<p align="center">
  让 AI 直接读懂任意代码仓库，自动生成 PDF 仓库手册指南
</p>

---

## 快速开始

### 1. 安装 skill

RepoGuide 需要被安装到 AI agent 的 skills 目录后，才能通过 `repoguide` 触发。**仅仅把仓库 clone 到本地是不够的**，agent 默认从 `~/.claude/skills/repoguide/` 加载。

```bash
# 下载仓库
git clone https://github.com/gry1024/RepoGuide.git
cd RepoGuide

# 安装到 Claude Code（默认）
./install.sh

# 或安装到 Codex / Kimi Code
./install.sh --codex
./install.sh --kimi
```

安装后，skill 文件会被复制到 `~/.claude/skills/repoguide/`。

### 2. 更新 skill

**每次 `git pull` 更新仓库后，必须重新运行 `./install.sh`**，否则 agent 仍然使用旧版本。

```bash
cd RepoGuide
git pull
./install.sh
```

### 3. 使用

打开任意 AI coding agent，直接说：

```
分析 https://github.com/owner/repo
```

带上论文链接（可选）：

```
分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
```

指定细致度（可选）：

```
快速分析 https://github.com/owner/repo
深度分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
```

AI 会自动完成：

1. 获取仓库（GitHub URL 默认浅克隆，本地路径/当前目录无需克隆）
2. 识别技术栈
3. 分析架构与数据流
4. 详解核心代码
5. 解析论文（如果有）
6. 建立论文-代码映射
7. 处理论文/仓库图片与生成架构图（可选）
8. 用 xelatex 渲染 PDF 仓库手册（不可用时降级为 HTML）

最终产物（假设仓库名为 `<repo_name>`）：

- `<当前目录>/<repo_name>-manual.pdf`（需要 xelatex）
- `<当前目录>/<repo_name>-manual.html`（xelatex 不可用时降级）
- `<当前目录>/<repo_name>-manual.md`
- `<当前目录>/_repoguide/`（中间产物目录，默认保留）

## 特点

- **零学习成本**: 不需要记命令，直接自然语言对话
- **Agent Team 模式**: 多个 subagent 并行分析
- **自动论文解析**: 支持 arXiv 链接与本地 PDF
- **LaTeX 精美 PDF**: 使用 xelatex + ctex 中文模板
- **跨平台**: 自动适配 Claude Code / Codex / Kimi Code
- **纯 Markdown**: 无脚本，无 CLI，所有逻辑以代码片段写在 md 中

## 仓库结构

```
├── skill.md                    # 主 skill（唯一入口）
├── install.sh                  # 传统安装脚本（可选）
├── README.md                   # 本文件
├── sub-skills/                 # skill 子模块
│   ├── runtime/                # 运行时与 Agent Team
│   ├── tasks/                  # 任务流程
│   └── tools/                  # 工具方法（纯代码片段）
└── references/                 # 模板与规则
    ├── manual-template.md      # 仓库手册 Markdown 模板
    ├── depth-rules.md          # 智能分层规则
    ├── language-profiles.md    # 语言特征表
    └── latex-template/         # LaTeX PDF 模板
```

## License

MIT
