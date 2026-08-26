# Structured Output Gateway · 域夹索引（L1）

> **track**：`agent-infra` / structured-output  
> **实现包**：`app/ops/structured_output/`  
> **对照**：Agently output-control（ResponseParser + DataFlow）；**不是** Skill

---

## 本夹文件

| 文件 | 层级 | 说明 |
|---|---|---|
| [`SPEC-structured-output-gateway_v0.md`](./SPEC-structured-output-gateway_v0.md) | L2 现行契约 | P0–P3 已落地；管道与 Host 权威真值 |
| [`ROADMAP_kernel_hygiene_v0.md`](./ROADMAP_kernel_hygiene_v0.md) | L2 升级 | 域 schema 抽离；可选 acomplete 接入（后置） |

上级：[`../README.md`](../README.md) · [`../00_architecture_and_boundaries.md`](../00_architecture_and_boundaries.md) · [`../01_upgrade_roadmap.md`](../01_upgrade_roadmap.md)

相关 DESIGN：`docs/guides/DESIGN_structured-output-gateway-coexistence_v0.md`

---

## 现状一句话

管道通用；`lg_rag` 以 **complete 一次 + `parse_only`** 接入（避免双重 LLM）。下一优先：把 `schemas/*` 业务模型迁出本包，保持内核可迁移。
