# Inform 图谱补齐 · 专项 SPEC 包（ops-desk-api）

> **状态**：`draft`（规划真值 · **不含**业务改码）  
> **版本**：`v1` · `2026-08-23`  
> **上游盘点**：00 调研棒（Inform 覆盖 × CI × task 薄更新策略）  
> **Open Folder**：`ops-desk-api/`  
> **图谱真值目录**：`docs/_tech_graph/`（本包只写「应补什么」，不替代 yaml 源）

---

## 一句话

把 Phase α 之后「模块表有、flow/G-L0/G-L2 缺」的 Inform 资产，拆成 **按层 + 按模块** 的可执行补齐规格；后续每一棒只认领本包中 **一个 wave × 一个模块/层** 文件，按验收清单落盘 yaml 并跑 `./scripts/graph-compile.sh`。

**相关预留 SPEC（编译器迁移）**：[`../SPEC-harness-to-dsh-kit-graph-migrate_v0.md`](../SPEC-harness-to-dsh-kit-graph-migrate_v0.md) — `cyning-harness` → `dsh-coding-kit`；切之前须备份 `scripts/legacy/`，用完成度矩阵验证；本仓 normalize 更优则反哺 kit DEF-023。

---

## 读序（维护者 / 30 Agent）

1. 本文件（总纲与 wave 表）
2. [`00_policy_and_boundaries.md`](./00_policy_and_boundaries.md) — Phase α 边界、CI 能力、与 task 字段关系
3. [`01_execution_waves.md`](./01_execution_waves.md) — P0→P2 执行波次与依赖
4. **按波次打开**：
   - 层：`layers/G-L0_00_main.md` → `layers/G-L1_flows.md` → `layers/G-L2_indexes.md`
   - 模块：`modules/*.md`（见下表）
5. 过程纪律：`process/skill_and_task_policy.md`
6. 可选机械闸：`ci/coverage_check.md`（warn 一期 · 另开 task 实现脚本）

---

## 目录结构

```text
docs/spec/inform-graph-backfill/
├── README.md                 # 本文件 · 读序与 wave 总表
├── 00_policy_and_boundaries.md
├── 01_execution_waves.md
├── layers/
│   ├── G-L0_00_main.md
│   ├── G-L1_flows.md
│   └── G-L2_indexes.md
├── modules/
│   ├── _TEMPLATE.md          # 新模块补齐时复制
│   ├── entry.md
│   ├── api.md
│   ├── auth.md
│   ├── chat.md
│   ├── rag.md
│   ├── lc_evidence_chain.md
│   ├── lg_rag.md
│   ├── data.md
│   ├── admin.md
│   ├── llm.md
│   └── db.md
├── ci/
│   └── coverage_check.md
└── process/
    └── skill_and_task_policy.md
```

---

## Wave 总表（执行顺序）

| Wave | 目标 | 主要落点文件 | 模块 spec |
|------|------|--------------|-----------|
| **W0** | 纪律与 task 字段对齐 | `process/skill_and_task_policy.md` | — |
| **W1 · P0** | G-L0 挂全路由 + chat flow 追平代码 | `layers/G-L0_00_main.md` · `modules/chat.md` | `api.md` |
| **W2 · P0** | 旁路域 G-L1 flow（lg_rag / lc_evidence） | `layers/G-L1_flows.md` | `lg_rag.md` · `lc_evidence_chain.md` |
| **W3 · P1** | chat G-L2 indexes 追平 + 试点扩展策略 | `layers/G-L2_indexes.md` | `chat.md` |
| **W4 · P1** | RAG 域 G-L1 摘要 flow（可选折叠） | `layers/G-L1_flows.md` | `rag.md` |
| **W5 · P2** | auth/sync 补 anchors；coverage warn 脚本 | `modules/auth.md` · `ci/coverage_check.md` | `data.md` · `admin.md` |
| **W6 · P2** | 模块表「长备注瘦身」回指 flow | `modules/lg_rag.md` §6 | `01_modules.md` |

**禁止跳波**：W2 依赖 W1 的 `00_main` 已挂 HTTP 节点；W3 依赖 W1 的 `10_flow_chat` 节点 id 稳定。

---

## 模块 spec 索引

| module_id | spec 路径 | 当前图谱 | Wave |
|-----------|-----------|----------|------|
| `entry` | [`modules/entry.md`](./modules/entry.md) | G-L0 间接覆盖 | W5 |
| `api` | [`modules/api.md`](./modules/api.md) | 无独立 flow | W1 |
| `auth` | [`modules/auth.md`](./modules/auth.md) | `10_flow_auth` 已有 | W5 |
| `chat` | [`modules/chat.md`](./modules/chat.md) | `10_flow_chat` **拓扑滞后** | **W1 + W3** |
| `rag` | [`modules/rag.md`](./modules/rag.md) | 仅模块行 | W4 |
| `lc_evidence_chain` | [`modules/lc_evidence_chain.md`](./modules/lc_evidence_chain.md) | 仅模块行 | **W2** |
| `lg_rag` | [`modules/lg_rag.md`](./modules/lg_rag.md) | 仅模块行长备注 | **W2** |
| `data` | [`modules/data.md`](./modules/data.md) | `11_flow_sync_to_chat` 部分 | W5 |
| `admin` | [`modules/admin.md`](./modules/admin.md) | 同上 | W5 |
| `llm` | [`modules/llm.md`](./modules/llm.md) | 外部节点 | W5 |
| `db` | [`modules/db.md`](./modules/db.md) | 外部节点 | — |

---

## 每棒开工检查（摘自 Harness）

1. 新建或认领 `docs/tasks/active/task_inform_graph_backfill_<wave>_<slug>.md`
2. `graph_change_layer` / `graph_delta` **必须指向本包具体路径**，禁止只写「改模块表半句」除非 W6
3. 30 前：`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_*.md`
4. 改 yaml 后：`./scripts/graph-compile.sh` exit 0
5. `HG-GRAPH-MODULES`：若只改 flow 不改模块边界 → 备注「不新增一级模块」即可

---

## 非范围（整包）

- 不改 `app/` 业务 Python（除非另开功能 task）
- 不实现 AST / 全仓自动生图（产品边界）
- 不把「无 graph_query」当本仓故障主因
- 不扩散 `ops-desk-web` / `ops-desk-ios` 物理分层
- 本包 **draft** 阶段不自动改 `docs/_tech_graph/**/*.graph.yaml`

---

## 关联路径

| 路径 | 说明 |
|------|------|
| `docs/_tech_graph/README.md` | 图谱读序 |
| `docs/_tech_graph/l1/01_modules.md` | G-L1 模块真值（已齐 · 待 W6 瘦身） |
| `docs/tasks/done/task_glayer_phase_alpha_api.md` | Phase α 完成态 / 不做全仓 G-L2 |
| `docs/harness/evidence/EVAL_tech_graph_third_party_20260730.md` | CI 能力边界定稿 |
| `docs/skills/s-l1-tech-graph-ops/SKILL.md` | 日常操作规程（待 W0 补丁 POINTER） |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-23 | v1 初稿：00 调研棒落盘 · 分模块 spec 包 |
