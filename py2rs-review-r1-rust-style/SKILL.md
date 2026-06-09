---
name: "py2rs-review-r1-rust-style"
description: "[DRAFT] 第 1 轮审查：把 Python 风格的 Rust 改写为工程化 Rust。引入 mod.rs / lib.rs / trait / crate 划分 / 生命周期整理。允许结构层面小改，不允许改业务语义。"
---

# 第 1 轮 · Rust 工程化审查（R1）

> **DRAFT（草稿状态）**。下面的目录结构建议都是猜想。

## 脚手架猜想（可能会有）

- `rs/src/lib.rs` 模板 —— 对外暴露一个稳定 `pub mod ...` 结构
- `rs/src/<domain>/mod.rs` 模板 —— 一个领域一个目录
- `rustfmt.toml` / `.clippy.toml`（可选）—— 统一风格与 lint 级别
- `reviews/r1-<module>.md` 模板 —— 本轮审查报告要填的栏目

> 具体拆几个 crate、mod 怎么切，实战项目里定，不是这里能预言的。

---

## 1. 前置检查（在任何改代码前必须做）

**本 skill 必须在 `py2rs-review-r0-behavior` 之后启动。**启动前必须确认：

- [ ] 目标模块在 `manifest/modules.yaml` 中状态为 `verified` 或更高
- [ ] 存在 `tests/compare/<module>.log` 且显示 100% PASS（由 R0 skill 产出）
- [ ] 存在 `reviews/r0-<module>-signature.md`（由 R0 skill 产出的签名对比报告）
- [ ] 目标模块已有 `manifest/signatures/<module>.json`（供本审查用作契约）

若任一未满足，**本 skill 直接拒绝启动**。

## 2. 本轮目标

```text
Python 风格 Rust
       ↓
  工程化 Rust
```

迁移刚完成时的代码通常长这样：

```rust
// rs/main.rs —— 一眼看就是从 py 直译过来的
pub fn get_user(user_id: i64) -> ... { ... }
pub fn save_user(user: &User) -> ... { ... }
pub fn crawl() -> ... { ... }
```

本 skill 把它推进到标准 Rust 工程形态：

```text
rs/
├─ main.rs              # 仅保留入口（CLI / 服务启动）
├─ lib.rs               # library root
├─ user/
│   ├─ mod.rs
│   ├─ model.rs
│   └─ service.rs
└─ crawler/
    ├─ mod.rs
    └─ http.rs
```

## 3. 具体审查清单

### 3.1 目录与模块

- [ ] `main.rs` 不再包含业务函数，仅做入口 / 参数解析 / 启动 runtime
- [ ] 存在 `lib.rs`，对外暴露需要被 runtime 调用的 API
- [ ] 每个领域至少有一个 `mod.rs`（或者直接用 `name.rs` 也可，但要显式规划好）
- [ ] `pub` 只暴露真正对外需要的 API，内部函数为私有

### 3.2 类型与 trait

- [ ] 相同业务概念有统一的类型（例如不再到处写 `HashMap<String, String>` 而是 `pub struct User { ... }`）
- [ ] 合理使用 trait 来表达“可存储 / 可序列 / 可克隆”这类通用能力，而不是一堆自由函数
- [ ] 没有无意义的 `Clone` 爆炸（这是迁移代码最常见的味道）

### 3.3 生命周期与借用

- [ ] 函数参数尽量 `&str` / `&[T]`，而不是传 `String` / `Vec<T>` 的所有权
- [ ] 生命周期标注只在编译器提示需要时才加上；不会为“炫技”而加
- [ ] 没有 `Arc<Mutex<_>>` 的过度嵌套（留到 R5 再大规模重构，但本轮要标出来）

### 3.4 错误（本轮只做小改，不引入统一的错误体系——那个是 R2 的事）

- [ ] 没有 `unwrap()` / `expect()` 在非测试代码中出现，或者显式注释“为什么安全”

## 4. 本轮允许与禁止

- ✅ 允许：模块 / 文件结构调整、类型抽出、trait 抽象引入、生命周期整理、可见性收敛
- ✅ 允许：函数改名到更 Rust 的命名（例如 `get_user` → `fetch_user` 视业务而定），只要 `manifest/signatures/<module>.json` 中的对外契约层被同步更新（在 bridge 处保留同名入口即可）
- ❌ 禁止：改变对外行为语义（包括返回值含义、异常类型、外部可见副作用）
- ❌ 禁止：引入 async / tokio / rayon（那是 R3）
- ❌ 禁止：修改算法 / 数据结构选型（那是 R4 / R5）

## 5. 结束时的交付

- [ ] 代码已按新的 mod / lib 结构组织
- [ ] `cargo build` 无 warning 或仅有可解释的 warning
- [ ] `cargo test` 全部通过
- [ ] `tests/compare/<module>.log` 再次运行仍为 PASS（R0 的后置验证）
- [ ] 在 `manifest/modules.yaml` 中把该模块状态推进为 `optimized`（若这是最后一轮，则直接写 `optimized_at: ...`）
- [ ] 写入审查报告 `reviews/r1-<module>.md`
