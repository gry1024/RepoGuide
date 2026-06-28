---
name: repoguide-task-phase-4
description: RepoGuide Phase 4：手册组装。按面向人、全中文、卡片式模板生成 manual.md。
---

# Phase 4: 手册组装

## 执行方式

创建 **writer** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json + analysis_arch.json + analysis_code.json + analysis_paper.json(可选) + analysis_map.json(可选) + image-manifest.json(可选)
输出: $WORK_DIR/manual.md
```

## 任务

1. 读取所有分析产物与 `image-manifest.json`。
2. 严格按 `references/manual-template.md` 的模板与"排版硬规则"组装。
3. **第 1 层（一页速览）由 writer 自己综合**：一句话总括、三条命令、五个最关键文件。
4. **架构总览图**：引用 `images/architecture_overview.png`（由 image-handler 渲染）。若图缺失，用 3.3 数据流叙述替代并在附录记录限制。
5. **注释化目录树**：直接取 `analysis_arch.json.annotated_tree`，不得删注释。
6. **卡片式代码**：按 `analysis_code.json.core_files` 渲染；`key_logic` 超 12 行截断并加 `# ...（略）`。
7. **论文公式**：以 `$$...$$` 写入，保留原始 LaTeX，不得转义。
8. **全中文校验**：写完后调用 `sub-skills/tools/manual-quality-checker.md` 的英文整句扫描逻辑；若发现违规项，必须改写为中文后重新检查。
9. 写入 `$WORK_DIR/manual.md`。

## 手册结构（与模板一致）

1. 一页速览（一句话 + 命令 + 五关键文件）
2. 技术栈与依赖
3. 架构与数据流（总览图 + 注释化目录树 + 数据流叙述 + 流转表 + 状态点 + 设计决策）
4. 核心代码详解（卡片式）+ 周边文件清单 + 配置/脚本/资源
5. 论文—代码映射（可选：速览 + 公式 + 三层映射 + 论文原图 + 术语表）
6. 附录（文件清单 + 已知限制 + 生成信息）

## 按 depth 调整内容

### standard
- 注释化目录树为核心目录。
- 卡片式代码聚焦核心文件。
- 论文部分仅主要章节与公式。

### deep
- 完整注释化目录树。
- 卡片式代码覆盖所有核心文件，每个类/函数。
- 论文逐章映射 + 论文原图 + 术语表。

## 输出校验

```python
validate_file_exists("$WORK_DIR/manual.md", min_bytes=100)
```

附加检查：手册须含"一、一页速览"、"三、架构与数据流"、"四、核心代码详解"标题；目录树代码块内 ≥ 80% 行含 ` # `。

## 下一 Phase

完成后进入 [phase-5-renderer.md](phase-5-renderer.md)。
