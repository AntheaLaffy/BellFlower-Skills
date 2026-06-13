---
name: "py2rs-review-r3-io-concurrency"
description: "[DRAFT] 第 3 轮审查：消除阻塞 IO 与不必要等待。引入 async、tokio、rayon。允许 IO 层面大改；允许算法逻辑小改以匹配 IO。"
---

# 第 3 轮 · IO 与并发审查（R3）

> **DRAFT（草稿状态）**。是否用 tokio、是否引入 rayon、是否真的需要 async，都可能在实战里被推翻。

## 脚手架猜想（可能会有）

- `rs/src/main.rs` 的 `#[tokio::main] async fn main()` 模板
- `rs/src/` 下一个 `http.rs` / `fs.rs` / `db.rs` 的 async 化示例
- `Cargo.toml` 中 `tokio = { version = "*", features = ["full"] }` 的初始依赖（实际 feature 会缩）
- 一个基准脚本 `scripts/bench_io_async_vs_sync.py` —— 跑前后性能对比
- `reviews/r3-<module>.md` 模板 —— 记录并发改造 + 基准数字

> 实战里也可能完全不需要 async（某些小脚本同步更快）。这里只是一个可能的审查路线。

---

## 0. 前置检查（强约束）

**本 skill 必须在 R0 / R1 / R2 均完成之后启动。**必须同时满足：

- [ ] 存在 `reviews/r0-<module>-signature.md`（R0 通过）
- [ ] 存在 `reviews/r1-<module>.md`（R1 通过）
- [ ] 存在 `reviews/r2-<module>.md`（R2 通过）
- [ ] `manifest/modules.yaml` 中目标模块状态 ≥ `verified`

若任一未满足，**本 skill 直接拒绝启动**。

## 1. 本轮要解决的味道

```text
同步 IO  ↔  等待 ↔  等待 ↔  等待
```

Python 版本通常是串行同步的。迁移到 Rust 后，最容易直接获得收益的就是并发与并行能力。

## 2. 引入的依赖

```bash
cargo add tokio --features full
cargo add rayon
cargo add reqwest --features json   # 若有 HTTP
```

## 3. 审查清单

### 3.1 识别阻塞点

- [ ] 读文件：`std::fs::read_to_string` → `tokio::fs::read_to_string`
- [ ] HTTP：`reqwest::blocking` → `reqwest` async
- [ ] DB：若用 `sqlx`，直接启用其 async runtime；若使用自建同步驱动，本阶段先标为 TODO（避免大范围驱动改动）
- [ ] 循环中互相独立的 N 次调用 → `futures::join_all!` / `rayon::par_iter()`

### 3.2 async 化

- [ ] `main` 函数改为 `#[tokio::main] async fn main()`（或保留同步壳，业务函数全部 `async fn`）
- [ ] 对外暴露给 Python 的桥接函数如果必须保持同步，内部用 `runtime.block_on(...)` 托管异步逻辑；**不允许在 tokio runtime 内部再次 block_on 当前 runtime**（会死锁）
- [ ] runtime 的 bridge 层明确标注“同步调用 async”的边界

### 3.3 并发数控制

- [ ] 并行请求加 `Semaphore` 限制并发
- [ ] 大规模数据处理用 `rayon`
- [ ] 没有无界并发

### 3.4 日志一致性（R2 的延续）

- [ ] async 任务 spawn 时传递 `trace_id`，日志仍然可串联

## 4. 允许与禁止（本阶段最关键的边界）

- ✅ 允许：IO 路径改造（从同步到异步，或从单线程到并行）
- ✅ 允许：为匹配新 IO 模型做 **小幅度** 的算法/结构调整（比如把一个遍历的内部类型从 `Vec<String>` 改到 `Stream<Item=String>`）
- ❌ 禁止：在没有充分理由的情况下把算法复杂度从 O(n log n) 改成别的（那是 R4）
- ❌ 禁止：引入 `Mutex`/`RwLock` 的复杂嵌套（那是 R5 要重新审视的）

## 5. 必须做的性能对比

本轮结束前至少跑一份基准：

- 改造前：`cargo build --release` + 跑一遍 `tests/bench/<module>.py`，得到基准耗时
- 改造后：再跑一遍，报告相对提升 / 下降
- 若有下降：要么回滚，要么在 `reviews/r3-<module>.md` 中给出理由（例如“为了稳定性放弃 5% 性能”）

## 6. 结束时的交付

- [ ] `cargo build`、`cargo test` 通过
- [ ] `cargo clippy` 无严重 warning
- [ ] 有一份基准对比报告（含数字）
- [ ] 行为对比测试仍为 PASS
- [ ] `reviews/r3-<module>.md`
