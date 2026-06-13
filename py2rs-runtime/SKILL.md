---
name: "py2rs-runtime"
description: "[DRAFT] 建立 py2rs 的运行时骨架：manifest 注册、迁移状态机读写、路由协议、跨语言调用桥。是 py2rs 总 skill 的唯一事实来源和决策层。"
---

# py2rs-runtime — 运行时与迁移状态机子 skill

> **DRAFT（草稿状态）**。下面的目录、文件名、manifest schema 都是猜想；跑不通就改。
> 本 skill 目前是 AI 的 SOP，不是编译器能直接跑的代码 —— 这是刻意的，因为现在还不知道实战项目需要什么形状。

## 边界声明（运行时阶段的硬规则：manifest 只登记非 GUI 代码；router / bridge 不做窗口渲染；审查阶段不引入新依赖）

- ✅ `manifest/modules.yaml` 只登记项目里的脚本 / 模块 / 服务 / CLI / 批处理任务——**Web 后端接口脚本在这里登记没问题**，Web 端本身（HTML/CSS/JS）不需要登记
- ✅ `runtime/router.py` 只在 Python 进程内做“走 py 实现还是走 rs 实现”的分派，不做 HTTP 路由选择的改动、不做前端请求转发
- ✅ `runtime/bridge/py2rs_bridge.py` 只负责 Python ↔ Rust 的 FFI 调用，不引入任何 GUI 框架
- ❌ **不登记、不迁移任何 GUI / 桌面窗体代码**（Qt / Tk / Electron / iced / egui / Tauri 等），它们保持原样不动
- ❌ **迁移-验收循环（Stage 2~Stage 3 + R0）期间不许补依赖**——发现缺库视为 Stage 0 漏项，回到 Stage 0 补齐
- ✅ **审查阶段（R1~R6）允许引入新依赖**——允许为了 Rust 风格、错误体系、IO 并发、算法、架构等质量目标而 `cargo add` 新 crate
- ✅ Web 端（HTML/CSS/JS）天然统一，自由复用——本 skill 不产出前端改动，也不禁止你在项目其他地方继续维护它们

## 脚手架猜想（可能会有，但现在不写死）

- `manifest/modules.yaml` —— 模块清单 + owner + status + history（字段都可能改）
- `manifest/signatures/<module>.json` —— 每个脚本的对外接口签名（参数 / 返回 / 异常 / 副作用）
- `manifest/history/YYYY-MM-DD-<action>-<module>.log` —— 每次状态变更的审计日志
- `runtime/router.py` —— Python 侧唯一入口，读 manifest 分派到 py / rs / runtime
- `runtime/bridge/py2rs_bridge.py` —— FFI 桥：加载 Rust .so、参数翻译、异常翻译、trace_id 注入
- `runtime/state.py` —— manifest 读写 + 状态机合法性校验 + 一个极简 CLI `python -m runtime.state <action> <module>`
- `runtime/__init__.py` —— 让 router / state 成为包（也可能不这么组织）
- 一个 `runtime/examples/` 目录 —— 最小 demo，演示「改 manifest 一行 owner 就切实现」的感觉

> 上面每一个文件都可能在实战里被删掉、改名、合并。猜想而已。

---

> 本 skill 是 **Stage 1 骨架 + Stage 2~4 的控制器**。
> 它定义：
> - 哪些脚本存在、当前归谁（py / rs）、处于什么状态
> - 外部调用该走 Python 还是 Rust
> - 每一次迁移 / 回滚 / 验证如何更新状态

**核心信条**：所有迁移动作必须先更新运行时模型，再修改代码；所有跨语言调用必须先经过 runtime，再进入具体语言实现。

## 1. 本 skill 交付的文件（全部必须落到磁盘）

```text
manifest/
├─ modules.yaml                # 模块清单 + 迁移状态机
├─ signatures/
│   ├─ <module>.json           # 每个脚本的对外接口签名
│   └─ ...
└─ history/
    └─ <YYYY-MM-DD>-<action>.log   # 每次状态变更的审计日志

runtime/
├─ router.py                   # Python 侧入口路由（决定走 py 还是 rs）
├─ bridge/
│   └─ py2rs_bridge.py         # FFI / subprocess / IPC 桥的统一入口
└─ state.py                    # manifest 读写 + 状态迁移合法性校验

py2rs_manifest/
└─ runtime.yaml                # runtime 自身的版本与配置
```

## 2. manifest / modules.yaml（最关键文件）

### 2.1 格式

```yaml
version: 1
modules:
  <module_name>:
    owner: py | rs | runtime
    status: planned | archived | reimplemented | verified | promoted | optimized
    path_py:  py/<module>.py         # 可 null（代表未归档 / 未存在）
    path_rs:  rs/<module>.rs         # 可 null（代表未实现）
    signature: manifest/signatures/<module>.json
    verified_at: "2026-01-01T00:00:00Z"   # 或 null
    owner_history:
      - { at: "...", owner: py }
      - { at: "...", owner: rs }
```

### 2.2 状态迁移图（本 skill 强制校验）

```text
planned
  ↓ (归档旧实现)
archived(py)
  ↓ (在 rs/ 中建立同名职责实现)
reimplemented(rs)
  ↓ (py 测试 + rs 测试 + 行为对比 全部通过)
verified
  ↓ (用户真实使用验收)
promoted
  ↓ (进入 6 轮审查)
optimized
```

状态机操作规则：

- **只能前进，不能跳步**：例如 `archived → verified` 是非法的
- **允许回滚**：任何状态都可以回退到前一个状态（例如 `verified → reimplemented`），并写一条 `history`
- **禁止直接删除模块条目**：必须先把 `owner` 设为 `py`，再处理

## 3. 接口签名文件 `manifest/signatures/<module>.json`

用于行为对比测试的自动生成，以及 Writer Agent 迁移时的契约。

```json
{
  "module": "user_service",
  "functions": [
    {
      "name": "get_user",
      "args": [{"name": "user_id", "type": "int"}],
      "returns": "dict | None",
      "raises": ["UserNotFoundError", "IOError"],
      "side_effects": ["read_db", "read_cache"]
    }
  ]
}
```

字段说明：

- `returns`：Python 侧的返回类型描述（文字即可，用于生成对比测试）
- `raises`：该函数可能抛出的异常
- `side_effects`：副作用列表（非常重要——决定了行为对比测试需要 mock 哪些外部依赖）

## 4. runtime/router.py（Python 侧唯一入口）

逻辑伪码：

```python
def call(module: str, function: str, *args, **kwargs):
    # 1. 读 manifest
    entry = manifest.get(module)

    # 2. 根据 owner 决定路由
    if entry.owner == "py":
        return call_py(entry.path_py, function, *args, **kwargs)
    if entry.owner == "rs":
        return call_rs_via_bridge(function, *args, **kwargs)
    if entry.owner == "runtime":
        return call_runtime_handler(function, *args, **kwargs)

    raise RuntimeError(f"module {module} has no owner in manifest")
```

**关键点**：
- router 不理解业务，只做分派
- router 要记录每一次调用的来源（py / rs），写入 manifest/history，便于后续审查时判断影响面

## 5. runtime/bridge/py2rs_bridge.py

统一的 Python→Rust 调用桥。负责：

1. **加载 Rust 动态库**（由 `maturin develop` 产出）
2. **参数适配**：Python 对象 → Rust 能接受的类型
3. **返回值适配**：Rust 返回 → Python 对象
4. **异常翻译**：PyErr → Python 异常
5. **trace_id 注入**：把 Python 侧 `logging` / `opentelemetry` 的 trace_id 传给 Rust，让两侧日志可串联
6. **超时 / 重试**：简单的超时与重试策略（迁移期非常有用）

注意：bridge 只做技术翻译，不做业务逻辑聚合。业务逻辑必须在 py/ 或 rs/ 里。

## 6. AI 操作规范（每次执行迁移动作的强制顺序）

1. 读 `manifest/modules.yaml`，确认当前脚本的状态
2. 若模块未注册 → 先补注册（状态 `planned`），再做其它事
3. 归档旧实现（状态从 `active` → `archived`），**不要直接删文件**
4. 创建新实现（状态从 `archived` → `reimplemented`）
5. 跑测试（py 侧、rs 侧、行为对比），全部通过才更新状态为 `verified`
6. 通知用户做验收；验收通过 → `promoted`
7. 进入 6 轮审查后 → `optimized`

每一步都必须 **先写 manifest / history，再碰代码**。

## 7. 对 runtime 层的“禁区”

- 禁止在 runtime 中实现业务
- 禁止把 py 与 rs 的对象相互透传（必须经过 bridge 的翻译层）
- 禁止让 Rust 直接 import Python 模块（或反之）以“节省桥接代码”
- 禁止把 manifest 当“临时草稿”随意改；每次修改都要有 history 记录

## 8. 本 skill 验收标准

- [ ] `manifest/modules.yaml` 已初始化（至少包含一个 `_example` 模块说明格式）
- [ ] `runtime/router.py` 能跑通一个手动测试：对一个 `owner=py` 的模块调用，走 Python；对 `owner=rs` 的模块调用，走 Rust
- [ ] 写一个脚本 `runtime/state_machine_test.py`，验证：
  - `archived → verified` 这种跳步会被拒绝
  - `reimplemented → archived` 这种合法回滚可以通过
  - 每个状态变更都会写一条 `history/` 日志
- [ ] `py2rs_manifest/runtime.yaml` 中声明了 runtime 版本

## 9. 与其它子 skill 的衔接

- `py2rs-dep-align` / `py2rs-env-bootstrap`：在它们完成后才启动本 skill
- Writer（迁移）Agent：必须通过 `runtime/state.py` 暴露的 API 来推进状态
- 6 个 `py2rs-review-rN-*` 审查 skill：启动前会读 manifest，只有 `verified` 状态的模块才允许被审查；审查结束后会把状态推进到 `optimized`
