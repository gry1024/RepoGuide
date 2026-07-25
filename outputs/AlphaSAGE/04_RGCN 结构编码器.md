# 第 4 章：RGCN 结构编码器

欢迎来到第 4 章！本章将带你理解 **RGCN 结构编码器**。

## 它解决什么问题？

> **类比**：像给公式做语法树体检，把算子当节点、按关系连边，再用图神经网络读出结构。

把 RPN token 序列转成关系图，用 RGCNConv 按六类边关系传递消息，再全局平均池化得到表达式结构嵌入。

## 明星函数

### `GNNEncoder.forward`

- **位置**：`src/alpha_gfn/modules.py:96`
- **为何重要**：多层 RGCNConv + 全局池化，结构感知的核心前向

**关键逻辑**：

```python
x = self.embed(tokens)
for conv in self.convs:
    x = conv(x, edge_index, edge_type)
return global_mean_pool(x, batch)
```

### `_build_graph_from_rpn`

- **位置**：`src/alpha_gfn/modules.py:13`
- **为何重要**：RPN 序列转关系图，定义六类边类型

**关键逻辑**：

```python
nodes, edges = parse_rpn(rpn_tokens)
edge_index, edge_type = build_relations(nodes)
return Data(x=nodes, edge_index=edge_index, edge_type=edge_type)
```

## 关联公式

$$
h_i^{(l+1)} = \text{ReLU}\left(\sum_{r}\sum_{j\in N_r(i)} W_r^{(l)} h_j^{(l)}\right)
$$

## 关联文件

| 文件 | 一句话职责 |
|------|------------|
| `src/alpha_gfn/modules.py` | RGCN 编码器与图构建 |

---

← [第 3 章：GFlowNet 生成框架](03_GFlowNet 生成框架.md) | [目录](index.md) | [第 5 章：Alpha 池管理](05_Alpha 池管理.md) →
