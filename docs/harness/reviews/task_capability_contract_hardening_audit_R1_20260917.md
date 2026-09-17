# Task Audit R1：capability-contract-hardening

> **hat_id**：20-task-audit  
> **task**：`docs/tasks/active/task_capability_contract_hardening.md`  
> **上游**：`docs/discussions/2026-09-17_interview_gaps_adoption_and_landing_v0.md` §1 A · §5 波次 α · §8 阶段 H  
> **10 invoke**：`docs/harness/invokes/by-task/capability-contract-hardening/invoke_20260917_10_task_capability-contract-hardening.md`  
> **00 invoke**：`docs/harness/invokes/by-task/capability-contract-hardening/invoke_20260917_00_start_capability-contract-hardening.md`  
> **日期**：2026-09-17 · 审查人：20-task-audit  
> **分支**：`task/capability-contract-hardening`（本帽核实）  
> **task lint**：本帽复跑 `npx spec-wave task lint --file docs/tasks/active/task_capability_contract_hardening.md` → **PASS**

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS** · 零内容阻塞 · 不退回 10 |
| **流程闸** | `HG-AUDIT-R1` **仍 pending**（正确 · 20 不代签）· `HG-TASK-DRAFT` / `HG-GRAPH-MODULES` 均为 pending |
| **30 授权** | **未签发** · pending 时禁止附 30 Prompt；真值在 task 人工闸表 |

**总评**：阶段 H 波次 α（A–F）竖切可执行；范围/非范围/验收/failure_paths/思考轮/元信息齐全；未静默扩 β/T/W/P。

---

## 审查核对（对照上游 §1 A / §5 α / §8 H · 00/10 invoke · 用户审查要点）

| # | 审查点 | 结论 |
|---|--------|------|
| 1 | 范围锁死阶段 H（A–F） | **通过**。范围节显式 A–F 同竖切；背景写「一竖切 CLOSE」；与 §5 α 项 1–5 对齐（schema/校验、tool args、allowlist、tenant_scoped、观测） |
| 2 | 非范围显式排除 T/W/P | **通过**。非范围专节列阶段 T/W/P；跟进节再钉 T/W 串行；failure_paths 含「误扩 T/W/P → 审查拒收」 |
| 3 | 波次 β（supervisor 预算）未进验收 | **通过**。非范围明列「波次 β · supervisor 总步数/墙钟预算」；跟进指向讨论稿 §5 项 6。注：§8 H 行文字含「supervisor 预算」，本 task **按 §5 α 锁死并排除 β**——与 00 范围锁及审查要点一致，**非扩 scope** |
| 4 | 验收可勾选、可测 | **通过**。A–F 各有路径/行为断言 + 点名测文件；另有 pytest 列表、ruff、graph-compile、lint-wiki-delta、`chat/graph.py` 零 diff |
| 5 | failure_paths 覆盖 schema / allowlist / tenant / 闸拒开工 | **通过**。含 `HG-AUDIT-R1` pending 拒开工、args_schema 不合规、allowlist 外、`tenant_scope_missing`、未知 id、既有 Policy 挡、误扩 T/W/P、注册中心误称、业务不变量入 schema |
| 6 | R0–R5 / 思考轮控制 | **通过**。控制表 R0–R4 有结论；R4 `early_stop=yes` + reason（上游已钉 A–F 与 H→T→W；锚点已扫清；R5 无新增决策面）；`residual_risks` 写 B 兼容拖长 / C 安全默认须 30 钉死；R5 标明未开；正文 R0–R4 回填闭合 |
| 7 | `graph_change_layer` / `wiki_delta` / `test_strategy` / 人工闸表 | **通过**。`graph_change_layer=G-L1` + graph_delta 路径；`wiki_delta=n/a` + note；`test_strategy=required` + note（离线、覆盖四类）；闸表三行 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 齐全且均为 pending |
| 8 | 口径 F（注册表≠注册中心；业务不变量不进 args_schema） | **通过**。范围 F + 钉死契约 F + 验收 F + failure_paths 两行。注：§5 β 项 7 亦写口径文档，本 task **前移 F 进 α**——对齐 §1 A P0 口径/纪律与审查要点，合理 |
| 9 | 静默扩 scope（β / 写 / 多租户产品） | **未扩**。写能力仅「强制校验写进注释/ROADMAP」与 `approval_id` 字段名预留；多租户仅构造性单租户注入 + `tenant_scoped` 机制，明禁 Workspace；β 预算非范围 |
| 10 | 行为变更 · 旧测 grep 影响面（K7） | **已钩（弱但够）**。本 task 改校验/allowlist 默认/租户门——属行为变更；验收末条点名 6 个既有测文件须绿 + 现状锚点列回归面。非阻塞建议：30 自检可附 `grep` 触及清单（`args_schema` / `CANDIDATE_CAPABILITY_IDS` / `ainvoke`），不退回 10 |
| 11 | 10 钉死契约 vs 实现歧义 | **通过**。无 schema 不校验、有 schema 失败不抛垮、args 优先 input 兼容、禁止 None=全开、缺租户拒、F 用词——均可测 |
| 12 | 必读列表 / 真实代码锚点 | **通过**。锚点表与必读列表覆盖 types/gateway/policy/defaults/manifest/lookups/strategy/subtasks/nodes 与归档 task |

---

## 阻塞

无。

---

## 非阻塞风险（不退回 10 · 00/30 知情即可）

1. **§8 H 行 vs §5 α**：上游阶段 H 总表含「supervisor 预算」，本 task 按波次 α 排除——正确；00 派 30 时勿被 §8 总表诱扩 β。  
2. **上游 α 写 lookup/retrieve**：本 task D 仅钉 `get_issue_by_number` / `get_pr_by_number`；仓内 capability 包未见独立 `retrieve` 注册缺口陈述。若后续发现 retrieve 类能力，跟进另开，不阻塞本竖切。  
3. **C 安全默认**：空 allowlist vs 最小只读集留给 30 钉死（R4 residual）——验收已要求「禁止静默全开」+ 单测，可接受。  
4. **B 兼容风险**：task 已预留跟进拆 `task_capability_tool_args_v2`；默认不拆合理。  
5. **K7**：建议 30 自检显式列出旧测影响面 grep 结果（非本波 task 必改）。

---

## 回填清单

无（内容零阻塞 · **不改** task 实质 · **不改**人工闸表 status）。

---

## 签收

**内容签收 · PASS**（终轮 R1）。  
流程闸 `HG-AUDIT-R1` 仍 **pending**（本帽不签发）——**可交 00 代签** `HG-TASK-DRAFT` + `HG-AUDIT-R1`（及本 task 行 `HG-GRAPH-MODULES` 若改 G-L1 备注）；pending 期间禁止下发 30 Prompt。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（00 代签 · 维护者令开启 · 日期）
- [ ]（建议同签）HG-TASK-DRAFT → approved
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
