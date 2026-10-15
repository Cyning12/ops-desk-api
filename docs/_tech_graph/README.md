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
6. （可选）交互浏览：[`../arch-browser/README.md`](../arch-browser/README.md) — 消费 `graph.json` + Host 大纲的**衍生 HTML**；改图后可 `./scripts/arch-browser-build.sh`

## 主线与 legacy 阅读约定（2026-09-23）

- **主线**：`lg_rag` 复杂 Agent（见 `l1/10_flow_lg_rag.md`）；目标形态对齐 [Agent Host 完整框架大纲](../discussions/2026-09-23_agent-host-full-framework-outline_v0.md)。
- **先读**：`l1/01_modules.md` 的「主线与遗留约定」节（legacy / dormant / 内部依赖面标记真值）。
- **legacy（非默认读）**：`l1/10_flow_chat.md`（旧主线 · `/chat/stream` 已 410 · 保留作历史拓扑）——仅在维护 WS/models/sessions 兼容或查历史拓扑时针对性读取。
- **dormant / 内部依赖面**：`app/ops/skill_registry/**`（H5 stub · 无运行时消费方）、`rag` / `lc_evidence_chain`（主线内部依赖 · 非独立演进面）——不针对性读取则不纳入默认上下文。

## 编译

```bash
./scripts/graph-compile.sh
```
