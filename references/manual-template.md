# 五层结构仓库手册指南模板

writer agent 按本模板组装 Markdown 内容。

输入 JSON：
- `profile.json`
- `analysis_arch.json`
- `analysis_code.json`
- `analysis_paper.json`（可选）
- `analysis_map.json`（可选）

## 模板内容

```markdown
# {{repo_name}} 仓库手册指南

> 由 RepoGuide skill 自动生成于 {{generated_at}}  
> 仓库路径: `{{repo_path}}`  
> 生成耗时: {{duration}}

---

## 第 0 层 · 元信息

| 项 | 值 |
|----|-----|
| 仓库名 | {{repo_name}} |
| 路径 | `{{repo_path}}` |
| 主语言 | {{primary_language}} |
| 所有语言 | {{all_languages}} |
| 文件总数 | {{file_count_total}} |
| 论文 | {{paper_found ? "已检测" : "未检测"}} |

### 按扩展名统计

| 扩展名 | 文件数 |
|--------|--------|
{{#each file_count_by_ext}}
| .{{ext}} | {{count}} |
{{/each}}

### 论文信息

{{#if paper_found}}
- **标题**: {{paper_title}}
- **作者**: {{paper_authors}}
- **PDF 路径**: `{{paper_path}}`
{{else}}
- 未在仓库中检测到论文
{{/if}}

---

## 第 1 层 · 一句话总括 + 快速上手

### 一句话总括

{{one_liner}}

### 3 条命令上手

```bash
# 安装
{{install_cmd}}

# 运行
{{run_cmd}}

# 测试
{{test_cmd}}
```

### 5 个最关键的文件

1. `{{top_file_1}}` — {{top_file_1_desc}}
2. `{{top_file_2}}` — {{top_file_2_desc}}
3. `{{top_file_3}}` — {{top_file_3_desc}}
4. `{{top_file_4}}` — {{top_file_4_desc}}
5. `{{top_file_5}}` — {{top_file_5_desc}}

---

## 第 2 层 · 技术栈与依赖

### 语言与版本

- {{primary_language}}: {{language_version}}

### 包管理文件

{{#each package_managers}}
- `{{this}}`
{{/each}}

### 核心依赖

{{#each dependency_groups}}
#### {{group_name}}

| 包 | 用途 |
|----|------|
{{#each packages}}
| {{name}} | {{purpose}} |
{{/each}}
{{/each}}

---

## 第 3 层 · 架构与数据流

### 3.1 模块划分

#### 模块依赖图

```mermaid
{{module_dependency_graph}}
```

### 3.2 数据流

{{data_flow_narrative}}

```mermaid
{{data_flow_graph}}
```

#### 关键状态点

{{#each key_state_points}}
- **{{name}}**: {{description}} (位于 `{{file}}:{{line}}`)
{{/each}}

### 3.3 关键设计决策

{{#each design_decisions}}
#### {{decision}}

**证据**: `{{evidence}}`

{{reasoning}}
{{/each}}

### 3.4 配图

{{#each generated_diagrams}}
#### {{caption}}

![{{caption}}]({{path}})
{{/each}}

{{#each repo_figures}}
#### 仓库图片: {{path}}

![{{path}}]({{path}})
{{/each}}

### 3.5 仓库目录树

> 仅在 `depth == deep` 时输出完整目录树。standard/fast 输出关键文件清单。

```text
{{directory_tree}}
```

目录树规范：
- 使用 `tree` 命令风格：
  ```
  repo/
  ├── src/
  │   └── main.py          # 入口文件
  └── README.md
  ```
- 每个核心目录/文件右侧用 `# 简短注释` 说明作用。
- 忽略 `.git/`、`__pycache__/`、`node_modules/` 等无关目录。
- 保持层级清晰，深度建议不超过 5 层。

---

## 第 4 层 · 核心代码详解

### 4.1 核心模块详细分析

{{#each core_files}}
#### `{{path}}`

**作用**: {{one_liner}}

**依赖**: {{#each dependencies}}`{{this}}` {{/each}}

##### 类清单

{{#each classes}}
- `{{name}}` (line {{line}}): `{{signature}}` — {{purpose}}
{{/each}}

##### 函数清单

{{#each functions}}
- `{{name}}` (line {{line}}): `{{signature}}`

  关键逻辑:
  ```{{lang}}
  {{key_logic}}
  ```
{{/each}}

{{/each}}

### 4.2 周边模块简略清单

| 路径 | 一句话作用 | 重要度 |
|------|-----------|--------|
{{#each peripheral_files}}
| `{{path}}` | {{one_liner}} | {{importance}} |
{{/each}}

### 4.3 配置/脚本/资源

#### 配置文件

{{#each config_files}}
- `{{path}}`: {{purpose}}
{{/each}}

#### 脚本

{{#each scripts}}
- `{{path}}`: {{purpose}}
{{/each}}

#### 资源

{{#each resources}}
- `{{path}}`: {{purpose}}
{{/each}}

#### 测试策略

{{test_strategy}}

---

{{#if paper_found}}
## 第 5 层 · 论文-代码映射

### 5.1 论文速览

**标题**: {{paper_title}}

**作者**: {{paper_authors}}

**核心贡献**:
{{#each paper_core_contributions}}
- {{this}}
{{/each}}

#### 章节结构

{{#each paper_section_tree}}
- {{indent}}{{title}}
{{/each}}

### 5.2 论文-代码三层映射

#### 层级 1: 论文章节 ↔ 代码模块

| 论文章节 | 代码模块 | 置信度 |
|----------|----------|--------|
{{#each layer1_section_to_module}}
| {{section}} | `{{module}}` | {{confidence}} |
{{/each}}

#### 层级 2: 论文公式/算法 ↔ 代码函数/类

| 论文公式/算法 | 代码函数/类 | 位置 | 置信度 |
|---------------|-------------|------|--------|
{{#each layer2_formula_to_function}}
| {{formula}} | `{{function}}` | `{{file}}:{{line}}` | {{confidence}} |
{{/each}}

#### 层级 3: 论文实验/表格 ↔ 评估脚本

| 论文实验/表格 | 评估脚本 | 位置 |
|---------------|----------|------|
{{#each layer3_experiment_to_script}}
| {{experiment}} | `{{script}}` | `{{file}}` |
{{/each}}

### 5.3 论文原图

{{#each paper_figures}}
#### {{caption}}

![{{caption}}]({{path}})
{{/each}}

### 5.4 关键术语对照表

| 论文术语 | 代码标识符 |
|----------|------------|
{{#each paper_glossary}}
| {{term}} | `{{code_identifier}}` |
{{/each}}
{{/if}}

---

## 附录

### 文件清单 (按扩展名分组)

{{#each file_groups}}
- **{{ext}}** ({{count}} 个): {{sample_paths}}
{{/each}}

### 已知限制 / 不确定项

{{#each limitation_notes}}
- {{this}}
{{/each}}

### 生成信息

- **生成时间**: {{generated_at}}
- **总耗时**: {{duration}}
- **执行模式**: {{execution_mode}}
- **降级情况**: {{degradation_notes}}
```

## 使用说明

1. writer agent 读取 `profile.json` + `analysis_*.json`。
2. 按字段名填入对应位置。
3. 缺失字段留空或在"已知限制"附录标注。
4. mermaid 图直接嵌入 `mermaid` 代码块。
5. 输出到 `$WORK_DIR/manual.md`，随后渲染为 PDF（或 HTML 降级）。
