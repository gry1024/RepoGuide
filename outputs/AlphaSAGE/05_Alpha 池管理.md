# 第 5 章：Alpha 池管理

欢迎来到第 5 章！本章将带你理解 **Alpha 池管理**。

## 它解决什么问题？

> **类比**：像选秀节目的待定席，新选手要与现有成员比相关性，达标才入围、末位被淘汰。

维护候选 alpha 集合，按 IC 与互相关阈值筛选入池，支持基于嵌入的 KNN 查找与末位淘汰，保存为 pool_*.json。

## 明星函数

### `AlphaPoolGFN.try_new_expr`

- **位置**：`src/alpha_gfn/alpha_pool.py:28`
- **为何重要**：入池判定核心，IC 与互相关阈值决定去留

**关键逻辑**：

```python
ic = calc_ic(expr, target)
if ic < threshold: return False
for existing in self.pool:
    if abs(calc_ic(expr, existing)) > corr_thresh:
        return False
self.pool.append(expr)
```

### `AlphaPoolGFN._find_k_nearest_neighbors`

- **位置**：`src/alpha_gfn/alpha_pool.py:90`
- **为何重要**：基于嵌入 L2 距离的 KNN，SSL 奖励的前置

**关键逻辑**：

```python
dists = (embeddings - query).pow(2).sum(-1)
idx = dists.topk(k, largest=False).indices
return [self.pool[i] for i in idx]
```

## 关联公式

$$
r_{NOV} = 1 - \max_k |IC_{mut,k}|
$$

## 关联文件

| 文件 | 一句话职责 |
|------|------------|
| `src/alpha_gfn/alpha_pool.py` | Alpha 池入池淘汰与 KNN |

---

← [第 4 章：RGCN 结构编码器](04_RGCN 结构编码器.md) | [目录](index.md) | [第 6 章：多维奖励函数](06_多维奖励函数.md) →
