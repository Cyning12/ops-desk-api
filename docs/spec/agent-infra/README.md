# Agent Infra · 长期 SPEC 包

> **用途**：LangGraph 旁路（`lg_rag` 等）之上的**应用层基础设施**契约；与单次业务 task 解耦，可跨版本迭代。  
> **状态约定**：`draft` → `active` → `stable`；破坏性契约变更升 `_vN`；升级路线写 `ROADMAP_*`，不污染 v0 已落地契约正文。  
> **上游讨论**：`docs/discussions/`（含 2026-08-26 架构对照 + 后续会话结论）  
> **下游落地**：须另开 `docs/tasks/active/task_*.md` + 人工闸；**本目录本身不授权 30 改码**。

---

## 文档层级（读序）

| 层 | 路径 | 写什么 | 不写什么 |
|---|---|---|---|
| **L0 总纲** | 本 README | 索引、读序、命名边界、当前状态表 | 实现细节 |
| **L0 架构** | [`00_architecture_and_boundaries.md`](./00_architecture_and_boundaries.md) | Agent / Graph / Capability / SO 边界；Mode A；静态图+动态 plan | 波次验收清单 |
| **L0 升级总表** | [`01_upgrade_roadmap.md`](./01_upgrade_roadmap.md) | 跨模块升级顺序与依赖（讨论结论落盘） | 单 SPEC 契约条文 |
| **L1 域夹** | `capability/` · `structured-output/` | 该域 README + 现行 SPEC + 域 ROADMAP | 跨域总序（回指 L0） |
| **L2 现行契约** | `*/SPEC-*_v0.md` | 已签收、P0–P3 已落地的接口与失败语义 | 未开工升级设想 |
| **L2 升级路线** | `*/ROADMAP_*_v0.md` | 下一波可拆 task 的升级规格 | 直接授权 30 |

```text
docs/spec/agent-infra/
├── README.md                              # L0 总纲（本文件）
├── 00_architecture_and_boundaries.md      # L0 架构边界
├── 01_upgrade_roadmap.md                  # L0 升级总表
├── capability/                            # L1 域：能力网关
│   ├── README.md
│   ├── SPEC-capability-gateway_v0.md      # L2 现行契约（P0–P3 已落地）
│   └── ROADMAP_portable_core_v0.md        # L2 升级：可迁移内核 / Mode A
├── structured-output/                     # L1 域：结构化出口
│   ├── README.md
│   ├── SPEC-structured-output-gateway_v0.md
│   └── ROADMAP_kernel_hygiene_v0.md       # L2 升级：schema 抽离等卫生项
├── SPEC-capability-gateway_v0.md          # POINTER（兼容旧链）
└── SPEC-structured-output-gateway_v0.md   # POINTER（兼容旧链）
```

**推荐读序（维护者 / 00）**：本 README → `00_architecture` → `01_upgrade_roadmap` → 认领域夹 README → 现行 SPEC → 对应 ROADMAP → 再开 task。

---

## 命名边界（强制）

| 名称 | 管什么 | 不是什么 |
|---|---|---|
| **Capability Gateway** | 节点 ↔ 外置能力（local_fn / MCP / sandbox / CLI / skill） | 业界 LLM Gateway；不是 LangGraph `ToolNode` 本身 |
| **Structured Output Gateway** | LLM 文本 → 校验/纠偏/预算重试 → 结构化结果 | Skill；不是模型可选 tool |
| **编排壳（StateGraph）** | 静态拓扑 + 解释 plan | Agently Agent 的完整 1:1；默认不动态 compile 新图 |
| **LLM Gateway**（本仓另议） | 应用 ↔ 模型供应商 | 本包当前**不**立 SPEC |

---

## 当前资产状态

| ID | 现行契约 | 状态 | 下一升级（ROADMAP） |
|---|---|---|---|
| `capability-gateway` | [`capability/SPEC-capability-gateway_v0.md`](./capability/SPEC-capability-gateway_v0.md) | active · P0–P3 已落地 · PR #59 | [`ROADMAP_portable_core_v0`](./capability/ROADMAP_portable_core_v0.md) · **优先** |
| `structured-output-gateway` | [`structured-output/SPEC-structured-output-gateway_v0.md`](./structured-output/SPEC-structured-output-gateway_v0.md) | active · P0–P3 已落地 · PR #58 | [`ROADMAP_kernel_hygiene_v0`](./structured-output/ROADMAP_kernel_hygiene_v0.md) · 穿插卫生 |

---

## 迭代规则

1. **现行契约（SPEC v0）**：只改已落地行为的勘误与修订记录；新设想进 ROADMAP。  
2. **ROADMAP**：可拆 task 的升级规格；**不**直接授权 30；落地后把「已完成」波次回写 ROADMAP + 必要时升 SPEC `_v1`。  
3. **破坏性变更**：新文件 `_vN`，本 README 换链；旧路径可留 POINTER。  
4. 与 Agently 对照只作思想对齐，禁止拖进运行时依赖。  
5. 首批接入面仍优先 `lg_rag`；**不**默认改 `chat/graph.py`。

---

## 关联

| 类型 | 路径 |
|---|---|
| 讨论小结（初版） | `docs/discussions/2026-08-26_lg-rag-agent-capability-architecture.md` |
| Phase 4 设计 | `docs/guides/DESIGN_langgraph-lg-rag-phase4-multiagent_v1.md` |
| SO 与原生 API 并存 | `docs/guides/DESIGN_structured-output-gateway-coexistence_v0.md` |
| Capability skill 划界 | `docs/guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md`（若存在） |
| 图谱前后对比 | `docs/guides/COMPARE_tech-graph-agent-infra-gateways_v0.md` |
| 实现包 | `app/ops/capability/` · `app/ops/structured_output/` |

---

## 修订记录

| 日期 | 摘要 |
|---|---|
| 2026-08-26 | 建索引；挂 capability / structured-output 两份 SPEC |
| 2026-08-26 | **细分文档层级**：L0 架构+升级总表；L1 域夹；L2 SPEC/ROADMAP；旧 SPEC 路径改 POINTER；讨论结论写入升级路线 |
