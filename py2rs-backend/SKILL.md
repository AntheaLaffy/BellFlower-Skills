---
name: "py2rs"
description: "[DRAFT] Python→Rust 渐进式重写总 skill。定义核心思想、链路、运行时模型、上下文管理机制与状态机；统一调度依赖对齐、跑通环境、运行时、7轮审查等子 skill。"
---

# py2rs — Python → Rust 渐进式重写与现代化流水线

> **DRAFT（草稿状态）** —— 本文档目前是给 AI 读的规范，不是编译器能跑的代码。
> 下方「脚手架猜想」是对将来实战环境下可能需要的实际代码的猜想，**不是强制教条**。
> 等跑通一个真实项目的迁移后，再回过来修订这里的条目。

## 依赖管理（核心思想：保证 py 侧与 rs 侧依赖覆盖的能力范围相当，这是前 3 个阶段渐进式替换能保持行为一致的基础）

本模块讲“哪些依赖可以纳入迁移，哪些不行”——而不是讲“后端/前端能不能碰”。前 3 个阶段（Stage 0 依赖对齐 → Stage 0 环境跑通 → Stage 1 运行时 + Stage 2~3 迁移-验收循环 + R0 行为一致性 gate）之所以能做到渐进式替换，前提就是：**Python 依赖能做到的事情，Rust 侧有等价的依赖去覆盖**。违反这条前提的依赖一律视为 Stage 0 漏项。

### 原则 1 — 允许纳入迁移的依赖（py↔rs 有等价实现）
- ✅ **后端 / 批处理 / CLI / HTTP / 数据处理 / 并发 / 异步 / 序列化 / 日志 / 错误处理**：这类依赖在 Python 和 Rust 生态中一般都有成熟等价实现，直接纳入
- ✅ **像 Qt 这种“每种语言都有成熟桥接”的 GUI 框架**：Python 有 PyQt/PySide，C++ 有 Qt Widgets，Rust 也有 `cxx-qt` / `qmetaobject-rs` / `rust-qt` 等绑定；因为能力范围相当，**可以纳入迁移**（注意：是否真要迁 GUI 仍由项目决定，这里只是说“能力上允许”）
- ✅ **Web 端（HTML / CSS / JS）**：天然统一、天然与后端解耦；不需要迁移，直接复用即可，也不在这里禁止
- 判断标准：**“Python 侧依赖能做的事，Rust 侧依赖能不能以同等语义覆盖？”**——能，就纳入；不能，就不纳入

### 原则 2 — 不允许纳入迁移的依赖（py↔rs 没有等价实现，或者差异太大）
- ❌ **强绑定特定 GUI 库、且 Rust 侧没有同等语义的对应物**：例如某个 Python 项目重度依赖 Kivy 的自定义渲染管线、重度依赖某个 WinForms 控件的行为语义、重度依赖 Tk 的布局模型——这类依赖在 Rust 侧找不到能力范围相当的替代，**渐进式替换失去基础，不纳入**
- ❌ **强依赖特定解释器 / 特定平台插件 / 特定运行时二进制**：如果 Python 代码强依赖 CPython 的某个内部 API、某个 `.pyd` / `.so` 扩展、某个闭源 SDK 的 Python binding，而 Rust 侧没有同等语义的 binding，**不纳入**
- ❌ **npm / yarn / pnpm / vite / webpack 等前端构建工具**：不是“能力范围不相当”，而是“它们属于前端工程，不在本 skill 负责的迁移路径上”；Web 端直接复用即可，不需要走 py↔rs 替换

### 原则 3 — 依赖必须在 Stage 0 先对齐好；迁移-验收循环锁死依赖；审查阶段（R1~R6）允许大改和新依赖
- ✅ **Stage 0（依赖对齐 / 环境跑通）**：明确列出每个脚本会用到的 Python 依赖及其等价 Rust 依赖；**发现“缺等价依赖”就必须在这里补齐**
- ✅ **Stage 1~Stage 3 + R0（运行时 + 迁移-验收循环 + 行为一致性 gate）**：**锁死依赖**，只允许使用 Stage 0 已经对齐好的依赖清单；如果在这里发现缺依赖，**视为 Stage 0 漏项，必须回到 Stage 0 补齐再重新跑**——**这是为了保证行为一致性**
- ✅ **R1~R6（审查阶段）**：**允许大改、允许 `cargo add` 新 crate、允许替换底层实现**——前提是每轮结束时能再次通过 R0 级别的行为一致性测试
- 简单记忆：**前 3 个阶段锁死依赖是为了保行为一致；审查阶段才允许为了质量而改依赖**

**一句话总括：py↔rs 依赖能力范围相当 → 才能渐进式替换 → 才能保证行为一致。** 这是前 3 个阶段存在的根本理由。

## 脚手架猜想（可能会有，但先不确定）

- 一个 `py2rs` CLI（可能是 `pyproject.toml` 里的 console script，也可能是 `Makefile`）
- 一个 `_scaffold/manifest/modules.yaml` 的**初始模板**（字段名、状态枚举可能会改）
- 一组 `_scaffold/runtime/*.py` —— router / state / bridge 的最小可运行版本
- 一组 `_scaffold/demo/` 下的 hello-world py + rs 实现
- 一个 `pyproject.toml` + `Cargo.toml` 的**双构建骨架**（maturin / pyo3）
- 一组 `_scaffold/tests/compare/` 下的行为对比 pytest 模板
- 一个 `_scaffold/reviews/` 下的 markdown 报告模板（供 R0~R6 填）

以上任何一项都不承诺现在就写；先用实战项目倒逼出真正需要的形状。

---

## 1. 最终目标（不是翻译器）

> 在持续可运行、持续可验证、持续可回滚的前提下，完成系统级渐进式重写与现代化改造。

- **不是**：把 Python 代码“机械翻译成” Rust 代码
- **而是**：把迁移看成一个长期的、可中断、可恢复、可验收的软件工程过程

这条总则是所有子 skill 共同遵守的最高约束。

---

## 2. 核心思想（四个基石）

### 2.1 Principle 1 — 行为优先于架构

迁移阶段严格遵守：

```text
行为一致性 > 代码优雅性
```

- 禁止：提前重构 / 提前优化 / 提前抽象
- 允许：函数名、结构、目录与 Python 版本“丑陋地一致”

### 2.2 Principle 2 — 先迁移，后优化

流程必须是两段式：

```text
Python
↓
行为等价 Rust（第一阶段，丑但对）
↓
测试通过 + 用户验收
↓
工程化优化（第二阶段，由 6 轮审查驱动）
```

风险拆开是本 skill 最大的设计决策。如果把“迁移”和“优化”混在一起做，最后没人知道 Bug 到底来自哪里。

### 2.3 Principle 3 — 实现与路由分离

**禁止**：

```text
Python ←→ Rust 直接 FFI 耦合
```

**必须**：

```text
Python 实现
    ↓
  Runtime 路由层（唯一事实来源）
    ↓
Rust 实现
```

- rs 只认识 rs，py 只认识 py
- 跨语言必须经过 runtime
- runtime 是路由器，不是业务层

### 2.4 Principle 4 — 任何时刻可回滚

- 旧实现永远保留在 `py/`，不删除
- 新实现独立落地在 `rs/`，不覆盖
- runtime 根据 manifest 决定“这次走 py 还是走 rs”
- 回滚 = 把 manifest 里对应模块的 `owner` 改回 `py`

---

## 3. 迁移单元定义

迁移单元不是模块、不是服务，而是：

```text
脚本（Script）
```

例如：`main.py` / `user_service.py` / `payment.py` / `crawler.py`。

选择脚本作为迁移单元的根本原因：AI 在单个职责明确的代码单元上最不容易翻车。越大的迁移单元，上下文越容易超过窗口，错误越不可验证。

---

## 4. 四阶段迁移总链路

```text
Stage 0  —— 依赖对齐 + 跑通环境
Stage 1  —— 运行时验证（Demo）
Stage 2  —— 按脚本逐个迁移（py→rs 同名职责）
Stage 3  —— 验证 / 验收
Stage 4  —— 循环直到全部完成

           ↓（进入审查阶段）

Round 0   —— 行为一致性审查（冻结语义，不允许改代码）
Round 1   —— Rust 工程化审查（mod / lib / trait / 生命周期）
Round 2   —— 错误追踪审查（tracing / anyhow / thiserror）
Round 3   —— IO 与并发审查（tokio / rayon / async）
Round 4   —— 算法复杂度审查（需有复杂度证明 + Benchmark）
Round 5   —— 架构与数据结构审查（所有权 / API 设计）
Round 6   —— 产品与人体工学审查（只分析不写代码）
```

---

## 5. 标准项目结构

```text
project/
├─ runtime/          # 路由层、运行时模型、适配层
├─ py/               # 旧实现归档 + 仍在运行的 Python
├─ rs/               # 新实现，按脚本同名对应
├─ manifest/         # 迁移状态唯一事实来源（YAML）
└─ tests/            # py 测试 / rs 测试 / 行为对比测试
```

### 迁移过程中目录的三种状态

- **阶段 A（纯 Python）**：只有根目录 Python 文件
- **阶段 B（混合运行）**：根目录只有 runtime + `py/` + `rs/`，部分 py、部分 rs
- **阶段 C（纯 Rust）**：根目录只有 runtime + `rs/`，`py/` 仅作归档
- **阶段 D（最终）**：只有 `rs/`，runtime 兼容层可删除

---

## 6. 运行时模型（Runtime Model）

> 所有迁移动作必须先更新运行时模型，再修改代码；所有跨语言调用必须先经过 runtime，再进入具体语言实现。

运行时模型是本 skill 的**唯一迁移执行依据**。AI 在处理任何脚本迁移、回滚、转发、验证前，都必须先读取并更新它，而不是根据目录是否为空来“猜”。

### 6.1 运行时模型组成

它把四类信息合并为一个统一知识源：

1. **模块清单**：每个脚本/模块的归属（py / rs / runtime）
2. **迁移状态**：`active` / `archived` / `planned` / `reimplemented` / `verified` / `promoted` / `optimized`
3. **路由规则**：调用该走 Python 还是 Rust，是否需要转发 / 包装 / 兼容
4. **验证状态**：py 测试是否通过、rs 测试是否通过、行为是否一致、是否已用户验收

### 6.2 迁移状态机（每个脚本必经）

```text
planned
  ↓
archived(py)            # 原文件移入 py/
  ↓
reimplemented(rs)       # rs/ 中建立同名职责实现
  ↓
verified                # py 测试 & rs 测试 & 行为对比 全部通过
  ↓
promoted                # 允许用户真实使用
  ↓
optimized               # 进入 6 轮审查与重构
```

**AI 每次只允许推进一个明确状态，禁止跳过验证直接优化。**

### 6.3 runtime 的职责边界（只能做三件事）

1. 读取运行时模型
2. 决定当前请求转发给 Python 还是 Rust
3. 记录迁移状态与验证结果

**runtime 不做业务实现，也不直接污染 py/rs 里的业务逻辑。**

它是一个“过渡架构中的 router / temporary adapter / transformer”，属于 Anti-Corruption Layer 的思想——只做翻译，不让旧模型污染新模型。

---

## 7. 上下文管理机制（本 skill 最重要的约束）

本 skill 最大的敌人不是“AI 不会写 Rust”，而是：

```text
迁移对象 > 上下文窗口
```

因此上下文管理是本 skill 的核心工程。

### 7.1 上下文切分原则

- **按脚本切分上下文**：每次 AI 的输入不超过一个迁移单元 + 其直接依赖的 manifest 摘要
- **分层压缩**：大仓库被压成 “迁移画像”（manifest + 各模块状态摘要），而不是全量代码
- **Agent 职责隔离**：Writer ≠ Reviewer ≠ Tester ≠ Architect。不同角色读不同上下文，不共享推理过程

### 7.2 Agent 职责矩阵

| Agent | 职责 | 读什么上下文 | 不做什么 |
|-------|------|-------------|---------|
| Writer（迁移者） | 把 py 脚本改写成行为等价的 rs 脚本 | 原 py 文件 + 当前脚本的 manifest 条目 | 不做架构优化、不做抽象 |
| Reviewer（行为审查） | 寻找行为差异 | py 实现 + rs 实现（不看 Writer 思路） | 不关心代码优雅性 |
| Tester（边界测试） | 生成边界 / 异常 / 压力测试 | 函数签名 + 已知输入输出 | 不改生产代码 |
| Architect（后期优化） | 驱动 6 轮审查与现代化 | 已 verified 的 rs 代码 + 审查报告 | 不在迁移阶段提前介入 |

### 7.3 跨 Agent 交接协议

Agent 之间**不通过聊天记录传递上下文**，只通过下面三类持久化文件交接：

1. `manifest/*.yaml` —— 当前迁移状态机
2. `reviews/round-N.md` —— 每轮审查报告
3. `tests/*_compare.log` —— 行为对比测试结果

这是确保整个流水线可中断、可恢复、可审计的关键。

### 7.4 单轮迁移的最小上下文包

每一次让 AI 做迁移时，你传入的上下文应该只包含：

- 目标脚本的路径（单个文件）
- 该脚本在 manifest 中的当前状态
- 该脚本的外部接口签名（来自 `manifest/signatures/`）
- 最近一次的行为对比测试结果（如果存在）

**严禁一次喂给 AI 整个项目源码。**

---

## 8. 子 skill 调度总览

本总 skill 不亲自“做事”，它定义做事顺序与准则。具体执行由下列子 skill 承担：

### 8.1 前期准备（Stage 0）

| 子 skill | 作用 |
|---------|------|
| `py2rs-dep-align` | 对齐 py/rs/FFI 依赖，拉取并锁定版本 |
| `py2rs-env-bootstrap` | 跑通混合运行环境，验证 FFI / async / 错误追踪 |

### 8.2 运行时层（Stage 1 骨架）

| 子 skill | 作用 |
|---------|------|
| `py2rs-runtime` | 建立 runtime / manifest / 路由协议 / 状态机读写 |

### 8.3 审查阶段（迁移完成后）

| 子 skill | 作用 | 允许的修改幅度 |
|---------|------|--------------|
| `py2rs-review-r0-behavior`     | 行为一致性审查（第 0 轮，所有后续审查的 gate） | **禁止改代码**，仅验证 |
| `py2rs-review-r1-rust-style`    | Rust 工程化审查（第 1 轮） | 允许小改（结构） |
| `py2rs-review-r2-error-tracing` | 错误追踪审查（第 2 轮）    | 允许小改（增加调试信息） |
| `py2rs-review-r3-io-concurrency`| IO 与并发审查（第 3 轮）    | 允许 IO 层面大改；允许算法逻辑小改 |
| `py2rs-review-r4-algo-complexity` | 算法复杂度审查（第 4 轮） | 只在有“复杂度分析 + 理论依据 + Benchmark”三件套时允许改 |
| `py2rs-review-r5-architecture`  | 架构与数据结构审查（第 5 轮） | 允许数据结构大改 |
| `py2rs-review-r6-ergonomics`    | 产品与人体工学审查（第 6 轮） | **只审查不写代码**，输出报告 |

> 共 7 个独立的审查子 skill。R0 是 R1~R6 启动的强制前置 gate。

### 8.5 调用顺序（强约束）

```text
py2rs-dep-align
    ↓
py2rs-env-bootstrap
    ↓
py2rs-runtime  (建立骨架后)
    ↓
[按脚本循环：Writer → Reviewer → Tester → 用户验收]
    ↓
py2rs-review-r0-behavior     ←— 第 0 轮：行为一致性 gate
    ↓
py2rs-review-r1-rust-style
    ↓
py2rs-review-r2-error-tracing
    ↓
py2rs-review-r3-io-concurrency
    ↓
py2rs-review-r4-algo-complexity
    ↓
py2rs-review-r5-architecture
    ↓
py2rs-review-r6-ergonomics
```

上一轮没有在 manifest 中标记 `verified`，下一轮 **禁止启动**。任何 R1~R6 审查 skill 启动时，如未发现 `reviews/r0-*-signature.md` 报告则直接拒绝。

---

## 9. manifest 规范（最小示例）

`manifest/modules.yaml`：

```yaml
modules:
  main:
    owner: rs            # py | rs | runtime
    status: verified     # planned | archived | reimplemented | verified | promoted | optimized
    path_py:  py/main.py
    path_rs:  rs/main.rs
    signature: manifest/signatures/main.json

  user_service:
    owner: py
    status: active
    path_py:  py/user_service.py
    path_rs:  null
    signature: manifest/signatures/user_service.json
```

`manifest/signatures/<name>.json`：该脚本对外的函数签名、输入、输出、异常列表——用于行为对比测试自动生成。

---

## 10. 给 AI 的操作总则（执行子 skill 前必读）

1. **先读运行时模型，再碰代码**。若 manifest 中没有该模块条目，必须先补注册再处理。
2. **一次推进一个状态**。不允许从 `reimplemented` 直接跳到 `optimized`。
3. **rs 只依赖 rs，py 只依赖 py**。跨语言必须走 runtime。
4. **审查者 ≠ 写代码者**。确认 bias 是本 skill 显式防御的目标。
5. **任何改动必须可回滚**。回滚的操作复杂度 ≈ 改 manifest 中的一个 `owner` 字段。

---

## 11. 本 skill 成功的核心指标

> 不是“代码生成成功率”，而是：
> **任意迁移进度下，系统仍然可运行。**
