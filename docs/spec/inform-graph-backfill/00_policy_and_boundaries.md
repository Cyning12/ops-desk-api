# 00 · 政策与边界

> **受众**：00/10 规划 · 30 执行前必读  
> **真值**：本文件 + `docs/tasks/done/task_glayer_phase_alpha_api.md` + `EVAL_tech_graph_third_party_20260730.md`

---

## 1. Phase α 已交付什么

| 项 | 状态 | 证据 |
|----|------|------|
| 物理目录 `l0/l1/l2/shared` | ✅ | `docs/_tech_graph/LAYER_README.md` |
| 模块真值 `l1/01_modules.md` | ✅ | 含 `rag` / `lc_evidence_chain` / `lg_rag` |
| G-L0 `00_main` | ✅ 但 **滞后** | 未挂 lc/lg HTTP；锚点行号旧 |
| G-L1 flow | ✅ 仅 3 条 | auth · chat · sync→chat |
| G-L2 indexes | ✅ **仅 chat 试点** | `l2/indexes/*` |
| `graph-compile.sh` + CI | ✅ | `.github/workflows/tech-graph.yml` |

**Phase α 明示不做**（`task_glayer_phase_alpha_api.md` L62）：

- web/ios 物理搬家
- 回灌 cyning-harness（Phase β）
- **全仓 G-L2 覆盖**

结论：试点收窄的是 **完成态**，不是关掉 tech-graph CI。

---

## 2. 为何后续开发「图谱没跟上」

根因分层（本仓过程纪律 · 非产品 AST 缺失）：

| 层 | 机制 | 效果 |
|----|------|------|
| Task 验收 | `graph_delta` 几乎恒为 `01_modules.md` 一行/半句 | lg_rag Phase1–4、lc_evidence HTTP 均 **不要求** 新建 `10_flow_*` |
| Skill 默认 | `s-l1-tech-graph-ops` 热点 flow 仅 3 条；G-L2 只提 chat | Agent 合法地不画旁路拓扑 |
| 人闸 | `HG-GRAPH-MODULES` 护模块表人签 | **不**机械校验「新路由是否进 flow」 |
| CI | `graph yaml check` 文档内闭环 | 漏画仍全绿 |

本补齐包的目的是：**把「薄更新」升级为可验收的分层资产**，仍不追求全仓 G-L2。

---

## 3. Inform 三层在本仓的职责

| 层 | 回答的问题 | 本仓补齐目标 |
|----|------------|--------------|
| **G-L0** | 系统有哪些对外入口域？谁依赖谁？ | `00_main` 挂全 `/api/ops/*` 一级路由 + POINTER 到 G-L1 |
| **G-L1** | 某域内主流程 / 条件边 / HTTP→图？ | 新建/刷新 `10_flow_*`；**禁止**把整张状态机只写进 `01_modules` 备注 |
| **G-L2** | 改哪个文件哪个 symbol 影响哪条边？ | 先 **chat 追平**；lg_rag 为 **P2 可选第二试点**（见 `layers/G-L2_indexes.md`） |

---

## 4. CI 与本包的关系

**已启用**：`tech-graph.yml` → `./scripts/graph-compile.sh`（无 pilot 开关）。

**CI 断言**：

- yaml → md 编译一致
- yaml → `shared/graph.json` 一致
- harness `graph yaml check` 通过

**CI 不断言**（本包 W5 才可选加 warn 脚本）：

- `app/ops/router.py` 与 G-L0 节点集合一致
- 一级模块是否有对应 `10_flow`
- G-L2 indexes 与 `implementedBy` 同步
- 锚点行号与源码一致

**本仓已断言（2026-08-24）**：`graph_mermaid_normalize.py --check`（mermaid 围栏无 `//`、无旧边 `--"…"-->`）。治根与切 `dsh-coding-kit` 见 `docs/spec/SPEC-harness-to-dsh-kit-graph-migrate_v0.md`。

每棒验收仍以 **`graph-compile.sh` exit 0** 为硬门槛；coverage 脚本一期 **warn only**。

---

## 5. graph_change_layer 填写约定（补齐棒专用）

| 变更类型 | `graph_change_layer` | `graph_delta` 示例 |
|----------|---------------------|-------------------|
| 只改 `00_main` 挂路由 | `G-L0` | `docs/_tech_graph/l0/00_main.graph.yaml` |
| 新建/改 `10_flow_*` | `G-L1` | `docs/_tech_graph/l1/10_flow_lg_rag.graph.yaml`（新建） |
| chat 增节点 + indexes | `mixed` | flow yaml + `l2/indexes/by_path.yaml` |
| 仅缩短 `01_modules` 备注 | `G-L1` | `docs/_tech_graph/l1/01_modules.md` |
| coverage 脚本 | `none` | `scripts/graph_coverage_check.py`（若开 task） |

**禁止**：功能 task 再把 Phase 3/4 拓扑只写进模块表而不建 flow（除非维护者显式选 W6-only）。

---

## 6. 与现有 flow 的兼容

| 现有 graph_id | 处理策略 |
|---------------|----------|
| `00_main` | **增量** 加节点/边；不删 chat  POINTER |
| `10_flow_chat` | **破坏性刷新** 拓扑（追加 retrieve/grade/refuse）；保持 graph_id |
| `10_flow_auth` | 保持；W5 补 anchors / 可选 `implementedBy` |
| `11_flow_sync_to_chat` | 保持；W5 核对 data 只读端点 |

新建：

- `10_flow_lc_evidence`（建议 graph_id）
- `10_flow_lg_rag`（建议 graph_id；内含 basic/router/supervisor 折叠说明）

---

## 7. 验收口径（包级）

- [ ] W1 后：`00_main` 含 lc-evidence / lg-rag 路由节点，且 `POINTERS_cross_repo.md` 更新
- [ ] W1 后：`10_flow_chat` 与 `app/ops/chat/graph.py` 拓扑同构（节点名可对齐或文档化映射表）
- [ ] W2 后：存在 `10_flow_lc_evidence` + `10_flow_lg_rag` yaml，且 G-L0 有 `::triggers` 或等价 POINTER
- [ ] W3 后：`l2/indexes` 含 `rag_nodes.py` 三节点；`graph-compile` 绿
- [ ] W6 后：`lg_rag` 模块表备注 ≤ 3 行 + POINTER 到 flow
