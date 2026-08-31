# LAYER_README · G-L 物理分层约定

> **目录 l0 ≡ G-L0 · 目录 l1 ≡ G-L1 · 目录 l2 ≡ G-L2**  
> 正文 / task / Skill **必须**写 `G-L*` / `S-L*` / `PDD-*`，禁止裸「L0/L1/L2」作架构义。

## 目录

| 路径 | 层 | 内容 |
|------|-----|------|
| `l0/` | G-L0 | `00_main.*` · `POINTERS_cross_repo.md` |
| `l1/` | G-L1 | `01_modules.md` · `10_flow_*` / `11_flow_*` |
| `l2/` | G-L2 | `indexes/`：**分域** `by_path*.yaml` · `by_symbol*.yaml`（chat / lg_rag；禁止单文件全仓汇总） |
| `shared/` | 跨层 | `99_*` · `02_version.md` · **`graph.json`**（C1） |

## 变更策略（摘要）

| 层 | 思考 | review_hat 默认 |
|----|------|-----------------|
| G-L0 | longest | 20（高风险可 50） |
| G-L1 | tripartite | 20 |
| G-L2 | shortest | 20 |

## Skill

操作规程真值：`docs/skills/`（S-L0 / S-L1）；IDE 仅拷贝。

## 规格 POINTER

长文规格在工作区：`Projects/docs/harness/spec/graph_skill_layering_v1/`（做法 C · 不强制独立管理仓）。
