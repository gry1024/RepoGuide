<p align="center">
  <img src="image/logo.png" alt="RepoGuide Logo" width="180">
</p>

<h1 align="center">RepoGuide</h1>

<p align="center">
  <strong>让 AI 直接读懂任意代码仓库，自动生成 PDF 仓库手册指南</strong>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#特点">特点</a> ·
  <a href="#仓库结构">仓库结构</a> ·
  <a href="#输出示例">输出示例</a>
</p>

---

## 快速开始

对 Claude Code / Codex / Kimi Code 说：

```
repoguide 分析 https://github.com/owner/repo
```

推荐带上论文链接：

```
repoguide 分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
```

agent 会自行读取 [skill.md](skill.md)，并行调用多个 subagent 完成仓库画像、架构分析、代码解读、论文解析与 PDF 渲染。

> 执行前 agent 会主动询问分析细致度（快速 / 标准 / 深度）。

---

## AI 会自动完成

1. 获取仓库（GitHub URL 默认浅克隆，本地路径 / 当前目录无需克隆）
2. 识别技术栈
3. 分析架构与数据流
4. 详解核心代码
5. 解析论文（如果有）
6. 建立论文-代码映射
7. 处理论文 / 仓库图片与生成架构图
8. 用 xelatex 渲染 PDF 仓库手册（不可用时降级为 HTML）

## 最终产物

假设仓库名为 `<repo_name>`：

- `<当前目录>/<repo_name>-manual.pdf`（需要 xelatex）
- `<当前目录>/<repo_name>-manual.html`（xelatex 不可用时降级）
- `<当前目录>/<repo_name>-manual.md`
- `<当前目录>/_repoguide/`（中间产物目录，默认保留）

---

## 特点

- **零学习成本**：不需要记命令，直接自然语言对话
- **Agent Team 模式**：多个 subagent 并行分析
- **自动论文解析**：支持 arXiv 链接与本地 PDF
- **LaTeX 精美 PDF**：使用 xelatex + ctex 中文模板
- **跨平台**：自动适配 Claude Code / Codex / Kimi Code
- **纯 Markdown**：无脚本，无 CLI，所有逻辑以代码片段写在 md 中

---

## 仓库结构

```
├── skill.md                    # 主 skill（唯一入口）
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

---

## 输出示例

以 `AlphaSAGE` 仓库为例，最终产物包括：

```
.
├── AlphaSAGE-manual.md
├── AlphaSAGE-manual.pdf
└── _repoguide/
    ├── repo/                   # 被分析仓库代码
    ├── paper.pdf               # 论文（可选）
    ├── images/                 # 论文/架构图
    ├── profile.json            # 仓库画像
    ├── analysis_arch.json      # 架构分析
    ├── analysis_code.json      # 代码分析
    └── analysis_paper.json     # 论文分析（可选）
```

---

## License

MIT
