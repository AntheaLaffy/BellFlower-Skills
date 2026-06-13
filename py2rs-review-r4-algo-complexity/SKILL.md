---
name: "py2rs-review-r4-algo-complexity"
description: "[DRAFT] 第 4 轮审查：算法复杂度与效率（计算机科学家视角）。只在有复杂度分析 + 理论依据 + Benchmark 三件套时才允许修改算法。"
---

# 第 4 轮 · 算法复杂度审查（R4）

> **DRAFT（草稿状态）**。很多项目其实根本不需要这一轮 —— 这是一个很有可能被整轮跳过的审查。

## 脚手架猜想（可能会有，也可能真的不需要）

- `benches/` 目录下一个 `Criterion.rs` 的基准模板
- `scripts/bench_complexity.py` 或 `rs` 侧的一个基准命令
- `reviews/r4-<module>.md` 模板：字段固定为「旧复杂度 / 新复杂度 / 理论依据 / Benchmark 数字」
- 一个 checklist：是不是真的有 O(n²) 热点？换了数据结构之后内存占用是否还能接受？

> 如果前三轮已经让代码够快、瓶颈在 IO / 网络 / DB，这一轮就直接标「无需改动」。

---

## 1. 前置检查

- [ ] 存在 `reviews/r0-<module>-signature.md`（R0 通过）
- [ ] 存在 `reviews/r1-<module>.md`、`reviews/r2-<module>.md`、`reviews/r3-<module>.md`
- [ ] `manifest/modules.yaml` 中目标模块状态 ≥ `verified`

未满足则**拒绝启动**。

## 2. 本轮目标

```text
让“复杂度”从“看不见的味道”变成“可量化的改进”
```

注意：Python 版本往往已经调用了高效的 C 扩展（numpy / pandas / sorted 等），所以 Rust 并不天然更快。**只有在算法本身可改进时才改**。

## 3. 审查清单

### 3.1 复杂度标注

- [ ] 为每个 `O(n²)` 级别的循环标注复杂度，并评估 n 的典型规模 / 最大规模
- [ ] 为涉及哈希 / 排序 / 正则 / 反序列化的操作标注成本
- [ ] 写出复杂度分析（手写一段简短 markdown，不追求形式化）

### 3.2 改进候选

典型可改进点：

- 线性扫描 → 预建 `HashMap` / `BTreeMap` / 索引
- `O(n²)` 嵌套循环 → 重排为 `O(n log n)` 或 `O(n)`
- 重复排序 / 去重 → 一次处理
- 字符串拼接（`+=`）→ `String::with_capacity` 或 `Vec<u8>`
- 反序列化 / 解析的 hot path → 检查是否可以用 `zerocopy` / `simd-json` 等

### 3.3 必须的三件套（**本 skill 最硬的约束**）

对每一个要改动的函数，必须同时产出：

1. **复杂度分析**（`旧复杂度 → 新复杂度`，说明为什么新的更优）
2. **理论依据**（例如“预建 HashMap 后查询从 O(n) 降到 O(1)”）
3. **Benchmark**（`cargo bench`、`criterion` 或至少一个手工脚本，给出改进前后的数字）

**三件套缺一则禁止修改代码。** 这是你在原始文档里的核心设计：“必须提供漏洞证据或更优算法证明。”

## 4. 允许与禁止

- ✅ 允许：在满足三件套前提下改写核心算法
- ✅ 允许：引入 `hashbrown` / `simd-json` / `rayon` 等高性能 crate（前提已在 R3 之前加入）
- ❌ 禁止：任何“我感觉更快”的改动
- ❌ 禁止：改变对外可见行为（必须回到 R0 重新验证）

## 5. 结束时的交付

- [ ] 三件套写入 `reviews/r4-<module>.md`
- [ ] `cargo bench` 或等价基准脚本有数字记录（前后对比）
- [ ] 行为对比测试（R0）重新跑过，仍为 PASS
- [ ] `manifest/modules.yaml` 中对应模块状态标记为 `optimized(r4_done)`
