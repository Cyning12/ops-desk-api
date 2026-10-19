# 20-task-audit R1 书面审：task_memory_injection_consumer

> **hat_id**：20-task-audit（R1）
> **审查对象**：`docs/tasks/active/task_memory_injection_consumer.md`（draft · 230 行 · 分支 `docs/task-memory-injection-consumer` · commit f6ef048）
> **审查日期**：2026-10-19 · **审查人**：Harness 20-task-audit（书面审 · 不改 task 实质 · **不代签**任何人工闸）
> **结论**：**conditional_pass（PASS-WITH-NITS）** · 内容面零阻塞 · 非阻塞 N1–N3（均 30/裁定点执行层提示，不退回 10-task）· **HG-AUDIT-R1 维持 pending，维护者签闸后方可 30**
> **实证复核范围**：task 全文 230 行逐行 · SPEC v0.1 全文 166 行 · 审查文 `spec_memory-injection-consumer_audit_R1_20261019.md`（R1+R2）全文 152 行 · 源码实读 `app/ops/lg_rag/continuity.py:130-239,300-374,505-544` · `app/ops/lg_rag/nodes.py:44-58,110-164,205-269` · `app/ops/lg_rag/graph.py:50-64,190-214,270-284` · `app/ops/lg_rag/multi/nodes.py:1035-1066,1155-1174,1425-1439,2028-2055` · `docs/_tech_graph/l1/01_modules.md:30-69` · grep 全仓 4000 截断先例 · TC12 九个旧测文件存在性 · invoke 目录存在性

---

## 一、结论摘要

| 维度 | 裁定 |
|------|------|
| **内容面**（范围/验收/FP/思考轮/锚点） | **PASS（零内容阻塞）** |
| **流程闸** HG-AUDIT-R1 | **pending**（本帽不代签；签前 30 拒改码，含 Phase A tests/ 新增） |
| **流程闸** HG-PHASE-B-DECISION | pending（新增裁定点闸 · 设计自洽，见 §四） |

---

## 二、核对项实录（逐条）

### 1. 范围越/缩 SPEC · **PASS**

- 范围 = SPEC §2 两阶段串行原样（Phase A 观测-only → 裁定点 → Phase B），五结局触发/内容与 SPEC §2 分支表逐行对应，无越界新增功能面。
- 非范围 = SPEC §3 五条逐字继承（task :97-101 ↔ SPEC :73-77 逐字一致）；task 级补充五条（:105-109）均为纪律性约束（Phase A 不动 app/ · 不临场发明 · 未落签不进 Phase B · 不重复查询 · 本起草阶段零改码），不加新功能面，**非范围无缩减**。
- graph_change_layer=none 预期、freeze_id 零契约变更均与 SPEC 元信息一致（task :20/:31 ↔ SPEC :25/:26）。
- 新增件均有 SPEC 授权依据：HG-PHASE-B-DECISION ← SPEC §7「接线/收窄争议由维护者在 task 签收时按 Phase A 证据裁定」+ §6「分支选择有 Phase A 证据引用」；8000 字符定值 ← SPEC §7「块总量设上限（task 阶段定数值）」（见 §二.6）。

### 2. Phase A 观测-only 口径 · **PASS（TC5 兜底充分 · N2 可更严）**

- 纪律三层互锁：范围节「Phase A 不动 `app/` 任何生产码，spy 只在 `tests/`」（:67）+ 非范围 task 级补充（:105）+ **TC5 diff 面断言**（:139「相对 master 的 `git diff --name-only` 不含 `app/` 任何文件」）。
- SPEC 侧互锁原样在册（§3 首条 + §7 风险表首行）。TC5 为黑名单形态（排除 app/），对本 task「零生产码」声明充分——生产运行码全部位于 app/ 下。
- **N2**：TC5 可收紧为白名单形态（diff ⊆ tests/ + docs/），scripts/、alembic/ 等非 app 面未显式排除；Phase A 无触达动机，属 30 执行层可顺手收紧项，不退回。

### 3. Phase B 五结局完备性与互斥触发 · **PASS（互斥成立 · N1 形式完备性提示）**

- **互斥** ✅（R2-N2 吸收落实）：②B-a/③B-b 触发行均补显式前提「且 router/basic 有消费者坐实」（task :84-85），与 ④a/④b「三模式均零消费」（:86-87）及 ①「三模式均有消费者」（:83）三向互斥，无重叠。
- **R2-N1 吸收** ✅：task 全文统一五案口径（:18 test_strategy_note · :50-52 目标节口径对齐段点名 SPEC 残留三坐标）；task 内「二选一」仅存于两处**引述残留问题**的语境（:52、:198），无规范性使用。
- **R2-N3 吸收** ✅：回滚段（:91）补「第三结局两案同为默认关下行为」并分别钉死回滚语义（扩展接线=移除接线恢复原组装 · 全模式收窄=恢复注入查询路径）。
- **N1（低 · 形式完备性）**：task :199 称结局空间「完备无漏」，严格按 2×2 证据象限（supervisor 有/无 × router/basic 有/无），「supervisor **有**消费者 ∧ router/basic **零**消费」一象限无对应触发结局。缓解事实：(a) 静态证据下该组合几乎不可能——三模式消费点全部重建 query-only prompt（本审 §三锚点实测）；(b) 既有 fail-safe：FP-9（:127）规定表外情形退回裁定点由维护者裁定另立 SPEC，不死锁。建议维护者在 HG-PHASE-B-DECISION 裁定时，若证据组合不落五案触发，径按 FP-9 处置；可在裁定记录位顺手补一句兜底口径。不退回（SPEC 层面同框架已经 20-spec-audit R2 判完备并签收，本帽不翻 SPEC 案）。

### 4. HG-PHASE-B-DECISION 新闸设计 · **PASS（自洽 · 不越 SPEC 自锁）**

- **blocks 面正确**：blocks_hats=30（Phase B），明示「Phase A（观测-only）不受本闸阻塞」（:40）；与 HG-AUDIT-R1「签前 30 拒改码（含 Phase A tests/ 新增）」（:38）分层清晰——Phase A 只被 HG-AUDIT-R1 挡，不被裁定点闸挡。
- **裁定记录位双落**：task 闸表 + invoke 裁定记录位（:40 · TC6 :140），格式钉死「因 Phase A 实证行 X → 裁定结局 Y」。
- **自锁原样继承**：task :77 引 SPEC §2「全部结局的处置方案都已在下表预写，30 不临场发明表外方案」——与 SPEC :50 逐字一致；FP-9 兜底表外方案。
- **授权链闭合**：SPEC §7「争议由维护者在 task 签收时裁定」（:121）→ task 把该裁定点**形式化为人工闸**并加记录位，属裁定权的操作化落实，非新增裁决权，不越 SPEC。

### 5. 验收 TC 可机器化 · **PASS**

TC1–TC12 全部 spy/fake LLM / 夹具 / 零 diff 对拍 / diff 面断言，**不打真模型**；无人工判断项。边界口径钉死：TC7「>8000 截尾+span `memory_injection_truncated=true` · ≤8000 不截」闭区间无歧义；TC2 默认关逐元素相等。TC6（裁定记录位）为文档内容 grep 可断。K7 旧测影响面 TC12（:146-150）九个既有测试文件**逐一实测全部存在**：`tests/test_memory_injection.py` · `test_memory_episode_recall.py` · `test_lg_rag_session_continuity.py` · `test_session_summary.py` · `test_memory_vector_p1.py` · `test_memory_service_db.py` · `test_memory_extract_p1.py` · `test_input_isolation_wiring.py` · `tests/eval/test_input_isolation.py`。

### 6. 8000 字符定值授权依据 · **PASS**

SPEC §7（:120）明文「块总量设上限（**task 阶段定数值**）」——授权在册。定值推导有据：「窗先例 query+answer 各截 4000 ×2」实测对应 `app/ops/memory/extract.py:46` `EXTRACT_WINDOW_MAX_CHARS = 4000` 与 `app/ops/memory/README.md:121`「本轮 query + 终答，单侧截断 4000」；8000=2×4000 量级一致，截尾+span 标记机断可测。task R2 轮（:201）如实标注「本帽定值（SPEC §7 授权），实测若不足由 40 上抛」。

### 7. FP 映射闭合 · **PASS**

SPEC FP-1~FP-6 → task FP-1~FP-6 全数在册（:119-124），措辞按五结局口径对齐（FP-3 双分支判定、FP-4 扩截尾断言、FP-5 扩 ④b）；新增 FP-7~FP-9（:125-127）覆盖裁定点/闸纪律/表外方案，与 HG-PHASE-B-DECISION、HG-AUDIT-R1、SPEC §2 自锁一一互锁。无悬空 FP、无无归属失败面。

### 8. R0–R5 思考轮 · **PASS**

控制表六轮齐全（:177-184），各轮小节在册，`actual_last_round=R5`（:186）；R5 诚实标注两闸 pending「签前/裁定前 30 拒改码」；R2 轮逐条记录 R2-N1~N3 吸收裁定（:198-201）；residual_risks 如实挂账（spy 穿透深度、8000 定值）。

### 9. 闸表 · **PASS**

| 闸 | task 表状态 | 实证 |
|---|---|---|
| HG-SPEC-SIGNOFF | approved | 有据：SPEC 状态行 :3 + §9 :166 + 审查文 R2 节三处同载 |
| **HG-AUDIT-R1** | **pending** | ✅ 符合纪律（本帽审查不代签；00 落闸动作在本审之后） |
| HG-GRAPH-MODULES | approved | 在册实测：`01_modules.md` 人签记录表 :61 起多行 approved；`memory` 行 :36、`lg_rag` 行 :35 均在册 |
| **HG-PHASE-B-DECISION** | **pending** | ✅ 新增裁定点闸，起草时 pending 正确 |

---

## 三、锚点抽查实录（30 处 · 当前分支含 PR #284 代码面）

| task 引用 | 实测 | 裁定 |
|---|---|---|
| `continuity.py:349-362` `inject_memory_facts_block` | def :349 · 空块原样返回 :354-355 · `return [*messages[:idx], SystemMessage(content=block), *messages[idx:]]` :362 | ✅ 逐字 |
| `continuity.py:527` episodes 落点 | `return inject_memory_facts_block(messages, episode_block)` :527 | ✅ 逐字 |
| `continuity.py:200` `MEMORY_EPISODES_HEADER` · `:316` `render_memory_episodes_block` | :200 / :316 逐字 | ✅ |
| `continuity.py:142-151` / `:208-222` 开关默认关·非法回退关 | 语义成立（未设 false :146/:217 · 非法 warning+fallback :151-152/:222-223）；**行区间恰差尾行 `return False`（:152/:223）→ N3** | ✅（N3） |
| `nodes.py:48-53` `_last_user_text` 仅末条 HumanMessage | :48-53 逐字（:50 `type=="human"` 判定） | ✅ |
| `nodes.py:119` router_node | :119 `query = _last_user_text(state["messages"])` | ✅ |
| `nodes.py:153-154` rag_node → `ainvoke_evidence_answer(query)` | :153-154 逐字（只传 query 字符串） | ✅ |
| `nodes.py:209-218` rewrite_node 重建 `[system, user=original]` | :209 取 original · :214-218 双消息 complete | ✅ |
| `nodes.py:255-263` direct_answer_node 重建双消息 | :255 取 query · :260-263 `[system, user=query]` | ✅ |
| `graph.py:56-62` basic 图 `START→rag→END` | :56-62 逐字 | ✅ |
| `graph.py:199-206` fresh 装配入 payload · `:278` `history_turns` 缺省 None | :199-205 `assemble_graph_messages_with_memory` · :206 payload · :278 缺省 None | ✅ |
| `multi/nodes.py:1163-1170` planner `[system, user=query]` | :1163-1170 逐字 | ✅ |
| `multi/nodes.py:2035-2043` off 态 · `:2046-2048` on 态三参无 history | off `(query, payload)` :2035-2043 · on `(query, results, payload)` :2046-2048 | ✅ |
| `multi/nodes.py:1432-1435` rag 工人未传 `history_turns` | :1432-1435 `astream_router_agent(result["input"], thread_id=...)` | ✅ |
| `multi/nodes.py:1041-1063` `_worker_state` 带全量 messages 但工人不用 | :1054 `"messages": list(...)` 在册；工人路径只用 `result["input"]`（:1433） | ✅ |
| 10 帽自述 SPEC 残留坐标 :4/:44/:23 | SPEC :4「Phase B 按实证结论二选一修复」· :44「则二选一处置：(a) 接线…或 (b) 收窄」· :23「接线修复…或按模式跳过注入」——三处残留措辞属实 | ✅ |
| invoke 目录（承 R1 N3） | `docs/harness/invokes/by-task/memory-injection-consumer/invoke_20261019_10_task_draft.md` 已落 | ✅ |

**30 处锚点全命中**；continuity.py 校正值（PR #284 漂移后 :349-362/:527/:316/:200/:142-151/:208-222）与现行代码一致，task「按实校正」声明属实。

---

## 四、非阻塞 nits（不退回 · 30/裁定点执行层吸收）

| ID | 严重级 | 位置 | 内容 |
|---|---|---|---|
| N1 | 低 | task :83-87 · :199 | 结局空间 2×2 象限中「supervisor 有消费者 ∧ router/basic 零消费」无触发结局，「完备无漏」表述形式上过强；静态证据下该组合几乎不可能，且 FP-9 已提供 fail-safe（退回裁定点另立 SPEC）。建议：HG-PHASE-B-DECISION 遇未覆盖证据组合径按 FP-9 处置，可在裁定记录位补兜底口径一句 |
| N2 | 低 | task :139（TC5） | TC5 为黑名单形态（diff 不含 app/）；可收紧为白名单（diff ⊆ tests/ + docs/invokes），scripts/、alembic/ 等非 app 面未显式排除。30 执行时顺手收紧即可 |
| N3 | 低 | task :73 · :161 | continuity.py 开关锚点行区间 :142-151/:208-222 恰差尾行 `return False`（:152/:223）；语义声明实测成立，30 按实校正行号即可 |

---

## 五、回填清单

无（零内容阻塞，无需退回 10-task）。

## 六、维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-10-19 | R1：SPEC 对照（范围/非范围/FP/验收）零越缩 · R2-N1~N3 吸收逐条落实 · HG-PHASE-B-DECISION 新闸设计自洽不越 SPEC 自锁 · 8000 定值有 §7 授权+4000 先例实测 · 锚点 30 处全命中（N3 差尾行 1 行）· TC12 九旧测文件存在 · 结论 **conditional_pass** · 非阻塞 N1–N3 · HG-AUDIT-R1 维持 pending（不代签） |
