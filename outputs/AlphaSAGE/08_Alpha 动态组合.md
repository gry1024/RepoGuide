# 第 8 章：Alpha 动态组合

欢迎来到第 8 章！本章将带你理解 **Alpha 动态组合**。

## 它解决什么问题？

> **类比**：像每日换菜单的厨师长，只用历史食材做回归，当天配出最稳的 alpha 混合口味。

run_adaptive_combination.py 逐日只用历史窗口筛选 alpha，用最小二乘回归当天权重，输出日度预测与 ret_s.npy。

## 明星函数

### `run`

- **位置**：`run_adaptive_combination.py:282`
- **为何重要**：Mega-Alpha 主入口，滚动筛选+回归+预测

**关键逻辑**：

```python
for day in range(start, end):
    window = pool[day-lookback:day]
    beta = ols(window)
    pred[day] = factors[day] @ beta
```

### `remove_linearly_dependent_cols`

- **位置**：`run_adaptive_combination.py:79`
- **为何重要**：QR 分解去共线因子，保证回归数值稳定

**关键逻辑**：

```python
_, R = qr(matrix)
keep = diag(R).abs() > tol
return matrix[:, keep]
```

## 关联公式

$$
\beta = (X^\top X)^{-1}X^\top y,\quad \hat{y} = x_{pred}\,\beta
$$

## 关联文件

| 文件 | 一句话职责 |
|------|------------|
| `run_adaptive_combination.py` | Mega-Alpha 动态组合 |

---

← [第 7 章：训练主循环](07_训练主循环.md) | [目录](index.md) | [第 9 章：评估指标](09_评估指标.md) →
