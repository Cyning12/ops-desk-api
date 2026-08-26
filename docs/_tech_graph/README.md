# docs/_tech_graph · 读序（PDD-0）

> **一句话**：ops-desk-api 技术图谱物理分层真值。  
> **何时读**：改路由/表/事件/LangGraph 节点前；新会话 onboarding。  
> **不要**：默认 `cat` 全目录；G-L2 仅在 path/倒排命中后打开。

## 读序

1. 本文件 → [`LAYER_README.md`](./LAYER_README.md)（目录缩写 ≡ G-L\*）
2. G-L0：[`l0/00_main.md`](./l0/00_main.md) · [`l0/POINTERS_cross_repo.md`](./l0/POINTERS_cross_repo.md)
3. G-L1：[`l1/01_modules.md`](./l1/01_modules.md) → 按需 `l1/10_flow_*.md`
4. G-L2：[`l2/indexes/`](./l2/indexes/)（chat 试点）
5. 协议 / export：[`shared/`](./shared/) · **`shared/graph.json`**（唯一机器轨真值）

## 编译

```bash
./scripts/graph-compile.sh
```
