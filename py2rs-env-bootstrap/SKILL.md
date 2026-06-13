---
name: "py2rs-env-bootstrap"
description: "[DRAFT] 打通 Python/Rust 混合运行环境。用最小 Demo 验证 FFI 调用、参数/返回值/错误传递、async 调度、日志追踪。py2rs 流水线 Stage 0 的后半部分。"
---

# py2rs-env-bootstrap — 跑通环境子 skill

> **DRAFT（草稿状态）**。下面的 demo 结构、文件数、工具链都是猜想，真正上手项目时可能要改。

## 边界声明（跑通环境阶段的硬规则：只验证 py↔rs 混合运行；不做 GUI 构建；Stage 0 的依赖必须在这里先对齐好）

- ✅ 本阶段要跑通的东西：Python 调 Rust（maturin / pyo3 路径）、参数与返回值、错误传递、tokio async、tracing 日志串起来、并发调用不崩
- ❌ **不跑任何 GUI 构建 / 桌面窗口启动**：不引入 PyQt / Tk / eframe / iced / tauri / egui 等 GUI 框架，不启动任何窗口渲染
- ❌ Web 端（HTML / CSS / JS）**天然不需要在这里验证**——它本来就和后端解耦，直接复用即可
- ❌ **迁移-验收循环（Stage 2~Stage 3 + R0）期间不许补依赖**——发现缺库视为 Stage 0 漏项，回到 Stage 0 补齐
- ✅ **审查阶段（R1~R6）允许引入新依赖**——允许为了 Rust 风格、错误体系、IO 并发、算法、架构等质量目标而 `cargo add` 新 crate

如果你在 `demo/` 目录下看到 GUI 相关的窗口/组件代码，默认视为本 skill 失败。

## 脚手架猜想（可能会有）

- `demo/Cargo.toml` —— 声明 `[lib] crate-type = ["cdylib", "rlib"]`
- `demo/src/lib.rs` —— 一个 `#[pyfunction] fn greet(name: &str) -> String`，再加几个可能会 `return Err(...)` 的函数
- `demo/python/demo_*.py` —— 5 个小用例：hello / error / async / tracing / concurrent
- `pyproject.toml` —— maturin build backend 的最小配置
- `demo/run_all.py` 或 `Makefile` —— 总验收脚本，跑 5 个 demo 全部通过才算完

> 实际用什么构建工具（maturin / setuptools-rust / 纯 cffi）还没定；先用 maturin 试试，不行再换。

---

> 属于 py2rs 的 **Stage 0（后半）**。
> 目标：在写任何业务迁移代码之前，先证明“Python 能调 Rust、Rust 能回传、异步能跑、错误能定位、日志能串起来”。
> 本阶段不追求业务正确，只追求 **环境可靠**。

## 1. 为什么单独作为一个 skill

- 混合编程环境一旦不稳，后面所有迁移代码都无法被信任
- 这是最容易出现“静默失败”的阶段：编译通过但行为错位、跨线程崩溃、Python GIL 与 Rust async 冲突
- 把它从依赖对齐里拆出来，是为了让失败场景可定位、可回滚

## 2. 必须跑通的最小 Demo 矩阵

你需要在仓库里建立一个 `demo/` 目录，并逐一验证下列用例：

| # | Demo 名称 | 验证点 | 输出必须可见 |
|---|-----------|--------|--------------|
| 1 | `hello_py2rs` | Python 调 Rust，传字符串 / 整数 / 列表，回传结构化值 | Python 侧 `print` 可见 Rust 返回 |
| 2 | `propagate_error` | Rust 侧返回错误，经由 FFI / bridge 以 Python 异常形式抛出 | Python 侧 `try/except` 能捕获，含错误信息与调用栈 |
| 3 | `async_roundtrip` | Rust 侧 `tokio::spawn` / `.await`，Python 侧 `asyncio` 能等待结果 | 无数据 race，无未初始化返回 |
| 4 | `tracing_span` | Rust 侧 `tracing::info_span!` + Python 侧 `logging` 或 `tracing` 桥，输出结构化日志 | 一条日志里可见 py→rs→py 的完整链路 id |
| 5 | `concurrent_call` | 并发调用 100 次 Demo 1，确认不崩、不漏、不锁 | 全部成功，统计次数正确 |

每个 Demo 必须有：

- 一个 `Cargo.toml` 条目 / 或 demo crate
- 一个 Python 入口脚本 `demo/<name>.py`
- 一个 `README.md`（极简）说明预期输出

## 3. 推荐骨架（Maturin 路线）

```text
demo/
├─ Cargo.toml                # 声明 [lib] crate-type = ["cdylib", "rlib"]
├─ src/
│   ├─ lib.rs                # pyo3 暴露的模块入口
│   ├─ hello.rs
│   ├─ errors.rs
│   ├─ async_rt.rs
│   └─ tracing_demo.rs
├─ python/
│   └─ demo_<name>.py        # 每个 case 一个脚本
└─ pyproject.toml            # maturin build-backend
```

`lib.rs` 最小示例（仅示意，具体代码由你实际写）：

```rust
use pyo3::prelude::*;

#[pyfunction]
fn greet(name: &str) -> String {
    format!("hello from rust, {}", name)
}

#[pymodule]
fn py2rs_demo(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(greet, m)?)?;
    Ok(())
}
```

构建与运行：

```bash
maturin develop --release
python3 demo/python/demo_hello.py
```

## 4. 必须通过的验收脚本

在本 skill 末尾，运行一个 **总验收脚本** `demo/run_all.py`（或 `Makefile` 的一个 target），它：

1. 依次跑 5 个 demo
2. 为每个 demo 打印 `CASE <name>: PASS / FAIL`
3. 结束时输出总结：

```text
5/5 cases passed
py2rs-runtime-env: READY
```

**只要有 1 个 case FAIL，本 skill 就没有完成。**

## 5. 完成后写入 manifest

在 `py2rs_manifest/stage0.yaml` 追加：

```yaml
env-bootstrap:
  status: done
  at: <ISO-TS>
  demo_results:
    hello_py2rs:         PASS
    propagate_error:     PASS
    async_roundtrip:     PASS
    tracing_span:        PASS
    concurrent_call:     PASS
  notes:
    - "Python GIL 与 tokio runtime 未死锁"
    - "错误以 PyException 形式在 Python 侧可被捕获"
    - "tracing span id 在 Python/Rust 两侧一致"
```

## 6. 失败时的标准回滚动作

- **编译不通过** → 回到 `py2rs-dep-align`，检查 Rust 工具链 / crate 版本
- **FFI 加载失败** → 检查 `maturin develop` 是否在正确虚拟环境中运行
- **async 死锁** → 检查 `pyo3` 的 `auto-initialize` feature 与 Python `asyncio` 事件循环兼容性
- **日志不串** → 统一使用一个 trace_id（可由 Python 侧生成，注入到每次 FFI 调用的上下文中）

## 7. 与运行时 skill 的衔接

- `py2rs-runtime` 会复用你在本阶段验证过的 FFI / async / 错误 / 日志方案
- 你在此阶段选择的 `pyo3` + `tokio` + `tracing` 组合会被写入 `py2rs_manifest/dependencies.yaml` 的 `bridge` 段，供后续所有子 skill 参考
