# 第 3 章：GFlowNet 生成框架

欢迎来到第 3 章！本章将带你理解 **GFlowNet 生成框架**。

## 它解决什么问题？

> **类比**：像一个多路探险家，同时派许多路径去采样不同 alpha，而非只走一条最优路。

基于 Trajectory Balance 的 GFlowNet，通过前向/后向策略估计器和熵正则项，采样多样化 alpha 表达式轨迹。

## 明星函数

### `EntropyTBGFlowNet.loss`

- **位置**：`src/alpha_gfn/gflownet.py:81`
- **为何重要**：TB 损失核心，直接对应论文 L_TB 公式

**关键逻辑**：

```python
log_pf, log_pb, log_r = traj_scores
loss = (log_pf - log_pb - log_r + log_z).pow(2).mean()
loss -= lam * entropy
```

### `EntropyTBGFlowNet.get_trajectories_scores`

- **位置**：`src/alpha_gfn/gflownet.py:23`
- **为何重要**：计算 log_pf/log_pb 与熵项，损失的数据来源

**关键逻辑**：

```python
log_pf = self.forward(states)
log_pb = self.backward(states)
return log_pf, log_pb, reward
```

## 关联公式

$$
L_{TB} = \mathbb{E}\left[\left(\log\frac{P_F(\tau)}{P_B(\tau)R(\tau)} + \log Z\right)^2\right] - \lambda_H H(\pi)
$$

$$
H(\pi) = -\sum_a \pi(a)\log\pi(a)
$$

## 关联文件

| 文件 | 一句话职责 |
|------|------------|
| `src/alpha_gfn/gflownet.py` | TB 损失与轨迹采样 |

---

← [第 2 章：表达式与算子体系](02_表达式与算子体系.md) | [目录](index.md) | [第 4 章：RGCN 结构编码器](04_RGCN 结构编码器.md) →
