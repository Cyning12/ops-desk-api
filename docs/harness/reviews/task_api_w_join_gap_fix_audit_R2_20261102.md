# 审查文 · task_api_w_join_gap_fix · 20-R2（2026-11-02 · 复审）

| 字段 | 值 |
|------|-----|
| **审查对象** | `docs/tasks/active/task_api_w_join_gap_fix.md`（commit `8b47be5` · 承接 R1 FAIL 修订版） |
| **审查帽** | 20-task-audit · R2（复审 R1 findings 闭环 + 双仓扩范围新增完整性） |
| **日期** | 2026-11-02 |
| **前序** | R1 审查文 `docs/harness/reviews/task_api_w_join_gap_fix_audit_R1_20261102.md`（FAIL · B1+M1–M3） |
| **结论** | **PASS-WITH-MINOR**（blocker ×0 · minor ×1 · note ×3）——R1 全部 findings 核验闭环；余 1 项 minor 为 30 前程序补救项，不构成内容阻塞 |

---

## 结论摘要

- **内容面**：R1 的 B1/M1/M2/M3/N3 五条 findings 逐字核验全部闭环（见下表）；双仓扩范围引入 1 个新 minor（M4 · web 仓 GATE_VERIFY 闸据缺位，30 前须补救——属程序补救项，本审查结论维持通过）。范围/非范围、钉死契约、failure_paths、验收可判定性、思考轮回填闭合均复检通过。
- **流程闸**：`HG-AUDIT-R1` = **pending**（待维护者依据本 R2 结论签收）· `HG-GRAPH-MODULES` / `HG-W-FIX-DESIGN` 均 pending。闸表未动（符合分工）。30 开工授权以维护者签闸为真值。

---

## R1 findings 闭环核验（逐条对照修订后行号）

| R1 finding | 落点（修订后行号） | 核验 |
|------------|--------------------|--------|
| **B1** FP-5 可达性链条断裂 | `:41③` 补「与 A5 可达性绑定：web `onResume` 过期 mapping 已列入本 task 范围」· `:65` 现状锚点补「`onResume` catch `:173-180` 无 mapping（409 透传 `:176` · 泛化 `:179`）」实证 · `:78` 过期出口钉死补配套 web 薄改 · `:90` 新增范围条 W-fix-1-web · `:95` 非范围收窄为「web 其余业务码」· `:112` failure_path 双条件（文案不含「过期」**或** web mapping 未落地）· `:125` A5 验收链路明示「api resume 过期出口 → web `onResume` mapping → FP-5 行级提示可达」· 元信息 `:17` implement_repo 双仓 · `:19` web 质量门 · `:22-25` graph/wiki_delta web 侧评估 · `:31` orchestration 双分支双 PR | ✅ **闭环**——码面事实摆进签决策面，A5 达成路径与③选型绑定，五处联动无漏；锚点行号（`:173-180`/`:176`/`:179`/`:150`）与 R1 抽验值一致 |
| **M1** 闸决策点缺终态 | `:41④` 补「单据终态语义（`STATUS_EXPIRED` 启用与否）· 与正文『单据终态』行对齐」 | ✅ 闭环（闸行四点 = ①出口语义 ②freeze ③作用面 ④终态，与 `:79`/`:89` 对齐） |
| **M2** ③与「批准不过期」选型冲突 | `:41③` 收窄为「decide 不拒超龄 pending 为已定前提 · 不 reopen；本点仅签 resume/消费环出口选型」 | ✅ 闭环（与 `:77` 钉死、`:123` decide 回归验收、`:126` decide 语义零变化不再冲突） |
| **M3** 缺旧测 grep 影响面 | `:128` 新增验收项（api `tests/` + web 测试 · 逐条标注保留/修改/删除+理由 · 禁止静默改测对齐） | ✅ 闭环 |
| **N3** 从严偏离签署 | `:82` 补「偏离从严默认须维护者签，30 不得自主裁量」 | ✅ 闭环 |

**辅助核验**：`:189` R3 增补落字维护者裁决记录（思考轮回填闭合 ✓）；`:215` 修订行如实登记 R1 承接；lint 20-R2 复跑 **PASS**（`npx spec-wave task lint` · 2026-11-02）。

---

## Minor（不阻塞 20 通过 · 30 前须闭环）

### M4 · web 仓 30 的 GATE_VERIFY 闸据缺位（双仓扩范围新增程序缺口）

- **task 行号**：`:31`（orchestration：30 走 api 分支 + web 分支 `task/web-hitl-resume-expired-mapping` 双 PR）
- **理由**：web 仓（`ops-desk-web`）AGENTS.md 纪律为「无 active task 不改码 · 30 前 `npx spec-wave verify --target . --task docs/tasks/active/task_*.md`」；实证 web 仓 `docs/tasks/active/` 当前**仅有 README.md、无 task 档**。本 task 把 W-fix-1-web 列入范围并安排了 web 分支，但未安排 web 仓侧 task 档（镜像薄壳指回本 task 闸表）或「web 侧 30 以 api 仓 task 为闸据」的显式裁决——web 仓 30 开工时 GATE_VERIFY 将无 task 可验而被拒。
- **建议修法（10 回填 · 可随签闸同批）**：`:31` orchestration 或依赖表补一条——web 仓落镜像 task 壳（范围=W-fix-1-web · 闸表指回本 task）**或**维护者显式裁决 web 侧 30 以 api 仓本 task 为闸据并在 web PR 描述挂接；二者择一即闭环。

---

## Note（留档 · 不要求修订）

- **N5 · 文档语境滞后（NIT）**：`:3` 状态行仍写「GO 20-R1」、`:39` HG-AUDIT-R1 说明仍写「20-R1 审查文 PASS 后维护者签」、`:205` 自检行仍标「10 起草自检」——均为 R2 语境下的小滞后，不影响执行判定；可在维护者签闸同批顺手刷新。
- **N6 · freeze 签署面提醒**：web `HitlApprovalView.vue` 文件头有「D2 冻结契约零分叉」自约束；W-fix-1-web 把 FP-5 文案触发面从 decide 扩展到 resume 错误路径，属渲染语义增量。`:41②`（freeze 是否增补 TTL 条）签署时建议维护者一并确认该触发面扩展是否需入 `hitl-browser-decide-v1` 增补条——决策点已挂在闸上，不算漏项，仅提醒签署时覆盖。
- **N7 · web 分支执行期事项**：`task/web-hitl-resume-expired-mapping` 在 web 仓 remote 尚不存在（20-R2 实证 `git ls-remote` 无）；分支创建属 30 开工时执行期事项，且以 M4 闭环为前提，不计文档缺陷。
- **N8 · 复检通过项**：F11/F12 覆盖无漏、「批准不过期，执行权过期」三环自洽、A4②/A5 回接锚定、failure_paths 完备（`:112` 双条件后更显式）、红测先行双仓可执行（api pytest + web Vitest · web 仓 `vitest ^3.2.4` 实证在位）、graph/wiki_delta 双仓评估留「以 30 实扫为准」活口、R0–R3 控制表与增补闭合——均复检通过。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R2 审查结论（PASS-WITH-MINOR · M4 为 30 前程序补救项）
- [ ] M4 闭环：web 仓镜像 task 壳 或 维护者裁决 web 侧 30 以 api 仓 task 为闸据（可随签闸同批落字）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] HG-GRAPH-MODULES / HG-W-FIX-DESIGN 维护者签收（②签署时留意 N6 freeze 触发面）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时 30 不得开工（见 `docs/harness/prompts/TEMPLATE_30_gate_stop.md`）。

---

### 修订

| 日期 | 说明 |
|------|------|
| 2026-11-02 | 20-R2 复审：R1 findings（B1/M1/M2/M3/N3）逐条核验**全部闭环** → 结论 **PASS-WITH-MINOR**；新立 M4（web 仓 GATE_VERIFY 闸据缺位 · 30 前程序补救）· note ×4（N5 语境滞后 NIT · N6 freeze 触发面提醒 · N7 web 分支执行期 · N8 复检通过项）· lint 复跑 PASS · 闸表未动 |
