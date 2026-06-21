<p align="center">
  <strong>RepoGuide</strong>
</p>

<p align="center">
  让 AI 直接读懂任意代码仓库，自动生成 PDF 仓库手册指南
</p>

---

## 快速开始

打开任意 AI coding agent（Claude Code / Codex / Kimi Code），直接说：

```
下载 https://github.com/gry1024/RepoGuide，并执行这个 skill
分析 https://github.com/owner/repo
```

带上论文链接（可选）：

```
分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
```

AI 会自动完成：

1. 克隆仓库
2. 识别技术栈
3. 分析架构与数据流
4. 详解核心代码
5. 解析论文（如果有）
6. 建立论文-代码映射
7. 用 xelatex 渲染 PDF 仓库手册

最终产物：

- `<当前目录>/repoguide-manual.pdf`
- `<当前目录>/repoguide-manual.md`

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

## 可选安装

如果你想把 skill 安装到 agent 的 skills 目录：

```bash
./install.sh              # Claude Code
./install.sh --codex      # Codex
./install.sh --kimi       # Kimi Code
```

## License

MIT
