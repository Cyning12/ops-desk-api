# Task：图谱 × Skill 物理分层 · Phase α（ops-desk-api）

> **状态**：completed  
> **类型**：图谱 / Skill 试点落盘（无业务功能改码）  
> **关联**：`docs/_tech_graph/` · `docs/skills/` · 规格包 `Projects/.../graph_skill_layering_v1/`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `glayer-phase-alpha-api` |
| **git_branch** | `task/glayer-phase-alpha-api-v1` |
| **graph_change_layer** | `mixed` |
| **review_hat** | `20` |
| **review_hat_reason** | `""` |
| **thinking_profile** | `tripartite` |
| **skill_refs** | `[s-l0-project-map, s-l1-tech-graph-ops]` |
| **invoke_retention_profile** | `default` |
| **required_invoke_hats** | `10,30,40` |
| **test_strategy** | `recommended` |
| **test_strategy_note** | `./scripts/graph-compile.sh`；文件存在性；无业务 pytest 增量 |
| **code_quality_bar** | `not_applicable` |
| **experience_capture** | `recommended` |

### 拍板默认（C1–C4）

| ID | 采用 |
|----|------|
| C1 | `shared/graph.json` 为真值；根目录过渡双写副本 |
| C2 | 闸改指 `l1/01_modules` 后，根 stub **≥1 Epic** 再删 |
| C3 | 「初步完善」= 迁移 DoD + 回灌门槛 + 人签（本 task 仅 api α） |
| C4 | 本仓先包递归 export；形状稳后再回灌产品 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-PILOT-OPSDESK-GLAYER** | approved | **30** | 维护者 2026-07-27：批准 api/web 物理分层试点；采 C1–C4；B1–B5 同意建议 |
| **HG-GRAPH-MODULES** | approved | **30** | 模块表真值迁至 `l1/01_modules.md`；根 `01_struct.md` stub 保留 |
| HG-TASK-DRAFT | approved | 22-R1 | 对齐回合已审方案；本 task 合并骨架+modules+export+chat G-L2+skills |
| HG-AUDIT-R1 | approved | 30 | 无业务逻辑改码；仅文档/图谱/脚本 |

---

## 背景与目标

把平铺 `docs/_tech_graph` 升为物理分层（G-L0/G-L1/G-L2），Skill 真值落 `docs/skills`，递归 export 跑通。

**完成态**：

- [x] `l0|l1|l2|shared` + `LAYER_README`（目录 l0≡G-L0）
- [x] `l1/01_modules.md` 为模块真值；根 stub；AGENTS 闸路径已更新
- [x] chat 域 G-L2：`implementedBy` + `l2/indexes`
- [x] `docs/skills` S-L0 + S-L1
- [x] `./scripts/graph-compile.sh` 递归通过；`shared/graph.json` 产出
- [x] 未改 web/ios 源码；未改 Projects 规格

**不做**：web 物理搬家；ios 分层；回灌 cyning-harness（Phase β）；全仓 G-L2 覆盖

---

## 范围

- [x] 物理骨架与文件迁入 `l0/l1/l2/shared`
- [x] export 脚本递归（B1）
- [x] 模块表 / AGENTS 闸路径
- [x] chat G-L2 倒排
- [x] `docs/skills` + IDE 拷贝说明
- [x] `l0/POINTERS_cross_repo.md`

## 非范围

- `ops-desk-web` / `ops-desk-ios` 目录实施
- 业务 Python 行为变更

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|---|---|---|---|
| `HG-PILOT-OPSDESK-GLAYER` pending | 拒开工 | 是 | 须维护者签闸 |
| 仅迁目录未改递归 export | compile 漏图 / 空 json | 是 | A7/C4 硬依赖 |
| 闸路径漏改 | 误拒/误放 | 是 | AGENTS + stub 双保险 |

---

## 验收标准

- [x] 存在 `docs/_tech_graph/{l0,l1,l2,shared}` 与 `docs/skills/s-l0-*`、`s-l1-*`
- [x] 模块真值在 `l1/01_modules.md`；`HG-GRAPH-MODULES` 路径已更新
- [x] chat G-L2 indexes 可按 path/symbol 反查
- [x] `./scripts/graph-compile.sh` 绿
- [x] 正文无裸架构义「L0/L1/L2」（目录名与历史引用除外）

---

## 关联路径

1. `docs/_tech_graph/`
2. `docs/skills/`
3. `scripts/graph-compile.sh` · `scripts/graph_yaml_to_json.py`
4. `AGENTS.md`

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-27 |
| **帽** | 40（补录；与 30 同 Agent） |
| **命令** | `./scripts/graph-compile.sh` → 0；`harness verify --task …/task_glayer_phase_alpha_api.md` → 见下；路径存在性 → 0 |
| **验收** | 5/5 pass（见 `invoke_20260727_40_glayer-phase-alpha-api.md`） |
| **已知未测** | 全量 pytest（本 task 无业务改码义务） |
| **过程债** | 首次未先落 10/40 invoke 即执行 30；已补 `invoke_*_10_*` / `invoke_*_40_*` |
| **产品跟进** | pre-30 硬闸需求已交 cyning-harness：`SPEC-verify-pre30-invoke-hats-gate_v1` + `Projects/.../task_cyning_harness_verify_pre30_invoke_hats_gate_v1.md`；**本仓等 2.14+ upgrade 后再 dogfood** |
| **下一棒** | 维护者审 diff → commit/PR；Phase β / harness upgrade 另 task |

Phase α 本仓落盘完成。未改 web/ios/Projects 规格。
