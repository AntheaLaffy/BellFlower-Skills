---
name: "py2rs-review-r2-error-tracing"
description: "[DRAFT] 第 2 轮审查：统一错误与追踪体系。引入 tracing/anyhow/thiserror，让错误能定位到文件 / 函数 / 调用链。允许小改。"
---

# 第 2 轮 · 错误与追踪审查（R2）

> **DRAFT（草稿状态）**。具体用哪个日志框架可能改（tracing / log / slog 都有可能）。

## 脚手架猜想（可能会有）

- `rs/src/error.rs` —— 统一的 `AppError` 枚举 + `thiserror` derive 的模板
- `rs/src/lib.rs` 里的 `tracing_subscriber::fmt::init()` 初始化代码段
- 一个 `rust-toolchain.toml` ？（如果项目需要固定工具链）
- `reviews/r2-<module>.md` 模板 —— 记录本轮引入了哪些 tracing span / error context

> `anyhow::Result<T>` 这种全局简写是否合适，也可能在实战里被推翻。
> **另外：本 skill 仅处理后端代码的错误与追踪**。前端 / GUI 的错误展示不属于这里。

---

## 0. 前置检查（强约束）

**本 skill 必须在 `py2rs-review-r0-behavior` 与 `py2rs-review-r1-rust-style` 均完成之后启动。**必须同时满足：

- [ ] 存在 `reviews/r0-<module>-signature.md` 且显示签名一致（R0 通过）
- [ ] 存在 `reviews/r1-<module>.md`（R1 已产出报告）
- [ ] `manifest/modules.yaml` 中目标模块状态 ≥ `verified`

若任一未满足，**本 skill 直接拒绝启动**。

## 1. 本轮要解决的味道

迁移后的代码常见这类问题：

```rust
// 味道 A：笼统的 Err
return Err("something failed");

// 味道 B：到处 .expect("...")，没有调用链
let data = fetch().expect("fetch failed");

// 味道 C：没有日志，线上出问题全靠猜
```

本轮把它推进到：

```rust
use thiserror::Error;
use anyhow::{Result, Context};
use tracing::{info, warn, error, info_span};

#[derive(Debug, Error)]
enum AppError {
    #[error("user {0} not found")]
    UserNotFound(i64),
    #[error(transparent)]
    Io(#[from] std::io::Error),
}

fn do_work(user_id: i64) -> Result<()> {
    let span = info_span!("do_work", user_id);
    let _enter = span.enter();

    let data = fetch(user_id)
        .with_context(|| format!("fetch failed for user {user_id}"))?;
    Ok(())
}
```

## 2. 必须引入的依赖

若在 `py2rs-dep-align` 阶段已经加入则跳过，否则补齐：

```bash
cargo add thiserror anyhow
cargo add tracing tracing-subscriber
```

## 3. 审查清单

### 3.1 错误体系

- [ ] 所有对外的 `pub fn` 返回类型统一为 `Result<T, AppError>` 或 `anyhow::Result<T>`
- [ ] 使用 `thiserror` 定义业务错误枚举，给每个错误一个稳定语义（而不是字符串）
- [ ] 使用 `anyhow::Context` / `.with_context(|| ...)` 给调用链添加上下文
- [ ] 非测试代码里不允许裸 `unwrap()`，除非伴随显式 `// safety: ...` 注释

### 3.2 日志 / 追踪

- [ ] 在 `main.rs`（或 lib 的初始化处）调用一次 `tracing_subscriber::fmt::init()` 或等价初始化
- [ ] 关键函数（对外 API、IO 函数）都有 `info_span!` / `debug_span!`
- [ ] 错误路径至少打一条 `error!(err = ?err)`，把结构化错误写进日志
- [ ] 日志中能看到 `py2rs-runtime` 注入的 trace_id（由 Python 侧传入的上下文）

### 3.3 对外契约一致性

- [ ] `manifest/signatures/<module>.json` 中的 `raises` 列表与 Rust 代码能抛出的业务错误枚举一致
- [ ] Python 侧的 bridge 能把 Rust 的业务错误翻译为对应 Python 异常（而不是笼统的 `PyRuntimeError`）

## 4. 允许与禁止

- ✅ 允许：引入 `thiserror` / `anyhow` / `tracing`，重构返回类型、增加 span、补充错误上下文
- ❌ 禁止：改变算法 / IO 模型（那是 R3）
- ❌ 禁止：改变行为语义（仍然要过 R0 行为一致性测试）

## 5. 结束时的交付

- [ ] `cargo build`、`cargo test` 通过
- [ ] 手动跑一个会触发错误路径的用例，确认日志里能看到：文件、函数名、调用参数、底层错误原因
- [ ] `tests/compare/<module>.log` 仍为 PASS
- [ ] 审查报告 `reviews/r2-<module>.md`
