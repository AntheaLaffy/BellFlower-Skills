---
name: "py2rs-dep-align"
description: "[DRAFT] 对齐 Python / Rust / FFI / async / 错误追踪 三方依赖；生成清单；优先用 cargo add 锁定最新版。py2rs 流水线 Stage 0 的前半部分。"
---

# py2rs-dep-align — 依赖对齐子 skill

> **DRAFT（草稿状态）**。下面的依赖清单、文件路径、工具选择都是猜想，可能会被实战项目推翻。
> 不承诺一次写对；跑不通时回到这里修订。

## 依赖管理（对齐阶段的硬规则：先列出 py↔rs 等价依赖；能力范围不相当的依赖不纳入）

- ✅ Python 侧：项目原有业务依赖（保持原样不动） + `maturin` / `pytest`（仅用于构建扩展、跑测试）
- ✅ Rust 侧：`pyo3`（FFI） / `tokio`（异步运行时） / `thiserror` + `anyhow`（错误） / `tracing`（日志） / `rayon`（并行） / `serde` + `serde_json`（序列化），以及项目已经在用的等价库——**每一个 Python 依赖都必须在这里找到一个能力范围相当的 Rust 依赖对应物**
- ✅ **像 Qt 这种“每种语言都有成熟桥接”的 GUI 框架：允许纳入**——只要 Python 侧（PyQt/PySide）与 Rust 侧（`cxx-qt` / `qmetaobject-rs` / `rust-qt` 等）的能力范围相当，渐进式替换就有基础
- ❌ **强绑定特定 GUI 库、且 Rust 侧没有同等语义对应物的依赖：不纳入**——例如重度依赖 Kivy 的自定义渲染管线、重度依赖某个 WinForms 控件的行为语义、重度依赖 Tk 的布局模型
- ❌ Web 端（HTML / CSS / JS）天然统一且与后端解耦，**不需要走 py↔rs 替换路径**，所以不在这里引入 npm / yarn / pnpm / vite / webpack
- ❌ **迁移-验收循环（Stage 1~Stage 3 + R0）期间不许补依赖**——如果你在迁移某个脚本时发现“没这个库就写不出来”，视为 Stage 0 漏项，应先回到本阶段补齐依赖并更新 skill / 脚手架，再重新跑迁移-验收
- ✅ **审查阶段（R1~R6）允许引入新依赖**——允许为了 Rust 风格、错误体系、IO 并发、算法、架构等质量目标而 `cargo add` 新 crate，前提是每轮结束时行为一致性测试仍能通过

如果你在依赖清单里看到“某个 Python 依赖找不到能力范围相当的 Rust 对应物”，**视为本 skill 失败**——要么回到 Stage 0 补一个，要么把该脚本从迁移范围中移出；如果在 Stage 1~Stage 3 / R0 的迁移-验收循环期间发现缺依赖，**视为 Stage 0 漏项，需要回到 Stage 0 补齐**；审查阶段（R1~R6）`cargo add` 新东西是允许的，但必须能保持行为一致。

## 脚手架猜想（可能会有）

- `pyproject.toml` 或 `requirements.txt` —— Python 侧依赖（maturin / pyo3 构建）
- `Cargo.toml` 模板 —— pyo3 / tokio / thiserror / anyhow / tracing / rayon / serde / serde_json 的初始依赖（实际版本让 `cargo add` 自动选）
- `py2rs_manifest/dependencies.yaml` —— 依赖对齐清单（字段、结构都可能改）
- `cargo.lock` 的纳入方式 —— 可能 git 追踪，也可能不追踪，取决于项目
- 一个 `make deps` 或 `script/bootstrap.sh` —— 一键装齐所有依赖的脚本（猜想，不一定用）

> 所有 above 都是猜想。实战里哪个好用留哪个，哪个反人类就删哪个。

---

> 属于 py2rs 的 **Stage 0（前半）**。
> 目标：把混合运行环境需要的所有依赖“先拉齐、再谈业务”。

## 1. 目标产物

本 skill 执行完毕后，仓库里必须有且仅有：

- `requirements.txt` 或 `pyproject.toml`（Python 侧依赖）
- `Cargo.toml` + `Cargo.lock`（Rust 侧依赖，由 `cargo add` 自动维护）
- `py2rs_manifest/dependencies.yaml`（一个统一的依赖对齐清单，供 runtime 和审查 skill 查询）

**不允许手写版本号串**。Rust 侧一律使用 `cargo add <crate>` 让 Cargo 选最新稳定版。

## 2. 三类依赖分别对齐

### 2.1 Python 侧依赖

确认 / 补齐：

- 项目原有业务依赖（保留原样，不动）
- 桥接 / FFI 侧：`maturin`（用于构建 Rust 扩展）
- 测试与行为对比：`pytest`、若有需要 `pytest-asyncio`

操作：

```bash
# 1. 列出当前环境已安装依赖
pip freeze > requirements_before.txt

# 2. 补齐缺少的 FFI / 构建依赖
pip install maturin
```

### 2.2 Rust 侧依赖

用 `cargo add` 安装（优先使用最新稳定版，避免手写版本）：

- **基础 FFI / Python 桥**：`pyo3`（带 `extension-module` feature，按需）
- **异步运行时**：`tokio`（至少 features = `["full"]` 或 `"rt-multi-thread","macros","io-util","time"`）
- **错误体系**：`thiserror` + `anyhow`
- **日志 / 追踪**：`tracing` + `tracing-subscriber`
- **并发 / 并行**：`rayon`（如果后续 IO 审查会用到）
- **序列化 / 反序列化**：`serde` + `serde_json`（用于 runtime 与 manifest 交互）

操作示例：

```bash
cargo init --name <project>       # 如果还没有 Cargo.toml
cargo add pyo3 --features extension-module
cargo add tokio --features full
cargo add thiserror anyhow
cargo add tracing tracing-subscriber
cargo add rayon
cargo add serde --features derive
cargo add serde_json
```

### 2.3 跨语言 / 构建依赖

- Python：`maturin` 必须可执行
- Rust：工具链 `stable` 可用（`rustc --version`、`cargo --version`）
- （可选）若走 `setuptools-rust` 路线：列出相应依赖

## 3. 输出的依赖清单（`py2rs_manifest/dependencies.yaml`）

格式如下（必须写磁盘，供后续 skill 读取）：

```yaml
python:
  runtime:
    - name: maturin
      version: "x.y.z"   # 由 pip freeze / maturin --version 采集
  dev:
    - name: pytest
      version: "..."

rust:
  - name: pyo3
    version_from_cargo_lock: true
  - name: tokio
    features: ["full"]
  - name: thiserror
  - name: anyhow
  - name: tracing
  - name: tracing-subscriber
  - name: rayon
  - name: serde
  - name: serde_json

bridge:
  build_backend: maturin
  ffi_crate: pyo3
  async_runtime: tokio
  error_stack: thiserror+anyhow
  tracing_stack: tracing+tracing-subscriber
```

## 4. 检查清单（必须全部 green 才视为完成）

- [ ] `cargo --version` 可用
- [ ] `python3 --version` 可用
- [ ] `maturin --version` 可用
- [ ] `cargo build` 能通过空项目（或你当前项目）的编译
- [ ] `Cargo.lock` 已生成并提交纳入版本控制
- [ ] `py2rs_manifest/dependencies.yaml` 已生成
- [ ] 运行时依赖中 async / 错误 / 日志三条线都存在对应 crate

## 5. 完成后向总 skill 回传的状态

写入 `py2rs_manifest/stage0.yaml`：

```yaml
stage: dep-align
status: done
at: <ISO-TS>
notes:
  - "rust toolchain: 1.xx"
  - "pyo3: x.xx"
  - "tokio: x.xx"
  - "maturin: x.xx"
```

后续 `py2rs-env-bootstrap` 会读取这份文件，避免重复探测。
