# 审查文：task_host_v1_visibility_scenario_policy · 20-task-audit R2（2026-09-23）

> **hat_id**：20-task-audit · **轮次**：R2（R1 FAIL 回填后复审）· **审查对象**：`docs/tasks/active/task_host_v1_visibility_scenario_policy.md`（draft · 267 行 · R1 回填版）
> **对照真值**：SPEC `docs/spec/host-v1-visibility-scenario-policy/SPEC-host-v1-visibility-scenario-policy_v0.md`（signed · 231 行 · 含 R1 B-1 澄清段）· R1 审查文 `task_host_v1_visibility_scenario_policy_audit_R1_20260923.md`
> **方法**：R1 回填项逐条真读核对；代码真值亲读（nodes.py :925-948）；task lint 亲跑

---

## 结论摘要

| 维度 | 结论 |
|------|------|
| **内容** | **PASS-WITH-NITS** —— B-1 阻塞消解（三方一致）· N1–N5 逐条闭环 · 残留 1 条微 nit（N-R2-1） |
| **流程闸** HG-AUDIT-R1 | **pending（如实）** → 30 拒开工维持；本帽不签发 |

**总结论：PASS-WITH-NITS**。R1 唯一阻塞 B-1 经「00 亲验代码真值 → 回 10-spec 澄清（未 task 独断）→ task 同步」路径正确处置：SPEC D2 管线段（SPEC :71）与 FP-6（SPEC :172）勘正为「三重交集交换律等价 · 落点按数据可得性」，task 钉死契约（:87）、范围 D2（:102）、白名单（:163）与代码真值（`multi/nodes.py:933-948` · `strategy/builder.py`）三方一致，验收 catch-22 不复存在。N1–N5 全部闭环。残留 nit 仅文档精度级，可由 00 签闸前微修或留痕豁免。

---

## 一、B-1 阻塞复核（核心）✅ 消解

### 1. 三方一致性（钉死落点 vs 白名单 vs 代码真值）

| 面 | 内容 | 复核 |
|----|------|------|
| SPEC 澄清 | SPEC :71（D2 两阶段管线与落点 · 标注「2026-09-23 R1 审查 B-1 澄清 · 语义零改」）· SPEC :172（FP-6 同款措辞） | ✅ 真读 |
| task 钉死契约 | :87「管线与落点（FP-6 · SPEC R1 B-1 澄清）」：三重交集 · Builder 内 基线→scenario_trim→有效可见集 · supervisor 内 `delegation_scope = requested_scope ∩ 有效可见集`（对 V1-A 唯一接线改动） | ✅ 与 SPEC 逐字对齐 |
| task 范围 D2 | :102「Builder 接线（stage 2：基线→有效可见集）+ supervisor 接线（`nodes.py:933-948` 交集输入改有效可见集）」 | ✅ |
| task 白名单 | :163 已补「lg_rag/multi/nodes.py（:933-948 交集输入改有效可见集 · R1 审查 B-1 补列）」 | ✅ catch-22 消除 |
| 代码真值 | 亲读 `multi/nodes.py:925-954`：:933 `if _delegation_active() and not fallback and subtasks`（off 短路注释 :930）· :934 取 requested_scope · :937-939 `effective_scope_from_requested(requested_scope, allowed_ids)` · :940 写 `delegation_scope`；图序 intent→builder（graph.py:97）→ Builder 运行时意图已可得、requested_scope 尚不存在 | ✅ 行号/语义全吻合 |

### 2. 「交换律等价 · 语义零改」数学核验

- S1/S2/S3 规则产出 ∅，与交集顺序无关（∅ ∩ X = ∅）；
- S4 是**逐元素过滤器**（按 `x.risk_level` 剔除 medium），S5 恒等——对逐元素过滤有 `requested ∩ scenario(baseline) = scenario(requested ∩ baseline)` 恒成立；
- 故「基线→交集→场景维」与「基线→场景维→交集」终态相同，SPEC「语义零改」声明**成立**，非遁辞。
- 附加效应如实：enforce 下 supervisor 规划目录（allowed_capability_ids）也将是场景维后有效可见集——这正是 SPEC D2「最终可见集」本意；off 模式零 diff 由既有短路（nodes.py :930-933 · builder off 跳过 stage 2）双保险。

### 3. 程序合规

- 未 task 独断：先 10-spec 澄清（SPEC 修订记录 :231「R1 审查 B-1 澄清 · 00 代录同令 · 规则表 S1–S5/四字段/非范围全不动」）再 task 同步；本帽抽验 SPEC 其余段（:73-85 规则表 · :92-98 四字段 · FP 表 :167-174）确认除 D2 管线段与 FP-6 外零改动，澄清边界诚实。

---

## 二、N1–N5 闭环核对

| # | R1 问题 | 回填证据 | 结论 |
|---|---------|----------|------|
| N1 | failure_paths 计数 11 vs 实 12 | R3 控制表 :226「**12 条** = FP-1~8 + 过程三 + 畸形 intent 安全默认一（R1 审查 N1 计数修正）」· R3 节 :246「共十二条」 | ✅ 闭环 |
| N2 | 验收计数 16 vs 实 14 | R4 控制表 :227「验收 **14 条**（1/2/3/1/4/3 = 14 · R1 审查 N2 计数修正 · 变异检验×3 与注记不计入）」· R4 节 :250 · 自检 :258 | ✅ 闭环（实点复核：人工闸 1 + D1×2 + D2×3 + D3×1 + D4×4 + D5×3 = 14 ✓） |
| N3 | builder 锚点行号漂移 | 现状锚点 :68 重钉「:39-60（build_allowlist · stripped :55-59）· :63-75（effective_scope · MAX_SCOPE_IDS=64）」· 改造对象 :198「:39-75」· 必读 :213 | ✅ 主体闭环（R0 控制表残留旧号 → N-R2-1）；亲读核：build_allowlist 现 :39-60 · stripped 警告 :55-59 · MAX_SCOPE_IDS :63-64 · effective_scope def :67 —— 全部吻合 |
| N4 | SPEC §6-8/§6-10 映射未显式化 | 验收 D5 末 :164 注记（不计验收计数 · 标注 R1 审查 N4）：SSE 零新事件由 off 零 diff + B1 组 5 覆盖 · PR+CI merge 由 orchestration 承载 | ✅ 闭环 |
| N5 | 03 轨 risk_hint 真值指针 | 依赖行 :194「risk_hint 真值载体 = `docs/tasks/done/task_intent_schema_v1.md`（S2 · PR #80 MERGED）+ 代码 `schemas/intent.py:25-28`（R1 审查 N5 精确化）」 | ✅ 闭环 |

---

## 三、全面抽复（防回填引入新伤）

- **闸表**：HG-TASK-DRAFT approved（双令）· **HG-AUDIT-R1 pending（:40 维持）** · HG-GRAPH-MODULES approved · PILOT n/a —— 四行诚实如初。
- **task lint 亲跑**：`npx spec-wave verify --target . --task docs/tasks/active/task_host_v1_visibility_scenario_policy.md` → 闸表读出正确，报告 `VERIFY: BLOCKED · HG-AUDIT-R1 pending`（failClosed 一致 · 与 00「lint PASS」自述兼容——lint 通过而闸 pending 阻 30，正是设计行为）。
- **B1/验收/变异检验**：与 R1 版一致（B1 19 文件 · 三态 · 组 2/3 复核提示保留 :179-180）；白名单新增 nodes.py 一项已核（上述）。
- **修订记录** :267：R1 FAIL 回填全轨迹留痕（B-1 处置路径 + N1–N5 逐条），与本次复核所见一致，无虚报。

---

## 四、残留 nit（非阻塞）

| # | 内容 | 建议处置 |
|---|------|----------|
| N-R2-1 | 思考轮 **R0 控制表行 :223** 仍残留旧锚点「Builder 落点 :74-80」（N3 重钉漏网 · R0 节 :234 无此行号故仅表格一处）；另闸表 :40 说明「待 20-task-audit **R1** 审查文落盘后 00 代录」——R1 已落盘（FAIL）、现处 R2，措辞轻微过时 | 00 签 HG-AUDIT-R1 前将 R0 行 :74-80 改 :39-75 · 闸行措辞改「待 20-task-audit 审查文落盘」；或修订记录留痕豁免 |

---

## 五、纪律自查

- 本帽未改 task/SPEC 实质内容 · 未动 `app/` 代码 · 未签发任何 human_gate。
- HG-AUDIT-R1 仍 **pending**（task :40 · lint 复核 BLOCKED 一致），本审查文不附 30 Prompt。

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R2 审查结论（PASS-WITH-NITS · B-1 消解 · N1–N5 闭环 · 残留 N-R2-1 一条微修/豁免留痕）
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者授权 · 00 代录 · 日期 + 原话留痕）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt（30 由 00 委派子 Agent · 分支 `task/host-v1-visibility-scenario-policy` · 当前在 master 须先切分支）

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-23 | 20-task-audit R2：B-1 三方一致复核（SPEC :71/:172 · task :87/:102/:163 · 代码 nodes.py:925-954）+ 交换律等价数学核验（语义零改成立）+ N1–N5 逐条闭环 + lint 亲跑（BLOCKED 与 pending 一致）→ **PASS-WITH-NITS**（残留 N-R2-1：R0 行旧锚点 :74-80 · 闸行 R1 措辞过时）· HG-AUDIT-R1 维持 pending |
