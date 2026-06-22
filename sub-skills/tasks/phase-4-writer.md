---
name: repoguide-task-phase-4
description: RepoGuide Phase 4：手册组装。创建 writer agent，读取所有分析产物并按模板生成 manual.md。
---

# Phase 4: 手册组装

## 执行方式

创建 **writer** agent 执行本 Phase。

```
输入: $WORK_DIR/profile.json + analysis_*.json + image-manifest.json(可选)
输出: $WORK_DIR/manual.md
```

## 任务

1. 读取所有分析产物。
2. 如果存在 `image-manifest.json`，在第 3 层和第 5 层插入图片。
3. 参考 `references/manual-template.md` 的五层结构。
4. 主 agent 自己综合第 1 层（一句话总括 + 3 条命令 + 5 个关键文件）。
5. 组装完整 Markdown 仓库手册指南。
6. 写入 `$WORK_DIR/manual.md`。

## 手册结构

1. 第 0 层：元信息
2. 第 1 层：一句话总括 + 快速上手
3. 第 2 层：技术栈与依赖
4. 第 3 层：架构与数据流（含模块依赖图、数据流图、仓库/论文配图）
5. 第 4 层：核心代码详解
6. 第 5 层：论文-代码映射（可选，含论文原图）
7. 附录：文件清单、已知限制、生成信息

## 按 depth 调整内容

### standard

- 第 3 层包含模块依赖图和核心数据流图。
- 第 4 层聚焦核心文件，每个文件给出关键类/函数说明。
- 目录树为核心目录 tree。

### deep

- 第 3 层包含完整模块依赖图、数据流图、调用链图、状态/生命周期图。
- 第 4 层覆盖所有文件，每个类/函数都有说明。
- 目录树为完整 tree，每个核心文件带注释。
- 第 5 层（如有论文）包含逐章映射和论文原图。

## 下一 Phase

完成后进入 [phase-5-renderer.md](phase-5-renderer.md)。
