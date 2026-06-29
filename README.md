<p align="center">
  <img src="image/logo.png" alt="RepoGuide Logo" width="180">
</p>

<h1 align="center">RepoGuide</h1>

<p align="center">
  <strong>分析代码仓库，生成 Markdown / PDF 仓库手册</strong>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#特点">特点</a> ·
  <a href="#仓库结构">仓库结构</a> 
</p>

---

## 快速开始

对 Claude Code / Codex / Kimi Code 说：

```
repoguide 分析 https://github.com/owner/repo
```

可带论文链接：

```
repoguide 分析 https://github.com/owner/repo，论文 https://arxiv.org/abs/xxxx.xxxxx
```

如果未提供论文链接，RepoGuide 会先扫描仓库 README、CITATION、docs、paper(s) 等元文件；发现 arXiv 或本地论文文件后自动进入论文-代码联合分析。

agent 会读取 [skill.md](skill.md)，调用 subagent 完成仓库画像、架构分析、代码解读、论文解析与 PDF 渲染。

> 执行前 agent 会主动询问分析细致度（标准 / 深度）。

---

## AI 会自动完成

1. 获取仓库（GitHub URL 默认浅克隆，本地路径 / 当前目录无需克隆）
2. 识别技术栈
3. 分析架构与数据流
4. 详解核心代码
5. 发现并解析论文（如果显式提供，或仓库元文件中可发现）
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

- **自然语言触发**：直接给仓库地址或本地路径
- **Agent Team**：多个 subagent 并行分析
- **论文联合分析**：支持显式论文链接，也会从仓库元文件自动发现
- **LaTeX PDF**：使用 xelatex + ctex 中文模板
- **跨平台**：自动适配 Claude Code / Codex / Kimi Code
- **Markdown-first**：流程、工具和模板都以 md 维护

## 开发与验收

```bash
pytest -q
```

测试校验关键契约：细致度确认、技术栈识别、仓库名解析、论文自动发现、生成目录隔离、手册质量检查。

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

## License

MIT
