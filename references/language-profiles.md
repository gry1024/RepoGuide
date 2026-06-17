# 语言特征表

本文件定义 RepoGuide 支持的 6 种语言（Python / JavaScript / TypeScript / Java / Go / Rust）的特征，subagent 按此 dispatch。

## 1. Python

**包管理/依赖文件**:
- `pyproject.toml` (优先，含 [project] section)
- `requirements.txt`, `requirements-*.txt`, `requirements/*.txt`
- `setup.py`, `setup.cfg`
- `Pipfile`, `Pipfile.lock`
- `poetry.lock`
- `uv.lock`
- `conda.yml`, `environment.yml`

**入口识别**:
- `pyproject.toml` 的 `[project.scripts]` 段
- `setup.py` 的 `entry_points`
- 包含 `if __name__ == "__main__":` 的文件
- `app.py`, `main.py`, `__main__.py`, `cli.py`, `run.py` 命名约定

**模块系统**: import + package (有 `__init__.py` 的目录)

**AST 提取**: Python 内置 `ast` 模块（无需外部依赖）

**核心标识符前缀**:
- `class <Name>:` → 类
- `def <name>(` / `async def <name>(` → 函数
- 装饰器 `@<decorator>` 紧贴 def/class

**降级**: 若 ast 失败 → 用正则 `^class\s+\w+` / `^(async\s+)?def\s+\w+`

## 2. JavaScript

**包管理/依赖文件**:
- `package.json` (核心)
- `package-lock.json`
- `yarn.lock`
- `pnpm-lock.yaml`
- `bun.lockb`

**入口识别**:
- `package.json` 的 `main` 字段
- `package.json` 的 `bin` 字段
- `index.js`, `index.mjs`, `index.cjs` 命名约定
- `app.js`, `server.js`, `main.js`

**模块系统**:
- CommonJS: `require()` / `module.exports`
- ESM: `import` / `export`
- 用 `package.json` 的 `"type": "module"` 字段判断

**AST 提取**: 用 Node 内置解析或正则（避免外部工具）

**核心标识符前缀**:
- `class <Name> {` → 类
- `function <name>(` / `const <name> = (` → 函数
- `const <Name> = (` 紧贴大括号块 → 组件或对象

**降级**: 用正则 `^class\s+\w+` / `^function\s+\w+` / `^const\s+\w+\s*=\s*\(`

## 3. TypeScript

**包管理/依赖文件**: 同 JavaScript + `tsconfig.json`

**入口识别**: 同 JavaScript + `tsconfig.json` 的 `outDir`/`rootDir` + `src/index.ts`, `src/main.ts`

**模块系统**: ESM 为主

**AST 提取**: 同 JavaScript，重点提取 type 声明

**核心标识符前缀**: 同 JavaScript
- `interface <Name> {` → 接口
- `type <Name> =` → 类型别名
- `enum <Name> {` → 枚举

**降级**: 同 JavaScript

## 4. Java

**包管理/依赖文件**:
- `pom.xml` (Maven)
- `build.gradle`, `build.gradle.kts` (Gradle)
- `settings.gradle*`

**入口识别**:
- 含 `@SpringBootApplication` 注解的类
- 含 `public static void main(String[] args)` 的类
- `pom.xml` 的 `<mainClass>` 段
- `src/main/java/.../Application.java` 命名约定

**模块系统**: package + import (基于目录)

**AST 提取**: 优先用 `javap -p <file.class>` (需要 class 文件)，否则用正则

**核心标识符前缀**:
- `(public|private|protected)?\s*(static\s+)?class\s+\w+` → 类
- `(public|private|protected)?\s*[\w<>,\s]+\s+\w+\s*\(` → 方法

**降级**: 用正则

## 5. Go

**包管理/依赖文件**:
- `go.mod`
- `go.sum`

**入口识别**:
- `package main` 中的 `func main()`
- `cmd/<name>/main.go` 目录约定
- `Makefile` 中包含的目标

**模块系统**: package + import

**AST 提取**: Go 内置 `go/ast` 工具链（如果有 Go 工具链），否则正则

**核心标识符前缀**:
- `^func\s+(\(\w+\s+\*?\w+\)\s+)?\w+\(` → 方法/函数
- `^type\s+\w+\s+struct` → 结构体
- `^type\s+\w+\s+interface` → 接口

**降级**: 用正则 + 文件名约定

## 6. Rust

**包管理/依赖文件**:
- `Cargo.toml` (核心)
- `Cargo.lock`

**入口识别**:
- `src/main.rs` (binary crate)
- `src/lib.rs` (library crate)
- `Cargo.toml` 的 `[[bin]]` 表
- `examples/`, `benches/` 目录

**模块系统**: crate + mod + use

**AST 提取**: `cargo check --message-format=json` (慢，回退到正则) / `rustc --emit=metadata` (慢)

**核心标识符前缀**:
- `^(pub\s+)?(async\s+)?fn\s+\w+` → 函数
- `^(pub\s+)?struct\s+\w+` → 结构体
- `^(pub\s+)?trait\s+\w+` → trait
- `^(pub\s+)?enum\s+\w+` → 枚举
- `^(pub\s+)?impl\s+` → impl 块

**降级**: 用正则
