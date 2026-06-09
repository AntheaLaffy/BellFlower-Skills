---
name: "py2rs-review-r5-architecture"
description: "[DRAFT] 第 5 轮审查：架构与数据结构（资深软件工程师视角）。允许数据结构大改；关注所有权模型、Arc<Mutex> 使用、API 设计。"
---

# 第 5 轮 · 架构与数据结构审查（R5）

> **DRAFT（草稿状态）**。这一轮具体怎么切 crate / 怎么拆 mod，完全取决于项目本身；下面的“猜想”最多是启发。

## 脚手架猜想（可能会有）

- `rs/crates/` 或 `rs/src/<domain>/` 的一个拆分建议模板
- `rs/src/error.rs` / `rs/src/model.rs` / `rs/src/service.rs` 的“默认三区”建议（但不是教条）
- `reviews/r5-<module>.md` 模板：列出改动前 / 后的数据结构、为什么改
- `cargo clippy --all-targets -- -D warnings` 的 lint 门槛（作为 R5 的结束标志之一）

> 真实项目可能把 R5 拆成多次小 PR，而不是一次性“大重构”。
> **另外：本 skill 仅重构后端的架构与数据结构**。前端组件结构、GUI 框架选型等一律不碰。

---

## 0. 前置检查（强约束）

- [ ] 存在 `reviews/r0-<module>-signature.md`（R0 通过）
- [ ] 存在 `reviews/r1-<module>.md` ~ `reviews/r4-<module>.md`（前 4 轮审查报告齐全）
- [ ] `manifest/modules.yaml` 中目标模块状态 ≥ `verified`

未满足则**拒绝启动**。

## 1. 本轮聚焦

> “好的程序员关心数据结构和它们之间的关系。” —— Linus Torvalds（你在原始文档中引用的核心依据）

本阶段跳出“逐函数优化”，审视：

- 数据结构是否适合业务语义
- 所有权模型是否清晰（谁拥有什么、借用关系是否成环）
- 模块之间的 API 是否稳定、可扩展、可测试

本轮是允许**大规模重构**的最后一轮。

## 2. 审查清单

### 2.1 数据结构

- [ ] 频繁增删头部 / 尾部的 `Vec<T>` → 考虑 `VecDeque<T>`
- [ ] 需要保留插入顺序同时需要查找 → `BTreeMap` / `IndexMap`
- [ ] 配置 / 枚举应该用 `enum { A, B, C }`，而不是 `String` + `match` + `panic!("unreachable")`
- [ ] 跨线程共享的对象：是否必须 `Arc<Mutex<...>>`，还是能拆成“部分只读 + 部分独享”，以减少锁竞争

### 2.2 所有权与并发安全

- [ ] 没有 `Arc<Mutex<HashMap<...>>>` 被整颗树锁住的场景（典型反模式）
- [ ] 能改成 `RwLock` 的，不使用 `Mutex`；能避免同步的就避免
- [ ] 明确哪些结构“永远只在一个线程里用”，哪些需要跨线程
- [ ] 没有 `unsafe` 代码，除非有显式的 `// SAFETY: ...` 注释

### 2.3 API 设计

- [ ] 对外 API 尽量接受 `&str` / `&[T]`，而不是所有权
- [ ] 返回值优先 `Result<T, E>`，而不是 `Option<T>`（有明确“正常空”语义时例外）
- [ ] 构建器（Builder）模式替代“有 10 个参数的 new 函数”
- [ ] 类型系统防止误用（例如“把 UserId 和 PostId 区分成不同 newtype，而不是都是 i64”）

### 2.4 模块边界

- [ ] 每个 crate / module 的公开 API 面积极小
- [ ] 没有“跨模块互相依赖造成的循环”（Rust 编译器会阻止，重点在于领域建模）
- [ ] 可单独测试、可 mock

## 3. 允许与禁止

- ✅ 允许：数据结构重构（可能大改）
- ✅ 允许：引入 newtype、Builder、trait 对象、`Arc<->RwLock` 替换等所有权层面的调整
- ✅ 允许：把某个 crate 拆成多个 crate（如果确实能显著降低耦合）
- ❌ 禁止：在没有 R0 回归验证的情况下合并任何改动

## 4. 结束时交付

- [ ] `reviews/r5-<module>.md`：记录所有被“升格”的数据结构及其理由
- [ ] `cargo clippy --all-targets -- -D warnings` 无 warning（推荐作为 R5 硬门槛）
- [ ] R0 行为对比测试仍为 PASS
- [ ] 更新 `manifest/modules.yaml`：`optimized(r5_done)`
