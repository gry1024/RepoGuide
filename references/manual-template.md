# 仓库手册指南模板（面向人 · 全中文 · 卡片式）

writer agent 按本模板组装 Markdown 内容。**唯一读者是人**：一切叙述须简体中文，让人最快掌握结构、架构与代码-论文映射。

输入 JSON：
- `profile.json`
- `analysis_arch.json`（含 `annotated_tree`、`architecture_overview_dot`、`data_flow_narrative`、`data_flow_table`）
- `analysis_code.json`（含 `core_files` 卡片式、`peripheral_files`、`config_files`、`scripts`、`resources`）
- `analysis_paper.json`（可选）
- `analysis_map.json`（可选）
- `image-manifest.json`（可选）

## 排版硬规则

1. 目录树必须每行带 `# 中文用途注释`（≤ 30 字），无注释的行不得出现。
2. 类/函数一律用"卡片"：签名代码块 + 一句话中文职责 + 参数表 + 关键逻辑片段（≤ 12 行）。禁止把多段说明性文字堆成密密麻麻的段落。
3. 论文公式用 `$$...$$` 块，公式编号用 `\tag{n}`。术语表、映射表用 Markdown 表格。
4. 图片引用前必须有中文图注段落；图片路径用相对路径 `images/xxx.png`。
5. 架构总览图只嵌入 1 张（`images/architecture_overview.png`），不出多张树状图。
6. 全文不出现英文整句；专有名词（GFlowNet、RGCN、PPO、Qlib 等）可保留原文。

## 模板内容

```markdown
# {{repo_name}} 仓库手册指南

> 由 RepoGuide 自动生成于 {{generated_at}}  
> 仓库路径：`{{repo_path}}`  
> 分析档位：{{depth}}　生成耗时：{{duration}}

---

## 一、一页速览

> **一句话总括**：{{one_liner}}

| 项 | 值 |
|----|----|
| 主语言 | {{primary_language}} |
| 文件总数 | {{file_count_total}} |
| 论文 | {{paper_found ? "已配套" : "未配套"}} |
| 核心入口 | {{entry_points_short}} |

### 三条命令上手

```bash
# 安装
{{install_cmd}}

# 训练/运行
{{run_cmd}}

# 测试/评估
{{test_cmd}}
```

### 五个最关键的文件

| # | 文件 | 用途 |
|---|------|------|
| 1 | `{{top_file_1}}` | {{top_file_1_desc}} |
| 2 | `{{top_file_2}}` | {{top_file_2_desc}} |
| 3 | `{{top_file_3}}` | {{top_file_3_desc}} |
| 4 | `{{top_file_4}}` | {{top_file_4_desc}} |
| 5 | `{{top_file_5}}` | {{top_file_5_desc}} |

---

## 二、技术栈与依赖

### 语言与版本

- {{primary_language}}：{{language_version}}

### 包管理

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

## 三、架构与数据流

### 3.1 架构总览图

![AlphaSAGE 架构总览](images/architecture_overview.png)

> 图 1：分层架构与数据流转总览（graphviz 生成）。

### 3.2 注释化目录树

> 每一行末尾 `#` 后为该文件/目录的中文用途说明。{{depth}} 模式。

```text
{{annotated_tree}}
```

### 3.3 数据流叙述

{{data_flow_narrative}}

#### 数据流转表

| 步骤 | 输入 | 处理模块 | 输出 | 关键文件 |
|------|------|----------|------|----------|
{{#each data_flow_table}}
| {{step}} | {{input}} | {{module}} | {{output}} | `{{file}}` |
{{/each}}

#### 关键状态点

{{#each key_state_points}}
- **{{name}}**：{{description}}（`{{file}}:{{line}}`）
{{/each}}

### 3.4 关键设计决策

{{#each design_decisions}}
#### {{decision}}

- **证据**：`{{evidence}}`
- **理由**：{{reasoning}}
{{/each}}

---

## 四、核心代码详解（卡片式）

> 每个核心文件一张"卡片"：签名 → 一句话职责 → 类清单表 → 函数卡片。

{{#each core_files}}
### `{{path}}`

> **职责**：{{one_liner}}  
> **依赖**：{{#each dependencies}}`{{this}}` {{/each}}

#### 类清单

| 类名 | 行号 | 职责 |
|------|------|------|
{{#each classes}}
| `{{name}}` | {{line}} | {{purpose}} |
{{/each}}

#### 函数卡片

{{#each functions}}
##### `{{name}}`

```{{lang}}
{{signature}}
```

- **职责**：{{purpose}}
- **参数**：

| 参数 | 含义 |
|------|------|
{{#each params}}
| `{{name}}` | {{meaning}} |
{{/each}}

- **返回**：{{returns}}
- **关键逻辑**：

```{{lang}}
{{key_logic}}
```

{{/each}}

---

{{/each}}

### 4.x 周边文件清单

| 路径 | 用途 | 重要度 |
|------|------|--------|
{{#each peripheral_files}}
| `{{path}}` | {{one_liner}} | {{importance}} |
{{/each}}

### 4.y 配置 / 脚本 / 资源

**配置文件**

| 路径 | 用途 |
|------|------|
{{#each config_files}}
| `{{path}}` | {{purpose}} |
{{/each}}

**脚本**

| 路径 | 用途 |
|------|------|
{{#each scripts}}
| `{{path}}` | {{purpose}} |
{{/each}}

**资源**

| 路径 | 用途 |
|------|------|
{{#each resources}}
| `{{path}}` | {{purpose}} |
{{/each}}

**测试策略**：{{test_strategy}}

---

{{#if paper_found}}
## 五、论文—代码映射

### 5.1 论文速览

- **标题**：{{paper_title}}
- **作者**：{{paper_authors}}

**核心贡献**：

{{#each paper_core_contributions}}
- {{this}}
{{/each}}

**章节结构**：

{{#each paper_section_tree}}
- {{indent}}{{title}}
{{/each}}

### 5.2 关键公式

{{#each paper_key_formulas}}
$$
{{latex}}
$$

> 公式 {{index}}：{{meaning}}
{{/each}}

### 5.3 论文—代码三层映射

**层级 1：论文章节 ↔ 代码模块**

| 论文章节 | 代码模块 | 置信度 |
|----------|----------|--------|
{{#each layer1_section_to_module}}
| {{section}} | `{{module}}` | {{confidence}} |
{{/each}}

**层级 2：论文公式/算法 ↔ 代码函数/类**

| 论文公式/算法 | 代码函数/类 | 位置 | 置信度 |
|---------------|-------------|------|--------|
{{#each layer2_formula_to_function}}
| {{formula}} | `{{function}}` | `{{file}}:{{line}}` | {{confidence}} |
{{/each}}

**层级 3：论文实验/表格 ↔ 评估脚本**

| 论文实验/表格 | 评估脚本 | 位置 |
|---------------|----------|------|
{{#each layer3_experiment_to_script}}
| {{experiment}} | `{{script}}` | `{{file}}` |
{{/each}}

### 5.4 论文原图

{{#each paper_figures}}
**图 {{index}}：{{caption}}**

![{{caption}}]({{path}})
{{/each}}

### 5.5 术语对照表

| 论文术语 | 代码标识符 | 含义 |
|----------|------------|------|
{{#each paper_glossary}}
| {{term}} | `{{code_identifier}}` | {{description}} |
{{/each}}
{{/if}}

---

## 附录

### 文件清单（按扩展名分组）

{{#each file_groups}}
- **{{ext}}**（{{count}} 个）：{{sample_paths}}
{{/each}}

### 已知限制 / 不确定项

{{#each limitation_notes}}
- {{this}}
{{/each}}

### 生成信息

- 生成时间：{{generated_at}}
- 总耗时：{{duration}}
- 执行模式：{{execution_mode}}
- 降级情况：{{degradation_notes}}
```

## writer 组装规则

1. 读取 `profile.json` + `analysis_*.json` + `image-manifest.json`。
2. **第 1 层（速览）由 writer 自己综合**：从 `analysis_code.json` 选 5 个最关键文件，从 README/配置提取安装/运行/测试命令。
3. **架构总览图**：直接引用 `images/architecture_overview.png`（由 image-handler 从 `analysis_arch.json.architecture_overview_dot` 渲染）。若图缺失，改用 3.3 数据流叙述替代并记录限制。
4. **注释化目录树**：直接取 `analysis_arch.json.annotated_tree`，**不得删去注释**。
5. **卡片式代码**：按 `analysis_code.json.core_files` 渲染；函数的 `key_logic` 若超过 12 行须截断并加 `# ...（略）` 注释。
6. **公式**：论文公式以 `$$...$$` 写入，保留原始 LaTeX；writer 不得对公式内容做转义。
7. **全中文校验**：写完 `manual.md` 后，扫描是否含英文整句（连续 ≥ 4 个英文单词且非代码/专有名词），若有则改写为中文。
8. 缺失字段留空并在附录"已知限制"标注。
9. 输出到 `$WORK_DIR/manual.md`。
