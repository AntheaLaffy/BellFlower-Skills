---
name: "py2rs-review-r0-behavior"
description: "[DRAFT] 第 0 轮审查：行为一致性验证。证明 Python 实现 == 迁移版 Rust 实现。不允许改代码，仅产出对比报告。"
---

# 第 0 轮 · 行为一致性审查（R0）

> **DRAFT（草稿状态）**。下面的产物结构、输入输出都是猜想。

## 脚手架猜想（可能会有）

- `tests/compare/conftest.py` —— pytest 的 fixture，统一加载 py 与 rs 两侧的同名模块
- `tests/compare/test_<module>.py` —— 一组用例：正常路径 / 边界值 / 异常路径 / 副作用
- `tests/compare/<module>.log` —— 运行产物，格式约定：每一行 `<case> : PASS | FAIL <detail>`
- `reviews/r0-<module>-signature.md` —— 签名对比报告的模板（函数 / 参数 / 返回 / 异常 / 副作用）
- 一个 CLI：`python -m tests.compare.run --module <name>`（可选）

> 上面任何一样都可能在第一个真实项目里被推翻重写。

---

> 本 skill 是 **所有后续审查（R1~R6）启动的前置 gate**。
> 如果你在 R1 / R2 / R3 / R4 / R5 / R6 中发现“好像语义变了”，回到这里。

## 1. 本轮的唯一目标

```text
Python 实现  ==  Rust 实现
```

**用一组可重复的输入/输出对来证明上式成立。**

本 skill **不写代码、不改结构、不做任何优化**，只做一件事：生成并跑行为对比测试。

## 2. 输入

- `py/<module>.py`（原实现，已归档）
- `rs/<module>.rs`（迁移版实现）
- `manifest/signatures/<module>.json`（对外函数签名契约）

## 3. 要生成的产物

### 3.1 行为对比测试脚本

`tests/compare/test_<module>.py`（或 `.rs`），形如：

```python
for case in CASES:
    py_result = py_imp.fn(case.input)
    rs_result = rs_imp.fn(case.input)
    assert py_result == rs_result, case.label
```

其中 `CASES` 至少覆盖：

- **正常路径**：每个对外函数至少 3 条典型输入
- **边界值**：空列表、空字符串、零值、最大/最小值
- **异常路径**：非法输入、不存在的资源、网络失败
- **副作用**：写入 DB / 文件 / 缓存后的值（若可 mock）

### 3.2 一份签名对比报告

`reviews/r0-<module>-signature.md`，逐函数列出：

| 项 | Python | Rust | 状态 |
|----|--------|------|------|
| 参数列表 | `get_user(user_id: int)` | `get_user(user_id: i64)` | ✅ |
| 返回类型 | `dict \| None` | `Option<HashMap<String, Value>>` | ✅ |
| 抛出异常 | `UserNotFoundError, IOError` | `AppError::UserNotFound, AppError::Io` | ✅ |
| 副作用 | 读 DB | 读 DB | ✅ |

### 3.3 一份执行日志

`tests/compare/<module>.log`：

```text
Case normal_1          PASS
Case normal_2          PASS
Case empty_input       PASS
Case invalid_id        PASS (一致地抛出 NotFound)
Case io_failure        PASS (一致地抛出 IOError)
Total: 17 / 17 PASS
```

## 4. 若发现行为不一致怎么办

- **严禁本 skill 去“修”**。把问题写入 `reviews/r0-<module>-diff.md`
- 交给负责“迁移”的 Writer Agent 去修正，或交给 Tester Agent 补充 case
- 修正完毕后重新跑本 skill，直到 `N / N PASS`

## 5. 允许与禁止

- ✅ 允许：生成对比测试、写审查报告、更新 manifest 中的 `verified_at`
- ❌ 禁止：修改任何生产代码（py 或 rs）
- ❌ 禁止：以“这个差异其实不重要”为由跳过任何 FAIL 的 case

## 6. 结束时交付给下一轮的状态

- [ ] `tests/compare/<module>.log` 中显示 100% PASS
- [ ] `reviews/r0-<module>-signature.md` 写好并存档
- [ ] `manifest/modules.yaml` 中对应模块状态被推进为 `verified`（或保持 `verified` 并刷新 `verified_at`）
- [ ] `manifest/history/<ts>-r0-<module>.log` 记录“已通过行为一致性审查”

只有本 skill 完成后，R1~R6 才允许启动。
