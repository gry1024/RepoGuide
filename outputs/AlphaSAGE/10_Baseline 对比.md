# 第 10 章：Baseline 对比

欢迎来到第 10 章！本章将带你理解 **Baseline 对比**。

## 它解决什么问题？

> **类比**：像同场竞技的对照组，PPO、QCM、AFF 各显神通，用以衡量 GFlowNet 的优势。

PPO、QCM（分布式 RL）、AFF 三类基线，与 GFlowNet 共享数据与池接口，用于对照验证生成与组合效果。

## 明星函数

### `run`

- **位置**：`train_ppo.py:95`
- **为何重要**：PPO 基线入口，与 GFN 共享环境与池

**关键逻辑**：

```python
for step in range(steps):
    traj = rollout(policy, env)
    loss = ppo_loss(traj)
    loss.backward()
```

### `run`

- **位置**：`train_qcm.py:14`
- **为何重要**：QCM 分布式 RL 基线入口，对照生成质量

**关键逻辑**：

```python
for worker in workers:
    worker.sample(env)
loss = qcm_loss(batch)
loss.backward()
```

### `run`

- **位置**：`combine_AFF.py:106`
- **为何重要**：AFF 融合组合入口，对照 Mega-Alpha 效果

**关键逻辑**：

```python
aff = AttentionFusion()
for alpha in pool:
    out = aff(alpha)
return out
```

## 关联文件

| 文件 | 一句话职责 |
|------|------------|
| `train_ppo.py` | PPO 基线训练入口 |
| `train_qcm.py` | QCM 分布式 RL 基线 |
| `combine_AFF.py` | AFF 融合组合基线 |

---

← [第 9 章：评估指标](09_评估指标.md) | [目录](index.md)
